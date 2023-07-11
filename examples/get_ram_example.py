from pylnet.interfaces.factory import InterfaceFactory, InterfaceType as IType
from pylnet.lnet import LNet
interface = InterfaceFactory.get_interface(IType.SERIAL, port="COM8", baudrate= 115200)
l_net = LNet(interface)
value = l_net.handshake()
print(value.monitorDate)
print(value.processorID)
print(f"appversion:{value.appVer}....... DSP state:{value.dsp_state}")
ret_bytes = l_net.get_ram(4148, 2)
print(int.from_bytes(ret_bytes))
