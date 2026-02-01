from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, TYPE_CHECKING

from qiskit import QuantumCircuit, qasm3


class BaseCircuit(ABC):
    """Base class for circuits used to claim edges in the game."""

    min_bell_pairs = 1
    max_bell_pairs = 8

    def __init__(self, circuit_path: Path | None = None) -> None:
        self.circuit_path = circuit_path
        self._circuit: QuantumCircuit | None = None

    @abstractmethod
    def build_circuit(self, edge: Dict[str, Any]) -> tuple[QuantumCircuit, int, int]:
        """Build the circuit if one is not loaded from disk."""

    @abstractmethod
    def get_num_bell_pairs(self, edge: Dict[str, Any]) -> int:
        """Choose the number of Bell pairs based on edge difficulty and threshold."""

    @abstractmethod
    def get_flag_qubit(self, edge: Dict[str, Any]) -> int:
        """Choose the classical flag bit index for post-selection."""

    def load(self, edge: Dict[str, Any]) -> QuantumCircuit:
        if self._circuit is not None:
            return self._circuit

        if self.circuit_path:
            resolved_path = self.circuit_path.expanduser().resolve()
            if not resolved_path.exists():
                raise FileNotFoundError(f"Circuit file not found: {resolved_path}")
            qasm_text = resolved_path.read_text()
            self._circuit = qasm3.loads(qasm_text)
            return self._circuit

        circuit, _, _ = self.build_circuit(edge)
        return circuit

    def circuit_for_edge(self, edge: Dict[str, Any]) -> QuantumCircuit:
        return self.load(edge)

    def qasm(self, edge: Dict[str, Any]) -> str:
        return qasm3.dumps(self.circuit_for_edge(edge))

    def should_retry(self, result: Dict[str, Any], attempt: int, max_attempts: int) -> bool:
        if attempt >= max_attempts:
            return False
        if not result.get("ok", False):
            return True
        data = result.get("data", {})
        return not data.get("success", False)

    def attempt_claims(
        self,
        game: "Game",
        edge_id: tuple[str, str],
        edge_info: Dict[str, Any] | None = None,
        capture_mode: str = "real",
        max_attempts: int = 1,
    ) -> Dict[str, Any]:
        """Attempt to claim an edge multiple times using this circuit."""
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")
        results: List[Dict[str, Any]] = []
        last_result: Dict[str, Any] | None = None
        for attempt in range(1, max_attempts + 1):
            last_result = game.claim_edge(
                edge_id=edge_id,
                circuit=self,
                edge_info=edge_info,
                capture_mode=capture_mode,
            )
            results.append(last_result)
            if not self.should_retry(last_result, attempt, max_attempts):
                break
        return {
            "ok": bool(last_result and last_result.get("ok", False)),
            "attempts": len(results),
            "results": results,
            "last_result": last_result,
        }


if TYPE_CHECKING:
    from game import Game
