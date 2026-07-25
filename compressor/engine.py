from pathlib import Path

from compressor.analyzer import analyze_block, select_compression_method, select_pattern_model
from compressor.block import Block, BlockMetadata
from compressor.format import write_nova_file
from compressor.graph.pattern_search import PatternCandidate, build_pattern_encoded_block
from compressor.entropy.huffman import encode as huffman_encode
from compressor.utils.hashing import merkle_root_hash, sha256_bytes

BLOCK_SIZE = 1024 * 1024
COMPRESSION_METHOD_RAW = 0
COMPRESSION_METHOD_PATTERN = 1
COMPRESSION_METHOD_HUFFMAN = 2
PATTERN_MODEL_NONE = 0
PATTERN_MODEL_FRACTAL = 2
PATTERN_MODEL_TOKEN = 3


class NovaCompressor:
    def __init__(self, block_size: int = BLOCK_SIZE):
        self.block_size = block_size

    def _compress_block(self, block_id: int, payload: bytes) -> Block:
        method, pattern_model, candidate = analyze_block(payload)
        if method == COMPRESSION_METHOD_RAW:
            compressed_data = payload
        elif method == COMPRESSION_METHOD_PATTERN and candidate is not None:
            token_stream = build_pattern_encoded_block(payload, candidate.pattern, candidate.non_overlapping_offsets)
            compressed_data = huffman_encode(token_stream)
            method = COMPRESSION_METHOD_HUFFMAN
            if len(compressed_data) >= len(payload):
                compressed_data = payload
                method = COMPRESSION_METHOD_RAW
                pattern_model = PATTERN_MODEL_NONE
        elif method == COMPRESSION_METHOD_HUFFMAN:
            if pattern_model == PATTERN_MODEL_TOKEN and isinstance(candidate, bytes):
                compressed_data = huffman_encode(candidate)
            elif isinstance(candidate, PatternCandidate):
                token_stream = build_pattern_encoded_block(payload, candidate.pattern, candidate.non_overlapping_offsets)
                compressed_data = huffman_encode(token_stream)
            else:
                raise NotImplementedError("Huffman block requires a token stream or pattern candidate")
            if len(compressed_data) >= len(payload):
                compressed_data = payload
                method = COMPRESSION_METHOD_RAW
                pattern_model = PATTERN_MODEL_NONE
        else:
            raise NotImplementedError(f"Compression method {method} is not supported")

        block_hash = sha256_bytes(payload)
        metadata = BlockMetadata(
            block_id=block_id,
            uncompressed_size=len(payload),
            compressed_size=len(compressed_data),
            compression_method=method,
            pattern_model=pattern_model,
            hash_bytes=block_hash,
        )
        return Block(metadata=metadata, data=compressed_data)

    def compress_file(self, input_path: Path, output_path: Path) -> None:
        blocks = []
        with open(input_path, "rb") as stream:
            block_id = 0
            while True:
                chunk = stream.read(self.block_size)
                if not chunk:
                    break
                block = self._compress_block(block_id, chunk)
                blocks.append(block)
                block_id += 1

        root_hash = merkle_root_hash([block.metadata.hash_bytes for block in blocks])
        write_nova_file(output_path, blocks, root_hash)
