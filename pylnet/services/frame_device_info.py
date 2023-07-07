import logging
from pylnet.pylnet.lnetframe import LNetFrame


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

    def uc_id(self, uC_id: int = 0):
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

        data_received = int(self.received[10], 16)

        self.processor_id(data_received) # processor id 16 or 32 bit

        return self.uc_id(data_received) # returning the width for the address setup in get ram and put ram

    # LOG_FILENAME = "Frame_device_info.log"
#
# logging.basicConfig(
#     level=logging.NOTSET,
#     filename=LOG_FILENAME,
#     format="%(asctime)s %(levelname)s %(name)s %(message)s",
# )
# # handler = logging._handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=5)
# try:
#     serial_setup = serial.Serial(port="COM4", baudrate=115200)
#     request_string = b'\x55\x01\x01\x00\x57'
#     serial_setup.write(request_string)
#     responseList = []
#
#     counter = 0
#     i = 0
#     readSize = 4
#     while i < readSize:
#         responseList.append(serial_setup.read().hex())
#         counter += 1
#         if counter == 3:
#             # print(responseList[1])
#             readSize = int(responseList[1], 16) + readSize
#
#         i += 1
#     # print(responseList)
#     logging.info(len(responseList))
#     # print(len(responseList))
#
#     if responseList[3] == '00':  # Service ID for device info
#         logging.info(int(responseList[10], 16))
#         logging.debug(True)
#     else:
#         logging.debug(False)
#     if responseList[10] == '10':
#         logging.debug('its a 16 bit microcontroller')
#     if responseList[10] == '20':
#         logging.debug('Its a 32 bit microcontroller')
#     logging.debug(responseList)
#
# except Exception as e:
#     logging.error(e)
