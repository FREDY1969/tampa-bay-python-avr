#!/usr/bin/python

# dump_asm.py (package_dir | file.ucl | file.asm)\n")

r'''Dumps the assembler source database in a simple ascii format.

id: label(section) @address for length, clock_cycles ticks
  id: opcode operand1 operand2 for length, clocks ticks
'''

from __future__ import with_statement

import itertools
import os.path
import sqlite3 as db

Db_filename = "ucc.db"
For_column = 40

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
    db_cur.execute("""select id, label, section, address, length, clock_cycles
                        from assembler_blocks
                       order by id
    """)
    for info in db_cur.fetchall():
        print
        dump_block(info, db_cur)

def dump_block(info, db_cur):
    print "%d: %s(%s) @%s for %s, %s ticks" % info
    dump_insts(db_cur, info[0])

def dump_insts(db_cur, id):
    db_cur.execute("""
        select id, opcode, operand1, operand2, length, clocks
          from assembler_code
         where block_id = ?
         order by inst_order
        """,
        (id,))
    for id, opcode, operand1, operand2, length, clocks in db_cur:
        id_str = str(id)
        for_spaces = For_column - len(id_str) - len(opcode) - 3
        if operand1 is None:
            assert operand2 is None, "operand2 with no operand1"
            print "  %s: %s%sfor %s, %s ticks" % \
                    (id_str, opcode, ' ' * for_spaces, length, clocks)
        elif operand2 is None:
            print "  %s: %s %s%sfor %s, %s ticks" % \
                    (id_str, opcode, operand1,
                     ' ' * (for_spaces - len(operand1) - 1), 
                     length, clocks)
        else:
            print "  %s: %s %s, %s%sfor %s, %s ticks" % \
                    (id_str, opcode, operand1, operand2,
                     ' ' * (for_spaces - len(operand1) - len(operand2) - 3),
                     length, clocks)

if __name__ == "__main__":
    import sys

    def usage():
        sys.stderr.write(
          "usage: dump_asm.py (package_dir | file.ucl | file.asm)\n")
        sys.exit(2)

    len(sys.argv) == 2 or usage()

    if sys.argv[1].lower().endswith(('.ucl', '.asm')):
        package_dir, file = os.path.split(sys.argv[1])
        with db_cursor(package_dir) as db_cur:
            db_cur.execute("""select id, label, section, address, length,
                                     clock_cycles
                                from assembler_blocks
                               where label = ?
                           """,
                           (file[:-4],))
            dump_block(db_cur.fetchone(), db_cur)
    else:
        with db_cursor(sys.argv[1]) as db_cur:
            dump(db_cur)
