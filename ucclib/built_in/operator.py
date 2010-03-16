# operator.py

r'''These are the binary and unary operators of the language.

They are translated straight into intermediate code, but constant operands are
evaluated at compile time to be macro expanded into a constant.  And types are
propogated up and down from the operator node to its arguments.
'''

from ucc.database import block, symbol_table
from ucclib.built_in import declaration

class operator(declaration.word):
    r'''Used for operators that go straight into intermediate code.
    
    The label is used as the intermediate code operator.
    ''' 
    def compile_value(self, ast_node):
        assert len(ast_node.args) >= 2 and len(ast_node.args) <= 3, \
               "{}: incorrect number of arguments, expected 1 or 2, got {}" \
                 .format(self.label, len(ast_node.args) - 1)

        arg1 = ast_node.args[1].compile()
        arg2 = None
        if len(ast_node.args) == 3:
            arg2 = ast_node.args[2].compile()

        return block.Current_block.gen_triple(
                 self.label,
                 arg1,
                 arg2,
                 syntax_position_info=ast_node.get_syntax_position_info())

