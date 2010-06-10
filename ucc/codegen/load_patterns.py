# load_patterns.py

r'''Loads a "patterns" file into a machine database.

The patterns file uses '#' to EOL as comments and blank lines are ignored.

Each pattern has one line with 1 to 3 comma separated components:

    operator
        -- this is simply the name of the triples.operator followed by a colon
    parameter
        -- comma separated parameter specification in parameter_num order
           followed by a colon
    reg_requirement
        -- comma separated reg_requirements for code sequence (in addition to
           parameter registers).

The parameter specifications look like:

    pattern [= use]

Pattern is:

    'ans'
  | [last_use|reused] [operator [[min]-[max]]]

Use is:

    ([<num_regs_used_from_param> *] reg_class [output|trashed] | delink)

Reg_requirement is:

    [<num_regs_used_from_param> *] reg_class
'''

import sys
import re

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
                        components = Line.split(':')
                        if len(components) < 1:
                            raise SyntaxError("missing ':'",
                                              (Filename, Lineno, None, Line))
                        elif len(components) > 3:
                            raise SyntaxError("too many ':' components",
                                              (Filename, Lineno, None, Line))

                        operator = components[0].strip()
                        #print("operator", operator)
                        if operator != last_operator:
                            last_operator = operator
                            preference = 1

                        code_seq_id = crud.insert('code_seq',
                                        preference=preference,
                                        operator=operator)

                        preference += 1

                        if len(components) > 1 and components[1].strip():
                            for i, component \
                             in enumerate(components[1].split(',')):
                                opcode, min, max, last_use, \
                                  reg_class, num_regs, \
                                  trashes, delink, output = \
                                    parse_component(component)

                                if opcode != 'ans':
                                    crud.insert('code_seq_parameter',
                                                code_seq_id=code_seq_id,
                                                parameter_num=i + 1,
                                                opcode=opcode,
                                                const_min=min,
                                                const_max=max,
                                                last_use=last_use,
                                                reg_class=reg_class,
                                                num_registers=num_regs,
                                                trashes=trashes,
                                                delink=delink)

                                    if output:
                                        crud.update('code_seq',
                                                    {'id': code_seq_id},
                                                    output_reg_class=reg_class,
                                                    num_output=num_regs,
                                                    from_param_num=i + 1)
                                else:
                                    crud.update('code_seq',
                                                {'id': code_seq_id},
                                                output_reg_class=reg_class,
                                                num_output=num_regs)

                        if len(components) > 2 and components[2].strip():
                            for req in components[2].split(','):
                                reg_class, number = reg_req(req.strip())
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

Pattern_re = re.compile(r'''
      \s*
      (?: (?P<delink> delink)
        | (?: (?P<num_regs> \d+) \s* \* \s*)?
          (?P<reg_class>\w+)
          (?: \s+
              (?: (?P<trashed> trashed)
                | (?P<output> output)
              )
          )?
      )
    ''',
    re.VERBOSE)

def parse_component(text):
    r'''Parse argument pattern.

    Returns 8 values:
        opcode, min, max, last_use, reg_class, num_regs, trashes, delink, output

        >>> parse_component("int 0- =single")
        ('int', 0, None, None, 'single', 1, False, False, False)
        >>> parse_component("int -63 =single")
        ('int', None, 63, None, 'single', 1, False, False, False)
        >>> parse_component("int 0-63 =single")
        ('int', 0, 63, None, 'single', 1, False, False, False)
        >>> parse_component("any")
        (None, None, None, None, None, None, False, False, False)
        >>> parse_component(" any = 2*immed trashed ")
        (None, None, None, None, 'immed', 2, True, False, False)
        >>> parse_component(" last_use = 2*immed output ")
        (None, None, None, 1, 'immed', 2, True, False, True)
        >>> parse_component(" reused = 2*immed trashed ")
        (None, None, None, 0, 'immed', 2, True, False, False)
        >>> parse_component("int =delink")
        ('int', None, None, None, None, None, False, True, False)
    '''

    pattern_use = text.split('=')
    if len(pattern_use) == 1:
        pattern, use = pattern_use[0], ''
    elif len(pattern_use) == 2:
        pattern, use = pattern_use
    else:
        raise SyntaxError("too many '=' in one operand",
                          (Filename, Lineno, None, Line))

    opcode = min = max = last_use = None
    pattern_args = pattern.split()
    if pattern_args[0] == 'ans':
        if len(pattern_args) > 1:
            raise SyntaxError("no min/max allowed on ans",
                              (Filename, Lineno, None, Line))
        opcode = 'ans'
    elif pattern_args[0] == 'last_use':
        last_use = 1
        pattern_args = pattern_args[1:]
    elif pattern_args[0] == 'reused':
        last_use = 0
        pattern_args = pattern_args[1:]
    if pattern_args and pattern_args[0] != 'any':
        opcode = pattern_args[0]
    if len(pattern_args) > 1:
        min_arg, max_arg = pattern_args[1].split('-')
        if min_arg: min = int(min_arg)
        if max_arg: max = int(max_arg)
    if len(pattern_args) > 2:
        raise SyntaxError("too many pattern args",
                          (Filename, Lineno, None, Line))

    reg_class = num_regs = None
    trashes = delink = output = False
    if use.strip():
        m = Pattern_re.match(use)
        if not m:
            raise SyntaxError("invalid register spec",
                              (Filename, Lineno, None, Line))
        if m.group('delink'):
            delink = True
        else:
            num_regs = int(m.group('num_regs') or 1)
            reg_class = m.group('reg_class')
            if m.group('trashed'):
                trashes = True
            if m.group('output'):
                trashes = True
                output = True

    if opcode == 'ans' and reg_class is None:
        raise SyntaxError("ans needs reg_class", (Filename, Lineno, None, Line))

    return opcode, min, max, last_use, reg_class, num_regs, trashes, delink, \
           output


Reg_req_re = re.compile(
    r'\s* (?: (?P<num_regs> \d+) \s* \* \s*)? (?P<reg_class>\w+)',
    re.VERBOSE)

def reg_req(text):
    r'''Returns reg_class, number required.
    '''
    m = Reg_req_re.match(text)
    return m.group('reg_class'), int(m.group('num_regs') or 1)

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
