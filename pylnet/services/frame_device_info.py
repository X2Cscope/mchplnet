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
            32: 4,  # Mapping 32-bit microcontroller ID to value 4
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

    def processor_id(self, data):
        """ """
        print(data)
        value1 = int(data[10], 16)
        value2 = int(data[11], 16)

        # Combine the values
        result = hex((value2 << 8) | value1)

        print(type(result))

        processor_dict = {
            "0x8110": "__GENERIC_MICROCHIP_DSPIC__",
            "0x8210": "__GENERIC_MICROCHIP_PIC32__",
            "0x8230": "__GENERIC_MICROCHIP_PIC24__",
            "0x8310": "__GENERIC_ARM_ARMV7__",
            "0x8320": "__GENERIC_ARM_ARMV6__",
            "0x8410": "__GENERIC_X86__",
            "0x8420": "__GENERIC_X64__",
            "0x0111": "__TMS320F2401__",
            "0x0112": "__TMS320F2402__",
            "0x0113": "__TMS320F2403__",
            "0x0114": "__TMS320F2406__",
            "0x0115": "__TMS320F2407__",
            "0x0121": "__TMS320F2801__",
            "0x0122": "__TMS320F2802__",
            "0x0123": "__TMS320F2806__",
            "0x0124": "__TMS320F2808__",
            "0x0125": "__TMS320F2809__",
            "0x0131": "__TMS320F2810__",
            "0x0132": "__TMS320F2811__",
            "0x0133": "__TMS320F2812__",
            "0x0141": "__TMS320F28332__",
            "0x0142": "__TMS320F28334__",
            "0x0143": "__TMS320F28335__",
            "0x0151": "__TMS320F28035__",
            "0x0152": "__TMS320F28034__",
            "0x0161": "__TMS320F28069__",
            "0x0171": "__TM4C123GH6__",
            "0x0172": "__TM4C123BE6__",
            "0x0181": "__TMS320F28027__",
            "0x0221": "__DSPIC33FJ256MC710__",
            "0x0222": "__DSPIC33FJ128MC706__",
            "0x0223": "__DSPIC33FJ128MC506__",
            "0x0224": "__DSPIC33FJ64GS610__",
            "0x0225": "__DSPIC33FJ64GS406__",
            "0x0226": "__DSPIC33FJ12GP202__",
            "0x0228": "__DSPIC33FJ128MC802__",
            "0x0231": "__DSPIC33EP256MC506__",
            "0x0232": "__DSPIC33EP128GP502__",
            "0x0233": "__DSPIC33EP32GP502__",
            "0x0234": "__DSPIC33EP256GP502__",
            "0x0235": "__DSPIC33EP256MC502__",
            "0x0236": "__DSPIC33EP128MC202__",
            "0x0237": "__DSPIC33EP128GM604__",
            "0x0241": "__PIC32MZ2048EC__",
            "0x0251": "__PIC32MX170F256__",
            "0x0311": "__STM32F103VB__",
            "0x0312": "__STM32F103T6__",
            "0x0313": "__STM32F103V8__",
            "0x0314": "__STM32F103T4__",
            "0x0315": "__STM32F103ZC__",
            "0x0321": "__STM32F101C4__",
            "0x0322": "__STM32F101C6__",
            "0x0331": "__STM32F100C6__",
            "0x0341": "__STM32F407ZG__",
            "0x0342": "__STM32F407ZE__",
            "0x0343": "__STM32F407VG__",
            "0x0351": "__STM32F051R8__",
            "0x0352": "__STM32F051C8__",
            "0x0361": "__STM32F303RE__",
            "0x0362": "__STM32F303RB__",
            "0x0411": "__MC56F8XXX__",
            "0x0421": "__MPC5643L__",
            "0x0511": "__RX62T__ or __R5F562TA__",
            "0x0512": "__RX62G__ or __R5F562GA__",
            "0x0611": "__KECONTROL__",
            "0x0711": "__XMC4800F144K2048__",
        }

        return processor_dict.get(result, "Unknown Processor")

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
        DeviceInfo.width = self._uc_id(
            uc_id_data
        )  # Returning the width for the address setup in get ram and put ram
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
        return "".join(ascii_chars)

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
            0x05: "APPLICATION RUNNING - POWER ON - Application is running with enabled power electronics",
        }

        return dsp_state.get(data, "Unknown DSP State")
