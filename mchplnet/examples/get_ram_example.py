import logging

from mchplnet.interfaces.factory import InterfaceFactory
from mchplnet.interfaces.factory import InterfaceType as IType
from mchplnet.lnet import LNet

logging.basicConfig(level=logging.DEBUG)  # Configure the logging module


interface = InterfaceFactory.get_interface(IType.SERIAL, port="COM13", baudrate=115200)
l_net = LNet(interface)
value = l_net.interface_handshake()
logging.debug(value.monitorDate)
logging.debug(value.processorID)
logging.debug(value.uc_width)
logging.debug(f"appversion:{value.appVer}....... DSP state:{value.dsp_state}")
read_bytes = l_net.get_ram(4148, 2)
logging.debug(int.from_bytes(read_bytes))
# put_value = l_net.put_ram(4148,2,bytes(50))
# logging.debug(put_value)
