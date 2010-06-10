# reg_alloc.py

r'''Register allocation code.
'''

#import sys   # for debug traces
import itertools
import collections

from ucc.database import crud, triple2
from ucc.codegen import code_seq

def alloc_regs():
    subsets = get_reg_class_subsets()
    sizes = get_reg_class_sizes()
    figure_out_multi_use(subsets, sizes)
    code_seqs = code_seq.get_code_seq_info()
    create_reg_map(subsets, sizes, code_seqs)

def get_reg_class_subsets():
    r'''Returns {(reg_class1, reg_class2), subset_reg_class}.
    '''
    return dict(((rc1, rc2), subset)
                for rc1, rc2, subset
                 in crud.read_as_tuples('reg_class_subsets',
                                        'rc1', 'rc2', 'subset'))

def get_reg_class_sizes():
    r'''Returns the number of registers in each reg_class.

    The return value is {reg_class: number_of_registers}
    '''
    crud.Db_cur.execute('''
        select reg_class, count(reg)
          from reg_in_class
         group by reg_class
      ''')
    return dict(crud.Db_cur.fetchall())

def figure_out_multi_use(subsets, sizes):
    with crud.db_transaction():
        crud.Db_cur.execute('''
            update triples
               set reg_class =       (select cs.output_reg_class
                                        from code_seq cs
                                       where triples.code_seq_id = cs.id),
                   num_regs_output = (select cs.num_output
                                        from code_seq cs
                                       where triples.code_seq_id = cs.id)
             where operator not in
                     ('output', 'output-bit-set', 'output-bit-clear',
                      'global_addr', 'global', 'local_addr', 'local',
                      'call_direct', 'call_indirect', 'return',
                      'if_false', 'if_true')
          ''')

    with crud.db_transaction():
        # FIX: Need to add info for function call parameters!
        crud.Db_cur.execute('''
            update triple_parameters
               set reg_class_for_parent =
                     (select csp.reg_class
                        from code_seq_parameter csp
                       where triple_parameters.parent_code_seq_id =
                               csp.code_seq_id
                         and triple_parameters.parameter_num =
                               csp.parameter_num),
                   num_regs_for_parent =
                     (select csp.num_registers
                        from code_seq_parameter csp
                       where triple_parameters.parent_code_seq_id =
                               csp.code_seq_id
                         and triple_parameters.parameter_num =
                               csp.parameter_num),
                   trashed =
                     (select csp.trashes
                        from code_seq_parameter csp
                       where triple_parameters.parent_code_seq_id =
                               csp.code_seq_id
                         and triple_parameters.parameter_num =
                               csp.parameter_num),
                   delink =
                     (select csp.delink
                        from code_seq_parameter csp
                       where triple_parameters.parent_code_seq_id =
                               csp.code_seq_id
                         and triple_parameters.parameter_num =
                               csp.parameter_num)
             where parent_id not in (select t.id
                                       from triples t
                                      where t.operator in ('call_direct',
                                                           'call_indirect'))
          ''')

    # This will handle the vast majority of triple_parameters:
    with crud.db_transaction():
        crud.Db_cur.execute('''
            update triple_parameters
               set needed_reg_class = reg_class_for_parent
             where last_parameter_use
               and reg_class_for_parent notnull
          ''')

    with crud.db_transaction():
        rows = tuple(crud.read_as_dicts('triple_parameters',
                     'parameter_id', 'parent_id', 'parameter_num',
                     'trashed', 'reg_class_for_parent', 'last_parameter_use',
                     order_by=('parameter_id', ('parent_seq_num', 'desc'))))
        for k, params \
         in itertools.groupby(rows, key=lambda row: row['parameter_id']):
            params = tuple(params)
            for i, row in enumerate(params):
                if i == 0:
                    next_rc = row['reg_class_for_parent']
                    assert row['last_parameter_use']
                    if next_rc is None: break
                elif row['trashed']:
                    crud.update('triple_parameters',
                                {'parameter_id': row['parameter_id'], 
                                 'parent_id': row['parent_id'],
                                 'parameter_num': row['parameter_num']},
                                needed_reg_class = next_rc,
                                move_needed_to_parent = 1)
                elif row['reg_class_for_parent'] is None:
                    break
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
                    if prior < len(params):
                        p = params[prior]
                        if p['reg_class_for_parent'] is None \
                           or p['trashed'] is None:
                            break
                        if not p['trashed']:
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
                                       'parent_id': params[i - 1]['parent_id'],
                                       'parameter_num':
                                         params[i - 1]['parameter_num']},
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
                                         'parent_id':
                                           params[i - 1]['parent_id'],
                                         'parameter_num':
                                           params[i - 1]['parameter_num']},
                                        move_prior_to_needed = 1)
                        else:
                            crud.update('triple_parameters',
                                        {'parameter_id': row['parameter_id'],
                                         'parent_id': row['parent_id'],
                                         'parameter_num': row['parameter_num']},
                                        needed_reg_class = next_rc,
                                        move_needed_to_parent = 1)

    # Reset ghost flag for delinked triple_parameters:
    # FIX: This could violate a triple_order_constraint!
    #      But I don't think that it will because it should only be
    #      constant parameters that are delinked.
    with crud.db_transaction():
        # Mark delinks as ghosts.
        crud.Db_cur.execute('''
            update triple_parameters
               set ghost = 1
             where ghost = 0 and delink
          ''')

        # And pick another triple_parameter to evaluate the parameter triple.
        # Note that if all triple_parameters are marked 'delink', then the
        # parameter triple will not have any ghost = 0, so will not have code
        # generated for it.
        crud.Db_cur.execute('''
            update triple_parameters
               set ghost = 0
             where not exists
                     (select null
                        from triple_parameters tp
                       where tp.parameter_id = triple_parameters.parameter_id
                         and tp.ghost = 0)
               and parent_seq_num =
                     (select min(parent_seq_num)
                        from triple_parameters tp
                       where tp.parameter_id = triple_parameters.parameter_id
                         and not tp.delink)
          ''')

    # Finally, copy the triple_parameters.abs_order_in_block down to its
    # child.
    with crud.db_transaction():
        crud.Db_cur.execute('''
            update triples
               set abs_order_in_block = (select abs_order_in_block
                                           from triple_parameters tp
                                          where triples.id = tp.parameter_id
                                            and tp.ghost = 0),
                   needed_reg_class =   (select tp.needed_reg_class
                                           from triple_parameters tp
                                          where triples.id = tp.parameter_id
                                            and tp.ghost = 0),
                   num_needed_regs =    (select tp.num_regs_for_parent
                                           from triple_parameters tp
                                          where triples.id = tp.parameter_id
                                            and tp.ghost = 0)
             where use_count != 0
          ''')


def create_reg_map(subsets, sizes, code_seqs):
    for next_fn_layer in get_functions():
        # FIX: What needs to happen between fn layers?
        # {(reg_class, reg_num): [(kind, kind_id, reg_class, reg_num), ...]}
        reg_map = {}
        for symbol_id in next_fn_layer:
            do_reg_map_for_fun(symbol_id, subsets, sizes, code_seqs, reg_map)
        write_reg_map(reg_map)

def get_functions():
    r'''Yields sets of functions in a bottom-up order.

    Each set is all of the functions that don't call any functions not yet
    yielded.

    Each function in the set is simply its symbol_id.
    '''
    fns = set()
    calls = collections.defaultdict(set)
    called_by = collections.defaultdict(set)
    for caller_id, called_id \
     in crud.read_as_tuples('fn_calls', 'caller_id', 'called_id', depth=1):
        fns.add(called_id)
        fns.add(caller_id)
        calls[caller_id].add(called_id)
        called_by[called_id].add(caller_id)
    while fns:
        bottom = fns - calls.keys()
        yield bottom
        fns -= bottom
        for fn in bottom:
            for caller in called_by[fn]:
                calls[caller].remove(fn)
                if not calls[caller]: del calls[caller]

def do_reg_map_for_fun(symbol_id, subsets, sizes, code_seqs, reg_map):
    fn_name, kind, suspends = crud.read1_as_tuple('symbol_table',
                                                  'label', 'kind', 'suspends',
                                                  id=symbol_id)
    locals = gather_locals(symbol_id, subsets, sizes)

    #print(fn_name, "locals", locals, file=sys.stderr)

def gather_locals(fn_symbol_id, subsets, sizes):
    r'''Returns {symbol_id: (reg_class, num_regs, use_count)}
    '''

    crud.Db_cur.execute('''
        select u.symbol_id, u.reg_class, count(*), max(u.num_regs)
          from blocks b
                 inner join (  select t.block_id, t.symbol_id, 'use',
                                      needed_reg_class as reg_class,
                                      num_needed_regs as num_regs
                                 from triples t
                                where operator = 'local'
                             union
                               select t2.block_id, tl.symbol_id, 'definition',
                                      t2.reg_class, t2.num_regs_output
                                 from triples t2
                                        inner join triple_labels tl
                                          on t2.id = tl.triple_id
                                        inner join symbol_table st
                                          on tl.symbol_id = st.id
                                          and st.context = ?
                            ) u
                   on b.id = u.block_id
         where b.word_symbol_id = ?
         group by u.symbol_id, u.reg_class
         order by u.symbol_id
      ''', (fn_symbol_id, fn_symbol_id))

    ans = {}    # {symbol_id: (reg_class, num_regs, use_count)}

    #print('sizes', sizes, file=sys.stderr)

    for id, reg_iter in itertools.groupby(list(crud.Db_cur.fetchall()),
                                          lambda t: t[0]):
        reg_classes = collections.defaultdict(int)  # {rc: num_uses}
        max_regs = 0
        saved_reg_iter = tuple(info for info in reg_iter if info[1] is not None)
        for _, reg_class, count, max_needed in saved_reg_iter:
            if max_needed > max_regs: max_regs = max_needed
            reg_classes[reg_class] = count
        for (_, rc1, count1, _), (_, rc2, count2, _) \
         in itertools.combinations(saved_reg_iter, 2):
            sub_rc = subsets.get((rc1, rc2))
            if sub_rc is not None:
                if sub_rc != rc1:
                    reg_classes[sub_rc] += count1
                if sub_rc != rc2:
                    reg_classes[sub_rc] += count2

        # Select max count:
        rc, count = sorted(reg_classes.items(),
                           key=lambda i: (i[1], sizes[i[0]]),
                           reverse=True) \
                      [0]
        ans[id] = (rc, max_regs, count)

    return ans

def write_reg_map(reg_map):
    # FIX: implement this!
    pass
