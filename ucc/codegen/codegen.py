# codegen.py

import sys
import itertools

from ucc.database import crud, triple2

Debug = 0

def gen_assembler():
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
                          for t in triples if len(t.parents) > 1) if len(s) > 1]
        if Debug: print("shareds", shareds, file=sys.stderr)
        for top in order_tops(tops, pred_succ, shareds):
            print('gen_assembler for block', block_id, 'triple', top.id, file=sys.stderr)
            #with crud.db_transaction():

def tops(triples):
    return itertools.chain.from_iterable(
             (tops(t.parents) if t.parents else (t,)) for t in triples)

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

