# pass_.py

from ucclib.built_in import macro

class pass_(macro.macro):
    def macro_expand(self, fn_symbol, ast_node, words_by_label, words_needed):
        return ast_node.macro_expand((), kind='no-op')

