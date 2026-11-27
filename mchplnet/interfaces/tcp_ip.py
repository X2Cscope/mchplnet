"""TCP/IP interface implementation for LNet protocol."""
import logging
import socket

from mchplnet.framing import LNetFrameAssembler
from mchplnet.interfaces.abstract_interface import Interface


class LNetTcpIp(Interface):
    """LNet TCP/IP interface implementation (placeholder)."""

    def is_open(self):
        """Check if the TCP/IP interface is open."""
        return self.socket.fileno() != -1

    # Connection attempts in start() if the device resets the connection during the connection test
    CONNECT_ATTEMPTS = 2

    def start(self) -> bool:
        """Start the TCP/IP interface: connect and run the connection test (LNet handshake).

        Some lwIP-based devices reset (TCP RST) the first connection after their own reset, while they
        still resolve the host's MAC address; the next connection works. Therefore the connection is
        opened once more if the device resets it during the connection test.

        Raises:
            ValueError: If the device cannot be reached (connect or handshake timeout).
            ConnectionError: If the device also resets the second connection.
        """
        for attempt in range(1, self.CONNECT_ATTEMPTS + 1):
            try:
                self._assembler.reset()  # no stale bytes from a previous connection
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)
                self.socket.connect((self.host, self.port))
                return super().start()
            except TimeoutError as e:
                self.stop()
                logging.debug(e)
                raise ValueError("No connection to LNet TCP/IP interface, is the IP address correct?") from e
            except ConnectionError as e:
                self.stop()
                if attempt == self.CONNECT_ATTEMPTS:
                    raise
                logging.warning("LNet TCP/IP: connection to %s:%s reset by the device (%s), reconnecting",
                                self.host, self.port, type(e).__name__)
        return False

    def stop(self):
        """Stop the TCP/IP interface."""
        if self.socket:
            self.socket.close()
        self.socket = None

    def __init__(self, *args, **kwargs):
        """Initialize the TCP/IP interface."""
        super().__init__(*args, **kwargs)
        self.port = int(kwargs["tcp_port"]) if "tcp_port" in kwargs else 12666
        self.host = kwargs["host"] if "host" in kwargs else "localhost"
        self.timeout = kwargs["timeout"] if "timeout" in kwargs else 0.05
        self.socket = None
        self._assembler = LNetFrameAssembler()

    def write(self, data):
        """Write data to the TCP/IP interface."""
        self.socket.sendall(data)

    def read(self):
        """Read the next complete LNet frame from the TCP/IP interface.

        A TCP segment may contain part of a frame or several frames (e.g. stream frames pushed by the
        device). Bytes after the returned frame are kept for the next call.

        Returns:
            bytearray: Raw frame (SYN … checksum, including fill bytes).

        Raises:
            TimeoutError: If no data arrives within the socket timeout.
            ConnectionError: If the device closed the connection.
        """
        frame = self._assembler.pop_frame()
        while frame is None:
            chunk = self.socket.recv(4096)  # raises TimeoutError (socket.timeout) after self.timeout
            if not chunk:
                raise ConnectionError("LNet TCP/IP connection closed by the device")
            self._assembler.feed(chunk)
            frame = self._assembler.pop_frame()
        return frame
