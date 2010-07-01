# macro.py

r'''Base class for all macros.

Macros may define new statements in the grammar.
'''

from ucclib.built_in import singleton

class macro(singleton.singleton):
    def new_syntax2(self):
        syntax = tuple('raw_statement : ' + x.value
                       for x in self.ww.get_answer('syntax') or ())
        keywords = self.ww.get_answer('new_syntax_keyword') or ()
        return syntax, {x.keyword_name.value: x.token_value.value
                        for x in keywords}

