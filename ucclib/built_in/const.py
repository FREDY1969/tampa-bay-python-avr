# const.py

r'''A word representing a constant value.
'''

from ucc.database import ast
from ucclib.built_in import declaration

class const(declaration.word):
    def macro_expand(self, fn_symbol, ast_node, words_needed):
        assert ast_node.expects in ('value', 'condition'), \
               "In fn %s: const used as " % (fn_symbol.label, ast_node.kind)
        value = self.ww.get_value('value')
        return ast_node.macro_expand(fn_symbol, words_needed, (),
                                     kind='int', int1=value)
