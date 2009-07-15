#!/usr/bin/python

# tk_gui.py

from __future__ import with_statement

# This causes doctest program to fail...
#from __future__ import absolute_import

import setpath

import sys
import os.path
import contextlib
import functools
import subprocess

from Tkinter import *
import tkFont
import Pmw
import sqlite3 as db

debug = 1

db_filename = 'python-avr.db'

class App(object):
    def __init__(self):
        self.root = Tk()

        menubar = Menu(self.root)
        menubar.add_command(label="New Word", command=self.new)
        menubar.add_command(label="Save", command=self.save)
        menubar.add_command(label="Edit", command=self.edit)
        menubar.add_command(label="Quit", command=self.root.quit)

        self.root.config(menu=menubar)

        vert_pane = Pmw.PanedWidget(self.root, orient='horizontal',
                                    hull_width=1200,
                                    hull_height=900)
        vert_pane.pack(expand=1, fill='both')
        vert_pane.add('word-list', min=200)
        db_cur.execute("select name, id from word")
        self.words = dict(db_cur)
        self.words_by_id = dict(zip(self.words.itervalues(),
                                    self.words.iterkeys()))
        word_list = sorted(self.words.keys(), key=lambda x: x.lower())
        if debug: print "word_list:", word_list
        self.word_list = Pmw.ScrolledListBox(vert_pane.pane('word-list'),
                                             items=word_list,
                                             labelpos='nw',
                                             label_text="Words",
                                             label_font=
                                               tkFont.Font(size=14,
                                                           weight='bold'),
                                             label_pady=5,
                                             selectioncommand=self.select_word,
                                             usehullsize=1)
        self.word_list.pack(expand=1, fill='both')
        self.word_list.setvalue(word_list[0].encode())
        vert_pane.add('word-view')

        horz_pane = Pmw.PanedWidget(vert_pane.pane('word-view'),
                                    orient='vertical')
        horz_pane.pack(expand=1, fill='both')
        horz_pane.add('questions', min=320)
        self.question_pane = Pmw.ScrolledFrame(horz_pane.pane('questions'),
                                               horizflex='elastic',
                                               hscrollmode='none',
                                               labelpos='n',
                                               vertflex='expand',
                                               vertfraction=0.15,
                                               usehullsize=1)
        self.question_pane.pack(expand=1, fill='both')

        horz_pane.add('file-text')
        self.word_body = Pmw.ScrolledText(horz_pane.pane('file-text'),
                                          usehullsize=1)
        self.word_body.pack(expand=1, fill='both')

    def new(self):
        new_word(app.root)

    def add_word(self, name, id):
        assert name not in self.words, "Duplicate word name: " + name
        self.word_list.setlist(sorted((name,) + self.word_list.get(),
                                      key=lambda x: x.lower()))
        self.words[name] = id
        self.word_list.setvalue(name)

    def edit(self):
        if self.selected_word.filename:
            #subprocess.check_call(('gvim', '-f', self.selected_word.filename),
            subprocess.check_call(('gedit', self.selected_word.filename),
                                  close_fds=True)
            with open(self.selected_word.filename) as f:
                self.selected_word.file_contents = f.read()
            self.word_body.setvalue(self.selected_word.file_contents)

    def save(self):
        self.selected_word.save()

    def cur_word(self):
        return self.word_list.getvalue()[0]

    def select_word(self):
        word_name = self.cur_word()
        self.selected_word = word.from_db(self.words[word_name])
        self.selected_word.display()

    def run(self):
        self.root.mainloop()

class new_word(object):
    def __init__(self, parent, **kws):
        self.top = Toplevel(parent, height=200, takefocus=True, width=250)
        self.top.title("New Word")
        self.top.transient(app.root)

        frame = Frame(self.top)
        frame.grid(row=1, column=1, columnspan=3, sticky=N+S+E+W)

        db_cur.execute("""select name, id from word where defining_word = 1""")
        self.kinds = dict(db_cur)

        self.kind = Pmw.ComboBox(frame, labelpos='w', label_text="Kind of Word",
                                 scrolledlist_items=sorted(self.kinds.keys()))
        self.kind.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

        Label(frame, anchor='w', text="Name").grid(row=2, column=1, pady=5)
        self.name = Entry(frame)
        self.name.grid(row=2, column=2, sticky=E+W, padx=5)

        Button(self.top, anchor=CENTER, text="Ok", command=self.ok) \
          .grid(row=2, column=1, pady=5)
        Button(self.top, anchor=CENTER, text="Apply", command=self.apply) \
          .grid(row=2, column=2)
        Button(self.top, anchor=CENTER, text="Cancel", command=self.cancel) \
          .grid(row=2, column=3)

    def cancel(self):
        self.top.destroy()

    def apply(self):
        try:
            name = self.name.get()
            kind_id = self.kinds[self.kind.get()]
            if debug: print "new_word:", name, kind_id
            assert name not in app.words, "Duplicate word name: " + name
            db_cur.execute("""insert into word (name, kind, defining_word)
                              values (?, ?, ?)
                           """, (name, kind_id, kind_id == 1))
            if debug > 2: print "new_word: lastrowid", db_cur.lastrowid
            id = db_cur.lastrowid
            create_answers(kind_id, id)
        except Exception:
            db_conn.rollback()
            raise
        db_conn.commit()
        app.add_word(name, id)

    def ok(self):
        self.apply()
        app.select_word()
        self.cancel()


class word(object):
    def __init__(self, id, name, kind, defining_word):
        self.id = id
        self.name = name
        self.kind = kind
        self.kind_name = app.words_by_id[kind]
        self.defining_word = defining_word
        self.read_suffix()

    def __repr__(self):
        return "<word %s>" % self.name

    def read_suffix(self):
        db_cur.execute("""select answer 
                          from answer
                          where word_id = ? and question_id = ?
                       """, (self.kind, filename_suffix_qid))
        filename_suffix = db_cur.fetchone()[0]
        if filename_suffix:
            self.filename = os.path.join(dir, '.'.join((self.name,
                                                        filename_suffix)))
            if not os.path.exists(self.filename):
                open(self.filename, 'w').close()
        else:
            self.filename = ''

    def get_answers(self):
        self.answers = get_answers(self, self.kind)

    @classmethod
    def from_db(cls, id):
        if debug: print "word.from_db: id", repr(id)
        db_cur.execute("""select name, kind, defining_word
                            from word
                          where id = ?
                       """, (id,))
        name, kind, defining_word = db_cur.fetchone()
        ans = cls(id, name, kind, defining_word)
        if ans.filename:
            with open(ans.filename) as f:
                ans.file_contents = f.read()
        ans.get_answers()
        return ans

    def display(self):
        app.question_pane.configure(label_text="%s: %s [%s]" %
                                                 (self.kind_name,
                                                  self.name,
                                                  self.id),
                                    label_font=
                                      tkFont.Font(size=14, weight='bold'),
                                    label_pady=5)
        for w in app.question_pane.interior().grid_slaves():
            if debug > 2: print "word.display: destroying", w
            w.destroy()
        answer.display_list(self.answers)
        app.question_pane.reposition()
        if self.filename:
            app.word_body.setvalue(self.file_contents)
        else:
            app.word_body.clear()

    def save(self):
        try:
            for a in self.answers: a.save()
            if self.filename:
                app.word_body.exportfile(self.filename)
                self.file_contents = app.word_body.get()
        except Exception:
            db_conn.rollback()
            raise
        db_conn.commit()

    def changed(self):
        return self.filename and self.file_contents != app.word_body.get()


def pairs(it):
    r'''Yields sliding pairs of items from it iterable.

    >>> list(pairs(()))
    []
    >>> list(pairs((1,)))
    [(1, None)]
    >>> list(pairs((1,2,3)))
    [(1, 2), (2, 3), (3, None)]
    '''
    it = iter(it)
    last = it.next()
    for x in it:
        yield last, x
        last = x
    yield last, None

class placeholder(object):
    def __init__(self, the_word, parent, question_id, qid_for_children,
                 question_text):
        self.the_word = the_word
        self.parent = parent
        self.question_id = question_id
        self.qid_for_children = qid_for_children
        self.question_text = question_text
        self.repeatable = True

    def __repr__(self):
        return "<placeholder %s.%s>" % (self.the_word.name, self.question_text)

    def display(self, indent, row, next):
        frame = app.question_pane.interior()
        Button(frame, anchor=W,
               text=' ' * (indent - 1) + "Add " + self.question_text,
               padx=3, pady=0, command=self.add) \
          .grid(row=row, column=2, sticky=W)
        return row + 1

    def add(self):
        if self.parent:
            db_cur.execute("""select max(position)
                                from answer
                               where answer.parent = ?
                                 and answer.word_id = ?
                                 and answer.question_id = ?
                           """, (self.parent, self.the_word.id,
                                 self.question_id))
        else:
            db_cur.execute("""select max(position)
                                from answer
                               where answer.parent is null
                                 and answer.word_id = ?
                                 and answer.question_id = ?
                           """, (self.the_word.id, self.question_id))
        row = db_cur.fetchone()
        if row and row[0]:
            last_position = row[0]
        else:
            last_position = 0
        if debug: print "answer.add: last_position %s" % last_position
        create_subanswers(self.the_word.id, self.parent, self.question_id,
                          self.qid_for_children, self.question_text,
                          'False', last_position + 1)
        db_conn.commit()
        self.the_word.get_answers()
        self.the_word.display()

    def delete2(self):
        pass

    def save(self):
        pass


class answer(placeholder):
    def __init__(self, the_word, parent, id, question_id, qid_for_children,
                 question_text, text, position):
        super(answer, self).__init__(the_word, parent, question_id,
                                     qid_for_children, question_text)
        self.id = id
        self.text = text
        self.position = position
        with contextlib.closing(db_conn.cursor()) as cur:
            cur.execute("""select answer from answer
                            where question_id = ? and parent = ?
                        """, (repeatable_qid, qid_for_children,))
            self.repeatable = cur.fetchone()[0] == 'True'
            if debug > 1:
                print "answer: question_text", question_text, \
                      "repeatable", self.repeatable

    def __repr__(self):
        return "<answer %s.%s[%s] = %r>" % \
                 (self.the_word.name, self.question_text, self.position,
                  self.text)

    @classmethod
    def from_db(cls, the_word, parent, id, question_id, qid_for_children,
                question_text, repeatable, text, position):
        if debug:
            print "answer.from_db: the_word %s, parent %s, id %s, " \
                  "question_id %s," % \
                    (the_word, parent, id, question_id)
            print "                qid_for_children %s, question_text %s," % \
                    (qid_for_children, question_text)
            print "                repeatable %s, text %r, position %s" % \
                    (repeatable, text, position)

        if id is None:
            if repeatable == 'True':
                return placeholder(the_word, parent, question_id,
                                   qid_for_children, question_text)
            else:
                raise AssertionError("unanswered non-repeatable question: " +
                                       question_text)

        if text is None: text = ''
        ans = cls(the_word, parent, id, question_id, qid_for_children,
                  question_text, text, position)
        if question_id in (question_qid, subquestion_qid) and text.isdigit():
            ans.children = ()
        else:
            with contextlib.closing(db_conn.cursor()) as cur:
                cur.execute("""select answer.id, 
                                      question.id,
                                      ifnull(meta.id, question.id),
                                      ifnull(meta.answer, question.answer),
                                      repeatable.answer,
                                      answer.answer,
                                      answer.position
                                 from answer as question left outer join answer
                                   on question.id = answer.question_id
                                      and answer.parent = ?
                                      left outer join answer as meta
                                   on cast(question.answer as int) = meta.id
                                      inner join answer as repeatable
                                   on ifnull(meta.id, question.id) =
                                        repeatable.parent
                                where question.parent = ?
                                  and repeatable.question_id = ?
                                order by question.position, answer.position
                            """, (id, qid_for_children, repeatable_qid))
                ans.children = tuple(map(lambda row:
                                           answer.from_db(the_word, id, *row),
                                         debug_iter(cur, "answer.from_db")))
        return ans

    @staticmethod
    def display_list(l, indent = 0, row = 0):
        for a, next in pairs(l):
            row = a.display(indent, row, next)
        return row

    def display(self, indent, row, next):
        frame = app.question_pane.interior()
        #frame.columnconfigure(2, weight=2)
        frame.columnconfigure(4, weight=5)
        if self.repeatable:
            Button(frame, anchor=CENTER, text="Del", padx=3, pady=0,
                   command=self.delete) \
              .grid(row=row, column=1, sticky=E+W)
            if next and self.question_id == next.question_id:
                Button(frame, anchor=CENTER, text="Move Down", padx=3, pady=0,
                       command=functools.partial(self.move_down, next)) \
                  .grid(row=row, column=3, sticky=E+W)
        Label(frame, text=' ' * indent + self.question_text, anchor=W) \
          .grid(row=row, column=2, sticky=E+W)
        self.entry = Entry(frame, width=40)
        self.entry.insert(END, self.text)
        self.entry.grid(row=row, column=4, sticky=E+W)
        self.entry.bind("<FocusOut>", self.check_entry)
        Label(frame, text=str(self.id), justify=RIGHT) \
          .grid(row=row, column=5, sticky=E+W)
        row = answer.display_list(self.children, indent + 4, row + 1)
        if self.repeatable and \
           (not next or self.question_id != next.question_id):
            Button(frame, anchor=W,
                   text=' ' * (indent - 1) + "Add " + self.question_text,
                   padx=3, pady=0, command=self.add) \
              .grid(row=row, column=2, sticky=W)
            return row + 1
        return row

    def delete(self):
        self.delete2()
        db_conn.commit()
        self.the_word.get_answers()
        self.the_word.display()

    def delete2(self):
        if debug: print "deleting answer", self.id
        db_cur.execute("""delete from answer where id = ?""", (self.id,))
        for child in self.children:
            child.delete2()

    def move_down(self, next):
        assert self.question_id == next.question_id, \
               "bogus next to move_down: I'm %s, next is %s" % \
                 (self.question_id, next.question_id)
        assert self.parent == next.parent, \
               "bogus next to move_down: " \
               "my parent is %s, next's parent is %s" % \
                 (self.parent, next.parent)
        if debug:
            print "setting answer[%s].position = %s" % (self.id, next.position)
        db_cur.execute("""update answer set position = ? where id = ?""",
                       (next.position, self.id))
        if debug:
            print "setting answer[%s].position = %s" % (next.id, self.position)
        db_cur.execute("""update answer set position = ? where id = ?""",
                       (self.position, next.id))
        db_conn.commit()
        self.the_word.get_answers()
        self.the_word.display()

    def check_entry(self, *args):
        if self.entry.get() != self.text:
            try:
                self.save()
            except Exception:
                db_conn.rollback()
                raise
            db_conn.commit()

    def save(self):
        cur_text = self.entry.get()
        if cur_text != self.text:
            self.text = cur_text
            db_cur.execute("""update answer set answer = ? where id = ?""",
                           (cur_text or None, self.id))

def debug_iter(it, msg):
    if debug: print "debug_iter:", msg
    for x in it:
        if debug: print "debug_iter:", x
        yield x
    if debug: print "debug_iter: done"

def get_answers(the_word, kind):
    db_cur.execute("""select answer.id,
                             question.id,
                             ifnull(meta.id, question.id),
                             ifnull(meta.answer, question.answer),
                             repeatable.answer,
                             answer.answer,
                             answer.position
                        from answer as question left outer join answer
                          on question.id = answer.question_id
                             and answer.word_id = ?
                             left outer join answer as meta
                          on cast(question.answer as int) = meta.id
                             inner join answer as repeatable
                          on ifnull(meta.id, question.id) = repeatable.parent
                       where question.word_id = ? and question.parent is null
                         and repeatable.question_id = ?
                       order by question.position, answer.position
                   """, (the_word.id, kind, repeatable_qid))
    return tuple(map(lambda row: answer.from_db(the_word, None, *row),
                     debug_iter(db_cur, "get_answers")))

def create_answers(kind, word_id):
    db_cur.execute("""select answer.id, ifnull(meta.id, answer.id),
                             answer.answer, repeatable.answer, answer.position
                      from answer left outer join answer as meta
                        on cast(answer.answer as int) = meta.id
                           inner join answer as repeatable
                        on ifnull(meta.id, answer.id) = repeatable.parent
                      where answer.word_id = ? and answer.parent is null
                        and repeatable.question_id = ?
                      order by answer.position
                   """, (kind, repeatable_qid))
    for row in debug_iter(db_cur, "create_answers"):
        create_subanswers(word_id, None, *row)

def create_subanswers(word_id, parent, question_id, qid_for_children,
                      question_text, repeatable, position):
    if debug:
        print "create_subanswers: word_id %s, parent %s, question_id %s," % \
                (word_id, parent, question_id)
        print "                   qid_for_children %s, question_text %s," % \
                (qid_for_children, question_text)
        print "                   repeatable %s, position %s" % \
                (repeatable, position)
    if repeatable == 'True': return 
    with contextlib.closing(db_conn.cursor()) as cur:
        cur.execute("""insert into answer (question_id, parent, position,
                                           word_id)
                       values (?, ?, ?, ?)
                    """, (question_id, parent, position, word_id))
        id = cur.lastrowid
        if debug: print "create_subanswers inserted", id
        cur.execute("""select answer.id,
                              ifnull(meta.id, answer.id),
                              ifnull(meta.answer, answer.answer),
                              repeatable.answer,
                              answer.position
                       from answer left outer join answer as meta
                         on cast(answer.answer as int) = meta.id
                            inner join answer as repeatable
                         on ifnull(meta.id, answer.id) = repeatable.parent
                       where answer.parent = ?
                         and answer.question_id in (?, ?)
                         and repeatable.question_id = ?
                       order by answer.position
                    """, (qid_for_children, question_id, subquestion_qid,
                          repeatable_qid))
        for row in debug_iter(cur, "create_subanswers"):
            create_subanswers(word_id, id, *row)


def run():
    global dir, db_conn, db_cur, question_qid, repeatable_qid, subquestion_qid
    global filename_suffix_qid, app

    if len(sys.argv) != 2:
        sys.stderr.write("usage: tk_gui directory\n")
        sys.exit(2)

    dir = sys.argv[1]

    with contextlib.closing(db.connect(os.path.join(dir, db_filename))) \
      as db_conn:
        with contextlib.closing(db_conn.cursor()) as db_cur:
            db_cur.execute("""select id, answer
                              from answer
                              where word_id = 1 and question_id in (1, 2)
                              order by id
                           """)
            question_qid = repeatable_qid = subquestion_qid = \
              filename_suffix_qid = None
            for id, question in db_cur:
                if debug:
                    print "run: loading qids: id", id, "question", question
                if question == 'question':
                    question_qid = id
                elif question == 'repeatable':
                    repeatable_qid = id
                elif question.isdigit() and int(question) == question_qid:
                    subquestion_qid = id
                elif question == 'filename suffix':
                    filename_suffix_qid = id
            assert question_qid, \
                   "failed to find the 'question' compiler question"
            assert repeatable_qid, \
                   "failed to find the 'repeatable' compiler question"
            assert subquestion_qid, \
                   "failed to find the 'subquestion' compiler question"
            assert filename_suffix_qid, \
                   "failed to find the 'filename suffix' compiler question"
            if debug: print "question_qid:", question_qid
            if debug: print "repeatable_qid:", repeatable_qid
            if debug: print "subquestion_qid:", subquestion_qid
            if debug: print "filename_suffix_qid:", filename_suffix_qid
            app = App()
            app.select_word()
            app.run()

if __name__ == '__main__':
    run()
