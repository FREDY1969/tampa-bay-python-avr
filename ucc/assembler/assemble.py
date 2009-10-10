# assemble.py

import asm_opcodes

def assemble(insts):
    # Calculate instruction labels:
    address = 0
    labels = {}
    for label, opcode, op1, op2 in insts:
        if label is not None:
            labels[label] = address
        if opcode is not None:
            address += getattr(asm_opcodes, opcode.upper()).len

    # Generate instructions:
    address = 0
    for label, opcode, op1, op2 in insts:
        if opcode is not None:
            inst = getattr(asm_opcodes, opcode.upper())
            address += inst.len
            for n in inst.assemble(op1, op2, labels, address):
                yield n

