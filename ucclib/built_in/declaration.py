# declaration.py

import os.path
from ucc.parser import parse
from ucc.word import helpers, word as word_module

class declaration(object):
    def __init__(self, name, label):
        self.name = name
        self.label = label

    @classmethod
    def init_class(cls, name, label, project_dir):
        cls.kind = name
        cls.kind_label = label
        cls.init_class2(project_dir)

    @classmethod
    def init_class2(cls, project_dir):
        pass

    @classmethod
    def create_instance(cls, project_pkg, name, label, project_dir):
        return load_class(project_pkg, name, label, project_dir), None

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)

    def parse_file(self, parser, project_dir):
        pass

class word(declaration):
    @classmethod
    def init_class2(cls, project_dir):
        cls.answers = get_answers(cls.kind, project_dir)
        cls.init_class3(project_dir)

    @classmethod
    def init_class3(cls, project_dir):
        suffix = cls.answers['filename_suffix']
        cls.filename_suffix = None if suffix is None else suffix.value

    @classmethod
    def create_instance(cls, project_pkg, name, label, project_dir):
        ans = cls(name, label)
        return ans, None

    def get_filename(self, project_dir):
        assert self.filename_suffix
        return os.path.join(project_dir, self.name + '.' + self.filename_suffix)

    def compile(self, db_cur, words_by_name):
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

    def prepare_children(self, ast_id, expect, db_cur, words_by_name):
        args = []
        macros_seen = False
        for id, kind, word_name, int1, int2, str1, expect, \
            parent_arg_num, arg_order \
         in get_ast_nodes(db_cur, ast_id):
            self.update_expect(id, parent_arg_num, arg_order, db_cur)
            new_id_info = getattr(words_by_name[word_name],
                                  'prepare_' + expect) \
                            (id, kind, int1, int2, str1, db_cur, words_by_name)
            args.append(new_id_info + [parent_arg_num, arg_order])
            if new_id_info[0] != id: macros_seen = True
        return macros_seen, args, self.update_type(ast_id, args, db_cur)

    def create_macro(self, ast_id, kind, int1, int2, str1, expect, type,
                           db_cur, args, macros_seen):
        return ast_id, kind, self.name, int1, int2, str1, expect, type

    def generic_prepare(self, ast_id, kind, int1, int2, str1, expect, db_cur,
                              words_by_name):
        macros_seen, args, type = self.prepare_children(ast_id, expect, db_cur,
                                                        words_by_name)
        return self.create_macro(ast_id, kind, int1, int2, str1, expect, type,
                                 db_cur, args, macros_seen)

    def prepare_statement(self, ast_id, kind, int1, int2, str1, db_cur,
                                words_by_name):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'statement', db_cur, words_by_name)

    def compile_statement(self, ast_id, kind, int1, int2, str1, type, db_cur,
                                words_by_name):
        raise AssertionError("%s used as a statement" % self.label)

    def prepare_cond(self, ast_id, kind, int1, int2, str1, db_cur,
                                words_by_name):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'cond', db_cur, words_by_name)

    def compile_cond(self, ast_id, kind, int1, int2, str1, type, db_cur,
                                words_by_name):
        raise AssertionError("%s used as a condition" % self.label)

    def prepare_value(self, ast_id, kind, int1, int2, str1, db_cur,
                                words_by_name):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'value', db_cur, words_by_name)

    def compile_value(self, ast_id, kind, int1, int2, str1, type, db_cur,
                                words_by_name):
        raise AssertionError("%s used as a value" % self.label)

    def prepare_lvalue(self, ast_id, kind, int1, int2, str1, db_cur,
                                words_by_name):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'lvalue', db_cur, words_by_name)

    def compile_lvalue(self, ast_id, kind, int1, int2, str1, type, db_cur,
                                words_by_name):
        raise AssertionError("tried to assign to %s" % self.label)

    def prepare_producer(self, ast_id, kind, int1, int2, str1, db_cur,
                                words_by_name):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'producer', db_cur, words_by_name)

    def compile_producer(self, ast_id, kind, int1, int2, str1, type, db_cur,
                                words_by_name):
        raise AssertionError("%s used as a producer" % self.label)

    def prepare_start_stop(self, ast_id, kind, int1, int2, str1, db_cur,
                                words_by_name):
        return self.generic_prepare(ast_id, kind, int1, int2, str1,
                                    'start_stop', db_cur, words_by_name)

    def compile_start_stop(self, ast_id, kind, int1, int2, str1, type, db_cur,
                                words_by_name):
        raise AssertionError("%s used as a context manager" % self.label)

class high_level_word(word):
    def parse_file(self, parser, project_dir):
        filename = self.get_filename(project_dir)
        worked, word_body_id = parse.parse_file(parser, filename)
        if not worked:
            raise AssertionError, "parse failed for " + filename
        self.word_body_id = word_body_id

    def compile(self, db_cur, words_by_name):
        print "%s.compile" % (self.name,), "id", self.word_body_id
        series_to_compile = []
        for ast_id, kind, word, int1, int2, str1, expect, _, _ \
         in get_ast_nodes(db_cur, self.word_body_id):
            print "%s.prepare_%s" % (word, expect)
            series_to_compile.append(
              getattr(words_by_name[word], 'prepare_' + expect)
                (ast_id, kind, int1, int2, str1, db_cur, words_by_name))
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

def get_ast_nodes(db_cur, parent_id):
    r'''Returns a list of information on the arguments for parent_id.

    The information is: [ast_id, kind, word_name, int1, int2, str1, expect,
                         parent_arg_num, arg_order]
    '''
    db_cur.execute("""select id, kind, word, int1, int2, str1, expect,
                             parent_arg_num, arg_order
                        from ast
                       where parent_node = :parent_id
                       order by parent_arg_num, arg_order
                   """,
                   {'parent_id': parent_id})
    return db_cur.fetchall()

def load_class(project_pkg, name, label, project_dir):
    mod = helpers.import_module("%s.%s" % (project_pkg, name))
    new_word = getattr(mod, name)
    new_word.init_class(name, label, project_dir)
    return new_word

def get_answers(name, project_dir):
    r'''Get_answers for this word.

    The answers are returned in a dict where the question name is the key.

    For non-repeatable answers, the value is an answer object or None (for
    optional unanswered questions).

    For repeatable answers, the value is a (possibly empty) list of answer
    objects.
    '''
    return word_module.read_word(name, project_dir).answers
