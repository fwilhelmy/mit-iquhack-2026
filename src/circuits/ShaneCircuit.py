from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from qiskit.circuit.classical import expr
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from circuits.BaseCircuit import BaseCircuit

if TYPE_CHECKING:
    from game import Game

def measure_z_errors():
    """
    Number of bell pairs: 1
    Run this circuit on measure the probability with which Z errors occur.
    Set the flag bit to idx 2.
    1 - success rate is equal with the probability of which Z errors occur.
    """
    qr = QuantumRegister(2, 'q')  # 4 qubits for 2 Bell pairs
    cr = ClassicalRegister(3, 'c')  # Classical bits for measurements + flag
    qc = QuantumCircuit(qr, cr)

    qc.measure(qr[0], cr[0])
    qc.measure(qr[1], cr[1])

    qc.store(cr[2], expr.bit_xor(expr.lift(cr[0]), expr.lift(cr[1])))

    return qc, 1

def measure_x_errors():
    """
    Number of bell pairs: 1
    Run this circuit on measure the probability with which X errors occur.
    Set the flag bit to idx 2.
    1 - success rate is equal with the probability of which X errors occur.
    """
    qr = QuantumRegister(2, 'q')  # 4 qubits for 2 Bell pairs
    cr = ClassicalRegister(3, 'c')  # Classical bits for measurements + flag
    qc = QuantumCircuit(qr, cr)
    qc.h(0)
    qc.h(1)

    qc.measure(qr[0], cr[0])
    qc.measure(qr[1], cr[1])

    qc.store(cr[2], expr.bit_xor(expr.lift(cr[0]), expr.lift(cr[1])))

    return qc, 1


def create_x():
    qubit_pairs = 2
    qc = QuantumCircuit(qubit_pairs * 2, 3)

    qc.cx(1, 0)
    qc.cx(2, 3)

    qc.measure(0, 0)
    qc.measure(3, 1)
    condition1 = expr.bit_xor(expr.lift(qc.clbits[0]), expr.lift(qc.clbits[1]))
    qc.store(qc.clbits[2], condition1)
    return qc

def create_z():
    qubit_pairs = 2
    qc = QuantumCircuit(qubit_pairs * 2, 3)

    qc.cx(0, qubit_pairs - 1)
    qc.h(0)
    qc.cx(qubit_pairs * 2 - 1, qubit_pairs)
    qc.h(qubit_pairs * 2 - 1)

    qc.measure(0, 0)
    qc.measure(3, 1)

    condition1 = expr.bit_xor(expr.lift(qc.clbits[0]), expr.lift(qc.clbits[1]))
    qc.store(qc.clbits[2], condition1)
    qc.name = "Z_distillation"
    return qc

def shane_distillation_circuit_1(t):
    "Basically, the identity"
    qc = QuantumCircuit(2, 1)
    return qc

def shane_distillation_circuit_2(t): # THIS ONE
    """Example distillation circuit template for 2 Bell pairs."""
    """Minimum case"""
    "t = z or x"
    if t == "z":
        q = create_z()
    elif t == "x":
        q = create_x()
    num_bell_pairs = 2
    qr = QuantumRegister(num_bell_pairs * 2, 'q')  # 4 qubits for 2 Bell pairs
    cr = ClassicalRegister(num_bell_pairs * 3, 'c')  # Classical bits for measurements + flag
    qc = QuantumCircuit(qr, cr)

    qc.compose(q, qubits=[0, 1, 2, 3], clbits=range(3), inplace=True)
    return qc


def shane_distillation_circuit_4(t):
    """Example distillation circuit template for 2 Bell pairs."""
    "t = z or x"
    if t == "z":
        q = create_z()
    elif t == "x":
        q = create_x()
    num_bell_pairs = 4
    qr = QuantumRegister(num_bell_pairs * 2, 'q')  # 4 qubits for 2 Bell pairs
    cr = ClassicalRegister(num_bell_pairs * 3, 'c')  # Classical bits for measurements + flag
    qc = QuantumCircuit(qr, cr)

    ##ORDERING IS IMPORTANT HERE
    qc.compose(q, qubits =[0,1,6,7],clbits=range(3),inplace=True)
    qc.compose(q, qubits=[2,3,4,5], clbits=range(3,6),inplace=True)
    qc.compose(q, qubits=[1,3,4,6], clbits=range(6,9),inplace=True)

    false1 = expr.bit_or(expr.lift(qc.clbits[2]), expr.lift(qc.clbits[5]))
    qc.store(qc.clbits[9], false1)
    false_condition = expr.bit_or(expr.lift(qc.clbits[8]), expr.lift(qc.clbits[9]))
    qc.store(qc.clbits[10], false_condition)

    return qc

def distillation_circuit_6(t):
    """Example distillation circuit template for 2 Bell pairs."""
    "t = z or x"
    if t == "z":
        q = create_z()
    elif t == "x":
        q = create_x()
    num_bell_pairs = 6
    qr = QuantumRegister(num_bell_pairs * 2, 'q')  # 4 qubits for 2 Bell pairs
    cr = ClassicalRegister(19, 'c')  # Classical bits for measurements + flag
    qc = QuantumCircuit(qr, cr)

    qz = create_z()
    qx = create_x()
    ##ORDERING IS IMPORTANT HERE
    #Stage 1
    qc.compose(qx, qubits=[0,1,10,11], clbits=range(3),inplace=True)
    qc.compose(qx, qubits=[2,3,8,9], clbits=range(3,6),inplace=True)
    qc.compose(qx, qubits=[4,5,6,7], clbits=range(6,9),inplace=True)
    #Stage 2
    qc.compose(qx, qubits=[1,3,8,10], clbits=range(9,12),inplace=True)
    #Stage 3
    qc.compose(qx, qubits=[3,5,6,8], clbits=range(12,15),inplace=True)

    # COMPARISONS
    false1 = expr.bit_or(expr.lift(qc.clbits[2]), expr.lift(qc.clbits[5]))
    qc.store(qc.clbits[15], false1)
    false2 = expr.bit_or(expr.lift(qc.clbits[8]), expr.lift(qc.clbits[11]))
    qc.store(qc.clbits[16], false2)

    # COMPARISONS STAGE 2
    false4 = expr.bit_or(expr.lift(qc.clbits[15]), expr.lift(qc.clbits[16]))
    qc.store(qc.clbits[17], false4)

    false_condition = expr.bit_or(expr.lift(qc.clbits[14]), expr.lift(qc.clbits[17]))
    qc.store(qc.clbits[18], false_condition)

    return qc


class ShaneCircuit(BaseCircuit):
    """Shane's distillation circuit family."""

    _BELL_PAIR_STEPS = (2, 4, 6)

    _CIRCUIT_BUILDERS = {
        1: shane_distillation_circuit_1,
        2: shane_distillation_circuit_2,
        4: shane_distillation_circuit_4,
        6: distillation_circuit_6,
    }

    _FLAG_BITS = {
        1: 0,
        2: 2,
        4: 10,
        6: 18,
    }

    def __init__(self) -> None:
        super().__init__()

    def build_circuit(
        self,
        edge: Dict[str, Any],
        bell_pairs: int | None = None,
        distillation_type: str | None = None,
    ) -> tuple[QuantumCircuit, int, int]:
        bell_pairs = self.get_num_bell_pairs(edge, bell_pairs=bell_pairs)
        distillation_type = distillation_type or edge.get("distillation_type", "z")
        try:
            builder = self._CIRCUIT_BUILDERS[bell_pairs]
        except KeyError as exc:
            raise ValueError(f"Unsupported bell pair count: {bell_pairs}") from exc
        if bell_pairs == 1:
            circuit = builder()
        else:
            circuit = builder(distillation_type)
        flag_bit = self.get_flag_qubit(edge, bell_pairs=bell_pairs)
        return circuit, flag_bit, bell_pairs

    def get_num_bell_pairs(self, edge: Dict[str, Any], bell_pairs: int | None = None) -> int:
        if bell_pairs is not None:
            return bell_pairs
        return int(edge.get("bell_pairs", 2))

    def get_flag_qubit(self, edge: Dict[str, Any], bell_pairs: int | None = None) -> int:
        resolved_pairs = self.get_num_bell_pairs(edge, bell_pairs=bell_pairs)
        try:
            return self._FLAG_BITS[resolved_pairs]
        except KeyError as exc:
            raise ValueError(f"Unsupported bell pair count: {resolved_pairs}") from exc

    def attempt_claims(
        self,
        game: "Game",
        edge_id: tuple[str, str],
        edge_info: Dict[str, Any] | None = None,
        capture_mode: str = "real",
        max_attempts: int = 1,
    ) -> Dict[str, Any]:
        """Attempt to claim an edge using Shane's adaptive heuristic."""
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")
        if edge_info is None:
            edge_info = game.get_edge_info(edge_id[0], edge_id[1])
        if edge_info is None:
            raise ValueError("Edge metadata is required to claim an edge.")

        difficulty = int(edge_info.get("difficulty_rating", 0))
        distillation_type = "z" if difficulty % 2 == 1 else "x"
        bell_pairs = 2

        results: list[Dict[str, Any]] = []
        last_result: Dict[str, Any] | None = None

        for attempt in range(1, max_attempts + 1):
            attempt_edge_info = dict(edge_info)
            attempt_edge_info["bell_pairs"] = bell_pairs
            attempt_edge_info["distillation_type"] = distillation_type
            last_result = game.claim_edge(
                edge_id=edge_id,
                circuit=self,
                edge_info=attempt_edge_info,
                capture_mode=capture_mode,
            )
            last_result['bell_pairs'] = bell_pairs
            last_result['distillation_type'] = distillation_type
            results.append(last_result)

            if last_result.get("ok", False) and last_result.get("data", {}).get("success", False):
                break

            fidelity = last_result.get("data", {}).get("fidelity")
            if fidelity is not None and fidelity > 0.75:
                bell_pairs = self._next_bell_pair_count(bell_pairs)
            else:
                distillation_type = "x" if distillation_type == "z" else "z"
                bell_pairs = 2

        return {
            "ok": bool(last_result and last_result.get("ok", False)),
            "attempts": len(results),
            "results": results,
            "last_result": last_result,
        }

    def _next_bell_pair_count(self, bell_pairs: int) -> int:
        for count in self._BELL_PAIR_STEPS:
            if count > bell_pairs:
                return count
        return bell_pairs
