from __future__ import annotations

from typing import Dict, List, Sequence

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
    ) -> None:
        self.graph = graph
        self.utility_weight = utility_weight
        self.bell_pair_weight = bell_pair_weight
        self.capacity_weight = capacity_weight
        self.degree_weight = degree_weight
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
        return (
            self.utility_weight * utility
            + self.bell_pair_weight * bell_pairs
            + self.capacity_weight * capacity
            + self.degree_weight * degree
        )

    def _edge_value(self, edge: Edge) -> tuple[float, float, tuple[str, str]]:
        node_a, node_b = edge.get("edge_id", ("", ""))
        score_a = self.node_scores.get(node_a, 0.0)
        score_b = self.node_scores.get(node_b, 0.0)
        best = max(score_a, score_b)
        combined = score_a + score_b
        edge_id = tuple(sorted((node_a, node_b)))
        return (-best, -combined, edge_id)

    def sort_edges(self, edges: List[Edge]) -> List[Edge]:
        return sorted(edges, key=self._edge_value)

    def select_edge(self, edges: List[Edge]) -> Edge:
        return edges[0]
