# order_triples.py

import sys
import itertools

from ucc.database import crud

Debug = False

def update_order_constraints():
    propogate_links()
    delete_extranious_links()
    add_transitive_links()

def propogate_links():
    r'''Propogate links upward through the heirarchy.

    Propogate both sides of every constraint up through all of the parents
    to the roots of both sides.  This will create a lot of extranious links
    (including links where the predecessor and successor are the same triple!)
    which we'll clean up later.

    Returns the number of times it looped.
    '''
    total = 1   # force first run through the loop
    iterations = 0
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
        iterations += 1
    return iterations

def delete_extranious_links():
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

def add_transitive_links():
    r'''Add transitive links.  E.g., where A->B and B->C, add A->C.

    Returns the number times it ran the SQL command.
    '''
    for depth in itertools.count(1):
        crud.Db_cur.execute('''
            insert or replace into triple_order_constraints
              (predecessor, successor, depth)
              select tos_p.predecessor, tos_s.successor, tos_p.depth + 1
                from triple_order_constraints tos_p
                       inner join triple_order_constraints tos_s
                         on tos_p.successor = tos_s.predecessor
               where tos_p.depth = ? and tos_s.depth = 1
          ''',
          (depth,))
        if crud.Db_cur.rowcount == 0:
            return depth

def order_children():
    update_order_constraints()
    iterations = 0
    re_triple_count = re_block_count = re_fun_count = 0
    tp_order_count = 1  # force calc_reg_est_for_triples first time through
    tl_triple_order_count = 0
    total = 1   # force first run through the loop
    while total:
        total = 0
        if tp_order_count or re_fun_count:
            re_triple_count = calc_reg_est_for_triples()
            total += re_triple_count
        else:
            re_triple_count = 0
        if re_triple_count:
            re_block_count = calc_reg_est_for_blocks()
            total += re_block_count
        else:
            re_block_count = 0
        if re_block_count:
            re_fun_count = calc_reg_est_for_functions()
            total += re_fun_count
        else:
            re_fun_count = 0
        if re_triple_count:
            tp_order_count = update_triple_parameter_orders()
            total += tp_order_count
        else:
            tp_order_count = 0
        iterations += 1
    update_top_level_triple_orders()
    calc_master_order()
    return iterations

def calc_reg_est_for_triples():
    r'''Calc triples.register_est.
    
    Triples must have an evaluation_order for all of their triple_parameters.

    Returns the number of triples updated.
    '''
    crud.Db_cur.execute('''
        update triples
           set register_est = max(
             (select max(1, count(*))
                from triple_parameters tp
               where tp.parent_id = id)
             + ifnull((select num_extra_regs
                         from operator_info io
                        where io.operator = triples.operator), 0),
             case when triples.operator = 'call_direct'
                  then (select sym.register_est
                          from symbol_table sym
                         where triples.symbol_id = sym.id)
                  else 0
             end,
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
           and (triples.operator != 'call_direct'
                or (select sym.register_est notnull
                      from symbol_table sym
                     where triples.symbol_id = sym.id))
      ''')
    total = crud.Db_cur.rowcount
    if Debug: print("update triples total", total, file=sys.stderr)
    return total

def calc_reg_est_for_blocks():
    r'''Calc blocks.register_est.
    
    Blocks must have a register_est for all of their top-level triples.

    Returns the number of blocks updated.
    '''
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
    total = crud.Db_cur.rowcount
    if Debug: print("update blocks total", total, file=sys.stderr)
    return total

def calc_reg_est_for_functions():
    r'''Calc symbol_table.register_est for kind in ('function', 'task').
    
    Functions/tasks must have at least one block and have a register_est for
    all of their blocks.

    Returns the number of symbols updated.

    FIX: Need to account for parameters and locals.  Do they get mapped into
    registers?  Or least do a max on the number of parameters...
    '''
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
    total = crud.Db_cur.rowcount
    if Debug: print("update symbol_table total", total, file=sys.stderr)
    return total

def update_triple_parameter_orders():
    r'''Calculates and updates the triple_parameters.evaluation_order column.

    This works on the level of the set of parameters to each triples node who
    still need it.  All of the triples parameters must have a register_est.

    Returns the number of triple_parameters updated.
    '''

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
                        )) desc,
                    tp.parameter_num
      ''')
    total = crud.Db_cur.rowcount
    if Debug: print("insert param_order total", total, file=sys.stderr)

    if total:
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
        if Debug:
            print("update triple_parameters total", total, file=sys.stderr)

    # We're done with the param_order table.
    crud.Db_cur.execute('''
        drop table param_order
      ''')

    return total

def update_top_level_triple_orders():
    r'''Calculates and updates the triples.order_in_block column.

    This works on a block level for all blocks who still need it, and all of
    whose top-level triples have a register_est.

    Returns the number of triples updated.

    FIX: This doesn't actually use register_est, so this function could
    probably just be run once, rather than each time through the order_children
    loop.
    '''

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
                           )) desc,
                    t.id
      ''')
    total = crud.Db_cur.rowcount
    if Debug: print("insert param_order total", total, file=sys.stderr)

    if total:
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
             where id in (select triple_id from param_order)
          ''')
        if Debug: print("update triples total", total, file=sys.stderr)

    # We're done with the param_order table.
    crud.Db_cur.execute('''
        drop table param_order
      ''')

    return total

def calc_master_order():
    calc_tree_sizes()
    calc_abs_offsets()
    mark_ghost_links()
    calc_abs_order_in_block()

def calc_tree_sizes():
    r'''Calculate all triples.tree_size figures.
    
    Tree_size is the number of triples in the tree rooted at that triple
    (counting the triple itself).
    '''
    total = 1
    while total:
        crud.Db_cur.execute('''
            update triples
               set tree_size = (select ifnull(sum(child.tree_size), 0) + 1
                                  from triple_parameters tp
                                         inner join triples child
                                           on tp.parameter_id = child.id
                                 where tp.parent_id = triples.id)
             where tree_size isnull
               and not exists (select null
                                 from triple_parameters tp
                                        inner join triples child
                                          on tp.parameter_id = child.id
                                where tp.parent_id = triples.id
                                  and child.tree_size isnull)
          ''')
        total = crud.Db_cur.rowcount

def calc_abs_offsets():
    r'''Calculate abs_offsets for top-level triples and triple_parameters.
    '''

    # first for top-level triples:
    crud.Db_cur.execute('''
        update triples
           set abs_offset =
                 (select ifnull(sum(prior.tree_size), 0)
                    from triples prior
                   where prior.block_id = triples.block_id
                     and prior.use_count = 0
                     and prior.order_in_block < triples.order_in_block)
         where use_count = 0
      ''')

    # then for triple_parameters:
    total = 1
    while total:
        crud.Db_cur.execute('''
            update triple_parameters
               set abs_offset =
                     (select ifnull(min(parent.abs_offset),
                                    (select t.abs_offset
                                       from triples t
                                      where triple_parameters.parent_id = t.id))
                        from triple_parameters parent
                       where parent.parameter_id = triple_parameters.parent_id)
                   + (select ifnull(sum(prior.tree_size), 0)
                        from triple_parameters tp
                               inner join triples prior
                                 on tp.parameter_id = prior.id
                       where tp.parent_id = triple_parameters.parent_id
                         and tp.evaluation_order <
                               triple_parameters.evaluation_order)
             where abs_offset isnull
               and not exists
                     (select null
                        from triple_parameters parent
                       where parent.parameter_id = triple_parameters.parent_id
                         and parent.abs_offset isnull)
          ''')
        total = crud.Db_cur.rowcount

def mark_ghost_links():
    r'''Set triple_parameter.ghost for links to ghost triples.

    Ghost triples have already been evaluated by the time this
    triple_parameter is needed.  So the triple is a ghost, and code is not
    generated for it here.
    '''
    crud.Db_cur.execute('''
        update triple_parameters
           set ghost = 1
         where triple_parameters.abs_offset >
                 (select min(tp.abs_offset)
                    from triple_parameters tp
                   where triple_parameters.parameter_id = tp.parameter_id)
      ''')

def calc_abs_order_in_block():
    r'''Calc abs_order_in_block for triples and triple_parameters.
    '''
    # first for top-level triples:
    crud.Db_cur.execute('''
        update triples
           set abs_order_in_block = abs_offset + tree_size
         where use_count = 0
      ''')

    # then for triple_parameters:
    crud.Db_cur.execute('''
        update triple_parameters
           set abs_order_in_block = abs_offset +
                 case when ghost
                      then 1
                      else (select tree_size
                              from triples child
                             where triple_parameters.parameter_id = child.id)
                 end
      ''')

    # finally, copy the triple_parameters.abs_order_in_block down to its
    # child.
    crud.Db_cur.execute('''
        update triples
           set abs_order_in_block = (select abs_order_in_block
                                       from triple_parameters tp
                                      where triples.id = tp.parameter_id
                                        and tp.ghost = 0)
         where use_count != 0
      ''')

