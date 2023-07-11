import logging

from pylnet.lnetframe import LNetFrame


class FramePutRam(LNetFrame):
    def __init__(self, address: int, size: int, width: int, value: bytearray = []):
        """
        responsible for setting up the request frame for MCU to 'Set' the variable value.

        @param address: address of the variable
        @param size: size of the variable
        @param value: value to set on the defined variable in bytes
        @param width: width according to the type of microcontroller
        """
        super().__init__()
        self.width = width
        self.service_id = 10
        self.address = address
        self.size = size
        self.value_user = value

    def _get_data(self) -> list:
        """
        _get_data helps the user to get the data of the variable from the MCU
        @return: list
        """
        byte_address = self.address.to_bytes(length=self.width, byteorder="little")
        add_setup = [*byte_address]
        return [self.service_id, *add_setup, self.size, *self.value_user]

    def set_all(self, address: int, size: int, value: bytearray) -> None:
        """

        @param address: self.address
        @param size: self.size
        @param value: self.value
        """
        self.address = address
        self.size = size
        self.value_user = value

    def set_size(self, size: int) -> object:
        """
        setting size of Variable for the LNET frame for getRamBlock
        @rtype: object
        @param size: int
        """
        self.size = size

    def get_size(self) -> object:
        """
        @return: self.size
        """
        return self.size

    def set_address(self, address: int):
        self.address = address

    def get_address(self):
        """
        @return: self.address
        """
        return self.address

    def set_user_value(self, value: int):
        """

        @param value: user defined value for the specific variable
        """
        self.value_user = value

    def get_user_value(self):
        """
        @return: self.user_value
        """
        return self.value_user

    def _deserialize(self, received: bytearray) -> bytearray:
        data_received = int(self.received[-2], 16)
        if (
            not data_received == 0
        ):  # TODO : check if this is the correct way to return if it is not 0?
            return
        logging.info("Error_id : {}".format(self.error_id(data_received)))
        return self.error_id(data_received)
