# macro.py

from examples.washer import declaration

class macro(declaration.word):
    @classmethod
    def create_instance(cls, project_pkg, name, id, db_cur):
        ans = declaration.load_class(project_pkg, name, id, db_cur)
        return ans, new_syntax(id, cls.kind_id, db_cur)

class macro_word(macro):
    @classmethod
    def init_class3(cls, db_cur):
        pass

def new_syntax(word_id, macro_id, db_cur):
    ans = declaration.get_answers(word_id, macro_id, db_cur)
    syntax = ans['syntax']
    if isinstance(syntax[0], (str, unicode)):
        syntax = ('statement : ' + syntax[0],)
    else:
        syntax = tuple('statement : ' + x[0] for x in syntax)
    keywords = ans['new syntax keyword']
    return syntax, dict((x[0], x[2]['token value'][0]) for x in keywords)

