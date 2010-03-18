# codegen.py

import sys
import itertools

from ucc.database import crud, triple2

Debug = 0

def gen_assembler(processor):
    # Update use_counts of all triples:
    crud.Db_cur.execute('''
        update triples
           set use_count = (select count(*) from triples p1
                             where p1.operator not in ({qmarks1})
                               and p1.int1 = triples.id)
                         + (select count(*) from triples p2
                             where p2.operator not in ({qmarks2})
                               and p2.int2 = triples.id)
      '''.format(
            qmarks1=', '.join(['?'] * len(triple2.int1_operator_exclusions)),
            qmarks2=', '.join(['?'] * len(triple2.int2_operator_exclusions))),
      triple2.int1_operator_exclusions + triple2.int2_operator_exclusions)

    """ Sort this out later...
    crud.Db_cur.execute('''
        update triples
           set code_seq_id = (
              select p.code_seq_id
                from pattern p
                       inner join pattern_by_processor pp
                         on p.id = pp.pattern_id
               where pp.processor = ?

                 and (left_const is null and left_multi_use is null or
                      (select (left_const isnull or
                               left_const and left.operator = 'int' or
                               not left_const and left.operator != 'int') and
                              (left_const_min isnull or
                               left_const_min <= left.int1) and
                              (left_const_max isnull or
                               left_const_max >= left.int1) and
                              (left_multi_use isnull or
                               left_multi_use and left.use_count > 1 or
                               not left_multi_use and left.use_count <= 1)
                         from triples left
                        where left.id = triples.int1))

                 and (right_const is null and right_multi_use is null or
                      (select (right_const isnull or
                               right_const and right.operator = 'int' or
                               not right_const and right.operator != 'int') and
                              (right_const_min isnull or
                               right_const_min <= right.int1) and
                              (right_const_max isnull or
                               right_const_max >= right.int1) and
                              (right_multi_use isnull or
                               right_multi_use and right.use_count > 1 or
                               not right_multi_use and right.use_count <= 1)
                         from triples right
                        where right.id = triples.int2))

               order by preference
               limit 1)
    ''', (processor,))
    """

    for block_id, name, word_symbol_id, next, next_conditional \
     in crud.read_as_tuples('blocks', 'id', 'name', 'word_symbol_id', 'next',
                                      'next_conditional'):
        triples = triple2.read_triples(block_id)
        if Debug: print("triples", triples, file=sys.stderr)
        tops = [t for t in triples if len(t.parents) == 0]
        if Debug: print("tops", tops, file=sys.stderr)
        crud.Db_cur.execute('''
                select predecessor, successor
                  from triple_order_constraints
                 where predecessor in ({qmarks}) or successor in ({qmarks})
            '''.format(qmarks = ', '.join('?' * len(triples))),
            [t.id for t in triples] * 2)
        pred_succ = crud.Db_cur.fetchall()
        if Debug: print("pred_succ", pred_succ, file=sys.stderr)
        shareds = [s for s in (frozenset(tops(t.parents))
                               for t in triples
                               if len(t.parents) > 1)
                     if len(s) > 1]
        if Debug: print("shareds", shareds, file=sys.stderr)
        for top in order_tops(tops, pred_succ, shareds):
            print('gen_assembler for block', block_id, 'triple', top.id, file=sys.stderr)
            #with crud.db_transaction():

def tops(triples):
    return itertools.chain.from_iterable(
             (tops(t.parents) if t.parents else (t,))
             for t in triples)

def order_tops(tops, pred_succ, shareds):
    tops = list(tops)
    leftovers = set()

    def process(t_set, shareds):
        def remove(t):
            assert t in tops
            tops.remove(t)
            if t in leftovers: leftovers.remove(t)
            return [ps for ps in shareds if ps[0] != t and ps[1] != t]
        for t_shared in pick(t_set, shareds):
            found_one = False
            try_again = True
            while t_shared and try_again:
                try_again = False
                for t in t_shared.copy():
                    if t not in succs:
                        shareds = remove(t)
                        t_shared.remove(t)
                        try_again = True
                        found_one = True
                        yield t, shareds
            assert found_one
            for t in leftovers:
                if t not in succs:
                    shareds = remove(t)
                    yield t, shareds
            leftovers.update(t_shared)
            break
        else:
            assert False, "pick failed"

    while pred_succ:
        if Debug: print("pred_succ", pred_succ, file=sys.stderr)
        if Debug: print("tops", tops, file=sys.stderr)
        preds = frozenset(ps[0] for ps in pred_succ)
        succs = frozenset(ps[1] for ps in pred_succ)
        available_preds = preds - succs
        assert available_preds
        for t, shareds in process(available_preds, shareds):
            yield t
    if Debug: print("while done: tops", tops, file=sys.stderr)
    if tops:
        succs = frozenset(ps[1] for ps in pred_succ)
        for t, shareds in process(frozenset(tops), shareds):
            yield t

def pick(t_set, shareds):
    if Debug: print("pick", t_set, shareds, file=sys.stderr)
    t_yielded = set()
    for t in t_set:
        t_shared = set(s for s in shareds if t in s)
        if t_shared:
            t_yielded.add(t)
            yield t_shared
    for t in t_set - t_yielded:
        yield set((t,))

