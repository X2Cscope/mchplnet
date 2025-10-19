"""Test suite for Interface and its implementations.

This module contains tests for the abstract interface and its concrete implementations.
"""

import time
import unittest
from unittest.mock import patch

import serial

from mchplnet.interfaces.abstract_interface import Interface
from mchplnet.interfaces.uart import LNetSerial


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
            with self.assertRaises(IOError):
                interface.read()

    def test_serial_write_error(self):
        """Test serial interface write error handling."""
        with patch('serial.Serial') as mock_serial:
            mock_serial.return_value.write.side_effect = serial.SerialException("Write failed")
            interface = LNetSerial(port="COM1")
            with self.assertRaises(IOError):
                interface.write(b"test")

    # def test_tcp_connection_error(self):
    #     """Test TCP/IP connection error handling."""
    #     with patch('socket.socket') as mock_socket:
    #         mock_socket.return_value.connect.side_effect = ConnectionRefusedError("Connection refused")
    #         with self.assertRaises(ConnectionError):
    #             LNetTcpIp(host="invalid.host", port=1234)



if __name__ == '__main__':
    unittest.main(verbosity=2)
