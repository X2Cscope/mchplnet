"""Test suite for Interface and its implementations.

This module contains tests for the abstract interface and its concrete implementations.
"""

import time
import unittest
from unittest.mock import patch, MagicMock

import serial

from mchplnet.interfaces.abstract_interface import Interface
from mchplnet.interfaces.tcp_ip import LNetTcpIp
from mchplnet.interfaces.uart import LNetSerial

# Import CAN interface
from mchplnet.interfaces.can import LNetCan


class TestInterface(unittest.TestCase):
    """Test cases for the Interface abstract base class."""

    def test_interface_contract(self):
        """Test that all required methods are defined as abstract."""
        self.assertTrue(hasattr(Interface, 'write'))
        self.assertTrue(hasattr(Interface, 'read'))
        self.assertTrue(hasattr(Interface, 'start'))
        self.assertTrue(hasattr(Interface, 'stop'))
        self.assertTrue(hasattr(Interface, 'is_open'))


class MockInterface(Interface):
    """Concrete implementation of Interface for testing."""

    def __init__(self, **kwargs):
        """Initialize the mock interface.

        Args:
            **kwargs: Arbitrary keyword arguments including delay and auto_start.
        """
        self._is_open = False
        self.write_buffer = bytearray()
        self.read_buffer = bytearray()
        self.delay = kwargs.get('delay', 0)
        self.auto_start = kwargs.get('auto_start', True)
        if self.auto_start:
            self.start()

    def write(self, data):
        """Write data to the mock interface.

        Args:
            data: Data to write.

        Returns:
            int: Number of bytes written.

        Raises:
            IOError: If interface is not open.
        """
        if not self.is_open():
            raise IOError("Interface not open")
        if self.delay > 0:
            time.sleep(self.delay)
        self.write_buffer.extend(data)
        return len(data)

    def read(self):
        """Read data from the mock interface.

        Returns:
            bytes: Data read from the interface.

        Raises:
            IOError: If interface is not open.
        """
        if not self.is_open():
            raise IOError("Interface not open")
        if self.delay > 0:
            time.sleep(self.delay)
        data = bytes(self.read_buffer)
        self.read_buffer.clear()
        return data

    def start(self):
        """Start the mock interface."""
        self._is_open = True

    def stop(self):
        """Stop the mock interface."""
        self._is_open = False

    def is_open(self):
        """Check if the mock interface is open.

        Returns:
            bool: True if open, False otherwise.
        """
        return self._is_open


class TestMockInterface(unittest.TestCase):
    """Test cases for the MockInterface implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.interface = MockInterface()

    def test_initial_state(self):
        """Test the initial state of the interface."""
        self.assertTrue(self.interface.is_open())
        self.assertEqual(len(self.interface.write_buffer), 0)
        self.assertEqual(len(self.interface.read_buffer), 0)

    def test_write_read(self):
        """Test basic write and read operations."""
        test_data = b"test data"
        self.interface.read_buffer = bytearray(test_data)

        # Test write
        written = self.interface.write(test_data)
        self.assertEqual(written, len(test_data))
        self.assertEqual(self.interface.write_buffer, test_data)

        # Test read
        read_data = self.interface.read()
        self.assertEqual(read_data, test_data)
        self.assertEqual(len(self.interface.read_buffer), 0)  # Buffer should be cleared after read

    def test_interface_lifecycle(self):
        """Test start/stop lifecycle."""
        self.assertTrue(self.interface.is_open())
        self.interface.stop()
        self.assertFalse(self.interface.is_open())
        self.interface.start()
        self.assertTrue(self.interface.is_open())

    def test_write_when_closed(self):
        """Test write operation when interface is closed."""
        self.interface.stop()
        with self.assertRaises(IOError):
            self.interface.write(b"data")

    def test_read_when_closed(self):
        """Test read operation when interface is closed."""
        self.interface.stop()
        with self.assertRaises(IOError):
            self.interface.read()

    def test_destructor(self):
        """Test that the interface is properly closed when destroyed."""
        interface = MockInterface()
        self.assertTrue(interface.is_open())
        del interface  # This should call __del__ which calls stop()
        # Can't directly test this as the object is gone, but we can check the mock


class TestInterfaceErrorConditions(unittest.TestCase):
    """Test error conditions and edge cases for the interface."""

    def test_large_data(self):
        """Test with large amounts of data."""
        large_data = b'x' * (1024 * 1024)  # 1MB of data
        interface = MockInterface()
        written = interface.write(large_data)
        self.assertEqual(written, len(large_data))
        self.assertEqual(interface.write_buffer, large_data)

    def test_slow_interface(self):
        """Test with simulated slow interface."""
        interface = MockInterface(delay=0.1)
        start_time = time.time()
        interface.write(b"test")
        elapsed = time.time() - start_time
        self.assertGreaterEqual(elapsed, 0.1)

    def test_partial_read_write(self):
        """Test partial reads and writes."""
        interface = MockInterface()
        test_data = b"partial data"

        # Write partial data
        written = interface.write(test_data[:5])
        self.assertEqual(written, 5)

        # Write remaining data
        written = interface.write(test_data[5:])
        self.assertEqual(written, len(test_data[5:]))

        # Verify complete data was written
        self.assertEqual(interface.write_buffer, test_data)


class TestInterfaceErrorHandling(unittest.TestCase):
    """Test error handling in interface implementations."""

    def test_serial_read_timeout(self):
        """Test serial interface read timeout handling."""
        with patch('serial.Serial') as mock_serial:
            mock_serial.return_value.read.side_effect = serial.SerialTimeoutException("Timeout")
            interface = LNetSerial(port="COM1")
            interface.start()
            with self.assertRaises(IOError):
                interface.read()

    def test_serial_write_error(self):
        """Test serial interface write error handling."""
        with patch('serial.Serial') as mock_serial:
            mock_serial.return_value.write.side_effect = serial.SerialException("Write failed")
            interface = LNetSerial(port="COM1")
            interface.start()
            with self.assertRaises(IOError):
                interface.write(b"test")

    def test_tcp_connection_error(self):
        """Test TCP/IP connection error handling."""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.connect.side_effect = ConnectionRefusedError("Connection refused")
            with self.assertRaises(ConnectionError):
                LNetTcpIp(host="invalid.host").start()


class TestCANInterface(unittest.TestCase):
    """Test cases for the CAN interface implementation."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the can.interface.Bus
        self.mock_bus_patcher = patch('can.interface.Bus')
        self.mock_bus = self.mock_bus_patcher.start()
        self.mock_bus_instance = MagicMock()
        self.mock_bus.return_value = self.mock_bus_instance
        self.mock_bus_instance._is_shutdown = False

    def tearDown(self):
        """Tear down test fixtures."""
        self.mock_bus_patcher.stop()

    def test_can_initialization(self):
        """Test CAN interface initialization."""
        interface = LNetCan(
            bustype='pcan_usb',
            channel=1,
            baud_rate=500000,
            id_tx=0x100,
            id_rx=0x101
        )
        self.assertEqual(interface.bustype, 'pcan_usb')
        self.assertEqual(interface.channel, 'PCAN_USBBUS1')
        self.assertEqual(interface.bitrate, 500000)
        self.assertEqual(interface.can_id_tx, 0x100)
        self.assertEqual(interface.can_id_rx, 0x101)

    def test_can_start(self):
        """Test starting the CAN interface."""
        interface = LNetCan(bustype='pcan_usb', channel=1)
        interface.start()
        self.assertTrue(interface.is_open())
        self.mock_bus.assert_called_once()

    def test_can_stop(self):
        """Test stopping the CAN interface."""
        interface = LNetCan(bustype='pcan_usb', channel=1)
        interface.start()
        interface.stop()
        self.mock_bus_instance.shutdown.assert_called_once()

    def test_can_write(self):
        """Test writing data to CAN interface."""
        interface = LNetCan(bustype='pcan_usb', channel=1)
        interface.start()

        # Create test data
        test_data = bytearray([0x55, 0x04, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06])

        # Write data
        interface.write(test_data)

        # Verify that CAN messages were sent
        self.assertTrue(self.mock_bus_instance.send.called)

    def test_can_read(self):
        """Test reading data from CAN interface."""
        interface = LNetCan(bustype='pcan_usb', channel=1, id_rx=0x101)
        interface.start()

        # Create mock CAN messages
        mock_message = MagicMock()
        mock_message.arbitration_id = 0x101
        mock_message.data = bytearray([8, 0x55, 0x04, 0x01, 0x02, 0x03, 0x04])  # Length + data

        # Second message with remaining data
        mock_message2 = MagicMock()
        mock_message2.arbitration_id = 0x101
        mock_message2.data = bytearray([0x05, 0x06])

        # Mock recv to return our test messages
        self.mock_bus_instance.recv.side_effect = [mock_message, mock_message2, None]

        # Read data
        data = interface.read()

        # Verify data was read
        self.assertIsInstance(data, bytearray)
        self.assertTrue(self.mock_bus_instance.recv.called)

    def test_can_write_fragmentation(self):
        """Test that large frames are fragmented correctly."""
        interface = LNetCan(bustype='pcan_usb', channel=1, id_tx=0x100)
        interface.start()

        # Create large test data (more than 7 bytes to force fragmentation)
        test_data = bytearray(range(20))

        # Write data
        interface.write(test_data)

        # Verify multiple CAN messages were sent
        call_count = self.mock_bus_instance.send.call_count
        self.assertGreater(call_count, 1, "Large data should be fragmented into multiple messages")

    def test_can_default_parameters(self):
        """Test CAN interface with default parameters (PCAN USB)."""
        interface = LNetCan()
        self.assertEqual(interface.bustype, 'pcan_usb')
        self.assertEqual(interface.channel, 'PCAN_USBBUS1')
        self.assertEqual(interface.bitrate, 500000)

    def test_can_socketcan(self):
        """Test CAN interface with SocketCAN."""
        interface = LNetCan(bustype='socketcan', channel='can0')
        self.assertEqual(interface.bustype, 'socketcan')
        self.assertEqual(interface.channel, 'can0')

    def test_can_error_handling(self):
        """Test CAN interface error handling."""
        self.mock_bus.side_effect = Exception("CAN initialization failed")
        interface = LNetCan(bustype='pcan_usb', channel=1)

        with self.assertRaises(Exception):
            interface.start()

    def test_can_write_before_start(self):
        """Test writing to CAN before starting."""
        interface = LNetCan(bustype='pcan_usb', channel=1)

        with self.assertRaises(RuntimeError):
            interface.write(bytearray([0x01, 0x02, 0x03]))

    def test_can_read_before_start(self):
        """Test reading from CAN before starting."""
        interface = LNetCan(bustype='pcan_usb', channel=1)

        with self.assertRaises(RuntimeError):
            interface.read()

    def test_can_extra_config(self):
        """Test that extra configuration is passed to python-can."""
        interface = LNetCan(
            bustype='pcan',
            channel='PCAN_USBBUS1',
            receive_own_messages=True,  # Extra config
            fd=True  # Extra config
        )
        interface.start()

        # Verify that extra config was passed
        call_kwargs = self.mock_bus.call_args[1]
        self.assertTrue('receive_own_messages' in call_kwargs)
        self.assertTrue('fd' in call_kwargs)

    def test_can_channel_conversion_pcan_usb(self):
        """Test channel number conversion for PCAN USB."""
        interface = LNetCan(bustype='pcan_usb', channel=1)
        self.assertEqual(interface.channel, 'PCAN_USBBUS1')

        interface = LNetCan(bustype='pcan_usb', channel=2)
        self.assertEqual(interface.channel, 'PCAN_USBBUS2')

    def test_can_channel_conversion_pcan_lan(self):
        """Test channel number conversion for PCAN LAN."""
        interface = LNetCan(bustype='pcan_lan', channel=1)
        self.assertEqual(interface.channel, 'PCAN_LANBUS1')

        interface = LNetCan(bustype='pcan_lan', channel=2)
        self.assertEqual(interface.channel, 'PCAN_LANBUS2')

    def test_can_channel_conversion_socketcan(self):
        """Test channel number conversion for SocketCAN (0-indexed)."""
        interface = LNetCan(bustype='socketcan', channel=1)
        self.assertEqual(interface.channel, 'can0')

        interface = LNetCan(bustype='socketcan', channel=2)
        self.assertEqual(interface.channel, 'can1')

    def test_can_channel_conversion_vector(self):
        """Test channel number conversion for Vector (0-indexed string)."""
        interface = LNetCan(bustype='vector', channel=1)
        self.assertEqual(interface.channel, '0')

        interface = LNetCan(bustype='vector', channel=2)
        self.assertEqual(interface.channel, '1')

    def test_can_channel_conversion_kvaser(self):
        """Test channel number conversion for Kvaser (0-indexed integer)."""
        interface = LNetCan(bustype='kvaser', channel=1)
        self.assertEqual(interface.channel, 0)

        interface = LNetCan(bustype='kvaser', channel=2)
        self.assertEqual(interface.channel, 1)

    def test_can_bustype_mapping(self):
        """Test that our bustype names are mapped to python-can's expected names."""
        # Test pcan_usb -> pcan
        interface = LNetCan(bustype='pcan_usb', channel=1)
        interface.start()
        call_kwargs = self.mock_bus.call_args[1]
        self.assertEqual(call_kwargs['bustype'], 'pcan')

        # Test pcan_lan -> pcan
        interface = LNetCan(bustype='pcan_lan', channel=1)
        interface.start()
        call_kwargs = self.mock_bus.call_args[1]
        self.assertEqual(call_kwargs['bustype'], 'pcan')

    def test_can_mode_standard(self):
        """Test standard CAN ID mode (11-bit)."""
        interface = LNetCan(bustype='pcan_usb', channel=1, mode='standard')
        self.assertFalse(interface.is_extended_id)

    def test_can_mode_extended(self):
        """Test extended CAN ID mode (29-bit)."""
        interface = LNetCan(bustype='pcan_usb', channel=1, mode='extended')
        self.assertTrue(interface.is_extended_id)

        # Test alternative names
        interface = LNetCan(bustype='pcan_usb', channel=1, mode='ext')
        self.assertTrue(interface.is_extended_id)

        interface = LNetCan(bustype='pcan_usb', channel=1, mode='29bit')
        self.assertTrue(interface.is_extended_id)

    def test_can_baud_rate_parameter(self):
        """Test baud_rate parameter."""
        interface = LNetCan(bustype='pcan_usb', channel=1, baud_rate=250000)
        self.assertEqual(interface.bitrate, 250000)

        # Test different baud rates
        interface = LNetCan(bustype='pcan_usb', channel=1, baud_rate=1000000)
        self.assertEqual(interface.bitrate, 1000000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
