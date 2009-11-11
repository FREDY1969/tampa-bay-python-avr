# macro.py

from ucclib.built_in import declaration

class macro(declaration.word):
    @classmethod
    def new_syntax(cls):
        syntax = tuple('raw_statement : ' + x.value
                       for x in cls.kind_ww.get_answer('syntax', ()))
        keywords = cls.kind_ww.get_answer('new_syntax_keyword', ())
        return syntax, dict((x.keyword_name.value, x.token_value.value)
                            for x in keywords)

    def __repr__(self):
        return "<macro macro>"

class macro_word(macro):
    def __repr__(self):
        return "<%s %s>" % (self.__name__, self.kind)


