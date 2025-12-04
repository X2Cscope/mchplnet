"""TCP/IP interface implementation for LNet protocol."""
import logging
import socket

from mchplnet.interfaces.abstract_interface import Interface


class LNetTcpIp(Interface):
    """LNet TCP/IP interface implementation (placeholder)."""
    def is_open(self):
        """Check if the TCP/IP interface is open."""
        pass

    def start(self):
        """Start the TCP/IP interface."""
        try:
            with self.socket as s:
                s.connect((self.host, self.port))
        except TimeoutError as e:
            logging.debug(e)

    def stop(self):
        """Stop the TCP/IP interface."""
        pass

    def __init__(self, *args, **kwargs):
        """Initialize the TCP/IP interface."""
        self.port = int(kwargs["port"]) if "port" in kwargs else 12666
        self.host = kwargs["host"] if "host" in kwargs else "localhost"
        self.timeout = kwargs["timeout"] if "timeout" in kwargs else 2
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)

    def write(self, data):
        """Write data to the TCP/IP interface."""
        self.socket.sendall(data)

    def read(self):
        """Read data from the TCP/IP interface."""
        self.socket.recv(64)
