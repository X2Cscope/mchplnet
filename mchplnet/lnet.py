import logging

from mchplnet.interfaces.abstract_interface import InterfaceABC
from mchplnet.services.frame_device_info import DeviceInfo, FrameDeviceInfo
from mchplnet.services.frame_getram import FrameGetRam
from mchplnet.services.frame_load_parameter import (FrameLoadParameter,
                                                    LoadScopeData)
from mchplnet.services.frame_putram import FramePutRam
from mchplnet.services.frame_save_parameter import (FrameSaveParameter,
                                                    ScopeSetup)


class LNet:
    """
    LNet is a class that handles the LNet logic and services for communication with a microcontroller.

    it provides methods to perform interface handshake, retrieve device information, save scope configuration
    parameters, load scope parameters, read and write data to the microcontroller RAM.

    attributes:
        interface (InterfaceABC): The interface used for communication.
        load_parameter (LoadScopeData): Loaded scope parameters.
        device_info (DeviceInfo): Device information retrieved during the handshake.

    methods:
        __init__(interface: InterfaceABC, handshake: bool = True):
            Initialize the LNet instance.

        interface_handshake():
            Perform the interface handshake and retrieve device information.

        scope_save_parameter(scope_config: ScopeConfiguration) -> Response:
            Save scope configuration parameters to the microcontroller.

        load_parameters() -> LoadScopeData:
            Load scope parameters from the microcontroller.

        get_ram(address: int, size: int) -> bytearray:
            Read data from the microcontroller RAM.

        put_ram(address: int, size: int, value: bytes) -> Response:
            Write data to the microcontroller RAM.

    raises:
        RuntimeError: If device information is not retrieved before certain operations.

    example:
        # Create an instance of LNet with a serial interface
        serial_interface = LNetSerial(port="COM1", baud_rate=115200)
        lnet = LNet(serial_interface)
        lnet.interface_handshake()
        lnet.scope_save_parameter(scope_config)
    """

    def __init__(self, interface: InterfaceABC, handshake: bool = True):
        """
        initialize the LNet instance.

        args:
            interface (InterfaceABC): The interface to communicate with.
            handshake (bool, optional): Perform interface handshake if True. defaults to True.

        returns:
            None
        """
        self.load_parameter = None
        self.interface = interface
        self.device_info = None
        self.scope_setup = ScopeSetup()
        if handshake:
            self._handshake()  # Perform interface handshake if requested

    def _handshake(self):
        """
        Retrieve from microcontroller the device_info and load_parameter frames

        Raises:
            RuntimeError: If device information is not retrieved successfully.
        """
        try:
            self.get_device_info()
            self.load_parameters()
        except Exception as e:
            logging.error(e)
            RuntimeError("Failed to retrieve device information.")

    def get_device_info(self) -> DeviceInfo:
        """
        Load from the microcontroller and return a DeviceInfo dataclass.

        Returns:
            DeviceInfo
        """
        if not self.device_info:
            device_info = FrameDeviceInfo()
            device_info.received = self._read_data(device_info.serialize())
            self.device_info = device_info.deserialize()
        return self.device_info

    def _check_device_info(self):
        if self.device_info is None:
            RuntimeError("DeviceInfo is not initialized. Call get_device_info() first.")

    def save_parameter(self):
        """
        Save scope configuration parameters to the microcontroller.

        Args:
            scope_config (ScopeSetup): Scope configuration parameters.

        Returns:
            Response: Response from the MCU.

        Raises:
            RuntimeError: If device information is not retrieved before saving parameters.
        """
        self._check_device_info()
        frame_save_param = FrameSaveParameter()
        frame_save_param.set_scope_setup(self.scope_setup)
        frame_save_param.received = self._read_data(frame_save_param.serialize())
        return frame_save_param.deserialize()

    def load_parameters(self) -> LoadScopeData:
        """
        Load scope parameters from the microcontroller.

        Returns:
            LoadScopeData: Loaded scope parameters.

        Raises:
            RuntimeError: If device information is not retrieved before loading parameters.
        """
        self._check_device_info()
        frame_load_param = FrameLoadParameter()
        frame_load_param.received = self._read_data(frame_load_param.serialize())
        self.load_parameter = frame_load_param.deserialize()
        return self.load_parameter

    def get_ram_array(self, address: int, bytes_to_read: int, data_type: int):
        self._check_device_info()
        get_ram_frame = FrameGetRam(
            address, bytes_to_read, data_type, self.device_info.uc_width
        )  # Pass self.device_info as an argument
        get_ram_frame.received = self._read_data(get_ram_frame.serialize())
        array = get_ram_frame.deserialize()
        return array

    def get_ram(self, address: int, data_type: int) -> bytearray:
        """
        read data from the microcontroller RAM.

        args:
            address (int): The address to read from the microcontroller RAM.
            data_type (int): The number of bytes to read from the microcontroller RAM.

        returns:
            bytearray: The bytes read from the microcontroller RAM.

        raises:
            RuntimeError: If device information is not retrieved before reading RAM.
        """
        bytes_to_read = data_type

        self._check_device_info()
        get_ram_frame = FrameGetRam(
            address, bytes_to_read, data_type, self.device_info.uc_width
        )
        get_ram_frame.received = self._read_data(get_ram_frame.serialize())
        return get_ram_frame.deserialize()

    def put_ram(self, address: int, size: int, value: bytearray):
        """
        write data to the microcontroller RAM.

        args:
            address (int): The address to write to the microcontroller RAM.
            size (int): The number of bytes to write to the microcontroller RAM.
            value (bytes): The bytes to write to the microcontroller RAM.

        returns:
            Response: Response from the MCU.

        raises:
            RuntimeError: If device information is not retrieved before writing RAM.
        """
        self._check_device_info()
        put_ram_frame = FramePutRam(address, size, self.device_info.uc_width, value)
        put_ram_frame.received = self._read_data(put_ram_frame.serialize())
        return put_ram_frame.deserialize()

    def _read_data(self, frame):
        """
        Write the frame to the interface and read the response.

        Args:
            frame: The frame to be sent.

        Returns:
            Response: The response from the MCU.
        """
        self.interface.write(frame)
        return self.interface.read()

    def get_scope_setup(self) -> ScopeSetup:
        """
        Returns the ScopeSetup instance

        Any channel to be monitored or triggered must be handled
        through this instance of Scope Setup.
        """
        return self.scope_setup
