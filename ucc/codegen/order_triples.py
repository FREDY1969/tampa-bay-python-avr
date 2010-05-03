# order_triples.py

import sys
import itertools

from ucc.database import crud

Debug = True

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
                from triple_order_constraints tos
                       inner join triple_parameters tp
                         on tos.predecessor = tp.parameter_id
          ''')
        total = crud.Db_cur.rowcount
        # Add links to parents of successors:
        crud.Db_cur.execute('''
            insert or ignore into triple_order_constraints
              (predecessor, successor, orig_pred, orig_succ)
              select tos.predecessor, tp.parent_id, tos.orig_pred, tos.orig_succ
                from triple_order_constraints tos
                       inner join triple_parameters tp
                         on tos.successor = tp.parameter_id
          ''')
        total += crud.Db_cur.rowcount

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
                from triple_order_constraints tos_p
                       inner join triple_order_constraints tos_s
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
    update_order_constraints()
    total = 1   # force first run through the loop
    while total:
        # calc register_est for all triples who have an evaluation_order
        # computed for all of their children.
        crud.Db_cur.execute('''
            update triples
               set register_est = max(
                 (select max(1, count(*))
                    from triple_parameters tp
                   where tp.parent_id = id)
                 + ifnull((select num_extra_regs
                             from operator_info io
                            where io.operator = triples.operator), 0),
                 (select
                      ifnull(max(child.register_est + tp2.evaluation_order - 1),
                             0)
                    from triple_parameters tp2
                           inner join triples child
                             on tp2.parameter_id = child.id
                   where tp2.parent_id = triples.id))
             where triples.register_est isnull
               and not exists (select null
                                 from triple_parameters tp
                                where tp.parent_id = id
                                  and tp.evaluation_order isnull)
          ''')
        total = crud.Db_cur.rowcount
        if Debug: print("update triples total", total, file=sys.stderr)

        # calc register_est for all blocks who have a register_est for all of
        # their top-level triples.
        crud.Db_cur.execute('''
            update blocks
               set register_est = 
                 (select ifnull(max(t.register_est), 0)
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
        if Debug: print("update blocks total", total, file=sys.stderr)

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
               and exists (select null
                             from blocks b
                            where b.word_symbol_id = symbol_table.id)
               and not exists (select null
                                 from blocks b
                                where b.word_symbol_id = symbol_table.id
                                  and b.register_est isnull)
          ''')
        total += crud.Db_cur.rowcount
        if Debug: print("update symbol_table total", total, file=sys.stderr)

        # Create table to assign sequential evaluation_order numbers to
        # sorted triple_parameters.
        crud.Db_cur.execute('''
            create temp table param_order (
                seq_num integer not null primary key,  -- assigned seq number
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
                                             from triple_parameters ctp
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
        if Debug: print("insert param_order total", total, file=sys.stderr)

        # Copy the assigned seq_nums from param_order to triple_parameters.
        crud.Db_cur.execute('''
            update triple_parameters
               set evaluation_order =
                     (select 1 + po.seq_num
                               - (select min(parent_po.seq_num)
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
        total += crud.Db_cur.rowcount
        if Debug:
            print("update triple_parameters total", total, file=sys.stderr)

        # We're done with the param_order table.
        crud.Db_cur.execute('''
            drop table param_order
          ''')

        # Create table to assign sequential evaluation_order numbers to
        # sorted top-level triples.
        crud.Db_cur.execute('''
            create temp table param_order (
                seq_num integer not null primary key,    -- assigned seq number
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
        if Debug: print("insert param_order total", total, file=sys.stderr)

        # Copy the assigned seq_nums from param_order to triples.
        crud.Db_cur.execute('''
            update triples
               set order_in_block =
                     (select 1 + po.seq_num
                               - (select min(block_po.seq_num)
                                    from param_order block_po
                                   where block_po.block_id = triples.block_id)
                        from param_order po
                       where po.triple_id = triples.id)
             where id in (select triple_id from param_order po)
          ''')
        total += crud.Db_cur.rowcount
        if Debug: print("update triples total", total, file=sys.stderr)

        # We're done with the param_order table.
        crud.Db_cur.execute('''
            drop table param_order
          ''')

