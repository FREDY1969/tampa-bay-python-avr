# declaration.py

class declaration(object):
    def __init__(self, name, id, kind):
        self.name = name
        self.id = id
        self.kind = kind
    def process_answers(self, db_cur):
        return False
    def parse_file(self, parser, filename):
        pass
    def get_answers(self, db_cur):
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
                       """, (repeatable_qid, self.id, self.kind))

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


