#!/usr/bin/env python

# dump.py (project_dir | file.ucl)\n")

r'''Dumps the ast database in a simple ascii format.

id: label word kind int1 int2 str1 str2 expect type_id
  - child1
  - child2.1
    child2.2
  < node replaced

'''

from __future__ import with_statement

import itertools
import os.path
import sqlite3 as db

Db_filename = "ucl.db"

class db_cursor(object):
    def __init__(self, project_dir):
        self.project_dir = project_dir
    def __enter__(self):
        self.db_conn = db.connect(os.path.join(self.project_dir, Db_filename))
        self.db_cur = self.db_conn.cursor()
        return self.db_cur
    def __exit__(self, exc_type, exc_value, exc_tb):
        #print "closing db connection"
        self.db_cur.close()
        self.db_conn.close()

def dump(db_cur):
    db_cur.execute("""select id from ast
                       where word_body_id is null
                       order by word""")
    for id, in db_cur.fetchall():
        print
        dump_word(id, db_cur)

def dump_word(id, db_cur, indent = ''):
    db_cur.execute("""
        select label, word, kind, int1, int2, str1, str2, expect, type_id
          from ast
         where id = ?
        """,
        (id,))
    row = db_cur.fetchone()
    label, word, kind, int1, int2, str1, str2, expect, type_id = row
    print indent + str(id) + ":", \
          ' '.join(itertools.imap(str, filter(lambda x: x is not None,
                                              (label, word, kind,
                                               int1, int2, str1, str2,
                                               expect, type_id))))

    # Do children:
    db_cur.execute("""
        select id, parent_arg_num, arg_order
          from ast
         where parent_node = ?
         order by parent_arg_num, arg_order""",
        (id,))
    last_parent_arg_num = None
    hold_id = None
    first_child = True
    if not indent: indent = '  '
    else: indent = ' ' * len(indent)
    def dump_child(child_id):
        dump_word(child_id, db_cur, indent = (indent + '- ' if first_child
                                                            else indent + '  '))
    for child_id, parent_arg_num, arg_order in db_cur.fetchall():
        if parent_arg_num == last_parent_arg_num:
            assert hold_id is not None
            dump_child(hold_id)
            hold_id = child_id
            first_child = False
        else:
            last_parent_arg_num = parent_arg_num
            if hold_id is not None:
                dump_child(hold_id)
            hold_id = child_id
            first_child = True
    if hold_id is not None:
        dump_child(hold_id)


if __name__ == "__main__":
    import sys

    def usage():
        sys.stderr.write("usage: dump.py (project_dir | file.ucl)\n")
        sys.exit(2)

    len(sys.argv) == 2 or usage()

    if sys.argv[1].lower().endswith('.ucl'):
        project_dir, file = os.path.split(sys.argv[1])
        with db_cursor(project_dir) as db_cur:
            db_cur.execute("""select id
                                from ast
                               where kind = 'word_body' and word = ?
                           """,
                           (file[:-4],))
            dump_word(db_cur.fetchone()[0], db_cur)
    else:
        with db_cursor(sys.argv[1]) as db_cur:
            dump(db_cur)
