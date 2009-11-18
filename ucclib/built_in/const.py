# const.py

from ucclib.built_in import declaration

class const(declaration.word):
    def compile(self, words_by_label):
        value = self.ww.get_value('value')
        return (((self.name, 'code-addr', 'do-const', None),
                 (None, 'word', str(value), None)),
                (),
                (),
                (),
                ('do-const',))
