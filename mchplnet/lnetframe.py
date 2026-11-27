"""LNet frame serialization and deserialization implementation."""

import logging
from abc import ABC, abstractmethod

from mchplnet.errors import LNetDeviceError, LNetFrameError, error_description, service_name

# LNet protocol constants
LNET_SYN_BYTE = 0x55  # Frame synchronization byte
LNET_FILL_BYTE_1 = 0x55  # First fill byte marker
LNET_FILL_BYTE_2 = 0x02  # Second fill byte marker
LNET_SYN_BYTE_DECIMAL = 85  # SYN byte in decimal (0x55)

# LNet frame counter positions
LNET_FRAME_SIZE_IDX = 3  # Position in frame counter when SIZE field is read
LNET_MIN_FRAME_LENGTH = 2  # Minimum frame length (data + CRC)
LNET_MIN_RESPONSE_LENGTH = 6  # SYN, SIZE, NODE, Service ID, Error ID, CRC
LNET_RESPONSE_HEADER = 3  # SYN, SIZE, NODE (bytes not counted by SIZE)


class LNetFrame(ABC):
    """LNetFrame is an abstract base class that implements the structure of LNet frames.

    LNet frames consist of several parts, including SYN, SIZE, NODE, DATA, and CRC.
    the SYN byte indicates the start of a frame and is always 0x55.
    the SIZE byte
    represents the number of data bytes in the frame.
    the NODE byte identifies the
    target slave node.
    the DATA area contains the frame's data, and the CRC byte is
    used for error checking.

    Attributes:
        received (bytearray): The received frame data.
        service_id (int): The Service ID identifying the type of service.
        __syn (int): The SYN byte value (always 0x55).
        __node (int): The NODE byte value (default is 1).
        data (list): The data part of the frame.
        crc (int): The calculated CRC value for the frame.

    Methods:
        _get_data(self) -> list:
            Abstract method to be implemented by subclasses.
            returns the data part of the frame.

        serialize(self) -> bytearray:
            Serialize the frame and add SYN, SIZE, NODE, DATA, and CRC bytes.

        _crc_checksum(self, list_crc) -> int:
            Calculate a checksum from the contents of a list.

        _fill_bytes(self, frame) -> list:
            Handle reserved key values (0x55 and 0x02) in SIZE, NODE, or DATA areas.

        _crc_check(self, received) -> int:
            Check the CRC of the received frame.

        frame_integrity(self) -> bool:
            Check the integrity of the received frame by verifying the CRC.

        _check_id(self) -> bool:
            Check the Service ID and error status in the received frame.

        remove_fill_byte(self):
            Remove fill bytes (0x00) from the received frame.

        _deserialize(self, received):
            Abstract method to be implemented by subclasses.
            deserialize the frame data.

        error_id(error_id) -> str:
            Get the error description based on the error ID.

        deserialize(self, received) -> None or object:
            Save the parameters and check for errors in the received frame.
    """

    def __init__(self):
        """Initialize an LNetFrame instance."""
        self.received = None
        self.service_id = None
        self.__syn = LNET_SYN_BYTE_DECIMAL
        self.__node = 1
        self.data = []  # data

    @abstractmethod
    def _get_data(self):
        """Append service payload to the member class self.data.

        This method is called by LNetFrame serialize method retrieving specific information from the subclass
        specialization. When this method is called, self.data is empty and the service needs to append its own
        data to the data member class
        """
        pass

    def serialize(self):
        """Serialize the frame by setting up SYN, SIZE, NODE, DATA, and CRC bytes.

        Returns:
            bytearray: Serialized frame.
        """
        self.data.clear()  # clear the data array
        self._get_data()  # Get data from the subclass (actual service)
        frame_size = len(self.data)  # Get the length of the data frame
        self.data[:0] = [self.__syn, frame_size, self.__node]  # prepend frame bytes
        self._add_fill_byte_and_crc()
        return bytearray(self.data)

    def _add_fill_byte_and_crc(self):
        """Handle reserved key values 0x55 and 0x02 in SIZE, NODE, or DATA areas.

        If any of these key values occur within SIZE, NODE, or DATA area, a 0x00 'fill_bytes'
        will be added, which will not be counted as data size and not be used in checksum calculation.
        """
        result = [self.data[0]]
        crc_sum = 0x55 # SYN

        for byte_val in self.data[1:]:
            result.append(byte_val)
            crc_sum += byte_val
            if byte_val in (LNET_FILL_BYTE_1, LNET_FILL_BYTE_2):
                result.append(0x00)  # Fill byte not counted in CRC

        # Calculate and handle checksum inversion in one step
        # Checksum 0x55 => 0xAA   85 => 170
        # Checksum 0x02 => 0xFD   02 => 253
        crc = crc_sum % 256
        if crc in (LNET_FILL_BYTE_1, LNET_FILL_BYTE_2):
            crc = (~crc) & 0xFF
        result.append(crc)
        self.data = result

    def frame_integrity(self) -> bool:
        """Check the integrity of the received frame by verifying the CRC.

        Returns:
            bool: True if the frame integrity check passes, False otherwise.
        """
        if len(self.received) < LNET_MIN_FRAME_LENGTH:  # Need at least data + CRC
            return False

        received = self.received
        fill_bytes = (LNET_FILL_BYTE_1, LNET_FILL_BYTE_2)
        result = [received[0]]
        crc_sum = received[0]
        i = 1
        while i < len(received) - 1:
            byte_val = received[i]
            result.append(byte_val)
            crc_sum += byte_val
            if byte_val in fill_bytes:
                i += 2  # Skip the next byte
            else:
                i += 1

        calculated_crc = crc_sum % 256
        if calculated_crc in fill_bytes:
            calculated_crc = (~calculated_crc) & 0xFF

        crc_error = calculated_crc != received[-1]
        self.received = bytearray(result)
        return crc_error

    @abstractmethod
    def _deserialize(self):
        """Deserialize the frame data stored on class member 'received'.

        Returns: None or object: Deserialize frame for the respected service ID and provide required Data or None if
        there are errors.
        """
        pass

    def _check_frame_protocol(self):
        """Check the Service ID and error status in the received frame.

        Returns:
            bool: True if the Service ID and error status are valid, False otherwise.
        """
        return self.received[3] == self.service_id and self.received[4] == 0

    def _check_frame_length(self):
        """Check that the received frame (fill bytes and checksum removed) is complete and consistent.

        Raises:
            LNetFrameError: If the frame is shorter than a response header or SIZE does not match.
        """
        if len(self.received) < LNET_MIN_RESPONSE_LENGTH - 1:
            raise LNetFrameError(f"Response to service {service_name(self.service_id)} too short: "
                                 f"{bytes(self.received).hex()}")
        if self.received[1] != len(self.received) - LNET_RESPONSE_HEADER:
            raise LNetFrameError(f"Response to service {service_name(self.service_id)}: SIZE {self.received[1]} "
                                 f"does not match {len(self.received) - LNET_RESPONSE_HEADER} data bytes")

    def _raise_protocol_error(self):
        """Raise the exception matching the Service ID and Error ID of the received frame.

        Raises:
            LNetFrameError: If the response belongs to another service (e.g. a late response).
            LNetDeviceError: If the device answered with an error ID.
        """
        if self.received[3] != self.service_id:
            raise LNetFrameError(f"Expected response to service {service_name(self.service_id)}, "
                                 f"received service {service_name(self.received[3])}")
        raise LNetDeviceError(self.service_id, self.received[4])

    def deserialize(self):
        """Check the response frame and return the service data.

        Returns:
            object: Deserialized service data, depending on the service.

        Raises:
            LNetFrameError: On checksum error, incomplete frame, SIZE mismatch or unexpected Service ID.
            LNetDeviceError: If the device answered with an error ID.
        """
        if self.received is None or len(self.received) < LNET_MIN_RESPONSE_LENGTH:
            raise LNetFrameError(f"Response to service {service_name(self.service_id)} too short: "
                                 f"{bytes(self.received or b'').hex()}")
        raw = bytes(self.received)
        if self.frame_integrity():
            raise LNetFrameError(f"Checksum error in response to service {service_name(self.service_id)}: "
                                 f"{raw.hex()}")
        self._check_frame_length()
        if not self._check_frame_protocol():
            self._raise_protocol_error()
        return self._deserialize()

    @staticmethod
    def get_error_id(error_id: int):
        """Get the error description based on the error ID.

        Args:
            error_id (int): Error ID.

        Returns:
            str: Error description; "Unknown error ID 0x.." for IDs not defined by LNet.
        """
        return error_description(error_id)


if __name__ == "__main__":
    logging.debug("Elf_parser.__name__")
