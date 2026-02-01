from __future__ import annotations

from typing import Any, Dict

from qiskit import QuantumCircuit

from circuits.BaseCircuit import BaseCircuit


def aaron_circuit_2pairs():
    qc = QuantumCircuit(4, 3)
    qc.cx(1, 0)
    qc.cx(2, 3)
    qc.measure(0, 0)
    qc.measure(3, 1)
    with qc.if_test((qc.clbits[0], 1)):
        qc.x(1)
    with qc.if_test((qc.clbits[1], 1)):
        qc.x(2)
    qc.reset(0)
    with qc.if_test((qc.clbits[0], 1)):
        qc.x(0)
    with qc.if_test((qc.clbits[1], 1)):
        qc.x(0)
    qc.measure(0, 2)
    return qc, 2

def aaron_circuit_3pairs_xx():
    qc = QuantumCircuit(6, 5)
    for i in range(2):
        qc.cx(2, i)
        qc.cx(3, 5-i)
    for i in range(2):
        qc.measure(i, i)
        qc.measure(5-i, 2+i)
    for i in range(2):
        with qc.if_test((qc.clbits[i], 1)):
            qc.x(2)
        with qc.if_test((qc.clbits[2+i], 1)):
            qc.x(3)
    qc.reset(1)
    for i in range(4):
        with qc.if_test((qc.clbits[i], 1)):
            qc.x(1)
    qc.measure(1, 4)
    return qc, 3

def aaron_circuit_4pairs():
    qc = QuantumCircuit(8, 7)
    for i in range(3):
        qc.cx(3, i)
        qc.cx(4, 7-i)
    for i in range(3):
        qc.measure(i, i)
        qc.measure(7-i, 3+i)
    for i in range(3):
        with qc.if_test((qc.clbits[i], 1)):
            qc.x(3)
        with qc.if_test((qc.clbits[3+i], 1)):
            qc.x(4)
    qc.reset(1)
    for i in range(6):
        with qc.if_test((qc.clbits[i], 1)):
            qc.x(1)
    qc.measure(1, 6)
    return qc, 4


class AaronCircuit(BaseCircuit):
    """Aaron's distillation circuit family."""

    _CIRCUIT_BUILDERS = {
        2: aaron_circuit_2pairs,
        3: aaron_circuit_3pairs_xx,
        4: aaron_circuit_4pairs,
    }

    def __init__(self, bell_pairs: int = 2) -> None:
        super().__init__()
        self.bell_pairs = bell_pairs

    def build_circuit(self, edge: Dict[str, Any]) -> tuple[QuantumCircuit, int, int]:
        bell_pairs = self.get_num_bell_pairs(edge)
        try:
            builder = self._CIRCUIT_BUILDERS[bell_pairs]
        except KeyError as exc:
            raise ValueError(f"Unsupported bell pair count: {bell_pairs}") from exc
        circuit, num_pairs = builder()
        flag_bit = circuit.num_clbits - 1
        return circuit, flag_bit, num_pairs

    def get_num_bell_pairs(self, edge: Dict[str, Any]) -> int:
        return self.bell_pairs

    def get_flag_qubit(self, edge: Dict[str, Any]) -> int:
        circuit, flag_bit, _ = self.build_circuit(edge)
        return flag_bit
