#!/usr/bin/python

# dump.py (package_dir | file.ucl)\n")

r'''Dumps the ast database in a simple ascii format.

id: name(kind) from source_filename
  id: label symbol_id kind int1 int2 str1 str2 expect type_id
    - child1
    - child2.1
    . child2.2
    < node replaced

'''

from __future__ import with_statement

import itertools
import os.path
import sqlite3 as db

Db_filename = "ucl.db"

class db_cursor(object):
    def __init__(self, package_dir):
        self.package_dir = package_dir
    def __enter__(self):
        self.db_conn = db.connect(os.path.join(self.package_dir, Db_filename))
        self.db_cur = self.db_conn.cursor()
        return self.db_cur
    def __exit__(self, exc_type, exc_value, exc_tb):
        #print "closing db connection"
        self.db_cur.close()
        self.db_conn.close()

def dump(db_cur):
    db_cur.execute("""select id, label, kind, source_filename from symbol_table
                       where context is null
                       order by label""")
    for info in db_cur.fetchall():
        print
        dump_word(info, db_cur)

def dump_word(info, db_cur):
    print "%d: %s(%s) from %s" % info
    dump_children(db_cur, info[0], indent = '  ')

def dump_node(word_symbol_id, id, db_cur, indent = ''):
    db_cur.execute("""
        select label, symbol_id, kind, int1, int2, str1, str2, expect, type_id
          from ast
         where id = ?
        """,
        (id,))
    row = db_cur.fetchone()
    label, symbol_id, kind, int1, int2, str1, str2, expect, type_id = row
    print indent + str(id) + ":", \
          ' '.join(itertools.imap(str, filter(lambda x: x is not None,
                                              (label, symbol_id, kind,
                                               int1, int2, str1, str2,
                                               expect, type_id))))
    dump_children(db_cur, word_symbol_id, id, indent)

def dump_children(db_cur, word_symbol_id, parent_id = None, indent = ''):
    # Do children:
    if parent_id is None:
        db_cur.execute("""
            select id, parent_arg_num, arg_order
              from ast
             where word_symbol_id = ? and parent_node is null
             order by parent_arg_num, arg_order""",
            (word_symbol_id,))
    else:
        db_cur.execute("""
            select id, parent_arg_num, arg_order
              from ast
             where word_symbol_id = ? and parent_node = ?
             order by parent_arg_num, arg_order""",
            (word_symbol_id, parent_id))
    last_parent_arg_num = None
    hold_id = None
    first_child = True
    if not indent: indent = '  '
    else: indent = ' ' * len(indent)
    def dump_child(child_id):
        dump_node(word_symbol_id, child_id, db_cur,
                  indent = (indent + '- ' if first_child
                                          else indent + '+ '))
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
        sys.stderr.write("usage: dump.py (package_dir | file.ucl)\n")
        sys.exit(2)

    len(sys.argv) == 2 or usage()

    if sys.argv[1].lower().endswith('.ucl'):
        package_dir, file = os.path.split(sys.argv[1])
        with db_cursor(package_dir) as db_cur:
            db_cur.execute("""select id, label, kind, source_filename
                                from symbol_table
                               where context is null and label = ?
                           """,
                           (file[:-4],))
            dump_word(db_cur.fetchone(), db_cur)
    else:
        with db_cursor(sys.argv[1]) as db_cur:
            dump(db_cur)
