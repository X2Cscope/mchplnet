import serial
from pylnet.pylnet.interfaces.uart import LNetSerial
from pylnet.pylnet.services.frame_getram import FrameGetRam
from pylnet.pylnet.services.frame_putram import FramePutRam
from pylnet.pylnet.services.frame_device_info import FrameDeviceInfo
from pylnet.pylnet.interfaces.abstract_interface import InterfaceABC


class LNet(object):
    """Handle the LNet logic and services"""

    def __init__(self, interface: InterfaceABC, handshake: bool = True):
        self.interface = interface
        self.width = None  # Initialize the width as None
        self.device_info = None
        if handshake:
            self.handshake() # Perform handshake if requested

    def handshake(self):
        if self.width is None:  # Check if width is already set
            device_info = FrameDeviceInfo()
            response = self._read_data(device_info.serialize())
            response = device_info.deserialize(response)
            self.width = response # TODO device_info.width
        return self.width

    def get_ram(self, address: int, size: int) -> bytearray:
        """
        Handles the Get RAM service-id.
        address: int - The address to read from the microcontroller RAM
        size: int - The number of bytes to read from the microcontroller RAM

        Returns: bytearray - The bytes read from the microcontroller RAM
        """
        if self.width is None:
            raise RuntimeError("Device width is not set. Call device_info() first.")
        get_ram_frame = FrameGetRam(address, size, self.width)  # Pass self.width as an argument
        # self.ser.write(get_ram_frame.serialize())

        response = self._read_data(get_ram_frame.serialize())
        response = get_ram_frame.deserialize(response)
        return response

    def put_ram(self, address: int, size: int, value: bytes):
        """
        Handles the Put RAM service-id.
        address: int - The address to write to the microcontroller RAM
        size: int - The number of bytes to write to the microcontroller RAM
        value: bytes - The bytes to write to the microcontroller RAM
        """
        if self.width is None:
            raise RuntimeError("Device width is not set. Call device_info() first.")
        put_ram_frame = FramePutRam(address, size, self.width, value)  # Pass self.width as an argument
        # self.ser.write(put_ram_frame.serialize())

        response = self._read_data(put_ram_frame.serialize())
        response = put_ram_frame.deserialize(response)
        return response

    def _read_data(self, frame):

        self.interface.write(frame)
        return self.interface.read()