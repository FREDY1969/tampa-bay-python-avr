#!/usr/bin/env python

# import_tables.py [-i] db csv_file...

from __future__ import with_statement
import sys
import os.path
import contextlib
import sqlite3 as db

def get_max_version(db_cur):
    db_cur.execute("""select max(version) from db_table""")
    return db_cur.fetchone()[0]

def run():
    global New_version
    if len(sys.argv) < 3:
        sys.stderr.write("usage: import_tables.py db csv_file...\n")
        sys.exit(2)
    db_file = sys.argv[1]
    csv_files = sys.argv[2:]

    with contextlib.closing(db.connect(db_file)) as db_conn:
        with contextlib.closing(db_conn.cursor()) as db_cur: 
            New_version = get_max_version(db_cur)
            db_cur.execute("""select table_name, table_order from db_table
                               where version = ?
                               order by table_order
                           """, (New_version,))
            order_dict = dict(db_cur)
            order_dict['db_table'] = -2
            order_dict['db_column'] = -1
            csv_files.sort(key=lambda csv_file:
                                   order_dict[get_table_name(csv_file)])
            try:
                for csv_file in csv_files:
                    import_file(csv_file, db_cur)
            except Exception:
                db_conn.rollback()
                raise
            db_conn.commit()

def get_table_name(csv_file):
    return os.path.split(csv_file)[1][:-4]

def import_file(csv_file, db_cur):
    with open(csv_file) as f:
        table_name = get_table_name(csv_file)
        col_names = f.readline().split('\t')

        for line in f:
            row = [(None if col == '' else col)
                   for col in line.rstrip('\r\n').split('\t')]
            #print "row:", row
            db_cur.execute("""insert into %s (%s) values (%s)""" % 
                             (table_name, ', '.join(col_names),
                              ', '.join('?' * len(col_names))),
                           row)


if __name__ == "__main__":
    run()
