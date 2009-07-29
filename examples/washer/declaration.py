# declaration.py

import os.path
from ucc.parser import parse

class declaration(object):
    def __init__(self, name, id):
        self.name = name
        self.id = id
    @classmethod
    def init_class(cls, name, id, db_cur):
        cls.kind_name = name
        cls.kind_id = id
        cls.init_class2(db_cur)
    @classmethod
    def init_class2(cls, db_cur):
        cls.question_qid = 1
        cls.subquestion_qid = 2
        cls.repeatable_qid = 3
        cls.filename_qid = 4
    def parse_file(self, parser, project_dir):
        pass
    def new_syntax(self, db_cur):
        return (), {}

class word(declaration):
    @classmethod
    def init_class2(cls, db_cur):
        cls.answers = get_answers(cls.kind_id, cls.__bases__[0].kind_id, db_cur)
        cls.filename_suffix = cls.answers['filename suffix'][0]
        cls.init_class3(db_cur)
    @classmethod
    def init_class3(cls, db_cur):
        pass
    def get_filename(self, project_dir = ''):
        assert self.filename_suffix
        return os.path.join(project_dir,
                            self.name + '.' + self.filename_suffix)

class high_level_word(word):
    def parse_file(self, parser, project_dir):
        filename = self.get_filename(project_dir)
        if not parse.parse_file(parser, filename):
            raise AssertionError, "parse failed for " + filename

def get_answers(word_id, kind_id, db_cur):
    r'''Get_answers for this word.

    The answers are returned in a dict where the question is the key.  For
    non-repeatable answers, the value is [answer, children_dict].  For
    repeatable answers, the value is a list of [answer, children_dict].
    '''
    db_cur.execute("""select question.answer,
                             repeat.answer = 'True',
                             answer.id,
                             answer.parent,
                             answer.answer
                        from answer
                             inner join answer as question
                             on answer.question_id = question.id
                             inner join answer as repeat
                             on question.id = repeat.parent
                                and repeat.question_id = ?
                       where answer.word_id = ?
                         and question.word_id = ?
                       order by answer.parent, question.position,
                                answer.position
                   """, (declaration.repeatable_qid, word_id, kind_id))

    ans = {}
    ans_index = {}  # {id: children_dict}
    for question, repeatable, id, parent, answer in db_cur:
        if parent is None:
            where = ans
        else:
            where = ans_index[parent]
        children_dict = {}
        ans_index[id] = children_dict
        if repeatable:
            where.setdefault(question, []).append([answer, children_dict])
        else:
            where[question] = [answer, children_dict]
    return ans
