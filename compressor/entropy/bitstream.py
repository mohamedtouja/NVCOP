"""Simple bit-level writer/reader used by the Huffman coder.

This is a compact, dependency-free implementation suitable for unit
testing and small data sizes.
"""
from typing import ByteString


class BitWriter:
    def __init__(self) -> None:
        self._bits = 0
        self._count = 0
        self._out = bytearray()

    def write_bits(self, value: int, count: int) -> None:
        # write `count` low-order bits from value, MSB-first into stream
        for i in range(count - 1, -1, -1):
            bit = (value >> i) & 1
            self._bits = (self._bits << 1) | bit
            self._count += 1
            if self._count == 8:
                self._out.append(self._bits & 0xFF)
                self._bits = 0
                self._count = 0

    def get_bytes(self) -> bytes:
        if self._count > 0:
            # pad remaining bits with zeros
            self._out.append((self._bits << (8 - self._count)) & 0xFF)
            self._bits = 0
            self._count = 0
        return bytes(self._out)


class BitReader:
    def __init__(self, data: ByteString) -> None:
        self._data = data
        self._pos = 0
        self._bits = 0
        self._count = 0

    def read_bit(self) -> int:
        if self._count == 0:
            if self._pos >= len(self._data):
                raise EOFError("No more bits")
            self._bits = self._data[self._pos]
            self._pos += 1
            self._count = 8
        self._count -= 1
        return (self._bits >> self._count) & 1

    def read_bits(self, count: int) -> int:
        value = 0
        for _ in range(count):
            value = (value << 1) | self.read_bit()
        return value
