# repeat.py

from ucc.ast import ast, crud, symbol_table
from ucclib.built_in import macro

class repeat(macro.macro_word):
    def macro_expand(self, ast_node, words_by_label):
        #print "repeat.macro_expand"
        _, count, body = ast_node.args
        loop_label = crud.gensym('repeat')
        if not count:
            #print "no count"
            new_args = (
              ast.ast(kind='label', label=loop_label, expect='statement'),
              body,
              ast.ast(kind='jump', label=loop_label, expect='statement'),
            )
        else:
            count = count[0]
            #print "count", count
            loop_var = crud.gensym('repeat_var')
            symbol_id = symbol_table.symbol.create(loop_var, 'var',
                                                   ast_node.word_symbol_id) \
                                    .id
            test = crud.gensym('repeat_test')
            new_args = (
              ast.ast((ast.ast(kind='word', label='set',
                               symbol_id=symbol_table.Keep_symbols['set'].id),
                       ast.ast(kind='word', label=loop_var,
                               symbol_id=symbol_id),
                       count,
                      ),
                      kind='call',
                      expect='statement').prepare(words_by_label),
              ast.ast(kind='jump', label=test, expect='statement'),
              ast.ast(kind='label', label=loop_label, expect='statement'),
            ) + body + (
              ast.ast((ast.ast(kind='word', label='set',
                               symbol_id=symbol_table.Keep_symbols['set'].id),
                       ast.ast(kind='word', label=loop_var,
                               symbol_id=symbol_id),
                       ast.ast((ast.ast(
                                  kind='word', label='-',
                                  symbol_id=symbol_table.Keep_symbols['-'].id),
                                ast.ast(kind='word', label=loop_var,
                                        symbol_id=symbol_id),
                                ast.ast(kind='int', int1=1),
                               ),
                               kind='call',
                              ).prepare(words_by_label),
                      ),
                      kind='call',
                      expect='statement').prepare(words_by_label),
              ast.ast(kind='label', label=test, expect='statement'),
              ast.ast(ast.ast(kind='word', label=loop_var,
                              symbol_id=symbol_id, expect='condition'),
                      kind='if-true',
                      label=loop_label,
                      expect='statement'),
            )
        return ast_node.macro_expand(new_args, kind='series')

