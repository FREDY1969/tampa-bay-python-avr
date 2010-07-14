# if_.py

r'''If statement.

This is implemented as a macro.
'''

from ucc.database import ast, crud
from ucclib.built_in import macro

class if_(macro.macro):
    def macro_expand(self, fn_symbol, ast_node, words_needed):
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
              ast.ast.from_parser(ast_node.get_syntax_position_info(),
                                  kind='label', label=endif_label,
                                  expect='statement'),
            )
        else:
            else_label = crud.gensym('else')
            syntax_position = ast_node.get_syntax_position_info()
            new_args = (
              ast.ast.from_parser(condition.get_syntax_position_info(),
                                  condition,
                                  kind='if-false',
                                  label=else_label,
                                  expect='statement'),
              true_branch,
              ast.ast.from_parser(syntax_position,
                                  kind='jump', label=endif_label,
                                  expect='statement'),
              ast.ast.from_parser(syntax_position,
                                  kind='label', label=else_label,
                                  expect='statement'),
              false_branch,
              ast.ast.from_parser(syntax_position,
                                  kind='label', label=endif_label,
                                  expect='statement'),
            )
        return ast_node.macro_expand(fn_symbol, words_needed, new_args,
                                     kind='series')
