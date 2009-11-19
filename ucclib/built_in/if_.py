# if_.py

from ucc.database import ast, crud
from ucclib.built_in import macro

class if_(macro.macro):
    def macro_expand(self, fn_symbol, ast_node, words_by_label, words_needed):
        _, condition, true_branch, false_branch = ast_node.args
        endif_label = crud.gensym('endif')
        if false_branch is None:
            new_args = (
              ast.ast.from_parser(condition.get_syntax_position_info(),
                                  condition,
                                  kind='if-false',
                                  label=endif_label,
                                  expect='statement'),
              true_branch,
              ast.ast(kind='label', label=endif_label, expect='statement'),
            )
        else:
            else_label = crud.gensym('else')
            new_args = (
              ast.ast.from_parser(condition.get_syntax_position_info(),
                                  condition,
                                  kind='if-false',
                                  label=else_label,
                                  expect='statement'),
              true_branch,
              ast.ast(kind='jump', label=endif_label, expect='statement'),
              ast.ast(kind='label', label=else_label, expect='statement'),
              false_branch,
              ast.ast(kind='label', label=endif_label, expect='statement'),
            )
        return ast_node.macro_expand(fn_symbol, words_by_label, words_needed,
                                     new_args, kind='series')
