import logging

from mchplnet.interfaces.factory import InterfaceFactory
from mchplnet.interfaces.factory import InterfaceType as IType
from mchplnet.lnet import LNet

interface = InterfaceFactory.get_interface(IType.SERIAL, port="COM4", baudrate=115200)
l_net = LNet(interface)
logging.debug(l_net.device_info.monitorDate)
logging.debug(l_net.device_info.processor_id)
logging.debug(l_net.device_info.uc_width)
logging.debug(f"appversion:{l_net.device_info.appVer}....... DSP state:{l_net.device_info.dsp_state}")
read_bytes = l_net.get_ram(4148, 2)
logging.debug(int.from_bytes(read_bytes, byteorder="little"))
# put_value = l_net.put_ram(4148,2,bytes(50))
# logging.debug(put_value)
