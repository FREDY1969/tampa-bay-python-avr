# asm_inst.py

bits = {
    0x01: 0,
    0x02: 1,
    0x04: 2,
    0x08: 3,
    0x10: 4,
    0x20: 5,
    0x40: 6,
    0x80: 7,
}

convert = {

    'A':        # I/O register number (0-31) or (0-63)
        lambda arg, num_bits, note: int(arg),
    'b':        # bit number (0-7)
        lambda arg, num_bits, note: \
          bits[int(arg)] if arg.lower().startswith('0x') else int(arg),
    'd':        # dest register (0,31), (0,30,2), (16,31), (16,23), (24,30,2)
        lambda arg, num_bits, note: \
          int(arg[1:]) if note is None else \
          int(arg[1:])*2+note[0] if note[1] == 30 else \
          int(arg[1:])+note[0],
    'k':        # addr (data or flash memory), offset in flash
        lambda arg, num_bits, note: int(arg),
    'K':        # an immediate number
        lambda arg, num_bits, note: int(arg),
    'p':        # inc/dec code: 00=no inc/dec, 01 post inc, 10 pre dec
        lambda arg, num_bits, note: \
          2 if arg[0] == '-' else \
          1 if arg[-1] == '+' else \
          0,
    'q':        # offset from Y or Z
        lambda arg, num_bits, note: \
          int(arg[arg.index('+')+1:]) if '+' in arg else 0,
    'r':        # source register (0,31), (0,30,2), (16,31), (16,23)
        lambda arg, num_bits, note: \
          int(arg[1:]) if note is None else \
          int(arg[1:])*2+note[0] if note[1] == 30 else \
          int(arg[1:])+note[0],
    's':        # bit# in status register (SREG) (0-7)
        lambda arg, num_bits, note: \
          bits[int(arg)] if arg.lower().startswith('0x') else \
          int(arg),
    'x':        # X/Y/Z, 11=X, 10=Y, 00=Z
        lambda arg, num_bits, note: \
          3 if 'x' in arg.lower() else \
          2 if 'y' in arg.lower() else \
          0 if 'z' in arg.lower() else \
          invalid_operand(arg, "X, Y or Z"),
    'y':        # Y/Z, 1=Y, 0=Z
        lambda arg, num_bits, note: \
          1 if 'y' in arg.lower() else \
          0 if 'z' in arg.lower() else \
          invalid_operand(arg, "Y or Z"),

}

def invalid_operand(arg, expected):
    raise SyntaxError("expected %s, got %s" % (expected, arg))

def format(s, operands, notes, **args):
    r'''
        >>> hex(format('0000 0000 0000 0000'.replace(' ',''), {}, {}))
        '0x0'
        >>> hex(format('1111 1111 1111 1111'.replace(' ',''), {}, {}))
        '0xffff'
        >>> hex(format('1111 1111 1111 1111 1111 1111 1111 1111'
        ...              .replace(' ',''),
        ...            {}, {}))
        '0xffffffffL'
        >>> hex(format('0000 11rd dddd rrrr'.replace(' ',''),
        ...            {'r': 5, 'd': 5}, {}, r='r12', d='r4'))
        '0xc4c'
    '''
    assert len(s) % 16 == 0
    values = dict((name, convert[name](args[name], num_bits, notes.get(name)))
                  for name, num_bits in operands.iteritems())
    ans = 0
    for i, x in enumerate(s[::-1]):
        if x == '0': pass
        elif x == '1': ans |= 1 << i
        else:
            ans |= (values[x] & 1) << i
            values[x] >>= 1
    return ans

class inst1(object):
    len = 1
    def __init__(self, name, opcode, cycles, **notes):
        self.name = name
        self.opcode = opcode.replace(' ', '')
        s = set(self.opcode)
        s.discard('0')
        s.discard('1')
        self.operands = dict((operand, opcode.count(operand)) for operand in s)
        self.cycles = cycles
        self.notes = notes

class inst2(inst1):
    len = 2

