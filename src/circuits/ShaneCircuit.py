from __future__ import annotations

from typing import Any, Dict

from qiskit.circuit.classical import expr
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from circuits.BaseCircuit import BaseCircuit

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

def shane_distillation_circuit_1():
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

    def __init__(self, bell_pairs: int = 2, distillation_type: str = "z") -> None:
        super().__init__()
        self.bell_pairs = bell_pairs
        self.distillation_type = distillation_type

    def build_circuit(self, edge: Dict[str, Any]) -> tuple[QuantumCircuit, int, int]:
        bell_pairs = self.get_num_bell_pairs(edge)
        try:
            builder = self._CIRCUIT_BUILDERS[bell_pairs]
        except KeyError as exc:
            raise ValueError(f"Unsupported bell pair count: {bell_pairs}") from exc
        if bell_pairs == 1:
            circuit = builder()
        else:
            circuit = builder(self.distillation_type)
        flag_bit = self.get_flag_qubit(edge)
        return circuit, flag_bit, bell_pairs

    def get_num_bell_pairs(self, edge: Dict[str, Any]) -> int:
        return self.bell_pairs

    def get_flag_qubit(self, edge: Dict[str, Any]) -> int:
        try:
            return self._FLAG_BITS[self.bell_pairs]
        except KeyError as exc:
            raise ValueError(f"Unsupported bell pair count: {self.bell_pairs}") from exc
