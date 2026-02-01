from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

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

    def validate_edge(self, edge: Dict[str, Any]) -> None:
        """Validate edge metadata against circuit limits."""
        num_bell_pairs = self.get_num_bell_pairs(edge)
        if num_bell_pairs < self.min_bell_pairs:
            raise ValueError(
                f"num_bell_pairs must be >= {self.min_bell_pairs} for {self.__class__.__name__}."
            )
        if num_bell_pairs > self.max_bell_pairs:
            raise ValueError(
                f"num_bell_pairs must be <= {self.max_bell_pairs} for {self.__class__.__name__}."
            )

    def load(self, edge: Dict[str, Any]) -> QuantumCircuit:
        self.validate_edge(edge)
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
