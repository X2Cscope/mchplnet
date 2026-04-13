"""Factory interface implementation.

Usage: Ensures the proper configuration of the communication interface supported by X2Cscope.
"""

import logging
import warnings
from enum import Enum

from mchplnet.interfaces.abstract_interface import Interface
from mchplnet.interfaces.can import LNetCan
from mchplnet.interfaces.tcp_ip import LNetTcpIp
from mchplnet.interfaces.uart import LNetSerial


class InterfaceType(Enum):
    """Enumeration of supported interface types."""
    SERIAL = 1
    CAN = 2
    TCP_IP = 3


class InterfaceFactory:
    """Factory class for creating interface instances."""

    @staticmethod
    def get_interface(interface_type: InterfaceType, *args, **kwargs) -> Interface:
        r"""Create and return an interface instance based on the specified type.

        Args:
            interface_type (InterfaceType): The type of interface to create.
            \*args: Variable length argument list passed to the interface constructor.
            \*\*kwargs: Arbitrary keyword arguments passed to the interface constructor.

        Returns:
            Interface: An instance of the requested interface type.
        """
        interfaces = {
            InterfaceType.SERIAL: LNetSerial,
            InterfaceType.CAN: LNetCan,
            InterfaceType.TCP_IP: LNetTcpIp,
        }
        default_args = {
            "port": LNetSerial,
            "host": LNetTcpIp,
            "bustype": LNetCan,
        }
        default = [default_args.get(key) for key in default_args if key in kwargs]
        if len(default) == 0 and interface_type is None:
            warnings.warn("No interface select, setting Serial as default.", Warning)
            default = [LNetSerial]
        return interfaces.get(interface_type, default[0])(*args, **kwargs)


if __name__ == "__main__":
    interface = InterfaceType.SERIAL
    interface_kwargs = {"port": "COM8", "baud-rate": 115200}

    try:
        interface = InterfaceFactory.get_interface(interface, **interface_kwargs)
        logging.debug("Interface created: %s", interface)
    except ValueError as e:
        logging.debug("Error creating interface: %s", str(e))
