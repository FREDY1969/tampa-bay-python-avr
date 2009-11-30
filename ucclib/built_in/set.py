# set.py

from ucc.database import block
from ucclib.built_in import singleton

class set(singleton.singleton):
    def update_expect(self, ast_node):
        ast_node.args[1][0].expect = 'lvalue'

    def compile_statement(self, ast_node):
        assert len(ast_node.args) == 2
        assert len(ast_node.args[1]) == 2, \
               "incorrect number of arguments to 'set', expected 2, got %d" % \
                 len(ast_node.args[1])

        lvalue, rvalue = ast_node.args[1]

        assert lvalue.kind in ('word', 'ioreg'), \
               "set: can only assign to variables or ioregs, " \
               "fancier assignments not implemented"

        ans = rvalue.compile()
        if lvalue.kind == 'word':
            block.Current_block.label(lvalue.symbol_id, ans)
            return ans
        return block.Current_block.gen_triple('output',
                                              string=lvalue.label, int1=ans)

