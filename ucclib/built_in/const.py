# const.py

from ucclib.built_in import declaration

class const(declaration.word):
    def compile(self, words_by_label):
        value = self.answers['value'][0]
        return (((self.name, 'code-addr', 'do-const', None),
                 (None, 'word', str(value), None)),
                (),
                (),
                (),
                ('do-const',))
