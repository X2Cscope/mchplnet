"""Tests for response checking: device error IDs, checksum, length and service ID raise typed exceptions.

Before, deserialize() only logged (with an inverted condition) and parsed error responses as data, e.g. a
Load Parameter error looked like "scope idle", and Put RAM / Save Parameter errors were silently ignored.
"""

import unittest
from unittest.mock import Mock

from mchplnet.errors import LNetDeviceError, LNetError, LNetFrameError, error_description
from mchplnet.lnet import LNet
from mchplnet.lnetframe import LNetFrame
from mchplnet.services.frame_getram import FrameGetRam
from mchplnet.services.frame_load_parameter import FrameLoadParameter
from mchplnet.services.frame_putram import FramePutRam
from mchplnet.services.frame_save_parameter import FrameSaveParameter

RESERVED = (0x55, 0x02)


def response(data, node=0x01, size=None, checksum=None) -> bytearray:
    """Build a raw LNet v5 response frame with fill bytes (independent reference implementation)."""
    size = len(data) if size is None else size
    payload = [0x55, size, node, *data]
    raw = bytearray([0x55])
    for byte in payload[1:]:
        raw.append(byte)
        if byte in RESERVED:
            raw.append(0x00)
    crc = sum(payload) & 0xFF
    if crc in RESERVED:
        crc = (~crc) & 0xFF
    raw.append(crc if checksum is None else checksum)
    return raw


def get_ram_frame(size=4):
    """Return a Get RAM Block request frame for a 32-bit device."""
    return FrameGetRam(0x20001000, size, 1, 4)


def parse(frame: LNetFrame, raw: bytearray):
    """Deserialize a raw response with the given frame object."""
    frame.received = bytearray(raw)
    return frame.deserialize()


class TestValidResponses(unittest.TestCase):
    """Valid responses are still parsed as before."""

    def test_get_ram_data(self):
        """Get RAM Block returns the service data."""
        self.assertEqual(parse(get_ram_frame(), response([0x09, 0x00, 0x11, 0x22, 0x33, 0x44])),
                         bytearray([0x11, 0x22, 0x33, 0x44]))

    def test_get_ram_data_with_reserved_values(self):
        """Data containing 0x55/0x02 (fill bytes on the wire) is parsed correctly."""
        self.assertEqual(parse(get_ram_frame(3), response([0x09, 0x00, 0x55, 0x02, 0x55])),
                         bytearray([0x55, 0x02, 0x55]))

    def test_put_ram_success(self):
        """Put RAM Block success response (SIZE 2, followed by a fill byte) is accepted."""
        parse(FramePutRam(0x20001000, 4, 4, bytearray(4)), response([0x0A, 0x00]))

    def test_save_parameter_success(self):
        """Save Parameter success response is accepted."""
        parse(FrameSaveParameter(), response([0x12, 0x00]))


class TestDeviceErrors(unittest.TestCase):
    """Error IDs sent by the device raise LNetDeviceError."""

    def _assert_device_error(self, frame, service_id, error_id):
        with self.assertRaises(LNetDeviceError) as ctx:
            parse(frame, response([service_id, error_id]))
        self.assertEqual(ctx.exception.service_id, service_id)
        self.assertEqual(ctx.exception.error_id, error_id)
        return ctx.exception

    def test_get_ram_format_error(self):
        """Get RAM Block answered with 0x14: descriptive exception instead of ValueError."""
        error = self._assert_device_error(get_ram_frame(), 0x09, 0x14)
        self.assertIn("Get RAM Block", str(error))
        self.assertIn("Format error", str(error))
        self.assertEqual(error.description, "Format error")

    def test_put_ram_error_is_not_ignored(self):
        """Put RAM Block errors were silently ignored before."""
        self._assert_device_error(FramePutRam(0x20001000, 4, 4, bytearray(4)), 0x0A, 0x14)

    def test_save_parameter_error_is_not_ignored(self):
        """Save Parameter errors were silently ignored before."""
        self._assert_device_error(FrameSaveParameter(), 0x12, 0x40)

    def test_load_parameter_error_does_not_look_like_idle_scope(self):
        """A Load Parameter error parsed as all-zero data, i.e. 'scope idle / data ready'."""
        self._assert_device_error(FrameLoadParameter(), 0x11, 0x43)

    def test_unknown_error_id(self):
        """Unknown error IDs raise LNetDeviceError too (get_error_id raised KeyError before)."""
        error = self._assert_device_error(get_ram_frame(), 0x09, 0x99)
        self.assertEqual(error.description, "Unknown error ID 0x99")
        self.assertEqual(LNetFrame.get_error_id(0x99), "Unknown error ID 0x99")

    def test_error_table(self):
        """Error IDs of LNet v5, v6 and the X2Cscope profile are known."""
        for error_id in (0x13, 0x14, 0x15, 0x21, 0x22, 0x23, 0x40, 0x41, 0x42, 0x43, 0x44):
            self.assertFalse(error_description(error_id).startswith("Unknown error ID"), hex(error_id))

    def test_exception_hierarchy(self):
        """Both exception types can be caught as LNetError."""
        self.assertTrue(issubclass(LNetDeviceError, LNetError))
        self.assertTrue(issubclass(LNetFrameError, LNetError))


class TestInvalidFrames(unittest.TestCase):
    """Invalid response frames raise LNetFrameError."""

    def test_checksum_error(self):
        """A wrong checksum is rejected (was only logged under an inverted condition)."""
        raw = response([0x09, 0x00, 0x11, 0x22, 0x33, 0x44])
        raw[-1] ^= 0x01
        with self.assertRaisesRegex(LNetFrameError, "Checksum"):
            parse(get_ram_frame(), raw)

    def test_response_of_other_service(self):
        """A response to another service (e.g. a late response) is rejected."""
        with self.assertRaisesRegex(LNetFrameError, "received service 0x0A"):
            parse(get_ram_frame(), response([0x0A, 0x00]))

    def test_size_mismatch(self):
        """SIZE not matching the received data bytes is rejected."""
        with self.assertRaisesRegex(LNetFrameError, "SIZE"):
            parse(get_ram_frame(), response([0x09, 0x00, 0x11, 0x22], size=6))

    def test_too_short(self):
        """Frames shorter than SYN, SIZE, NODE, Service ID, Error ID, CRC are rejected."""
        for raw in (bytearray(), bytearray([0x55]), bytearray([0x55, 0x01, 0x01, 0x09, 0x60])):
            with self.subTest(raw=raw.hex()), self.assertRaises(LNetFrameError):
                parse(get_ram_frame(), raw)

    def test_no_response(self):
        """No received data at all is rejected."""
        frame = get_ram_frame()
        frame.received = None
        with self.assertRaises(LNetFrameError):
            frame.deserialize()


class TestLNetApi(unittest.TestCase):
    """Errors propagate through the LNet API."""

    def setUp(self):
        """LNet with a mocked interface and 32-bit device."""
        self.interface = Mock()
        self.lnet = LNet(self.interface, handshake=False)
        self.lnet.device_info = Mock()
        self.lnet.device_info.uc_width = 4

    def test_get_ram_raises_device_error(self):
        """get_ram() raises LNetDeviceError with the device's error ID."""
        self.interface.read.return_value = response([0x09, 0x15])
        with self.assertRaises(LNetDeviceError) as ctx:
            self.lnet.get_ram(0x20001000, 4)
        self.assertEqual(ctx.exception.error_id, 0x15)

    def test_put_ram_raises_device_error(self):
        """put_ram() raises instead of returning silently."""
        self.interface.read.return_value = response([0x0A, 0x14])
        with self.assertRaises(LNetDeviceError):
            self.lnet.put_ram(0x20001000, 4, bytearray(4))

    def test_load_parameters_raises_device_error(self):
        """load_parameters() raises instead of reporting an idle scope."""
        self.interface.read.return_value = response([0x11, 0x43])
        with self.assertRaises(LNetDeviceError):
            self.lnet.load_parameters()

    def test_get_ram_success(self):
        """get_ram() still returns the data of a valid response."""
        self.interface.read.return_value = response([0x09, 0x00, 0x78, 0x56, 0x34, 0x12])
        self.assertEqual(self.lnet.get_ram(0x20001000, 4), bytearray([0x78, 0x56, 0x34, 0x12]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
