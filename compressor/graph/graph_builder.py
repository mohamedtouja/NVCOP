from __future__ import annotations

from collections import defaultdict
from typing import Dict, Tuple

Graph = Dict[int, Dict[int, int]]


def build_transition_graph(data: bytes) -> Graph:
    """Build a directed graph from byte transitions in the block.

    Each byte value is a node and each immediate successor is an edge.
    """
    graph: Graph = defaultdict(lambda: defaultdict(int))
    for prev, curr in zip(data, data[1:]):
        graph[prev][curr] += 1
    return graph


def extract_edge_frequencies(graph: Graph) -> Dict[Tuple[int, int], int]:
    return {(src, dst): count for src, targets in graph.items() for dst, count in targets.items()}


def node_frequencies(graph: Graph) -> Dict[int, int]:
    return {node: sum(targets.values()) for node, targets in graph.items()}
