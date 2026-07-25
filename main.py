from pathlib import Path

from compressor.engine import NovaCompressor
from decompressor.engine import NovaDecompressor


def _print_usage():
    print("NovaGraph Compressor (NGC) Phase 1")
    print("Usage:")
    print("  python main.py compress <input_file> <output_file>")
    print("  python main.py decompress <input_file> <output_file>")


def main() -> None:
    import sys

    if len(sys.argv) != 4:
        _print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()
    input_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    if command == "compress":
        compressor = NovaCompressor()
        compressor.compress_file(input_path, output_path)
        print(f"Compressed {input_path} -> {output_path}")
    elif command == "decompress":
        decompressor = NovaDecompressor()
        decompressor.decompress_file(input_path, output_path)
        print(f"Decompressed {input_path} -> {output_path}")
    else:
        _print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
