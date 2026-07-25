from typing import Optional, Tuple


def detect_fractal(data: bytes, min_len: int = 1, max_len: int = 64, min_repeats: int = 3, similarity_threshold: float = 0.8) -> Optional[Tuple[bytes, int]]:
    """Detect simple fractal/self-similar repetition patterns.

    Returns a tuple (pattern, repeat_count) when a repeating unit is found such that
    (repeat_count * len(pattern)) / len(data) >= similarity_threshold and repeat_count >= min_repeats.

    This is a heuristic, light-weight detector for Phase 3 integration.
    """
    n = len(data)
    if n == 0:
        return None

    max_len = min(max_len, n)
    for L in range(min_len, max_len + 1):
        # try to find a candidate pattern based on the prefix
        pattern = data[0:L]
        # count non-overlapping repeats of the pattern
        count = 0
        i = 0
        while i + L <= n:
            if data[i : i + L] == pattern:
                count += 1
                i += L
            else:
                i += 1
        if count >= min_repeats and (count * L) / n >= similarity_threshold:
            return pattern, count
    return None
