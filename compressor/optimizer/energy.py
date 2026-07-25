def energy_score(bits_saved: float, cpu_cost: float, memory_cost: float) -> float:
    denominator = cpu_cost + memory_cost
    if denominator <= 0:
        return 0.0
    return bits_saved / denominator
