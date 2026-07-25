from compressor.graph.graph_builder import Graph


def compute_graph_complexity(graph: Graph) -> float:
    """Compute a lightweight score from node and edge statistics."""
    node_count = len(graph)
    edge_count = sum(len(targets) for targets in graph.values())
    if node_count == 0:
        return 0.0
    return edge_count / node_count


def has_repeated_cycle(graph: Graph) -> bool:
    """Detect presence of simple repeated transitions using edge frequency."""
    for targets in graph.values():
        for count in targets.values():
            if count >= 3:
                return True
    return False
