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

class word(declaration):
    def compile(self, db_cur, words_by_name, translation_dict):
        print "FIX: Implement compile for class", self.__class__.__name__
        return (), (), (), (), ()

    def update_expect(self, child_ast_id, arg_num, pos_num, db_cur):
        r'''Updates expect for child_ast_id node in database.
        '''
        pass

    def update_type(self, ast_id, args, db_cur):
        r'''Updates type for ast_id node in database and returns new type.
        '''
        return None

    def prepare_children(self, ast_id, expect, db_cur, words_by_name,
                               translation_dict):
        args = []
        macros_seen = False
        for id, kind, word_label, int1, int2, str1, expect, \
            parent_arg_num, arg_order \
         in get_ast_nodes(ast_id):
            self.update_expect(id, parent_arg_num, arg_order, db_cur)
            new_id_info = \
              getattr(words_by_name[
                        translation_dict.get(word_label, word_label)],
                      'prepare_' + expect) \
                (id, kind, int1, int2, str1, db_cur, words_by_name,
                 translation_dict)
            args.append(new_id_info + [parent_arg_num, arg_order])
            if new_id_info[0] != id: macros_seen = True
        return macros_seen, args, self.update_type(ast_id, args, db_cur)

    def create_macro(self, ast_id, kind, int1, int2, str1, expect, type,
                           db_cur, args, macros_seen):
        return ast_id, kind, self.name, int1, int2, str1, expect, type

    def generic_prepare(self, ast_id, kind, int1, int2, str1, expect, db_cur,
                              words_by_name, translation_dict):
        macros_seen, args, type = self.prepare_children(ast_id, expect, db_cur,
                                                        words_by_name,
                                                        translation_dict)
        return self.create_macro(ast_id, kind, int1, int2, str1, expect, type,
                                 db_cur, args, macros_seen)

    def prepare_statement(self, ast_id, kind, int1, int2, str1, db_cur,
                                words_by_name, translation_dict):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'statement', db_cur, words_by_name,
                                    translation_dict)

    def compile_statement(self, ast_id, kind, int1, int2, str1, type, db_cur,
                                words_by_name):
        raise AssertionError("%s used as a statement" % self.label)

    def prepare_cond(self, ast_id, kind, int1, int2, str1, db_cur,
                           words_by_name, translation_dict):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'cond', db_cur, words_by_name,
                                    translation_dict)

    def compile_cond(self, ast_id, kind, int1, int2, str1, type, db_cur,
                           words_by_name):
        raise AssertionError("%s used as a condition" % self.label)

    def prepare_value(self, ast_id, kind, int1, int2, str1, db_cur,
                            words_by_name, translation_dict):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'value', db_cur, words_by_name,
                                    translation_dict)

    def compile_value(self, ast_id, kind, int1, int2, str1, type, db_cur,
                            words_by_name):
        raise AssertionError("%s used as a value" % self.label)

    def prepare_lvalue(self, ast_id, kind, int1, int2, str1, db_cur,
                             words_by_name, translation_dict):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'lvalue', db_cur, words_by_name,
                                    translation_dict)

    def compile_lvalue(self, ast_id, kind, int1, int2, str1, type, db_cur,
                             words_by_name):
        raise AssertionError("tried to assign to %s" % self.label)

    def prepare_producer(self, ast_id, kind, int1, int2, str1, db_cur,
                               words_by_name, translation_dict):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'producer', db_cur, words_by_name,
                                    translation_dict)

    def compile_producer(self, ast_id, kind, int1, int2, str1, type, db_cur,
                               words_by_name):
        raise AssertionError("%s used as a producer" % self.label)

    def prepare_start_stop(self, ast_id, kind, int1, int2, str1, db_cur,
                                 words_by_name, translation_dict):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'start_stop', db_cur, words_by_name,
                                    translation_dict)

    def compile_start_stop(self, ast_id, kind, int1, int2, str1, type, db_cur,
                                 words_by_name):
        raise AssertionError("%s used as a context manager" % self.label)

class high_level_word(word):
    def parse_file(self, parser, debug = 0):
        filename = self.ww.get_filename()
        worked = parse.parse_file(parser, self.ww, debug)
        if not worked:
            raise AssertionError, "parse failed for " + filename

    def compile(self, db_cur, words_by_name, translation_dict):
        print "%s.compile" % (self.name,), "id", self.ww.symbol_id
        series_to_compile = []
        for ast_id, kind, word_label, int1, int2, str1, expect, _, _ \
         in get_ast_nodes(self.ww.symbol_id):
            print "%s.prepare_%s" % (word_label, expect)
            series_to_compile.append(
              getattr(words_by_name[
                        translation_dict.get(word_label, word_label)],
                      'prepare_' + expect)
                (ast_id, kind, int1, int2, str1, db_cur, words_by_name,
                 translation_dict))
        flash = []
        data = []
        bss = []
        eeprom = []
        words_needed = []
        for ast_id, kind, word, int1, int2, str1, expect, type \
         in series_to_compile:
            print "%s.compile_%s" % (word, expect)
            f, d, b, e, n = getattr(words_by_name[word], 'compile_' + expect) \
                              (ast_id, kind, int1, int2, str1, type,
                               db_cur, words_by_name)
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
