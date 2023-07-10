import logging
from pylnet.pylnet.lnetframe import LNetFrame
from pylnet.pylnet.services.device_info import DeviceInfo


class FrameDeviceInfo(LNetFrame):

    def __init__(self):
        """
        This frame is responsible for Hand-Shake, Monitor-Version, Identifying processor Type, Application Version,
        :return

        """
        super().__init__()
        self.service_id = 0

    def _get_data(self) -> list:
        """
        provides the value of the variable defined by the user.
        @return: list
        """

        return [self.service_id]

    def _uc_id(self, uC_id: int = 0):
        _uC_id = {
            16: 2,
            32: 4
        }
        try:
            __uC_id = _uC_id[uC_id]
        except IndexError:
            logging.error("Unknown Microcontroller")
            logging.error("Valid microcontrollers are: {} " .format(_uC_id.keys()))
            return
        return _uC_id[uC_id]

    @staticmethod
    def hand_shake(device_info: int) -> bool:
        if device_info == 0:
            return True
        return False

    @staticmethod
    def processor_id(data_received):
        if data_received == 16:
            print("16 bit microcontroller")
            logging.info('16 bit microcontroller')
        elif data_received == 32:
            print("32 bit microcontroller")
            logging.info('32 bit microcontroller')

    def _deserialize(self, received: bytearray):
        self.received = received
        device_info = int(self.received[3],16) # checking if the service id is correct
        if not self.hand_shake(device_info):
            return
        monitor_id = int(self.received[5], 16)
        app_ver_id = int(self.received[7], 16)
        uc_id_data = int(self.received[10], 16)


        self.processor_id(uc_id_data) # processor id 16 or 32 bit

        DeviceInfo.appVer = self._app_ver(app_ver_id)
        DeviceInfo.monitorVer = self._monitor_ver(monitor_id)
        DeviceInfo.width = self._uc_id(uc_id_data) # returning the width for the address setup in get ram and put ram
        return DeviceInfo

    def _app_ver(self,data):
        return data
    def _monitor_ver(self,data):
        return data