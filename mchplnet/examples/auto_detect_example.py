"""Example demonstrating auto-detection of LNet device on serial port.

This script shows how to use the AUTO port feature to automatically
detect which COM port has an LNet device connected.
"""

import logging

from mchplnet.interfaces.uart import LNetSerial
from mchplnet.lnet import LNet

# Enable logging to see auto-detection process
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_auto_detection():
    """Test auto-detection with no port specified."""
    print("\n=== Test 1: Auto-detection with no port specified ===")
    try:
        # Create interface without specifying port (will default to AUTO)
        interface = LNetSerial()
        lnet = LNet(interface)

        # If we get here, auto-detection succeeded
        device_info = lnet.get_device_info()
        print("✓ Auto-detection successful!")
        print(f"  Connected port: {interface.com_port}")
        print(f"  Monitor version: {device_info.monitor_version}")
        print(f"  Processor width: {device_info.uc_width}-bit")

        lnet.interface.stop()
        return True
    except Exception as e:
        print(f"✗ Auto-detection failed: {e}")
        return False

def test_explicit_auto():
    """Test auto-detection with explicit AUTO parameter."""
    print("\n=== Test 2: Auto-detection with explicit 'AUTO' parameter ===")
    try:
        # Create interface with explicit AUTO
        interface = LNetSerial(port="AUTO")
        lnet = LNet(interface)

        device_info = lnet.get_device_info()
        print("✓ Auto-detection successful!")
        print(f"  Connected port: {interface.com_port}")
        print(f"  Monitor version: {device_info.monitor_version}")

        lnet.interface.stop()
        return True
    except Exception as e:
        print(f"✗ Auto-detection failed: {e}")
        return False

def test_explicit_port():
    """Test with explicit port specification (traditional method)."""
    print("\n=== Test 3: Manual port specification ===")
    try:
        # This will only work if you change COM3 to your actual port
        interface = LNetSerial(port="COM3")
        lnet = LNet(interface)

        device_info = lnet.get_device_info()
        print("✓ Manual connection successful!")
        print(f"  Connected port: {interface.com_port}")
        print(f"  Monitor version: {device_info.monitor_version}")

        lnet.interface.stop()
        return True
    except Exception as e:
        print(f"✗ Manual connection failed: {e}")
        print("  (This is expected if COM3 is not your device port)")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("LNet Serial Port Auto-Detection Example")
    print("=" * 60)

    # Run tests
    test_auto_detection()
    test_explicit_auto()
    test_explicit_port()

    print("\n" + "=" * 60)
    print("Auto-detection feature demonstration complete!")
    print("=" * 60)
