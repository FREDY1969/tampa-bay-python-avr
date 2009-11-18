# singleton.py

from ucclib.built_in import declaration

class singleton(declaration.word):
    @classmethod
    def create_instance(cls, ww):
        new_cls, new_syntax = cls.create_subclass(ww)
        assert new_syntax is None
        ans = new_cls(ww)
        return ans, ans.new_syntax2()

    def new_syntax2(self):
        r'''Returns None, or (syntax, tokens).

        This is used for singleton new_syntax because:

           1.  The new_syntax method has to be a normal method rather than a
               classmethod.
           2.  It can't have the same name as the (inherited) classmethod.

        Syntax is a tuple of strings, e.g.:
          "raw_statement : IF() condition [series] ( ELSE_TOK [series] )?"
        Tokens is a dict {keyword_name: token_value}, e.g.:
          {'if': 'IF', 'else': 'ELSE_TOK'}
        '''
        return None

