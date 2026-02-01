from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from client import GameClient
from circuits import BaseCircuit
from utils import visualization

GraphFrames = Dict[str, pd.DataFrame]


class Game:
    """Game-level helpers for interacting with the quantum network graph."""

    def __init__(self, client: GameClient) -> None:
        self.client = client
        self._cached_graph: Optional[Dict[str, Any]] = None
        self._cached_graph_frames: Optional[GraphFrames] = None

    def _to_graph_frames(self, graph: Dict[str, Any]) -> GraphFrames:
        nodes = pd.DataFrame(graph.get("nodes", []))
        edges = pd.DataFrame(graph.get("edges", []))
        if not edges.empty and "edge_id" in edges.columns:
            edges = edges.copy()
            edges[["node_a", "node_b"]] = pd.DataFrame(edges["edge_id"].tolist(), index=edges.index)
        return {"nodes": nodes, "edges": edges}

    def get_graph_raw(self, force: bool = False) -> Dict[str, Any]:
        """Get the quantum network graph structure (cached)."""
        if force or self._cached_graph is None:
            self._cached_graph = self.client.get_graph_raw()
        return self._cached_graph

    def get_graph_frames(self, force: bool = False) -> GraphFrames:
        """Get the quantum network graph structure as pandas DataFrames (cached)."""
        if force or self._cached_graph_frames is None:
            self._cached_graph_frames = self._to_graph_frames(self.get_graph_raw(force=force))
        return self._cached_graph_frames

    def get_claimable_edges(self) -> List[Dict[str, Any]]:
        """Get edges adjacent to owned nodes that can be claimed."""
        status = self.client.get_status()
        owned = set(status.get("owned_nodes", []))
        if not owned:
            return []

        graph = self.get_graph_raw()
        claimable = []
        for edge in graph.get("edges", []):
            n1, n2 = edge["edge_id"]
            if (n1 in owned) != (n2 in owned):
                claimable.append(edge)
        return claimable

    def claim_edge(
        self,
        edge_id: Tuple[str, str],
        circuit: BaseCircuit,
        num_bell_pairs: int | None = None,
        flag_bit: int | None = None,
        capture_mode: str = "real",
    ) -> Dict[str, Any]:
        """Claim an edge using a circuit instance.

        Args:
            edge_id: Tuple of (node_a, node_b)
            circuit: Circuit instance used for distillation.
            num_bell_pairs: Override for the number of Bell pairs to request.
            flag_bit: Override for the flag bit index used for post-selection.
            capture_mode: "real" to post to the API, "sim" to simulate locally.
        """
        resolved_pairs = num_bell_pairs if num_bell_pairs is not None else circuit.num_bell_pairs
        resolved_flag = flag_bit if flag_bit is not None else circuit.flag_bit
        mode = capture_mode.lower()
        if mode == "sim":
            from utils import simulation

            edge_info = self.get_edge_info(edge_id[0], edge_id[1])
            threshold = edge_info.get("base_threshold") if edge_info else None
            return simulation.simulate_capture(
                edge_id=edge_id,
                circuit=circuit.circuit,
                num_bell_pairs=resolved_pairs,
                flag_bit=resolved_flag,
                threshold=threshold,
            )
        if mode == "real":
            result = self.client.claim_edge(edge_id, circuit.circuit, resolved_flag, resolved_pairs)
            return result
        return {
            "ok": False,
            "error": {
                "code": "INVALID_CAPTURE_MODE",
                "message": f"Unknown capture mode: {capture_mode}",
            },
        }

    def get_graph_tool(self, force: bool = False) -> visualization.GraphTool:
        """Return a GraphTool instance built from the cached graph."""
        return visualization.GraphTool(self.get_graph_raw(force=force))

    def get_neighbors(self, node_id: str, force: bool = False) -> List[str]:
        """Get neighboring nodes for a given node ID."""
        return self.get_graph_tool(force=force).get_neighbors(node_id)

    def get_node_info(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific node."""
        nodes = self.get_graph_frames().get("nodes", pd.DataFrame())
        if nodes.empty or "node_id" not in nodes.columns:
            return None
        match = nodes.loc[nodes["node_id"] == node_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def get_edge_info(self, node_a: str, node_b: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific edge."""
        edges = self.get_graph_frames().get("edges", pd.DataFrame())
        if edges.empty or "edge_id" not in edges.columns:
            return None
        edge_id = tuple(sorted([node_a, node_b]))
        edge_ids = edges["edge_id"].apply(lambda value: tuple(sorted(value)))
        match = edges.loc[edge_ids == edge_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def get_status_summary(self) -> Dict[str, Any]:
        """Return a summarized view of player status."""
        status = self.client.get_status()
        if not status:
            return {"ok": False, "error": {"code": "NO_STATUS", "message": "Not registered or no status available."}}

        owned_nodes = status.get("owned_nodes", [])
        owned_edges = status.get("owned_edges", [])
        claimable = self.get_claimable_edges()

        return {
            "ok": True,
            "player_id": status.get("player_id", "Unknown"),
            "name": status.get("name", ""),
            "score": status.get("score", 0),
            "budget": status.get("budget", 0),
            "is_active": status.get("is_active", False),
            "starting_node": status.get("starting_node", "Not selected"),
            "owned_nodes": owned_nodes,
            "owned_edges": owned_edges,
            "owned_nodes_count": len(owned_nodes),
            "owned_edges_count": len(owned_edges),
            "claimable_edges": claimable,
            "claimable_edges_count": len(claimable),
        }

    def print_status(self) -> None:
        """Print a formatted summary of player status."""
        summary = self.get_status_summary()
        if not summary.get("ok"):
            print(summary.get("error", {}).get("message", "Not registered or no status available."))
            return

        print("=" * 50)
        print(f"Player: {summary.get('player_id', 'Unknown')} ({summary.get('name', '')})")
        print(
            f"Score: {summary.get('score', 0)} | "
            f"Budget: {summary.get('budget', 0)} bell pairs"
        )
        print(f"Active: {'Yes' if summary.get('is_active', False) else 'No'}")
        print(f"Starting node: {summary.get('starting_node', 'Not selected')}")

        owned_nodes = summary.get("owned_nodes", [])
        owned_edges = summary.get("owned_edges", [])
        print(f"Owned: {len(owned_nodes)} nodes, {len(owned_edges)} edges")

        claimable = summary.get("claimable_edges", [])
        print(f"Claimable edges: {len(claimable)}")
        for edge in claimable[:3]:
            print(
                f"  - {edge['edge_id']}: threshold={edge['base_threshold']:.2f}, "
                f"difficulty={edge['difficulty_rating']}"
            )
        if len(claimable) > 3:
            print(f"  ... and {len(claimable) - 3} more")
        print("=" * 50)
