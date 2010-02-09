# clear_output_bit.py

r'''Expects an "ioreg-bit" AST node as its single argument.

This is intended to be machine independent.

The "ioreg-bit" AST nodes are only generated through special words like:

    - `output_pin`
'''

from ucc.database import block
from ucclib.built_in import singleton

class clear_output_bit(singleton.singleton):
    def update_expect(self, ast_node):
        ast_node.args[1][0].expect = 'lvalue'

    def compile_statement(self, ast_node):
        assert len(ast_node.args) == 2
        assert len(ast_node.args[1]) == 1, \
               "incorrect number of arguments to 'clear_output_bit', " \
               "expected 1, got %d" % \
                 len(ast_node.args[1])

        ioreg_bit = ast_node.args[1][0]

        assert ioreg_bit.kind == 'ioreg-bit', \
               "clear_output_bit: can only assign to ioreg-bits"

        block.Current_block.gen_triple(
          'output-bit-clear',
          string=ioreg_bit.label,
          int1=ioreg_bit.int1,
          syntax_position_info=ast_node.get_syntax_position_info())
        return None

