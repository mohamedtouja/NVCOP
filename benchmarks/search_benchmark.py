"""Benchmark search performance for the rolling hash pattern index vs naive search."""
import sys
import time
from pathlib import Path as _Path

PROJECT_ROOT = str(_Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from compressor.graph.pattern_search import (
    find_repeated_patterns,
    find_repeated_patterns_naive,
)

SAMPLES = {
    "text": b"The quick brown fox jumps over the lazy dog. " * 8192,
    "log": b"2026-07-18 12:00:00 INFO Service started pid=1234\n" * 4096,
    "fractal": b"ABC12345" * 32768,
}


def benchmark():
    print("Search benchmark: rolling hash vs naive")
    for name, data in SAMPLES.items():
        print(f"\nSample: {name} ({len(data)} bytes)")

        t0 = time.perf_counter()
        rolling = list(find_repeated_patterns(data, min_length=4, max_length=32, top_k=5, window_size=8))
        t1 = time.perf_counter()
        naive = list(find_repeated_patterns_naive(data, min_length=4, max_length=32, top_k=5))
        t2 = time.perf_counter()

        print(f" rolling hash: {t1 - t0:.4f}s, candidates={len(rolling)}")
        print(f"     naive: {t2 - t1:.4f}s, candidates={len(naive)}")
        if len(rolling) > 0:
            print(f"   best rolling pattern len={rolling[0].length} freq={rolling[0].frequency}")
        if len(naive) > 0:
            print(f"     best naive pattern len={naive[0].length} freq={naive[0].frequency}")


if __name__ == "__main__":
    benchmark()
