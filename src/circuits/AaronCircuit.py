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