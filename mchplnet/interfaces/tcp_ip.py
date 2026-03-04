"""TCP/IP interface implementation for LNet protocol."""
import logging
import socket

from mchplnet.interfaces.abstract_interface import Interface
from mchplnet.lnetframe import LNET_FILL_BYTE_1, LNET_FILL_BYTE_2


class LNetTcpIp(Interface):
    """LNet TCP/IP interface implementation (placeholder)."""

    def is_open(self):
        """Check if the TCP/IP interface is open."""
        return self.socket.fileno() != -1

    def start(self):
        """Start the TCP/IP interface."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
        except TimeoutError as e:
            self.stop()
            logging.debug(e)

    def stop(self):
        """Stop the TCP/IP interface."""
        if self.socket:
            self.socket.close()
        self.socket = None

    def __init__(self, *args, **kwargs):
        """Initialize the TCP/IP interface."""
        self.port = int(kwargs["tcp_port"]) if "tcp_port" in kwargs else 12666
        self.host = kwargs["host"] if "host" in kwargs else "localhost"
        self.timeout = kwargs["timeout"] if "timeout" in kwargs else 0.1
        self.socket = None

    def write(self, data):
        """Write data to the TCP/IP interface."""
        self.socket.sendall(data)

    def read(self):
        """Read data from the TCP/IP interface."""
        # LNET Frame (SYN, SIZE, NODE, SERVICE_ID, DATA, CRC)
        # SIZE contains the number of DATA bytes
        # Read initial 2 bytes (SYN, SIZE)
        size = 2
        fill_bytes = (LNET_FILL_BYTE_1, LNET_FILL_BYTE_2)
        data = bytearray()

        while size:
            chunk = self.socket.recv(size)
            data.extend(chunk)
            size -= len(chunk)

        size = data[1] + 2 # NODE, SERVICE_ID, CRC
        size += 1 if data[1] in fill_bytes else 0

        while size:
            chunk = self.socket.recv(1024)
            for byte in chunk:
                data.append(byte)
                size -= 0 if byte in fill_bytes else 1
        return data
