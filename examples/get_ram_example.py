import pylnet
import serial

l_net = pylnet.LNet(serial.Serial('COM8', 115200))
print(l_net.device_info.appVer)
# 0x00000000 is the address of the variable in RAM and 4 is the number of bytes to read
ret_bytes = l_net.get_ram(0x00000000, 4) 
print(ret_bytes)