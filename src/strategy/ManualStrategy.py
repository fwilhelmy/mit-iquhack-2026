from __future__ import annotations

from typing import List, Optional

from graph_types import Edge
from .BaseStrategy import BaseStrategy


class ManualStrategy(BaseStrategy):
    """Prompt the user to manually choose the next edge to claim."""

    def select_edge(self, edges: List[Edge]) -> Optional[Edge]:
        print("\nSelect the next edge to claim:")
        for index, edge in enumerate(edges, start=1):
            edge_id = edge.get("edge_id", ["?", "?"])
            threshold = edge.get("base_threshold", 0)
            difficulty = edge.get("difficulty_rating", "?")
            print(
                f"  {index}. {tuple(edge_id)} "
                f"(threshold={threshold:.3f}, difficulty={difficulty})"
            )

        selection = input(
            "Enter the edge number or 'node_a node_b' (blank to skip): "
        ).strip()
        if not selection:
            return None

        if selection.isdigit():
            index = int(selection)
            if 1 <= index <= len(edges):
                return edges[index - 1]
            print("Invalid selection number.")
            return None

        parts = selection.split()
        if len(parts) != 2:
            print("Selection must be an index or two node IDs.")
            return None

        normalized = tuple(sorted(parts))
        for edge in edges:
            edge_id = tuple(sorted(edge.get("edge_id", [])))
            if edge_id == normalized:
                return edge

        print("Edge not found in the claimable list.")
        return None

    def choose_num_bell_pairs(
        self,
        edge: Edge,
        min_pairs: int = 1,
        max_pairs: int = 8,
    ) -> int:
        """Prompt the user to choose how many Bell pairs to use."""
        prompt = (
            f"Enter Bell pairs to request ({min_pairs}-{max_pairs}, "
            f"blank for {min_pairs}): "
        )
        selection = input(prompt).strip()
        if not selection:
            return min_pairs
        if selection.isdigit():
            value = int(selection)
            if min_pairs <= value <= max_pairs:
                return value
        print(f"Invalid selection. Using {min_pairs} Bell pairs.")
        return min_pairs
