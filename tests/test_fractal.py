import unittest
from compressor.fractal.detector import detect_fractal


class FractalDetectorTests(unittest.TestCase):
    def test_detect_simple_repetition(self):
        data = b"ABC" * 200
        res = detect_fractal(data, min_len=1, max_len=8, min_repeats=2, similarity_threshold=0.7)
        self.assertIsNotNone(res)
        pattern, count = res
        self.assertEqual(pattern, b"ABC")
        self.assertGreaterEqual(count, 100)

    def test_no_false_positive_random(self):
        import os

        data = os.urandom(1024)
        res = detect_fractal(data, min_len=1, max_len=8, min_repeats=2, similarity_threshold=0.7)
        self.assertIsNone(res)

    def test_fractal_block_compression(self):
        from pathlib import Path
        import tempfile

        from compressor.engine import NovaCompressor
        from decompressor.engine import NovaDecompressor
        from compressor.format import read_nova_file

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original = temp_path / "fractal.bin"
            compressed = temp_path / "fractal.nova"
            restored = temp_path / "fractal_restored.bin"

            # build simple fractal: a small pattern repeated many times
            original.write_bytes(b"XYZ" * 4096)

            compressor = NovaCompressor()
            compressor.compress_file(original, compressed)

            decompressor = NovaDecompressor()
            decompressor.decompress_file(compressed, restored)

            self.assertEqual(original.read_bytes(), restored.read_bytes())

            blocks, _ = read_nova_file(compressed)
            self.assertEqual(len(blocks), 1)
            # Expect pattern compression to be used for fractal data
            # Accept direct pattern (1) or Huffman-wrapped pattern (2)
            self.assertIn(blocks[0].metadata.compression_method, (1, 2))
            self.assertEqual(blocks[0].metadata.pattern_model, 2)


if __name__ == "__main__":
    unittest.main()
