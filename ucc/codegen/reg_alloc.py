# reg_alloc.py

r'''Register allocation code.
'''

import itertools

from ucc.database import crud

def alloc_regs():
    subsets = get_reg_class_subsets()
    sizes = get_reg_class_sizes()
    figure_out_multi_use(subsets, sizes)

def get_reg_class_subsets():
    return dict(((rc1, rc2), subset)
                for rc1, rc2, subset
                 in crud.read_as_tuples('reg_class_subsets',
                                        'rc1', 'rc2', 'subset'))

def get_reg_class_sizes():
    crud.Db_cur.execute('''
        select reg_class, count(reg)
          from reg_in_class
         group by reg_class
      ''')
    return dict(crud.Db_cur.fetchall())

def figure_out_multi_use(subsets, sizes):
    with crud.db_transaction():
        crud.Db_cur.execute('''
            update triple_parameters
               set reg_class_for_parent =
                     (select csp.reg_class
                        from triples t
                               inner join code_seq_parameter csp
                                 on t.code_seq_id = csp.code_seq_id
                       where t.id = triple_parameters.parent_id
                         and triple_parameters.parameter_num =
                               csp.parameter_num),
                   num_regs_for_parent =
                     (select csp.num_registers
                        from triples t
                               inner join code_seq_parameter csp
                                 on t.code_seq_id = csp.code_seq_id
                       where t.id = triple_parameters.parent_id
                         and triple_parameters.parameter_num =
                               csp.parameter_num),
                   trashed =
                     (select csp.trashes
                        from triples t
                               inner join code_seq_parameter csp
                                 on t.code_seq_id = csp.code_seq_id
                       where t.id = triple_parameters.parent_id
                         and triple_parameters.parameter_num =
                               csp.parameter_num),
                   delink =
                     (select csp.delink
                        from triples t
                               inner join code_seq_parameter csp
                                 on t.code_seq_id = csp.code_seq_id
                       where t.id = triple_parameters.parent_id
                         and triple_parameters.parameter_num =
                               csp.parameter_num)
          ''')

    # This will handle the vast majority of triple_parameters:
    with crud.db_transaction():
        crud.Db_cur.execute('''
            update triple_parameters
               set needed_reg_class = reg_class_for_parent
             where last_parameter_use
          ''')

    with crud.db_transaction():
        rows = tuple(crud.read_as_dicts('triple_parameters',
                     'parameter_id', 'parent_id', 'parameter_num',
                     'trashed', 'reg_class_for_parent', 'last_parameter_use',
                     order_by=('parameter_id', ('parent_seq_num', 'desc'))))
        last_parameter = None
        for i, row in enumerate(rows):
            if row['parameter_id'] != last_parameter:
                last_parameter = row['parameter_id']
                next_rc = row['reg_class_for_parent']
                assert row['last_parameter_use']
            elif trashed:
                crud.update('triple_parameters',
                            {'parameter_id': row['parameter_id'], 
                             'parent_id': row['parent_id'],
                             'parameter_num': row['parameter_num']},
                            needed_reg_class = next_rc,
                            move_needed_to_parent = 1)
            elif (next_rc, row['reg_class_for_parent']) in subsets:
                next_rc = subsets[next_rc, row['reg_class_for_parent']]
                crud.update('triple_parameters',
                            {'parameter_id': row['parameter_id'], 
                             'parent_id': row['parent_id'],
                             'parameter_num': row['parameter_num']},
                            needed_reg_class = next_rc)
            else:
                prior = i + 1
                done = False
                if prior < len(rows) and not rows[prior]['trashed']:
                    p = rows[prior]
                    subset = subsets.get((p['reg_class_for_parent'],
                                          row['reg_class_for_parent']))
                    if subset is not None:
                        if sizes[subset] > sizes[next_rc]:
                            next_rc = subset
                            crud.update('triple_parameters',
                                        {'parameter_id': row['parameter_id'], 
                                         'parent_id': row['parent_id'],
                                         'parameter_num': row['parameter_num']},
                                        needed_reg_class = next_rc)
                            crud.update('triple_parameters',
                                        {'parameter_id': row['parameter_id'],
                                         'parent_id': rows[i - 1]['parent_id'],
                                         'parameter_num':
                                           rows[i - 1]['parameter_num']},
                                        move_prior_to_needed = 1)
                        else:
                            next_rc = subset
                            crud.update('triple_parameters',
                                        {'parameter_id': row['parameter_id'], 
                                         'parent_id': row['parent_id'],
                                         'parameter_num': row['parameter_num']},
                                        needed_reg_class = next_rc,
                                        move_needed_to_next = 1)
                        done = True
                    else:
                        subset = subsets.get((p['reg_class_for_parent'],
                                              next_rc))
                        if subset is not None:
                            next_rc = subset
                            crud.update('triple_parameters',
                                        {'parameter_id': row['parameter_id'],
                                         'parent_id': row['parent_id'],
                                         'parameter_num': row['parameter_num']},
                                        needed_reg_class = next_rc,
                                        move_needed_to_parent = 1)
                            done = True
                if not done:
                    if sizes[row['reg_class_for_parent']] > sizes[next_rc]:
                        next_rc = row['reg_class_for_parent']
                        crud.update('triple_parameters',
                                    {'parameter_id': row['parameter_id'],
                                     'parent_id': row['parent_id'],
                                     'parameter_num': row['parameter_num']},
                                    needed_reg_class = next_rc)
                        crud.update('triple_parameters',
                                    {'parameter_id': row['parameter_id'], 
                                     'parent_id': rows[i - 1]['parent_id'],
                                     'parameter_num':
                                       rows[i - 1]['parameter_num']},
                                    move_prior_to_needed = 1)
                    else:
                        crud.update('triple_parameters',
                                    {'parameter_id': row['parameter_id'],
                                     'parent_id': row['parent_id'],
                                     'parameter_num': row['parameter_num']},
                                    needed_reg_class = next_rc,
                                    move_needed_to_parent = 1)

