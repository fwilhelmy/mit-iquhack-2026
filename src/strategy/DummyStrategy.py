from __future__ import annotations

from typing import List

from graph_types import Edge
from .BaseStrategy import BaseStrategy


class DummyStrategy(BaseStrategy):
    """Naive strategy that always picks the first edge."""

    def select_edge(self, edges: List[Edge]) -> Edge:
        return edges[0]
