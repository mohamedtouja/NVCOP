from dataclasses import dataclass


@dataclass
class BlockMetadata:
    block_id: int
    uncompressed_size: int
    compressed_size: int
    compression_method: int
    pattern_model: int
    hash_bytes: bytes


@dataclass
class Block:
    metadata: BlockMetadata
    data: bytes

    @property
    def uncompressed_size(self) -> int:
        return self.metadata.uncompressed_size

    @property
    def compressed_size(self) -> int:
        return self.metadata.compressed_size
