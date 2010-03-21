# word.py

'''
    There are two kinds of functions:

        1.  Deferrable
        2.  Non-deferrable

    The frame for deferrable functions is allocated statically, so they are
    not reentrant.  A deferrable function may only be called by another
    deferrable function; but a deferrable function may call either kind of
    function.

    The frame for a non-deferrable function is allocated on the stack (like
    normal languages).  So they are reentrant and may be recursive.  A
    non-deferrable function may only call other non-deferrable functions.

    Threads hold argument stacks that are only used to pass arguments to both
    types of functions.  Thus, these stacks are smaller than full function
    activation record stacks.

    A Frame looks like:

           FP
           |
           V
    +------+--+---+------ ... +----+----+----+----+
    | my   | args | local ... | calling | calling |
    | word | addr | vars      | FP      | PC      |
    +------+--+---+------ ... +----+----+----+----+

    The args are in reverse order (first arg last).

'''

PC = None         # Processor PC
FP = None         # FP of currently running function
TSP = None        # Thread SP (grows down)
PSP = None        # Processor SP

Data = [0] * (2 * 1024)
Data_end = 0
Stack_size = 256  # Just a wild guess
Data_limit = (2 * 1024) - Stack_size

Flash = [0] * (15 * 1024)
Flash_end = 0

Words = {}
Wtable = []
Num_words = 0

def push_flash1(x):
    if Flash_end >= 15 * 1024:
        raise MemoryError("Out of Flash space")
    Flash[Flash_end] = x
    Flash_end += 1

def push_flash2(x):
    push_flash1(x & 0xff)
    push_flash1(x >> 8)

def push1(x):
    if SP < Data_end:
        raise MemoryError("Processor stack overflow")
    SP -= 1
    Data[SP] = x

def push2(x):
    push1(x >> 8)
    push1(x & 0xff)

def pop1():
    if SP >= 2 * 1024:
        raise SystemError("Processor stack underflow")
    ans = Data[SP]
    SP += 1
    return ans

def pop2():
    return pop1() + 256 * pop1()

def tpush1(x):
    if TSP < 0: # FIX
        raise MemoryError("Thread stack overflow")
    TSP -= 1
    Data[TSP] = x

def tpush2(x):
    tpush1(x >> 8)
    tpush1(x & 0xff)

def tpop1():
    if TSP >= (2 * 1024): # FIX
        raise SystemError("Thread stack underflow")
    ans = Data[TSP]
    TSP += 1
    return ans

def tpop2():
    return tpop1() + 256 * tpop1()

def get_data2(addr):
    return Data[addr] + 256 * Data[addr + 1]

def put_data2(data, addr):
    Data[addr] = data & 0xff
    Data[addr + 1] = data >> 8

def next():
    word = Wtable[Flash[PC]]
    PC += 1
    word.run()

def run():
    while True: next()

# Precedence values (bigger numbers have higher precedence, 0 == not allowed):
Left_fun, Right_fun = 0, 10                     # unary
Left_plus, Right_plus = 20, 30                  # left assoc
Left_minus, Right_minus = 20, 30                # left assoc
Left_divide, Right_divide = 50, 40              # right assoc
Left_multiply, Right_multiply = 60, 70          # left assoc
Left_negate, Right_negate = 0, 30               # unary

class DupWord(Exception): pass

class non_deferrable_word:
    def __init__(self, name):
        self.name = name
        self.min_args_len = 0
        self.max_args_len = 0
        self.ret_domain = None
        self.left_prec = Left_fun
        self.right_prec = Right_fun
        self.frame_size = 7
        self.stack_size = 0
        if name in Words:
            raise DupWord(name)
        if Num_words >= 256:
            raise MemoryError("Word table full")
        self.word_index = Num_words
        Num_words += 1
        Wtable[self.word_index] = self
        Words[name] = self
    def finish_def(self): pass
    def compile_value(self, compiler, prev_domain = None):
        r''' Returns a domain.
             At run time, returns a value in this domain.
        '''
        if prev_domain:
            raise SyntaxError("word {!r} acts like unary operator, "
                              "but no compile_value declared on it for that"
                                .format(self.name),
                              compiler.syntaxerror_params())
        compiler.compile_params(self)
        compiler.push(self.word_index)
        return self.ret_domain
    def compile_lvalue(self, compiler):
        r''' Returns a domain.
             At run time, returns a pointer to a value in this domain.
             This pointer always points into the Data (SRAM) area.
        '''
        raise SyntaxError("illegal lvalue: {!r}".format(self.name),
                          compiler.syntaxerror_params())
    def compile_cond(self, compiler, fall_through_true = True):
        r''' Returns a tuple of two sequences.
             The first sequence are flash addresses to be patched to the
             address to jump to for the true case.
             The second sequence are flash addresses to be patched to the
             address to jump to for the false case.
        '''
        self.compile_value(compiler)
        if fall_through_true:
            compiler.push(jf)
            return (), (compiler.addr(),)
        else:
            compiler.push(jt)
            return (compiler.addr(),), ()
    def compile_decl(self, compiler):
        r''' Doesn't return anything. '''
        raise SyntaxError("illegal declaration: {}".format(self.name),
                          compiler.syntaxerror_params())
    def run(self):
        if (self.max_args_len > self.min_args_len):
            arg_len_passed = Flash[PC]
            PC += 1
            TSP -= self.max_args_len - arg_len_passed
            tpush(arg_len_passed)
        push2(PC)
        push2(FP)
        PSP -= self.size_locals
        push2(TSP)      # args addr
        FP = PSP
        PC = self.code_addr
        push1(self.word_index)

class deferrable_word(non_deferrable_word):
    def finish_def(self):
        if Data_end + self.frame_size >= Data_limit:
            raise MemoryError("Data space exceeded")
        self.frame_addr = Data_end
        Data_end += self.frame_size
        Data[self.frame_addr] = self.word_index
        self.frame_addr = frame_addr + 1
    def run(self):
        if (self.max_args_len > self.min_args_len):
            arg_len_passed = Flash[PC]
            PC += 1
            TSP -= self.max_args_len - arg_len_passed
            tpush(arg_len_passed)
        put_data2(self.frame_addr + self.size_locals + 4, PC) 
        put_data2(self.frame_addr + self.size_locals + 2, FP)
        put_data2(self.frame_addr, TSP)
        FP = self.frame_addr
        PC = self.code_addr

# mixin
class lvalue:
    def compile_value(self, compiler, prev_domain = None):
        self.compile_lvalue(compiler)
        compiler.push

