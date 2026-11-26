"""LNet protocol handler for microcontroller communication."""

import logging
import threading
from collections import deque

from mchplnet.framing import LNET_SYN_STREAM
from mchplnet.interfaces.abstract_interface import Interface
from mchplnet.services.frame_device_info import DeviceInfo, FrameDeviceInfo
from mchplnet.services.frame_getram import FrameGetRam
from mchplnet.services.frame_load_parameter import FrameLoadParameter, LoadScopeData
from mchplnet.services.frame_putram import FramePutRam
from mchplnet.services.frame_reboot import FrameReboot
from mchplnet.services.frame_save_parameter import FrameSaveParameter
from mchplnet.services.scope import ScopeSetup

# Maximum number of stream frames kept until get_stream_frames() is called; older frames are discarded.
STREAM_QUEUE_MAX_FRAMES = 10000

# LNet v5 maximum frame size (SIZE is one byte); used if the device does not report one
LNET_DEFAULT_MAX_FRAME_SIZE = 255
# Data types accepted by Get/Put RAM Block (X2Cscope profile 5.3); 64-bit values use type 4
RAM_ACCESS_TYPES = (4, 2, 1)


class LNet:
    """LNet is a class that handles communication with a microcontroller.

    This class facilitates interface handshake, retrieving device information, saving and loading scope parameters,
    and reading/writing data to the microcontroller's RAM.

    When initialized with an interface that supports auto-detection (e.g., LNetSerial with port="AUTO"),
    the class automatically sets up connection validation using get_device_info() and the interface
    will find and connect to the first available device that responds correctly to LNet protocol.

    Example:
        >>> # Auto-detection
        >>> interface = LNetSerial(port="AUTO")
        >>> lnet = LNet(interface)
        >>> print(f"Connected to {interface.com_port}")

        >>> # Manual port
        >>> interface = LNetSerial(port="COM3")
        >>> lnet = LNet(interface)
    """

    def __init__(self, interface: Interface, handshake: bool = True):
        """Initialize the LNet instance.

        Args:
            interface (Interface): The interface for communication with the microcontroller.
            handshake (bool, optional): If True, performs an interface handshake upon initialization. Defaults to True.
        """
        self.scope_data = None
        self.interface = interface
        self.device_info = None
        self.scope_setup = ScopeSetup()
        self._lock = threading.Lock()
        # Stream frames (SYN 0x02) pushed by the device; see get_stream_frames()
        self._stream_frames = deque(maxlen=STREAM_QUEUE_MAX_FRAMES)
        self.discarded_stream_frames = 0
        if handshake:
            # Set the test connection callback for auto-detection
            self.interface.set_test_connection(self.get_device_info)
            if self.interface.start():
                self.load_parameters()

    def get_device_info(self) -> DeviceInfo:
        """Retrieve and return the device information.

        Returns:
            DeviceInfo: The device information retrieved from the microcontroller.
        """
        if not self.device_info:
            device_info_frame = FrameDeviceInfo()
            device_info_frame.received = self._xchg_data(device_info_frame.serialize())
            self.device_info = device_info_frame.deserialize()
        return self.device_info

    def reboot_device(self):
        """Retrieve and return the device information.

        Returns:
            DeviceInfo: The device information retrieved from the microcontroller.
        """
        reboot_device = FrameReboot()
        print(reboot_device.serialize())
        reboot_device.received = self._xchg_data(reboot_device.serialize())
        return reboot_device.received

    def save_parameter(self):
        """Save the current scope configuration parameters to the microcontroller.

        Returns:
            The response from the microcontroller.

        Raises:
            RuntimeError: If device information is not retrieved before saving parameters.
        """
        frame_save_param = FrameSaveParameter()
        frame_save_param.set_scope_setup(self.scope_setup)
        frame_save_param.received = self._xchg_data(frame_save_param.serialize())
        return frame_save_param.deserialize()

    def load_parameters(self) -> LoadScopeData:
        """Load and return the scope parameters from the microcontroller.

        Returns:
            LoadScopeData: The loaded scope parameters.

        Raises:
            RuntimeError: If device information is not retrieved before loading parameters.
        """
        frame_load_param = FrameLoadParameter()
        frame_load_param.received = self._xchg_data(frame_load_param.serialize())
        self.scope_data = frame_load_param.deserialize()
        return self.scope_data

    @property
    def max_frame_size(self) -> int:
        """Return the maximum frame size (SIZE) reported by the device, 255 if not known."""
        size = getattr(self.device_info, "max_frame_size", 0) if self.device_info else 0
        if isinstance(size, int) and 0 < size <= LNET_DEFAULT_MAX_FRAME_SIZE:
            return size
        return LNET_DEFAULT_MAX_FRAME_SIZE

    @property
    def max_read_size(self) -> int:
        """Return the maximum number of bytes one Get RAM Block request can read.

        Response: Service ID, Error ID and the data must fit into one frame (253 for 255-byte frames).
        """
        return self.max_frame_size - 2

    @property
    def max_write_size(self) -> int:
        """Return the maximum number of bytes one Put RAM Block request can write.

        Request: Service ID, address (uc_width bytes), data type and the data must fit into one frame
        (249 on 32-bit, 251 on 16-bit devices for 255-byte frames).
        """
        return self.max_frame_size - 2 - self.device_info.uc_width

    @staticmethod
    def _access_type(size: int, data_type: int = 4) -> int:
        """Return the largest data type accepted by the device (4, 2, 1) that divides size and is <= data_type.

        64-bit values (data_type 8) are accessed as two 32-bit words in one request, because Get/Put RAM
        Block only accept the data types 1, 2 and 4.
        """
        for access_type in RAM_ACCESS_TYPES:
            if access_type <= data_type and size % access_type == 0:
                return access_type
        return 1

    def _get_ram_block(self, address: int, size: int, access_type: int) -> bytearray:
        """Send one Get RAM Block request (size <= max_read_size, multiple of access_type)."""
        get_ram_frame = FrameGetRam(address, size, access_type, self.device_info.uc_width)
        get_ram_frame.received = self._xchg_data(get_ram_frame.serialize())
        return get_ram_frame.deserialize()

    def get_ram_array(self, address: int, bytes_to_read: int, data_type: int):
        """Read an array of data from the microcontroller's RAM.

        Reads of any length are split into requests of at most max_read_size bytes; every request reads a
        multiple of the data type, so values are never split between two requests.

        Args:
            address (int): The starting address in RAM to read data from.
            bytes_to_read (int): The number of bytes to read.
            data_type (int): The data type to read (1, 2, 4; 8 is read as two 32-bit words).

        Returns:
            bytearray: The data read from RAM.

        Raises:
            RuntimeError: If device information is not retrieved before reading RAM.
        """
        access_type = self._access_type(bytes_to_read, data_type)
        chunk_size = self.max_read_size - self.max_read_size % access_type
        if bytes_to_read <= chunk_size:
            return self._get_ram_block(address, bytes_to_read, access_type)
        data = bytearray()
        offset = 0
        while offset < bytes_to_read:
            size = min(chunk_size, bytes_to_read - offset)
            data.extend(self._get_ram_block(address + offset, size, access_type))
            offset += size
        return data

    def get_ram(self, address: int, data_type: int) -> bytearray:
        """Read data from the microcontroller's RAM.

        Args:
            address (int): The address to read data from in the microcontroller's RAM.
            data_type (int): The data type (number of bytes) to read: 1, 2, 4 or 8.

        Returns:
            bytearray: The data read from the RAM.

        Raises:
            RuntimeError: If device information is not retrieved before reading RAM.
        """
        return self._get_ram_block(address, data_type, self._access_type(data_type, data_type))

    def put_ram(self, address: int, size: int, value: bytearray):
        """Write data to the microcontroller's RAM.

        Writes of any length are split into requests of at most max_write_size bytes. Values of 1, 2 and 4
        bytes are written with their own data type, 8-byte values as two 32-bit words in one request.

        Args:
            address (int): The address in the microcontroller's RAM to write data to.
            size (int): The size (number of bytes) of the data to write.
            value (bytearray): The data to be written to RAM.

        Returns:
            The response from the microcontroller (of the last request).

        Raises:
            RuntimeError: If device information is not retrieved before writing to RAM.
            ValueError: If value does not contain size bytes.
        """
        value = bytearray(value)
        if len(value) != size:
            raise ValueError(f"put_ram: value has {len(value)} bytes, size is {size}")
        access_type = self._access_type(size)
        chunk_size = self.max_write_size - self.max_write_size % access_type
        result = None
        offset = 0
        while offset < size or offset == 0:
            chunk = value[offset:offset + chunk_size]
            put_ram_frame = FramePutRam(address + offset, access_type, self.device_info.uc_width, chunk)
            put_ram_frame.received = self._xchg_data(put_ram_frame.serialize())
            result = put_ram_frame.deserialize()
            offset += max(len(chunk), 1)
        return result

    def _xchg_data(self, frame):
        """Send a frame to the microcontroller and read the response.

        This method is thread-safe and ensures that only one thread can access the interface at a time.

        Args:
            frame: The frame data to be sent.

        Returns:
            The response from the microcontroller.

        On a timeout or a lost connection (e.g. the device answers with a TCP RST, raised as
        ConnectionResetError), the interface is restarted once and the frame is sent again. Some
        lwIP-based devices reset the first TCP connection after their own reset while they still
        resolve the host's MAC address; the second connection works.
        """
        with self._lock:
            try:
                self.interface.write(frame)
                return self._read_response()
            except (TimeoutError, ConnectionError) as error:
                if not self.interface.initialised:
                    if isinstance(error, TimeoutError):
                        raise TimeoutError("Interface not initialized, check connection parameters.") from error
                    raise
                logging.warning("LNet: %s, restarting interface and retrying once", type(error).__name__)
                self.interface.stop()
                self.interface.start()
                self.interface.write(frame)
                return self._read_response()

    def _read_response(self):
        """Read frames until the response to the pending request arrives.

        Stream frames (SYN 0x02) pushed by the device while waiting are queued for get_stream_frames().

        Returns:
            The response frame.
        """
        while True:
            frame = self.interface.read()
            if frame and frame[0] == LNET_SYN_STREAM:
                self._queue_stream_frame(frame)
                continue
            return frame

    def _queue_stream_frame(self, frame):
        """Store a received stream frame, discarding the oldest one if the queue is full."""
        if len(self._stream_frames) == self._stream_frames.maxlen:
            self.discarded_stream_frames += 1
            logging.debug("LNet: stream queue full, oldest stream frame discarded")
        self._stream_frames.append(bytearray(frame))

    def get_stream_frames(self) -> list:
        """Return and remove all stream frames received so far.

        Stream frames (SYN 0x02) are pushed by the device without a request. They are separated from
        the responses while requests are exchanged.

        Returns:
            list[bytearray]: Raw stream frames (SYN … checksum, including fill bytes), oldest first.
        """
        frames = []
        while True:
            try:
                frames.append(self._stream_frames.popleft())
            except IndexError:
                return frames


    def get_scope_setup(self) -> ScopeSetup:
        """Get the current scope setup.

        Returns:
            ScopeSetup: The current scope setup instance.
        """
        return self.scope_setup
