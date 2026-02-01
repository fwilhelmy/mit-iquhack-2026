from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from graphs import Edge


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

    @abstractmethod
    def select_edge(self, edges: List[Edge]) -> Optional[Edge]:
        """Select an edge from the pre-sorted list."""
        raise NotImplementedError
