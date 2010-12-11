# assign_registers.py

r'''Assigns registers to each register_group.

The only function called here from outside is assign_registers (called from
attempt_register_allocation in ucc/codegen/populate_register_groups.py).
'''

import sys              # only for debugging
import itertools
import operator

from ucc.database import crud

Init_done = False

def create_views():
    global Init_done

    if not Init_done:
        crud.execute('''
            create temp view available_registers as
              select rg.id, rg.stacking_order, rg.assignment_certain, ric.reg
                from register_group rg
                     left outer join reg_in_class ric
                       on  ric.reg_class = rg.reg_class
                       and not exists (
                               select null
                                 from neighbors n
                                      inner join alias a
                                        on  n.assigned_register2 = a.r1
                                where n.id1 = rg.id
                                  and n.assigned_register2 notnull
                                  and a.r2 = ric.reg
                             )
          ''')

        crud.execute('''
            create temp view score as
              select ar.id, ar.stacking_order, ar.reg, count(n.id2) as score
                from available_registers ar
                     left outer join neighbors n
                       on  ar.id = n.id1
                       and not n.assignment_certain2
                       and n.assigned_register2 isnull
                       and
                       (   not exists (select null from class_alias
                                        where reg_class = n.reg_class2
                                          and reg = ar.reg)
                        or exists (select null
                                     from neighbors n2
                                          inner join alias a
                                            -- FIX: this should be based on
                                            -- register subset not intersection
                                            on  a.r1 = n2.assigned_register2
                                    where n.id2 = n2.id1
                                      and n2.id2 != n.id1
                                      and n2.assigned_register2 notnull
                                      and a.r2 = ar.reg)
                       )
               group by ar.id, ar.reg
          ''')

        Init_done = True

def assign_registers(max_stacking_order, attempt_number):
    r'''Pops register_groups off of the "stack" and assigns a register to each.

    Return True if everything goes OK and False if we need to rerun the
    register allocation process.
    '''
    with crud.db_transaction():
        create_views()

        ans = True
        # Assign registers in LIFO order from stack:
        for i in range(max_stacking_order, 0, -1):

            # Here's the plan:
            #
            # 1. Get available registers for each register_group at stacking
            #    level i.
            # 2. Score each register based on how many unassigned uncertain
            #    neighboring register_groups are not affected by that choice
            #    of register.  There are two reasons that a neighboring
            #    register_group would be unaffected:
            #      A.  The register is not in its reg_class.
            #      B.  It already has another neighbor using that register.
            # 3. Assign the highest scoring register.

            print("available_registers", file = sys.stderr)
            for row in crud.read_as_rows('available_registers'):
                print("row:", row, file = sys.stderr)
            print(file = sys.stderr)

            print("score", file = sys.stderr)
            for row in crud.read_as_rows('score'):
                print("row:", row, file = sys.stderr)
            print(file = sys.stderr)

            for id, assignment_certain, reg_class \
             in crud.read_as_tuples('register_group', 'id',
                                    'assignment_certain', 'reg_class',
                                    stacking_order=i, order_by='id'):

                reg = next(crud.fetchall('''
                                select get_max(score, reg)
                                  from score
                                 where id = :id
                              ''', (id,)), (None,))[0]

                print("assigning", id, "assignment_certain",
                      assignment_certain, "reg", reg, file = sys.stderr)

                if reg is None:
                    assert not assignment_certain
                    ans = False
                else:
                    # Assign reg to id!
                    crud.update('register_group', {'id': id},
                                assigned_register = reg)

    with crud.db_transaction():
        if ans:
            # Copy assigned_register to reg_use table
            crud.execute('''
                update reg_use
                   set assigned_register = (select rg.assigned_register
                                              from register_group rg
                                             where rg.id = reg_use.reg_group_id)
              ''')
        else:
            break_links(attempt_number)

    return ans

def break_links(attempt_number):
    r'''
    '''
    assert False        # FIX: implement breaking links here!

    # NOTE: One rul may be involved in more than one reg_class, through
    #       multiple rg_neighbors!  ... But I guess it doesn't matter ...
    it = crud.fetchall('''
             select unassigned_rg.id, rc.reg, rul.id as rul_id
               from reg_use_linkage rul
                    inner join overlaps ov
                      on  rul.id = ov.linkage_id
                    inner join rg_neighbors rgn
                      on  rgn.id = ov.rg_neighbor_id
                    inner join register_group unassigned_rg
                      on  unassigned_rg.id in (rgn.rg1, rgn.rg2)
                    inner join register_group neighbor_rg
                      on  neighbor_rg.id in (rgn.rg1, rgn.rg2)
                      and neighbor_rg.id != unassigned_rg.id
                    inner join reg_in_class rc
                      on  rc.reg_class = unassigned_rg.reg_class
                    inner join alias a
                      on  a.r1 = rc.reg
                      and a.r2 = neighbor_rg.assigned_register
              where unassigned_rg.assigned_register isnull
                and neighbor_rg.assigned_register notnull
                and rul.broken = 0
              order by id, reg
           ''')

    # rg_ruls is [(rg_id, [{rul_id}])]
    # This is in order that the rg_ids need to be processed (ascending min
    # {rul_id} length).
    rg_ruls = sorted(((rg_id, [{rul_id for _, _, rul_id in ruls}
                               for _, ruls
                                in itertools.groupby(
                                     regs,
                                     key=operator.itemgetter(1))])
                      for rg_id, regs
                       in itertools.groupby(it, key=operator.itemgetter(0))),
                     key=lambda x: min(len(s) for s in x[1]))

    ruls_broken = set()
    for rg_id, rul_sets in rg_ruls:
        rul_set = get_smallest_remaining_set(rul_sets, ruls_broken)
        crud.executemany('''
            update reg_use_linkage
               set broken = ?
             where id = ?
          ''', zip(itertools.repeat(attempt_number), rul_set))
        ruls_broken.update(rul_set)

def get_smallest_remaining_set(source_sets, items_to_ignore):
    return min((s.difference(items_to_ignore) for s in source_sets), key=len)
