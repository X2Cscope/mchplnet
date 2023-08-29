import logging

from mchplnet.interfaces.abstract_interface import InterfaceABC
from mchplnet.services.frame_device_info import DeviceInfo, FrameDeviceInfo
from mchplnet.services.frame_getram import FrameGetRam
from mchplnet.services.frame_load_parameter import FrameLoadParameter, LoadScopeData
from mchplnet.services.frame_putram import FramePutRam
from mchplnet.services.frame_save_parameter import (
    FrameSaveParameter,
    ScopeChannel,
    ScopeConfiguration,
    ScopeTrigger,
)


class LNet(object):
    """Handle the LNet logic and services"""

    def __init__(self, interface: InterfaceABC, handshake: bool = True):
        self.load_parameter = None
        self.interface = interface
        self.device_info = None
        if handshake:
            self.interface_handshake()  # Perform interface_handshake if requested

    def interface_handshake(self):
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

    def save_paramater(self, scope_config: ScopeConfiguration):
        if self.device_info is None:
            raise RuntimeError("Device width is not set. Call device_info() first.")
        frame_save_param = FrameSaveParameter()
        frame_save_param.set_scope_configuration(scope_config)
        response = self._read_data(frame_save_param.serialize())
        logging.debug(response)
        response = frame_save_param.deserialize(response)

        return response

    def load_parameters(self) -> LoadScopeData:
        """

        :return: ScopeData
        """
        if self.device_info is None:
            raise RuntimeError("Device width is not set. Call device_info() first.")
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
        handles Get RAM service-id.
        address: int - The address to read from the microcontroller RAM
        size: int - The number of bytes to read from the microcontroller RAM

        returns: bytearray - The bytes read from the microcontroller RAM
        """
        if self.device_info is None:
            raise RuntimeError("Device width is not set. Call device_info() first.")
        get_ram_frame = FrameGetRam(
            address, size, self.device_info.uc_width
        )  # Pass self.device_info as an argument
        # self.ser.write(get_ram_frame.serialize())

        response = self._read_data(get_ram_frame.serialize())
        response = get_ram_frame.deserialize(response)
        return response

    def put_ram(self, address: int, size: int, value: bytes):
        """
        handles the Put RAM service-id.
        address: int - The address to write to the microcontroller RAM
        size: int - The number of bytes to write to the microcontroller RAM
        value: bytes - The bytes to write to the microcontroller RAM
        """
        if self.device_info is None:
            raise RuntimeError("Device width is not set. Call device_info() first.")
        put_ram_frame = FramePutRam(
            address, size, self.device_info.uc_width, value
        )  # Pass self.device_info as an argument
        # self.ser.write(put_ram_frame.serialize())

        response = self._read_data(put_ram_frame.serialize())
        response = put_ram_frame.deserialize(response)
        return response

    def _read_data(self, frame):
        self.interface.write(frame)
        return self.interface.read()
