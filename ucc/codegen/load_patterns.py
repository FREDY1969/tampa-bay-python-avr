# load_patterns.py

import sys

if __name__ == "__main__":
    from doctest_tools import setpath
    #print("sys.path[0:2]", sys.path[0:2], file=sys.stderr)
    setpath.setpath(__file__, remove_first=True)
    #print("sys.path[0:2]", sys.path[0:2], file=sys.stderr)

from ucc.database import crud

# SyntaxError params (filename, lineno, column, line)

Filename = 'test file'
Line = 'test line'
Lineno = 1

def load(database_filename, pattern_filename):
    global Line, Lineno, Filename
    Filename = pattern_filename
    with crud.db_connection(database_filename, False, False):
        with open(pattern_filename) as f:
            last_operator = None
            Line = f.readline()
            while Line:
                #print("got Line", repr(Line))
                if '#' in Line:
                    Line = Line[:Line.index('#')]
                Line = Line.strip()
                if not Line:
                    Lineno += 1
                    Line = f.readline()
                else:
                    with crud.db_transaction():
                        components = Line.split(',')
                        if not (3 <= len(components) <= 4):
                            raise SyntaxError("syntax error",
                                              (Filename, Lineno, None, Line))

                        if len(components) == 3:
                            components.append('')

                        operator = components[0].strip()
                        #print("operator", operator)
                        if operator != last_operator:
                            last_operator = operator
                            preference = 1

                        l_opcode, l_min, l_max, l_multi_use, \
                          l_reg_class, l_num_regs, l_trashes, l_delink = \
                            parse_half(components[1])

                        r_opcode, r_min, r_max, r_multi_use, \
                          r_reg_class, r_num_regs, r_trashes, r_delink = \
                            parse_half(components[2])

                        code_seq_id = crud.insert('code_seq',
                                        left_reg_class=l_reg_class,
                                        left_num_registers=l_num_regs,
                                        left_trashes=l_trashes,
                                        left_delink=l_delink,
                                        right_reg_class=r_reg_class,
                                        right_num_registers=r_num_regs,
                                        right_trashes=r_trashes,
                                        right_delink=r_delink)

                        pattern_id = crud.insert('pattern',
                                        preference=preference,
                                        code_seq_id=code_seq_id,
                                        operator=components[0].strip(),
                                        left_opcode=l_opcode,
                                        left_const_min=l_min,
                                        left_const_max=l_max,
                                        left_multi_use=l_multi_use,
                                        right_opcode=r_opcode,
                                        right_const_min=r_min,
                                        right_const_max=r_max,
                                        right_multi_use=r_multi_use)

                        preference += 1

                        for reg_class, number in reg_req(components[3]):
                            crud.insert('reg_requirements',
                                        code_seq_id=code_seq_id,
                                        reg_class=reg_class,
                                        num_needed=number)

                        for i, (label, opcode, operand1, operand2) \
                         in enumerate(read_insts(f)):
                            crud.insert('code',
                                        code_seq_id=code_seq_id,
                                        inst_order=i + 1,
                                        opcode=opcode,
                                        operand1=operand1,
                                        operand2=operand2)

def parse_half(text):
    r'''Parse argument pattern.

    Returns 8 values:
        opcode, min, max, multi_use, reg_class, num_regs, trashes, delink

        >>> parse_half("int 0- =single")
        ('int', 0, None, None, 'single', 1, False, False)
        >>> parse_half("int -63 =single")
        ('int', None, 63, None, 'single', 1, False, False)
        >>> parse_half("int 0-63 =single")
        ('int', 0, 63, None, 'single', 1, False, False)
        >>> parse_half("any")
        (None, None, None, None, None, None, False, False)
        >>> parse_half(" any = 2*immed trashed ")
        (None, None, None, None, 'immed', 2, True, False)
        >>> parse_half(" single_use = 2*immed trashed ")
        (None, None, None, False, 'immed', 2, True, False)
        >>> parse_half(" multi_use = 2*immed trashed ")
        (None, None, None, True, 'immed', 2, True, False)
        >>> parse_half("int =2*single delink")
        ('int', None, None, None, 'single', 2, False, True)
    '''

    pattern_use = text.split('=')
    if len(pattern_use) == 1:
        pattern, use = pattern_use[0], None
    elif len(pattern_use) == 2:
        pattern, use = pattern_use
    else:
        raise SyntaxError("too many '=' in one operand",
                          (Filename, Lineno, None, Line))

    opcode = min = max = multi_use = None
    pattern_args = pattern.split()
    if pattern_args[0] != 'any':
        if pattern_args[0] == 'single_use':
            multi_use = False
        elif pattern_args[0] == 'multi_use':
            multi_use = True
        else:
            opcode = pattern_args[0]
    if len(pattern_args) > 1:
        min_arg, max_arg = pattern_args[1].split('-')
        if min_arg: min = int(min_arg)
        if max_arg: max = int(max_arg)

    num_regs = 1
    reg_class = num_regs = None
    trashes = delink = False
    if use:
        use_args = use.split()
        reg_specs = use_args[0].split('*')
        if len(reg_specs) == 1:
            reg_class = reg_specs[0].strip()
            num_regs = 1
        elif len(reg_specs) == 2:
            num_regs = int(reg_specs[0])
            reg_class = reg_specs[1].strip()
        else:
            raise SyntaxError("invalid register spec",
                              (Filename, Lineno, None, Line))
        for option in use_args[1:]:
            option = option.strip()
            if option == 'trashed': trashes = True
            elif option == 'delink': delink = True
            else:
                raise SyntaxError("invalid option on register spec",
                                  (Filename, Lineno, None, Line))

    return opcode, min, max, multi_use, reg_class, num_regs, trashes, delink

def reg_req(text):
    r'''Generate reg_class, number tuples.
    '''
    return
    yield a, b

def read_insts(f):
    r'''Generate label, opcode, operand1, operand2.

    Keep Line and Lineno up to date.

        >>> from io import StringIO
        >>> f = StringIO("""
        ...        ADD  {operand1}, lo({foobar})
        ...   foo: SUB  {operand1}
        ...   bar:
        ...        NOOP
        ... """)
        >>> for ans in read_insts(f):
        ...     print(ans)
        (None, 'ADD', '{operand1}', 'lo({foobar})')
        ('foo', 'SUB', '{operand1}', None)
        ('bar', None, None, None)
        (None, 'NOOP', None, None)
    '''

    def read():
        global Line, Lineno

        Line = f.readline()
        Lineno += 1
        if '#' in Line:
            return Line[:Line.index('#')] + '\n'
        return Line

    line = read()
    while line and (not line.strip() or line[0] == ' '):
        line = line.rstrip()
        if line:
            operands = line.strip().split(',')
            leading = operands[0].strip().split()
            #print("leading", leading, file=sys.stderr)
            if len(operands) == 2:
                operand2 = operands[1].strip()
            elif len(operands) > 2:
                raise SyntaxError("too many operands",
                                  (Filename, Lineno, None, Line))
            else:
                operand2 = None
            if leading[0].endswith(':'):
                label = leading[0].strip()[:-1]
                del leading[0]
            else:
                label = None
            if len(leading) == 2:
                yield label, leading[0].strip(), leading[1].strip(), operand2
            elif len(leading) == 1:
                if operand2:
                    raise SyntaxError("missing opcode",
                                      (Filename, Lineno, None, Line))
                yield label, leading[0].strip(), None, None
            elif len(leading) == 0:
                if operand2 or not label:
                    raise SyntaxError("missing opcode",
                                      (Filename, Lineno, None, Line))
                else:
                    yield label, None, None, None
            else:
                raise SyntaxError("missing comma",
                                  (Filename, Lineno, None, Line))
        line = read()

if __name__ == "__main__":
    load(sys.argv[1], sys.argv[2])
