# macro.py

from examples.washer import declaration

class macro(declaration.word):
    @classmethod
    def init_class3(cls, db_cur):
        cls.syntax_qid = cls.answers['syntax']
        cls.keyword_qid = cls.answers['new syntax keyword']
        cls.token_value_qid = cls.answers['token value']
    def new_syntax(self, db_cur):
        ans = declaration.get_answers(self.id, self.kind_id, db_cur)
        syntax = ans['syntax']
        if isinstance(syntax[0], (str, unicode)):
            syntax = ('statement : ' + syntax[0],)
        else:
            syntax = tuple('statement : ' + x[0] for x in syntax)
        keywords = ans['new syntax keyword']
        return syntax, dict((x[0], x[1]['token value'][0]) for x in keywords)

