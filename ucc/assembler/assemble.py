# assemble.py

r'''The AVR assembler.
'''

import itertools

from ucc.database import assembler, crud
from ucc.assembler import asm_opcodes, hex_file
from ucc.codegen import expand_assembler

def assign_labels(section, labels, starting_address = 0):
    r'''Assign addresses to all labels in 'section'.

    Addresses are stored in 'labels' dict.  This is {label: address}.
    '''
    last_next = None
    running_address = starting_address
    for block_id, block_label, block_address, next_block \
     in assembler.gen_blocks(section):
        if last_next and last_next != block_label:
            running_address += \
              getattr(asm_opcodes, 'JMP').length(last_next, None)[1]
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
                address += getattr(asm_opcodes, opcode.upper()) \
                             .length(op1, op2)[1]
        if address > running_address:
            running_address = address
    return running_address

def assemble(section, labels):
    r'''Meta generator for an assembler 'section'.

    This generator function yields (address, byte) for all blocks in 'section'.
    '''
    last_next = None
    last_address = None
    for block_id, block_label, block_address, next_block \
     in assembler.gen_blocks(section):
        if last_next and last_next != block_label:
            last_address += 1
            for n in getattr(asm_opcodes, 'JMP') \
                       .assemble(last_next, None, labels, last_address):
                yield last_address, n
                last_address += 1
        assert last_address is None or last_address + 1 == block_address, \
               "internal logic error: last_address ({}) != block_address ({})" \
                 .format(last_address, block_address)
        for address, byte in assemble_word(block_id, block_address, labels):
            yield address, byte
            last_address = address
        last_next = next_block
    if last_next is not None:
        last_address += 1
        for n in getattr(asm_opcodes, 'JMP') \
                   .assemble(last_next, None, labels, last_address):
            yield last_address, n
            last_address += 1

def assemble_word(block_id, block_address, labels):
    r'''Yields (address, byte) for all instructions in an assembler block.

    The bytes are generated taking byte swapping into account.  The AVR is
    little-endian, so the least significant byte of each instruction word is
    generated first.
    '''
    address = block_address
    for label, opcode, op1, op2 in assembler.gen_insts(block_id):
        if opcode is not None:
            inst = getattr(asm_opcodes, opcode.upper())
            for n in inst.assemble(op1, op2, labels, address):
                yield address, n
                address += 1
            #address += getattr(asm_opcodes, opcode.upper()).length(op1, op2)[1]

def assemble_program(package_dir):
    r'''Assemble all of the sections.

    Generates .hex files in package_dir.
    '''

    # Assign addresses to all labels in all sections:
    labels = {}         # {label: address}

    with crud.db_transaction():
        # code
        start_data = assign_labels('code', labels)

        # data
        assert 'start_data' not in labels, \
               "duplicate assembler label: start_data"
        labels['start_data'] = start_data
        data_len = assign_labels('data', labels)
        assert 'data_len' not in labels, \
               "duplicate assembler label: data_len"
        labels['data_len'] = data_len

        # bss
        bss_end = assign_labels('bss', labels, data_len)
        assert 'bss_len' not in labels, \
               "duplicate assembler label: bss_len"
        labels['bss_len'] = bss_end - data_len

        # eeprom
        assign_labels('eeprom', labels)

    # assemble flash and data:
    hex_file.write(itertools.chain(assemble('code', labels),
                                   assemble('data', labels)),
                   package_dir, 'flash')

    # check that bss is blank!
    try:
        next(assemble('bss', labels))
    except StopIteration:
        pass
    else:
        raise AssertionError("bss is not blank!")

    # assemble eeprom:
    hex_file.write(assemble('eeprom', labels), package_dir, 'eeprom')

