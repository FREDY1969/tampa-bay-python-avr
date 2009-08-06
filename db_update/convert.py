#!/usr/bin/python

# convert.py

from __future__ import with_statement

import os.path
import sys
import sqlite3 as db

# set the python path:
python_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print "python_path", python_path

if sys.path[0] == '': sys.path[0] = python_path
else: sys.path.insert(0, python_path)

from ucc.word import word, questions, answers, xml_access, helpers

Types = {
    'address': questions.q_int,
    'data-direction-register-address': questions.q_int,
    'data-register-address': questions.q_int,
    'freq': questions.q_number,
    'input-pins-register-address': questions.q_int,
    'pin-number': questions.q_int,
    'use-pullup?': questions.q_bool,
    'use-pullups?': questions.q_bool,
}

# 'on-is' (3 questions, 3 answers)
# 'selected-pin-is' (1 question, 1 answer)
# 'syntax' should be repeatable (1 question, 1 answer)
# 'type' (for pwm) (1 question, 0 answers)

Series_names = {
    'input': ('translation', 'input'),
    'pin-number': ('pin mapping', 'pin-number'),
    'new syntax keyword': ('new syntax keyword', 'keyword name'),
}

def open_db(project_dir):
    global Db_conn, Db_cur
    Db_conn = db.connect(os.path.join(project_dir, 'python-avr.db'))
    Db_cur = Db_conn.cursor()

Question_qid = 1
Subquestion_qid = 2
Repeatable_qid = 3
Filename_suffix_qid = 4

def convert(project_dir):
    if project_dir[-1] in '/\\': project_dir = project_dir[:-1]
    open_db(project_dir)

    # Gather up the list of words:
    Db_cur.execute("select id, name, defining_word, kind from word")
    word_info = {}      # {id: word object}
    for word_id, name, defining, kind in Db_cur:
        word_info[word_id] = word.word(name, name, bool(defining), kind)

    # Gather up questions and filename suffixes:
    question_info = {}  # {id: [name, label, repeatable, parent, position,
                        #       word_id]}
    for word_id in word_info.iterkeys():
        if word_info[word_id].defining:
            Db_cur.execute(
              """select q.id, q.answer, repeatable.answer, q.parent, q.position
                   from answer as q inner join answer as repeatable
                     on q.id = repeatable.parent and repeatable.question_id = 3
                  where q.word_id = ? and q.question_id in (1,2)
                    and q.id not in (1,2,3)
              """, (word_id,))
            for id, name, repeatable, parent, position in Db_cur:
                question_info[id] = [helpers.legalize_name(name), name,
                                     repeatable.lower() == 'true',
                                     parent, position, word_id]
            Db_cur.execute(
              """select answer
                   from answer
                  where word_id = ? and question_id = 4
              """, (word_id,))
            row = Db_cur.fetchone()
            if row and row[0]: word_info[word_id].filename_suffix = row[0]
            else: word_info[word_id].filename_suffix = None

    # Fix name in words that python sees:
    for w in word_info.itervalues():
        if word_info[w.kind].filename_suffix == 'py':
            w.name = helpers.legalize_name(w.name)

    # Fix kind in words (word id => word name):
    for w in word_info.itervalues():
        w.kind_word = word_info[w.kind]
        w.kind = w.kind_word.name

    # Write out word list:
    package_name = os.path.basename(project_dir)
    xml_access.write_word_list(package_name,
                               [w.name for w in word_info.itervalues()],
                               project_dir)

    # Store questions in words:
    questions_by_word = {}  # {word_id: [question_id]}
    for id, (name, label, repeatable, parent, position, word_id) \
     in question_info.iteritems():
        questions_by_word.setdefault(word_id, []).append(id)
    for word_id, question_list in questions_by_word.iteritems():
        # Gather questions by parent:
        questions_by_parent = {}  # {qid: [children]}
        for qid in question_list:
            questions_by_parent.setdefault(question_info[qid][3], []) \
                               .append(qid)

        # Sort children by position:
        for l in questions_by_parent.itervalues():
            l.sort(key = lambda id: question_info[id][4])

        # This groups the parent and its children as a series.  Questions
        # without children are just simple q_strings.
        def create_question(id):
            name, label, repeatable, parent, position, word_id = \
              question_info[id]
            q_cls = Types.get(label, questions.q_string)
            if repeatable:
                this_q = q_cls(name, label, min = 0, orderable = True)
            elif label == 'filename suffix':
                this_q = q_cls(name, label, min = 0, max = 1)
            else:
                this_q = q_cls(name, label)
            this_q.qid = id
            if id not in questions_by_parent:
                return this_q

            print "series", label
            series_label, first_q_label = Series_names[label]
            series_name = helpers.legalize_name(series_label)

            subquestions = [this_q] + [create_question(child_id)
                                       for child_id in questions_by_parent[id]]
            this_q.label = first_q_label
            this_q.name = helpers.legalize_name(first_q_label)

            if repeatable:
                this_q.min = None
                this_q.orderable = None
                series = questions.q_series(series_name, series_label,
                                            subquestions = subquestions,
                                            min = 0, orderable = True)
            else:
                series = questions.q_series(series_name, series_label,
                                            subquestions = subquestions)
            series.qid = id
            return series
        word_info[word_id].questions = [create_question(id)
                                        for id in questions_by_parent[None]]

    # Gather up answers:
    for word_id in word_info.iterkeys():
        # Get the answers for this word:
        Db_cur.execute(
          """select id, question_id, answer, parent, position
               from answer
              where word_id = ? and question_id not in (1,2,3)
          """, (word_id,))
        answer_info = {}        # {id: [question_id, answer, parent, position]}
        answers_by_parent = {}  # {(parent, qid): [children]}
        for id, question_id, answer, parent, position in Db_cur:
            answer_info[id] = [question_id, answer, parent, position]
            answers_by_parent.setdefault((id, question_id), []).append(id)
            answers_by_parent.setdefault((parent, question_id), []).append(id)

        # Sort by position
        for l in answers_by_parent.itervalues():
            l.sort(key = lambda id: answer_info[id][3])

        w = word_info[word_id]

        def create_answer(parent_answer, question):
            if isinstance(question, questions.q_series):
                if question.is_repeatable():
                    a = []
                    for id in answers_by_parent.get((parent_answer,
                                                     question.qid),
                                                    ()):
                        a.append(answers.ans_series(question.name,
                                                    create_answers(id,
                                                      question.subquestions)))
                else:
                    ids = answers_by_parent.get((parent_answer, question.qid),
                                                ())
                    assert len(ids) <= 1, \
                           "non-repeating question, %s, " \
                           "has more than one answer in word %s" % \
                             (question.label, w.label)
                    if not ids:
                        assert question.is_optional(), \
                               "no answer for %s in word %s" % \
                                 (question.label, w.label)
                        a = None
                    else:
                        id = ids[0]
                        a = answers.ans_series(question.name,
                                               create_answers(id,
                                                 question.subquestions))
            else:
                if question.is_repeatable():
                    a = []
                    for id in answers_by_parent.get((parent_answer,
                                                     question.qid),
                                                    ()):
                        a.append(question.make_answer(answer_info[id][1]))
                else:
                    ids = answers_by_parent.get((parent_answer, question.qid),
                                                ())
                    assert len(ids) <= 1, \
                           "non-repeating question, %s, " \
                           "has more than one answer in word %s" % \
                             (question.label, w.label)
                    if ids and answer_info[ids[0]][1] is None:
                        print "deleting answer", answer_info[ids[0]]
                        ids = ()
                    if not ids:
                        assert question.is_optional(), \
                               "no answer for %s in word %s" % \
                                 (question.label, w.label)
                        a = None
                    else:
                        id = ids[0]
                        a = question.make_answer(answer_info[id][1])
            #if word_id == 30:
            #    print "create_answer returning", a
            return a

        def create_answers(parent_answer, question_list):
            #if word_id == 30:
            #    print "create_answers", parent_answer, question_list
            if not question_list:
                #if word_id == 30:
                #    print "create_answers => None"
                return None
            ans = dict((question.name, create_answer(parent_answer, question))
                       for question in question_list)
            #if word_id == 30:
            #    print "create_answers =>", ans
            return ans

        w.answers = create_answers(None, w.kind_word.questions)

    # Write words out:
    for w in word_info.itervalues():
        w.write_xml(project_dir)

if __name__ == "__main__":
    assert len(sys.argv) == 2, "usage: convert.py project_dir"
    convert(sys.argv[1])
