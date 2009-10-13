# macro.py

from examples.washer import declaration

class macro(declaration.word):
    @classmethod
    def create_instance(cls, project_pkg, name, label, project_dir):
        ans = declaration.load_class(project_pkg, name, label, project_dir)
        return ans, new_syntax(name, project_dir)

    def __repr__(self):
        return "<macro macro>"

class macro_word(macro):
    @classmethod
    def init_class3(cls, project_dir):
        pass

    def __repr__(self):
        return "<%s %s>" % (self.__name__, self.kind)

def new_syntax(name, project_dir):
    ans = declaration.get_answers(name, project_dir)
    syntax = tuple('raw_statement : ' + x.value for x in ans['syntax'])
    keywords = ans['new_syntax_keyword']
    return syntax, dict((x.keyword_name.value, x.token_value.value)
                        for x in keywords)

