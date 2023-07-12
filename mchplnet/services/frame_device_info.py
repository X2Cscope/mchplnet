from mchplnet.lnetframe import LNetFrame
from mchplnet.services.device_info import DeviceInfo


class FrameDeviceInfo(LNetFrame):
    def __init__(self):
        """
        This frame is responsible for Hand-Shake, Monitor-Version, Identifying processor Type, Application Version.
        """
        super().__init__()
        self.service_id = 0

    def _get_data(self) -> list:
        """
        provides the value of the variable defined by the user.
        @return: list
        """
        return [self.service_id]

    def _uc_id(self):
        """
        Maps the microcontroller ID to the corresponding value.
        """
        value1 = int(self.received[10], 16)
        value2 = int(self.received[11], 16)

        # Combine the values
        result = hex((value2 << 8) | value1)

        processor_ids_16_bit = {
            "0x8210": "__GENERIC_MICROCHIP_DSPIC__",
            "0x8230": "__GENERIC_MICROCHIP_PIC24__",
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
        }

        processor_ids_32_bit = {
            "0x8110": "__GENERIC_TI_C28X__",
            "0x8220": "__GENERIC_MICROCHIP_PIC32__",
            "0x8320": "__GENERIC_ARM_ARMV6__",
            "0x8310": "__GENERIC_ARM_ARMV7__",
            "0x0241": "__PIC32MZ2048EC__",
            "0x0251": "__PIC32MX170F256__",
        }

        if result in processor_ids_16_bit:
            return 2
        elif result in processor_ids_32_bit:
            return 4
        else:
            return None

    @staticmethod
    def hand_shake(device_info: int) -> bool:
        """
        Checks if the device info is 0 (indicating successful interface_handshake).
        """
        if device_info == 0:
            return True
        return False

    def processor_id(self):
        """ """
        value1 = int(self.received[10], 16)
        value2 = int(self.received[11], 16)

        # Combine the values
        result = hex((value2 << 8) | value1)

        processor_dict = {
            "0x8210": "__GENERIC_MICROCHIP_DSPIC__",
            "0x8220": "__GENERIC_MICROCHIP_PIC32__",
            "0x8230": "__GENERIC_MICROCHIP_PIC24__",
            "0x8310": "__GENERIC_ARM_ARMV7__",
            "0x8320": "__GENERIC_ARM_ARMV6__",
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
        dsp_state = int(self.received[38], 16)

        DeviceInfo.appVer = self._app_ver(app_ver_id)
        DeviceInfo.monitorVer = self._monitor_ver(monitor_id)
        DeviceInfo.width = (
            self._uc_id()
        )  # Returning the width for the address setup in get ram and put ram
        DeviceInfo.monitorDate = self._monitor_date()
        DeviceInfo.dsp_state = self._dsp_state(dsp_state)
        DeviceInfo.processorID = self.processor_id()
        return DeviceInfo

    @staticmethod
    def _app_ver(data):
        """
        Returns the application version.
        """
        return data

    @staticmethod
    def _monitor_ver(data):
        """
        Returns the monitor version.
        """
        return data

    def _monitor_date(self):
        """
        Extracts and converts monitor date and time from the received data.
        """
        monitor_date_time = []
        for i in range(12, 21):
            monitor_date_time.append(int(self.received[i], 16))
        ascii_chars = [chr(ascii_val) for ascii_val in monitor_date_time]
        return "".join(ascii_chars)

    @staticmethod
    def _dsp_state(data):
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
