from __future__ import annotations

from typing import Any, Dict

from qiskit import QuantumCircuit

from circuits.BaseCircuit import BaseCircuit


class AaronCircuit(BaseCircuit):
    """Two-pair recurrence (BBPSSW/DEJMPS-style) distillation circuit."""

    min_bell_pairs = 2
    max_bell_pairs = 2

    def get_num_bell_pairs(self, edge: Dict[str, Any]) -> int:
        return 2

    def get_flag_qubit(self, edge: Dict[str, Any]) -> int:
        return 2

    def build_circuit(self, edge: Dict[str, Any]) -> tuple[QuantumCircuit, int, int]:
        num_bell_pairs = self.get_num_bell_pairs(edge)
        flag_bit = self.get_flag_qubit(edge)
        if num_bell_pairs != 2:
            raise ValueError("AaronCircuit is fixed to two Bell pairs.")

        qc = QuantumCircuit(4, 3)

        qc.cx(1, 0)
        qc.cx(2, 3)
        
        qc.measure(0, 0)
        qc.measure(3, 1)
        
        # Corrections
        with qc.if_test((qc.clbits[0], 1)):
            qc.x(1)
        with qc.if_test((qc.clbits[1], 1)):
            qc.x(2)
        
        # Flag calculation: c[2] = c[0] XOR c[1]
        # If both 0 or both 1: c[2] = 0 (keep)
        # If different: c[2] = 1 (discard)
        qc.reset(0)  # Reuse qubit 0 for flag
        with qc.if_test((qc.clbits[0], 1)):
            qc.x(0)
        with qc.if_test((qc.clbits[1], 1)):
            qc.x(0)
        qc.measure(0, flag_bit)

        return qc, num_bell_pairs, flag_bit
