"""Factory interface implementation.

Usage: Ensures the proper configuration of the communication interface supported by X2Cscope.
"""

import logging
from enum import Enum

from mchplnet.interfaces.abstract_interface import Interface
from mchplnet.interfaces.can import LNetCan
from mchplnet.interfaces.lin import LNetLin
from mchplnet.interfaces.tcp_ip import LNetTcpIp
from mchplnet.interfaces.uart import LNetSerial


class InterfaceType(Enum):
    """Enumeration of supported interface types."""
    SERIAL = 1
    CAN = 2
    LIN = 3
    TCP_IP = 4


class InterfaceFactory:
    """Factory class for creating interface instances."""

    @staticmethod
    def get_interface(interface_type: InterfaceType, *args, **kwargs) -> Interface:
        r"""Create and return an interface instance based on the specified type.

        Args:
            interface_type (InterfaceType): The type of interface to create.
            *args: Variable length argument list passed to the interface constructor.
            **kwargs: Arbitrary keyword arguments passed to the interface constructor.

        Returns:
            Interface: An instance of the requested interface type.
        """
        interfaces = {
            InterfaceType.SERIAL: LNetSerial,
            InterfaceType.CAN: LNetCan,
            InterfaceType.LIN: LNetLin,
            InterfaceType.TCP_IP: LNetTcpIp,
        }
        return interfaces.get(interface_type, LNetSerial)(*args, **kwargs)


if __name__ == "__main__":
    interface = InterfaceType.SERIAL
    interface_kwargs = {"port": "COM8", "baud-rate": 115200}

    try:
        interface = InterfaceFactory.get_interface(interface, **interface_kwargs)
        logging.debug("Interface created: %s", interface)
    except ValueError as e:
        logging.debug("Error creating interface: %s", str(e))
