import logging
from pylnet.lnetframe import LNetFrame
from pylnet.services.device_info import DeviceInfo

class FrameDeviceInfo(LNetFrame):
    def __init__(self):
        """
        This frame is responsible for Hand-Shake, Monitor-Version, Identifying processor Type, Application Version,
        """
        super().__init__()
        self.service_id = 0

    def _get_data(self) -> list:
        """
        Provides the value of the variable defined by the user.
        @return: list
        """
        return [self.service_id]

    def _uc_id(self, uC_id: int = 0):
        """
        Maps the microcontroller ID to the corresponding value.
        """
        _uC_id = {
            16: 2,  # Mapping 16-bit microcontroller ID to value 2
            32: 4   # Mapping 32-bit microcontroller ID to value 4
        }
        try:
            __uC_id = _uC_id[uC_id]
        except IndexError:
            logging.error("Unknown Microcontroller")
            logging.error("Valid microcontrollers are: {} ".format(_uC_id.keys()))
            return
        return _uC_id[uC_id]

    @staticmethod
    def hand_shake(device_info: int) -> bool:
        """
        Checks if the device info is 0 (indicating successful handshake).
        """
        if device_info == 0:
            return True
        return False


    def processor_id(self,data):
        """
        """
        print(data)
        value1 = int(data[10], 16)
        value2 = int(data[11], 16)

        # Combine the values
        result = (value2 << 8) | value1

        print("result",hex(result))


    def _deserialize(self, received: bytearray):
        """
        Deserializes the received data and extracts relevant information.
        """
        self.received = received
        device_info = int(self.received[3], 16)  # Checking if the service id is correct
        if not self.hand_shake(device_info):
            return
        monitor_id = int(self.received[5], 16)
        app_ver_id = int(self.received[7], 16)
        uc_id_data = int(self.received[10], 16)
        dsp_state = int(self.received[38], 16)

        DeviceInfo.appVer = self._app_ver(app_ver_id)
        DeviceInfo.monitorVer = self._monitor_ver(monitor_id)
        DeviceInfo.width = self._uc_id(uc_id_data)  # Returning the width for the address setup in get ram and put ram
        DeviceInfo.monitorDate = self._monitor_date(self.received)
        DeviceInfo.dsp_state = self._dsp_state(dsp_state)
        DeviceInfo.processorID = self.processor_id(self.received)
        return DeviceInfo

    def _app_ver(self, data):
        """
        Returns the application version.
        """
        return data

    def _monitor_ver(self, data):
        """
        Returns the monitor version.
        """
        return data

    def _monitor_date(self, data):
        """
        Extracts and converts monitor date and time from the received data.
        """
        monitor_date_time = []
        for i in range(12, 21):
            monitor_date_time.append(int(self.received[i], 16))
        ascii_chars = [chr(ascii_val) for ascii_val in monitor_date_time]
        return ''.join(ascii_chars)

    def _dsp_state(self, data):
        """
        Returns the DSP state as a descriptive string.
        """
        dsp_state = {
            0x00: "MONITOR - Monitor runs on target but no application",
            0x01: "APPLICATION LOADED - Application runs on target (X2C Update function is being executed)",
            0x02: "IDLE - Application is idle (X2C Update Function is not being executed)",
            0x03: "INIT - Application is initializing and usually changes to state 'IDLE' after being finished",
            0x04: "APPLICATION RUNNING - POWER OFF - Application is running with disabled power electronics",
            0x05: "APPLICATION RUNNING - POWER ON - Application is running with enabled power electronics"
        }

        return dsp_state.get(data, "Unknown DSP State")

