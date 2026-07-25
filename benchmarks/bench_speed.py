import os
import time
import zlib
from pathlib import Path

from compressor import analyzer as compressor_analyzer
from compressor.engine import NovaCompressor
from decompressor.engine import NovaDecompressor
from compressor.format import read_nova_file

SIZES = [1 * 1024 * 1024, 4 * 1024 * 1024]


def make_sample_files(base_dir: Path):
    base_dir.mkdir(parents=True, exist_ok=True)
    files = []

    # Repetitive pattern file
    p = base_dir / "repeated.bin"
    with open(p, "wb") as f:
        f.write((b"ABC12345" * (SIZES[-1] // 8)) + b"END")
    files.append(p)

    # Random binary
    import os

    r = base_dir / "random.bin"
    with open(r, "wb") as f:
        f.write(os.urandom(SIZES[-1]))
    files.append(r)

    # Text-like file
    t = base_dir / "text.txt"
    with open(t, "wb") as f:
        chunk = (b"the quick brown fox jumps over the lazy dog\n" * 1024)
        repeat = SIZES[-1] // len(chunk) + 1
        f.write(chunk * repeat)
    files.append(t)

    return files


def measure_nova(path: Path, tmp_out: Path) -> dict:
    compressor = NovaCompressor()
    decompressor = NovaDecompressor()

    compressor_analyzer.reset_stats()
    orig_size = path.stat().st_size

    t0 = time.perf_counter()
    compressor.compress_file(path, tmp_out)
    t1 = time.perf_counter()

    comp_size = tmp_out.stat().st_size

    t2 = time.perf_counter()
    decompressor.decompress_file(tmp_out, tmp_out.with_suffix('.restored'))
    t3 = time.perf_counter()

    return {
        "orig_size": orig_size,
        "comp_size": comp_size,
        "compress_time": t1 - t0,
        "decompress_time": t3 - t2,
        "skipped_search_blocks": compressor_analyzer.skipped_search_blocks,
    }


def measure_zlib(path: Path) -> dict:
    orig_size = path.stat().st_size
    data = path.read_bytes()

    t0 = time.perf_counter()
    compressed = zlib.compress(data)
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    decompressed = zlib.decompress(compressed)
    t3 = time.perf_counter()

    assert decompressed == data

    return {
        "orig_size": orig_size,
        "comp_size": len(compressed),
        "compress_time": t1 - t0,
        "decompress_time": t3 - t2,
    }


def pretty_mb_s(size_bytes, seconds):
    if seconds <= 0:
        return "inf"
    return f"{(size_bytes / (1024*1024))/seconds:.2f} MB/s"


def run_all():
    base = Path("bench_data")
    os.chdir(Path(__file__).parent)
    files = make_sample_files(base)

    print("Benchmarking NovaGraph Compressor vs zlib")
    print()

    for f in files:
        print(f"File: {f.name} size={f.stat().st_size}")

        nova_out = f.with_suffix('.nova')
        result_nova = measure_nova(f, nova_out)
        print(" Nova:")
        print(f"  compressed={result_nova['comp_size']} ratio={(result_nova['comp_size']/result_nova['orig_size']):.3f}")
        print(f"  compress_time={result_nova['compress_time']:.4f}s ({pretty_mb_s(result_nova['orig_size'], result_nova['compress_time'])})")
        print(f"  decompress_time={result_nova['decompress_time']:.4f}s ({pretty_mb_s(result_nova['orig_size'], result_nova['decompress_time'])})")
        print(f"  skipped_search_blocks={result_nova['skipped_search_blocks']}")

        z = measure_zlib(f)
        print(" zlib:")
        print(f"  compressed={z['comp_size']} ratio={(z['comp_size']/z['orig_size']):.3f}")
        print(f"  compress_time={z['compress_time']:.4f}s ({pretty_mb_s(z['orig_size'], z['compress_time'])})")
        print(f"  decompress_time={z['decompress_time']:.4f}s ({pretty_mb_s(z['orig_size'], z['decompress_time'])})")

        print()


if __name__ == '__main__':
    run_all()
