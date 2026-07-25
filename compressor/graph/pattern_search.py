from __future__ import annotations

import struct
from collections import defaultdict
from typing import DefaultDict, Dict, Iterable

from compressor.optimizer.energy import energy_score
from compressor.optimizer.gravity import gravity_score


class PatternCandidate:
    def __init__(self, pattern: bytes, offsets: list[int]) -> None:
        self.pattern = pattern
        self.offsets = sorted(offsets)

    @property
    def frequency(self) -> int:
        return len(self.non_overlapping_offsets)

    @property
    def length(self) -> int:
        return len(self.pattern)

    @property
    def non_overlapping_offsets(self) -> list[int]:
        selected: list[int] = []
        end_index = -1
        for offset in self.offsets:
            if offset >= end_index:
                selected.append(offset)
                end_index = offset + self.length
        return selected

    def estimate_storage(self) -> int:
        return self.length + 8 + self.frequency * 2

    def gravity(self) -> float:
        return gravity_score(self.frequency, self.length, self.estimate_storage())

    def energy(self) -> float:
        bits_saved = self.length * self.frequency
        cpu_cost = self.length * 0.5
        memory_cost = self.frequency * 0.2
        return energy_score(bits_saved, cpu_cost, memory_cost)


def _find_repeated_patterns_naive(data: bytes, min_length: int = 4, max_length: int = 32, top_k: int = 5) -> Iterable[PatternCandidate]:
    data_len = len(data)
    lengths = [4, 5, 6, 8, 12, 16, 24, 32]
    candidates: dict[bytes, list[int]] = {}

    for length in lengths:
        if length > max_length or length > data_len:
            continue
        seen: dict[bytes, list[int]] = defaultdict(list)
        for offset in range(0, data_len - length + 1):
            fragment = data[offset : offset + length]
            seen[fragment].append(offset)
        for fragment, offsets in seen.items():
            if len(offsets) >= 2:
                candidates.setdefault(fragment, []).extend(offsets)

    patterns = [PatternCandidate(pattern, offsets) for pattern, offsets in candidates.items()]
    patterns.sort(key=lambda candidate: (candidate.gravity(), candidate.energy()), reverse=True)
    return patterns[:top_k]


def _rolling_hash_positions(data: bytes, length: int, base: int = 257) -> dict[int, list[int]]:
    mask = (1 << 64) - 1
    n = len(data)
    if length > n:
        return {}
    hashes: DefaultDict[int, list[int]] = defaultdict(list)
    h = 0
    for i in range(length):
        h = ((h * base) + data[i]) & mask
    hashes[h].append(0)
    power = pow(base, length - 1, 1 << 64)
    for i in range(length, n):
        h = ((h - (data[i - length] * power) & mask) * base + data[i]) & mask
        hashes[h].append(i - length + 1)
    return hashes


def _extend_pattern(data: bytes, positions: list[int], min_length: int, max_length: int) -> dict[bytes, list[int]]:
    patterns: dict[bytes, list[int]] = {}
    if len(positions) < 2:
        return patterns
    reference = positions[0]
    for pos in positions[1:]:
        extension = min(max_length, len(data) - max(reference, pos))
        match_len = 0
        while match_len < extension and data[reference + match_len] == data[pos + match_len]:
            match_len += 1
        if match_len >= min_length:
            pattern = data[reference : reference + match_len]
            patterns.setdefault(pattern, []).extend([reference, pos])
    return patterns


def estimate_pattern_density(data: bytes, seed_length: int = 4, sample_fraction: float = 0.1) -> float:
    n = len(data)
    if n < seed_length * 2:
        return 0.0
    sample_size = min(n, max(seed_length * 16, int(n * sample_fraction)))
    counts: dict[bytes, int] = {}
    for i in range(0, sample_size - seed_length + 1):
        fragment = data[i : i + seed_length]
        counts[fragment] = counts.get(fragment, 0) + 1
    repeated_bytes = sum((count - 1) * seed_length for count in counts.values() if count > 1)
    return min(repeated_bytes / n, 1.0)


def find_repeated_patterns(
    data: bytes,
    min_length: int = 4,
    max_length: int = 64 * 1024,
    top_k: int = 5,
    window_size: int = 8,
) -> Iterable[PatternCandidate]:
    """Find repeated byte patterns using a rolling hash index.

    This is significantly faster than the naive O(n^2) substring search
    used previously. The search is controlled by a minimum pattern length,
    maximum pattern length, and an initial rolling hash window size.
    """
    n = len(data)
    if n < min_length:
        return []

    sample_density = estimate_pattern_density(data, seed_length=min_length, sample_fraction=0.1)
    if sample_density < 0.01 and n > 4096:
        return []

    seed_length = max(min_length, min(window_size, max_length))
    hash_index = _rolling_hash_positions(data, seed_length)
    candidates: Dict[bytes, list[int]] = {}

    for positions in hash_index.values():
        if len(positions) < 2:
            continue
        groups: dict[bytes, list[int]] = defaultdict(list)
        for pos in positions:
            seed = data[pos : pos + seed_length]
            groups[seed].append(pos)
        for seed_positions in groups.values():
            if len(seed_positions) < 2:
                continue
            extended = _extend_pattern(data, seed_positions, min_length, max_length)
            for pattern, offsets in extended.items():
                if len(offsets) < 2:
                    continue
                unique_offsets = sorted(set(offsets))
                candidates.setdefault(pattern, []).extend(unique_offsets)

    patterns = [PatternCandidate(pattern, offsets) for pattern, offsets in candidates.items()]
    patterns.sort(key=lambda candidate: (candidate.gravity(), candidate.energy()), reverse=True)
    return patterns[:top_k]


find_repeated_patterns_naive = _find_repeated_patterns_naive


def build_pattern_encoded_block(data: bytes, pattern: bytes, offsets: list[int]) -> bytes:
    marker = b"PG"
    pattern_length = len(pattern)
    position_set = set(offsets)
    chunks: list[bytes] = []
    index = 0
    while index < len(data):
        if index in position_set and data[index : index + pattern_length] == pattern:
            chunks.append(b"\x01")
            index += pattern_length
            continue
        start = index
        while index < len(data) and (index not in position_set or data[index : index + pattern_length] != pattern):
            index += 1
        literal = data[start:index]
        chunks.append(b"\x00" + struct.pack("<I", len(literal)) + literal)
    body = b"".join(chunks)
    header = (
        marker
        + struct.pack("<I", len(data))
        + struct.pack("<H", pattern_length)
        + pattern
        + struct.pack("<I", len(chunks))
    )
    return header + body


def decode_pattern_encoded_block(encoded: bytes) -> bytes:
    marker = encoded[:2]
    if marker != b"PG":
        raise ValueError("Invalid pattern encoded block")
    pos = 2
    uncompressed_len = struct.unpack_from("<I", encoded, pos)[0]
    pos += 4
    pattern_length = struct.unpack_from("<H", encoded, pos)[0]
    pos += 2
    pattern = encoded[pos : pos + pattern_length]
    pos += pattern_length
    chunk_count = struct.unpack_from("<I", encoded, pos)[0]
    pos += 4
    result = bytearray()
    for _ in range(chunk_count):
        tag = encoded[pos]
        pos += 1
        if tag == 0:
            literal_len = struct.unpack_from("<I", encoded, pos)[0]
            pos += 4
            result.extend(encoded[pos : pos + literal_len])
            pos += literal_len
        elif tag == 1:
            result.extend(pattern)
        else:
            raise ValueError("Unknown chunk tag in pattern encoded block")
    if len(result) != uncompressed_len:
        raise ValueError("Decoded length does not match expected size")
    return bytes(result)
