"""
FrameGetRam

FrameGetRam enables the function call load parameter of LNet protocol.
"""

from mchplnet.lnetframe import LNetFrame


class FrameGetRam(LNetFrame):
    """
    Class implementation for 'GetRam' frame in the LNet protocol.

    This frame is responsible for setting up the request frame for the MCU to 'Get' the variable value.
    """

    def __init__(self, address: int, data_type: int, size: int, uc_width: int):
        """
        initialize the FrameGetRam instance.

        args:
            address (int): Address of the variable.
            size (int): Size of the variable.
            width (int): Width of the variable (in bytes).
        """
        super().__init__()

        self.service_id = 9
        self.address = address
        self.read_Size = size
        self.uc_width = uc_width
        self.value_dataType = data_type

    def _get_data(self) -> list:
        """
        Get the data to be sent in the frame.

        Returns:
            list: A list containing the frame data.
        """
        byte_address = self.address.to_bytes(length=self.uc_width, byteorder="little")
        data = [*byte_address]

        return [self.service_id, *data, self.read_Size, self.value_dataType]

    def _deserialize(self, received):
        """
        Deserializes the received data and returns it as a bytearray.

        Args:
            received (bytearray): Data received from the MCU.

        Returns:
            bytearray: Deserialized data as a bytearray.

        Raises:
            ValueError: If the received data is incomplete or has an invalid size.
        """
        # Check if received data is empty
        if len(received) < 2:
            raise ValueError("Received data is incomplete.")

        # Extract the size of the received data
        size_received_data = int(received[1], 16)

        # Check if received data size is valid
        if size_received_data < 2 or size_received_data > len(received) - 4:
            raise ValueError("Received data size is invalid.")

        # Extract the data bytes
        data_received = received[5: 5 + size_received_data - 2]

        # Convert the data bytes to a bytearray
        b_array = bytearray()
        for char in data_received:
            try:
                i = int.from_bytes(
                    bytes.fromhex(char), byteorder="little", signed=False
                )
                b_array.append(i)
            except ValueError:
                raise ValueError("Failed to convert data bytes.")

        return b_array

    def set_size(self, size: int):
        """
        Set the size of the variable for the LNET frame for GetRamBlock.

        Args:
            size (int): Size of the variable.
        """
        self.read_Size = size

    def get_size(self):
        """
        Get the size of the variable.

        Returns:
            int: Size of the variable.
        """
        return self.read_Size

    def set_address(self, address: int):
        """
        Set the address of the variable.

        Args:
            address (int): Address of the variable.
        """
        self.address = address

    def get_address(self):
        """
        Get the address of the variable.

        Returns:
            int: Address of the variable.
        """
        return self.address
