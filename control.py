# control.py

# This is just some _very_ preliminary thinking!  -- bruce

import word

class jmp(word):
    def compile(self, compiler):
        super(jmp, self).compile(source)
        word.push_flash2(source.next())
    def run(self):
        word.PC = word.Flash[word.PC] + 256 * word.Flash[word.PC + 1]

class jz(jmp):
    def run(self):
        if not word.pop2():
            super(jz, self).run()

class jnz(jmp):
    def run(self):
        if word.pop2():
            super(jnz, self).run()

class ret(word):
    def run(self):
        word.PC = word.get_data2(word.FP + self.args_len + 3)
        word.SP = word.FP
        word.FP = word.get_data2(word.FP + self.args_len + 1)

class constant(word):
    def __init__(self, name, value):
        super(constant, self).__init__(name, 0, 2)
        self.value = value
    def run(self):
        word.push2(self.value)

class variable(word):
