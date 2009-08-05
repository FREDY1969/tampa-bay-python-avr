#!/usr/bin/env python

# backup.py db

from __future__ import with_statement
import sys
import os.path
import contextlib
import sqlite3 as db

db_backup_dir = 'backups'

def get_max_version(db_cur):
    db_cur.execute("""select max(version) from db_table""")
    return db_cur.fetchone()[0]

def run():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: backup.py db\n")
        sys.exit(2)
    db_file = sys.argv[1]
    dir = os.path.split(db_file)[0]
    if dir == '': dir = '.'
    dir = os.path.join(dir, db_backup_dir)
    with contextlib.closing(db.connect(db_file)) as db_conn:
        with contextlib.closing(db_conn.cursor()) as db_cur: 
            version = get_max_version(db_cur)
            with open(os.path.join(dir, 'version'), 'w') as f:
                f.write("%s\n" % version)
            db_cur.execute("""select id, table_name from db_table
                              where version = ?
                           """, (version,))
            for id, table_name in db_cur.fetchall():
                backup(id, dir, table_name, version, db_cur)

def backup(id, dir, table_name, version, db_cur):
    db_cur.execute("""select col_name
                        from db_column
                       where col_name is not null
                         and table_id = ?
                         and version = ?
                       order by position
                   """, (id, version))
    col_names = map(lambda x: x[0], db_cur.fetchall())
    with open(os.path.join(dir, table_name + '.cols'), 'w') as f:
        tail = ''
        if 'fixed_data' in col_names: tail += " where fixed_data = 0"
        if 'id' in col_names: tail += " order by id"
        db_cur.execute("""select %s from %s%s""" % (', '.join(col_names),
                                                    table_name, tail))
        for row in db_cur:
            f.write("----------------\n\n")
            for col, data in zip(col_names, row):
                f.write("%s\t%s\n\n" % (col, repr(data)))


if __name__ == "__main__":
    run()
