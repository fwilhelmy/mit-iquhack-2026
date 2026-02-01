from __future__ import annotations

from typing import List

from graphs import Edge
from .BaseStrategy import BaseStrategy


class GreedyStrategy(BaseStrategy):
    """Greedy strategy prioritizing low difficulty and low threshold edges."""

    def sort_edges(self, edges: List[Edge]) -> List[Edge]:
        return sorted(
            edges,
            key=lambda edge: (
                edge.get("difficulty_rating", 0),
                edge.get("base_threshold", 0),
                edge.get("edge_id", ()),
            ),
        )

    def select_edge(self, edges: List[Edge]) -> Edge:
        return edges[0]
