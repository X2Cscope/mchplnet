import logging

from mchplnet.lnetframe import LNetFrame


class FramePutRam(LNetFrame):
    """
    FramePutRam is responsible for setting up the request frame for MCU to 'Set' the variable value.
    """

    def __init__(self, address: int, size: int, width: int, value: bytearray = None):
        """
        initialize the FramePutRam instance.

        args:
            address (int): Address of the variable.
            size (int): Size of the variable.
            value (bytearray, optional): Value to set on the defined variable in bytes.
            width (int): Width according to the type of microcontroller.
        """
        super().__init__()
        if value is None:
            value = []
        self.value_dataType = width
        self.service_id = 10
        self.address = address
        self.size = size
        self.user_value = value

    def _get_data(self):
        byte_address = self.address.to_bytes(length=self.value_dataType, byteorder="little")
        self.data.extend([self.service_id, *byte_address, self.size, *self.user_value])

    def set_all(self, address: int, size: int, value: bytearray) -> None:
        """
        set all parameters of the frame.

        args:
            address (int): Address of the variable.
            size (int): Size of the variable.
            value (bytearray): Value to set on the defined variable in bytes.
        """
        self.address = address
        self.size = size
        self.user_value = value

    def set_size(self, size: int):
        """
        Set the size of the variable for the LNET frame for getRamBlock.

        Args:
            size (int): Size of the variable.
        """
        self.size = size

    def get_size(self) -> int:
        """
        Get the size of the variable.

        Returns:
            int: Size of the variable.
        """
        return self.size

    def set_address(self, address: int):
        """
        Set the address of the variable.

        Args:
            address (int): Address of the variable.
        """
        self.address = address

    def get_address(self) -> int:
        """
        Get the address of the variable.

        Returns:
            int: Address of the variable.
        """
        return self.address

    def set_user_value(self, value: int):
        """
        Set the user-defined value for the specific variable.

        Args:
            value (int): User-defined value for the specific variable.
        """
        self.user_value = value

    def get_user_value(self) -> bytearray:
        """
        Get the user-defined value for the specific variable.

        Returns:
            int: User-defined value for the specific variable.
        """
        return self.user_value

    def _deserialize(self, received: bytearray) -> bytearray | None:
        """
        Deserializes the received data and returns an error message if applicable.

        Args:
            received (bytearray): Data received from the MCU.

        Returns:
            bytearray: Error message if an error occurred, None otherwise.
        """
        data_received = int(received[-2], 16)

        if not data_received == 0:
            return
        logging.info("Error_id: {}".format(self.error_id(data_received)))
        return self.error_id(data_received)
