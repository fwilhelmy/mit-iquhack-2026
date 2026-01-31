from __future__ import annotations

import json
from pathlib import Path

from client import GameClient


class Session:
    """Manage session persistence and registration for the game client."""

    def __init__(
        self,
        session_path: Path | None = None,
        player_id: str | None = None,
        player_name: str | None = None,
        location: str = "remote",
    ) -> None:
        self.session_path = session_path or Path("session.json")
        self._data: dict[str, str] = {}
        self.client = self._bootstrap(player_id, player_name, location)

    def _default_base_url(self) -> str:
        return GameClient().base_url

    def _bootstrap(
        self,
        player_id: str | None,
        player_name: str | None,
        location: str,
    ) -> GameClient:
        client = self._load_client()
        if client:
            return client

        if not player_id:
            player_id = input("Enter your player ID: ").strip()
        if not player_name:
            player_name = input("Enter your player name: ").strip()
        return self._register(player_id, player_name, location)

    def _load_client(self) -> GameClient | None:
        if not self.session_path.exists():
            return None

        self._data = json.loads(self.session_path.read_text())
        base_url = self._data.get("base_url", self._default_base_url())
        client = GameClient(base_url=base_url, api_token=self._data.get("api_token"))
        client.player_id = self._data.get("player_id")
        client.name = self._data.get("name")

        status = client.get_status()
        if status:
            print(
                "Resumed: "
                f"{client.player_id} | Score: {status.get('score', 0)} | "
                f"Budget: {status.get('budget', 0)}"
            )
            return client

        print("Saved session could not be resumed. Registering again.")
        return None

    def _save(self, client: GameClient) -> None:
        if client.api_token:
            self.session_path.write_text(
                json.dumps(
                    {
                        "api_token": client.api_token,
                        "player_id": client.player_id,
                        "name": client.name,
                        "base_url": client.base_url,
                    }
                )
            )
            print("Session saved.")

    def _register(self, player_id: str, player_name: str, location: str) -> GameClient:
        base_url = self._data.get("base_url", self._default_base_url())
        client = GameClient(base_url=base_url)
        result = client.register(player_id, player_name, location=location)
        if result.get("ok"):
            print(f"Registered! Token: {client.api_token[:20]}...")
            candidates = result["data"].get("starting_candidates", [])
            print(f"Starting candidates ({len(candidates)}):")
            for candidate in candidates:
                print(
                    f"  - {candidate['node_id']}: {candidate['utility_qubits']} qubits, "
                    f"+{candidate['bonus_bell_pairs']} bonus"
                )
            self._save(client)
            return client
        raise SystemExit(f"Registration failed: {result.get('error', {}).get('message')}")
