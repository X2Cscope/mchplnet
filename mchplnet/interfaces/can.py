"""CAN interface implementation for LNet protocol."""

from mchplnet.interfaces.abstract_interface import Interface


class LNetCan(Interface):
    """LNet CAN interface implementation (placeholder)."""
    def is_open(self):
        """Check if the CAN interface is open."""
        pass

    def start(self):
        """Start the CAN interface."""
        pass

    def stop(self):
        """Stop the CAN interface."""
        pass

    def __init__(self, *args, **kwargs):
        """Initialize the CAN interface."""
        pass

    def write(self, data):
        """Write data to the CAN interface."""
        pass

    def read(self):
        """Read data from the CAN interface."""
        pass
