from pylnet.lnetframe import LNetFrame


class FrameGetRam(LNetFrame):
    def __init__(self, address: int, size: int, width: int):
        """
        Responsible for setting up the request frame for MCU to 'Get' the variable value.
        @param address: Address of the variable
        @param size: Size of the variable
        """
        super().__init__()

        self.service_id = 9
        self.address = address
        self.size = size
        self.width = width

    def _get_data(self) -> list:
        """
        Provides the value of the variable defined by the user.
        @return: List containing the frame data
        """
        byte_address = self.address.to_bytes(length=self.width, byteorder="little")
        data = [*byte_address]

        return [self.service_id, *data, self.size, self.size]

    def _deserialize(self, received):
        """
        Deserializes the received data and returns it as a bytearray.
        @param received: Data received from MCU
        @return: Deserialized bytearray
        """
        self.received = received

        # Check if received data is empty
        if len(received) < 2:
            raise ValueError("Received data is incomplete.")

        # Extract the size of the received data
        size_received_data = int(received[1], 16)

        # Check if received data size is valid
        if size_received_data < 2 or size_received_data > len(received) - 4:
            raise ValueError("Received data size is invalid.")

        # Extract the data bytes
        data_received = received[5 : 5 + size_received_data - 2]

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
        Sets the size of the variable for the LNET frame for getRamBlock.
        @param size: Size of the variable
        """
        self.size = size

    def get_size(self):
        """
        Returns the size of the variable.
        @return: Size of the variable
        """
        return self.size

    def set_address(self, address: int):
        """
        Sets the address of the variable.
        @param address: Address of the variable
        """
        self.address = address

    def get_address(self):
        """
        Returns the address of the variable.
        @return: Address of the variable
        """
        return self.address
