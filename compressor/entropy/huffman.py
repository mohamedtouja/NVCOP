"""A compact Huffman coder operating on bytes.

This implementation builds a frequency table for the input bytes,
serializes the table (256 uint32 values) followed by the bitstream
containing the encoded symbols. Decoder reconstructs the same tree
from the frequency table.

This is not optimized for performance or smallest header size but
is sufficient for prototype and research.
"""
from __future__ import annotations

import heapq
import struct
from typing import Dict, Optional

from compressor.entropy.bitstream import BitWriter, BitReader


class Node:
    def __init__(self, weight: int, symbol: Optional[int] = None, left: "Node" = None, right: "Node" = None):
        self.weight = weight
        self.symbol = symbol
        self.left = left
        self.right = right

    def __lt__(self, other: "Node") -> bool:  # for heapq
        return self.weight < other.weight


def _build_tree(freq: Dict[int, int]) -> Node:
    heap = [Node(w, s) for s, w in freq.items() if w > 0]
    if not heap:
        return Node(0, 0)
    heapq.heapify(heap)
    if len(heap) == 1:
        single = heapq.heappop(heap)
        return Node(single.weight, None, left=single)
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        heapq.heappush(heap, Node(a.weight + b.weight, None, left=a, right=b))
    return heap[0]


def _build_codes(node: Node, prefix: str = "", codes: Dict[int, str] = None) -> Dict[int, str]:
    if codes is None:
        codes = {}
    if node.symbol is not None:
        codes[node.symbol] = prefix or "0"
        return codes
    if node.left is not None:
        _build_codes(node.left, prefix + "0", codes)
    if node.right is not None:
        _build_codes(node.right, prefix + "1", codes)
    return codes


def encode(data: bytes) -> bytes:
    # frequency table for 0..255
    freq = {i: 0 for i in range(256)}
    for b in data:
        freq[b] += 1

    tree = _build_tree(freq)
    codes = _build_codes(tree)

    # write frequency table as 256 little-endian uint32
    header = b"".join(struct.pack("<I", freq[i]) for i in range(256))

    writer = BitWriter()
    for b in data:
        code = codes[b]
        for bit_char in code:
            writer.write_bits(1 if bit_char == "1" else 0, 1)

    body = writer.get_bytes()
    return header + body


def decode(encoded: bytes) -> bytes:
    # read frequency table
    if len(encoded) < 256 * 4:
        raise ValueError("Encoded data too short for Huffman header")
    freq = {}
    pos = 0
    for i in range(256):
        freq[i] = struct.unpack_from("<I", encoded, pos)[0]
        pos += 4

    tree = _build_tree(freq)

    # build decodable structure; traverse bits to produce symbols
    reader = BitReader(encoded[pos:])
    out = bytearray()

    # special-case: if tree has a single symbol, repeat it freq times
    total = sum(freq.values())
    if total == 0:
        return b""
    # If tree.left is a leaf and tree.right is None, it's single symbol
    if tree.left and tree.left.symbol is not None and tree.right is None:
        out.extend(bytes([tree.left.symbol]) * total)
        return bytes(out)

    # decode by walking the tree per bit
    node = tree
    decoded = 0
    try:
        while decoded < total:
            bit = reader.read_bit()
            node = node.right if bit else node.left
            if node is None:
                raise ValueError("Decoding error: walked to a non-node")
            if node.symbol is not None:
                out.append(node.symbol)
                decoded += 1
                node = tree
    except EOFError:
        raise ValueError("Unexpected end of Huffman bitstream")

    return bytes(out)
