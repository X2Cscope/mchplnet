from dataclasses import dataclass


@dataclass
class DeviceInfo:
    monitorVer: int = 0
    appVer: int = 0
    processorID: int = 0
    monitorDate: int = 0
    appDate: int = 0
    width: int = 0
    dsp_state: int = 0
