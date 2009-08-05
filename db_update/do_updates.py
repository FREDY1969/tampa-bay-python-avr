#!/usr/bin/env python

# do_updates.py db

from __future__ import with_statement
import sys
import os.path
import contextlib
import sqlite3 as db

Db_backups_dir = 'backups'

def get_backup_version(db_file):
    with open(os.path.join(os.path.split(db_file)[0],
                           Db_backups_dir,
                           'version')) \
      as f:
        return int(f.readline().strip())

def get_max_version(db_cur):
    db_cur.execute("""select max(version) from db_table""")
    return db_cur.fetchone()[0]

def run():
    global Backup_version, New_version

    if len(sys.argv) != 2:
        sys.stderr.write("usage: do_updates.py db\n")
        sys.exit(2)

    db_file = sys.argv[1]

    with contextlib.closing(db.connect(db_file)) as db_conn:
        with contextlib.closing(db_conn.cursor()) as db_cur: 
            Backup_version = get_backup_version(db_file)
            New_version = get_max_version(db_cur)
            db_cur.execute("""select new_table.python_update
                                from db_table as new_table
                               where new_table.version = ?
                                 and not exists(select id from db_table
                                                where id = new_table.id
                                                  and version = ?)
                                 and new_table.python_update is not null
                               order by new_table.table_order
                           """, (New_version, Backup_version))
            try:
                for python_update in db_cur.fetchall():
                    print "got:", python_update
                    exec python_update
            except Exception:
                db_conn.rollback()
                raise
            db_conn.commit()


if __name__ == "__main__":
    run()
