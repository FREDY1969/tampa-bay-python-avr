# assign_registers.py

r'''Assigns registers to each register_group.

The only function called here from outside is assign_registers (called from
attempt_register_allocation in ucc/codegen/populate_register_groups.py).
'''

import itertools

from ucc.database import crud

def assign_registers(max_stacking_order):
    r'''Pops register_groups off of the "stack" and assigns a register to each.

    Return True if everything goes OK and False if we need to rerun the
    register allocation process.
    '''
    with crud.db_transaction():
        for i in range(max_stacking_order, 0, -1):
            crud.execute('''
                update register_group
                   set assigned_register = (
                           select reg
                             from reg_in_class
                            where reg_class = register_group.reg_class
                              and reg not in (
                                      select a.r2
                                        from rg_neighbors rgn
                                             inner join register_group n
                                               on  n.id in (rg1, rg2)
                                             inner join alias a
                                               on  a.r1 = n.assigned_register
                                       where register_group.id in (rg1, rg2)
                                         and n.id != register_group.id
                                         and n.assigned_register notnull))
                 where stacking_order = ?
              ''', (i,))

        # Copy to reg_use table
        crud.execute('''
            update reg_use
               set assigned_register = (select rg.assigned_register
                                          from register_group rg
                                         where rg.id = reg_use.reg_group_id)
          ''')
    return True
