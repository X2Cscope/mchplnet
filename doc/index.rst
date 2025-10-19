mchplnet
========

**LNet Protocol Implementation for Microchip Microcontrollers**

The ``mchplnet`` package provides a Python implementation of the LNet protocol for communicating with 
X2Cscope-enabled firmwares running on Microchip microcontrollers. It serves as the communication layer 
for the pyx2cscope package, enabling real-time data exchange, scope functionality, and RAM access 
for embedded systems development.

Key Features
------------

* **Multiple Interface Support**: UART/Serial, CAN, LIN, and TCP/IP communication interfaces
* **LNet Protocol**: Complete frame serialization and deserialization with CRC checking
* **Device Communication**: Handshake, device information retrieval, and parameter management
* **Memory Operations**: Read and write data to microcontroller RAM
* **Scope Services**: Configure and retrieve scope channel data for real-time monitoring
* **Thread-Safe**: Built-in thread synchronization for concurrent operations

Overview
--------

The mchplnet package is organized into several key components:

**Interfaces**
   Abstract interface definitions and concrete implementations for UART, CAN, LIN, and TCP/IP 
   communication protocols.

**LNet Protocol**
   Frame-based communication protocol with automatic CRC calculation, fill byte handling, 
   and error detection.

**Services**
   Protocol services including device info, RAM access (GetRam/PutRam), scope parameter 
   management, and device reboot functionality.

Quick Example
-------------

.. code-block:: python

   from mchplnet.interfaces.factory import InterfaceFactory, InterfaceType
   from mchplnet.lnet import LNet

   # Create UART interface
   interface = InterfaceFactory.get_interface(
       InterfaceType.SERIAL, 
       port="COM8", 
       baud_rate=115200
   )

   # Initialize LNet communication
   lnet = LNet(interface)

   # Get device information
   device_info = lnet.get_device_info()
   print(f"Device: {device_info.processor_id}")
   print(f"Architecture: {device_info.uc_width}-bit")

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Documentation:

   autoapi/index

Protocol Details
----------------

**LNet Frame Structure**

LNet frames consist of the following components:

* **SYN** (0x55): Frame synchronization byte
* **SIZE**: Number of data bytes in the frame
* **NODE**: Target slave node identifier
* **DATA**: Service ID, error status, and payload
* **CRC**: Checksum for error detection

**Reserved Bytes**

The protocol handles reserved byte values (0x55 and 0x02) by inserting fill bytes (0x00) 
to prevent confusion with control characters.

Supported Services
------------------

* **Service 0**: Device Information - Retrieve firmware version, processor type, and device state
* **Service 9**: Get RAM - Read data from microcontroller memory
* **Service 10**: Put RAM - Write data to microcontroller memory
* **Service 18**: Save Parameter - Configure scope channels and trigger settings
* **Service 19**: Load Parameter - Retrieve scope configuration and data status
* **Service 25**: Reboot - Reset the microcontroller

Installation
------------

Install from PyPI:

.. code-block:: bash

   pip install mchplnet

Or install from source:

.. code-block:: bash

   git clone https://github.com/X2Cscope/mchplnet.git
   cd mchplnet
   pip install -e .

Requirements
------------

* Python 3.8 or higher
* pyserial (for UART communication)

Development
-----------

To contribute to mchplnet development:

.. code-block:: bash

   # Install development dependencies
   pip install -e ".[dev]"

   # Run tests
   pytest tests/

   # Run linting
   ruff check .

   # Build documentation
   sphinx-build -M html doc build -Wan --keep-going

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



