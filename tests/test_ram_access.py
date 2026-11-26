"""Tests for Get/Put RAM Block chunking by the device's maximum frame size and the data types it accepts.

A fake device applies the rules of the X2Cscope firmware (doc/lnet/x2cscope_lnet_profile.md, 5.3):
data types 1, 2, 4 only; size a multiple of the data type; request and response must fit into one frame
of the reported maximum frame size.
"""

import unittest
from unittest.mock import Mock

from mchplnet.errors import LNetDeviceError
from mchplnet.framing import LNetFrameAssembler, lnet_checksum
from mchplnet.lnet import LNet
from mchplnet.services.frame_device_info import FrameDeviceInfo

RESERVED = (0x55, 0x02)
BASE = 0x2000_0000
SID_GET_RAM = 0x09
SID_PUT_RAM = 0x0A
MAX_READ_255 = 253  # 255-byte frame - Service ID - Error ID
MAX_READ_64 = 62  # 64-byte frame - Service ID - Error ID
MAX_WRITE_16BIT = 251  # 255-byte frame - Service ID - 2-byte address - data type


def raw_frame(data: bytes) -> bytes:
    """Build a raw LNet response frame (fill bytes, checksum)."""
    payload = bytes([0x55, len(data), 0x01]) + bytes(data)
    raw = bytearray([0x55])
    for byte in payload[1:]:
        raw.append(byte)
        if byte in RESERVED:
            raw.append(0x00)
    raw.append(lnet_checksum(payload))
    return bytes(raw)


def unfill(raw: bytes) -> bytes:
    """Remove fill bytes and checksum: [SYN, SIZE, NODE, data...]."""
    out = bytearray([raw[0]])
    i = 1
    while i < len(raw) - 1:
        out.append(raw[i])
        i += 2 if raw[i] in RESERVED else 1
    return bytes(out)


class FakeDevice:
    """Interface answering Get/Put RAM Block like the X2Cscope firmware, on a simulated RAM."""

    def __init__(self, max_frame_size=255, uc_width=4, size=8192):
        """Create the device with a RAM of `size` bytes at BASE."""
        self.max_frame_size = max_frame_size
        self.uc_width = uc_width
        self.ram = bytearray((i * 7 + 3) & 0xFF for i in range(size))
        self.requests = []  # (service, address, size, type)
        self.initialised = True
        self._response = None

    def write(self, frame):
        """Process one request frame."""
        assembler = LNetFrameAssembler()
        assembler.feed(bytes(frame))
        request = unfill(assembler.pop_frame())
        size_field, data = request[1], request[3:]
        assert size_field <= self.max_frame_size, f"request SIZE {size_field} > {self.max_frame_size}"
        sid, w = data[0], self.uc_width
        address = int.from_bytes(data[1:1 + w], "little") - BASE
        if sid == SID_GET_RAM:
            size, dtype = data[1 + w], data[2 + w]
            self.requests.append(("get", address, size, dtype))
            if dtype not in (1, 2, 4) or size % dtype:
                self._response = raw_frame(bytes([SID_GET_RAM, 0x14]))
            elif size + 2 > self.max_frame_size:
                self._response = raw_frame(bytes([SID_GET_RAM, 0x15]))
            else:
                self._response = raw_frame(bytes([SID_GET_RAM, 0x00]) + self.ram[address:address + size])
        elif sid == SID_PUT_RAM:
            dtype, payload = data[1 + w], data[2 + w:]
            self.requests.append(("put", address, len(payload), dtype))
            if dtype not in (1, 2, 4) or len(payload) % dtype:
                self._response = raw_frame(bytes([SID_PUT_RAM, 0x14]))
            else:
                self.ram[address:address + len(payload)] = payload
                self._response = raw_frame(bytes([SID_PUT_RAM, 0x00]))
        else:
            raise AssertionError(f"unexpected service 0x{sid:02X}")

    def read(self):
        """Return the response to the last request."""
        return bytearray(self._response)


def make_lnet(max_frame_size=255, uc_width=4):
    """Return an LNet connected to a FakeDevice."""
    device = FakeDevice(max_frame_size, uc_width)
    lnet = LNet(device, handshake=False)
    lnet.device_info = Mock(uc_width=uc_width, max_frame_size=max_frame_size)
    return lnet, device


class TestDeviceInfoFrameSize(unittest.TestCase):
    """Get Device Info: maximum target frame size (service data byte 4)."""

    @staticmethod
    def _device_info(max_frame_size):
        data = (bytes([0x00, 0x00]) + (5).to_bytes(2, "little") + (1).to_bytes(2, "little")
                + bytes([max_frame_size]) + (0x8240).to_bytes(2, "little") + b"Jan012026" + b"1200"
                + b"Jan012026" + b"1200" + bytes([0x01]) + bytes(2) + bytes(4) + bytes(4))
        frame = FrameDeviceInfo()
        frame.received = bytearray(raw_frame(data))
        return frame.deserialize()

    def test_max_frame_size_is_parsed(self):
        """The value reported by the device is available as max_frame_size (and the old max_target_size)."""
        info = self._device_info(255)
        self.assertEqual(info.max_frame_size, 255)
        self.assertEqual(info.max_target_size, 255)
        self.assertEqual(self._device_info(64).max_frame_size, 64)

    def test_limits_from_frame_size(self):
        """Read/write limits follow from the frame size and the address width."""
        self.assertEqual(make_lnet(255, 4)[0].max_read_size, 253)
        self.assertEqual(make_lnet(255, 4)[0].max_write_size, 249)
        self.assertEqual(make_lnet(255, 2)[0].max_write_size, 251)
        self.assertEqual(make_lnet(64, 4)[0].max_read_size, 62)

    def test_unknown_frame_size_defaults_to_255(self):
        """Devices reporting 0 (or no device info attribute) use the LNet v5 maximum."""
        self.assertEqual(make_lnet(0, 4)[0].max_read_size, 253)


class TestGetRamChunking(unittest.TestCase):
    """get_ram_array() splits long reads and keeps values whole."""

    def test_small_read_is_one_request(self):
        """Reads up to the limit use one request, as before."""
        lnet, device = make_lnet()
        self.assertEqual(lnet.get_ram_array(BASE + 16, 100, 1), device.ram[16:116])
        self.assertEqual(device.requests, [("get", 16, 100, 1)])

    def test_long_byte_read(self):
        """5000 bytes (default scope buffer) with type 1: 253-byte chunks."""
        lnet, device = make_lnet()
        self.assertEqual(lnet.get_ram_array(BASE, 5000, 1), device.ram[:5000])
        sizes = [r[2] for r in device.requests]
        self.assertEqual(len(sizes), 20)
        self.assertTrue(all(s == MAX_READ_255 for s in sizes[:-1]))
        self.assertEqual(sum(sizes), 5000)

    def test_long_read_keeps_32_bit_values_whole(self):
        """With data type 4 every chunk is a multiple of 4 (252), as the firmware requires."""
        lnet, device = make_lnet()
        self.assertEqual(lnet.get_ram_array(BASE, 600, 4), device.ram[:600])
        self.assertEqual([r[2] for r in device.requests], [252, 252, 96])
        self.assertEqual([r[1] for r in device.requests], [0, 252, 504])

    def test_small_frame_size_device(self):
        """A device reporting 64-byte frames gets requests of at most 62 bytes."""
        lnet, device = make_lnet(max_frame_size=64)
        self.assertEqual(lnet.get_ram_array(BASE, 200, 2), device.ram[:200])
        self.assertTrue(all(r[2] <= MAX_READ_64 and r[2] % 2 == 0 for r in device.requests))

    def test_read_of_64_bit_value(self):
        """An 8-byte variable is read as two 32-bit words in one request (type 8 is rejected by the device)."""
        lnet, device = make_lnet()
        self.assertEqual(lnet.get_ram(BASE + 40, 8), device.ram[40:48])
        self.assertEqual(device.requests, [("get", 40, 8, 4)])

    def test_device_rejects_type_8(self):
        """The fake device behaves like the firmware: data type 8 is a format error."""
        lnet, _ = make_lnet()
        with self.assertRaises(LNetDeviceError) as ctx:
            lnet._get_ram_block(BASE, 8, 8)
        self.assertEqual(ctx.exception.error_id, 0x14)


class TestPutRamChunking(unittest.TestCase):
    """put_ram() writes values of any width and long buffers."""

    def test_32_bit_value(self):
        """A 4-byte value: one request with type 4, as before."""
        lnet, device = make_lnet()
        lnet.put_ram(BASE + 8, 4, bytearray(b"\x11\x22\x33\x44"))
        self.assertEqual(device.ram[8:12], b"\x11\x22\x33\x44")
        self.assertEqual(device.requests, [("put", 8, 4, 4)])

    def test_64_bit_value(self):
        """An 8-byte value (double on PIC32/ARM) is written as two 32-bit words in one request."""
        lnet, device = make_lnet()
        value = bytearray(range(1, 9))
        lnet.put_ram(BASE + 16, 8, value)
        self.assertEqual(device.ram[16:24], value)
        self.assertEqual(device.requests, [("put", 16, 8, 4)])

    def test_odd_size_uses_bytes(self):
        """3 bytes are written with type 1."""
        lnet, device = make_lnet()
        lnet.put_ram(BASE, 3, bytearray(b"abc"))
        self.assertEqual(device.ram[0:3], b"abc")
        self.assertEqual(device.requests[0][3], 1)

    def test_long_write_is_split(self):
        """600 bytes on a 32-bit device: chunks of at most 249 bytes, multiples of 4."""
        lnet, device = make_lnet()
        value = bytearray((i * 13) & 0xFF for i in range(600))
        lnet.put_ram(BASE + 100, 600, value)
        self.assertEqual(device.ram[100:700], value)
        self.assertEqual([r[2] for r in device.requests], [248, 248, 104])

    def test_16_bit_device(self):
        """16-bit devices have 2-byte addresses, so one more data byte fits (251)."""
        lnet, device = make_lnet(uc_width=2)
        value = bytearray(range(255)) * 2
        lnet.put_ram(BASE & 0xFFFF, 510, value)
        self.assertTrue(all(r[2] <= MAX_WRITE_16BIT for r in device.requests))

    def test_value_length_must_match(self):
        """A value of the wrong length is rejected before anything is sent."""
        lnet, device = make_lnet()
        with self.assertRaises(ValueError):
            lnet.put_ram(BASE, 4, bytearray(2))
        self.assertEqual(device.requests, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
