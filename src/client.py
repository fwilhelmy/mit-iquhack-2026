"""
Refactored GameClient - Player interface for the quantum networking game server.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from qiskit import QuantumCircuit, qasm3


GraphFrames = Dict[str, pd.DataFrame]


@dataclass
class ApiError:
    code: str
    message: str


class GameClient:
    """Client for interacting with the game server API."""

    def __init__(
        self,
        base_url: str = "https://demo-entanglement-distillation-qfhvrahfcq-uc.a.run.app",
        api_token: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.player_id: Optional[str] = None
        self.name: Optional[str] = None
        self._cached_graph: Optional[Dict[str, Any]] = None
        self._cached_graph_frames: Optional[GraphFrames] = None

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        require_auth: bool = True,
    ) -> Dict[str, Any]:
        if require_auth and not self.api_token:
            return {
                "ok": False,
                "error": {"code": "NO_TOKEN", "message": "No API token. Register first."},
            }
        url = f"{self.base_url}{path}"
        response = requests.request(
            method,
            url,
            json=payload,
            headers=self._headers(),
            timeout=120 if method.lower() == "get" else 30,
        )
        response.raise_for_status()
        return response.json()

    def _get(self, path: str) -> Dict[str, Any]:
        return self._request("get", path).get("data", {})

    def _post(
        self,
        path: str,
        payload: Dict[str, Any],
        require_auth: bool = True,
    ) -> Dict[str, Any]:
        return self._request("post", path, payload=payload, require_auth=require_auth)

    def _require_player(self) -> Optional[Dict[str, Any]]:
        if not self.player_id:
            return {"ok": False, "error": {"code": "NOT_REGISTERED", "message": "Not registered"}}
        return None

    # ---- Core API Methods ----

    def register(self, player_id: str, name: str, location: str = "remote") -> Dict[str, Any]:
        """Register a new player. Location: "in_person" (Americas) or "remote" (AfroEuroAsia)."""
        resp = self._post(
            "/v1/register",
            {"player_id": player_id, "name": name, "location": location},
            require_auth=False,
        )
        if resp.get("ok"):
            self.player_id = player_id
            self.name = name
            if "data" in resp and "api_token" in resp["data"]:
                self.api_token = resp["data"]["api_token"]
        elif resp.get("error", {}).get("code") == "PLAYER_EXISTS":
            self.player_id = player_id
            self.name = name
        return resp

    def select_starting_node(self, node_id: str) -> Dict[str, Any]:
        """Select a starting node from the candidates provided at registration."""
        guard = self._require_player()
        if guard:
            return guard
        return self._post("/v1/select_starting_node", {"player_id": self.player_id, "node_id": node_id})

    def restart(self) -> Dict[str, Any]:
        """Reset game progress (keeps player, resets starting node)."""
        guard = self._require_player()
        if guard:
            return guard
        return self._post("/v1/restart", {"player_id": self.player_id})

    def get_status(self) -> Dict[str, Any]:
        """Get current player status including score, budget, owned nodes/edges."""
        if not self.player_id:
            return {}
        return self._get(f"/v1/status/{self.player_id}")

    def get_graph_raw(self) -> Dict[str, Any]:
        """Get the quantum network graph structure as raw JSON."""
        return self._get("/v1/graph")

    def get_graph(self) -> GraphFrames:
        """Get the quantum network graph structure as pandas DataFrames."""
        graph = self.get_graph_raw()
        return self._to_graph_frames(graph)

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get the current leaderboard."""
        return self._get("/v1/leaderboard")

    def claim_edge(
        self,
        edge: Tuple[str, str],
        circuit: QuantumCircuit,
        flag_bit: int,
        num_bell_pairs: int,
    ) -> Dict[str, Any]:
        """
        Claim an edge by submitting a distillation circuit.

        Args:
            edge: Tuple of (node_a, node_b)
            circuit: 2N-qubit QuantumCircuit with LOCC operations
            flag_bit: Classical bit index for post-selection (0 = success)
            num_bell_pairs: Number of raw Bell pairs (1-8)

        Returns:
            Response with fidelity, success_probability, threshold, and success status.
        """
        guard = self._require_player()
        if guard:
            return guard

        payload = {
            "player_id": self.player_id,
            "edge": [edge[0], edge[1]],
            "num_bell_pairs": int(num_bell_pairs),
            "circuit_qasm": qasm3.dumps(circuit),
            "flag_bit": int(flag_bit),
        }
        return self._post("/v1/claim_edge", payload)

    # ---- Convenience Methods ----

    def _to_graph_frames(self, graph: Dict[str, Any]) -> GraphFrames:
        nodes = pd.DataFrame(graph.get("nodes", []))
        edges = pd.DataFrame(graph.get("edges", []))
        if not edges.empty and "edge_id" in edges.columns:
            edges = edges.copy()
            edges[["node_a", "node_b"]] = pd.DataFrame(edges["edge_id"].tolist(), index=edges.index)
        return {"nodes": nodes, "edges": edges}

    def get_cached_graph(self, force: bool = False) -> Dict[str, Any]:
        """Get graph with caching (graph doesn't change during game)."""
        if force or self._cached_graph is None:
            self._cached_graph = self.get_graph_raw()
        return self._cached_graph

    def get_cached_graph_frames(self, force: bool = False) -> GraphFrames:
        """Get cached graph as pandas DataFrames."""
        if force or self._cached_graph_frames is None:
            self._cached_graph_frames = self._to_graph_frames(self.get_cached_graph(force=force))
        return self._cached_graph_frames

    def get_claimable_edges(self) -> List[Dict[str, Any]]:
        """Get edges adjacent to owned nodes that can be claimed."""
        status = self.get_status()
        owned = set(status.get("owned_nodes", []))
        if not owned:
            return []

        graph = self.get_cached_graph()
        claimable = []
        for edge in graph.get("edges", []):
            n1, n2 = edge["edge_id"]
            if (n1 in owned) != (n2 in owned):
                claimable.append(edge)
        return claimable

    def get_node_info(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific node."""
        nodes = self.get_cached_graph_frames().get("nodes", pd.DataFrame())
        if nodes.empty or "node_id" not in nodes.columns:
            return None
        match = nodes.loc[nodes["node_id"] == node_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def get_edge_info(self, node_a: str, node_b: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific edge."""
        edges = self.get_cached_graph_frames().get("edges", pd.DataFrame())
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
        status = self.get_status()
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
