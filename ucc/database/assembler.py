# assembler.py

import itertools
from ucc.database import crud

def gen_blocks(section):
    for block_id, label, address \
     in itertools.chain(
          crud.read_as_tuples('assembler_words', 'id', 'label', 'address',
                              section=section,
                              address_=None,
                              order_by=('address',)),
          crud.read_as_tuples('assembler_words', 'id', 'label', 'address',
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

class block(object):
    def __init__(self, section, label, address = None, length = None):
        self.section = section
        self.label = label
        self.address = address
        self.length = length

    def write(self, insts):
        old_id = crud.read1_column('assembler_words', 'id',
                                   label=self.label, zero_ok=True)
        if old_id is not None:
            crud.delete('assembler_words', id=old_id)
            crud.delete('assembler_code', block_id=old_id)
        id = crud.insert('assembler_words',
                         section=self.section,
                         label=self.label,
                         address=self.address,
                         length=self.length,
                        )
        for i, inst in enumerate(insts):
            inst.write(id, i)

class inst(object):
    def __init__(self, label, opcode, operand1 = None, operand2 = None,
                       length = None, clocks = None,
                       position_info = (None, None, None, None)):
        self.label = label
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

