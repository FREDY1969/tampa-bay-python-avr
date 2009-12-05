# assemble.py

from ucc.database import assembler
from ucc.assembler import asm_opcodes

def assign_labels(section, labels, starting_address = 0):
    r'''Assign addresses to all labels in 'section'.

    Addresses are stored in 'labels' dict.  This is {label: address}.
    '''
    running_address = starting_address
    for block_id, block_label, block_address in assembler.gen_blocks(section):
        if block_address is None:
            address = running_address
            assembler.update_block_address(block_id, address)
        else:
            address = block_address
        assert block_label not in labels, \
               "duplicate assembler label: " + block_label
        labels[block_label] = address
        for label, opcode, op1, op2 in assembler.gen_insts(block_id):
            if label is not None:
                assert label not in labels, \
                       "duplicate assembler label: " + label
                labels[label] = address
            if opcode is not None:
                address += getattr(asm_opcodes, opcode.upper()).length(op1, op2)
        if address > running_address:
            running_address = address
    return running_address

def assemble(section, labels):
    r'''Yields individual bytes for all instructions in 'section'.
    '''
    for block_id, block_label, block_address in assembler.gen_blocks(section):
        yield block_address, assemble_word(block_id, block_address, labels)

def assemble_word(block_id, block_address, labels):
    r'''Yields individual bytes for all instructions in 'section'.
    '''
    address = block_address
    for label, opcode, op1, op2 in assembler.gen_insts(block_id):
        if opcode is not None:
            inst = getattr(asm_opcodes, opcode.upper())
            for n in inst.assemble(op1, op2, labels, address):
                yield n
                address += 1
            #address += getattr(asm_opcodes, opcode.upper()).length(op1, op2)
