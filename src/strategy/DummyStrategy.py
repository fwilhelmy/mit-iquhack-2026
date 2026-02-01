from __future__ import annotations

from typing import List

from graphs import Edge
from .BaseStrategy import BaseStrategy


class DummyStrategy(BaseStrategy):
    """Select the first available edge after default sorting."""

    def select_edge(self, edges: List[Edge]) -> Edge:
        return edges[0]
