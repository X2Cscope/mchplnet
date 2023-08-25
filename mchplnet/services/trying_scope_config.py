# Define error codes
ERRORSuccess = 0
ERRORSizeTooLarge = 1
ERRORParLimit = 2
ERRORBlkID = 3
ERRORFormat = 4
SvErrorInvalidDspState = 5
SvErrorFncTableNotInit = 6
SvErrorParamTableNotInit = 7
SvErrorInvalidParamId = 8
ERRORServiceNotAvail = 9

# Constants
MAX_SERVICE_ID = 4
SV_ID_SVDEVICEINFO = 0
SV_ID_GETTARGETSTATE = 1
SV_ID_SETTARGETSTATE = 2
SV_ID_SVSAVEPARAM = 3
SV_ID_SVLOADPARAM = 4

# Processor ID mapping
processor_id_mapping = {
    "__GENERIC_TI_C28X__": 0x8110,
    "__GENERIC_MICROCHIP_DSPIC__": 0x8210,
    "__GENERIC_MICROCHIP_PIC32__": 0x8220,
    # Add other processor ID mappings here
}


# Define tParameterTable and tSERVICEFunction as empty classes for now
class tParameterTable:
    pass


class tSERVICEFunction:
    pass


DEVINFO_MONITOR_VERSION = 0x0102  # Example value, change as needed
DEVINFO_PROCESSOR_ID = processor_id_mapping[
    "__GENERIC_TI_C28X__"
]  # Example value, change as needed


class TableStruct:
    def __init__(self):
        self.TParamTable = None
        self.TLimitSaveFncTable = None
        self.TFncTable = None
        self.framePrgCompDateTime = None
        self.framePrgVersion = 0
        self.piScope = None
        self.dynamicCodeData = None
        self.protocols = [None] * MAX_PROTOCOLS
        self.protocolCount = 0
        self.DSPState = 0
        self.eventType = 0
        self.eventId = 0

    def add_protocol(self, link_protocol):
        if self.protocolCount < MAX_PROTOCOLS:
            self.protocols[self.protocolCount] = link_protocol
            self.protocolCount += 1


# Define the Protocol class
class Protocol:
    def __init__(self):
        self.ucMaxCommSize = 46
        self.pServiceTable = [self.send_sv_not_available] * (MAX_SERVICE_ID + 1)
        self.DSPState = 0  # Default DSPState
        self.TParamTable = None  # Placeholder for tParameterTable
        self.TLimitSaveFncTable = None  # Placeholder for tLimitSaveFncTable
        self.TFncTable = None  # Placeholder for tFncTable

    def send_sv_not_available(self):
        self.ucFRAMESize = 2
        self.ucFRAMEData[1] = ERRORServiceNotAvail
        self.pSnd_Enable(self)

    def send_error(self, error_code):
        self.ucFRAMESize = 2
        self.ucFRAMEData[1] = error_code
        self.pSnd_Enable(self)

    def get_device_info(self):
        # Check frame buffer length
        if self.ucMaxCommSize < 46:
            self.send_error(ERRORSizeTooLarge)
            return

        self.ucFRAMESize = 46
        self.ucFRAMEData[1] = ERRORSuccess

        # monitor program version
        self.ucFRAMEData[2] = DEVINFO_MONITOR_VERSION & 0x00FF
        self.ucFRAMEData[3] = DEVINFO_MONITOR_VERSION >> 8

        # frame program version
        self.ucFRAMEData[4] = TableStruct.framePrgVersion & 0x00FF
        self.ucFRAMEData[5] = TableStruct.framePrgVersion >> 8

        # max comm size
        self.ucFRAMEData[6] = self.ucMaxCommSize

        self.ucFRAMEData[7] = DEVINFO_PROCESSOR_ID & 0x00FF
        self.ucFRAMEData[8] = DEVINFO_PROCESSOR_ID >> 8

        # monitor program compilation date as ASCII string
        self.ucFRAMEData[9:18] = list(__DATE__)

        # monitor program compilation time as ASCII string
        self.ucFRAMEData[18:22] = list(__TIME__)

        if TableStruct.framePrgCompDateTime == 0:
            for i in range(12):
                self.ucFRAMEData[22 + i] = ord("-")
        else:
            # frame program compilation date as ASCII string
            self.ucFRAMEData[22:34] = list(TableStruct.framePrgCompDateTime)

        self.ucFRAMEData[35] = TableStruct.DSPState & 0xFF
        self.ucFRAMEData[36] = TableStruct.eventType & 0xFF
        self.ucFRAMEData[37] = TableStruct.eventType >> 8
        self.ucFRAMEData[38] = TableStruct.eventId & 0xFF
        self.ucFRAMEData[39] = TableStruct.eventId >> 8
        self.ucFRAMEData[40] = TableStruct.eventId >> 16
        self.ucFRAMEData[41] = TableStruct.eventId >> 24

        tableStructAddr = TableStruct
        self.ucFRAMEData[42] = tableStructAddr & 0xFF
        self.ucFRAMEData[43] = (tableStructAddr >> 8) & 0xFF
        self.ucFRAMEData[44] = (tableStructAddr >> 16) & 0xFF
        self.ucFRAMEData[45] = (tableStructAddr >> 24) & 0xFF

        self.pSnd_Enable(self)

    def get_target_state(self):
        self.ucFRAMEData[1] = ERRORSuccess
        self.ucFRAMEData[2] = TableStruct.DSPState & 0xFF
        self.ucFRAMESize = 3
        self.pSnd_Enable(self)

    def set_target_state(self):
        error = ERRORSuccess

        state_id = self.ucFRAMEData[1]
        if state_id == 0:
            self.DSPState = MONITOR_STATE
        elif state_id == 1:
            self.DSPState = PRG_LOADED_STATE
        elif state_id == 2:
            self.DSPState = IDLE_STATE
        elif state_id == 3:
            self.DSPState = INIT_STATE
        elif state_id == 4:
            self.DSPState = RUN_STATE_POWER_OFF
        elif state_id == 5:
            self.DSPState = RUN_STATE_POWER_ON
        else:
            error = SvErrorInvalidDspState

        self.ucFRAMEData[1] = error
        self.ucFRAMESize = 2
        self.pSnd_Enable(self)

    def save_parameter(self):
        param_id = (self.ucFRAMEData[2] << 8) + self.ucFRAMEData[1]

        # Get block address from parameter table
        block_addr = self.get_block_address(self.TParamTable, param_id)
        if block_addr is None:
            self.send_error(SvErrorInvalidParamId)
            return

        # Check if parameter has a limit-save function
        if self.TLimitSaveFncTable:
            for item in self.TLimitSaveFncTable:
                if param_id == item.uiParID:
                    # Call the limit-save function if it exists
                    if (
                        item.pFLimitSave(
                            block_addr, self.ucFRAMEData[3:], self.ucFRAMESize - 3
                        )
                        != 0
                    ):
                        self.send_error(ERRORParLimit)
                    return

        if not self.TFncTable:
            self.send_error(SvErrorFncTableNotInit)
            return

        # Get block identifier
        block_id = block_addr[0:2]

        for item in self.TFncTable:
            if block_id == item.iBlockID:
                # Call the save function
                if (
                    item.pFSave(block_addr, self.ucFRAMEData[3:], self.ucFRAMESize - 3)
                    != 0
                ):
                    self.send_error(ERRORFormat)
                else:
                    self.ucFRAMESize = 2
                    self.ucFRAMEData[1] = ERRORSuccess
                    self.pSnd_Enable(self)
                return

        self.send_error(ERRORBlkID)

    def load_parameter(self):
        param_id = (self.ucFRAMEData[2] << 8) + self.ucFRAMEData[1]

        # Get block address from parameter table
        block_addr = self.get_block_address(self.TParamTable, param_id)
        if block_addr is None:
            self.send_error(SvErrorInvalidParamId)
            return

        if not self.TFncTable:
            self.send_error(SvErrorFncTableNotInit)
            return

        # Get block identifier
        block_id = block_addr[0:2]

        for item in self.TFncTable:
            if block_id == item.iBlockID:
                # Call the load function
                if item.pFLoad(block_addr, self.ucFRAMEData[2:]) != 0:
                    self.send_error(ERRORFormat)
                else:
                    self.ucFRAMESize = 2
                    self.ucFRAMEData[1] = ERRORSuccess
                    self.pSnd_Enable(self)
                return

        self.send_error(ERRORBlkID)

    def init_service_table(self):
        for i in range(0, MAX_SERVICE_ID + 1):
            self.pServiceTable[i] = self.send_sv_not_available

    def add_core_services(self):
        self.pServiceTable[SV_ID_SVDEVICEINFO] = self.get_device_info
        self.pServiceTable[SV_ID_GETTARGETSTATE] = self.get_target_state
        self.pServiceTable[SV_ID_SETTARGETSTATE] = self.set_target_state
        self.pServiceTable[SV_ID_SVSAVEPARAM] = self.save_parameter
        self.pServiceTable[SV_ID_SVLOADPARAM] = self.load_parameter

    def init(self):
        self.init_service_table()
        self.add_core_services()

    def get_block_address(self, param_table, param_id):
        error = ERRORSuccess
        block_addr = None

        # Send parameter ID error if no parameter table has been initialized
        if param_table is None:
            error = SvErrorParamTableNotInit
        else:
            for item in param_table:
                if param_id == item.uiParID:
                    block_addr = item.pAdr
                    break
            else:
                error = SvErrorInvalidParamId

        return block_addr, error


if __name__ == "__main__":
    # Sample usage of the Protocol class
    protocol = Protocol()
    protocol.init()

    # Simulate a request for Get Device Info (SV_ID_SVDEVICEINFO)
    request = {"service_id": SV_ID_SVDEVICEINFO}
    protocol.ucFRAMEData = [0] * 46
    protocol.get_device_info()  # Handle the request

    # Simulate a request for Get Target State (SV_ID_GETTARGETSTATE)
    request = {"service_id": SV_ID_GETTARGETSTATE}
    protocol.ucFRAMEData = [0] * 46
    protocol.get_target_state()  # Handle the request

    # Simulate a request for Set Target State (SV_ID_SETTARGETSTATE)
    request = {"service_id": SV_ID_SETTARGETSTATE, "state_id": 2}  # Setting IDLE_STATE
    protocol.ucFRAMEData = [0] * 46
    protocol.set_target_state()  # Handle the request

    # Simulate a request for Save Parameter (SV_ID_SVSAVEPARAM)
    request = {"service_id": SV_ID_SVSAVEPARAM, "param_id": 1234, "data": [1, 2, 3, 4]}
    protocol.ucFRAMEData = [0] * 46
    protocol.save_parameter()  # Handle the request

    # Simulate a request for Load Parameter (SV_ID_SVLOADPARAM)
    request = {"service_id": SV_ID_SVLOADPARAM, "param_id": 5678}
    protocol.ucFRAMEData = [0] * 46
    protocol.load_parameter()  # Handle the request
