from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from graph_types import Edge


class BaseStrategy(ABC):
    """Base class for edge-claiming strategies."""

    def sort_edges(self, edges: List[Edge]) -> List[Edge]:
        """Sort edges by default difficulty and threshold heuristics."""
        return sorted(
            edges,
            key=lambda edge: (
                edge.get("difficulty_rating", 0),
                edge.get("base_threshold", 0),
            ),
        )

    def choose_edge(self, edges: List[Edge]) -> Optional[Edge]:
        """Sort edges and select the next edge to claim."""
        if not edges:
            return None
        sorted_edges = self.sort_edges(edges)
        return self.select_edge(sorted_edges)

    def choose_num_bell_pairs(
        self,
        edge: Edge,
        min_pairs: int = 1,
        max_pairs: int = 8,
    ) -> int:
        """Select how many Bell pairs to use for a specific edge."""
        difficulty = edge.get("difficulty_rating", 0)
        threshold = edge.get("base_threshold", 0)
        recommended = 2
        if difficulty >= 4 or threshold >= 0.8:
            recommended = 6
        elif difficulty >= 3 or threshold >= 0.6:
            recommended = 5
        elif difficulty >= 2 or threshold >= 0.4:
            recommended = 4
        elif difficulty >= 1 or threshold >= 0.2:
            recommended = 3
        return max(min_pairs, min(max_pairs, recommended))

    @abstractmethod
    def select_edge(self, edges: List[Edge]) -> Optional[Edge]:
        """Select an edge from the pre-sorted list."""
        raise NotImplementedError
