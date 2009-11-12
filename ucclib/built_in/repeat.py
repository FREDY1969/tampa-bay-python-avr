# repeat.py

from ucclib.built_in import macro

class repeat(macro.macro_word):
    def compile_macro(self, ast_id):
        args = get_ast_args(ast_id)
        loop_label = gensym('repeat')
        if len(args) == 1:
            new_ast = (('label', loop_label),
                       args[0].compile_statement('...'),
                       ('jmp', loop_label),
                      )
        else:
            loop_var = gensym('repeat_var')
            test = gensym('repeat_test')
            new_ast = (('set', loop_var, args[0].compile_value('...')),
                       ('jmp', test),
                       ('label', loop_label),
                       args[1].compile_statement('...'),
                       ('dec', loop_var),
                       ('label', test),
                       ('jmp-true', loop_var, loop_label),
                      )
        replace_ast(ast_id, new_ast)

