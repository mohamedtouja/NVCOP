import math
from collections import Counter

from compressor.graph.graph_builder import build_transition_graph
from compressor.graph.graph_score import compute_graph_complexity, has_repeated_cycle
from compressor.graph.pattern_search import (
    PatternCandidate,
    build_pattern_encoded_block,
    estimate_pattern_density,
    find_repeated_patterns,
)
from compressor.fractal.detector import detect_fractal
from compressor.tokenizer import tokenize_data

COMPRESSION_METHOD_RAW = 0
COMPRESSION_METHOD_PATTERN = 1
COMPRESSION_METHOD_HUFFMAN = 2
PATTERN_MODEL_NONE = 0
PATTERN_MODEL_GRAPH = 1
PATTERN_MODEL_FRACTAL = 2
PATTERN_MODEL_TOKEN = 3

skipped_search_blocks = 0


def reset_stats() -> None:
    global skipped_search_blocks
    skipped_search_blocks = 0


def compute_shannon_entropy(block_bytes: bytes) -> float:
    if not block_bytes:
        return 0.0
    frequencies = Counter(block_bytes)
    length = len(block_bytes)
    entropy = 0.0
    for frequency in frequencies.values():
        probability = frequency / length
        entropy -= probability * math.log2(probability)
    return entropy


def analyze_block(block_bytes: bytes) -> tuple[int, int, object | None]:
    global skipped_search_blocks

    entropy = compute_shannon_entropy(block_bytes)
    density = estimate_pattern_density(block_bytes)
    tokenized = tokenize_data(block_bytes)
    if tokenized is not None:
        return COMPRESSION_METHOD_HUFFMAN, PATTERN_MODEL_TOKEN, tokenized

    if entropy >= 7.5 or (entropy >= 7.0 and density < 0.02):
        skipped_search_blocks += 1
        return COMPRESSION_METHOD_RAW, PATTERN_MODEL_NONE, None

    fractal = detect_fractal(block_bytes, min_len=1, max_len=64, min_repeats=3, similarity_threshold=0.75)
    if fractal is not None:
        pattern, count = fractal
        offsets = []
        i = 0
        L = len(pattern)
        n = len(block_bytes)
        while i + L <= n:
            if block_bytes[i : i + L] == pattern:
                offsets.append(i)
                i += L
            else:
                i += 1
        candidate = PatternCandidate(pattern, offsets)
        encoded = build_pattern_encoded_block(block_bytes, candidate.pattern, candidate.non_overlapping_offsets)
        if len(encoded) < len(block_bytes):
            return COMPRESSION_METHOD_PATTERN, PATTERN_MODEL_FRACTAL, candidate

    if density < 0.02 and entropy >= 6.8:
        skipped_search_blocks += 1
        return COMPRESSION_METHOD_RAW, PATTERN_MODEL_NONE, None

    graph = build_transition_graph(block_bytes)
    complexity = compute_graph_complexity(graph)
    repeated_cycle = has_repeated_cycle(graph)

    candidates = list(find_repeated_patterns(block_bytes))
    if candidates:
        best_pattern = candidates[0]
        encoded = build_pattern_encoded_block(block_bytes, best_pattern.pattern, best_pattern.non_overlapping_offsets)
        if len(encoded) < len(block_bytes):
            return COMPRESSION_METHOD_PATTERN, PATTERN_MODEL_GRAPH, best_pattern

    if repeated_cycle or complexity > 1.0:
        return COMPRESSION_METHOD_RAW, PATTERN_MODEL_GRAPH, None

    return COMPRESSION_METHOD_RAW, PATTERN_MODEL_NONE, None


def select_compression_method(block_bytes: bytes) -> int:
    method, _, _ = analyze_block(block_bytes)
    return method


def select_pattern_model(block_bytes: bytes) -> int:
    _, pattern_model, _ = analyze_block(block_bytes)
    return pattern_model
