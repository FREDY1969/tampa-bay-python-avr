# declaration.py

import os.path
from ucc.ast import crud
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
        return load_class(ww)

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

    def parse_file(self, parser, debug = 0):
        pass

    def get_method(self, prefix, expect):
        return getattr(self, prefix + '_' + expect) or \
               getattr(self, prefix + '_generic')

class word(declaration):
    def compile(self, words_by_label):
        print "FIX: Implement compile for class", self.__class__.__name__
        return (), (), (), (), ()

    def update_expect(self, child_ast_id, arg_num, pos_num):
        r'''Updates expect for child_ast_id node in database.
        '''
        pass

    def update_type(self, ast_id, args):
        r'''Updates type for ast_id node in database and returns new type.
        '''
        return None

    def prepare_children(self, ast_id, expect, words_by_label):
        args = []
        macros_seen = False
        for id, kind, word_label, int1, int2, str1, expect, \
            parent_arg_num, arg_order \
         in get_ast_nodes(ast_id):
            self.update_expect(id, parent_arg_num, arg_order)
            new_id_info = \
              words_by_label[word_label].get_method('prepare', expect) \
                (id, kind, int1, int2, str1, words_by_label)
            args.append(new_id_info + [parent_arg_num, arg_order])
            if new_id_info[0] != id: macros_seen = True
        return macros_seen, args, self.update_type(ast_id, args)

    def create_macro(self, ast_id, kind, int1, int2, str1, expect, type,
                           args, macros_seen):
        return ast_id, kind, self.name, int1, int2, str1, expect, type

    def prepare_generic(self, ast_id, kind, int1, int2, str1, expect,
                              words_by_label):
        macros_seen, args, type = self.prepare_children(ast_id, expect,
                                                        words_by_label)
        return self.create_macro(ast_id, kind, int1, int2, str1, expect, type,
                                 args, macros_seen)

    def compile_generic(self, ast_id, kind, int1, int2, str1, type,
                              words_by_label):
        raise ValueError("%s used as a %s" % (self.label, ast.expect))

class high_level_word(word):
    def parse_file(self, parser, debug = 0):
        filename = self.ww.get_filename()
        worked = parse.parse_file(parser, self.ww, debug)
        if not worked:
            raise AssertionError, "parse failed for " + filename

    def compile(self, words_by_label):
        print "%s.compile" % (self.name,), "id", self.ww.symbol_id
        series_to_compile = []
        for ast_id, kind, word_label, int1, int2, str1, expect, _, _ \
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

def get_ast_nodes(parent_id):
    r'''Returns a list of information on the arguments for parent_id.

    The information is: [ast_id, kind, label, int1, int2, str1, expect,
                         parent_arg_num, arg_order]
    '''
    return crud.read_as_tuples('ast',
                                 'id', 'kind', 'label',
                                 'int1', 'int2', 'str1',
                                 'expect', 'parent_arg_num', 'arg_order',
                               parent_node=parent_id,
                               order_by=('parent_arg_num', 'arg_order'))

def load_class(ww):
    mod = helpers.import_module("%s.%s" % (ww.package_name, ww.name))
    new_subclass = getattr(mod, ww.name)
    new_subclass.init_class(ww)
    return new_subclass
