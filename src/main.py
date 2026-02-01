from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from graphs import Edge
from game import Game
from session import Session
from strategy import (
    BaseStrategy,
    DummyStrategy,
    ManualStrategy,
    AdaptiveStrategy,
    NaiveStrategy,
    BlackListStrategy,
)
from circuits import BaseCircuit, AaronCircuit, ShaneCircuit
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
        choices=("dummy", "manual", "naive", "adaptive"),
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
    circuit_cls: type[BaseCircuit],
    max_attempts: int = 1,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Edge | None]:
    """Attempt to claim a single edge using a strategy."""
    claimable = game.get_claimable_edges()
    target = strategy.choose_edge(claimable)
    if not target:
        return {}, [], None
    circuit = circuit_cls()
    edge_id = tuple(target["edge_id"])
    results = circuit.attempt_claims(
        game=game,
        edge_id=edge_id,
        edge_info=target,
        capture_mode="real",
        max_attempts=max_attempts,
    )
    last_result = results.get("last_result", {})
    # strategy.observe_claim_result(target, last_result)
    attempt_records: List[Dict[str, Any]] = []
    for attempt_index, attempt_result in enumerate(results.get("results", []), start=1):
        record: Dict[str, Any] = {
            "edge_id": f"{edge_id[0]}-{edge_id[1]}",
            "edge_node_a": edge_id[0],
            "edge_node_b": edge_id[1],
            "attempt": attempt_index,
        }
        for key, value in attempt_result.items():
            if isinstance(value, (dict, list)):
                record[key] = json.dumps(value, ensure_ascii=False)
            else:
                record[key] = value
        attempt_records.append(record)
    return last_result, attempt_records, target

def write_attempts_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    if not records:
        return
    base_fields = ["edge_id", "edge_node_a", "edge_node_b", "attempt"]
    extra_fields = sorted({key for record in records for key in record.keys()} - set(base_fields))
    fieldnames = base_fields + extra_fields
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record)

def main() -> None:
    session = Session()
    client = session.client
    game = Game(client)

    ensure_starting_node(client)
    # game.print_status()
    # graph = game.get_graph_raw()
    # status = client.get_status()
    # base_strategy = AdaptiveStrategy(graph, owned_nodes=status.get("owned_nodes", []))
    base_strategy = NaiveStrategy()
    strategy = BlackListStrategy(base_strategy)
    print("Starting auto-claim loop.")
    all_attempts: List[Dict[str, Any]] = []
    try:
        while True:
            strategy.update_owned_nodes(client.get_status().get("owned_nodes", []))
            result, attempts, target_edge = claim_next_edge_with_strategy(
                game,
                strategy=strategy,
                circuit_cls=ShaneCircuit,
                max_attempts=2,
            )
            all_attempts.extend(attempts)
            if target_edge and (not result.get("ok") or not (result.get("data") or {}).get("success")):
                strategy.add_blacklisted_edge(target_edge)
            if result.get("ok"):
                data = result["data"]
                print(f"Success: {data.get('success')}")
                print(data)
                if data.get("success"):
                    player_id = client.player_id or "Unknown"
                    name = client.name or ""
                    score = data.get("score", 0)
                    edge_id = data.get("edge_id")
                    edge_nodes = [str(node) for node in edge_id] if edge_id else []
                    edge_name = " - ".join(edge_nodes) if edge_nodes else "Unknown edge"
                    edge_nodes_display = ", ".join(edge_nodes) if edge_nodes else "Unknown"
                    fidelity = data.get("fidelity", 0)
                    threshold = data.get("threshold", 0)
                    status = client.get_status()
                    budget = status.get("budget", 0)
                    session_id = status.get("session_id", "Unknown")
                    message = (
                        "```\n"
                        "Claim success\n"
                        f"Edge: {edge_name}\n"
                        f"Edge nodes: {edge_nodes_display}\n"
                        f"Player: {player_id}{f' ({name})' if name else ''}\n"
                        f"Session:\n"
                        f"Score: {score}\n"
                        f"Budget: {budget}\n"
                        f"Fidelity: {fidelity:.4f} (threshold: {threshold:.4f})\n"
                        "```"
                    )
                    discord.post_text(message)

            if status.get("budget", 0) <= 1:
                print("Budget exhausted. Stopping auto-claim loop.")
                break
    except KeyboardInterrupt:
        print("Auto-claim loop stopped.")
    finally:
        output_path = REPO_ROOT / "claim_attempts.csv"
        write_attempts_csv(all_attempts, output_path)
        if all_attempts:
            print(f"Wrote {len(all_attempts)} claim attempts to {output_path}")

if __name__ == "__main__":
    main()
