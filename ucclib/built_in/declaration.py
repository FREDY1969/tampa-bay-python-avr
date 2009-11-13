# declaration.py

import os.path
from ucc.ast import ast, crud
from ucc.parser import parse
from ucc.word import helpers, word as word_module

class declaration(object):
    r'''All defining words are subclasses of declaration.

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
        r'''Returns None, or (syntax, tokens).

        Syntax is a tuple of strings, e.g.:
          "raw_statement : IF() condition [series] ( ELSE_TOK [series] )?"
        Tokens is a dict {keyword_name: token_value}, e.g.:
          {'if': 'IF', 'else': 'ELSE_TOK'}
        '''
        return None

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)

    def parse_file(self, parser, words_by_label, debug = 0):
        pass

    def get_method(self, prefix, expect):
        return getattr(self, prefix + '_' + expect, None) or \
               getattr(self, prefix + '_generic')

class word(declaration):
    def compile(self, words_by_label):
        print "FIX: Implement compile for class", self.__class__.__name__
        return (), (), (), (), ()

    def update_expect(self, ast_node):
        r'''Chance to update 'expect' for ast_node.

        This is done prior to macro expanding the ast args and the ast_node
        itself.
        '''
        pass

    def update_types(self, ast_node):
        r'''Chance to update the types for the ast_node and/or its args.

        This is done after update_expect and after macro expanding the ast
        args.
        '''
        return None

    def macro_expand(self, ast_node, words_by_label):
        r'''Chance to macro expand the ast_node itself.

        This is the last step in preparing the ast_node prior to storing it in
        the database.

        Returns the (possibly new) ast_node.
        '''
        return ast_node

    def prepare_generic(self, ast_node, words_by_label):
        self.update_expect(ast_node)
        ast_node.prepare_args(words_by_label)
        self.update_types(ast_node)
        return self.macro_expand(ast_node, words_by_label)

    def compile_generic(self, ast_node, words_by_label):
        raise ValueError("%s used as a %s" % (self.label, ast_node.expect))

class high_level_word(word):
    def parse_file(self, parser, words_by_label, debug = 0):
        filename = self.ww.get_filename()
        worked, args = parse.parse_file(parser, self.ww, debug)
        if not worked:
            raise AssertionError, "parse failed for " + filename
        args = ast.prepare_args(args, words_by_label)
        with crud.db_transaction():
            ast.save_word(self.label, self.ww.symbol_id, args)

    def compile(self, words_by_label):
        print "%s.compile" % (self.name,), "id", self.ww.symbol_id
        return (), (), (), (), ()
        series_to_compile = []
        for ast_id, kind, word_label, int1, int2, str1, expect \
         in get_ast_nodes(self.ww.symbol_id):
            print "%s.prepare_%s" % (word_label, expect)
            series_to_compile.append(
              words_by_label[word_label].get_method('prepare', expect) \
                (ast_id, kind, int1, int2, str1, words_by_label))
        flash = []
        data = []
        bss = []
        eeprom = []
        words_needed = []
        for ast_id, kind, word_label, int1, int2, str1, expect, type \
         in series_to_compile:
            print "%s.compile_%s" % (word, expect)
            f, d, b, e, n = \
              words_by_label[word_label].get_method('compile', expect) \
                (ast_id, kind, int1, int2, str1, type, words_by_label)
            flash.extend(f)
            data.extend(d)
            bss.extend(b)
            eeprom.extend(e)
            words_needed.extend(n)
        return flash, data, bss, eeprom, words_needed

def load_class(ww):
    mod = helpers.import_module("%s.%s" % (ww.package_name, ww.name))
    new_subclass = getattr(mod, ww.name)
    new_subclass.init_class(ww)
    return new_subclass
