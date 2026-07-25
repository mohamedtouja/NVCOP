def gravity_score(frequency: int, pattern_length: int, storage_cost: float) -> float:
    if storage_cost <= 0:
        return 0.0
    return (frequency * (pattern_length ** 2)) / storage_cost
