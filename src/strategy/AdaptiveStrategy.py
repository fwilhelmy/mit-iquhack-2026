from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

from graphs import Edge, GraphData, Node
from .BaseStrategy import BaseStrategy


@dataclass
class _BanditBucket:
    """
    Online stats bucket for a (difficulty, threshold_bin).
    We learn P(claim_success) where claim_success := server returned success=True.
    Model: Beta(a, b) posterior over Bernoulli success.
    """
    a: float = 1.0
    b: float = 1.0
    n: int = 0

    # Optional telemetry (nice for debugging / logging)
    mean_fidelity: float = 0.0
    mean_postsel_p: float = 0.0
    mean_margin: float = 0.0  # fidelity - threshold

    def update(self, success: bool, fidelity: float, threshold: float, postsel_p: float) -> None:
        self.n += 1
        if success:
            self.a += 1.0
        else:
            self.b += 1.0

        # incremental means
        def inc(mean: float, x: float) -> float:
            return mean + (x - mean) / max(1, self.n)

        self.mean_fidelity = inc(self.mean_fidelity, fidelity)
        self.mean_postsel_p = inc(self.mean_postsel_p, postsel_p)
        self.mean_margin = inc(self.mean_margin, fidelity - threshold)

    @property
    def mean_success(self) -> float:
        return self.a / (self.a + self.b)


class AdaptiveStrategy(BaseStrategy):
    """Select claimable edges using node value + 2-hop potential + learned success odds."""

    def __init__(
        self,
        graph: GraphData,
        *,
        utility_weight: float = 1.0,
        bell_pair_weight: float = 1.0,
        capacity_weight: float = 1.0,
        degree_weight: float = 1.0,
        owned_nodes: Sequence[str] | None = None,
        distance_dampening: float = 1.0,
        potential_weight: float = 0.4,
        # Bandit knobs
        bandit_threshold_bin: float = 0.05,
        bandit_ucb_c: float = 0.35,
        bandit_min_samples: int = 3,
        bandit_prior_strength: float = 2.0,
    ) -> None:
        self.graph = graph
        self.utility_weight = float(utility_weight)
        self.bell_pair_weight = float(bell_pair_weight)
        self.capacity_weight = float(capacity_weight)
        self.degree_weight = float(degree_weight)
        self.distance_dampening = float(distance_dampening)
        self.potential_weight = float(potential_weight)

        self.bandit_threshold_bin = float(bandit_threshold_bin)
        self.bandit_ucb_c = float(bandit_ucb_c)
        self.bandit_min_samples = int(bandit_min_samples)
        self.bandit_prior_strength = float(bandit_prior_strength)

        self.owned_nodes: Set[str] = set(owned_nodes or [])

        # Cache adjacency for cheap 2-hop potential calculations
        self._adjacency = self._build_adjacency(self.graph.get("edges", []))

        # Online learning: (difficulty, threshold_bin) -> bucket
        self._bandit: Dict[Tuple[int, float], _BanditBucket] = {}
        self._bandit_total_updates: int = 0

        self._distance_from_owned = self._compute_distances_from_owned(self.owned_nodes)
        self.node_scores = self._compute_node_scores()

    def update_owned_nodes(self, owned_nodes: Sequence[str]) -> None:
        """Update ownership context and recompute node scores."""
        self.owned_nodes = set(owned_nodes)
        self._distance_from_owned = self._compute_distances_from_owned(self.owned_nodes)
        self.node_scores = self._compute_node_scores()

    # ----------------------------
    # Bandit update hook (call from game loop)
    # ----------------------------
    def observe_claim_result(self, edge: Edge, result: Dict[str, Any]) -> None:
        """
        Update bandit stats after a claim attempt.

        Expected result format (from server/game):
          result["ok"] == True
          result["data"] contains:
            - success (bool): whether fidelity >= threshold and edge is claimed
            - fidelity (float)
            - threshold (float)
            - success_probability (float)  [post-selection probability]
        """
        if not result or not result.get("ok"):
            return
        data = result.get("data") or {}
        if not isinstance(data, dict):
            return

        success = bool(data.get("success", False))
        fidelity = float(data.get("fidelity", 0.0) or 0.0)
        threshold = float(data.get("threshold", data.get("base_threshold", 0.0)) or 0.0)
        postsel_p = float(data.get("success_probability", 0.0) or 0.0)

        key = self._bucket_key(edge)
        bucket = self._bandit.get(key)

        if bucket is None:
            # Initialize a mild Beta prior centered at our proxy estimate
            prior = self._estimate_success_prob_proxy(edge)  # 0.01..0.99
            k = max(0.0, self.bandit_prior_strength)
            a0 = 1.0 + prior * k
            b0 = 1.0 + (1.0 - prior) * k
            bucket = _BanditBucket(a=a0, b=b0)
            self._bandit[key] = bucket

        bucket.update(success=success, fidelity=fidelity, threshold=threshold, postsel_p=postsel_p)
        self._bandit_total_updates += 1

    def _bucket_key(self, edge: Edge) -> Tuple[int, float]:
        difficulty = int(edge.get("difficulty_rating", 0) or 0)
        threshold = float(edge.get("base_threshold", 0.0) or 0.0)

        if self.bandit_threshold_bin > 0:
            thr_bin = round(threshold / self.bandit_threshold_bin) * self.bandit_threshold_bin
        else:
            thr_bin = threshold

        # Stabilize float keys
        thr_bin = float(f"{thr_bin:.3f}")
        return (difficulty, thr_bin)

    # ----------------------------
    # Graph helpers
    # ----------------------------
    def _build_adjacency(self, edges: Sequence[Edge]) -> Dict[str, List[str]]:
        adjacency: Dict[str, List[str]] = {}
        for edge in edges:
            node_a, node_b = edge.get("edge_id", ("", ""))
            if not node_a or not node_b:
                continue
            adjacency.setdefault(node_a, []).append(node_b)
            adjacency.setdefault(node_b, []).append(node_a)
        return adjacency

    def _compute_degrees(self, edges: Sequence[Edge]) -> Dict[str, int]:
        degrees: Dict[str, int] = {}
        for edge in edges:
            node_a, node_b = edge.get("edge_id", ("", ""))
            for node_id in (node_a, node_b):
                if not node_id:
                    continue
                degrees[node_id] = degrees.get(node_id, 0) + 1
        return degrees

    def _compute_distances_from_owned(self, owned_nodes: Iterable[str]) -> Dict[str, int]:
        nodes = self.graph.get("nodes", [])
        adjacency = self._adjacency

        distances: Dict[str, int] = {}
        queue: deque[str] = deque()

        for node_id in owned_nodes:
            if node_id:
                distances[node_id] = 0
                queue.append(node_id)

        while queue:
            current = queue.popleft()
            current_distance = distances[current]
            for neighbor in adjacency.get(current, []):
                if neighbor not in distances:
                    distances[neighbor] = current_distance + 1
                    queue.append(neighbor)

        # mark unreachable nodes as -1
        for node in nodes:
            node_id = node.get("node_id")
            if node_id and node_id not in distances:
                distances[node_id] = -1

        return distances

    def _distance_factor(self, node_id: str) -> float:
        if not self.owned_nodes:
            return 1.0
        distance = self._distance_from_owned.get(node_id, -1)
        if distance < 0:
            return 0.0
        return 1.0 / (1.0 + self.distance_dampening * distance)

    # ----------------------------
    # Node scoring
    # ----------------------------
    def _compute_node_scores(self) -> Dict[str, float]:
        nodes = self.graph.get("nodes", [])
        edges = self.graph.get("edges", [])
        degrees = self._compute_degrees(edges)

        scores: Dict[str, float] = {}
        for node in nodes:
            node_id = node.get("node_id")
            if not node_id:
                continue
            scores[node_id] = self._score_node(node, degrees.get(node_id, 0))
        return scores

    def _score_node(self, node: Node, degree: int) -> float:
        utility = float(node.get("utility_qubits", 0) or 0.0)
        bell_pairs = float(node.get("bonus_bell_pairs", 0) or 0.0)
        capacity = float(node.get("capacity", 0) or 0.0)

        # Capacity is better treated sub-linearly
        cap_term = math.log1p(max(0.0, capacity))

        base_score = (
            self.utility_weight * utility
            + self.bell_pair_weight * bell_pairs
            + self.capacity_weight * cap_term
            + self.degree_weight * float(degree)
        )

        node_id = node.get("node_id", "")
        return base_score * self._distance_factor(node_id)

    def _two_hop_potential(self, node_id: str) -> float:
        """
        Sum of nearby node scores within 2 hops (discounted).
        Approximates value of regions unlocked by claiming node_id.
        """
        if not node_id:
            return 0.0

        seen: Set[str] = {node_id}
        total = 0.0

        # 1-hop neighbors
        for n1 in self._adjacency.get(node_id, []):
            if n1 in seen:
                continue
            seen.add(n1)
            total += 0.5 * self.node_scores.get(n1, 0.0)

            # 2-hop neighbors
            for n2 in self._adjacency.get(n1, []):
                if n2 in seen:
                    continue
                seen.add(n2)
                total += 0.25 * self.node_scores.get(n2, 0.0)

        return total

    # ----------------------------
    # Success probability estimation
    # ----------------------------
    def _estimate_success_prob_proxy(self, edge: Edge) -> float:
        """
        Cheap prior: monotone decreasing in difficulty and threshold.
        Used until bandit has enough samples for a bucket.
        """
        difficulty = float(edge.get("difficulty_rating", 0) or 0.0)
        threshold = float(edge.get("base_threshold", 0) or 0.0)

        p = 1.0 / (1.0 + 0.7 * max(0.0, difficulty))
        p *= max(0.05, 1.1 - threshold)

        return max(0.01, min(0.99, p))

    def _estimate_success_prob(self, edge: Edge) -> float:
        """
        Bandit estimate for p(claim_success).
        Uses UCB optimism to keep exploring buckets.
        """
        key = self._bucket_key(edge)
        bucket = self._bandit.get(key)
        if bucket is None or bucket.n < self.bandit_min_samples:
            return self._estimate_success_prob_proxy(edge)

        # UCB bonus: mean + c * sqrt(log(T)/n)
        T = max(1, self._bandit_total_updates)
        bonus = self.bandit_ucb_c * math.sqrt(math.log(T + 1.0) / max(1.0, float(bucket.n)))
        p = bucket.mean_success + bonus

        return max(0.01, min(0.99, p))

    # ----------------------------
    # Edge scoring / selection
    # ----------------------------
    def _edge_value(self, edge: Edge) -> tuple[float, tuple[str, str]]:
        node_a, node_b = edge.get("edge_id", ("", ""))
        if not node_a or not node_b:
            return (float("inf"), ("", ""))

        # Determine which endpoint is owned and which is the new frontier node.
        a_owned = node_a in self.owned_nodes
        b_owned = node_b in self.owned_nodes

        if a_owned and not b_owned:
            origin, new_node = node_a, node_b
        elif b_owned and not a_owned:
            origin, new_node = node_b, node_a
        else:
            # Not strictly claimable (both owned or both unowned); fall back deterministically
            origin, new_node = node_a, node_b

        new_score = self.node_scores.get(new_node, 0.0)
        origin_score = self.node_scores.get(origin, 0.0)

        potential = self._two_hop_potential(new_node)
        p_success = self._estimate_success_prob(edge)

        total_score = (new_score + self.potential_weight * potential) * p_success + 0.01 * origin_score

        # Deterministic tie-break
        edge_id = tuple(sorted((node_a, node_b)))
        return (-total_score, edge_id)

    def sort_edges(self, edges: List[Edge]) -> List[Edge]:
        return sorted(edges, key=self._edge_value)

    def select_edge(self, edges: List[Edge]) -> Edge:
        return edges[0]