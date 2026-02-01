from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Set, Tuple, Union

from graphs import Edge, EdgeId

from .BaseStrategy import BaseStrategy


NormalizedEdgeId = Tuple[str, str]


class BlackListStrategy(BaseStrategy):
    """Filter edges using a blacklist and difficulty cutoff before delegating selection."""

    def __init__(
        self,
        strategy: BaseStrategy,
        *,
        blacklisted_edges: Sequence[Union[EdgeId, Edge]] | None = None,
        max_difficulty: int = 3,
    ) -> None:
        self.strategy = strategy
        self.max_difficulty = int(max_difficulty)
        self._blacklisted_edges: Set[NormalizedEdgeId] = set()
        self.add_blacklisted_edges(blacklisted_edges or [])

    def add_blacklisted_edge(self, edge: Union[EdgeId, Edge]) -> None:
        edge_id = self._normalize_edge_id(edge)
        if edge_id:
            self._blacklisted_edges.add(edge_id)

    def add_blacklisted_edges(self, edges: Iterable[Union[EdgeId, Edge]]) -> None:
        for edge in edges:
            self.add_blacklisted_edge(edge)

    def update_owned_nodes(self, owned_nodes: Sequence[str]) -> None:
        if hasattr(self.strategy, "update_owned_nodes"):
            self.strategy.update_owned_nodes(owned_nodes)

    def observe_claim_result(self, edge: Edge, result: dict) -> None:
        if hasattr(self.strategy, "observe_claim_result"):
            self.strategy.observe_claim_result(edge, result)

    def sort_edges(self, edges: List[Edge]) -> List[Edge]:
        return self.strategy.sort_edges(edges)

    def select_edge(self, edges: List[Edge]) -> Optional[Edge]:
        return self.strategy.select_edge(edges)

    def choose_edge(self, edges: List[Edge]) -> Optional[Edge]:
        eligible = [
            edge
            for edge in edges
            if self._is_edge_allowed(edge)
        ]
        if not eligible:
            return None
        return self.strategy.choose_edge(eligible)

    def _is_edge_allowed(self, edge: Edge) -> bool:
        difficulty = int(edge.get("difficulty_rating", 0) or 0)
        if difficulty > self.max_difficulty:
            return False
        edge_id = self._normalize_edge_id(edge)
        if edge_id in self._blacklisted_edges:
            return False
        return True

    def _normalize_edge_id(self, edge: Union[EdgeId, Edge]) -> Optional[NormalizedEdgeId]:
        if isinstance(edge, dict):
            raw = edge.get("edge_id")
        else:
            raw = edge
        if not raw or len(raw) != 2:
            return None
        node_a, node_b = raw
        if not node_a or not node_b:
            return None
        return tuple(sorted((str(node_a), str(node_b))))
