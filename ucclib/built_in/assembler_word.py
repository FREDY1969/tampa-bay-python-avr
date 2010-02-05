# assembler_word.py

from __future__ import with_statement

import itertools

from ucc.database import assembler, ast, crud
from ucclib.built_in import declaration

class assembler_word(declaration.word):
    def parse_file(self, parser, debug = 0):
        instructions = []
        filename = self.ww.get_filename()
        with open(filename) as f:
            block = assembler.block(self.ww.symbol.id, 'flash', self.label,
                                    self.ww.get_value('address'))
            blocks = [block]
            for i, line in enumerate(f):
                new_block = parse_asm(self.ww.symbol.id, block, filename, line,
                                      i + 1)
                if new_block:
                    blocks.append(new_block)
                    block.next_block(new_block.label)
                    block = new_block
        with crud.db_transaction():
            assembler.delete(self.ww.symbol)
            for b in blocks: b.write()
        labels_defined = frozenset(b.label for b in blocks)
        labels_used = \
          self.labels_used(
            tuple(itertools.chain.from_iterable(b.instructions
                                                for b in blocks)))
        return labels_used - labels_defined

    def labels_used(self, instructions):
        return frozenset(
            itertools.imap(extract_label,
              itertools.ifilter(is_legal_label,
                itertools.chain(itertools.imap(lambda x: x.operand1,
                                               instructions),
                                itertools.imap(lambda x: x.operand2,
                                               instructions)))))

def extract_label(operand):
    r'''Extract the label out of the operand.

    This is only fed operands that pass is_legal_label.

    >>> extract_label('mom')
    'mom'
    >>> extract_label('hi8(mom)')
    'mom'
    '''
    if '(' not in operand:
        return operand
    return operand[operand.index('(') + 1:operand.index(')')]

def is_legal_label(operand):
    r'''Determines whether operand is a legal label or not.

    >>> is_legal_label('mom')
    True
    >>> is_legal_label('r14')
    False
    >>> is_legal_label('Y+64')
    False
    >>> is_legal_label('X')
    False
    >>> is_legal_label('123')
    False
    >>> is_legal_label('0x23')
    False
    >>> is_legal_label("'x'")
    False
    >>> is_legal_label('"hi mom"')
    False
    >>> is_legal_label('io.spl')
    False
    '''
    if not operand: return False
    operand = operand.lower()
    if len(operand) >= 2 and operand[0] == 'r' and \
       operand[1:].isdigit() and 0 <= int(operand[1:]) <= 31:
        return False
    if len(operand) == 1 and operand in 'xyz' \
       or '+' in operand or '-' in operand:
        return False
    if operand[0].isdigit(): return False
    if operand[0] in "'\"": return False
    if operand.startswith('io.'): return False
    return True

def parse_asm(word_symbol_id, block, filename, line, lineno):
    r'''Parses one line of assembler code and appends it block.
    
    If the line has a label, it creates a new block, appends the instruction,
    and returns it.
    Otherwise it returns None.
    '''
    stripped_line = line.rstrip()
    comment = stripped_line.find('#')
    if comment >= 0: stripped_line = stripped_line[:comment].rstrip()
    if not stripped_line: return None
    fields = stripped_line.split()
    label = opcode = None
    operands = ()
    ans = None
    if stripped_line[0] == ' ':
        if fields:
            opcode = fields[0]
            operands = ''.join(fields[1:]).split(',')
    else:
        if fields:
            label = fields[0]
            ans = block = assembler.block(word_symbol_id, 'flash', label)
            if len(fields) > 1:
                opcode = fields[1]
                operands = ''.join(fields[2:]).split(',')
    if len(operands) == 1 and not operands[0]: operands = ()
    if opcode is None and not operands: return ans
    if len(operands) > 2:
        second_comma = line.find(',', line.find(',') + 1) + 1
        raise SyntaxError("no more than 2 operands are allowed",
                          (filename, lineno, second_comma, line))
    operand1 = operand2 = None
    if operands:
        operand1 = operands[0]
    if len(operands) > 1:
        operand2 = operands[1]
    length = clocks = 0
    syntax_error_info = None
    if opcode is not None:
        if label is not None:
            label_len = len(label)
            no_label = line[label_len:]
            opcode_column = \
              label_len + len(no_label) - len(no_label.lstrip()) + 1
        else:
            opcode_column = len(line) - len(line.lstrip()) + 1
        syntax_error_info = (filename, lineno, opcode_column, line)
    column_start = len(stripped_line) - len(stripped_line.lstrip()) + 1
    column_end = len(stripped_line)
    block.append_inst(opcode, operand1, operand2,
                      (lineno, column_start, lineno, column_end),
                      syntax_error_info=syntax_error_info)
    return ans

