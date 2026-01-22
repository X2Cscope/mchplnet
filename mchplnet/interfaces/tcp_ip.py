"""TCP/IP interface implementation for LNet protocol."""
import logging
import socket

from mchplnet.interfaces.abstract_interface import Interface
from mchplnet.lnetframe import LNET_FRAME_SIZE_IDX, LNET_FILL_BYTE_1, LNET_FILL_BYTE_2


class LNetTcpIp(Interface):
    """LNet TCP/IP interface implementation (placeholder)."""

    def is_open(self):
        """Check if the TCP/IP interface is open."""
        pass

    def start(self):
        """Start the TCP/IP interface."""
        try:
            self.socket.connect((self.host, self.port))
        except TimeoutError as e:
            logging.debug(e)

    def stop(self):
        """Stop the TCP/IP interface."""
        self.socket.close()

    def __init__(self, *args, **kwargs):
        """Initialize the TCP/IP interface."""
        self.port = int(kwargs["port"]) if "port" in kwargs else 12666
        self.host = kwargs["host"] if "host" in kwargs else "localhost"
        self.timeout = kwargs["timeout"] if "timeout" in kwargs else 0.1
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)

    def write(self, data):
        """Write data to the TCP/IP interface."""
        self.socket.sendall(data)

    def read(self):
        """Read data from the TCP/IP interface."""
        data = bytearray()
        # try:
        #     while True:
        #         chunk = self.socket.recv(1024)
        #         print("chunk read:", len(chunk))
        #         if not chunk:  # Connection closed
        #             break
        #         data.extend(chunk)
        # except socket.timeout:
        #     pass  # No more data available
        # return data

        # Read initial 4 bytes (SYN, SIZE, NODE, SERVICE_ID)
        counter = 0
        read_size = 4
        while counter < read_size:
            chunk = self.socket.recv(1024)
            print("chunk read:", len(chunk))
            for byte in chunk:
                data.append(byte)
                counter += 1
                if counter == 1:
                    pass
                elif counter == LNET_FRAME_SIZE_IDX:
                    read_size = data[1] + read_size
                elif byte in (LNET_FILL_BYTE_1, LNET_FILL_BYTE_2):
                    read_size += 1
        return data
