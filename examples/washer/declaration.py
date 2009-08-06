# declaration.py

import os.path
from ucc.parser import parse
from ucc.word import helpers, word as word_module

class declaration(object):
    def __init__(self, name):
        self.name = name

    @classmethod
    def init_class(cls, name, project_dir):
        cls.kind = name
        cls.init_class2(project_dir)

    @classmethod
    def init_class2(cls, project_dir):
        pass

    @classmethod
    def create_instance(cls, project_pkg, name, project_dir):
        return load_class(project_pkg, name, project_dir), None

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
    def create_instance(cls, project_pkg, name, project_dir):
        ans = cls(name)
        return ans, None

    def get_filename(self, project_dir):
        assert self.filename_suffix
        return os.path.join(project_dir, self.name + '.' + self.filename_suffix)

class high_level_word(word):
    def parse_file(self, parser, project_dir):
        filename = self.get_filename(project_dir)
        if not parse.parse_file(parser, filename):
            raise AssertionError, "parse failed for " + filename

def load_class(project_pkg, name, project_dir):
    mod = helpers.import_module(project_pkg, name)
    new_word = getattr(mod, name)
    new_word.init_class(name, project_dir)
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
