#!/usr/bin/python

# parse.py

from __future__ import with_statement

import sys
import os.path
import sqlite3 as db

db_filename = 'ast.db'

sys.path[0] = os.path.abspath(os.path.join('..', '..',
                                           os.path.dirname(__file__)))
                                           #print "sys.path:", sys.path

from ucc.parser import parser, scanner, parser_init

def usage():
    sys.stderr.write("usage: parse.py file\n")
    sys.exit(2)

def run():
    if len(sys.argv) != 2: usage()

    ast = parser_init.parse(parser, scanner, sys.argv[1], debug = 0,
                            extra_arg = parser.token_dict)
    if ast:
        name, ext = os.path.splitext(os.path.basename(sys.argv[1]))
        assert ext == '.ucl', "unknown file extension on: " + sys.argv[1]
        ast.word = name
        ast.str = sys.argv[1]

        if not os.path.exists(db_filename):
            db_conn = db.connect(db_filename)
            db_cur = db_conn.cursor()
            with open("../ast/schema.ddl") as f:
                commands = f.read().split(';')
            for command in commands:
                db_cur.execute(command)
            db_conn.commit()
            db_conn.close()

        db_conn = db.connect(db_filename)
        try:
            ast.insert(db_conn)
            db_conn.commit()
        except Exception:
            db_conn.rollback()
            raise

if __name__ == "__main__":
    run()

