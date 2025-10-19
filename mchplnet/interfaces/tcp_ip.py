"""TCP/IP interface implementation for LNet protocol."""

from mchplnet.interfaces.abstract_interface import Interface


class LNetTcpIp(Interface):
    """LNet TCP/IP interface implementation (placeholder)."""
    def is_open(self):
        """Check if the TCP/IP interface is open."""
        pass

    def start(self):
        """Start the TCP/IP interface."""
        pass

    def stop(self):
        """Stop the TCP/IP interface."""
        pass

    def __init__(self, *args, **kwargs):
        """Initialize the TCP/IP interface."""
        pass

    def write(self, data):
        """Write data to the TCP/IP interface."""
        pass

    def read(self):
        """Read data from the TCP/IP interface."""
        pass
