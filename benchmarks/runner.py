"""Simple benchmark runner comparing NovaGraph Compressor (phase 2) against zlib and gzip.

Generates a set of sample files, compresses/decompresses with Nova, and compares sizes and timings.
"""
import time
import tempfile
import os
from pathlib import Path
import zlib
import gzip
import hashlib
import sys
from pathlib import Path as _Path

# Ensure project root is on sys.path when executed as a script
PROJECT_ROOT = str(_Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from compressor.engine import NovaCompressor
from decompressor.engine import NovaDecompressor

SAMPLES = [
    ("text", 256 * 1024),
    ("json", 256 * 1024),
    ("code", 128 * 1024),
    ("log", 256 * 1024),
    ("random", 256 * 1024),
    ("fractal", 256 * 1024),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_sample(kind: str, size: int) -> bytes:
    if kind == "text":
        unit = b"The quick brown fox jumps over the lazy dog. "
        return (unit * ((size // len(unit)) + 1))[:size]
    if kind == "json":
        entry = b'{"user":"alice","action":"update","value":"' + (b"x" * 50) + b'"},'
        body = b"[" + (entry * (size // len(entry) + 1))[:size - 2] + b"]"
        return body
    if kind == "code":
        snippet = b"def f(x):\n    return x * 2\n\n" * 100
        return (snippet * ((size // len(snippet)) + 1))[:size]
    if kind == "log":
        line = b"2026-07-18 12:00:00 INFO Service started pid=1234\n"
        return (line * ((size // len(line)) + 1))[:size]
    if kind == "random":
        return os.urandom(size)
    if kind == "fractal":
        pattern = b"ABC12345"
        return (pattern * ((size // len(pattern)) + 1))[:size]
    raise ValueError("unknown sample kind")


def run_benchmark():
    compressor = NovaCompressor()
    decompressor = NovaDecompressor()

    results = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for kind, size in SAMPLES:
            print(f"\n-- Sample: {kind} ({size} bytes)")
            data = make_sample(kind, size)
            orig_file = tmp_path / f"sample_{kind}.bin"
            orig_file.write_bytes(data)

            # Nova compression
            nova_file = tmp_path / f"sample_{kind}.nova"
            t0 = time.perf_counter()
            compressor.compress_file(orig_file, nova_file)
            t1 = time.perf_counter()
            nova_comp_time = t1 - t0
            nova_size = nova_file.stat().st_size

            # Nova decompression
            restored = tmp_path / f"sample_{kind}_restored.bin"
            t0 = time.perf_counter()
            decompressor.decompress_file(nova_file, restored)
            t1 = time.perf_counter()
            nova_decomp_time = t1 - t0

            # verify
            assert sha256_bytes(data) == sha256_bytes(restored.read_bytes())

            # zlib
            t0 = time.perf_counter()
            z = zlib.compress(data)
            t1 = time.perf_counter()
            zlib_time = t1 - t0
            zlib_size = len(z)

            # gzip
            t0 = time.perf_counter()
            g = gzip.compress(data)
            t1 = time.perf_counter()
            gzip_time = t1 - t0
            gzip_size = len(g)

            res = {
                "kind": kind,
                "orig": len(data),
                "nova_size": nova_size,
                "nova_comp_time": nova_comp_time,
                "nova_decomp_time": nova_decomp_time,
                "zlib_size": zlib_size,
                "zlib_time": zlib_time,
                "gzip_size": gzip_size,
                "gzip_time": gzip_time,
            }
            results.append(res)
            print(f"orig: {res['orig']} | nova: {res['nova_size']} ({res['nova_comp_time']:.4f}s compress, {res['nova_decomp_time']:.4f}s decompress)")
            print(f"zlib: {res['zlib_size']} ({res['zlib_time']:.4f}s) | gzip: {res['gzip_size']} ({res['gzip_time']:.4f}s)")

    print("\nSummary:")
    for r in results:
        print(f"{r['kind']}: nova_ratio={r['nova_size']/r['orig']:.3f}, zlib_ratio={r['zlib_size']/r['orig']:.3f}, gzip_ratio={r['gzip_size']/r['orig']:.3f}")
    # Persist results for external consumption
    try:
        import json

        out_path = Path(__file__).resolve().parents[0] / "last_results.json"
        out_path.write_text(json.dumps(results, indent=2))
        print(f"\nWrote results to {out_path}")
    except Exception:
        pass


if __name__ == '__main__':
    run_benchmark()
