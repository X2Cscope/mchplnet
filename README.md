<p align="center">
  <img src="docs/img/microchip-technology-logo.png" alt="PyX2CScope Logo" width="250">
</p>

# pylnet
- pylnet is the Python implementation of the LNet protocol.
- It implements multiple LNet services to commincate to embedded systems/microcontrollers.
- Currently only pyserial interface is supported 
- Recommended to use pyx2cscope package instead of this low level implementation

## Getting Started

'''
import pylnet
import serial

l_net = pylnet.LNet(serial.Serial('COM8', 115200))
print(l_net.device_info.appVer)
# 0x00000000 is the address of the variable in RAM and 4 is the number of bytes to read
ret_bytes = l_net.get_ram(0x00000000, 4) 
print(ret_bytes)

'''

## Contribute
If you discover a bug or have an idea for an improvement, we encourage you to contribute! You can do so by following these steps:

1. Fork the repository.
2. Create a new branch for your changes.
3. Make the necessary changes and commit them. 
4. Push your changes to your forked repository. 
5. Open a pull request on the main repository, describing your changes.

We appreciate your contribution!



-------------------------------------------------------------------



