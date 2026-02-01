from __future__ import annotations

from typing import List, Sequence, Tuple, TypedDict

EdgeId = Tuple[str, str]


class Node(TypedDict, total=False):
    node_id: str
    utility_qubits: int
    bonus_bell_pairs: int
    capacity: int
    region: str
    latitude: float
    longitude: float


class Edge(TypedDict, total=False):
    edge_id: Sequence[str]
    base_threshold: float
    difficulty_rating: int
    distance: float
    successful_attempts: int


class GraphData(TypedDict, total=False):
    nodes: List[Node]
    edges: List[Edge]
