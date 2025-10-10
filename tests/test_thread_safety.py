"""
Test suite to verify threading.Lock() functionality in LNet class.

This test verifies that the threading lock in the _xchg_data method
prevents race conditions when multiple threads access the interface simultaneously.
"""

import threading
import time
import unittest
from unittest.mock import Mock, MagicMock

from mchplnet.lnet import LNet
from mchplnet.interfaces.abstract_interface import InterfaceABC


class MockInterface(InterfaceABC):
    """Mock interface for testing thread safety."""

    def __init__(self, delay=0.01):
        """Initialize mock interface with configurable delay.

        Args:
            delay (float): Simulated delay for read/write operations in seconds.
        """
        self.delay = delay
        self.write_count = 0
        self.read_count = 0
        self.concurrent_access_count = 0
        self.max_concurrent_access = 0
        self.access_lock = threading.Lock()
        self.call_order = []
        self._is_open = True  # Track if the interface is open

    def start(self):
        """Start the interface."""
        self._is_open = True

    def stop(self):
        """Stop the interface."""
        self._is_open = False

    def is_open(self):
        """Check if the interface is open."""
        return self._is_open

    def write(self, data):
        """Simulate write operation with delay to detect concurrent access."""
        with self.access_lock:
            self.concurrent_access_count += 1
            self.max_concurrent_access = max(self.max_concurrent_access, self.concurrent_access_count)
            self.call_order.append(('write_start', threading.current_thread().name))

        # Simulate work being done (this is where race conditions would occur)
        time.sleep(self.delay)
        self.write_count += 1

        with self.access_lock:
            self.call_order.append(('write_end', threading.current_thread().name))
            self.concurrent_access_count -= 1

    def read(self):
        """Simulate read operation with delay to detect concurrent access."""
        with self.access_lock:
            self.concurrent_access_count += 1
            self.max_concurrent_access = max(self.max_concurrent_access, self.concurrent_access_count)
            self.call_order.append(('read_start', threading.current_thread().name))

        # Simulate work being done
        time.sleep(self.delay)
        self.read_count += 1

        with self.access_lock:
            self.call_order.append(('read_end', threading.current_thread().name))
            self.concurrent_access_count -= 1

        # Return mock device info response for handshake
        return bytearray(b'\x00' * 100)

    def close(self):
        """Close the interface."""
        pass


class TestLNetThreading(unittest.TestCase):
    """Test cases for LNet threading lock functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_interface = MockInterface(delay=0.05)
        # Disable handshake for most tests
        self.lnet = LNet(self.mock_interface, handshake=False)
        # Mock device_info to bypass handshake requirement
        self.lnet.device_info = Mock()
        self.lnet.device_info.uc_width = 2

    def test_lock_prevents_concurrent_access(self):
        """Test that the lock prevents concurrent access to _xchg_data."""
        num_threads = 10
        threads = []
        results = []

        def call_xchg_data(thread_id):
            """Call _xchg_data and record the result."""
            try:
                result = self.lnet._xchg_data(bytearray(b'test_data'))
                results.append((thread_id, 'success', result))
            except Exception as e:
                results.append((thread_id, 'error', str(e)))

        # Create and start multiple threads
        for i in range(num_threads):
            thread = threading.Thread(target=call_xchg_data, args=(i,), name=f'Thread-{i}')
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)

        # Verify all threads completed successfully
        self.assertEqual(len(results), num_threads, "Not all threads completed")

        # Verify that concurrent access never exceeded 1
        self.assertEqual(
            self.mock_interface.max_concurrent_access,
            1,
            f"Lock failed: max concurrent access was {self.mock_interface.max_concurrent_access}, expected 1"
        )

        # Verify all operations completed
        self.assertEqual(self.mock_interface.write_count, num_threads)
        self.assertEqual(self.mock_interface.read_count, num_threads)

    def test_lock_serializes_operations(self):
        """Test that operations are properly serialized by the lock."""
        num_threads = 5
        threads = []

        def call_xchg_data():
            """Call _xchg_data."""
            self.lnet._xchg_data(bytearray(b'test'))

        # Create and start threads
        for i in range(num_threads):
            thread = threading.Thread(target=call_xchg_data, name=f'Thread-{i}')
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)

        # Verify that write/read operations are properly paired
        call_order = self.mock_interface.call_order

        # Check that operations don't interleave
        i = 0
        while i < len(call_order):
            if i + 3 < len(call_order):
                # Each complete operation should be: write_start, write_end, read_start, read_end
                self.assertEqual(call_order[i][0], 'write_start')
                self.assertEqual(call_order[i + 1][0], 'write_end')
                self.assertEqual(call_order[i + 2][0], 'read_start')
                self.assertEqual(call_order[i + 3][0], 'read_end')
                # All four operations should be from the same thread
                thread_name = call_order[i][1]
                self.assertEqual(call_order[i + 1][1], thread_name)
                self.assertEqual(call_order[i + 2][1], thread_name)
                self.assertEqual(call_order[i + 3][1], thread_name)
                i += 4
            else:
                break

    def test_lock_with_multiple_methods(self):
        """Test that the lock works correctly when different methods call _xchg_data."""
        num_threads = 5
        threads = []

        def call_get_ram():
            """Call get_ram which internally uses _xchg_data."""
            try:
                self.lnet.get_ram(0x1000, 4)
            except Exception:
                pass  # We're testing thread safety, not functionality

        def call_put_ram():
            """Call put_ram which internally uses _xchg_data."""
            try:
                self.lnet.put_ram(0x2000, 4, bytearray(b'\x00\x01\x02\x03'))
            except Exception:
                pass

        # Create mixed threads
        for i in range(num_threads):
            if i % 2 == 0:
                thread = threading.Thread(target=call_get_ram, name=f'GetRam-{i}')
            else:
                thread = threading.Thread(target=call_put_ram, name=f'PutRam-{i}')
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)

        # Verify no concurrent access occurred
        self.assertEqual(
            self.mock_interface.max_concurrent_access,
            1,
            "Lock failed with multiple method calls"
        )

    def test_lock_releases_on_exception(self):
        """Test that the lock is released even if an exception occurs."""
        # Create an interface that raises an exception
        error_interface = MockInterface()
        error_interface.read = Mock(side_effect=RuntimeError("Simulated error"))

        lnet_with_error = LNet(error_interface, handshake=False)
        lnet_with_error.device_info = Mock()

        # First call should raise an exception
        with self.assertRaises(RuntimeError):
            lnet_with_error._xchg_data(bytearray(b'test'))

        # Second call should still work (lock was released)
        error_interface.read = Mock(return_value=bytearray(b'response'))
        result = lnet_with_error._xchg_data(bytearray(b'test'))
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)