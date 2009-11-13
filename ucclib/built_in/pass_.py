# pass_.py

from ucclib.built_in import macro

class pass_(macro.macro_word):
    def macro_expand(self, ast_node, words_by_label):
        return ast_node.macro_expand((), kind='no-op')

