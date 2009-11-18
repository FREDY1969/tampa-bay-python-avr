# var.py

from ucclib.built_in import declaration

class var(declaration.word):
    def compile(self, words_by_label):
        initial_value = self.ww.get_value('initial_value')
        data_name = self.name + "__data"
        if initial_value is None:
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

