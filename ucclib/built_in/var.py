# var.py

from ucc.database import assembler
from ucclib.built_in import declaration

class var(declaration.word):
    def compile(self, words_by_label):
        initial_value = self.ww.get_value('initial_value')
        if initial_value is None:
            assembler.block('bss', self.name).write((
                assembler.inst('zeroes', '2', length=2),
            ))
        else:
            assembler.block('data', self.name).write((
                assembler.inst('int16', str(initial_value), length=2),
            ))

