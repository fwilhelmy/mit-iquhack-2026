from __future__ import annotations

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

from circuits.BaseCircuit import BaseCircuit


class AaronCircuit(BaseCircuit):
    """Two-pair recurrence (BBPSSW/DEJMPS-style) distillation circuit."""

    def build_circuit(self) -> QuantumCircuit:
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
        qc.measure(0, 2)
        
        return qc