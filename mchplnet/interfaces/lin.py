"""LIN interface implementation for LNet protocol."""

from mchplnet.interfaces.abstract_interface import Interface


class LNetLin(Interface):
    """LNet LIN interface implementation (placeholder)."""
    def is_open(self):
        """Check if the LIN interface is open."""
        pass

    def start(self):
        """Start the LIN interface."""
        pass

    def stop(self):
        """Stop the LIN interface."""
        pass

    def __init__(self, *args, **kwargs):
        """Initialize the LIN interface."""
        pass

    def write(self, data):
        """Write data to the LIN interface."""
        pass

    def read(self):
        """Read data from the LIN interface."""
        pass
