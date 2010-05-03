# codegen.py

import sys
import itertools

from ucc.database import crud, triple2

Debug = 0

def gen_assembler(processor):
    update_use_counts()
    update_order_constraints()
    order_children()

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

def update_use_counts():
    # Update use_counts of all triples:
    crud.Db_cur.execute('''
        update triples
           set use_count = (select count(*) from triple_parameters tp
                             where tp.parameter_id = triples.id)
      ''')

def update_order_constraints():
    # Propogate both sides of every constraint up through all of the parents
    # to the roots of both sides.
    total = 1   # force first run through the loop
    while total:
        # Add links from parents of predecessors:
        crud.Db_cur.execute('''
            insert or ignore into triple_order_constraints
              (predecessor, successor, orig_pred, orig_succ)
              select tp.parent_id, tos.successor, tos.orig_pred, tos.orig_succ
                from triple_order_constraint tos
                       inner join triple_parameters tp
                         on tos.predecessor = tp.parameter_id
          ''')
        total = crud.Db_cur.rowcount
        # Add links to parents of successors:
        crud.Db_cur.execute('''
            insert or ignore into triple_order_constraints
              (predecessor, successor, orig_pred, orig_succ)
              select tos.predecessor, tp.parent_id, tos.orig_pred, tos.orig_succ
                from triple_order_constraint tos
                       inner join triple_parameters tp
                         on tos.successor = tp.parameter_id
          ''')
        total += first + crud.Db_cur.rowcount

    # When node A has both the predecessor and successor of a constraint as
    # (deep) children, we don't need predecessor constraints from an outside
    # node B, since it doesn't matter whether B is done before or after A.
    # (This doesn't apply to outside successor links, where the order does
    # matter).  Note that in this case node A will have a constraint showing A
    # as both predecessor and successor.  This is how we'll identify these
    # nodes.
    #
    # So delete all links from predecessors to nodes that link the predecessor
    # to themselves as the successor.
    crud.Db_cur.execute('''
        delete from triple_order_constraints
         where exists (select null
                         from triple_order_constraints tos
                        where triple_order_constraints.orig_pred = tos.orig_pred
                          and triple_order_constraints.orig_succ = tos.orig_succ
                          and triple_order_constraints.successor = tos.successor
                          and tos.predecessor = tos.successor)
      ''')

    # Then clean up by deleting all links where both the predecessor and
    # successor are the same node, and all links that aren't between siblings.
    crud.Db_cur.execute('''
        delete from triple_order_constraints
         where predecessor = successor
            or (not exists (
                    -- child relationship between predecessor and successor
                    select null
                      from triple_parameters ptp
                             inner join triple_parameters stp
                               on ptp.parent_id = stp.parent_id
                     where ptp.parameter_id = predecessor
                       and stp.parameter_id = successor)

                and not exists (
                        -- predecessor and successor top-levels for same block
                        select null
                          from triples pt
                                 inner join triples st
                                   on pt.block_id = st.block_id
                                   and pt.use_count = 0
                                   and st.use_count = 0
                         where pt.id = predecessor
                           and st.id = successor))
      ''')

    # And finally delete all but one of duplicate predecessor, successor links
    # (this destroys orig_pred and orig_succ which aren't needed any more).
    crud.Db_cur.execute('''
        delete from triple_order_constraints
         where exists
           (select null
              from triple_order_constraints tos
             where tos.predecessor = triple_order_constraints.predecessor
               and tos.successor = triple_order_constraints.successor
               and (tos.orig_pred < triple_order_constraints.orig_pred or
                    tos.orig_pred = triple_order_constraints.orig_pred and
                    tos.orig_succ < triple_order_constraints.orig_succ))
      ''')

    # Now, add transitive links.  E.g., where A->B and B->C, add A->C.
    for depth in itertools.count(1):
        crud.Db_cur.execute('''
            insert or replace into triple_order_constraints
              (predecessor, successor, depth)
              select tos_p.predecessor, tos_s.successor, tos_p.depth + 1
                from triple_order_constraint tos_p
                       inner join triple_order_constraint tos_s
                         on tos_p.successor = tos_s.predecessor
                       inner join triple_parameters ptp
                         on ptp.parameter_id = tos_p.predecessor
                       inner join triple_parameters stp
                         on stp.parameter_id = tos_s.successor
                            and stp.parent_id = ptp.parent_id
               where tos_p.depth = ? and tos_s.depth = 1
          ''',
          (depth,))
        if crud.Db_cur.rowcount == 0:
            break

def order_children():
    total = 1   # force first run through the loop
    while total:
        # calc register_est for all triples who have an evaluation_order
        # computed for all of their children.
        crud.Db_cur.execute('''
            update triples
               set register_est = max(
                 (select count(*)
                    from triples_parameters tp
                   where tp.parent_id = id)
                 + (select extras
                      from operator_info io
                     where io.operator = triples.operator),
                 (select max(child.register_est + tp2.evaluation_order - 1)
                    from triples_parameters tp2
                           inner join triples child
                             on tp2.parameter_id = child.id
                   where tp2.parent_id = triples.id))
             where triples.register_est isnull
               and not exists (select null
                                 from triples_parameters tp
                                where tp.parent_id = id
                                  and tp.evaluation_order isnull)
          ''')
        total = crud.Db_cur.rowcount

        # calc register_est for all blocks who have a register_est for all of
        # their top-level triples.
        crud.Db_cur.execute('''
            update blocks
               set register_est = 
                 (select max(t.register_est)
                    from triples t
                   where t.block_id = blocks.id
                     and t.use_count = 0)
             where blocks.register_est isnull
               and not exists (select null
                                 from triples t
                                where t.block_id = blocks.id
                                  and t.use_count = 0
                                  and t.register_est isnull)
          ''')
        total += crud.Db_cur.rowcount

        # calc register_est for all functions who have a register_est for all
        # of their blocks.
        crud.Db_cur.execute('''
            update symbol_table
               set register_est = 
                 (select max(b.register_est)
                    from blocks b
                   where b.word_symbol_id = symbol_table.id)
             where symbol_table.kind in ('function', 'task')
               and symbol_table.register_est isnull
               and not exists (select null
                                 from blocks b
                                where b.word_symbol_id = symbol_table.id
                                  and b.register_est isnull)
          ''')
        total += crud.Db_cur.rowcount

        # Create table to assign sequential evaluation_order numbers to
        # sorted triple_parameters.
        crud.Db_cur.execute('''
            create temp table param_order (
                order integer not null primary key,    -- assigned seq number
                parent_id int not null,                -- parent triple id
                parameter_id int not null
            )
          ''')

        # Load temp param_order table with all sets of triple_parameters that
        # are ready to order.
        crud.Db_cur.execute('''
            insert into param_order (parent_id, parameter_id)
              select tp.parent_id, tp.parameter_id
                from triple_parameters tp
               where tp.parent_id in
                       (select t.id
                          from triples t
                         where t.register_est isnull
                           and not exists (select null
                                             from triple_parameter ctp
                                                    inner join triples c
                                                      on ctp.parameter_id = c.id
                                            where ctp.parent_id = t.id
                                              and c.register_est isnull))
               order by tp.parent_id,
                        max((select t.register_est * 1000
                               from triples t
                              where tp.parameter_id = t.id
                            ),
                            (select
                                 ifnull(max(t.register_est * 1000 + tos.depth),
                                        0)
                               from triple_order_constraints tos
                                      inner join triples t
                                        on tos.successor = t.id
                              where tos.predecessor = tp.parameter_id
                            )) desc
          ''')
        total += crud.Db_cur.rowcount

        # Copy the assigned order numbers from param_order to triple_parameters.
        crud.Db_cur.execute('''
            update triple_parameters
               set evaluation_order =
                     (select 1 + po.order
                               - (select min(parent_po.order)
                                    from param_order parent_po
                                   where parent_po.parent_id =
                                           triple_parameters.parent_id)
                        from param_order po
                       where po.parent_id = triple_parameters.parent_id 
                         and po.parameter_id = 
                               triple_parameters.parameter_id)
             where exists (select null
                             from param_order po
                            where po.parent_id = triple_parameters.parent_id 
                              and po.parameter_id = 
                                    triple_parameters.parameter_id)
          ''')
        total += first + crud.Db_cur.rowcount

        # We're done with the param_order table.
        crud.Db_cur.execute('''
            drop table param_order
          ''')

        # Create table to assign sequential evaluation_order numbers to
        # sorted top-level triples.
        crud.Db_cur.execute('''
            create temp table param_order (
                order integer not null primary key,    -- assigned seq number
                block_id int not null,
                triple_id int not null
            )
          ''')

        # Load temp param_order table with all sets of top-level triples that
        # are ready to order.
        crud.Db_cur.execute('''
            insert into param_order (block_id, triple_id)
              select t.block_id, t.id
                from triples t
               where t.use_count = 0
                 and t.order_in_block isnull
                 and not exists
                       (select null
                          from triples sib
                         where sib.use_count = 0
                           and t.block_id = sib.block_id
                           and sib.register_est isnull)
               order by t.block_id,
                        ifnull((select 0
                                  from blocks b
                                 where t.block_id = b.id
                                   and b.last_triple_id = t.id
                               ),
                               (select ifnull(max(tos.depth) + 1, 1)
                                  from triple_order_constraints tos
                                 where tos.predecessor = t.id
                               )) desc
          ''')
        total += crud.Db_cur.rowcount

        # Copy the assigned order numbers from param_order to triples.
        crud.Db_cur.execute('''
            update triples
               set order_in_block =
                     (select 1 + po.order
                               - (select min(block_po.order)
                                    from param_order block_po
                                   where block_po.block_id = triples.block_id)
                        from param_order po
                       where po.triple_id = triples.id)
             where id in (select triples_id from param_order po)
          ''')
        total += first + crud.Db_cur.rowcount

        # We're done with the param_order table.
        crud.Db_cur.execute('''
            drop table param_order
          ''')

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

