# var.py

from ucc.database import assembler, block
from ucclib.built_in import declaration

class var(declaration.word):
    def compile(self):
        initial_value = self.ww.get_value('initial_value')
        if initial_value is None:
            assembler.block('bss', self.name).write((
                assembler.inst('zeroes', '2', length=2),
            ))
        else:
            assembler.block('data', self.name).write((
                assembler.inst('int16', str(initial_value), length=2),
            ))

    def compile_value(self, ast_node):
        return block.Current_block.gen_triple('global', self.ww.symbol)

