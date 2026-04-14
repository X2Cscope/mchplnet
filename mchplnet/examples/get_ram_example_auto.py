"""Example showing auto-detection feature for getting variable values.

This example demonstrates how to use the auto-detection feature to
automatically find the COM port with an LNet device connected.
"""

import logging

from mchplnet.interfaces.factory import InterfaceFactory
from mchplnet.interfaces.factory import InterfaceType as IType
from mchplnet.lnet import LNet

# Configure logging to aid in debugging
logging.basicConfig(level=logging.INFO)

# Create an interface instance with AUTO port detection.
# The system will automatically scan available COM ports and connect to the first one
# that responds to LNet protocol.
print("Starting auto-detection of LNet device...")
interface = InterfaceFactory.get_interface(IType.SERIAL, port="AUTO", baudrate=115200)

# LNet is responsible for managing low-level communication with the microcontroller.
l_net = LNet(interface)

print(f"\nSuccessfully connected to {interface.com_port}")

# Logging various information about the connected device.
print(f"Monitor Date: {l_net.device_info.monitor_date}")
print(f"Processor ID: {l_net.device_info.processor_id}")
print(f"UC Width: {l_net.device_info.uc_width}-bit")
print(f"App Version: {l_net.device_info.app_version}")
print(f"DSP State: {l_net.device_info.dsp_state}")

# Reading a specific memory address from the RAM of the microcontroller.
# Here we provide manually the address and the data type of the variable.
read_bytes = l_net.get_ram(4148, 2)

# Convert the read bytes to an integer for easier interpretation.
# The byte order is specified as 'little-endian'.
value = int.from_bytes(read_bytes, byteorder="little")
print(f"\nValue at address 4148: {value}")

# Close the connection
l_net.interface.stop()
print("\nConnection closed.")
