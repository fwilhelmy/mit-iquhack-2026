"""Refactored GameClient - Player interface for the quantum networking game server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
from qiskit import QuantumCircuit, qasm3

from graphs import GraphData


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
            timeout=120 if method.lower() == "get" else 60,
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

    def get_graph_raw(self) -> GraphData:
        """Get the quantum network graph structure as raw JSON."""
        return self._get("/v1/graph")

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
