Interfaces
==========

Interface Factory
-----------------

The Interface Factory provides a unified way to create communication interfaces based on
user-specified parameters. If no parameters are provided, it defaults to a standard serial
connection on ``COM1`` with a baud rate of ``115200``. Users can specify parameters for UART,
CAN, or TCP/IP interfaces to connect to their target devices.

Following parameters will specify which interface should be returned by the InterfaceFactory:

* ``port``: Serial port name (e.g., ``COM3``, ``/dev/ttyUSB0``) -> ``InterfaceType.SERIAL``
* ``host``: IP address or hostname of the target device -> ``InterfaceType.TCP_IP``
* ``bustype``: CAN interface type (e.g., ``pcan_usb``, ``socketcan``) -> ``InterfaceType.CAN``

Communication Interfaces
------------------------

Serial (UART) Interface
~~~~~~~~~~~~~~~~~~~~~~~

The most common interface for connecting to microcontrollers via serial/UART communication.
Supports automatic COM port detection when ``port="AUTO"`` is specified.

Parameters
^^^^^^^^^^

.. list-table::
   :widths: 20 15 15 50
   :header-rows: 1

   * - Parameter
     - Type
     - Default
     - Description
   * - ``port``
     - str
     - ``AUTO``
     - Serial port name (e.g., ``COM3``, ``/dev/ttyUSB0``) or ``AUTO`` for auto-detection
   * - ``baud_rate``
     - int
     - 115200
     - Communication speed in bits per second
   * - ``parity``
     - int
     - 0
     - Parity setting (0=None)
   * - ``stop_bit``
     - int
     - 1
     - Number of stop bits
   * - ``data_bits``
     - int
     - 8
     - Number of data bits

Auto-Detection Feature
^^^^^^^^^^^^^^^^^^^^^^

When ``port="AUTO"`` or no port is specified, the system automatically:

1. Enumerates all available COM ports
2. Tests each port by opening a connection with configured settings
3. Sends a device information request using the LNet protocol
4. Validates the response from each port
5. Connects to the first port that responds correctly

This is particularly useful for:

* **Development and testing** with a single device
* **User-friendly applications** where the COM port is unknown
* **Cross-machine compatibility** without hardcoding port names
* **Quick prototyping** without checking port numbers

**How it works:**

The auto-detection uses the ``get_device_info()`` method to validate each port. Only ports
that respond with valid LNet device information are selected. Default serial settings
(``115200`` baud, ``8N1``) are used during auto-detection.

Examples
^^^^^^^^

**Auto-detection (recommended for single device):**

.. code-block:: python

    interface = InterfaceFactory.get_interface(port="AUTO")
    lnet = LNet(interface)
    print(f"Connected to {interface.com_port}")

**Auto-detection with custom baud rate:**

.. code-block:: python

    interface = InterfaceFactory.get_interface(port="AUTO", baud_rate=9600)

**Manual port specification:**

.. code-block:: python

    interface = InterfaceFactory.get_interface(port="COM16")

**Serial connection with custom settings:**

.. code-block:: python

    interface = InterfaceFactory.get_interface(
        port="COM16",
        baud_rate=9600,
        parity=0,
        stop_bit=1,
        data_bits=8
    )

TCP/IP Interface
~~~~~~~~~~~~~~~~

For network-based connections to embedded systems with Ethernet capability.

Parameters
^^^^^^^^^^

.. list-table::
   :widths: 20 15 15 50
   :header-rows: 1

   * - Parameter
     - Type
     - Default
     - Description
   * - ``host``
     - str
     - ``localhost``
     - IP address or hostname of the target device
   * - ``tcp_port``
     - int
     - 12666
     - TCP port number for the connection
   * - ``timeout``
     - float
     - 0.1
     - Connection timeout in seconds

Examples
^^^^^^^^

**TCP/IP connection with default tcp_port:**

.. code-block:: python

    interface = InterfaceFactory.get_interface(host="192.168.1.100")

**TCP/IP connection with custom tcp_port:**

.. code-block:: python

    interface = InterfaceFactory.get_interface(host="192.168.1.100", tcp_port=12345)

CAN Interface
~~~~~~~~~~~~~

For CAN bus connections supporting multiple vendor interfaces including PCAN USB, PCAN LAN,
SocketCAN (Linux), Vector, and Kvaser. The interface automatically handles LNet frame
fragmentation over 8-byte CAN messages.

Parameters
^^^^^^^^^^

.. list-table::
   :widths: 20 15 15 50
   :header-rows: 1

   * - Parameter
     - Type
     - Default
     - Description
   * - ``bustype``
     - str
     - ``pcan_usb``
     - Interface type: ``pcan_usb``, ``pcan_lan``, ``socketcan``, ``vector``, ``kvaser``
   * - ``channel``
     - int
     - 1
     - CAN channel number (automatically converted to vendor format)
   * - ``baud_rate``
     - int
     - 500000
     - CAN bus baud rate in bits per second
   * - ``id_tx``
     - int
     - 0x110
     - CAN arbitration ID for transmitting to device
   * - ``id_rx``
     - int
     - 0x100
     - CAN arbitration ID for receiving from device
   * - ``mode``
     - str
     - ``standard``
     - CAN ID mode: ``standard`` (11-bit) or ``extended`` (29-bit)
   * - ``timeout``
     - float
     - 0.1
     - Read timeout in seconds

Supported Interfaces
^^^^^^^^^^^^^^^^^^^^

* **PCAN USB** (Peak-System USB adapters) - Default
* **PCAN LAN** (Peak-System Ethernet/LAN gateways)
* **SocketCAN** (Linux native CAN interface)
* **Vector** (Vector CANoe/CANalyzer hardware)
* **Kvaser** (Kvaser CAN interfaces)

Channel Conversion
^^^^^^^^^^^^^^^^^^

The interface automatically converts numeric channels to vendor-specific formats:

* PCAN USB: ``channel=1`` -> ``PCAN_USBBUS1``, ``channel=2`` -> ``PCAN_USBBUS2``
* PCAN LAN: ``channel=1`` -> ``PCAN_LANBUS1``, ``channel=2`` -> ``PCAN_LANBUS2``
* SocketCAN: ``channel=1`` -> ``can0``, ``channel=2`` -> ``can1`` (0-indexed)
* Vector: ``channel=1`` -> ``0``, ``channel=2`` -> ``1`` (0-indexed)
* Kvaser: ``channel=1`` -> ``0``, ``channel=2`` -> ``1`` (0-indexed)

Examples
^^^^^^^^

**PCAN USB connection (default):**

.. code-block:: python

    interface = InterfaceFactory.get_interface(bustype="pcan_usb", channel=1)

**PCAN LAN (Ethernet) connection:**

.. code-block:: python

    interface = InterfaceFactory.get_interface(bustype="pcan_lan", channel=1, baud_rate=500000)

**SocketCAN on Linux:**

.. code-block:: python

    interface = InterfaceFactory.get_interface(bustype="socketcan", channel=1)

**Extended CAN IDs (29-bit):**

.. code-block:: python

    interface = InterfaceFactory.get_interface(
        bustype="pcan_usb",
        channel=1,
        mode="extended",
        id_tx=0x18FF1234,
        id_rx=0x18FF5678
    )

Driver Requirements
^^^^^^^^^^^^^^^^^^^

**Python Package:**

.. code-block:: bash

   pip install python-can

**System Drivers:**

The CAN interface requires both system-level drivers and Python packages:

* **PCAN (USB/LAN)**: Install PCAN driver from Peak-System. The ``python-can`` base package includes PCAN support.
* **SocketCAN (Linux)**: Built into Linux kernel (no additional driver needed). The ``python-can`` base package includes SocketCAN support.
* **Vector**: Install Vector hardware drivers. Requires optional Python package: ``pip install python-can[vector]``
* **Kvaser**: Install Kvaser CANlib drivers. Requires optional Python package: ``pip install python-can[kvaser]``

For most users with PCAN hardware, the base ``python-can`` installation is sufficient.
