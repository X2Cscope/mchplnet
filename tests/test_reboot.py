"""Tests for LNet.reboot_device() (LNet service 0x19 Reboot).

LNet v5, 4.13: a device that executes the reboot does not answer; it answers only with an error ID.
"""

import contextlib
import io
import unittest
from unittest.mock import Mock

from mchplnet.errors import LNetDeviceError
from mchplnet.framing import lnet_checksum
from mchplnet.lnet import LNet
from mchplnet.services.frame_reboot import FrameReboot

REBOOT_REQUEST = bytes([0x55, 0x01, 0x01, 0x19, 0x70])  # SYN, SIZE, NODE, Service ID, checksum
SID_REBOOT = 0x19


def response(error_id: int) -> bytearray:
    """Return a Reboot response frame (SIZE 2, followed by a fill byte) with the given error ID."""
    payload = bytes([0x55, 0x02, 0x01, SID_REBOOT, error_id])
    return bytearray([0x55, 0x02, 0x00, 0x01, SID_REBOOT, error_id, lnet_checksum(payload)])


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
        self.assertIsNone(self.lnet.reboot_device())
        self.interface.write.assert_called_once()
        self.interface.start.assert_not_called()

    def test_connection_lost_is_success(self):
        """TCP: the connection drops because the device resets; no second reboot is sent."""
        self.interface.read.side_effect = ConnectionResetError()
        self.lnet.reboot_device()
        self.interface.write.assert_called_once()
        self.interface.stop.assert_not_called()

    def test_not_supported(self):
        """Firmware without reboot support answers 0x21."""
        self.interface.read.return_value = response(0x21)
        with self.assertRaises(LNetDeviceError) as ctx:
            self.lnet.reboot_device()
        self.assertEqual(ctx.exception.error_id, 0x21)
        self.assertIn("Reboot", str(ctx.exception))

    def test_refused_by_application(self):
        """The application refuses the reboot (e.g. motor running): 0x22."""
        self.interface.read.return_value = response(0x22)
        with self.assertRaises(LNetDeviceError) as ctx:
            self.lnet.reboot_device()
        self.assertEqual(ctx.exception.error_id, 0x22)

    def test_success_answer_is_accepted(self):
        """A device answering 'no error' before it resets is accepted as well."""
        self.interface.read.return_value = response(0x00)
        self.assertIsNone(self.lnet.reboot_device())

    def test_nothing_printed(self):
        """reboot_device() printed the request frame to stdout before; it must not print anything."""
        self.interface.read.side_effect = TimeoutError()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.lnet.reboot_device()
        self.assertEqual(out.getvalue(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
