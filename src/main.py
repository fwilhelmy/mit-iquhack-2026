from __future__ import annotations

import sys
from pathlib import Path

from circuit_runner import load_distillation_circuit
from game import Game
from session import Session

REPO_ROOT = Path(__file__).resolve().parents[1]
CHALLENGE_DIR = REPO_ROOT / "2026-IonQ-challenge"
sys.path.insert(0, str(CHALLENGE_DIR))

from client import GameClient  # noqa: E402


DEFAULT_NUM_BELL_PAIRS = 2
DEFAULT_FLAG_BIT = 0


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


def claim_first_edge(
    client: GameClient,
    circuit_path: Path | None = None,
    num_bell_pairs: int = DEFAULT_NUM_BELL_PAIRS,
    flag_bit: int = DEFAULT_FLAG_BIT,
) -> None:
    claimable = client.get_claimable_edges()
    if not claimable:
        print("No claimable edges available yet.")
        return

    claimable_sorted = sorted(
        claimable, key=lambda edge: (edge["difficulty_rating"], edge["base_threshold"])
    )
    target = claimable_sorted[0]
    edge_id = tuple(target["edge_id"])

    circuit = load_distillation_circuit(circuit_path, num_bell_pairs=num_bell_pairs)
    print(
        f"Claiming {edge_id} (threshold: {target['base_threshold']:.3f}) "
        f"with {num_bell_pairs} Bell pairs..."
    )

    result = game.client.claim_edge(
        edge_id, circuit, flag_bit, num_bell_pairs=num_bell_pairs)

    if result.get("ok"):
        data = result["data"]
        print(f"Success: {data.get('success')}")
        print(
            f"Fidelity: {data.get('fidelity', 0):.4f} "
            f"(threshold: {data.get('threshold', 0):.4f})"
        )
        print(f"Success probability: {data.get('success_probability', 0):.4f}")
    else:
        print(f"Error: {result.get('error', {}).get('message')}")


def main() -> None:
    session = Session()
    client = session.client
    game = Game(client)

    ensure_starting_node(client)
    game.print_status()
    claim_first_edge(game)


if __name__ == "__main__":
    main()
