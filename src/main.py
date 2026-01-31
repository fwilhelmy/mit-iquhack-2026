from __future__ import annotations

import argparse
import sys
from pathlib import Path

from circuit_runner import load_distillation_circuit
from session import Session

REPO_ROOT = Path(__file__).resolve().parents[1]
CHALLENGE_DIR = REPO_ROOT / "2026-IonQ-challenge"
sys.path.insert(0, str(CHALLENGE_DIR))

from client import GameClient  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the IonQ challenge workflow with a distillation circuit.",
    )
    parser.add_argument("--player-id", help="Player ID used for registration.")
    parser.add_argument("--player-name", help="Player name used for registration.")
    parser.add_argument(
        "--location",
        default="remote",
        choices=["remote", "in_person"],
        help="Competition location (remote or in_person).",
    )
    parser.add_argument(
        "--starting-node",
        help="Node ID to select as a starting node if not already set.",
    )
    parser.add_argument(
        "--circuit",
        type=Path,
        help="Optional path to a QASM3 circuit file.",
    )
    parser.add_argument(
        "--num-bell-pairs",
        type=int,
        default=2,
        help="Number of raw Bell pairs used in the distillation circuit.",
    )
    parser.add_argument(
        "--flag-bit",
        type=int,
        default=0,
        help="Classical bit index for post-selection (flag=0 is success).",
    )
    return parser.parse_args()


def ensure_starting_node(client: GameClient, starting_node: str | None) -> None:
    status = client.get_status()
    if status.get("starting_node"):
        print(f"Starting node: {status['starting_node']}")
        return
    if not starting_node:
        print("Select a starting node from your registration candidates.")
        return
    result = client.select_starting_node(starting_node)
    print(result)


def claim_first_edge(client: GameClient, args: argparse.Namespace) -> None:
    claimable = client.get_claimable_edges()
    if not claimable:
        print("No claimable edges available yet.")
        return

    claimable_sorted = sorted(
        claimable, key=lambda edge: (edge["difficulty_rating"], edge["base_threshold"])
    )
    target = claimable_sorted[0]
    edge_id = tuple(target["edge_id"])

    circuit = load_distillation_circuit(
        args.circuit, num_bell_pairs=args.num_bell_pairs
    )
    print(
        f"Claiming {edge_id} (threshold: {target['base_threshold']:.3f}) "
        f"with {args.num_bell_pairs} Bell pairs..."
    )

    result = client.claim_edge(
        edge_id, circuit, args.flag_bit, num_bell_pairs=args.num_bell_pairs
    )
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
    args = parse_args()
    session = Session(
        player_id=args.player_id,
        player_name=args.player_name,
        location=args.location,
    )
    client = session.client

    ensure_starting_node(client, args.starting_node)
    print(client.get_status())
    claim_first_edge(client, args)


if __name__ == "__main__":
    main()
