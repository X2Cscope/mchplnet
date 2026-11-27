"""Tests for LNet.reboot_device() (LNet service 0x19 Reboot).

LNet v5, 4.13: a device that executes the reboot does not answer; it answers only with an error ID.
"""

import contextlib
import io
import unittest
from unittest.mock import Mock

from mchplnet.errors import NO_ERROR, LNetFrameError, ServiceResult, error_description
from mchplnet.framing import lnet_checksum
from mchplnet.lnet import LNet
from mchplnet.services.frame_reboot import FrameReboot

REBOOT_REQUEST = bytes([0x55, 0x01, 0x01, 0x19, 0x70])  # SYN, SIZE, NODE, Service ID, checksum
SID_REBOOT = 0x19


def response(error_id: int) -> bytearray:
    """Return a Reboot response frame (SIZE 2, followed by a fill byte) with the given error ID."""
    payload = bytes([0x55, 0x02, 0x01, SID_REBOOT, error_id])
    return bytearray([0x55, 0x02, 0x00, 0x01, SID_REBOOT, error_id, lnet_checksum(payload)])


class TestServiceResult(unittest.TestCase):
    """ServiceResult carries the code and its description."""

    def test_from_code(self):
        """from_code() adds the description; success is only true for NO_ERROR."""
        result = ServiceResult.from_code(0x21)
        self.assertEqual(result, (0x21, error_description(0x21)))
        self.assertFalse(result.success)
        self.assertTrue(ServiceResult.from_code(NO_ERROR).success)

    def test_unpacking(self):
        """The result unpacks like a (code, text) tuple."""
        code, text = ServiceResult.from_code(0x22)
        self.assertEqual((code, text), (0x22, "Invalid DSP state"))


class TestRebootDevice(unittest.TestCase):
    """reboot_device() sends once and treats a missing answer as success."""

    def setUp(self):
        """LNet with a mocked, initialised interface."""
        self.interface = Mock()
        self.interface.initialised = True
        self.lnet = LNet(self.interface, handshake=False)

    def test_request_frame(self):
        """The request is the documented Reboot frame without service data."""
        self.assertEqual(bytes(FrameReboot().serialize()), REBOOT_REQUEST)

    def test_no_answer_is_success(self):
        """Timeout after the request: the device reboots; the request is not sent again."""
        self.interface.read.side_effect = TimeoutError()
        self.assertEqual(self.lnet.reboot_device(), (NO_ERROR, "No error"))
        self.interface.write.assert_called_once()
        self.interface.start.assert_not_called()

    def test_connection_lost_is_success(self):
        """TCP: the connection drops because the device resets; no second reboot is sent."""
        self.interface.read.side_effect = ConnectionResetError()
        self.assertTrue(self.lnet.reboot_device().success)
        self.interface.write.assert_called_once()
        self.interface.stop.assert_not_called()

    def test_not_supported(self):
        """Firmware without reboot support answers 0x21."""
        self.interface.read.return_value = response(0x21)
        self.assertEqual(self.lnet.reboot_device(), (0x21, "Service not available"))

    def test_refused_by_application(self):
        """The application refuses the reboot (e.g. motor running): 0x22."""
        self.interface.read.return_value = response(0x22)
        result = self.lnet.reboot_device()
        self.assertEqual(result, (0x22, "Invalid DSP state"))
        self.assertFalse(result.success)

    def test_unknown_error_id(self):
        """An unexpected error ID is returned with a generic description."""
        self.interface.read.return_value = response(0x14)
        self.assertEqual(self.lnet.reboot_device(), (0x14, "Format error"))

    def test_success_answer_is_accepted(self):
        """A device answering 'no error' before it resets is accepted as well."""
        self.interface.read.return_value = response(0x00)
        self.assertTrue(self.lnet.reboot_device().success)

    def test_invalid_answer_raises(self):
        """An answer to another service is not a reboot result."""
        payload = bytes([0x55, 0x02, 0x01, 0x09, 0x00])
        self.interface.read.return_value = bytearray([0x55, 0x02, 0x00, 0x01, 0x09, 0x00, lnet_checksum(payload)])
        with self.assertRaises(LNetFrameError):
            self.lnet.reboot_device()

    def test_nothing_printed(self):
        """reboot_device() printed the request frame to stdout before; it must not print anything."""
        self.interface.read.side_effect = TimeoutError()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.lnet.reboot_device()
        self.assertEqual(out.getvalue(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
