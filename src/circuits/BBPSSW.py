from __future__ import annotations

from typing import Any, Dict

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

from circuits.BaseCircuit import BaseCircuit


class BBPSSW(BaseCircuit):
    """Two-pair recurrence (BBPSSW/DEJMPS-style) distillation circuit."""

    min_bell_pairs = 2
    max_bell_pairs = 8

    def get_num_bell_pairs(self, edge: Dict[str, Any]) -> int:
        difficulty = edge.get("difficulty_rating", 0)
        threshold = edge.get("base_threshold", 0)
        recommended = 2
        if difficulty >= 4 or threshold >= 0.8:
            recommended = 6
        elif difficulty >= 3 or threshold >= 0.6:
            recommended = 5
        elif difficulty >= 2 or threshold >= 0.4:
            recommended = 4
        elif difficulty >= 1 or threshold >= 0.2:
            recommended = 3
        return max(self.min_bell_pairs, min(self.max_bell_pairs, recommended))

    def get_flag_qubit(self, edge: Dict[str, Any]) -> int:
        return 0

    def build_circuit(self, edge: Dict[str, Any]) -> tuple[QuantumCircuit, int, int]:
        num_bell_pairs = self.get_num_bell_pairs(edge)
        flag_bit = self.get_flag_qubit(edge)
        if num_bell_pairs < 2:
            raise ValueError("BBPSSW requires at least two Bell pairs.")

        total_qubits = 2 * num_bell_pairs
        qreg = QuantumRegister(total_qubits, "q")
        flag_reg = ClassicalRegister(flag_bit + 1, "flag")
        meas_reg = ClassicalRegister(2, "meas")
        circuit = QuantumCircuit(qreg, flag_reg, meas_reg)

        alice_keep = num_bell_pairs - 1
        bob_keep = num_bell_pairs
        alice_sacr = num_bell_pairs - 2
        bob_sacr = num_bell_pairs + 1

        circuit.cx(qreg[alice_keep], qreg[alice_sacr])
        circuit.cx(qreg[bob_keep], qreg[bob_sacr])

        circuit.measure(qreg[alice_sacr], meas_reg[0])
        circuit.measure(qreg[bob_sacr], meas_reg[1])

        circuit.reset(qreg[alice_sacr])
        with circuit.if_test((meas_reg, 1)):
            circuit.x(qreg[alice_sacr])
        with circuit.if_test((meas_reg, 2)):
            circuit.x(qreg[alice_sacr])

        circuit.measure(qreg[alice_sacr], flag_reg[flag_bit])
        return circuit, num_bell_pairs, flag_bit
