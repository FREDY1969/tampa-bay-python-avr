#!/usr/bin/env python

# create_tables.py db

r'''Create all the latest version of tables in the database listed in db_table.
'''

from __future__ import with_statement
import sys
import os.path
import contextlib
import sqlite3 as db

def get_backup_version(db_file):
    with open(os.path.join(os.path.split(db_file)[0], 'version')) as f:
        return int(f.readline().strip())

def get_max_version(db_cur):
    db_cur.execute("""select max(version) from db_table""")
    return db_cur.fetchone()[0]

def run():
    global New_version

    if len(sys.argv) != 2:
        sys.stderr.write("usage: create_tables.py db\n")
        sys.exit(2)

    db_file = sys.argv[1]

    with contextlib.closing(db.connect(db_file)) as db_conn:
        with contextlib.closing(db_conn.cursor()) as db_cur: 
            New_version = get_max_version(db_cur)
            db_cur.execute("""select id, table_name
                                from db_table
                               where version = ?
                               order by table_order
                           """, (New_version,))
            try:
                for id, table_name in db_cur.fetchall():
                    create_table(id, table_name, db_cur)
            except Exception:
                db_conn.rollback()
                raise
            db_conn.commit()

def create_table(id, table_name, db_cur):
    #print "create_table:", id, table_name
    db_cur.execute("""select col_name, definition
                        from db_column
                       where table_id = ? and version = ?
                       order by position
                   """, (id, New_version))
    lines = []
    for name, defn in db_cur:
        #print "name:", repr(name)
        #print "defn:", repr(defn)
        if name is not None:
            lines.append("    %s %s" % (name, defn))
        else:
            lines.append("    %s" % (defn,))
    cmd = "create table %s (\n%s\n)" % (table_name, ',\n'.join(lines))
    #print "cmd:", cmd
    db_cur.execute(cmd)


if __name__ == "__main__":
    run()
