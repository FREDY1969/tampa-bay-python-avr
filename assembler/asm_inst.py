# asm_inst.py

def bin(s):

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

def gen_R(R):
    if isinstance(R, str):
        assert R.lower().startswith('r')
        n = int(R[1:])
        assert 0 <= n < 32
        return n

def gen_A(A):
    assert 0 <= A < 64
    return A

def gen_q(q):
    assert 0 <= q < 64
    return q

def gen_k(k):
    assert 0 <= k < 4096
    return k

class inst1(object):
    def __init__(self, name, opcode, cycles):
        self.name = name
        self.opcode = opcode
        self.cycles = cycles
    def len(self): return 1

class inst2(inst):
    def len(self): return 2

class reg_direct_1(inst1):
    def gen(self, Rd):
        return (self.opcode | gen_R(Rd),)

class reg_direct_2(inst1):
    def gen(self, Rr, Rd):
        r = gen_R(Rr)
        d = gen_R(Rd)
        r1, rn = r >> 4, r & 0x0F
        d1, dn = d >> 4, d & 0x0F
        return (self.opcode | (r1 << 1 | d1) << 8 | dn << 4 | rn,)

class io_direct(inst1):
    def gen(self, R, A):
        return (self.opcode | (gen_R(R) << 6) | gen_A(A),)

class data_direct(inst2):
    def gen(self, R, addr):
        return (self.opcode | gen_R(R), gen_addr(addr))

class data_indirect_with_disp(inst1):
    def gen(self, R, q):
        return (self.opcode | (gen_R(R) << 6) | gen_q(q),)

class data_indirect(inst1):
    def gen(self):
        return (self.opcode,)

class data_indirect_pre_dec(inst1):
    def gen(self):
        return (self.opcode,)

class data_indirect_post_inc(inst1):
    def gen(self):
        return (self.opcode,)

class no_operand(inst1):
    def gen(self):
        return (self.opcode,)

class direct_program(inst2):
    def gen(self, addr):
        a = gen_prog_addr(addr)
        msb = a >> 16
        lsb = a & 0xFFFF
        return (self.opcode | msb, lsb)

class relative_program(inst1):
    def gen(self, k):
        return (self.opcode | gen_k(k),)

class reg_pair_imm(inst1):
    def gen(self, R, k):
        kv = gen_k(k)
        k2, kn = kv >> 4, kv & 0x0F
        return (self.opcode | ((k2 << 2) | gen_R2(R)) << 4 | kn,)
