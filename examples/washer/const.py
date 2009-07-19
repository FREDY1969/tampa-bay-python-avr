# const.py

import declaration

class const(declaration.declaration):
    def compile(self, db_cur):
        value = self.get_answers(db_cur)['value'][0]
        return (("%s:" % self.name,
                 "    .addr do-const",
                 "    .word %s" % value),
                ('do-const',))
