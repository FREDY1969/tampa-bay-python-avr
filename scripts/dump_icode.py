#!/usr/local/bin/python3.1

# dump_icode.py (package_dir | file.ucl)\n")

r'''Dumps the icode database in a simple ascii format.

fun_name.id: name [next id [/ id]] (predecessor ids)
  id: operator int1 int2 string (predecessor ids)
    child1
    child2

'''



import itertools
import os.path
import sqlite3 as db

Db_filename = "ucc.db"

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
    db_cur.execute("""select b.id, b.name, st.label,
                             b.last_triple_id, b.next, b.next_conditional
                        from blocks b inner join symbol_table st
                          on b.word_symbol_id = st.id
                       order by b.id
                   """)
    for info in db_cur.fetchall():
        print()
        dump_block(info, db_cur)

def dump_block(info, db_cur):
    id, name, fun_name, last_triple_id, next, next_cond = info
    db_cur.execute("""select predecessor
                        from block_successors
                       where successor = ?
                   """,
                   (id,))
    predecessors = ' '.join([str(x[0]) for x in db_cur])
    print("%s.%d: %s%s%s%s" % \
            (fun_name, id, name,
             ' next %s' % next if next else '',
             ' / %s' % next_cond if next_cond else '',
             ' (%s)' % predecessors if predecessors else ''))
    dump_triples(db_cur, id)

def dump_triples(db_cur, block_id):
    # Do triples for block:
    db_cur.execute("""
        select id, operator, int1, int2, string
          from triples
         where block_id = ?
         order by id""",
        (block_id,))

    triple_list = [triple(*info) for info in db_cur.fetchall()]
    triples = dict([(t.id, t) for t in triple_list])

    for t in triple_list:
        t.tag(triples)

    for t in triple_list:
        if not t.tagged:
            t.write(db_cur, triples)


class triple(object):
    op1 = ''
    triple1 = None
    op2 = ''
    triple2 = None
    tagged = False

    def __init__(self, id, operator, int1, int2, string):
        self.id = id
        self.operator = operator

        if operator in ('int', 'ratio', 'approx', 'param'):
            self.op1 = str(int1)
        elif operator in ('global_addr', 'global', 'local_addr', 'local',
                          'call_direct'):
            self.op1 = get_symbol(db_cur, int1)
        elif operator in ('input', 'input-bit',
                          'output', 'output-bit-set', 'output-bit-clear'):
            self.op1 = string
            string = None
        elif int1 is not None:
            self.triple1 = int1

        if operator in ('ratio', 'approx'):
            self.op2 = str(int2)
        elif operator in ('input-bit', 'output-bit-set', 'output-bit-clear'):
            self.op2 = str(int1)
        elif operator == 'output':
            self.triple2 = int1
        elif int2 is not None:
            self.triple2 = int2

        self.string = string
        self.written = False

    def tag(self, triples):
        if self.triple1 is not None:
            triples[self.triple1].tagged = True
        if self.triple2 is not None:
            triples[self.triple2].tagged = True

    def write(self, db_cur, triples, indent = 2):
        if self.written:
            print('%s%d.' % (' ' * indent, self.id))
        else:
            self.written = True

            db_cur.execute("""select predecessor
                                from triple_order_constraints
                               where successor = ?
                           """,
                           (self.id,))
            predecessors = ' '.join([str(x[0]) for x in db_cur])

            db_cur.execute("""select symbol_id, is_gen
                                from triple_labels
                               where triple_id = ?
                           """,
                           (self.id,))
            labels = ' '.join([(' => %s' if x[1] else ' -> %s') %
                                      get_symbol(db_cur, x[0]) for x in db_cur.fetchall()])

            print("%s%d: %s%s%s%s%s%s" % \
                  (' ' * indent,
                   self.id,
                   self.operator,
                   ' ' + self.op1 if self.op1 else '',
                   ' ' + self.op2 if self.op2 else '',
                   ' ' + self.string if self.string else '',
                   ' (%s)' % predecessors if predecessors else '',
                   labels))
            if self.triple1 is not None:
                triples[self.triple1].write(db_cur, triples, indent + 2)
            if self.triple2 is not None:
                triples[self.triple2].write(db_cur, triples, indent + 2)

def get_symbol(db_cur, id):
    db_cur.execute("""select label, context, kind, int1, side_effects, suspends
                        from symbol_table
                       where id = ?
                   """,
                   (id,))
    label, context, kind, int1, side_effects, suspends = db_cur.fetchone()
    while context is not None:
        db_cur.execute("""select label, context
                            from symbol_table
                           where id = ?
                       """,
                       (context,))
        label2, context = db_cur.fetchone()
        label = '.'.join((label2, label))
    return '%s[%s%s]%s%s' % \
             (label, kind, '-%d' % int1 if int1 is not None else '',
              'side_effects' if side_effects else '',
              'suspends' if suspends else '')


if __name__ == "__main__":
    import sys

    def usage():
        sys.stderr.write("usage: dump.py (package_dir | file.ucl)\n")
        sys.exit(2)

    len(sys.argv) == 2 or usage()

    if sys.argv[1].lower().endswith('.ucl'):
        package_dir, file = os.path.split(sys.argv[1])
        with db_cursor(package_dir) as db_cur:
            db_cur.execute("""select b.id, b.name, st.label, b.last_triple_id,
                                     b.next, b.next_conditional
                                from blocks b inner join symbol_table st
                                  on b.word_symbol_id = st.id
                               where st.label = ?
                               order by b.id
                           """,
                           (file[:-4],))
            for info in db_cur.fetchall():
                print()
                dump_block(info, db_cur)
    else:
        with db_cursor(sys.argv[1]) as db_cur:
            dump(db_cur)
