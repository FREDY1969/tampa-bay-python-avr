# declaration.py

r'''The granddaddy (root) of all words!
'''

import os.path
from ucc.database import ast, block, crud, symbol_table
from ucc.parser import parse
from ucc.word import helpers, word as word_module

Empty_set = frozenset()

class declaration:
    r'''All words are subclasses of declaration.

    Defining words are classes, while non-defining words are instances of
    those classes.  The "kind" is used both as the base class (for defining
    words) and the instance's class (for non-defining words).

    Thus, a defining word is a subclass of it's "kind".

    And, a non-defining word is an instance of it's "kind".
    '''
    def __init__(self, ww):
        r'''Initializes an instance of this declaration.
        '''
        self.ww = ww
        self.name = ww.name
        self.label = ww.label

    @classmethod
    def init_class(cls, ww):
        r'''Initializes the declaration itself.
        '''
        cls.kind_ww = ww
        cls.kind = ww.name
        cls.kind_label = ww.label
        cls.init_class2()

    @classmethod
    def init_class2(cls):
        r'''Meant to be overridden by subclasses...

        May not be needed anymore...
        '''
        pass

    @classmethod
    def create_subclass(cls, ww):
        r'''Loads and initializes a subclass of this declaration.

        Returns the newly loaded class object.
        '''
        ans = load_class(ww)
        return ans, ans.new_syntax()

    @classmethod
    def create_instance(cls, ww):
        r'''Creates an instance of this declaration.

        Returns the new instance.
        '''
        return cls(ww), None

    @classmethod
    def new_syntax(cls):
        r'''Returns the new syntax added by this word.

        Returns None, or (syntax, tokens).

        Syntax is a tuple of strings, e.g.:
          "raw_statement : IF() condition [series] ( ELSE_TOK [series] )?"
        Tokens is a dict {keyword_name: token_value}, e.g.:
          {'if': 'IF', 'else': 'ELSE_TOK'}

        May be overridden by base classes.
        '''
        return None

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.name)

    def parse_file(self, parser, debug = 0):
        r'''Returns a frozenset of the labels of the words needed.

        This must also update the 'side_effects' and 'suspends' attributes of
        the `symbol`, as well as record info in the 'fn_calls' and
        'fn_global_variables' tables using the `ucc.database.fn_xref` routines:
        'calls', 'uses' and 'sets'.

        The implementation of this method is left up to the subclass...
        '''
        return Empty_set

    def get_method(self, prefix, expect):
        return getattr(self, prefix + '_' + expect, None) or \
               getattr(self, prefix + '_generic')

class word(declaration):
    r'''Base class for all words that can be used in high-level code.
    '''
    def compile(self):
        r'''Empty stub as default action.
        '''
        pass

    def update_expect(self, ast_node):
        r'''Chance to update 'expect' for ast_node.

        This is done prior to `macro_expand`-ing the ast args and the ast_node
        itself.
        '''
        pass

    def update_types(self, ast_node):
        r'''Chance to update the types for the ast_node and/or its args.

        This is done after `update_expect` and after `macro_expand`-ing the ast
        args.
        '''
        return None

    def macro_expand(self, fn_symbol, ast_node, words_needed):
        r'''Chance to macro expand the ast_node itself.

        This is the last step in preparing the ast_node prior to storing it in
        the database.

        Returns the (possibly new) ast_node.
        '''
        return ast_node

    def prepare_generic(self, fn_symbol, ast_node, words_needed):
        self.update_expect(ast_node)
        ast_node.prepare_args(fn_symbol, words_needed)
        self.update_types(ast_node)
        return self.macro_expand(fn_symbol, ast_node, words_needed)

    def compile_generic(self, ast_node):
        raise ValueError("{} used as a {}".format(self.label, ast_node.expect))

class high_level_word(word):
    r'''Base class for all words with high-level code as their text.
    '''
    def parse_file(self, parser, debug = 0):
        filename = self.ww.get_filename()
        for i, label in enumerate(self.ww.get_value('argument')):
            symbol_table.symbol.create(label, 'parameter', self.ww.symbol,
                                       int1=i)
        worked, ast_args = parse.parse_file(parser, self.ww, debug)
        if not worked:
            raise AssertionError("parse failed for " + filename)
        words_needed = set()
        with crud.db_transaction():
            self.ast_args = \
              ast.prepare_args(self.ww.symbol, ast_args, words_needed)
            ast.save_word(self.label, self.ww.symbol, self.ast_args)
        return frozenset(words_needed)

    def compile(self):
        assert not block.Current_block, \
               "{}.compile: previous block({}) not written" \
                 .format(self.label, block.Current_block.name)
        block.delete(self.ww.symbol)
        block.block(self.label, self.ww.symbol.id)
        parameters = ast.compile_args(self.ast_args)
        if block.Current_block:
            block.Current_block.block_end(
              block.Current_block.gen_triple('return', parameters))

    def compile_value(self, ast_node):
        assert len(ast_node.args) == 2
        fn_args = self.ww.get_value('argument')
        assert len(ast_node.args[1]) == len(fn_args), \
               "{}: incorrect number of arguments, expected {}, got {}" \
                 .format(self.label, len(fn_args), len(ast_node.args[1]))
        return block.Current_block.gen_triple(
                 'call_direct',
                 tuple(arg.compile() for arg in ast_node.args[1]),
                 symbol=self.ww.symbol)

    def compile_statement(self, ast_node):
        self.compile_value(ast_node)


def load_class(ww):
    r'''Imports and initializes the Python class for a defining word.
    '''
    mod = helpers.import_module("{}.{}".format(ww.package_name, ww.name))
    new_subclass = getattr(mod, ww.name)
    new_subclass.init_class(ww)
    return new_subclass
