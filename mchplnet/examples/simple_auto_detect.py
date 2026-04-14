"""Simple example of auto-detection feature."""

import logging

from mchplnet.interfaces.uart import LNetSerial
from mchplnet.lnet import LNet

# Enable logging to see the auto-detection process
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Create interface with AUTO (or just don't specify port)
interface = LNetSerial(port="AUTO")

# LNet will auto-detect the correct port
lnet = LNet(interface)

print(f"✓ Connected to {interface.com_port}")
print(f"  Monitor version: {lnet.device_info.monitor_version}")
print(f"  Processor width: {lnet.device_info.uc_width}-bit")

# Clean up
lnet.interface.stop()
