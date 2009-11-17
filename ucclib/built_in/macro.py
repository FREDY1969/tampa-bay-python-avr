# macro.py

from ucclib.built_in import declaration

class macro(declaration.word):
    @classmethod
    def create_instance(cls, ww):
        new_cls, new_syntax = cls.create_subclass(ww)
        return new_cls(ww), new_syntax

    def __repr__(self):
        return "<macro macro>"

class macro_word(declaration.word):
    @classmethod
    def new_syntax(cls):
        syntax = tuple('raw_statement : ' + x.value
                       for x in cls.kind_ww.get_answer('syntax') or ())
        keywords = cls.kind_ww.get_answer('new_syntax_keyword') or ()
        return syntax, dict((x.keyword_name.value, x.token_value.value)
                            for x in keywords)

    def __repr__(self):
        return "<%s %s>" % (self.__name__, self.kind)

