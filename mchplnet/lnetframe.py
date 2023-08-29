import logging

logger = logging.getLogger(__name__)
from abc import ABC, abstractmethod


# noinspection PyTypeChecker
class LNetFrame(ABC):
    """
    Implements frame structure

    SYN SIZE NODE DATA CRC
    SYN
    Size: 1 byte
    Indicates the start of a frame. This byte is always 0x55.
    The value 0x02 is also reserved for future purposes. These 2 reserved values must be
    specially treated if they occur in any other frame area than in SYN. (see 3.6)

    SIZE: 1 byte
    The number of data bytes.
    Optional fill-bytes (see 3.6) will not be added to SIZE.

    Slave NODE ID
    Size: 1 byte
    Identifies the slave to which the master wants to send the frame.
    The master sets this byte to the slave ID it wants to communicate with, and the slave sets
    this byte to its own ID when responding to the master.

    DATA - Implemented by subclasses
    Size: up to 255 bytes
    Contain the data. The data area is also divided into several parts. Master and slave use
    different data structures.

        Master data structure (request frame)
        Data byteNameDescription
        0 Service IDIdentifies which service will be used
        1 ... nService data(optional) service data
    """

    def __init__(self):
        """
        LNet request and response frame setup dependent on the ServiceId and Size of the variable
        """
        self.received = None
        self.service_id = None
        self.__syn = 85
        self.__node = 1
        self.data = []  # data
        self.crc = None

    @abstractmethod
    def _get_data(self):
        """
        Define interface, job of subclass to implement based on the service type

        Returns:
            list: DATA part of the frame
        """
        pass

    def serialize(self):
        """
        This module sets up the whole request frame with provided Service ID, Symbol_size, and Symbol_address

        [syn, size, node, data, crc] as per LNET doc

        It creates the LNET request frame based on the Service-id

        It also calls the function like _add_setup and crc_checksum.

        Returns:
            bytearray: Serialized frame
        """
        self.data = self._get_data()  # get data from the subclass (actual service)
        frame_size = len(self.data)  # get the length of the data frame

        frame = [self.__syn, frame_size, self.__node, *self.data]
        crc = self._crc_checksum(frame)
        frame = [*frame, crc]
        frame_to_send = self._fill_bytes(frame)

        logger.debug("Serialized frame: {}".format(frame_to_send))

        return bytearray(frame_to_send)

    def _crc_checksum(self, list_crc):
        """
        A checksum is a value that is calculated from the contents of a file or data to detect changes or errors in
        transmission.

        Returns:
            int: Calculated CRC
        """
        sum_of_frame_data = sum(list_crc)  # summing the string (int)

        crc_calculation = sum_of_frame_data % 256  # doing the modulo calculation

        logging.debug("checksum: {}".format(crc_calculation))
        # Checksum 0x55 == 0xAA   85 == 170
        # Checksum 0x02 == 0xFD   02 == 253 (INVERTED)

        if crc_calculation == 85:
            crc_calculation = 170
        elif crc_calculation == 2:
            crc_calculation = 253

        self.crc = crc_calculation  # adding the hex checksum to the list of the data

        logging.debug(
            "Calculated CRC for the frame: {}  Based on: {}".format(self.crc, list_crc)
        )

        return self.crc

    @staticmethod
    def _fill_bytes(frame):
        """
        LNet has 2 reserved key values: 0x55 and 0x02.
        To avoid misinterpretation within SIZE, NODE, DATA or CRC area, these values must be
        differently handled.
        If any of these key values occur within SIZE, NODE, or DATA area, a 0x00'fill_bytes' will be
        added which will not be counted as data size and not be used in checksum calculation.

        Returns:
            list: Frame with fill bytes added
        """
        i = 1
        loop_length = len(frame)
        while i < loop_length:
            if frame[i] == 2 or frame[i] == 85:
                frame.insert(i + 1, 0)
                loop_length += 1
            i += 1
        logger.debug("_fill_bytes assembled frame: {}".format(frame))
        return frame

    def _crc_check(self, received):
        """
        This function helps us to check for the CRC of the request frame

        Args:
            received (bytearray): Received frame

        Returns:
            int: CRC value
        """
        received = list(received)
        received.pop(-1)
        received = [int(x, 16) for x in received]

        return self._crc_checksum(received)

    def frame_integrity(self):
        if self._crc_check(self.received) != int(self.received[-1], 16):
            logging.error(
                "Crc Checksum doesn't match: {}".format(
                    self._crc_checksum(self.received)
                )
            )
            return False
        return True

    @abstractmethod
    def _deserialize(self, received):
        pass

    def _check_id(self):
        if int(self.received[3], 16) == self.service_id:
            if int(self.received[4], 16) == 0:
                logging.debug(self.error_id(int(self.received[4], 16)))
                return True
            elif int(self.received[4], 16) != 0:
                logging.error(self.error_id(int(self.received[4], 16)))
        return False

    def remove_fill_byte(self):
        loop_value = len(self.received)
        z = 1
        while z < loop_value:
            if self.received[z] == "55" or self.received[z] == "02":
                self.received.pop(z + 1)

                loop_value -= 1
                pass
            z += 1
            continue

    def deserialize(self, received):
        """
        This helps us to save the parameters and check for errors in the response frame

        Args:
            received (bytearray): Received frame

        Returns:
            None or object: Deserialized frame or None if there are errors
        """
        self.received = received
        self.remove_fill_byte()
        if self.frame_integrity() and self._check_id():
            return self._deserialize(self.received)

    @staticmethod
    def error_id(error_id):
        _error_id = {
            0: "No Error",
            19: "Checksum Error",
            20: "Format Error",
            21: "Size too large",
            33: "Service not available",
            34: "Invalid DSP state",
            48: "Flash write error",
            49: "Flash write protect error",
            64: "Invalid Parameter ID",
            65: "Invalid Block ID",
            66: "Parameter Limit error",
            67: "Parameter table not initialized",
            80: "Power-on Error",
        }
        try:
            __error_id = _error_id[error_id]
        except IndexError:
            logging.error("Unknown Error")
            logging.error("Valid index numbers are: " + _error_id.keys())
            return
        return _error_id[error_id]


if __name__ == "__main__":
    logging.debug("Elf_parser.__name__")
