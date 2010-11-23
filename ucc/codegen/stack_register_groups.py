# stack_register_groups.py

r'''Stacks the register_groups, per the graph-coloring algorithm.

The only functions called here from outside are:
    initialize_rawZ_and_Z
    stack_register_groups

These are both called from attempt_register_allocation in
ucc/codegen/populate_register_groups.py.

The underlying algorithm here is taken from:

    A Generalized Algorithm for Graph-Coloring Register Allocation
        Michael D. Smith, Norman Ramsey, and Glenn Holloway
            Division of Engineering and Applied Sciences
            Harvard University

printed in Proceedings of the ACM SIGPLAN ’04 Conference on Programming
Language Design and Implementation

see: http://www.cs.tufts.edu/~nr/pubs/gcra-abstract.html
'''

import sys   # for debug traces
import itertools

from ucc.database import crud

def initialize_rawZ_and_Z():
    r'''Initialize the rawZ and Z values.

    This function may be called repeatedly, so it must delete info from prior
    calls.
    '''
    with crud.db_transaction():
        crud.delete('rawZ')

    with crud.db_transaction():
        # insert sum(worst) values part of rawZ:
        crud.execute('''
            insert into rawZ (reg_group_id, vertex_id, value)
            select n_id, v, sum(degree * w.value)
              from (select n.id as n_id, n.reg_class as n_rc,
                           c.id as c_id, c.v as v, count(rg.id) as degree
                      from register_group n
                           inner join rg_neighbors rgn
                             on n.id in (rg1, rg2)
                           inner join register_group rg
                             on rg.id in (rg1, rg2)
                             and rg.id != n.id
                           inner join reg_class c
                             on rg.reg_class = c.id
                     group by n.id, c.id)
                   inner join worst w
                     on w.N = n_rc
                     and w.C = c_id
             group by n_id, v
          ''')

        # insert 0 rawZ nodes where there are children
        v_heights = \
          tuple(range(1, 1 + max(crud.read_column('vertex', 'height'))))
        for v_height in v_heights[1:]:
            crud.execute('''
                insert or ignore into rawZ (reg_group_id, vertex_id, value)
                select r.reg_group_id, v.parent, 0
                  from rawZ r
                       inner join vertex v
                         on r.vertex_id = v.id
                         and v.height = ?
              ''', (v_height,))

        # add children to rawZ nodes
        for v_height in v_heights[1:]:
            crud.execute('''
                update rawZ
                   set value = value + (
                           select sum(min(b.value, child.value))
                             from rawZ child
                                  inner join vertex v
                                    on  child.vertex_id = v.id
                                  inner join register_group rg
                                    on  child.reg_group_id = rg.id
                                  inner join bound b
                                    on  b.N = rg.reg_class
                                    and b.v = v.id
                            where child.reg_group_id = rawZ.reg_group_id
                              and v.parent = rawZ.vertex_id
                              and v.height = ?)
                 where exists (select null
                                 from rawZ child
                                      inner join vertex v
                                        on child.vertex_id = v.id
                                where child.reg_group_id = rawZ.reg_group_id
                                  and v.parent = rawZ.vertex_id
                                  and v.height = ?)
              ''', (v_height, v_height))
        set_Z()

def set_Z():
    r'''Perform final Z(n, R) calculation for register_groups.

    This updates all register_groups.
    '''
    crud.execute('''
        update register_group
           set Z = (select sum(min(b.value, root.value))
                      from rawZ root
                           inner join vertex v
                             on  root.vertex_id = v.id
                           inner join register_group rg
                             on  root.reg_group_id = rg.id
                           inner join bound b
                             on  b.N = rg.reg_class
                             and b.v = v.id
                     where v.parent isnull
                       and root.reg_group_id = register_group.id)
      ''')

def stack_register_groups(num_register_groups):
    r'''Stacks register_groups by setting register_group.stacking_order.

    The stacking_order starts with 1 at the bottom of the stack and works up.
    It returns the maximum stacking_order assigned.

    This function may be called multiple times.
    '''

    if num_register_groups == 0:
        return 0

    with crud.db_transaction():
        # stack register_groups
        stacking_order = iter(itertools.count(1))
        while True:
            i = next(stacking_order)

            # Stack all assignment_certain register_groups (if any):
            row_count = crud.execute('''
                update register_group
                   set stacking_order = ?,
                       assignment_certain = 1
                 where stacking_order isnull
                   and Z < 
                   (select class_size
                      from reg_class rc
                     where rc.id = register_group.reg_class)
              ''', (i,))[0]
            print("stacking", i, "assignment_certain got", row_count,
                  file=sys.stderr)
            if row_count == 0:
                # No assignment_certain register_groups, select 1
                # register_group with least excess in registers required:
                group_id = next(crud.fetchall('''
                     select get_min(rg.Z - rc.class_size, rg.id)
                       from register_group rg
                            inner join reg_class rc
                              on  rc.id = rg.reg_class
                      where rg.stacking_order isnull
                  '''))[0]
                row_count = crud.execute('''
                    update register_group
                       set stacking_order = ?,
                           assignment_certain = 0
                     where id = ?
                  ''', (i, group_id))[0]
                print("stacking", i, "not assignment_certain got", row_count,
                      "with", group_id, file=sys.stderr)
                assert row_count == 1

            num_register_groups -= row_count
            if num_register_groups <= 0:
                return i

            # Update rawZ values to reflect deleted links to register_groups
            # just stacked.
            it = crud.fetchall('''
                     select -w.value as delta, rg.id as n, rc.v as C_v
                       from register_group rg_stacked
                            inner join rg_neighbors rgn
                              on  rg_stacked.id in (rg1, rg2)
                            inner join register_group rg
                              on  rg.id in (rg1, rg2)
                              and rg.stacking_order isnull
                            inner join reg_class rc
                              on  rg_stacked.reg_class = rc.id
                            inner join worst w
                              on  w.N = rg.reg_class
                              and w.C = rg_stacked.reg_class
                      where rg_stacked.stacking_order = ?
                        and not rgn.broken
              ''', (i,))
            crud.executemany('''
                update rawZ
                   set delta = ?
                 where reg_group_id = ?
                   and vertex_id = ?
              ''', it)

            delta_count = 1
            while delta_count:
                it = crud.fetchall('''
                         select min(0,
                                    max(child.delta,
                                        child.delta - (b.value - child.value))),
                                parent.reg_group_id, parent.vertex_id
                           from rawZ parent
                                inner join vertex child_v
                                  on  parent.vertex_id = child_v.parent
                                inner join rawZ child
                                  on  child.vertex_id = child_v.id
                                  and child.reg_group_id = parent.reg_group_id
                                inner join register_group rg
                                  on  child.reg_group_id = rg.id
                                inner join bound b
                                  on  b.N = rg.reg_class
                                  and b.v = child_v.id
                          where parent.delta isnull
                            and child.delta
                       ''')
                it = tuple(it)
                crud.executemany('''
                        update rawZ
                           set delta = ?
                         where reg_group_id = ?
                           and vertex_id = ?
                      ''', it)
                delta_count = len(it)
                print("propagating deltas got", delta_count, file=sys.stderr)

            # add deltas to values and clear deltas
            crud.execute('''
                update rawZ
                   set value = value + delta,
                       delta = NULL
                 where delta notnull
              ''')

            # Recalc Z values:
            set_Z()

