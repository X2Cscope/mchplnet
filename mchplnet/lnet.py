import logging
from mchplnet.interfaces.abstract_interface import InterfaceABC
from mchplnet.services.frame_device_info import DeviceInfo, FrameDeviceInfo
from mchplnet.services.frame_getram import FrameGetRam
from mchplnet.services.frame_load_parameter import FrameLoadParameter, LoadScopeData
from mchplnet.services.frame_putram import FramePutRam
from mchplnet.services.frame_save_parameter import (
    FrameSaveParameter,
    ScopeConfiguration,
)

class LNet(object):
    """
    LNet is a class that handles the LNet logic and services for communication with a microcontroller.

    It provides methods to perform interface handshake, retrieve device information, save scope configuration
    parameters, load scope parameters, read and write data to the microcontroller RAM.

    Attributes:
        interface (InterfaceABC): The interface used for communication.
        load_parameter (LoadScopeData): Loaded scope parameters.
        device_info (DeviceInfo): Device information retrieved during the handshake.

    Methods:
        __init__(interface: InterfaceABC, handshake: bool = True):
            Initialize the LNet instance.

        interface_handshake():
            Perform the interface handshake and retrieve device information.

        save_parameter(scope_config: ScopeConfiguration) -> Response:
            Save scope configuration parameters to the microcontroller.

        load_parameters() -> LoadScopeData:
            Load scope parameters from the microcontroller.

        get_ram(address: int, size: int) -> bytearray:
            Read data from the microcontroller RAM.

        put_ram(address: int, size: int, value: bytes) -> Response:
            Write data to the microcontroller RAM.

    Raises:
        RuntimeError: If device information is not retrieved before certain operations.

    Example:
        # Create an instance of LNet with a serial interface
        serial_interface = LNetSerial(port="COM1", baud_rate=115200)
        lnet = LNet(serial_interface)
        lnet.interface_handshake()
        lnet.save_parameter(scope_config)
    """

    def __init__(self, interface: InterfaceABC, handshake: bool = True):
        """
        Initialize the LNet instance.

        Args:
            interface (InterfaceABC): The interface to communicate with.
            handshake (bool, optional): Perform interface handshake if True. Defaults to True.

        Returns:
            None
        """
        self.load_parameter = None
        self.interface = interface
        self.device_info = None
        if handshake:
            self.interface_handshake()  # Perform interface handshake if requested

    def interface_handshake(self):
        """
        Perform the interface handshake and retrieve device information.

        This method sends a handshake request to the microcontroller and retrieves device information.

        Returns:
            DeviceInfo: Device information.

        Raises:
            RuntimeError: If device information is not retrieved successfully.
        """
        try:
            if self.device_info is None:  # Check if width is already set
                device_info = FrameDeviceInfo()
                response = self._read_data(device_info.serialize())
                self.device_info = device_info.deserialize(response)
                self.load_parameter = self.load_parameters()

            return DeviceInfo(
                monitorVer=self.device_info.monitorVer,
                appVer=self.device_info.appVer,
                processorID=self.device_info.processorID,
                uc_width=self.device_info.uc_width,
                dsp_state=self.device_info.dsp_state,
                monitorDate=self.device_info.monitorDate,
                appDate=self.device_info.appDate,
            )
        except Exception as e:
            logging.error(e)
            RuntimeError("Failed to retrieve device information.")

    def save_parameter(self, scope_config: ScopeConfiguration):
        """
        Save scope configuration parameters to the microcontroller.

        Args:
            scope_config (ScopeConfiguration): Scope configuration parameters.

        Returns:
            Response: Response from the MCU.

        Raises:
            RuntimeError: If device information is not retrieved before saving parameters.
        """
        if self.device_info is None:
            RuntimeError("Device width is not set. Call device_info() first.")
        frame_save_param = FrameSaveParameter()
        frame_save_param.set_scope_configuration(scope_config)
        response = self._read_data(frame_save_param.serialize())
        logging.debug(response)
        # response = frame_save_param.deserialize(response)

        return response

    def load_parameters(self) -> LoadScopeData:
        """
        Load scope parameters from the microcontroller.

        Returns:
            LoadScopeData: Loaded scope parameters.

        Raises:
            RuntimeError: If device information is not retrieved before loading parameters.
        """
        if self.device_info is None:
            RuntimeError("Device width is not set. Call device_info() first.")
        frame_load_param = FrameLoadParameter()
        response = self._read_data(frame_load_param.serialize())
        extracted_data = frame_load_param.deserialize(response)
        return LoadScopeData(
            scope_state=extracted_data.scope_state,
            num_channels=extracted_data.num_channels,
            sample_time_factor=extracted_data.sample_time_factor,
            data_array_pointer=extracted_data.data_array_pointer,
            data_array_address=extracted_data.data_array_address,
            trigger_delay=extracted_data.trigger_delay,
            trigger_event_position=extracted_data.trigger_event_position,
            data_array_used_length=extracted_data.data_array_used_length,
            data_array_size=extracted_data.data_array_size,
            scope_version=extracted_data.scope_version,
        )

    def get_ram(self, address: int, size: int) -> bytearray:
        """
        Read data from the microcontroller RAM.

        Args:
            address (int): The address to read from the microcontroller RAM.
            size (int): The number of bytes to read from the microcontroller RAM.

        Returns:
            bytearray: The bytes read from the microcontroller RAM.

        Raises:
            RuntimeError: If device information is not retrieved before reading RAM.
        """
        if self.device_info is None:
            RuntimeError("Device width is not set. Call device_info() first.")
        get_ram_frame = FrameGetRam(
            address, size, self.device_info.uc_width
        )  # Pass self.device_info as an argument
        response = self._read_data(get_ram_frame.serialize())
        response = get_ram_frame.deserialize(response)
        return response

    def put_ram(self, address: int, size: int, value: bytes):
        """
        Write data to the microcontroller RAM.

        Args:
            address (int): The address to write to the microcontroller RAM.
            size (int): The number of bytes to write to the microcontroller RAM.
            value (bytes): The bytes to write to the microcontroller RAM.

        Returns:
            Response: Response from the MCU.

        Raises:
            RuntimeError: If device information is not retrieved before writing RAM.
        """
        if self.device_info is None:
            RuntimeError("Device width is not set. Call device_info() first.")
        put_ram_frame = FramePutRam(address, size, self.device_info.uc_width, value)
        response = self._read_data(put_ram_frame.serialize())
        response = put_ram_frame.deserialize(response)
        return response

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
