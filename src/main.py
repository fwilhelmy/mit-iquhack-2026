from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from game import Game
from session import Session
from strategy import BaseStrategy, DummyStrategy, ManualStrategy, GreedyStrategy
from circuits import BaseCircuit, BBPSSW, AaronCircuit, FirstCircuit
from utils import discord

REPO_ROOT = Path(__file__).resolve().parents[1]
CHALLENGE_DIR = REPO_ROOT / "2026-IonQ-challenge"
sys.path.insert(0, str(CHALLENGE_DIR))

from client import GameClient  # noqa: E402

DEFAULT_LOOP_DELAY_SECONDS = 3.0

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the IonQ challenge client.")
    parser.add_argument(
        "--strategy",
        choices=("dummy", "manual"),
        default="dummy",
        help="Strategy to use when selecting the next edge.",
    )
    return parser.parse_args()

def ensure_starting_node(client: GameClient) -> None:
    status = client.get_status()
    if status.get("starting_node"):
        print(f"Starting node: {status['starting_node']}")
        return

    candidates = status.get("starting_candidates") or []
    if not candidates:
        print("Select a starting node from your registration candidates.")
        return

    print("Select a starting node from your registration candidates:")
    candidate_ids = []
    for index, candidate in enumerate(candidates, start=1):
        node_id = candidate.get("node_id", "unknown")
        candidate_ids.append(node_id)
        print(
            f"  {index}. {node_id}: {candidate.get('utility_qubits', 0)} qubits, "
            f"+{candidate.get('bonus_bell_pairs', 0)} bonus"
        )

    selection = input("Enter a node ID or the number from the list: ").strip()
    if not selection:
        print("No selection made. Skipping starting node selection.")
        return

    starting_node = selection
    if selection.isdigit():
        index = int(selection)
        if 1 <= index <= len(candidate_ids):
            starting_node = candidate_ids[index - 1]
        else:
            print("Invalid selection. Skipping starting node selection.")
            return

    result = client.select_starting_node(starting_node)
    print(result)


def claim_next_edge_with_strategy(
    game: Game,
    strategy: BaseStrategy,
    circuit_cls: type[BaseCircuit]
) -> Dict[str, Any]:
    """Attempt to claim a single edge using a strategy."""
    claimable = game.get_claimable_edges()
    target = strategy.choose_edge(claimable)
    circuit = circuit_cls()
    edge_id = tuple(target["edge_id"])
    return game.claim_edge(edge_id, circuit, target, capture_mode="real")

def main() -> None:
    session = Session()
    client = session.client
    game = Game(client)

    ensure_starting_node(client)
    game.print_status()
    strategy = ManualStrategy()
    print(
        "Starting auto-claim loop. "
        f"Waiting {DEFAULT_LOOP_DELAY_SECONDS:.1f}s between attempts."
    )
    try:
        while True:
            result = claim_next_edge_with_strategy(game, strategy=strategy, circuit_cls=AaronCircuit)
            if result.get("ok"):
                data = result["data"]
                print(f"Success: {data.get('success')}")
                print(
                    f"Fidelity: {data.get('fidelity', 0):.4f} "
                    f"(threshold: {data.get('threshold', 0):.4f})"
                )
                print(f"Success probability: {data.get('success_probability', 0):.4f}")
                if data.get("success"):
                    player_id = client.player_id or "Unknown"
                    name = client.name or ""
                    score = data.get("score", 0)
                    edge_id = data.get("edge_id")
                    edge_desc = f" on {tuple(edge_id)}" if edge_id else ""
                    fidelity = data.get("fidelity", 0)
                    threshold = data.get("threshold", 0)
                    message = (
                        f"Claim success{edge_desc} by {player_id}"
                        f"{f' ({name})' if name else ''}. "
                        f"Score: {score}. Fidelity: {fidelity:.4f} "
                        f"(threshold: {threshold:.4f})."
                    )
                    discord.post_text(message)
    except KeyboardInterrupt:
        print("Auto-claim loop stopped.")

if __name__ == "__main__":
    main()
