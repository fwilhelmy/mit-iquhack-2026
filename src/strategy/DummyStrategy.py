from __future__ import annotations

from typing import Any, Dict, List

from .BaseStrategy import BaseStrategy

Edge = Dict[str, Any]


class DummyStrategy(BaseStrategy):
    """Naive strategy that always picks the first edge."""

    def select_edge(self, edges: List[Edge]) -> Edge:
        return edges[0]
