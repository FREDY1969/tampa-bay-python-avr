# pass_.py

from ucclib.built_in import macro

class pass_(macro.macro_word):
    def compile_macro(self, ast_id, db_cur):
        replace_ast(ast_id, (), db_cur)
