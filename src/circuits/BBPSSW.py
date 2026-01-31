from __future__ import annotations

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

from circuits.BaseCircuit import BaseCircuit


class BBPSSW(BaseCircuit):
    """Two-pair recurrence (BBPSSW/DEJMPS-style) distillation circuit."""

    min_bell_pairs = 2
    max_bell_pairs = 8

    def build_circuit(self) -> QuantumCircuit:
        if self.num_bell_pairs < 2:
            raise ValueError("BBPSSW requires at least two Bell pairs.")

        total_qubits = 2 * self.num_bell_pairs
        qreg = QuantumRegister(total_qubits, "q")
        flag_reg = ClassicalRegister(self.flag_bit + 1, "flag")
        meas_reg = ClassicalRegister(2, "meas")
        circuit = QuantumCircuit(qreg, flag_reg, meas_reg)

        alice_keep = self.num_bell_pairs - 1
        bob_keep = self.num_bell_pairs
        alice_sacr = self.num_bell_pairs - 2
        bob_sacr = self.num_bell_pairs + 1

        circuit.cx(qreg[alice_keep], qreg[alice_sacr])
        circuit.cx(qreg[bob_keep], qreg[bob_sacr])

        circuit.measure(qreg[alice_sacr], meas_reg[0])
        circuit.measure(qreg[bob_sacr], meas_reg[1])

        circuit.reset(qreg[alice_sacr])
        with circuit.if_test((meas_reg, 1)):
            circuit.x(qreg[alice_sacr])
        with circuit.if_test((meas_reg, 2)):
            circuit.x(qreg[alice_sacr])

        circuit.measure(qreg[alice_sacr], flag_reg[self.flag_bit])
        return circuit
