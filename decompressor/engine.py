from pathlib import Path

from compressor.format import read_nova_file
from compressor.graph.pattern_search import decode_pattern_encoded_block
from compressor.entropy.huffman import decode as huffman_decode
from compressor.tokenizer import decode_token_stream
from compressor.utils.hashing import merkle_root_hash, sha256_bytes
from compressor.block import Block

COMPRESSION_METHOD_RAW = 0
COMPRESSION_METHOD_PATTERN = 1
COMPRESSION_METHOD_HUFFMAN = 2


class NovaDecompressor:
    def _decompress_block(self, block: Block) -> bytes:
        if block.metadata.compression_method == COMPRESSION_METHOD_RAW:
            return block.data
        if block.metadata.compression_method == COMPRESSION_METHOD_PATTERN:
            return decode_pattern_encoded_block(block.data)
        if block.metadata.compression_method == COMPRESSION_METHOD_HUFFMAN:
            decoded = huffman_decode(block.data)
            if decoded.startswith(b"TK"):
                return decode_token_stream(decoded)
            return decode_pattern_encoded_block(decoded)
        raise NotImplementedError(f"Compression method {block.metadata.compression_method} is not supported")

    def decompress_file(self, input_path: Path, output_path: Path) -> None:
        blocks, merkle_root = read_nova_file(input_path)
        block_hashes = []

        with open(output_path, "wb") as out_handle:
            for block in blocks:
                payload = self._decompress_block(block)
                if len(payload) != block.metadata.uncompressed_size:
                    raise ValueError("Block size mismatch during decompression")
                computed_hash = sha256_bytes(payload)
                if computed_hash != block.metadata.hash_bytes:
                    raise ValueError(f"Block hash mismatch for block {block.metadata.block_id}")
                out_handle.write(payload)
                block_hashes.append(computed_hash)

        computed_root = merkle_root_hash(block_hashes)
        if computed_root != merkle_root:
            raise ValueError("Merkle root verification failed")
