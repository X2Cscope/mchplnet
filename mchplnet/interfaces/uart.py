"""UART/Serial interface implementation for LNet protocol."""

import logging
import warnings

import serial

from mchplnet.interfaces.abstract_interface import Interface
from mchplnet.lnetframe import LNET_FILL_BYTE_1, LNET_FILL_BYTE_2

# LNet frame counter positions
FRAME_COUNTER_SIZE_POSITION = 3  # Position in frame counter when SIZE field is read


class LNetSerial(Interface):
    r"""A class representing a serial communication interface for the LNet framework.

    This class implements the Interface interface for serial communication.

    Attributes:
        com_port (str): The serial port name.
        baud_rate (int): The baud rate of the communication (bits per second).
        parity (int): The parity setting for serial communication.
        stop_bit (int): The number of stop bits.
        data_bits (int): The number of data bits.
        serial (serial.Serial): The serial communication object.

    Methods:
        __init__(\\*args, \\*\\*kwargs):
            Constructor for the LNetSerial class. Initializes serial communication with the provided settings.

        start():
            Set up the serial communication with the provided settings.

        stop():
            Close the serial communication.

        write(data):
            Write data to the serial port.

        is_open() -> bool:
            Check if the serial port is open and operational.

        read() -> list:
            Read data from the serial port.

    Raises:
        ValueError: If the provided serial settings are invalid.
    """

    def __init__(self, *args, **kwargs):
        r"""Constructor for the LNetSerial class. Initializes serial communication with the provided settings.

        Args:
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Keyword Args:
            port (str, optional): Serial port name. Defaults to "COM1".
            baud_rate (int, optional): Baud rate (bits per second). Defaults to 115200.
            parity (int, optional): Parity setting. Defaults to 0.
            stop_bit (int, optional): Number of stop bits. Defaults to 1.
            data_bits (int, optional): Number of data bits. Defaults to 8.

        Returns:
            None
        """
        if "port" not in kwargs:
            warnings.warn("No port provided, using default COM1", Warning)
        self.com_port = kwargs["port"] if "port" in kwargs else "COM1"
        self.baud_rate = kwargs["baud_rate"] if "baud_rate" in kwargs else 115200
        self.parity = kwargs["parity"] if "parity" in kwargs else 0
        self.stop_bit = kwargs["stop_bit"] if "stop_bit" in kwargs else 1
        self.data_bits = kwargs["data_bits"] if "data_bits" in kwargs else 8
        self.serial = None
        self.start()

    def start(self):
        """Set up the serial communication with the provided settings.

        Parity, stop bits, and data bits are converted from integer values to their respective constants.
        Initializes the serial communication object.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError: If the provided serial settings are invalid.
        """
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

        try:
            self.serial = serial.Serial(
                port=self.com_port,
                baudrate=self.baud_rate,
                parity=parity_value,
                stopbits=stop_bits_value,
                bytesize=data_bits_value,
                write_timeout=1,
                timeout=1,
            )
        except Exception as e:
            logging.debug(e)

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
        response_list = bytearray()
        if self.serial:
            counter = 0
            read_size = 4
            while counter < read_size:
                byte = ord(self.serial.read())
                response_list.append(byte)
                counter += 1
                if counter == 1:
                    pass
                elif counter == FRAME_COUNTER_SIZE_POSITION:
                    read_size = response_list[1] + read_size
                elif byte in (LNET_FILL_BYTE_1, LNET_FILL_BYTE_2):
                    read_size += 1
        return response_list
