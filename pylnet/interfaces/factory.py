from pylnet.interfaces.uart import LNetSerial
from pylnet.interfaces.can import LNetCan
from pylnet.interfaces.lin import LNetLin
from pylnet.interfaces.tcp_ip import LNetTcpIp
from pylnet.interfaces.abstract_interface import InterfaceABC
from enum import Enum


class InterfaceType(Enum):
    SERIAL = 1
    CAN = 2
    LIN = 3
    TCP_IP = 4


class InterfaceFactory:

    @staticmethod
    def get_interface(interface_type: InterfaceType, *args: object, **kwargs: object) -> InterfaceABC:
        interfaces = {
            InterfaceType.SERIAL: (LNetSerial, {
                'port': 'Serial port name or device path',
                'baudrate': 'Baudrate for the serial communication'
            }),
            InterfaceType.CAN: (LNetCan, {
                'channel': 'CAN channel number or identifier'
            }),
            InterfaceType.LIN: (LNetLin, {
                'channel': 'LIN channel number or identifier'
            }),
            InterfaceType.TCP_IP: (LNetTcpIp, {
                'host': 'IP address or hostname of the remote device',
                'port': 'Port number for TCP/IP communication'
            })
        }

        interface_class, required_params = interfaces[interface_type]

        # Check if all required parameters are provided
        missing_params = [param for param, description in required_params.items() if param not in kwargs]
        if missing_params:
            raise ValueError(f"Missing required parameters for {interface_type.name}: {', '.join(missing_params)}")

        return interface_class(*args, **kwargs)



if __name__ == "__main__":
    interface_type = InterfaceType.SERIAL
    interface_kwargs = {
        'port': 'COM8',
        'baudrate': 115200
    }

    try:
        interface = InterfaceFactory.get_interface(interface_type, **interface_kwargs)
        print("Interface created:", interface)
    except ValueError as e:
        print("Error creating interface:", str(e))