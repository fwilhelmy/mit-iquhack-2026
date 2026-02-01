from qiskit.circuit.classical import expr
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

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

    return qc

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

    return qc