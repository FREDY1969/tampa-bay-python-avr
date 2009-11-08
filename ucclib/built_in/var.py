# var.py

from ucclib.built_in import declaration

class var(declaration.word):
    def compile(self, db_cur, words_by_name):
        initial_value = self.answers['initial value'][0]
        data_name = self.name + "__data"
        if initial_value == '0':
            return (((self.name, 'code-addr', 'do-var', None),
                     (None, 'data-addr', data_name, None)),
                    (),
                    ((data_name, 2),),
                    (),
                    ('do-var',),
                   )
        return (((self.name, 'code-addr', 'do-var', None),
                 (None, 'data-addr', data_name, None)),
                ((data_name, 'word', initial_value),),
                (),
                (),
                ('do-var',),
               )

