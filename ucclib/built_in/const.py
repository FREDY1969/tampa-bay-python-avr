# const.py

from ucc.database import assembler
from ucclib.built_in import declaration

class const(declaration.word):
    def compile(self, words_by_label):
        value = self.ww.get_value('value')
        assembler.block('flash', self.name).write((
            assembler.inst('int16', str(value), length=2),
        ))
