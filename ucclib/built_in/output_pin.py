# output_pin.py

from ucc.database import ast, symbol_table
from ucc.assembler import io
from ucclib.built_in import declaration

class output_pin(declaration.word):
    def macro_expand(self, fn_symbol, ast_node, words_needed):
        r'''This macro expands to an if statement.

        if arg:
            set-output-bit port_name bit#
        else:
            clear-output-bit port_name bit#

        or

        if arg:
            clear-output-bit port_name bit#
        else:
            set-output-bit port_name bit#

        depending on on-is setting.
        '''
        assert len(ast_node.args) == 2
        assert len(ast_node.args[1]) == 1, \
               "%s: incorrect number of arguments, expected 1, got %s" % \
                 (self.label, len(ast_node.args[1]))
        fn_symbol.side_effects = 1
        pin_number = self.ww.get_value('pin_number')
        on_is = self.ww.get_answer('on_is').tag
        port_label, bit_number = digital_pin_lookup[pin_number]
        print "output_pin: port_label", port_label, ", bit_number", bit_number
        ioreg_bit = ast.ast(kind='ioreg-bit',
                            label='io.port' + port_label, int1=bit_number)
        if on_is == 'HIGH':
            true_call = 'set-output-bit'
            false_call = 'clear-output-bit'
        else:
            true_call = 'clear-output-bit'
            false_call = 'set-output-bit'
        new_args = (
            ast.ast.word('if'),
            ast_node.args[1][0],
            (ast.ast.call(true_call, ioreg_bit, expect='statement'),),
            (ast.ast.call(false_call, ioreg_bit, expect='statement'),),
        )
        return ast_node.macro_expand(fn_symbol, words_needed, new_args,
                                     kind='call')

digital_pin_lookup = {
    0: ('d', 0),
    1: ('d', 1),
    2: ('d', 2),
    3: ('d', 3),
    4: ('d', 4),
    5: ('d', 5),
    6: ('d', 6),
    7: ('d', 7),
    8: ('b', 0),
    9: ('b', 1),
    10: ('b', 2),
    11: ('b', 3),
    12: ('b', 4),
    13: ('b', 5),
    14: ('c', 0),
    15: ('c', 1),
    16: ('c', 2),
    17: ('c', 3),
    18: ('c', 4),
    19: ('c', 5),
}
