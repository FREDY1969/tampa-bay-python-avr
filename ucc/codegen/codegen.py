# codegen.py

import sys
import itertools

from ucc.database import crud, triple2

Debug = 0

def gen_assembler(processor):
    # Update use_counts of all triples:
    crud.Db_cur.execute('''
        update triples
           set use_count = (select count(*) from triple_parameters tp
                             where tp.parameter_id = triples.id)
      ''')

    # assign code_seq_id's to triples.
    crud.Db_cur.execute('''
        update triples
           set code_seq_id = (
              select p.code_seq_id
                from pattern p
                       inner join pattern_by_processor pp
                         on p.id = pp.pattern_id
               where pp.processor = ?

                 and (p.left_opcode is null and p.left_multi_use is null or
                      exists (select null
                         from triple_parameters tp inner join triples p1
                           on tp.parameter_id = p1.id
                        where tp.parent_id = triples.id
                          and tp.parameter_num = 1
                          and (p.left_opcode isnull or
                               p.left_opcode = p1.operator)
                          and (p.left_const_min isnull or
                               p.left_const_min <= p1.int1)
                          and (p.left_const_max isnull or
                               p.left_const_max >= p1.int1)
                          and (p.left_multi_use isnull or
                               p.left_multi_use and p1.use_count > 1 or
                               not p.left_multi_use and p1.use_count <= 1)))

                 and (p.right_opcode is null and p.right_multi_use is null or
                      exists (select null
                         from triple_parameters tp2 inner join triples p2
                           on tp2.parameter_id = p2.id
                        where tp2.parent_id = triples.id
                          and tp2.parameter_num = 2
                          and (p.right_opcode isnull or
                               p.right_opcode = p2.operator)
                          and (p.right_const_min isnull or
                               p.right_const_min <= p2.int1)
                          and (p.right_const_max isnull or
                               p.right_const_max >= p2.int1)
                          and (p.right_multi_use isnull or
                               p.right_multi_use and p2.use_count > 1 or
                               not p.right_multi_use and p2.use_count <= 1)))

               order by p.preference
               limit 1)
    ''', (processor,))

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
        shareds_with_dups = frozenset(s for s in (frozenset(tops_of(t.parents))
                                                  for t in triples
                                                  if len(t.parents) > 1)
                                        if len(s) > 1)
        
        shareds = {
          s for s in shareds_with_dups
            if not any(x.issubset(s)
                       for x in shareds_with_dups
                       if x != s)
        }

        if Debug: print("shareds", shareds, file=sys.stderr)
        for top in order_tops(tops, pred_succ, shareds):
            print('gen_assembler for block', block_id, 'triple', top.id, file=sys.stderr)
            #with crud.db_transaction():

def tops_of(triples):
    return itertools.chain.from_iterable(
             (tops_of(t.parents) if t.parents else (t,))
             for t in triples)

def order_tops(tops, pred_succ, shareds):
    r'''Yields triples from tops in their desired order.

    tops is a list of top-level triples.
    pred_succ is a list of (pred triple, succ triple).
    shareds is a set of frozenset(shared top-level triples).

    All three parameters are altered (destroyed).
    '''
    leftovers = set()

    def process(t_set):
        r'''Yields triples from t_set and triples shared with these.

        All triples in yielded in their proper order.

        t_set is a frozenset of triples to generate.

        Triples that can not be generated due to pred/succ constraints are
        placed in leftovers and will eventually get generated when the
        contraints are satisfied.
        '''
        def remove(t):
            assert t in tops
            tops.remove(t)
            if t in leftovers: leftovers.remove(t)
            for i, (pred, succ) in enumerate(pred_succ[:]):
                if pred == t or succ == t:
                    del pred_succ[i]
        for t in leftovers:
            if t not in succs:
                remove(t)
                yield t
        for t_shared in pick_shareds(t_set, shareds):
            t_shared = set(t_shared)
            found_one = False
            try_again = True
            while t_shared and try_again:
                try_again = False
                for t in t_shared.copy():
                    if t not in succs:
                        remove(t)
                        t_shared.remove(t)
                        try_again = True
                        found_one = True
                        yield t
            assert found_one
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
        assert available_preds, "circular pred/succ dependency!"
        for t in process(available_preds):
            yield t
    if Debug: print("while done: tops", tops, file=sys.stderr)
    succs = frozenset()
    while tops:
        for t in process(frozenset(tops)):
            yield t

def pick_shareds(t_set, shareds):
    r'''Yields all shared triples that contain something in t_set.

    t_set is a frozenset of triples to generate.
    shareds is a set of frozenset(shared top-level triples).

    shareds is altered to delete the sets generated.

    yields frozensets of triples.

    All triples in t_set are yielded in a shared frozenset.  Sometimes that
    means that the yielded frozenset has only one member.
    '''

    if Debug: print("pick", t_set, shareds, file=sys.stderr)
    t_yielded = set()
    for s in shareds.copy():
        if s.intersection(t_set):
            t_yielded.update(s)
            shareds.remove(s)
            yield s
    for t in t_set - t_yielded:
        yield set((t,))

