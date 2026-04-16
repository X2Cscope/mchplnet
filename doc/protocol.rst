Protocol Details
================

LNet Frame Structure
--------------------

LNet frames consist of the following components:

* **SYN** (0x55): Frame synchronization byte
* **SIZE**: Number of data bytes in the frame
* **NODE**: Target slave node identifier
* **DATA**: Service ID, error status, and payload
* **CRC**: Checksum for error detection

Reserved Bytes
--------------

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

Scope Sampling
--------------

In ``mchplnet``, the scope uses the internal LNet sampling pre-scaler directly.

The ``sample_time_factor`` is 0-based:

* ``0``: store every sample
* ``1``: store every 2nd sample
* ``2``: store every 3rd sample

Higher values extend the total capture window, but reduce time resolution because fewer samples are stored.

This is the raw LNet representation. Higher-level tools such as ``pyx2cscope`` may expose a different,
more user-oriented convention on top of it.
