"""Tests for reconnecting when the device resets the connection (TCP RST).

Observed on a dsPIC33AK T1S board with lwIP: after a board reset, the first TCP connection is reset by the
board right after the handshake (it still resolves the host's MAC address); the second connection works.
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

from mchplnet.interfaces.tcp_ip import LNetTcpIp
from mchplnet.lnet import LNet

RESERVED = (0x55, 0x02)


def response(service_id: int, data: bytes = b"", error_id: int = 0x00) -> bytes:
    """Build a raw LNet v5 response frame with fill bytes and checksum."""
    payload = bytes([0x55, len(data) + 2, 0x01, service_id, error_id]) + bytes(data)
    raw = bytearray([0x55])
    for byte in payload[1:]:
        raw.append(byte)
        if byte in RESERVED:
            raw.append(0x00)
    checksum = sum(payload) & 0xFF
    raw.append((~checksum) & 0xFF if checksum in RESERVED else checksum)
    return bytes(raw)


DEVICE_INFO = response(0x00, (5).to_bytes(2, "little") + (1).to_bytes(2, "little") + bytes([255])
                       + (0x8240).to_bytes(2, "little") + b"Jan012026" + b"1200" + b"Jan012026" + b"1200"
                       + bytes([0x01]) + bytes(2) + bytes(4) + bytes(4))
LOAD_PARAMETER = response(0x11, bytes([0, 0]) + bytes(18) + (5000).to_bytes(4, "little") * 2 + bytes([0x82]))


def reset_socket():
    """A socket that connects, but the device resets the connection on the first receive."""
    sock = MagicMock()
    sock.recv.side_effect = ConnectionResetError(10054, "An existing connection was forcibly closed")
    return sock


def working_socket(*chunks):
    """A socket that returns the given chunks."""
    sock = MagicMock()
    sock.recv.side_effect = list(chunks)
    return sock


class TestTcpReconnectOnReset(unittest.TestCase):
    """LNetTcpIp.start() reconnects once if the device resets the connection during the handshake."""

    def test_first_connection_reset_second_works(self):
        """The first connection after a device reset is reset; LNet connects on the second one."""
        first, second = reset_socket(), working_socket(DEVICE_INFO, LOAD_PARAMETER)
        with patch("socket.socket", side_effect=[first, second]) as socket_class, \
                self.assertLogs(level="WARNING") as logs:
            lnet = LNet(LNetTcpIp(host="192.168.0.100"))
        self.assertEqual(socket_class.call_count, 2)
        first.close.assert_called_once()
        self.assertEqual(lnet.device_info.uc_width, 4)
        self.assertEqual(lnet.scope_data.data_array_size, 5000)
        self.assertTrue(any("reset by the device" in line for line in logs.output))

    def test_both_connections_reset(self):
        """If the second connection is reset as well, the error is raised (no endless retry)."""
        with patch("socket.socket", side_effect=[reset_socket(), reset_socket()]) as socket_class, \
                self.assertRaises(ConnectionResetError), self.assertLogs(level="WARNING"):
            LNet(LNetTcpIp(host="192.168.0.100"))
        self.assertEqual(socket_class.call_count, 2)

    def test_connection_closed_by_device(self):
        """An orderly close (recv returns no data) during the handshake is retried the same way."""
        closing = working_socket(b"")
        with patch("socket.socket", side_effect=[closing, working_socket(DEVICE_INFO, LOAD_PARAMETER)]), \
                self.assertLogs(level="WARNING"):
            lnet = LNet(LNetTcpIp(host="192.168.0.100"))
        self.assertEqual(lnet.device_info.monitor_version, 5)

    def test_timeout_is_not_retried(self):
        """An unreachable device is reported as before (ValueError), without a second attempt."""
        sock = MagicMock()
        sock.connect.side_effect = TimeoutError("timed out")
        with patch("socket.socket", return_value=sock) as socket_class, self.assertRaises(ValueError):
            LNet(LNetTcpIp(host="192.168.0.100"))
        self.assertEqual(socket_class.call_count, 1)


class TestXchgDataReconnect(unittest.TestCase):
    """LNet._xchg_data reconnects once on a lost connection of an established interface."""

    def setUp(self):
        """LNet with a mocked, already initialised interface."""
        self.interface = Mock()
        self.interface.initialised = True
        self.lnet = LNet(self.interface, handshake=False)

    def test_reset_on_read_is_retried_once(self):
        """RST while waiting for the response: restart the interface and send the frame again."""
        self.interface.read.side_effect = [ConnectionResetError(), b"response"]
        with self.assertLogs(level="WARNING"):
            self.assertEqual(self.lnet._xchg_data(b"request"), b"response")
        self.interface.stop.assert_called_once()
        self.interface.start.assert_called_once()
        self.assertEqual(self.interface.write.call_count, 2)

    def test_reset_on_write_is_retried_once(self):
        """Broken connection when sending: restart and send again."""
        self.interface.write.side_effect = [BrokenPipeError(), None]
        self.interface.read.return_value = b"response"
        with self.assertLogs(level="WARNING"):
            self.assertEqual(self.lnet._xchg_data(b"request"), b"response")
        self.interface.start.assert_called_once()

    def test_second_failure_propagates(self):
        """Only one retry: a second reset is raised."""
        self.interface.read.side_effect = [ConnectionResetError(), ConnectionResetError()]
        with self.assertRaises(ConnectionResetError), self.assertLogs(level="WARNING"):
            self.lnet._xchg_data(b"request")
        self.interface.start.assert_called_once()

    def test_not_initialised_is_not_retried(self):
        """During the connection test (interface not initialised yet) the error is raised unchanged.

        start() is never called recursively; LNetTcpIp.start() handles that case itself.
        """
        self.interface.initialised = False
        self.interface.read.side_effect = ConnectionResetError()
        with self.assertRaises(ConnectionResetError):
            self.lnet._xchg_data(b"request")
        self.interface.start.assert_not_called()

    def test_timeout_still_retried(self):
        """Existing behaviour: a timeout is retried once as before."""
        self.interface.read.side_effect = [TimeoutError(), b"response"]
        with self.assertLogs(level="WARNING"):
            self.assertEqual(self.lnet._xchg_data(b"request"), b"response")


if __name__ == "__main__":
    unittest.main(verbosity=2)
