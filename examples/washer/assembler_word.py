# assembler_word.py

from __future__ import with_statement

from ucc.ast import ast
from ucc.assembler import asm_opcodes
from examples.washer import declaration

class assembler_word(declaration.word):
    def parse_file(self, parser, project_dir):
        with ast.db_transaction() as db_cur:
            ast.delete_word_by_name(self.name)
            instructions = []
            filename = self.get_filename(project_dir)
            with open(filename) as f:
                for i, line in enumerate(f):
                    inst = parse_asm(filename, line, i + 1)
                    if inst: instructions.append(inst)
            root = ast.ast(kind='word_body', word=self.name, str1=filename,
                           *instructions)
            self.word_body_id = root.save(db_cur)
    def compile(self, db_cur, words_by_name):
        db_cur.execute("""select label, word, str1, str2
                            from ast
                           where kind = 'flash'
                             and word_body_id = ?
                       """, (self.word_body_id,))
        return ((self.name, None, None, None),) + \
               tuple(tuple(row) for row in db_cur), (), (), (), ()

def parse_asm(filename, line, lineno):
    r'''Parses one line of assembler code.  Returns ast node or None.
    '''
    stripped_line = line.rstrip()
    comment = stripped_line.find('#')
    if comment >= 0: stripped_line = stripped_line[:comment].rstrip()
    if not stripped_line: return None
    fields = stripped_line.split()
    label = opcode = None
    operands = ()
    if stripped_line[0] == ' ':
        if fields:
            opcode = fields[0]
            operands = ''.join(fields[1:]).split(',')
    else:
        if fields:
            label = fields[0]
            if len(fields) > 1:
                opcode = fields[1]
                operands = ''.join(fields[2:]).split(',')
    if label is None and opcode is None and not operands: return None
    if len(operands) > 2:
        second_comma = line.find(',', line.find(',') + 1) + 1
        raise SyntaxError("no more than 2 operands are allowed",
                          (filename, lineno, second_comma, line))
    str1 = str2 = None
    if operands:
        str1 = operands[0]
    if len(operands) > 1:
        str2 = operands[1]
    int1 = int2 = 0
    if opcode is not None:
        inst_obj = getattr(asm_opcodes, opcode.upper(), None)
        if inst_obj is None:
            if label is not None:
                label_len = len(label)
                no_label = line[label_len:]
                opcode_column = \
                  label_len + len(no_label) - len(no_label.lstrip()) + 1
            else:
                opcode_column = len(line) - len(line.lstrip()) + 1
            raise SyntaxError("unknown opcode: %s" % opcode,
                              (filename, lineno, opcode_column, line))
        int1 = inst_obj.len
        if isinstance(inst_obj.cycles, int): int2 = inst_obj.cycles
        else: int2 = max(inst_obj.cycles)
    column_start = len(stripped_line) - len(stripped_line.lstrip()) + 1
    column_end = len(stripped_line)
    return ast.ast.from_parser((lineno, column_start, lineno, column_end),
                               kind = 'flash', label = label, word = opcode,
                               str1 = str1, str2 = str2,
                               int1 = int1, int2 = int2)

