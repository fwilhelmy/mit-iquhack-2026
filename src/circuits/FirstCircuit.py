from __future__ import annotations

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

from circuits.BaseCircuit import BaseCircuit


class FirstCircuit(BaseCircuit):
    min_bell_pairs = 2
    max_bell_pairs = 2

    def build_circuit(self) -> QuantumCircuit:
        return self.create_x()

    def create_x(self):
        qubit_pairs = 2
        qc = QuantumCircuit(qubit_pairs*2, 3)
        
        qc.cx(qubit_pairs-1, 0)
        qc.cx(qubit_pairs, qubit_pairs+1)

        qc.measure(0, 0)
        qc.measure(3, 1)
        
        # Flag calculation: c[2] = c[0] AND c[1]
        # If both 0 or both 1: c[2] = 0 (keep)
        # If different: c[2] = 1 (discard)
        self.storage(qc, 2)
        return qc

    def create_z(self):
        qubit_pairs = 2
        qc = QuantumCircuit(qubit_pairs*2, 3)

        qc.cx(0, qubit_pairs-1)
        qc.h(0)
        qc.cx(qubit_pairs*2-1, qubit_pairs)  
        qc.h(qubit_pairs*2-1)     

        qc.measure(0, 0)
        qc.measure(3, 1)

        # Flag calculation: c[2] = c[0] AND c[1]
        # If both 0 or both 1: c[2] = 0 (keep)
        # If different: c[2] = 1 (discard)
        self.storage(qc, 2)
        return qc

    def storage(self, qc, flag):
        qc.reset(0)  # Reuse qubit 0 for flag
        with qc.if_test((qc.clbits[0], 1)):
            qc.x(0)
        with qc.if_test((qc.clbits[1], 1)):
            qc.x(0)
        qc.measure(0, flag)

    def create_id(self):
        qc = QuantumCircuit(2, 1)
        return qc