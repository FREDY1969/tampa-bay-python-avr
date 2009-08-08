#!/usr/bin/python

# dump.py

r'''Dumps the ast database in a simple ascii format.

id: label word kind int1 int2 str1 str2 expect type_id
  - child1
  - child2.1
    child2.2
  < node replaced

'''

from __future__ import with_statement

import itertools
import contextlib
import os.path
import sqlite3 as db

Db_filename = "ast.db"

def dump(project_dir):
    with contextlib.closing(db.connect(os.path.join(project_dir,
                                                    Db_filename))) \
      as db_conn:
        with contextlib.closing(db_conn.cursor()) as db_cur:
            db_cur.execute("""select id from ast
                               where word_body_id is null
                               order by word""")
            for id, in db_cur.fetchall():
                print
                dump_word(id, db_cur)

def dump_word(id, db_cur, indent = ''):
    db_cur.execute("""
        select id, label, word, kind, int1, int2, str1, str2, expect, type_id,
               id_replaced
        from ast
        where root_id_replaced = ?
          and replacement_depth = (select max(replacement_depth) from ast
                                    where root_id_replaced = ?)
        """,
        (id, id))
    row = db_cur.fetchone()
    if not row:
        db_cur.execute("""
            select id, label, word, kind, int1, int2, str1, str2, expect,
                   type_id, NULL
            from ast
            where id = ?
        """,
        (id,))
        row = db_cur.fetchone()
    id, label, word, kind, int1, int2, str1, str2, \
      expect, type_id, id_replaced = row
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

    # Do node replaced:
    if id_replaced is not None:
        dump_word(id_replaced, db_cur, indent + '< ')

if __name__ == "__main__":
    import sys

    def usage():
        sys.stderr.write("usage: dump.py project_dir\n")
        sys.exit(2)

    len(sys.argv) == 2 or usage()

    dump(sys.argv[1])
