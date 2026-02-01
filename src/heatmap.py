from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Set

import matplotlib.pyplot as plt
import networkx as nx

from graphs import GraphData
from strategy.NodeValueStrategy import NodeValueStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a node score heatmap with owned nodes highlighted."
    )
    parser.add_argument(
        "--graph",
        type=Path,
        required=True,
        help="Path to the graph JSON file (GraphData format).",
    )
    parser.add_argument(
        "--owned",
        default="",
        help="Comma-separated list of owned node IDs to highlight in red.",
    )
    parser.add_argument(
        "--owned-file",
        type=Path,
        help="Optional file containing owned node IDs (JSON list or newline-delimited).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="If provided, save the heatmap to this path instead of showing it.",
    )
    parser.add_argument(
        "--figsize",
        default="10,6",
        help="Figure size as 'width,height' (default: 10,6).",
    )
    parser.add_argument(
        "--cmap",
        default="viridis",
        help="Matplotlib colormap to use for unowned nodes.",
    )
    return parser.parse_args()


def load_graph_data(path: Path) -> GraphData:
    return json.loads(path.read_text())


def normalize_owned_nodes(items: Iterable[str]) -> Set[str]:
    return {item.strip() for item in items if item.strip()}


def load_owned_nodes(arg_value: str, owned_file: Path | None) -> Set[str]:
    owned_nodes = normalize_owned_nodes(arg_value.split(",")) if arg_value else set()
    if not owned_file:
        return owned_nodes

    raw_text = owned_file.read_text().strip()
    if not raw_text:
        return owned_nodes

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        data = raw_text.splitlines()

    if isinstance(data, dict):
        candidates = data.get("owned_nodes", [])
    else:
        candidates = data

    return owned_nodes | normalize_owned_nodes(map(str, candidates))


def build_graph(graph_data: GraphData) -> nx.Graph:
    graph = nx.Graph()
    for node in graph_data.get("nodes", []):
        graph.add_node(node["node_id"], **node)
    for edge in graph_data.get("edges", []):
        edge_id = edge["edge_id"]
        graph.add_edge(edge_id[0], edge_id[1], **edge)
    return graph


def parse_figsize(raw_value: str) -> tuple[float, float]:
    parts = [part.strip() for part in raw_value.split(",")]
    if len(parts) != 2:
        raise ValueError("figsize must be formatted as width,height")
    return float(parts[0]), float(parts[1])


def render_heatmap(
    graph_data: GraphData,
    owned_nodes: Set[str],
    output: Path | None,
    figsize: tuple[float, float],
    cmap: str,
) -> None:
    graph = build_graph(graph_data)
    if graph.number_of_nodes() == 0:
        raise SystemExit("No nodes available to render heatmap.")

    scores = NodeValueStrategy(graph_data).node_scores
    pos = nx.spring_layout(graph, seed=42)

    nodes = list(graph.nodes())
    owned_nodes = {node for node in owned_nodes if node in graph}
    unowned_nodes = [node for node in nodes if node not in owned_nodes]

    node_sizes = {
        node: 300 + graph.nodes[node].get("utility_qubits", 1) * 100 for node in nodes
    }

    fig, ax = plt.subplots(figsize=figsize)

    if unowned_nodes:
        unowned_scores = [scores.get(node, 0.0) for node in unowned_nodes]
        unowned_sizes = [node_sizes[node] for node in unowned_nodes]
        scatter = nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=unowned_nodes,
            node_color=unowned_scores,
            cmap=cmap,
            node_size=unowned_sizes,
            edgecolors="black",
            ax=ax,
        )
        fig.colorbar(scatter, ax=ax, label="Score")

    if owned_nodes:
        owned_sizes = [node_sizes[node] for node in owned_nodes]
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=list(owned_nodes),
            node_color="#E53935",
            node_size=owned_sizes,
            edgecolors="black",
            ax=ax,
        )

    nx.draw_networkx_edges(graph, pos, edge_color="#9E9E9E", width=1, ax=ax)
    ax.set_title("Node Score Heatmap (Owned Nodes in Red)")
    ax.axis("off")

    if owned_nodes:
        legend = [
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor="#E53935",
                markeredgecolor="black",
                markersize=10,
                label="Owned",
            )
        ]
        ax.legend(handles=legend, loc="upper left")

    plt.tight_layout()
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output, dpi=150, bbox_inches="tight")
        print(f"Saved to {output}")
    else:
        plt.show()


def main() -> None:
    args = parse_args()
    graph_data = load_graph_data(args.graph)
    owned_nodes = load_owned_nodes(args.owned, args.owned_file)
    figsize = parse_figsize(args.figsize)
    render_heatmap(
        graph_data,
        owned_nodes,
        output=args.output,
        figsize=figsize,
        cmap=args.cmap,
    )


if __name__ == "__main__":
    main()
