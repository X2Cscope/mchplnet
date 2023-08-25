import logging

from mchplnet.interfaces.factory import InterfaceFactory
from mchplnet.interfaces.factory import InterfaceType as IType
from mchplnet.lnet import LNet

logging.basicConfig(level=logging.DEBUG)  # Configure the logging module


interface = InterfaceFactory.get_interface(IType.SERIAL, port="COM8", baudrate=115200)
l_net = LNet(interface)
value = l_net.interface_handshake()
print(value.monitorDate)
print(value.processorID)
print(value.uc_width)
print(f"appversion:{value.appVer}....... DSP state:{value.dsp_state}")
ret_bytes = l_net.get_ram(4148, 2)
print(int.from_bytes(ret_bytes))
# put_value = l_net.put_ram(4148,2,bytes(50))
# print(put_value)
