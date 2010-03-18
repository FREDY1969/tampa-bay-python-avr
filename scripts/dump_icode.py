#!/usr/local/bin/python3.1

# dump_icode.py (package_dir | file.ucl)\n")

r'''Dumps the icode database in a simple ascii format.

fun_name.id: name [next id [/ id]] (predecessor ids)
  id: [use_count] operator int1 int2 symbol string (predecessor ids) => sym
    child1
    child2

'''



import itertools
import os.path
import sqlite3 as db

Db_filename = "ucc.db"

Debug = False

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
    db_cur.execute("""select id, name, word_symbol_id, last_triple_id, next,
                             next_conditional
                        from blocks
                       order by id
                   """)
    for info in db_cur.fetchall():
        print()
        dump_block(info, db_cur)

def dump_block(info, db_cur):
    id, name, word_symbol_id, last_triple_id, next, next_cond = info
    if Debug: print("dump_block: ", id)
    db_cur.execute("""select predecessor
                        from block_successors
                       where successor = ?
                   """,
                   (id,))
    predecessors = ' '.join([str(x[0]) for x in db_cur])
    fun_name, kind, flags = get_symbol(db_cur, word_symbol_id)
    print("{fun_name}{kind}.{id}: {block_name}{next}{next_cond}{pred}{flags}"
            .format(fun_name=fun_name,
                    kind=kind,
                    flags=flags,
                    id=id,
                    block_name=name,
                    next=' next {}'.format(next) if next else '',
                    next_cond=' / {}'.format(next_cond) if next_cond else '',
                    pred=' ({})'.format(predecessors) if predecessors else ''))
    dump_triples(db_cur, id)

def dump_triples(db_cur, block_id):
    if Debug: print("dump_triples: ", block_id)
    # Do triples for block:
    db_cur.execute("""
        select id, use_count, operator, int1, int2, symbol_id, string
          from triples
         where block_id = ?
         order by id""",
        (block_id,))

    triple_list = [triple(db_cur, *info) for info in db_cur.fetchall()]
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

    def __init__(self, db_cur, id, use_count, operator, int1, int2, symbol_id,
                       string):
        self.id = id
        self.use_count = use_count
        self.operator = operator
        self.int1 = int1
        self.int2 = int2
        if symbol_id is None:
            self.symbol = None
        else:
            self.symbol = get_symbol(db_cur, symbol_id)[0]
        self.string = string
        db_cur.execute("""select parameter_id
                            from triple_parameters
                           where parent_id = ?
                           order by parameter_num
                       """,
                       (self.id,))
        self.parameter_ids = tuple(x[0] for x in db_cur)
        self.written = False

    def tag(self, triples):
        self.parameters = tuple(triples[id] for id in self.parameter_ids)
        for t in self.parameters: t.tagged = True

    def write(self, db_cur, triples, indent = 2):
        if self.written:
            print('{}{}.'.format(' ' * indent, self.id))
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
            labels = ''.join([(' => {}' if x[1] else ' -> {}')
                                .format(get_symbol(db_cur, x[0])[0])
                              for x in db_cur.fetchall()])

            print("{indent}{id}: [{uses}] {op}{int1}{int2}{sym}{st}{pred}{lbls}"
                    .format(indent=' ' * indent,
                            id=self.id,
                            uses=self.use_count,
                            op=self.operator,
                            int1=' ' + str(self.int1) if self.int1 else '',
                            int2=' ' + str(self.int2) if self.int2 else '',
                            sym=' ' + self.symbol if self.symbol else '',
                            st=' ' + repr(self.string) if self.string else '',
                            pred=' ({})'.format(predecessors) if predecessors
                                                              else '',
                            lbls=labels))
            for param in self.parameters:
                param.write(db_cur, triples, indent + 2)

def get_symbol(db_cur, id):
    if Debug: print("get_symbol: ", id)
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
    if Debug: print("get_symbol => ", label)
    return label, \
           '[{kind}{int1}]'.format(kind=kind,
                                   int1='-{}'.format(int1) if int1 is not None
                                                           else ''), \
           (' side_effects' if side_effects else '') + \
             (' suspends' if suspends else '')


if __name__ == "__main__":
    import sys

    def usage():
        sys.stderr.write("usage: dump_icode.py (package_dir | file.ucl)\n")
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
