# macro.py

from examples.washer import declaration

class macro(declaration.word):
    def new_syntax(self, db_cur):
        ans = declaration.get_answers(self.id, self.kind_id, db_cur)
        syntax = ans['syntax']
        if isinstance(syntax[0], (str, unicode)):
            syntax = ('statement : ' + syntax[0],)
        else:
            syntax = tuple('statement : ' + x[0] for x in syntax)
        keywords = ans['new syntax keyword']
        return syntax, dict((x[0], x[2]['token value'][0]) for x in keywords)

