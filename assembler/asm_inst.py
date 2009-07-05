# asm_inst.py

def format(s, **args):
    assert len(s) % 16 == 0
    operands = {}
    # Gather the operands and count the number of bits in each.
    for x in s:
        if x not in ('0', '1'):
            operands.setdefault(x, 0) += 1
    values = {}
    for name, num_bits in operands:
        values[name] = convert[name](args[name], num_bits)
    ans = 0
    for i, x in enumerate(s[::-1]):
        if x == '0': pass
        elif x == '1': ans |= 1 << i
        else:
            ans |= (values[x] & 1) << i
            values[x] >>= 1
    return ans

class inst1(object):
    def __init__(self, name, opcode, cycles, **notes):
        self.name = name
        self.opcode = opcode.replace(' ', '')
        s = set(self.opcode)
        s.discard('0')
        s.discard('1')
        self.operands = dict((operand, opcode.count(operand)) for operand in s)
        self.cycles = cycles
        self.notes = notes
    def len(self): return 1

class inst2(inst1):
    def len(self): return 2

