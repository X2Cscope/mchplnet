"""Assemble LNet (version 5) frames from a byte stream.

The transports (UART, TCP/IP, CAN) deliver an unstructured byte stream. ``LNetFrameAssembler`` finds the frames in
it, independent of how the bytes are split into reads, CAN messages or TCP segments:

* A frame starts with a SYN byte: ``0x55`` for standard (request/response) frames or ``0x02`` for stream frames
  pushed by the device (``LNET_SYN_STREAM``).
* ``SIZE`` counts the data bytes. A ``0x00`` fill byte follows every reserved value (``0x55``/``0x02``) in SIZE,
  NODE and DATA. Fill bytes are not counted and not part of the checksum.
* The checksum is the sum of all frame bytes (SYN included, fill bytes excluded) modulo 256, inverted if it equals
  a reserved value.

Bytes before a SYN are skipped. A reserved value that is not followed by a fill byte marks the start of a new frame
(LNet in-frame SYN detection), and a frame with a wrong checksum is dropped; in both cases parsing restarts at the
byte after the dropped frame's SYN. Bytes after a complete frame are kept for the next frame.

Complete frames are returned raw, i.e. including fill bytes and checksum, as expected by
``LNetFrame.frame_integrity()``.
"""

import logging
from collections import deque

LNET_SYN_STANDARD = 0x55
LNET_SYN_STREAM = 0x02
LNET_RESERVED_VALUES = (LNET_SYN_STANDARD, LNET_SYN_STREAM)
LNET_FILL_BYTE = 0x00

_STATE_SYN = 0
_STATE_SIZE = 1
_STATE_NODE = 2
_STATE_DATA = 3
_STATE_CRC = 4


def lnet_checksum(frame_without_fill: bytes) -> int:
    """Calculate the LNet v5 checksum.

    Args:
        frame_without_fill: SYN, SIZE, NODE and DATA bytes without fill bytes and without checksum.

    Returns:
        int: Checksum byte as sent on the wire (inverted if it equals a reserved value).
    """
    checksum = sum(frame_without_fill) & 0xFF
    if checksum in LNET_RESERVED_VALUES:
        checksum = (~checksum) & 0xFF
    return checksum


class LNetFrameAssembler:
    """Incremental LNet v5 frame assembler with resynchronisation.

    Example:
        >>> assembler = LNetFrameAssembler()
        >>> assembler.feed(bytes([0x55, 0x01, 0x01, 0x00, 0x57, 0x55]))
        >>> assembler.pop_frame().hex()
        '5501010057'
        >>> assembler.pop_frame() is None  # second frame not complete yet
        True
    """

    def __init__(self):
        """Initialize an empty assembler."""
        self._frames = deque()
        self.dropped_frames = 0
        self._reset_frame()

    def _reset_frame(self):
        self._state = _STATE_SYN
        self._raw = bytearray()  # current frame as received, including fill bytes
        self._payload = bytearray()  # current frame without fill bytes (for the checksum)
        self._expect_fill = False
        self._remaining = 0

    def reset(self):
        """Discard all buffered bytes and frames, e.g. after the interface was restarted."""
        self._frames.clear()
        self._reset_frame()

    def feed(self, data: bytes):
        """Process received bytes.

        Args:
            data: Received bytes in any chunking.
        """
        pending = deque(data)
        while pending:
            byte = pending.popleft()
            restart = self._process(byte)
            if restart is not None:
                # Framing error: parse again from the byte after the dropped frame's SYN.
                pending.extendleft(reversed(restart))

    def pop_frame(self):
        """Return the oldest complete frame, or None if no frame is complete.

        Returns:
            bytearray | None: Raw frame (SYN … checksum, including fill bytes).
        """
        return self._frames.popleft() if self._frames else None

    def pending_frames(self) -> int:
        """Return the number of complete frames not yet popped."""
        return len(self._frames)

    def _drop(self, reason: str, current_byte: int) -> bytearray:
        """Drop the current frame and return the bytes to parse again."""
        self.dropped_frames += 1
        logging.warning("LNet: dropped frame (%s): %s", reason, self._raw.hex())
        restart = self._raw[1:] + bytearray([current_byte])
        self._reset_frame()
        return restart

    def _append(self, byte: int):
        self._raw.append(byte)
        self._payload.append(byte)
        self._expect_fill = byte in LNET_RESERVED_VALUES

    def _process(self, byte: int):
        """Process one byte. Returns bytes to parse again after a framing error, otherwise None."""
        if self._state == _STATE_SYN:
            if byte in LNET_RESERVED_VALUES:
                self._raw.append(byte)
                self._payload.append(byte)
                self._state = _STATE_SIZE
            return None

        if self._expect_fill:
            if byte != LNET_FILL_BYTE:
                # The reserved value was the SYN of a new frame (in-frame SYN detection).
                return self._drop("missing fill byte", byte)
            self._raw.append(byte)
            self._expect_fill = False
            if self._state == _STATE_DATA and self._remaining == 0:
                self._state = _STATE_CRC
            return None

        if self._state == _STATE_SIZE:
            self._append(byte)
            self._remaining = byte
            self._state = _STATE_NODE
        elif self._state == _STATE_NODE:
            self._append(byte)
            self._state = _STATE_DATA if self._remaining else _STATE_CRC
        elif self._state == _STATE_DATA:
            self._append(byte)
            self._remaining -= 1
            if self._remaining == 0 and not self._expect_fill:
                self._state = _STATE_CRC
        elif self._state == _STATE_CRC:
            if byte != lnet_checksum(self._payload):
                return self._drop("checksum error", byte)
            self._raw.append(byte)
            self._frames.append(self._raw)
            self._reset_frame()
        return None
