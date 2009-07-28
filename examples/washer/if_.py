# if_.py

from examples.washer import macro

class if_(macro.macro):  # Is this really a class?
    def compile_macro(self, ast_id, db_cur):
        condition, true_branch, false_branch = get_ast_args(ast_id, db_cur)
        else_label = gensym('else')
        endif_label = gensym('endif')
        new_ast = (condition.compile_cond('...'),
                   ('jmp-false', else_label),
                   true_branch.compile_statement('...'),
                  )
        if false_branch is None:
            new_ast += (('label', else_label),)
        else:
            new_ast += (
                ('jmp', endif_label),
                ('label', else_label),
                false_branch.compile_statement('...'),
                ('label', endif_label),
              )
        replace_ast(ast_id, new_ast, db_cur)








