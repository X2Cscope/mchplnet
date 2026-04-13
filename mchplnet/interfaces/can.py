"""CAN interface implementation for LNet protocol."""
import logging
import time

import can

from mchplnet.interfaces.abstract_interface import Interface
from mchplnet.lnetframe import LNET_FILL_BYTE_1, LNET_FILL_BYTE_2

# LNet frame header constants
LNET_HEADER_SIZE = 2  # SYN and SIZE bytes
LNET_FRAME_OVERHEAD = 2  # NODE, SERVICE_ID, and CRC bytes (SIZE doesn't include these)


class LNetCan(Interface):
    """LNet CAN interface implementation.

    This class implements the CAN interface for LNet protocol communication.
    It uses the python-can library to handle CAN bus communication with multiple
    vendor interfaces.

    Supported CAN Interfaces:
    - PCAN USB: Peak-System USB adapters (default)
    - PCAN LAN: Peak-System Ethernet/LAN gateways
    - SocketCAN: Linux native CAN interface
    - Vector: Vector CANoe/CANalyzer hardware
    - Kvaser: Kvaser CAN interfaces

    Protocol Details:
    - LNet frames are fragmented into CAN messages (max 8 bytes per message)
    - Each CAN message carries part of the LNet frame
    - Specific CAN arbitration IDs are used for TX/RX communication
    - Fill-byte handling preserves LNet frame integrity

    Configuration:
    - bustype: Interface type ('pcan_usb', 'pcan_lan', 'socketcan', 'vector', 'kvaser')
    - channel: Numeric channel (1, 2, 3...) - automatically converted to vendor format
    - baud_rate: CAN bus speed in bps (default: 500000)
    - mode: 'standard' (11-bit IDs) or 'extended' (29-bit IDs)
    """

    def is_open(self):
        """Check if the CAN interface is open."""
        return self.bus is not None and hasattr(self.bus, '_is_shutdown') and not self.bus._is_shutdown

    def start(self):
        """Start the CAN interface."""
        try:
            # Map our bustype to python-can's bustype
            # pcan_usb and pcan_lan both use 'pcan' interface, differentiated by channel name
            python_can_bustype = self._get_python_can_bustype(self.bustype)

            self.bus = can.interface.Bus(
                channel=self.channel,
                bustype=python_can_bustype,
                bitrate=self.bitrate,
                **self.extra_config
            )
            logging.debug(f"CAN interface started on {self.bustype}:{self.channel} at {self.bitrate} bps")
            return super().start()
        except Exception as e:
            self.stop()
            logging.error(f"Failed to start CAN interface: {e}")
            raise

    def stop(self):
        """Stop the CAN interface."""
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception as e:
                logging.error(f"Error stopping CAN interface: {e}")
            finally:
                self.bus = None

    def __init__(self, *args, **kwargs):  # noqa: D417
        r"""Initialize the CAN interface.

        Args:
            \*args: Variable length argument list passed to parent class.
            bustype (str): CAN interface type:
                          - 'pcan_usb': PCAN USB adapter (default)
                          - 'pcan_lan': PCAN LAN/Ethernet adapter
                          - 'socketcan': Linux SocketCAN
                          - 'vector': Vector CAN interfaces
                          - 'kvaser': Kvaser CAN interfaces
            channel (int/str): CAN channel number (1, 2, 3...). Defaults to 1.
                              Will be converted to appropriate format for each interface type.
            baud_rate (int): CAN bus baud rate in bits per second. Defaults to 500000 (500 kbps).
            id_tx (int): CAN arbitration ID for transmitting LNet frames. Defaults to 0x110.
            id_rx (int): CAN arbitration ID for receiving LNet frames. Defaults to 0x100.
            mode (str): CAN ID mode - 'standard' for 11-bit IDs or 'extended' for 29-bit IDs.
                       Defaults to 'standard'.
            timeout (float): Timeout for CAN read operations in seconds. Defaults to 1 second.
            \*\*kwargs: Additional configuration passed to python-can Bus constructor.
        """
        super().__init__(*args, **kwargs)
        # Bustype refers to the interface type (USB/LAN, vendor)
        self.bustype = kwargs.get("bustype", "pcan_usb")

        # Channel number (as integer or string)
        channel_input = kwargs.get("channel", 1)

        # Convert channel number to appropriate format for each interface
        self.channel = self._convert_channel(self.bustype, channel_input)

        # Baud rate
        self.bitrate = kwargs.get("baud_rate", 500000)

        self.can_id_tx = kwargs.get("id_tx", 0x110)
        self.can_id_rx = kwargs.get("id_rx", 0x100)
        self.timeout = kwargs.get("timeout", 0.01)

        # CAN ID mode: 'standard' (11-bit) or 'extended' (29-bit)
        mode = kwargs.get("mode", "standard")
        if mode.lower() in ["extended", "ext", "29bit"]:
            self.is_extended_id = True
        else:
            self.is_extended_id = False

        # Store any extra configuration for python-can
        # Exclude parameters we've already processed
        self.extra_config = {k: v for k, v in kwargs.items()
                            if k not in ["channel", "bus", "bustype", "baud_rate",
                                        "id_tx", "id_rx", "timeout", "mode",
                                        "elf_file", "interface"]}

        self.bus = None
        self._rx_buffer = bytearray()

    def _get_python_can_bustype(self, bustype):
        """Convert our bustype to python-can's bustype.

        Args:
            bustype (str): Our interface type

        Returns:
            str: python-can interface type
        """
        # Map our bustype names to python-can's expected interface names
        # pcan_usb and pcan_lan both use 'pcan' in python-can
        bustype_map = {
            'pcan_usb': 'pcan',
            'pcan_lan': 'pcan',
            'pcan': 'pcan',
            'socketcan': 'socketcan',
            'vector': 'vector',
            'kvaser': 'kvaser'
        }
        return bustype_map.get(bustype, bustype)

    def _convert_channel(self, bustype, channel):
        """Convert channel number to appropriate format for the interface type.

        Args:
            bustype (str): The CAN interface type
            channel (int/str): The channel number

        Returns:
            str: Channel identifier in the format required by python-can
        """
        # Convert to integer if it's a string number
        try:
            channel_num = int(channel)
        except (ValueError, TypeError):
            # If it's already a string like 'PCAN_USBBUS1', return as-is
            return str(channel)

        # Map channel numbers to interface-specific identifiers
        channel_map = {
            'pcan': lambda n: f'PCAN_USBBUS{n}',
            'pcan_usb': lambda n: f'PCAN_USBBUS{n}',
            'pcan_lan': lambda n: f'PCAN_LANBUS{n}',
            'socketcan': lambda n: f'can{n - 1}' if n > 0 else 'can0',
            'vector': lambda n: str(n - 1) if n > 0 else '0',
            'kvaser': lambda n: n - 1 if n > 0 else 0,
        }

        if bustype in channel_map:
            return channel_map[bustype](channel_num)

        # For unknown types, just return the channel as-is
        logging.warning(f"Unknown bustype '{bustype}', using channel as-is: {channel}")
        return str(channel)

    def write(self, data):
        """Write data to the CAN interface.

        LNet frames are fragmented into CAN messages with up to 8 bytes each.
        The LNet frame is sent as-is without additional framing.

        Args:
            data (bytearray): The LNet frame data to transmit.
        """
        if not self.bus:
            raise RuntimeError("CAN interface not started")

        # Fragment the data into CAN messages (max 8 bytes per message)
        # Simply send the LNet frame in 8-byte chunks
        total_length = len(data)
        offset = 0
        message_count = 0

        try:
            while offset < total_length:
                # Send up to 8 bytes per CAN message
                chunk_size = min(8, total_length - offset)
                msg_data = bytes(data[offset:offset + chunk_size])
                offset += chunk_size

                msg = can.Message(
                    arbitration_id=self.can_id_tx,
                    data=msg_data,
                    is_extended_id=self.is_extended_id
                )
                self.bus.send(msg)
                message_count += 1

            logging.debug(f"Sent {total_length} bytes in {message_count} CAN messages")

        except Exception as e:
            logging.error(f"Error writing to CAN interface: {e}")
            raise

    def read(self):
        """Read data from the CAN interface.

        This method reconstructs LNet frames from fragmented CAN messages.
        It reads CAN messages until a complete LNet frame is received.
        Similar to TCP/IP implementation but for CAN fragmentation.

        Returns:
            bytearray: Complete LNet frame data.

        Raises:
            TimeoutError: If no data is received within timeout period.
        """
        if not self.bus:
            raise RuntimeError("CAN interface not started")

        # LNET Frame (SYN, SIZE, NODE, SERVICE_ID, DATA, CRC)
        # SIZE (at data[1]) contains the number of DATA bytes
        # Read initial 2 bytes (SYN, SIZE) from CAN messages
        fill_bytes = (LNET_FILL_BYTE_1, LNET_FILL_BYTE_2)
        data = bytearray()
        size = LNET_HEADER_SIZE  # Start by reading SYN and SIZE

        start = time.time()
        # Read initial SYN and SIZE bytes
        while size > 0:
            msg = self.bus.recv(timeout=self.timeout)

            if time.time() - start > 1:
                raise TimeoutError("No response from endpoint")

            if msg is None:
                if len(data) == 0:
                    continue
                else:
                    logging.warning("CAN read timeout while receiving frame")
                    break

            # Filter messages by our RX arbitration ID
            if msg.arbitration_id != self.can_id_rx:
                continue

            msg_data = bytearray(msg.data)
            data.extend(msg_data)
            size -= len(msg_data)

        # Now we have at least SYN and SIZE
        # Calculate remaining bytes: NODE, SERVICE_ID, DATA, CRC
        if len(data) >= LNET_HEADER_SIZE:
            size = data[1] + LNET_FRAME_OVERHEAD  # NODE, SERVICE_ID, CRC (SIZE doesn't include these)
            size += 1 if data[1] in fill_bytes else 0  # Add 1 if SIZE is a fill byte

            # Continue reading remaining bytes
            while size > 0:
                msg = self.bus.recv(timeout=self.timeout)

                if msg is None:
                    logging.warning("CAN read timeout while receiving remaining frame data")
                    break

                # Filter messages by our RX arbitration ID
                if msg.arbitration_id != self.can_id_rx:
                    continue

                msg_data = bytearray(msg.data)
                for byte in msg_data:
                    data.append(byte)
                    # Don't count fill bytes toward frame size
                    size -= 0 if byte in fill_bytes else 1

        logging.debug(f"CAN read complete: {len(data)} bytes - {data.hex()}")
        return data
