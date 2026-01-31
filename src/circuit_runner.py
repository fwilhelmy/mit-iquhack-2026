from __future__ import annotations

from pathlib import Path
from typing import Optional

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, qasm3


def create_distillation_circuit(num_bell_pairs: int = 2) -> QuantumCircuit:
    """Create a distillation circuit template based on the demo notebook."""
    if num_bell_pairs < 1:
        raise ValueError("num_bell_pairs must be at least 1.")

    qubit_count = 2 * num_bell_pairs
    qr = QuantumRegister(qubit_count, "q")
    cr = ClassicalRegister(2, "c")
    qc = QuantumCircuit(qr, cr)

    # TODO: Fill in your distillation protocol.
    # Qubit layout example for num_bell_pairs=2:
    #   q0, q3: Ancilla pair (to be measured)
    #   q1, q2: Data pair (output)

    return qc


def load_distillation_circuit(
    circuit_path: Optional[Path],
    num_bell_pairs: int = 2,
) -> QuantumCircuit:
    """Load a circuit from QASM3 or fall back to a template circuit."""
    if not circuit_path:
        circuit = create_distillation_circuit(num_bell_pairs=num_bell_pairs)
        print(circuit.draw(output="text"))
        return circuit

    resolved_path = circuit_path.expanduser().resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(f"Circuit file not found: {resolved_path}")

    qasm_text = resolved_path.read_text()
    circuit = qasm3.loads(qasm_text)
    print(circuit.draw(output="text"))
    return circuit
