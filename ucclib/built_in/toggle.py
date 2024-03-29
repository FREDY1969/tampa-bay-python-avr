# toggle.py

r'''Toggle statement.

Uses the AVR PIN bits to toggle an output pin.

Takes the output-pin as only argument.

This is implemented as a macro.
'''

from ucc.database import ast, symbol_table
from ucclib.built_in import macro, output_pin

class toggle(macro.macro):
    def macro_expand(self, fn_symbol, ast_node, words_needed):
        r'''This macro expands to an set-output-bit.

        set-output-bit port_name bit#
        '''
        assert len(ast_node.args) == 2
        assert len(ast_node.args[1]) == 1, \
               "{}: incorrect number of arguments, expected 1, got {}" \
                 .format(self.label, len(ast_node.args[1]))
        fn_symbol.side_effects = 1
        pin = ast_node.args[1][0]
        #print "toggle: pin", pin, pin.symbol_id, pin.label
        pin_number = \
          symbol_table.get_by_id(pin.symbol_id).word_word \
                      .get_value('pin_number')
        port_label, bit_number = output_pin.digital_pin_lookup[pin_number]
        #print "toggle: port_label", port_label, ", bit_number", bit_number
        ioreg_bit = ast.ast.from_parser(pin.get_syntax_position_info(),
                                        kind='ioreg-bit',
                                        label='pin' + port_label,
                                        int1=bit_number)
        new_args = (
            ast.ast.word('set-output-bit', ast_node.get_syntax_position_info()),
            (ioreg_bit,),
        )
        return ast_node.macro_expand(fn_symbol, words_needed, new_args,
                                     kind='call')

