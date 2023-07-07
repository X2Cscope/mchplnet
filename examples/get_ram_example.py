import serial

from pylnet.pylnet.interfaces.factory import InterfaceFactory, InterfaceType as IType
from pylnet.pylnet.lnet import LNet
interface = InterfaceFactory.get_interface(IType.SERIAL, port="COM8")
interface.start()
l_net = LNet(interface)
#print(l_net.device_info.appVer)
# 0x00000000 is the address of the variable in RAM and 4 is the number of bytes to read
ret_bytes = l_net.get_ram(4142, 2)
print(int.from_bytes(ret_bytes))