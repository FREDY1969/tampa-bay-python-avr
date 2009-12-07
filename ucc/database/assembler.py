# assembler.py

import itertools
from ucc.database import crud

def gen_blocks(section):
    for block_id, label, address \
     in itertools.chain(
          crud.read_as_tuples('assembler_blocks', 'id', 'label', 'address',
                              section=section,
                              address_=None,
                              order_by=('address',)),
          crud.read_as_tuples('assembler_blocks', 'id', 'label', 'address',
                              section=section,
                              address=None)):
        yield block_id, label, address

def gen_insts(block_id):
    for label, opcode, op1, op2 \
     in crud.read_as_tuples('assembler_code',
                            'label',
                            'opcode',
                            'operand1',
                            'operand2',
                            block_id=block_id,
                            order_by=('inst_order',)):
        yield label, opcode, op1, op2

def update_block_address(block_id, address):
    crud.update('assembler_blocks', {'id': block_id}, address=address)

class block(object):
    def __init__(self, section, label, address = None, length = None):
        self.section = section
        self.label = label
        self.address = address
        self.length = length or 0
        self.clock_cycles = 0
        self.instructions = []

    def append_inst(self, opcode, operand1 = None, operand2 = None,
                    length = None, clocks = None,
                    position_info = (None, None, None, None)):
        self.instructions.append(inst(opcode, operand1, operand2,
                                      length, clocks, position_info))
        self.length += length
        self.clock_cycles += clocks

    def write(self):
        old_id = crud.read1_column('assembler_blocks', 'id',
                                   label=self.label, zero_ok=True)
        if old_id is not None:
            crud.delete('assembler_blocks', id=old_id)
            crud.delete('assembler_code', block_id=old_id)
        self.id = crud.insert('assembler_blocks',
                              section=self.section,
                              label=self.label,
                              address=self.address,
                              length=self.length,
                              clock_cycles=self.clock_cycles,
                             )
        for i, instruction in enumerate(self.instructions):
            instruction.write(self.id, i)

class inst(object):
    def __init__(self, opcode, operand1 = None, operand2 = None,
                       length = None, clocks = None,
                       position_info = (None, None, None, None)):
        self.label = None
        self.opcode = opcode
        self.operand1 = operand1
        self.operand2 = operand2
        self.length = length
        self.clocks = clocks
        self.line_start, self.column_start, self.line_end, self.column_end = \
          position_info

    def write(self, block_id, inst_order):
        return crud.insert('assembler_code',
                           block_id=block_id,
                           inst_order=inst_order,
                           label=self.label,
                           opcode=self.opcode,
                           operand1=self.operand1,
                           operand2=self.operand2,
                           length=self.length,
                           clocks=self.clocks,
                           line_start=self.line_start,
                           column_start=self.column_start,
                           line_end=self.line_end,
                           column_end=self.column_end,
                          )

