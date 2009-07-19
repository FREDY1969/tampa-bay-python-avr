#!/usr/bin/env python

# load_table.py [-i] db cols_file...

from __future__ import with_statement
import sys
import os.path
import contextlib
import sqlite3 as db

Db_backup_dir = 'backups'

def get_backup_version(db_file):
    with open(os.path.join(os.path.split(db_file)[0],
                           Db_backup_dir,
                           'version')) \
      as f:
        return int(f.readline().strip())

def get_max_version(db_cur):
    db_cur.execute("""select max(version) from db_table""")
    return db_cur.fetchone()[0]

def run():
    global Backup_version, New_version

    if len(sys.argv) < 3:
        sys.stderr.write("usage: load_table.py db cols_file...\n")
        sys.exit(2)

    db_file = sys.argv[1]
    cols_files = sys.argv[2:]

    with contextlib.closing(db.connect(db_file)) as db_conn:
        with contextlib.closing(db_conn.cursor()) as db_cur: 
            Backup_version = get_backup_version(db_file)
            New_version = get_max_version(db_cur)
            db_cur.execute("""select table_name, table_order from db_table
                               where version = ?
                               order by table_order
                           """, (New_version,))
            order_dict = dict(db_cur)
            cols_files.sort(key=lambda cols_file:
                                   order_dict[get_table_name(cols_file)])
            try:
                for cols_file in cols_files:
                    load_file(cols_file, db_cur)
            except Exception:
                db_conn.rollback()
                raise
            db_conn.commit()

def get_table_name(cols_file):
    return os.path.split(cols_file)[1][:-5]

def load_file(cols_file, db_cur):
    with open(cols_file) as f:
        old_table_name = get_table_name(cols_file)

        print "old_table_name:", old_table_name, \
              "Backup_version:", Backup_version

        db_cur.execute("""select id from db_table
                           where table_name = ? and version = ?
                       """, (old_table_name, Backup_version))
        table_id = db_cur.fetchone()[0]
        db_cur.execute("""select table_name from db_table
                           where id = ? and version = ?
                       """, (table_id, New_version))
        new_table_name = db_cur.fetchone()[0]
        print "new_table_name:", new_table_name

        db_cur.execute("""select id, col_name from db_column
                           where table_id = ? and version = ?
                             and col_name is not null
                           order by position
                       """, (table_id, Backup_version))
        old_col_map = dict(db_cur)      # {id: col_name}
        old_col_names = old_col_map.values()
        print "old_col_names:", old_col_names

        db_cur.execute("""select id, col_name, python_default from db_column
                           where table_id = ? and version = ?
                             and col_name is not null
                           order by position
                       """, (table_id, New_version))
        new_col_names = []
        col_name_map = {}   # old: new
        defaults = {}       # new_col_name: python_default
        for id, new_name, python_default in db_cur:
            new_col_names.append(new_name)
            if id in old_col_map:
                old_name = old_col_map[id]
                col_name_map[old_name] = new_name
            elif python_default is not None:
                print "%s.python_default:" % new_name, repr(python_default)
                defaults[new_name] = python_default

        print "new_col_names:", new_col_names
        print "col_name_map:", col_name_map
        print "defaults:", defaults

        f_iter = iter(f)
        for line in f_iter:
            if line.startswith('-----'):
                assert f_iter.next().strip() == '', \
                       'expected blank link after ----- record delimiter'
            row = {}
            ncols = 0
            for line in f_iter:
                col_info = line.rstrip('\r\n').split('\t')
                print "col_info:", col_info
                assert len(col_info) == 2, \
                       "expected: 'col_name\tvalue\n'; got: " + line
                assert f_iter.next().strip() == '', \
                       'expected blank link after column ' + col_info[0]
                row[col_info[0]] = eval(col_info[1])
                ncols += 1
                if ncols == len(old_col_names): break

            new_row = dict((col_name_map[old_name], row[old_name])
                           for old_name in col_name_map.keys())

            for name, code in defaults.iteritems():
                context = {'name': name,
                           'old_row': row,
                           'new_row': new_row,
                           'db_cur': db_cur,
                           'default': None,
                          }
                print "exec", repr(code)
                exec code in context
                print "exec got:", context['default']
                new_row[name] = context['default']
            print "inserting into", new_table_name
            db_cur.execute("""insert into %s (%s) values (%s)""" % 
                             (new_table_name, ', '.join(new_col_names),
                              ', '.join('?' * len(new_col_names))),
                           tuple(new_row[name] for name in new_col_names))


if __name__ == "__main__":
    run()
