# asm_inst.py

import itertools

from ucc.assembler import io

Bits = {
    0x01: 0,
    0x02: 1,
    0x04: 2,
    0x08: 3,
    0x10: 4,
    0x20: 5,
    0x40: 6,
    0x80: 7,
}

def convert_reg(arg, num_bits, note, labels, address):
    r'''Convert register operand to number.

    'address' is in bytes.

    >>> convert_reg('r0', 5, None, None, None)
    0
    >>> convert_reg('r31', 5, None, None, None)
    31
    >>> convert_reg('r32', 5, None, None, None)
    Traceback (most recent call last):
        ...
    AssertionError: r32: illegal register
    >>> convert_reg('r31', 5, 'd', None, None)
    31
    >>> convert_reg('r16', 4, None, None, None)
    Traceback (most recent call last):
        ...
    AssertionError: r16: illegal register
    >>> convert_reg('r16', 4, (16, 31), None, None)
    0
    >>> convert_reg('r31', 4, (16, 31), None, None)
    15
    >>> convert_reg('r15', 4, (16, 31), None, None)
    Traceback (most recent call last):
        ...
    AssertionError: r15: illegal register
    >>> convert_reg('r15', 3, (16, 30), None, None)
    Traceback (most recent call last):
        ...
    AssertionError: r15: illegal register
    >>> convert_reg('r16', 3, (16, 30), None, None)
    0
    >>> convert_reg('r30', 3, (16, 30), None, None)
    7
    >>> convert_reg('r31', 3, (16, 30), None, None)
    Traceback (most recent call last):
        ...
    AssertionError: r31: illegal register
    >>> convert_reg('r17', 3, (16, 30), None, None)
    Traceback (most recent call last):
        ...
    AssertionError: r17: illegal register
    >>> convert_reg('r23', 2, (24, 30), None, None)
    Traceback (most recent call last):
        ...
    AssertionError: r23: illegal register
    >>> convert_reg('r24', 2, (24, 30), None, None)
    0
    >>> convert_reg('r30', 2, (24, 30), None, None)
    3
    >>> convert_reg('r31', 2, (24, 30), None, None)
    Traceback (most recent call last):
        ...
    AssertionError: r31: illegal register
    >>> convert_reg('r25', 2, (24, 30), None, None)
    Traceback (most recent call last):
        ...
    AssertionError: r25: illegal register
    '''
    assert arg[0].lower() == 'r', "%s: illegal register" % arg
    max = 2**num_bits
    n = int(arg[1:])
    if note is None or note == 'd':
        assert n < max, "%s: illegal register" % arg
        return n
    low, high = note
    assert low <= n <= high, "%s: illegal register" % arg
    if (high - low + 1) == max:
        return n - low
    if (high - low + 2) == 2*max:
        assert low <= n <= high, "%s: illegal register" % arg
        assert n % 2 == 0, "%s: illegal register" % arg
        return (n - low) // 2
    raise AssertionError("internal error: convert_reg: bad args: %r, %r, %r" %
                         (arg, num_bits, note))

Convert = {

    'A':        # I/O register number (0-31) or (0-63)
        lambda arg, num_bits, note, labels, address: \
          int(arg, 0) if arg.isdigit() or arg.lower().startswith('0x') \
                      else eval(arg, globals(), labels) - 0x20,
    'b':        # bit number (0-7)
        lambda arg, num_bits, note, labels, address: \
          Bits[int(arg, 0)] if arg.lower().startswith('0x') else int(arg, 0),
    'd':        # dest register (0,31), (0,30,2), (16,31), (16,23), (24,30,2)
        convert_reg,
    'k':        # addr (data or flash memory), offset in flash
        lambda arg, num_bits, note, labels, address: \
          eval(arg, globals(), labels) // 2 
            if num_bits > 16
            else (eval(arg, globals(), labels) - address) // 2,
    'K':        # an immediate number
        lambda arg, num_bits, note, labels, address: \
          eval(arg, globals(), labels),
    'p':        # inc/dec code: 00=no inc/dec, 01 post inc, 10 pre dec
        lambda arg, num_bits, note, labels, address: \
          2 if arg[0] == '-' else \
          1 if arg[-1] == '+' else \
          0,
    'q':        # offset from Y or Z
        lambda arg, num_bits, note, labels, address: \
          int(arg[arg.index('+')+1:], 0) if '+' in arg else 0,
    'r':        # source register (0,31), (0,30,2), (16,31), (16,23)
        convert_reg,
    's':        # bit# in status register (SREG) (0-7)
        lambda arg, num_bits, note, labels, address: \
          Bits[int(arg, 0)] if arg.lower().startswith('0x') else \
          int(arg, 0),
    'x':        # X/Y/Z, 11=X, 10=Y, 00=Z
        lambda arg, num_bits, note, labels, address: \
          3 if 'x' in arg.lower() else \
          2 if 'y' in arg.lower() else \
          0 if 'z' in arg.lower() else \
          invalid_operand(arg, "X, Y or Z"),
    'y':        # Y/Z, 1=Y, 0=Z
        lambda arg, num_bits, note, labels, address: \
          1 if 'y' in arg.lower() else \
          0 if 'z' in arg.lower() else \
          invalid_operand(arg, "Y or Z"),

}

def lookup(name, where, notes):
    try:
        return where[name]
    except KeyError:
        return where[notes[name]]

def hi8(n):
    r'''Returns the high (most significant) 8 bits of a 16 bit number.

    >>> hex(hi8(0x1234))
    '0x12'
    >>> hex(hi8(0xFEDC))
    '0xfe'
    '''
    return (n >> 8) & 0xff

def lo8(n):
    r'''Returns the low (least significant) 8 bits of a 16 bit number.

    >>> hex(lo8(0x1234))
    '0x34'
    '''
    return n & 0xff

Order = {

    'A': 20,      # I/O register number (0-31) or (0-63)
    'b': 80,      # bit number (0-7)
    'd': 10,      # dest register (0,31), (0,30,2), (16,31), (16,23), (24,30,2)
    'k': 50,      # addr (data or flash memory), offset in flash
    'K': 60,      # an immediate number
    'p': 30,      # inc/dec code: 00=no inc/dec, 01 post inc, 10 pre dec
    'q': 30,      # offset from Y or Z
    'r': 70,      # source register (0,31), (0,30,2), (16,31), (16,23)
    's': 40,      # bit# in status register (SREG) (0-7)
    'x': 30,      # X/Y/Z, 11=X, 10=Y, 00=Z
    'y': 30,      # Y/Z, 1=Y, 0=Z

}

def invalid_operand(arg, expected):
    raise SyntaxError("expected %s, got %s" % (expected, arg))

def format(s, operands, notes, args, labels, next_address):
    r'''
        >>> hex(format('0000 0000 0000 0000'.replace(' ',''),
        ...            {}, {}, {}, {}, 0))
        '0x0'
        >>> hex(format('1111 1111 1111 1111'.replace(' ',''),
        ...            {}, {}, {}, {}, 0))
        '0xffff'
        >>> hex(format('1111 1111 1111 1111 1111 1111 1111 1111'
        ...              .replace(' ',''),
        ...            {}, {}, {}, {}, 0))
        '0xffffffffL'
        >>> hex(format('0000 11rd dddd rrrr'.replace(' ',''),
        ...            {'r': 5, 'd': 5}, {}, {'r':'r12', 'd':'r4'},
        ...            {}, 0))
        '0xc4c'
        >>> hex(format('1111 1111 1111 1111 kkkk kkkk kkkk kkkk'
        ...              .replace(' ',''),
        ...            {'k': 16}, {}, {'k':'foo'}, {'foo': 0x1234}, 0x1000))
        '0xffff011aL'
        >>> hex(format('0000 1100 kkkk kkkk'.replace(' ',''),
        ...            {'k': 8}, {}, {'k':'foo'},
        ...            {'foo': 0x1234}, 0x1280))
        '0xcda'
        >>> hex(format('0000 1100 KKKK KKKK'.replace(' ',''),
        ...            {'K': 8}, {}, {'K':'hi8(foo)'},
        ...            {'foo': 0x1234}, 0x1280))
        '0xc12'
        >>> hex(format('0000 1100 KKKK KKKK'.replace(' ',''),
        ...            {'K': 8}, {}, {'K':'lo8(foo)'},
        ...            {'foo': 0x1234}, 0x1280))
        '0xc34'
    '''
    assert len(s) % 16 == 0
    values = dict((name, lookup(name, Convert, notes)
                           (args[name], num_bits, notes.get(name), labels,
                            next_address))
                  for name, num_bits in operands.iteritems())
    ans = 0
    for i, x in enumerate(s[::-1]):
        if x == '0': pass
        elif x == '1': ans |= 1 << i
        else:
            ans |= (values[x] & 1) << i
            values[x] >>= 1
    return ans

def operand_order(operands, notes):
    r'''Returns a tuple of operand tuples for each instruction operand.

    >>> operand_order(('p', 'd', 'q', 'x'), {})
    (('d',), ('p', 'q', 'x'))
    >>> operand_order(('p', 'r', 'q', 'x'), {})
    (('p', 'q', 'x'), ('r',))
    >>> operand_order(('d', 'D'), {'D':'d'})
    (('d', 'D'),)
    '''
    return tuple(
      itertools.imap(lambda x: tuple(itertools.imap(lambda x: x[1], x[1])),
                     itertools.groupby(
                       sorted(itertools.imap(
                                lambda x: (lookup(x, Order, notes), x),
                                operands),
                              key = lambda x: x[0]),
                       key = lambda x: x[0])))

class inst1(object):
    def __init__(self, name, opcode, cycles, **notes):
        self.name = name
        self.opcode = opcode.replace(' ', '')
        s = set(self.opcode)
        s.discard('0')
        s.discard('1')
        self.operands = dict((operand, opcode.count(operand)) for operand in s)
        self.operand_codes = operand_order(self.operands.keys(), notes)
        self.cycles = cycles
        self.notes = notes

    def length(self, op1, op2): return 2

    def make_args(self, op1, op2):
        if len(self.operand_codes) == 0:
            assert op1 is None and op2 is None, \
                   "%s instruction does not take operands" % self.name
            return {}
        if len(self.operand_codes) == 1:
            assert op1 is not None, \
                   "%s instruction requires one operand" % self.name
            assert op2 is None, \
                   "%s instruction only takes one operand" % self.name
            return dict(itertools.izip(self.operand_codes[0],
                                       itertools.repeat(op1)))
        assert len(self.operand_codes) == 2, \
               "internal error: %s illegal instruction format specification" % \
               self.name
        return dict(itertools.chain(
                      itertools.izip(self.operand_codes[0],
                                     itertools.repeat(op1)),
                      itertools.izip(self.operand_codes[1],
                                     itertools.repeat(op2))))

    def assemble(self, op1, op2, labels, address):
        bits = format(self.opcode, self.operands, self.notes,
                      self.make_args(op1, op2),
                      labels,
                      address + self.length(op1, op2))
        yield bits & 0xff
        yield bits >> 8


class inst2(inst1):
    def length(self, op1, op2): return 4

    def assemble(self, op1, op2, labels, address):
        bits = format(self.opcode, self.operands, self.notes,
                      self.make_args(op1, op2), labels, address)
        yield int((bits >> 16) & 0xff)
        yield int((bits >> 24) & 0xff)
        yield int(bits & 0xff)
        yield int((bits >> 8) & 0xff)


class bytes(inst1):
    def __init__(self): pass

    def length(self, op1, op2):
        if op1[0] in "\"'":
            return len(eval(op1))
        else:
            assert len(op1) % 2 == 0, \
                   "bytes opcode must have an even number of hex digits"
            return len(op1) // 2

    def assemble(self, op1, op2, labels, address):
        if op1[0] in "\"'":
            for c in eval(op1):
                yield ord(c)
        else:
            for i in range(0, len(op1), 2):
                yield int(op1[i:i+2], 16)


class int8(bytes):
    def length(self, op1, op2):
        return 1

    def assemble(self, op1, op2, labels, address):
        yield int(op1, 0)


class int16(bytes):
    def length(self, op1, op2):
        return 2

    def assemble(self, op1, op2, labels, address):
        n = int(op1, 0)
        yield n & 0xff
        yield (n >> 8) & 0xff


class int32(bytes):
    def length(self, op1, op2):
        return 4

    def assemble(self, op1, op2, labels, address):
        n = int(op1, 0)
        yield n & 0xff
        yield (n >> 8) & 0xff
        yield (n >> 16) & 0xff
        yield (n >> 24) & 0xff


class zeroes(bytes):
    def length(self, op1, op2):
        return int(op1, 0)

    def assemble(self, op1, op2, labels, address):
        return ()
