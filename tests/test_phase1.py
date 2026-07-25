import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from compressor.engine import NovaCompressor
from compressor.format import read_nova_file
from decompressor.engine import NovaDecompressor


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


class Phase1RoundtripTests(unittest.TestCase):
    def test_compress_decompress_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original = temp_path / "example.txt"
            compressed = temp_path / "example.nova"
            restored = temp_path / "example_restored.txt"

            original.write_bytes(b"Hello NovaGraph Compressor!\nThis is a phase 1 roundtrip test.\n")

            compressor = NovaCompressor()
            compressor.compress_file(original, compressed)

            decompressor = NovaDecompressor()
            decompressor.decompress_file(compressed, restored)

            self.assertTrue(restored.exists())
            self.assertEqual(sha256_file(original), sha256_file(restored))

    def test_empty_file_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original = temp_path / "empty.bin"
            compressed = temp_path / "empty.nova"
            restored = temp_path / "empty_restored.bin"

            original.write_bytes(b"")

            compressor = NovaCompressor()
            compressor.compress_file(original, compressed)

            decompressor = NovaDecompressor()
            decompressor.decompress_file(compressed, restored)

            self.assertEqual(restored.read_bytes(), b"")
            self.assertEqual(sha256_file(original), sha256_file(restored))

    def test_repeated_pattern_block_compression(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original = temp_path / "repeated.txt"
            compressed = temp_path / "repeated.nova"
            restored = temp_path / "repeated_restored.txt"

            original.write_bytes((b"ABC12345" * 1024) + b"END")

            compressor = NovaCompressor()
            compressor.compress_file(original, compressed)

            decompressor = NovaDecompressor()
            decompressor.decompress_file(compressed, restored)

            self.assertEqual(sha256_file(original), sha256_file(restored))

            blocks, _ = read_nova_file(compressed)
            self.assertEqual(len(blocks), 1)
            self.assertLess(blocks[0].metadata.compressed_size, blocks[0].metadata.uncompressed_size)
            # Accept pattern (1) or Huffman-wrapped pattern (2)
            self.assertIn(blocks[0].metadata.compression_method, (1, 2))
            # Either graph or fractal pattern model is acceptable depending on detector heuristics
            self.assertIn(blocks[0].metadata.pattern_model, (1, 2))

    def test_high_entropy_raw_storage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original = temp_path / "random.bin"
            compressed = temp_path / "random.nova"
            restored = temp_path / "random_restored.bin"

            original.write_bytes(os.urandom(4096))

            compressor = NovaCompressor()
            compressor.compress_file(original, compressed)

            decompressor = NovaDecompressor()
            decompressor.decompress_file(compressed, restored)

            blocks, _ = read_nova_file(compressed)
            self.assertEqual(len(blocks), 1)
            self.assertEqual(blocks[0].metadata.compression_method, 0)
            self.assertEqual(sha256_file(original), sha256_file(restored))


if __name__ == "__main__":
    unittest.main()
