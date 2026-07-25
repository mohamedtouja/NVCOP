import struct
from typing import Iterable, Iterator

from compressor.block import Block, BlockMetadata

MAGIC = b"NOVA"
VERSION = 1
HEADER_STRUCT = struct.Struct("<4sH I 32s")
BLOCK_HEADER_STRUCT = struct.Struct("<I I I B B 32s")


class NovaFormatError(Exception):
    pass


def pack_header(block_count: int, merkle_root: bytes) -> bytes:
    return HEADER_STRUCT.pack(MAGIC, VERSION, block_count, merkle_root)


def unpack_header(raw: bytes) -> tuple[int, bytes]:
    if len(raw) != HEADER_STRUCT.size:
        raise NovaFormatError("Invalid NOVA header size")
    magic, version, block_count, merkle_root = HEADER_STRUCT.unpack(raw)
    if magic != MAGIC:
        raise NovaFormatError("Invalid NOVA magic")
    if version != VERSION:
        raise NovaFormatError(f"Unsupported NOVA version {version}")
    return block_count, merkle_root


def serialize_block(block: Block) -> bytes:
    header = BLOCK_HEADER_STRUCT.pack(
        block.metadata.block_id,
        block.metadata.uncompressed_size,
        block.metadata.compressed_size,
        block.metadata.compression_method,
        block.metadata.pattern_model,
        block.metadata.hash_bytes,
    )
    return header + block.data


def iter_blocks_from_stream(stream) -> Iterator[Block]:
    while True:
        header_bytes = stream.read(BLOCK_HEADER_STRUCT.size)
        if not header_bytes:
            return
        if len(header_bytes) != BLOCK_HEADER_STRUCT.size:
            raise NovaFormatError("Unexpected truncated block header")
        block_id, uncompressed_size, compressed_size, compression_method, pattern_model, hash_bytes = BLOCK_HEADER_STRUCT.unpack(
            header_bytes
        )
        data = stream.read(compressed_size)
        if len(data) != compressed_size:
            raise NovaFormatError("Unexpected truncated block payload")
        metadata = BlockMetadata(
            block_id=block_id,
            uncompressed_size=uncompressed_size,
            compressed_size=compressed_size,
            compression_method=compression_method,
            pattern_model=pattern_model,
            hash_bytes=hash_bytes,
        )
        yield Block(metadata=metadata, data=data)


def write_nova_file(path, blocks: Iterable[Block], merkle_root: bytes) -> None:
    blocks_list = list(blocks)
    with open(path, "wb") as handle:
        handle.write(pack_header(len(blocks_list), merkle_root))
        for block in blocks_list:
            handle.write(serialize_block(block))


def read_nova_file(path) -> tuple[list[Block], bytes]:
    with open(path, "rb") as handle:
        header = handle.read(HEADER_STRUCT.size)
        block_count, merkle_root = unpack_header(header)
        blocks = list(iter_blocks_from_stream(handle))
        if len(blocks) != block_count:
            raise NovaFormatError("Block count does not match header")
        return blocks, merkle_root
