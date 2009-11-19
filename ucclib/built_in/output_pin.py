# output_pin.py

from ucc.database import ast, symbol_table
from ucc.assembler import io
from ucclib.built_in import declaration

class output_pin(declaration.word):
    def macro_expand(self, fn_symbol, ast_node, words_needed):
        assert len(ast_node.args) == 2
        assert len(ast_node.args[1]) == 1, \
               "%s: incorrect number of arguments, expected 1, got %s" % \
                 (self.label, len(ast_node.args[1]))
        fn_symbol.side_effects = 1
        pin_number = self.ww.get_value('pin_number')
        on_is = self.ww.get_answer('on_is').tag
        register, bit_number = digital_pin_lookup[pin_number]
        if on_is == 'HIGH':
            value = ast_node.args[1][0]
        else:
            value = ast.ast(ast.ast(kind='word', label='negate',
                                    symbol_id=symbol_table.get('negate').id),
                            ast_node.args[1][0],
                            kind='call')
        new_args = (
            ast.ast(kind='word', label='set_pin',
                    symbol_id=symbol_table.get('set_pin').id),
            (ast.ast(kind='int', int1=register),
             ast.ast(kind='int', int1=(1 << bit_number)),
             value,
            )
        )
        return ast_node.macro_expand(fn_symbol, words_needed, new_args,
                                     kind='call')

digital_pin_lookup = {
    0: (io.portd, 0),
    1: (io.portd, 1),
    2: (io.portd, 2),
    3: (io.portd, 3),
    4: (io.portd, 4),
    5: (io.portd, 5),
    6: (io.portd, 6),
    7: (io.portd, 7),
    8: (io.portb, 0),
    9: (io.portb, 1),
    10: (io.portb, 2),
    11: (io.portb, 3),
    12: (io.portb, 4),
    13: (io.portb, 5),
    14: (io.portc, 0),
    15: (io.portc, 1),
    16: (io.portc, 2),
    17: (io.portc, 3),
    18: (io.portc, 4),
    19: (io.portc, 5),
}
