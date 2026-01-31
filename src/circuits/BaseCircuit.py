from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, qasm3


class BaseCircuit(ABC):
    """Base class for circuits used to claim edges in the game."""

    def __init__(
        self,
        num_bell_pairs: int = 2,
        flag_bit: int = 0,
        circuit_path: Path | None = None,
    ) -> None:
        self.num_bell_pairs = num_bell_pairs
        self.flag_bit = flag_bit
        self.circuit_path = circuit_path
        self._circuit: QuantumCircuit | None = None

    @abstractmethod
    def build_circuit(self) -> QuantumCircuit:
        """Build the circuit if one is not loaded from disk."""

    def load(self) -> QuantumCircuit:
        if self._circuit is not None:
            return self._circuit

        if self.circuit_path:
            resolved_path = self.circuit_path.expanduser().resolve()
            if not resolved_path.exists():
                raise FileNotFoundError(f"Circuit file not found: {resolved_path}")
            qasm_text = resolved_path.read_text()
            self._circuit = qasm3.loads(qasm_text)
            return self._circuit

        self._circuit = self.build_circuit()
        return self._circuit

    @property
    def circuit(self) -> QuantumCircuit:
        return self.load()

    def qasm(self) -> str:
        return qasm3.dumps(self.circuit)


class DistillationCircuit(BaseCircuit):
    """Default distillation circuit based on the provided template."""

    def build_circuit(self) -> QuantumCircuit:
        if self.num_bell_pairs < 1:
            raise ValueError("num_bell_pairs must be at least 1.")

        qubit_count = 2 * self.num_bell_pairs
        qr = QuantumRegister(qubit_count, "q")
        cr = ClassicalRegister(2, "c")
        qc = QuantumCircuit(qr, cr)

        # TODO: Fill in your distillation protocol.
        # Qubit layout example for num_bell_pairs=2:
        #   q0, q3: Ancilla pair (to be measured)
        #   q1, q2: Data pair (output)

        return qc
