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

def shane_block_xx_x_4():
    """Example distillation circuit template for 2 Bell pairs."""
    num_bell_pairs = 4
    qr = QuantumRegister(num_bell_pairs*2, 'q')  # 4 qubits for 2 Bell pairs
    cr = ClassicalRegister(num_bell_pairs*3, 'c')  # Classical bits for measurements + flag
    qc = QuantumCircuit(qr, cr)

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

    qz = create_z()
    qx = create_x()
    ##ORDERING IS IMPORTANT HEREqc,[0,2,3,1],range(3)
    qc.compose(qx, qubits=[0,2,3,1], clbits=range(3),inplace=True)
    qc.compose(qx, qubits=[6,4,5,7], clbits=range(3,6),inplace=True)
    qc.compose(qz, qubits=[2,3,4,5], clbits=range(6,9),inplace=True)

    false1 = expr.bit_or(expr.lift(qc.clbits[2]),expr.lift(qc.clbits[5]))
    qc.store(qc.clbits[9],false1) 
    false_condition = expr.bit_or(expr.lift(qc.clbits[8]),expr.lift(qc.clbits[9]))
    qc.store(qc.clbits[10],false_condition)

    return qc, 4

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

