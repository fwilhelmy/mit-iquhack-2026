from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, partial_trace, state_fidelity

from circuit_runner import load_distillation_circuit


def _build_initial_state(num_bell_pairs: int) -> Statevector:
    if num_bell_pairs < 1:
        raise ValueError("num_bell_pairs must be at least 1.")

    total_qubits = 2 * num_bell_pairs
    circuit = QuantumCircuit(total_qubits)
    for index in range(num_bell_pairs):
        alice = index
        bob = total_qubits - 1 - index
        circuit.h(alice)
        circuit.cx(alice, bob)
    return Statevector.from_instruction(circuit)


def _strip_measurements(circuit: QuantumCircuit) -> QuantumCircuit:
    stripped = circuit.remove_final_measurements(inplace=False)
    for instruction in stripped.data:
        condition = getattr(instruction.operation, "condition", None)
        if condition is not None:
            raise ValueError("Simulation does not support classical conditionals.")
        if instruction.operation.name == "measure":
            raise ValueError("Simulation does not support mid-circuit measurements.")
    return stripped


def _flag_qubit_index(circuit: QuantumCircuit, flag_bit: int) -> int:
    for instruction in circuit.data:
        if instruction.operation.name != "measure":
            continue
        qubit = instruction.qubits[0]
        clbit = instruction.clbits[0]
        if circuit.clbits.index(clbit) == flag_bit:
            return circuit.qubits.index(qubit)
    raise ValueError(f"Flag bit {flag_bit} is not mapped to any measurement.")


def _post_select_zero(state: Statevector, qubit_index: int) -> Tuple[Statevector, float]:
    data = state.data.copy()
    for index in range(len(data)):
        if (index >> qubit_index) & 1:
            data[index] = 0
    success_prob = float(np.vdot(data, data).real)
    if success_prob <= 0:
        return Statevector(data), 0.0
    return Statevector(data / np.sqrt(success_prob)), success_prob


def _reduced_fidelity(state: Statevector, keep_qubits: Iterable[int]) -> float:
    total_qubits = state.num_qubits
    keep_qubits = sorted(keep_qubits)
    trace_out = [q for q in range(total_qubits) if q not in keep_qubits]
    reduced = partial_trace(state, trace_out)
    phi_plus = Statevector(np.array([1, 0, 0, 1]) / np.sqrt(2))
    return float(state_fidelity(reduced, phi_plus))


def simulate_capture(
    edge_id: Tuple[str, str],
    circuit: QuantumCircuit,
    num_bell_pairs: int,
    flag_bit: int,
    threshold: float | None = None,
) -> Dict[str, Any]:
    """Simulate a capture locally and return a response-like payload."""
    try:
        if circuit.num_qubits != 2 * num_bell_pairs:
            raise ValueError("Circuit qubit count must be 2 * num_bell_pairs.")
        if circuit.num_clbits <= flag_bit:
            raise ValueError("flag_bit is out of range for the circuit's classical bits.")

        measurement_qubit = _flag_qubit_index(circuit, flag_bit)
        initial_state = _build_initial_state(num_bell_pairs)
        evolved = initial_state.evolve(_strip_measurements(circuit))

        post_state, success_prob = _post_select_zero(evolved, measurement_qubit)
        if success_prob == 0:
            fidelity = 0.0
        else:
            target_qubits = (num_bell_pairs - 1, num_bell_pairs)
            fidelity = _reduced_fidelity(post_state, target_qubits)

        success = fidelity >= threshold if threshold is not None else True

        return {
            "ok": True,
            "data": {
                "edge": [edge_id[0], edge_id[1]],
                "fidelity": fidelity,
                "success_probability": success_prob,
                "success": success,
                "threshold": threshold,
                "flag_bit": flag_bit,
                "num_bell_pairs": num_bell_pairs,
                "mode": "sim",
            },
        }
    except ValueError as exc:
        return {
            "ok": False,
            "error": {"code": "SIMULATION_ERROR", "message": str(exc)},
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate an edge capture locally.")
    parser.add_argument("--edge", nargs=2, metavar=("NODE_A", "NODE_B"), required=True)
    parser.add_argument("--num-bell-pairs", type=int, default=2)
    parser.add_argument("--flag-bit", type=int, default=0)
    parser.add_argument("--circuit-path", type=Path)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    circuit = load_distillation_circuit(args.circuit_path, num_bell_pairs=args.num_bell_pairs)
    result = simulate_capture(
        edge_id=(args.edge[0], args.edge[1]),
        circuit=circuit,
        num_bell_pairs=args.num_bell_pairs,
        flag_bit=args.flag_bit,
        threshold=args.threshold,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
