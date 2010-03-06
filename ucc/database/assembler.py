# assembler.py

r'''Helper classes for the assembler source code in the database.
'''

import itertools
from ucc.database import crud
from ucc.assembler import asm_opcodes

def gen_blocks(section):
    r'''Generates (block_id, label, address) for each block in section.
    '''
    for block_id, label, address \
     in itertools.chain(
          crud.read_as_tuples('assembler_blocks', 'id', 'label', 'address',
                              section=section,
                              address_=None,
                              order_by=('address',)),
          crud.read_as_tuples('assembler_blocks', 'id', 'label', 'address',
                              section=section,
                              address=None,
                              order_by=('id',))):
        yield block_id, label, address

def gen_insts(block_id):
    r'''Generates (label, opcode, op1, op2) for each instruction in block.
    '''
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
    r'''This represents a block of assembler instructions.

    Assembler instructions are grouped into blocks to allow the assembler to
    order the blocks in such a way as to maximize the use of relative jump
    instructions.  Relative jumps are one word instructions, vs the absolute
    jump which is two words.
    '''
    def __init__(self, word_symbol_id, section, label,
                 address = None, length = None):
        self.word_symbol_id = word_symbol_id
        self.section = section
        self.label = label
        self.address = address
        self.min_length = length or 0
        self.max_length = length or 0
        self.min_clock_cycles = 0
        self.max_clock_cycles = 0
        self.next_label = None
        self.instructions = []

    def append_inst(self, opcode, operand1 = None, operand2 = None,
                    position_info = (None, None, None, None),
                    syntax_error_info = None):
        i = inst(opcode, operand1, operand2, position_info,
                 syntax_error_info=syntax_error_info)
        self.instructions.append(i)

        self.min_length += i.min_length
        self.max_length += i.max_length
        self.min_clock_cycles += i.min_clocks
        self.max_clock_cycles += i.max_clocks

    def falls_through(self):
        r'''Return True iff the block falls through to the next block.'''
        if self.instructions and self.instructions[-1].end:
            return False
        return True

    def next_block(self, next_label):
        self.next_label = next_label

    def write(self):
        r'''Also writes the instructions to the database.
        '''
        self.id = crud.insert('assembler_blocks',
                              section=self.section,
                              label=self.label,
                              address=self.address,
                              min_length=self.min_length,
                              max_length=self.max_length,
                              min_clock_cycles=self.min_clock_cycles,
                              max_clock_cycles=self.max_clock_cycles,
                              next_label=self.next_label
                                           if self.falls_through()
                                           else None,
                              word_symbol_id=self.word_symbol_id,
                             )
        for i, instruction in enumerate(self.instructions):
            instruction.write(self.id, i)

class inst(object):
    r'''Represents a single assembler instruction.
    '''
    def __init__(self, opcode, operand1 = None, operand2 = None,
                       position_info = (None, None, None, None),
                       syntax_error_info = None):
        self.label = None
        self.opcode = opcode
        self.operand1 = operand1
        self.operand2 = operand2
        inst_obj = getattr(asm_opcodes, opcode.upper(), None)
        if inst_obj is None:
            if syntax_error_info:
                raise SyntaxError("unknown opcode: %s" % opcode,
                                  syntax_error_info)
            raise AssertionError("unknown opcode: %s" % opcode)
        self.min_length, self.max_length = inst_obj.length(operand1, operand2)
        self.min_clocks, self.max_clocks = inst_obj.clock_cycles()
        self.end = inst_obj.end()
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
                           min_length=self.min_length,
                           max_length=self.max_length,
                           min_clocks=self.min_clocks,
                           max_clocks=self.max_clocks,
                           end=self.end,
                           line_start=self.line_start,
                           column_start=self.column_start,
                           line_end=self.line_end,
                           column_end=self.column_end,
                          )

def delete(symbol):
    r'''Deletes the block labeled 'symbol'.

    Also deletes the blocks instructions.
    '''
    asm_block_ids = crud.read_column('assembler_blocks', 'id',
                                     word_symbol_id=symbol)
    if asm_block_ids:
        crud.delete('assembler_code', block_id=asm_block_ids)
        crud.delete('assembler_blocks', id=asm_block_ids)
