# const.py

from ucclib.built_in import declaration

class const(declaration.word):
    def compile(self, db_cur, words_by_name):
        value = self.answers['value'][0]
        return (((self.name, 'code-addr', 'do-const', None),
                 (None, 'word', str(value), None)),
                (),
                (),
                (),
                ('do-const',))
