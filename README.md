<p align="center">
  <img src="pyx2cscope/docs/img/microchip-technology-logo.png" alt="PyX2CScope Logo" width="250">
</p>

# mchplnet
- mchplnet is the Python implementation of the LNet protocol.
- It implements multiple LNet services to communicate to embedded systems/microcontrollers.
- Currently only pyserial interface is supported 
- Recommended to use pyx2cscope package instead of this low-level implementation

## Getting Started

```
import mchplnet
import serial
l_net = mchplnet.LNet(serial.Serial('COM8', 115200))
var_address = 0x00000000
var_size = 4 
var_value = l_net.get_ram(var_address, var_size) 
print(var_value)
var_newValue = 500
l_net.put_ram(var_address, var_size, var_newValue)
```

## Contribute
If you discover a bug or have an idea for an improvement, we encourage you to contribute! You can do so by following these steps:

1. Fork the repository.
2. Create a new branch for your changes.
3. Make the necessary changes and commit them. 
4. Push your changes to your forked repository. 
5. Open a pull request on the main repository, describing your changes.

We appreciate your contribution!



-------------------------------------------------------------------



