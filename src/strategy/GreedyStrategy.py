from __future__ import annotations

from typing import Any, Dict, List

from .BaseStrategy import BaseStrategy

Edge = Dict[str, Any]


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

    def choose_num_bell_pairs(
        self,
        edge: Edge,
        min_pairs: int = 1,
        max_pairs: int = 8,
    ) -> int:
        """Use the minimum number of Bell pairs for greedy captures."""
        return min_pairs
