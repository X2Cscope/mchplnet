"""Tests for LNet frame assembly from byte streams (SYN detection, fill bytes, checksum, resync).

Covers the assembler itself, its use in the UART, TCP/IP and CAN transports, the separation of stream
frames (SYN 0x02) from responses in LNet, and the Load Parameter scope-version byte.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from mchplnet.framing import LNET_RESERVED_VALUES, LNetFrameAssembler, lnet_checksum
from mchplnet.interfaces.can import LNetCan
from mchplnet.interfaces.tcp_ip import LNetTcpIp
from mchplnet.interfaces.uart import LNetSerial
from mchplnet.lnet import LNet
from mchplnet.services.frame_load_parameter import FrameLoadParameter


def build_frame(syn: int, data: list, node: int = 0x01) -> bytearray:
    """Build a raw LNet v5 frame with fill bytes and checksum (independent reference implementation)."""
    payload = [syn, len(data), node, *data]
    raw = bytearray([syn])
    for byte in payload[1:]:
        raw.append(byte)
        if byte in LNET_RESERVED_VALUES:
            raw.append(0x00)
    raw.append(lnet_checksum(bytes(payload)))
    return raw


# Frames from the LNet v5 documentation (section 8) and doc/scope_streaming.md (section 12)
DEVICE_INFO_REQUEST = bytearray([0x55, 0x01, 0x01, 0x00, 0x57])
PUT_RAM_REQUEST = bytearray(  # LNet v5 doc 8.6: fill bytes after 0x02 and 0x55 values
    [0x55, 0x0C, 0x01, 0x0A, 0x00, 0x96, 0x00, 0x00, 0x02, 0x00, 0xEF, 0xBE, 0xFE, 0xCA, 0x02, 0x00, 0x55, 0x00, 0xD0]
)
ERASE_FLASH_RESPONSE = bytearray([0x55, 0x02, 0x00, 0x01, 0x04, 0x00, 0x5C])  # LNet v5 doc 8.2: fill after SIZE
STREAM_FRAME = bytearray(  # scope_streaming.md 12.2: SYN 0x02, k = 2 followed by a fill byte
    [0x02, 0x23, 0x01, 0x01, 0x00, 0xE8, 0x03, 0x00, 0x00, 0x64, 0x00, 0x00, 0x00, 0x02, 0x00]
    + [0xE8, 0x03, 0x00, 0x00, 0x00, 0x00, 0xC0, 0x3F, 0xFE, 0xFF, 0xFF, 0xFF]
    + [0xE9, 0x03, 0x00, 0x00, 0x00, 0x00, 0xC0, 0x3F, 0xFE, 0xFF, 0xFF, 0xFF, 0x43]
)
DOC_FRAMES = [DEVICE_INFO_REQUEST, PUT_RAM_REQUEST, ERASE_FLASH_RESPONSE, STREAM_FRAME]


def assemble(chunks) -> list:
    """Feed chunks into a new assembler and return all complete frames."""
    assembler = LNetFrameAssembler()
    frames = []
    for chunk in chunks:
        assembler.feed(bytes(chunk))
        while (frame := assembler.pop_frame()) is not None:
            frames.append(frame)
    return frames


class TestChecksum(unittest.TestCase):
    """Checksum calculation against the documented frames."""

    def test_documented_checksums(self):
        """build_frame (using lnet_checksum) reproduces the documented frames byte by byte."""
        self.assertEqual(build_frame(0x55, [0x00]), DEVICE_INFO_REQUEST)
        self.assertEqual(
            build_frame(0x55, [0x0A, 0x00, 0x96, 0x00, 0x00, 0x02, 0xEF, 0xBE, 0xFE, 0xCA, 0x02, 0x55]),
            PUT_RAM_REQUEST,
        )
        self.assertEqual(build_frame(0x55, [0x04, 0x00]), ERASE_FLASH_RESPONSE)

    def test_checksum_inversion(self):
        """A checksum equal to a reserved value is sent inverted (0x55 -> 0xAA, 0x02 -> 0xFD)."""
        self.assertEqual(lnet_checksum(bytes([0x55, 0x01, 0x01, 0xFE])), 0xAA)  # sum 0x155 -> 0x55
        self.assertEqual(lnet_checksum(bytes([0x55, 0x01, 0x01, 0xAB])), 0xFD)  # sum 0x102 -> 0x02


class TestFrameAssembler(unittest.TestCase):
    """LNetFrameAssembler behaviour."""

    def test_documented_frames_in_one_chunk(self):
        """Each documented frame is recognised unchanged (fill bytes and checksum kept)."""
        for frame in DOC_FRAMES:
            with self.subTest(frame=frame.hex()):
                self.assertEqual(assemble([frame]), [frame])

    def test_byte_by_byte(self):
        """Frames are assembled independent of chunking, even one byte at a time."""
        for frame in DOC_FRAMES:
            with self.subTest(frame=frame.hex()):
                self.assertEqual(assemble([[b] for b in frame]), [frame])

    def test_every_split_point(self):
        """A frame split into two chunks at any position is assembled correctly."""
        for frame in DOC_FRAMES:
            for split in range(1, len(frame)):
                with self.subTest(frame=frame.hex(), split=split):
                    self.assertEqual(assemble([frame[:split], frame[split:]]), [frame])

    def test_back_to_back_frames(self):
        """Several frames in one chunk (e.g. stream frames pushed by the device) are returned in order."""
        stream = STREAM_FRAME + PUT_RAM_REQUEST + STREAM_FRAME + ERASE_FLASH_RESPONSE
        self.assertEqual(assemble([stream]), [STREAM_FRAME, PUT_RAM_REQUEST, STREAM_FRAME, ERASE_FLASH_RESPONSE])

    def test_leftover_bytes_are_kept(self):
        """Bytes of the next frame after a complete frame are kept for the next frame."""
        assembler = LNetFrameAssembler()
        assembler.feed(bytes(DEVICE_INFO_REQUEST + STREAM_FRAME[:10]))
        self.assertEqual(assembler.pop_frame(), DEVICE_INFO_REQUEST)
        self.assertIsNone(assembler.pop_frame())
        assembler.feed(bytes(STREAM_FRAME[10:]))
        self.assertEqual(assembler.pop_frame(), STREAM_FRAME)

    def test_garbage_before_syn_is_skipped(self):
        """Bytes before the first SYN are ignored."""
        self.assertEqual(assemble([bytes([0x00, 0x13, 0xFF, 0x08]) + DEVICE_INFO_REQUEST]), [DEVICE_INFO_REQUEST])

    def test_bad_checksum_is_dropped_and_next_frame_found(self):
        """A frame with a wrong checksum is dropped; the following frame is still found."""
        corrupted = bytearray(DEVICE_INFO_REQUEST)
        corrupted[-1] ^= 0x01
        assembler = LNetFrameAssembler()
        with self.assertLogs(level="WARNING"):
            assembler.feed(bytes(corrupted + PUT_RAM_REQUEST))
        self.assertEqual(assembler.pop_frame(), PUT_RAM_REQUEST)
        self.assertIsNone(assembler.pop_frame())
        self.assertEqual(assembler.dropped_frames, 1)

    def test_truncated_frame_resyncs_on_in_frame_syn(self):
        """A truncated frame followed by a new frame: the SYN without fill byte starts the new frame."""
        truncated = bytearray([0x55, 0x05, 0x01, 0x07])  # SIZE 5, only 1 data byte received
        with self.assertLogs(level="WARNING"):
            frames = assemble([truncated + DEVICE_INFO_REQUEST])
        self.assertEqual(frames, [DEVICE_INFO_REQUEST])

    def test_incomplete_frame_is_not_returned(self):
        """An incomplete frame stays pending."""
        assembler = LNetFrameAssembler()
        assembler.feed(bytes(PUT_RAM_REQUEST[:-1]))
        self.assertIsNone(assembler.pop_frame())
        self.assertEqual(assembler.pending_frames(), 0)

    def test_reset_discards_partial_frame(self):
        """reset() discards partial frames, e.g. after reconnecting."""
        assembler = LNetFrameAssembler()
        assembler.feed(bytes(PUT_RAM_REQUEST[:8]))
        assembler.reset()
        assembler.feed(bytes(DEVICE_INFO_REQUEST))
        self.assertEqual(assembler.pop_frame(), DEVICE_INFO_REQUEST)

    def test_maximum_size_frame_with_reserved_data(self):
        """A 255-byte data frame consisting of reserved values (worst-case fill bytes) is assembled."""
        frame = build_frame(0x55, [0x09, 0x00] + [0x55, 0x02] * 126 + [0x55])
        self.assertEqual(len(frame), 3 + 255 * 2 - 2 + 1)  # every data byte except SID/ERR is escaped
        self.assertEqual(assemble([frame[:100], frame[100:]]), [frame])


class TestSerialFraming(unittest.TestCase):
    """UART transport uses the assembler."""

    def _interface(self, reads, in_waiting):
        with patch("serial.Serial") as mock_serial:
            port = mock_serial.return_value
            port.read.side_effect = reads
            type(port).in_waiting = property(lambda _: in_waiting.pop(0) if in_waiting else 0)
            interface = LNetSerial(port="COM1")
            interface.start()
        return interface, port

    def test_two_frames_in_one_read(self):
        """Two frames received together: the second is returned without reading the port again."""
        data = bytes(DEVICE_INFO_REQUEST + STREAM_FRAME)
        interface, port = self._interface([data[:1], data[1:]], [len(data) - 1])
        self.assertEqual(interface.read(), DEVICE_INFO_REQUEST)
        self.assertEqual(interface.read(), STREAM_FRAME)
        self.assertEqual(port.read.call_count, 2)

    def test_timeout_raises_timeout_error(self):
        """No byte within the serial timeout raises TimeoutError (not TypeError)."""
        interface, _ = self._interface([b""], [])
        with self.assertRaises(TimeoutError):
            interface.read()


class TestTcpFraming(unittest.TestCase):
    """TCP/IP transport uses the assembler."""

    def _interface(self, chunks):
        with patch("socket.socket") as mock_socket:
            sock = mock_socket.return_value
            sock.recv.side_effect = chunks
            interface = LNetTcpIp(host="localhost")
            interface.start()
        return interface, sock

    def test_segment_with_two_frames(self):
        """A TCP segment with two frames: no bytes of the second frame are lost."""
        interface, sock = self._interface([bytes(STREAM_FRAME + PUT_RAM_REQUEST)])
        self.assertEqual(interface.read(), STREAM_FRAME)
        self.assertEqual(interface.read(), PUT_RAM_REQUEST)
        self.assertEqual(sock.recv.call_count, 1)

    def test_frame_split_over_segments(self):
        """A frame split over several segments is assembled."""
        interface, _ = self._interface([bytes(PUT_RAM_REQUEST[:3]), bytes(PUT_RAM_REQUEST[3:12]),
                                        bytes(PUT_RAM_REQUEST[12:])])
        self.assertEqual(interface.read(), PUT_RAM_REQUEST)

    def test_connection_closed(self):
        """recv() returning no data means the device closed the connection."""
        interface, _ = self._interface([b""])
        with self.assertRaises(ConnectionError):
            interface.read()


class TestCanFraming(unittest.TestCase):
    """CAN transport uses the assembler."""

    def setUp(self):
        """Mock the python-can bus."""
        self.bus_patcher = patch("can.interface.Bus")
        self.bus = self.bus_patcher.start().return_value
        self.bus._is_shutdown = False

    def tearDown(self):
        """Stop mocking."""
        self.bus_patcher.stop()

    @staticmethod
    def _msg(data, arbitration_id=0x100):
        msg = MagicMock()
        msg.arbitration_id = arbitration_id
        msg.data = bytearray(data)
        return msg

    def _messages(self, raw):
        return [self._msg(raw[i:i + 8]) for i in range(0, len(raw), 8)]

    def test_frame_over_several_messages(self):
        """A frame fragmented into 8-byte messages, with foreign IDs and receive timeouts in between."""
        msgs = self._messages(PUT_RAM_REQUEST)
        self.bus.recv.side_effect = [None, msgs[0], self._msg([0x55, 0x01], 0x200), None] + msgs[1:]
        interface = LNetCan(bustype="pcan_usb", channel=1, id_rx=0x100)
        interface.start()
        self.assertEqual(interface.read(), PUT_RAM_REQUEST)

    def test_back_to_back_frames(self):
        """Stream frames sent back to back: the message holding the end of one frame and the start of the next."""
        msgs = self._messages(STREAM_FRAME + STREAM_FRAME)
        self.bus.recv.side_effect = msgs
        interface = LNetCan(bustype="pcan_usb", channel=1, id_rx=0x100)
        interface.start()
        self.assertEqual(interface.read(), STREAM_FRAME)
        self.assertEqual(interface.read(), STREAM_FRAME)

    def test_incomplete_frame_times_out(self):
        """An incomplete frame raises TimeoutError instead of returning partial data."""
        first = [self._msg(PUT_RAM_REQUEST[:8])]

        def recv(timeout):
            if first:
                return first.pop()
            time.sleep(timeout)  # like python-can: wait for the receive timeout, then return None
            return None

        self.bus.recv.side_effect = recv
        interface = LNetCan(bustype="pcan_usb", channel=1, id_rx=0x100)
        interface.start()
        with patch("mchplnet.interfaces.can.LNET_FRAME_TIMEOUT", 0.05), self.assertRaises(TimeoutError):
            interface.read()


class FrameQueueInterface:
    """Minimal interface returning prepared frames."""

    def __init__(self, frames):
        """Store the frames returned by read(), in order."""
        self.frames = list(frames)
        self.written = []
        self.initialised = True

    def write(self, data):
        """Record written data."""
        self.written.append(data)

    def read(self):
        """Return the next prepared frame."""
        return self.frames.pop(0)


class TestStreamFrameSeparation(unittest.TestCase):
    """LNet separates stream frames (SYN 0x02) from responses."""

    def test_stream_frames_are_queued_not_returned(self):
        """Stream frames arriving before the response are queued; the response is returned."""
        response = build_frame(0x55, [0x09, 0x00, 0x12, 0x34])
        interface = FrameQueueInterface([STREAM_FRAME, STREAM_FRAME, response])
        lnet = LNet(interface, handshake=False)
        self.assertEqual(lnet._xchg_data(bytearray([0x55])), response)
        self.assertEqual(lnet.get_stream_frames(), [STREAM_FRAME, STREAM_FRAME])
        self.assertEqual(lnet.get_stream_frames(), [])

    def test_stream_queue_is_bounded(self):
        """When nobody consumes stream frames, the oldest are discarded and counted."""
        response = build_frame(0x55, [0x00, 0x00])
        first = bytearray(STREAM_FRAME)
        with patch("mchplnet.lnet.STREAM_QUEUE_MAX_FRAMES", 2):
            lnet = LNet(FrameQueueInterface([first, STREAM_FRAME, STREAM_FRAME, response]), handshake=False)
        lnet._xchg_data(bytearray([0x55]))
        self.assertEqual(len(lnet.get_stream_frames()), 2)
        self.assertEqual(lnet.discarded_stream_frames, 1)


class TestLoadParameterScopeVersion(unittest.TestCase):
    """Load Parameter (scope block) keeps the last byte, the scope version."""

    @staticmethod
    def _load_response(version_byte: int) -> bytearray:
        scope_data = [0x00, 0x04, 0x00, 0x00]  # state, channels, prescaler
        scope_data += [0x10, 0x00, 0x00, 0x00]  # data array pointer
        scope_data += [0x00, 0x20, 0x00, 0x20]  # data array address
        scope_data += [0x00] * 8  # trigger delay, trigger event position
        scope_data += [0x88, 0x13, 0x00, 0x00] * 2  # used length, array size (5000)
        scope_data += [version_byte]
        return build_frame(0x55, [0x11, 0x00, *scope_data])

    def _parse(self, version_byte: int):
        frame = FrameLoadParameter()
        frame.received = self._load_response(version_byte)
        return frame.deserialize()

    def test_scope_version_is_parsed(self):
        """The last data byte (0x80 + scope version) is no longer cut off."""
        data = self._parse(0x82)
        self.assertEqual(data.scope_version, 0x82)
        self.assertEqual(data.scope_protocol_version, 2)
        self.assertEqual(data.data_array_size, 5000)
        self.assertFalse(data.supports_streaming)

    def test_streaming_support_detected(self):
        """Scope version 3 (byte 0x83) means scope streaming is supported."""
        self.assertTrue(self._parse(0x83).supports_streaming)

    def test_missing_version_flag(self):
        """A version byte without bit 7 is treated as 'not reported'."""
        self.assertEqual(self._parse(0x03).scope_protocol_version, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
