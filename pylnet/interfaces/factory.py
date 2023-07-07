from pylnet.pylnet.interfaces.uart import LNetSerial
from pylnet.pylnet.interfaces.can import LNetCan
from pylnet.pylnet.interfaces.lin import LNetLin
from pylnet.pylnet.interfaces.tcp_ip import LNetTcpIp
from pylnet.pylnet.interfaces.abstract_interface import InterfaceABC
from enum import Enum


class InterfaceType(Enum):
    SERIAL = 1
    CAN = 2
    LIN = 3
    TCP_IP = 4


class InterfaceFactory:

    @staticmethod
    def get_interface(interface_type: InterfaceType, *args, **kwargs) -> InterfaceABC:
        interfaces = {
            InterfaceType.SERIAL: LNetSerial,
            InterfaceType.CAN: LNetCan,
            InterfaceType.LIN: LNetLin,
            InterfaceType.TCP_IP: LNetTcpIp
        }
        return interfaces[interface_type](*args, **kwargs)
