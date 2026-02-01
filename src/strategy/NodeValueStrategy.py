from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List, Sequence, Set

from graphs import Edge, GraphData, Node
from .BaseStrategy import BaseStrategy


class NodeValueStrategy(BaseStrategy):
    """Select edges connected to the highest value node in the graph."""

    def __init__(
        self,
        graph: GraphData,
        *,
        utility_weight: float = 1.0,
        bell_pair_weight: float = 1.0,
        capacity_weight: float = 1.0,
        degree_weight: float = 1.0,
        owned_nodes: Sequence[str] | None = None,
        distance_dampening: float = 1.0,
    ) -> None:
        self.graph = graph
        self.utility_weight = utility_weight
        self.bell_pair_weight = bell_pair_weight
        self.capacity_weight = capacity_weight
        self.degree_weight = degree_weight
        self.distance_dampening = distance_dampening
        self.owned_nodes: Set[str] = set(owned_nodes or [])
        self._distance_from_owned = self._compute_distances_from_owned(self.owned_nodes)
        self.node_scores = self._compute_node_scores()

    def update_owned_nodes(self, owned_nodes: Sequence[str]) -> None:
        """Update ownership context and recompute node scores."""
        self.owned_nodes = set(owned_nodes)
        self._distance_from_owned = self._compute_distances_from_owned(self.owned_nodes)
        self.node_scores = self._compute_node_scores()

    def _compute_degrees(self, edges: Sequence[Edge]) -> Dict[str, int]:
        degrees: Dict[str, int] = {}
        for edge in edges:
            node_a, node_b = edge.get("edge_id", ("", ""))
            for node_id in (node_a, node_b):
                if not node_id:
                    continue
                degrees[node_id] = degrees.get(node_id, 0) + 1
        return degrees

    def _compute_distances_from_owned(self, owned_nodes: Iterable[str]) -> Dict[str, int]:
        nodes = self.graph.get("nodes", [])
        edges = self.graph.get("edges", [])
        adjacency: Dict[str, List[str]] = {}
        for edge in edges:
            node_a, node_b = edge.get("edge_id", ("", ""))
            if not node_a or not node_b:
                continue
            adjacency.setdefault(node_a, []).append(node_b)
            adjacency.setdefault(node_b, []).append(node_a)

        distances: Dict[str, int] = {}
        queue: deque[str] = deque()
        for node_id in owned_nodes:
            if node_id:
                distances[node_id] = 0
                queue.append(node_id)

        while queue:
            current = queue.popleft()
            current_distance = distances[current]
            for neighbor in adjacency.get(current, []):
                if neighbor not in distances:
                    distances[neighbor] = current_distance + 1
                    queue.append(neighbor)

        for node in nodes:
            node_id = node.get("node_id")
            if node_id and node_id not in distances:
                distances[node_id] = -1
        return distances

    def _distance_factor(self, node_id: str) -> float:
        if not self.owned_nodes:
            return 1.0
        distance = self._distance_from_owned.get(node_id, -1)
        if distance < 0:
            return 0.0
        return 1.0 / (1.0 + self.distance_dampening * distance)

    def _compute_node_scores(self) -> Dict[str, float]:
        nodes = self.graph.get("nodes", [])
        edges = self.graph.get("edges", [])
        degrees = self._compute_degrees(edges)

        scores: Dict[str, float] = {}
        for node in nodes:
            node_id = node.get("node_id")
            if not node_id:
                continue
            scores[node_id] = self._score_node(node, degrees.get(node_id, 0))
        return scores

    def _score_node(self, node: Node, degree: int) -> float:
        utility = node.get("utility_qubits", 0)
        bell_pairs = node.get("bonus_bell_pairs", 0)
        capacity = node.get("capacity", 0)
        base_score = (
            self.utility_weight * utility
            + self.bell_pair_weight * bell_pairs
            + self.capacity_weight * capacity
            + self.degree_weight * degree
        )
        node_id = node.get("node_id", "")
        return base_score * self._distance_factor(node_id)

    def _edge_value(self, edge: Edge) -> tuple[float, tuple[str, str]]:
        node_a, node_b = edge.get("edge_id", ("", ""))
        target_score = self.node_scores.get(node_a, 0.0)
        origin_score = self.node_scores.get(node_b, 0.0)

        difficulty = edge.get("difficulty_rating", 0)
        threshold = edge.get("base_threshold", 0)
        edge_score = 1.0 / (1.0 + difficulty + threshold)

        total_score = target_score + 0.1 * edge_score + 0.01 * origin_score
        edge_id = tuple(sorted((node_a, node_b)))
        return (-total_score, edge_id)

    def sort_edges(self, edges: List[Edge]) -> List[Edge]:
        return sorted(edges, key=self._edge_value)

    def select_edge(self, edges: List[Edge]) -> Edge:
        return edges[0]
