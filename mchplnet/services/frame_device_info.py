"""
File: frame_device_info.py
Description: This module defines a custom frame for device information retrieval and interpretation.

This frame is responsible for Hand-Shake, Monitor-Version, Identifying processor Type, and Application Version.
It extracts various parameters related to the device, such as monitor version, application version, processor ID,
monitor date, DSP state, microcontroller width, etc.

Usage:
    - Ensure that the necessary imports from external modules are satisfied.
    - The class `FrameDeviceInfo` inherits from `LNetFrame`, which is not provided in this module.
      Make sure to import the required module or define the `LNetFrame` class to use this module properly.
    - Utilize the `FrameDeviceInfo` class to deserialize received data and retrieve device information.

"""
import logging
from dataclasses import dataclass

from mchplnet.lnetframe import LNetFrame


@dataclass
class DeviceInfo:
    monitorVer: int = 0
    appVer: int = 0
    maxTargetSize = 0
    processorID: int = 0
    monitorDate: int = 0
    monitorTime: int = 0
    appDate: int = 0
    appTime: int = 0
    uc_width: int = 0
    dsp_state: int = 0
    eventType: int = 0
    eventID: int = 0
    tableStructAdd: int = 0


# noinspection PyTypeChecker
class FrameDeviceInfo(LNetFrame):
    """
    Custom frame for device information retrieval and interpretation.
    Inherits from LNetFrame.
    """

    def __init__(self):
        """
        Initialize the FrameDeviceInfo class.
        """
        super().__init__()
        self.service_id = 0

    def _get_data(self):
        self.data.append(self.service_id)

    def _Processor_id(self):
        """
        Maps the microcontroller ID to the corresponding value.

        Returns:
            int: Microcontroller width (2 for 16-bit uc or 4 for 32-bit uc) or None if not recognized.
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
            "0x8220": "__GENERIC_MICROCHIP_PIC32__",
            "0x8320": "__GENERIC_ARM_ARMV6__",
            "0x8310": "__GENERIC_ARM_ARMV7__",
            "0x0241": "__PIC32MZ2048EC__",
            "0x0251": "__PIC32MX170F256__",
        }

        if result in processor_ids_16_bit:
            logging.info(f"Processor is: {processor_ids_16_bit.get(result)} :16-bit")
            DeviceInfo.processorID = processor_ids_16_bit.get(result)
            return 2
        elif result in processor_ids_32_bit:
            logging.info(f"Processor is: {processor_ids_32_bit.get(result)} :32-bit")
            DeviceInfo.processorID = processor_ids_32_bit.get(result)
            return 4
        else:
            logging.error(f"Processor is: Unknown")
            return None

    @staticmethod
    def hand_shake(device_info: int) -> bool:
        """
        Check if the device info indicates a successful handshake.

        Args:
            device_info (int): The device information.

        Returns:
            bool: True if the handshake is successful, False otherwise.
        """
        if device_info == 0:
            return True
        return False

    def _deserialize(self, received: bytearray):
        """
        Deserializes the received data and extracts relevant information.

        Args:
            received (bytearray): The received data.

        Returns:
            DeviceInfo: An instance of DeviceInfo with extracted information.
        """
        self.received = received
        device_info = int(self.received[3], 16)  # Checking if the service id is correct
        if not self.hand_shake(device_info):
            return

        DeviceInfo.appVer = self._app_ver()
        DeviceInfo.monitorVer = self._monitor_ver()
        DeviceInfo.uc_width = (
            self._Processor_id()
        )  # Returning the width for the address setup in get ram and put ram
        DeviceInfo.monitorDate = self._monitor_date()
        DeviceInfo.monitorTime = self._monitor_time()
        DeviceInfo.appDate = self._app_date()
        DeviceInfo.appTime = self._app_time()
        DeviceInfo.dsp_state = self._dsp_state()
        DeviceInfo.eventType = self._event_type()
        DeviceInfo.eventID = self._event_id()
        DeviceInfo.tableStructAdd = self._table_struct_add()

        return DeviceInfo

    def _app_ver(self):
        """
        Get the application version.

        Args:
            data: The application version data.

        Returns:
            data: The application version data.
        """
        appVer = []
        for i in range(7, 9):
            appVer.append(int(self.received[i], 16))
        return int.from_bytes(bytes(appVer), byteorder="little")

    def _monitor_ver(
        self,
    ):
        """
        Get the monitor version.

        Args:
            data: The monitor version data.

        Returns:
            data: The monitor version data.
        """
        monitorVer = []
        for i in range(5, 7):
            monitorVer.append(int(self.received[i], 16))

        return int.from_bytes(bytes(monitorVer), byteorder="little")

    def _monitor_date(self):
        """
        Extract and convert monitor date and time from the received data.

        Returns:
            str: Monitor date and time as a string.
        """
        monitor_date = []
        for i in range(12, 21):
            monitor_date.append(int(self.received[i], 16))
        ascii_chars = [chr(ascii_val) for ascii_val in monitor_date]
        return "".join(ascii_chars)

    def _monitor_time(self):
        """
        Extract and convert monitor date and time from the received data.

        Returns:
            str: Monitor date and time as a string.
        """
        monitor_time = []
        for i in range(21, 25):
            monitor_time.append(int(self.received[i], 16))
        ascii_chars = [chr(ascii_val) for ascii_val in monitor_time]
        return "".join(ascii_chars)

    def _app_date(self):
        """
        Extract and convert monitor date and time from the received data.

        Returns:
            str: Monitor date and time as a string.
        """
        app_date = []
        for i in range(25, 34):
            app_date.append(int(self.received[i], 16))
        ascii_chars = [chr(ascii_val) for ascii_val in app_date]
        return "".join(ascii_chars)

    def _app_time(self):
        """
        Extract and convert monitor date and time from the received data.

        Returns:
            str: Monitor date and time as a string.
        """
        app_time = []
        for i in range(34, 38):
            app_time.append(int(self.received[i], 16))
        ascii_chars = [chr(ascii_val) for ascii_val in app_time]
        return "".join(ascii_chars)

    def _dsp_state(self):
        """
        Get the DSP state as a descriptive string.

        Args:
            data: The DSP state data.

        Returns:
            str: DSP state description or 'Unknown DSP State' if not recognized.
        """
        dsp_state = {
            0x00: "MONITOR - Monitor runs on target but no application",
            0x01: "APPLICATION LOADED - Application runs on target (X2Cscope Update function is being executed)",
            0x02: "IDLE - Application is idle (X2Cscope Update Function is not being executed)",
            0x03: "INIT - Application is initializing and usually changes to state 'IDLE' after being finished",
            0x04: "APPLICATION RUNNING - POWER OFF - Application is running with disabled power electronics",
            0x05: "APPLICATION RUNNING - POWER ON - Application is running with enabled power electronics",
        }

        return dsp_state.get(int(self.received[38], 16), "Unknown DSP State")

    def _event_type(
        self,
    ):
        """
        Get the monitor version.

        Args:
            data: The monitor version data.

        Returns:
            data: The monitor version data.
        """
        eventtype = []
        for i in range(39, 41):
            eventtype.append(int(self.received[i], 16))

        return int.from_bytes(bytes(eventtype), byteorder="little")

    def _event_id(
        self,
    ):
        """
        Get the monitor version.

        Args:
            data: The monitor version data.

        Returns:
            data: The monitor version data.
        """
        eventid = []
        for i in range(41, 45):
            eventid.append(int(self.received[i], 16))

        return int.from_bytes(bytes(eventid), byteorder="little")

    def _table_struct_add(
        self,
    ):
        """
        Get the monitor version.

        Args:
            data: The monitor version data.

        Returns:
            data: The monitor version data.
        """
        tableStruct_add = []
        for i in range(45, 49):
            tableStruct_add.append(int(self.received[i], 16))

        return int.from_bytes(bytes(tableStruct_add), byteorder="little")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
