Overview
========

Key Features
------------

* **Multiple Interface Support**: UART/Serial, CAN, and TCP/IP communication interfaces
* **Auto-Detection**: Automatic COM port detection for UART connections
* **LNet Protocol**: Complete frame serialization and deserialization with CRC checking
* **Device Communication**: Handshake, device information retrieval, and parameter management
* **Memory Operations**: Read and write data to microcontroller RAM
* **Scope Services**: Configure and retrieve scope channel data for real-time monitoring
* **Thread-Safe**: Built-in thread synchronization for concurrent operations

Architecture
------------

The mchplnet package is organized into several key components:

**Interfaces**
   Abstract interface definitions and concrete implementations for UART, CAN, and TCP/IP
   communication protocols.

**LNet Protocol**
   Frame-based communication protocol with automatic CRC calculation, fill byte handling,
   and error detection.

**Services**
   Protocol services including device info, RAM access (GetRam/PutRam), scope parameter
   management, and device reboot functionality.

Quick Example
-------------

**Auto-detection (Recommended for single device):**

.. code-block:: python

   from mchplnet.interfaces.factory import InterfaceFactory, InterfaceType
   from mchplnet.lnet import LNet

   interface = InterfaceFactory.get_interface(
       InterfaceType.SERIAL,
       port="AUTO",
       baud_rate=115200
   )

   lnet = LNet(interface)
   device_info = lnet.get_device_info()
   print(f"Connected to {interface.com_port}")
   print(f"Device: {device_info.processor_id}")
   print(f"Architecture: {device_info.uc_width}-bit")

**Manual port specification:**

.. code-block:: python

   from mchplnet.interfaces.factory import InterfaceFactory, InterfaceType
   from mchplnet.lnet import LNet

   interface = InterfaceFactory.get_interface(
       InterfaceType.SERIAL,
       port="COM8",
       baud_rate=115200
   )

   lnet = LNet(interface)
   device_info = lnet.get_device_info()
   print(f"Device: {device_info.processor_id}")
   print(f"Architecture: {device_info.uc_width}-bit")
