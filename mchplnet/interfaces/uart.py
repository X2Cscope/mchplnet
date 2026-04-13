"""UART/Serial interface implementation for LNet protocol."""

import logging
import warnings

import serial
import serial.tools.list_ports

from mchplnet.interfaces.abstract_interface import Interface
from mchplnet.lnetframe import LNET_FILL_BYTE_1, LNET_FILL_BYTE_2


class LNetSerial(Interface):
    r"""A class representing a serial communication interface for the LNet framework.

    This class implements the Interface interface for serial communication.
    Supports automatic COM port detection when port is set to "AUTO" or None.

    Auto-Detection:
        When port="AUTO", the interface automatically:
        - Enumerates all available COM ports on the system
        - Tests each port by opening it with the configured settings
        - Uses the test_connection callback (if set) to validate the connection
        - Connects to the first port that passes validation

    Attributes:
        com_port (str): The serial port name or "AUTO" for auto-detection.
        baud_rate (int): The baud rate of the communication (bits per second).
        parity (int): The parity setting for serial communication.
        stop_bit (int): The number of stop bits.
        data_bits (int): The number of data bits.
        serial (serial.Serial): The serial communication object.

    Methods:
        __init__(\\*args, \\*\\*kwargs):
            Constructor for the LNetSerial class. Initializes serial communication with the provided settings.

        get_available_ports():
            Enumerate all available COM ports on the system.

        start():
            Set up the serial communication. Performs auto-detection if port="AUTO".

        stop():
            Close the serial communication.

        write(data):
            Write data to the serial port.

        is_open() -> bool:
            Check if the serial port is open and operational.

        read() -> bytearray:
            Read data from the serial port with LNet protocol framing.

    Raises:
        ValueError: If the provided serial settings are invalid.
        RuntimeError: If auto-detection fails to find an LNet device.

    Example:
        >>> # Auto-detection
        >>> interface = LNetSerial(port="AUTO", baud_rate=115200)
        >>> lnet = LNet(interface)
        >>> print(f"Connected to {interface.com_port}")

        >>> # Manual port specification
        >>> interface = LNetSerial(port="COM3", baud_rate=115200)
        >>> lnet = LNet(interface)
    """

    def __init__(self, *args, **kwargs):
        r"""Constructor for the LNetSerial class. Initializes serial communication with the provided settings.

        Args:
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Keyword Args:
            port (str, optional): Serial port name. Use "AUTO" or None for auto-detection. Defaults to "AUTO".
            baud_rate (int, optional): Baud rate (bits per second). Defaults to 115200.
            parity (int, optional): Parity setting. Defaults to 0.
            stop_bit (int, optional): Number of stop bits. Defaults to 1.
            data_bits (int, optional): Number of data bits. Defaults to 8.

        Returns:
            None
        """
        super().__init__(*args, **kwargs)
        if "port" not in kwargs:
            warnings.warn("No port provided, will attempt auto-detection", Warning)
        self.com_port = kwargs.get("port", "AUTO")
        if self.com_port == "":
            self.com_port = "AUTO"
        self.baud_rate = kwargs["baud_rate"] if "baud_rate" in kwargs else 115200
        self.parity = kwargs["parity"] if "parity" in kwargs else 0
        self.stop_bit = kwargs["stop_bit"] if "stop_bit" in kwargs else 1
        self.data_bits = kwargs["data_bits"] if "data_bits" in kwargs else 8
        self.serial = None

    def get_available_ports(self):
        """Enumerate all available COM ports on the system.

        Returns:
            list: List of available COM port names (strings).
        """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def start(self) -> bool:
        """Set up the serial communication with the provided settings.

        Parity, stop bits, and data bits are converted from integer values to their respective constants.
        Initializes the serial communication object.
        If port is AUTO and test callback is set, tries all available ports.

        Args:
            None

        Returns:
            bool: True if handshake was performed (AUTO mode), False if manual port (needs handshake).

        Raises:
            ValueError: If the provided serial settings are invalid.
            RuntimeError: If AUTO mode and no valid device found.
        """
        # Check if auto-detection is requested
        if self.com_port is None or self.com_port.upper() == "AUTO":
            available_ports = self.get_available_ports()
            if not available_ports:
                raise RuntimeError("No COM ports available on the system")

            logging.info(f"Auto-detecting LNet device on ports: {available_ports}")

            for port in available_ports:
                self.com_port = port
                logging.debug(f"Trying port {port}...")
                try:
                    self._open_port()
                    if super().start():
                        logging.info(f"Successfully connected to LNet device on {port}")
                        return True
                except Exception as e:
                    logging.debug(f"Port {port} failed: {e}")
                self.stop()

            raise RuntimeError(f"No LNet device found on any available COM port: {available_ports}")
        else:
            self._open_port()
            return super().start()

    def _open_port(self):
        """Open the serial port with configured settings."""
        # Mapping of settings values to serial module constants
        parity_options = {
            0: serial.PARITY_NONE,
            2: serial.PARITY_EVEN,
            3: serial.PARITY_ODD,
            4: serial.PARITY_SPACE,
            5: serial.PARITY_MARK,
        }
        stop_bits_options = {
            1: serial.STOPBITS_ONE,
            2: serial.STOPBITS_TWO,
            3: serial.STOPBITS_ONE_POINT_FIVE,
        }
        data_bits_options = {
            5: serial.FIVEBITS,
            6: serial.SIXBITS,
            7: serial.SEVENBITS,
            8: serial.EIGHTBITS,
        }

        parity_value = parity_options.get(self.parity)
        stop_bits_value = stop_bits_options.get(self.stop_bit)
        data_bits_value = data_bits_options.get(self.data_bits)

        if None in [parity_value, stop_bits_value, data_bits_value]:
            raise ValueError("Invalid serial settings provided.")

        self.serial = serial.Serial(
            port=self.com_port,
            baudrate=self.baud_rate,
            parity=parity_value,
            stopbits=stop_bits_value,
            bytesize=data_bits_value,
            write_timeout=1,
            timeout=1,
        )

    def stop(self):
        """Close the serial communication.

        Args:
            None

        Returns:
            None
        """
        if self.serial:
            self.serial.close()

    def write(self, data):
        """Write data to the serial port.

        Args:
            data: The data to be written to the serial port.

        Returns:
            None
        """
        if self.serial:
            self.serial.write(data)

    def is_open(self) -> bool:
        """Check if the serial port is open and operational.

        Args:
            None

        Returns:
            bool: True if the serial port is open, False otherwise.
        """
        return self.serial.is_open if self.serial else False

    def read(self):
        """Read data from the serial port with LNet protocol framing.

        Returns:
            bytearray: The data read from the serial port.
        """
        # LNET Frame (SYN, SIZE, NODE, SERVICE_ID, DATA, CRC)
        # SIZE contains the number of DATA bytes
        # Read initial 2 bytes (SYN, SIZE)
        size = 2
        fill_bytes = (LNET_FILL_BYTE_1, LNET_FILL_BYTE_2)
        data = bytearray()

        while size:
            byte = ord(self.serial.read())
            data.append(byte)
            size -= 1

        size = data[1] + 2 # NODE, SERVICE_ID, CRC
        size += 1 if data[1] in fill_bytes else 0

        while size:
            byte = ord(self.serial.read())
            data.append(byte)
            size -= 0 if byte in fill_bytes else 1
        return data
