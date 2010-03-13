# input_pin.py

r'''Input pins are used as expressions.

The bit representing the pin is read each time the expression is executed.

You may specify whether the bit being ON or OFF represents True.
'''

from ucc.database import block
from ucclib.built_in import declaration, output_pin

class input_pin(declaration.word):
    def macro_expand(self, fn_symbol, ast_node, words_needed):
        r'''This just sets the side_effects bit on the fn_symbol.
        '''
        assert len(ast_node.args) == 2
        fn_symbol.side_effects = 1

    def compile_value(self, ast_node):
        r'''This uses input-bit.

        If on-is LOW, it does a bit-xor with the bit.
        '''
        assert len(ast_node.args) == 1

        pin_number = self.ww.get_value('pin_number')
        on_is = self.ww.get_answer('on_is').tag
        port_label, bit_number = output_pin.digital_pin_lookup[pin_number]
        print("input_pin: port_label", port_label, ", bit_number", bit_number)

        input_bit = block.Current_block.gen_triple(
                      'input-bit',
                      string='io.pin' + port_label,
                      int1=bit_number,
                      syntax_position_info=ast_node.get_syntax_position_info())

        if on_is == 'HIGH':
            return input_bit

        bit_mask = block.Current_block.gen_triple(
                     'int',
                     int1=1 << bit_number,
                     syntax_position_info=ast_node.get_syntax_position_info())

        return block.Current_block.gen_triple(
                     'bit-xor',
                     input_bit,
                     bit_mask,
                     syntax_position_info=ast_node.get_syntax_position_info())

    def compile_condition(self, ast_node):
        r'''This uses input-bit.

        If on-is LOW, it does a 'not' on the bit.
        '''
        assert len(ast_node.args) == 1

        pin_number = self.ww.get_value('pin_number')
        on_is = self.ww.get_answer('on_is').tag
        port_label, bit_number = output_pin.digital_pin_lookup[pin_number]
        print("input_pin: port_label", port_label, ", bit_number", bit_number)

        input_bit = block.Current_block.gen_triple(
                      'input-bit',
                      string='io.pin' + port_label,
                      int1=bit_number,
                      syntax_position_info=ast_node.get_syntax_position_info())

        if on_is == 'HIGH':
            return input_bit

        return block.Current_block.gen_triple(
                     'not',
                     input_bit,
                     syntax_position_info=ast_node.get_syntax_position_info())

