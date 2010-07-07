# reg_alloc.py

r'''Register allocation code.
'''

import sys   # for debug traces
import itertools
import collections

from ucc.database import crud, triple2
from ucc.codegen import code_seq

class aggr_rc_subset:
    r'''Sqlite3 aggregate function for aggr_rc_subset.
    
    Tries to produce the rc that is a subset to the most submitted entries.

        >>> subsets = {(1, 1): 1, (1, 3): 1, (3, 1): 1, 
        ...            (2, 2): 2, (2, 3): 2, (3, 2): 2, (3, 3): 3}
        >>> rcs = aggr_rc_subset(subsets)
        >>> rcs.finalize()       # NULL for 0 rows.
        >>> rcs = aggr_rc_subset(subsets)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(3)
        >>> rcs.step(1)
        >>> rcs.step(1)
        >>> rcs.finalize()
        2
    '''
    def __init__(self, subsets = None):
        if subsets: self.subsets = subsets
        else: self.subsets = Subsets
        self.rc_counts = collections.defaultdict(int)

    def step(self, rc):
        if rc is not None:
            self.rc_counts[rc] += 1

    def finalize(self):
        if not self.rc_counts: return None
        if len(self.rc_counts) == 1: return next(iter(self.rc_counts.keys()))

        # Eliminate all disjoint rc's with the smallest cost to keep.
        while len(self.rc_counts) > 1:
            keep_cost = collections.defaultdict(int)
            for rc1, rc2 in itertools.combinations(self.rc_counts.keys(), 2):
                if (rc1, rc2) not in self.subsets:
                    keep_cost[rc1] += self.rc_counts[rc2]
                    keep_cost[rc2] += self.rc_counts[rc1]
            if not keep_cost: break
            rc_to_dump = max(keep_cost.items(), key = lambda item: item[1])[0]
            print("keep_cost:", keep_cost, "rc_to_dump:", rc_to_dump,
                  file=sys.stderr)
            del self.rc_counts[rc_to_dump]

        # Return subset of all remaining rc's:
        ans = None
        for rc in self.rc_counts.keys():
            if ans is None: ans = rc
            else:
                ans = self.subsets.get((ans, rc))
                assert ans is not None, "aggr_rc_subset: internal logic error"
        return ans

class aggr_num_regs:
    r'''Sqlite3 aggregate function for aggr_num_regs.

    All num_regs seen should match.  If not, an AssertionError is raised.

        >>> nr = aggr_num_regs()
        >>> nr.finalize()       # NULL for 0 rows.
        >>> nr = aggr_num_regs()
        >>> nr.step(2)
        >>> nr.step(2)
        >>> nr.step(2)
        >>> nr.step(2)
        >>> nr.finalize()
        2
        >>> nr = aggr_num_regs()
        >>> nr.step(2)
        >>> nr.step(1)
        >>> nr.step(2)
        >>> nr.finalize()
        Traceback (most recent call last):
          ...
        AssertionError: non-conforming num_regs: {1, 2}
    '''
    def __init__(self):
        self.num_regs = set()

    def step(self, num_regs):
        if num_regs is not None:
            self.num_regs.add(num_regs)

    def finalize(self):
        if not self.num_regs: return None
        if len(self.num_regs) == 1: return next(iter(self.num_regs))
        raise AssertionError(
                "non-conforming num_regs: {}".format(self.num_regs))

def rc_subset(rc1, rc2):
    if rc1 is None: return rc2
    if rc2 is None: return rc1
    return Subsets.get((rc1, rc2))

def chk_num_regs(nr1, nr2):
    if nr1 is None: return nr2
    if nr2 is None: return nr1
    if nr1 == nr2: return nr1
    raise AssertionError("non-conforming num_regs: {{{}, {}}}".format(nr1, nr2))

def alloc_regs():
    global Subsets
    Subsets = get_reg_class_subsets()
    crud.Db_conn.db_conn.create_function("rc_subset", 2, rc_subset)
    crud.Db_conn.db_conn.create_function("chk_num_regs", 2, chk_num_regs)
    crud.Db_conn.db_conn.create_aggregate("aggr_rc_subset", 1, aggr_rc_subset)
    crud.Db_conn.db_conn.create_aggregate("aggr_num_regs", 1, aggr_num_regs)
    sizes = get_reg_class_sizes()
    figure_out_multi_use(Subsets, sizes)
    code_seqs = code_seq.get_code_seq_info()
    #create_reg_map(Subsets, sizes, code_seqs)

def get_reg_class_subsets():
    r'''Returns {(reg_class1, reg_class2): subset_reg_class}.
    '''
    return {(rc1, rc2): subset
            for rc1, rc2, subset
             in crud.read_as_tuples('reg_class_subsets',
                                    'rc1', 'rc2', 'subset')}

def get_subsets_of_reg_classes():
    r'''Returns {reg_class: {subset_rc}}
    '''
    it = crud.fetchall('''
             select rc.id, vc.C
               from v_classes vc
                    inner join reg_class rc
                      on rc.v = vc.v
              order by rc.id
           ''')
    return {rc: frozenset(sub[1] for sub in subs)
            for rc, subs in itertools.groupby(it, lambda row: row[0])}

def get_reg_class_sizes():
    r'''Returns the number of registers in each reg_class.

    The return value is {reg_class: number_of_registers}
    '''
    return dict(crud.fetchall('''
                    select reg_class, count(reg)
                      from reg_in_class
                     group by reg_class
                  '''))

def figure_out_multi_use(subsets, sizes):
    # Copy the triple_parameters.abs_order_in_block down to its child.
    with crud.db_transaction():
        crud.execute('''
            update triples
               set abs_order_in_block = (select abs_order_in_block
                                           from triple_parameters tp
                                          where triples.id = tp.parameter_id
                                            and tp.ghost = 0)
             where use_count != 0
          ''')

    # Populate reg_use
    with crud.db_transaction():
        # Populate reg_use for triple-output
        crud.execute('''
            insert into reg_use
              (kind, ref_id, initial_reg_class, num_registers, is_definition,
               block_id, abs_order_in_block)
              select 'triple-output', t.id, cs.output_reg_class, cs.num_output,
                     1, t.block_id, t.abs_order_in_block
                from triples t
                     inner join code_seq cs
                       on t.code_seq_id = cs.id
               where t.code_seq_id notnull
                 and t.operator not in 
                     ('output', 'output-bit-set', 'output-bit-clear',
                      'global_addr', 'global', 'local_addr', 'local',
                      'call_direct', 'call_indirect', 'return',
                      'if_false', 'if_true')
                 and cs.num_output
          ''')

        # Populate reg_use for triple-output for 'global' and 'local'
        crud.execute('''
            insert into reg_use
              (kind, ref_id, is_definition, block_id, abs_order_in_block)
              select 'triple-output', t.id, 1, t.block_id, t.abs_order_in_block
                from triples t
               where t.operator in ('global', 'local')
          ''')

        # Populate reg_use for triple/parameter
        crud.execute('''
            insert into reg_use
              (kind, ref_id, position_kind, position,
               initial_reg_class, num_registers,
               block_id, abs_order_in_block)
              select 'triple', t.id, 'parameter', csp.parameter_num,
                     csp.reg_class, csp.num_registers,
                     t.block_id, tp.abs_order_in_block
                from triples t
                     inner join triple_parameters tp
                       on t.id = tp.parent_id
                     inner join code_seq_parameter csp
                       on t.code_seq_id = csp.code_seq_id
                          and tp.parameter_num = csp.parameter_num
               where t.code_seq_id notnull
                 and t.operator not in 
                     ('output', 'output-bit-set', 'output-bit-clear',
                      'global_addr', 'global', 'local_addr', 'local',
                      'call_direct', 'call_indirect', 'return',
                      'if_false', 'if_true')
          ''')

        # Populate reg_use for 'call_direct' triple-output
        crud.execute('''
            insert into reg_use
              (kind, ref_id, is_definition, block_id, abs_order_in_block)
              select 'triple-output', t.id, 1, t.block_id, t.abs_order_in_block
                from triples t
               where t.operator = 'call_direct'
          ''')

        # Populate reg_use for 'call_direct' triple/parameter
        crud.execute('''
            insert into reg_use
              (kind, ref_id, position_kind, position,
               block_id, abs_order_in_block)
              select 'triple', t.id, 'parameter', tp.parameter_num,
                     t.block_id, tp.abs_order_in_block
                from triples t
                     inner join triple_parameters tp
                       on t.id = tp.parent_id
               where t.operator = 'call_direct'
          ''')

        # Populate reg_use for triple/temp
        it = crud.fetchall('''
              select t.id, rr.reg_class, rr.num_needed,
                     t.block_id, t.abs_order_in_block
                from triples t
                     inner join reg_requirements rr
                       on t.code_seq_id = rr.code_seq_id
               where t.code_seq_id notnull
                 and t.operator not in 
                     ('output', 'output-bit-set', 'output-bit-clear',
                      'global_addr', 'global', 'local_addr', 'local',
                      'call_direct', 'call_indirect', 'return',
                      'if_false', 'if_true')
          ''')
        crud.executemany('''
            insert into reg_use
              (kind, ref_id, position_kind, position,
               initial_reg_class, num_registers, block_id, abs_order_in_block)
              values ('triple', ?, 'temp', ?,
                      ?, 1, ?, ?)
          ''', ((id, n, rc, block_id, order)
                for id, rc, nn, block_id, order in it
                  for n in range(1, nn + 1)))

        # Populate reg_use for function:
        crud.execute('''
            insert into reg_use
              (kind, ref_id, position_kind, position, num_registers)
              select 'function', fn.id, local.kind,
                     case local.kind
                       when 'parameter' then local.int1
                       else local.id
                     end,
                     1
                from symbol_table fn
                     inner join symbol_table local
                       on fn.id = local.context
               where fn.kind in ('function', 'task')
                 and local.kind in ('parameter', 'var')
          ''')

        # Populate reg_use for function-return:
        crud.execute('''
            insert into reg_use (kind, ref_id)
              select 'function-return', fn.id
                from symbol_table fn
               where fn.kind in ('function', 'task')
                 and exists (select null
                               from blocks b
                                    inner join triples ret_t
                                      on ret_t.block_id = b.id
                                    inner join triple_parameters tp
                                      on ret_t.id = tp.parent_id
                              where b.word_symbol_id = fn.id
                                and ret_t.operator = 'return'
                                and tp.parameter_num = 1)
          ''')

    # Populate reg_use_linkage
    with crud.db_transaction():
        # triple(-output) -> triple/parameter linkages
        #   chaining the triple-output to its parent's triple_parameters.
        it = crud.fetchall('''
              select ru1.id, ru2.id
                from reg_use ru1
                     inner join triple_parameters tp
                       on ru1.ref_id = tp.parameter_id
                     inner join reg_use ru2
                       on     ru2.ref_id = tp.parent_id
                          and ru2.position = tp.parameter_num
               where ru1.kind = 'triple-output'
                 and ru2.kind = 'triple'
                 and ru2.position_kind = 'parameter'
               order by ru1.id, ru2.abs_order_in_block
          ''')
        crud.executemany('''
            insert into reg_use_linkage (reg_use_1, reg_use_2, is_segment)
                                 values (?, ?, 1)
          ''',
          itertools.chain.from_iterable(
            pairs(itertools.chain((head,), (r[1] for r in refs)))
            for head, refs in itertools.groupby(it, lambda x: x[0])))

        print("done inserting reg_use_linkage segments", file = sys.stderr)

        # triple-output -> function/parameter linkages
        #   assignment to parameter inside the function (not passing parameter).
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2)
              select ru1.id, ru2.id
                from reg_use ru1
                     inner join triple_labels tl
                       on ru1.ref_id = tl.triple_id
                     inner join symbol_table p
                       on p.id = tl.symbol_id
                     inner join reg_use ru2
                       on     ru2.ref_id = p.context
                          and ru2.position = p.int1
               where ru1.kind = 'triple-output'
                 and ru2.kind = 'function'
                 and ru2.position_kind = 'parameter'
          ''')

        print("done triple-output -> function/parameter", file = sys.stderr)

        # triple-output -> function/var linkages
        #   assignment to local variable inside a function.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2)
              select ru1.id, ru2.id
                from reg_use ru1
                     inner join triple_labels tl
                       on ru1.ref_id = tl.triple_id
                     inner join reg_use ru2
                       on ru2.position = tl.symbol_id
               where ru1.kind = 'triple-output'
                 and ru2.kind = 'function'
                 and ru2.position_kind = 'var'
          ''')

        print("done triple-output -> function/var", file = sys.stderr)

        # triple-output -> function-return linkages
        #   binding function-return to triple-output of 'call-direct' triples.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2)
              select ru1.id, ru2.id
                from reg_use ru1
                     inner join triples t
                       on ru1.ref_id = t.id
                     inner join reg_use ru2
                       on ru2.ref_id = t.symbol_id
               where ru1.kind = 'triple-output'
                 and t.operator = 'call-direct'
                 and ru2.kind = 'function-return'
          ''')

        print("done triple-output -> function-return", file = sys.stderr)

        # triple/parameter -> function/parameter linkages
        #   binding triple/parameter of 'call_direct' triples to
        #   function/parameters.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2)
              select ru1.id, ru2.id
                from reg_use ru1
                       inner join triples t
                         on ru1.ref_id = t.id
                       inner join reg_use ru2
                         on     ru2.ref_id = t.symbol_id
                            and ru1.position = ru2.position
               where ru1.kind = 'triple'
                 and ru1.position_kind = 'parameter'
                 and t.operator = 'call-direct'
                 and ru2.kind = 'function'
                 and ru2.position_kind = 'parameter'
          ''')

        print("done triple/parameter -> function/parameter", file = sys.stderr)

        # triple/parameter -> function-return linkages
        #   links triple/parameter of 'return' triple to function-return.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2)
              select ru1.id, ru2.id
                from reg_use ru1
                     inner join triples t
                       on t.id = ru1.ref_id
                     inner join blocks b
                       on b.id = t.block_id
                     inner join reg_use ru2
                       on ru2.ref_id = b.word_symbol_id
               where ru1.kind = 'triple'
                 and ru1.position_kind = 'parameter'
                 and ru1.position = 1
                 and t.operator = 'return'
                 and ru2.kind = 'function-return'
          ''')

        print("done triple/parameter -> function-return", file = sys.stderr)

        # function/parameter -> triple-output linkages
        #   function parameter use inside the function.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2)
              select ru1.id, ru2.id
                from reg_use ru1
                     inner join symbol_table p
                       on     p.context = ru1.ref_id
                          and p.int1 = ru1.position
                     inner join triples t
                       on t.symbol_id = p.id
                     inner join reg_use ru2
                       on ru2.ref_id = t.id
               where ru1.kind = 'function'
                 and ru1.position_kind = 'parameter'
                 and p.kind = 'parameter'
                 and t.operator = 'local'
                 and ru2.kind = 'triple-output'
          ''')

        print("done function/parameter -> triple-output", file = sys.stderr)

        # function/var -> triple-output linkages
        #   function local variable use inside the function.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2)
              select ru1.id, ru2.id
                from reg_use ru1
                     inner join triples t
                       on t.symbol_id = ru1.position
                     inner join reg_use ru2
                       on ru2.ref_id = t.id
               where ru1.kind = 'function'
                 and ru1.position_kind = 'var'
                 and t.operator = 'local'
                 and ru2.kind = 'triple-output'
          ''')

        print("done function/var -> triple-output", file = sys.stderr)

    # Populate reg_group
    #with crud.db_transaction():
    if True:
        # Extend reg_use_linkage
        for level in itertools.count(1):
          with crud.db_transaction():
            rowcount = crud.execute('''
                           insert into reg_use_linkage
                             (reg_use_1, reg_use_2, level)
                             select l1.id, l2.id, ? + 1
                               from reg_use_linkage l1
                                    inner join reg_use_linkage l2
                                      on    l1.reg_use_1 = l2.reg_use_1
                                         or l1.reg_use_1 = l2.reg_use_2
                                         or l1.reg_use_2 = l2.reg_use_1
                                         or l1.reg_use_2 = l2.reg_use_2
                              where l1.id < l2.id
                                and l1.level = ?
                                and l2.level = ?
                         ''', (level, level, level))[0]
            if rowcount == 0: break
            print("inserted", rowcount, "rows for reg_use_linkage level", level, file = sys.stderr)

        print("done extending reg_use_linkage", file = sys.stderr)

        # Gather the roots into register_group
        crud.execute('''
            insert into register_group (id)
              select rul1.id
                from reg_use_linkage rul1
               where not exists (select null
                                   from reg_use_linkage rul2
                                  where rul2.level > 1
                                    and (   rul2.reg_use_1 = rul1.id
                                         or rul2.reg_use_2 = rul1.id))
          ''')

        print("done gathering roots into register_group", file = sys.stderr)

        # Assign reg_group_id top down:
        #   First do the roots.
        rowcount = crud.execute('''
            update reg_use_linkage
               set reg_group_id = id
             where id in (select id from register_group)
          ''')[0]

        print("done assigning reg_group_id to roots", file = sys.stderr)

        #   Then propogate the reg_group_id down into each child node.
        while rowcount:
            rowcount = crud.execute('''
                update reg_use_linkage
                   set reg_group_id = (
                               select reg_group_id
                                 from reg_use_linkage p   -- parent
                                where p.level > 1
                                  and p.reg_group_id notnull
                                  and (   p.reg_use_1 = reg_use_linkage.id
                                       or p.reg_use_2 = reg_use_linkage.id))
                 where reg_group_id isnull
                   and exists (select null
                                 from reg_use_linkage p
                                where p.level > 1
                                  and p.reg_group_id notnull
                                  and (   p.reg_use_1 = reg_use_linkage.id
                                       or p.reg_use_2 = reg_use_linkage.id))
              ''')[0]
            print("propogated", rowcount, "reg_group_ids", file = sys.stderr)
        print("done propogating reg_group_ids", file = sys.stderr)

    with crud.db_transaction():
        #   Finally, copy the reg_group_id into the reg_uses:
        #     But first, check to make sure each reg_use only has one
        #     register_group:
        it = crud.fetchall('''
            select id
              from reg_use ru
             where (select count(distinct rul.reg_group_id)
                      from reg_use_linkage rul
                     where rul.level = 1
                       and (   rul.reg_use_1 = ru.id
                            or rul.reg_use_2 = ru.id)) > 1
          ''')
        count = 0
        for id in it:
            print("duplicate register_groups for reg_use", id)
            count += 1
        if count:
            raise AssertionError(
                    "{} reg_uses have duplicate register_groups".format(count))
        #     Then copy the reg_group_ids down to the reg_uses
        crud.execute('''
            update reg_use
               set reg_group_id = (select reg_group_id
                                     from reg_use_linkage rul
                                    where rul.level = 1
                                      and (   rul.reg_use_1 = reg_use.id
                                           or rul.reg_use_2 = reg_use.id))
          ''')


######################### OLD figure_out_multi_use code ###################
"""
    # Copy reg_class and num_regs_output from code_seq to triples.
    with crud.db_transaction():
        crud.execute('''
            update triples
               set reg_class =       (select cs.output_reg_class
                                        from code_seq cs
                                       where triples.code_seq_id = cs.id),
                   num_regs_output = (select cs.num_output
                                        from code_seq cs
                                       where triples.code_seq_id = cs.id)
             where code_seq_id not null
               and operator not in
                     ('output', 'output-bit-set', 'output-bit-clear',
                      'global_addr', 'global', 'local_addr', 'local',
                      'call_direct', 'call_indirect', 'return',
                      'if_false', 'if_true')
          ''')

    for next_fn_layer in get_functions():
        for symbol_id in next_fn_layer:
            with crud.db_transaction():
                it = crud.fetchall('''
                         select exp_t.reg_class, exp_t.num_regs_output
                           from blocks b
                                inner join triples ret_t
                                  on b.id = ret_t.block_id
                                inner join triple_parameters tp
                                  on tp.parent_id = ret_t.id
                                inner join triples exp_t
                                  on exp_t.id = tp.parameter_id
                          where b.word_symbol_id = ?
                            and ret_t.operator = 'return'
                       ''', (symbol_id,))
                for rc, num in it:
                    # FIX: Finish!
                    pass

    with crud.db_transaction():
        # FIX: Need to add info for function call parameters!
        crud.execute('''
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
        crud.execute('''
            update triple_parameters
               set needed_reg_class = reg_class_for_parent
             where last_parameter_use
               and reg_class_for_parent notnull
          ''')

    with crud.db_transaction():
        rows = tuple(crud.read_as_dicts('triple_parameters',
                     'id', 'parameter_id', 'trashed', 'reg_class_for_parent',
                     'last_parameter_use',
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
                                {'id': row['id']},
                                needed_reg_class = next_rc,
                                move_needed_to_parent = 1)
                elif row['reg_class_for_parent'] is None:
                    break
                elif (next_rc, row['reg_class_for_parent']) in subsets:
                    next_rc = subsets[next_rc, row['reg_class_for_parent']]
                    crud.update('triple_parameters',
                                {'id': row['id']},
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
                                      {'id': row['id']},
                                      needed_reg_class = next_rc)
                                    crud.update('triple_parameters',
                                      {'id': params[i - 1]['id']},
                                      move_prior_to_needed = 1)
                                else:
                                    next_rc = subset
                                    crud.update('triple_parameters',
                                      {'id': row['id']},
                                      needed_reg_class = next_rc,
                                      move_needed_to_next = 1)
                                done = True
                            else:
                                subset = subsets.get((p['reg_class_for_parent'],
                                                      next_rc))
                                if subset is not None:
                                    next_rc = subset
                                    crud.update('triple_parameters',
                                      {'id': row['id']},
                                      needed_reg_class = next_rc,
                                      move_needed_to_parent = 1)
                                    done = True
                    if not done:
                        if sizes[row['reg_class_for_parent']] > sizes[next_rc]:
                            next_rc = row['reg_class_for_parent']
                            crud.update('triple_parameters',
                                        {'id': row['id']},
                                        needed_reg_class = next_rc)
                            crud.update('triple_parameters',
                                        {'id': params[i - 1]['id']},
                                        move_prior_to_needed = 1)
                        else:
                            crud.update('triple_parameters',
                                        {'id': row['id']},
                                        needed_reg_class = next_rc,
                                        move_needed_to_parent = 1)

    # Reset ghost flag for delinked triple_parameters:
    # FIX: This could violate a triple_order_constraint!
    #      But I don't think that it will because it should only be
    #      constant parameters that are delinked.
    with crud.db_transaction():
        # Mark delinks as ghosts.
        crud.execute('''
            update triple_parameters
               set ghost = 1
             where ghost = 0 and delink
          ''')

        # And pick another triple_parameter to evaluate the parameter triple.
        # Note that if all triple_parameters are marked 'delink', then the
        # parameter triple will not have any ghost = 0, so will not have code
        # generated for it.
        crud.execute('''
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
        crud.execute('''
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
"""


def create_reg_map(subsets, sizes, code_seqs):
    for next_fn_layer in get_functions():
        for symbol_id in next_fn_layer:
            reg_map = reg_map_for_fun(symbol_id, subsets, sizes, code_seqs)
            write_reg_map(reg_map)
        # FIX: What needs to happen between fn layers?

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

def reg_map_for_fun(symbol_id, subsets, sizes, code_seqs):
    fn_name, kind, suspends = crud.read1_as_tuple('symbol_table',
                                                  'label', 'kind', 'suspends',
                                                  id=symbol_id)
    locals = gather_locals(symbol_id, subsets, sizes)

    #print(fn_name, "locals", locals, file=sys.stderr)

    temp_map = map_temporaries(symbol_id, locals, kind, suspends, sizes)

    # FIX: figure out reg_map for fn and return it!


def gather_locals(fn_symbol_id, subsets, sizes):
    r'''Returns {symbol_id: (reg_class, num_regs, use_count, total_definitions)}
    '''

    params = frozenset(crud.read_column('symbol_table', 'id',
                                        context=fn_symbol_id,
                                        kind='parameter'))

    it = crud.fetchall('''
             select u.symbol_id, u.reg_class,
                    count(*), max(u.num_regs), sum(definition)
               from blocks b
                      inner join (  select t.block_id, t.symbol_id,
                                           0 as definition,
                                           needed_reg_class as reg_class,
                                           num_needed_regs as num_regs
                                      from triples t
                                     where operator = 'local'
                                  union
                                    select t2.block_id, tl.symbol_id, 1,
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

    ans = {}  # {symbol_id: (reg_class, num_regs, use_count, total_definitions)}

    #print('sizes', sizes, file=sys.stderr)

    for id, reg_iter in itertools.groupby(it, lambda t: t[0]):
        reg_classes = collections.defaultdict(int)  # {rc: num_uses}
        max_regs = 0
        total_definitions = 0
        saved_reg_iter = tuple(info for info in reg_iter if info[1] is not None)
        for _, reg_class, count, max_needed, definitions in saved_reg_iter:
            reg_classes[reg_class] = count
            if max_needed > max_regs: max_regs = max_needed
            total_definitions += definitions
        for (_, rc1, count1, _, _), (_, rc2, count2, _, _) \
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
        if id in params: count += 1
        ans[id] = (rc, max_regs, count, total_definitions)
    return ans

def map_temporaries(fn_symbol_id, locals, kind, suspends, sizes):
    r'''Returns {symbol_id: (reg_class, num_regs, use_count, total_definitions)}
    '''
    rows = crud.fetchall('''
               select b.id block_id, t.id, t.abs_order_in_block,
                      t.needed_reg_class t_needed_reg_class,
                      t.num_needed_regs t_num_needed_regs,
                      t.reg_class t_reg_class,
                      t.num_regs_output t_num_regs_output,
                      tp.parent_id, tp.ghost, tp.parameter_num,
                      tp.reg_class_for_parent, tp.num_regs_for_parent,
                      tp.needed_reg_class tp_needed_reg_class,
                      tp.move_prior_to_needed, tp.move_needed_to_parent,
                      tp.move_needed_to_next,
                      rr.reg_class rr_reg_class, rr.num_needed rr_num_needed
                 from blocks b
                      inner join triples t
                        on b.id = t.block_id
                      left outer join triple_parameters tp
                        on t.id = tp.parameter_id
                      left outer join reg_requirements rr
                        on t.code_seq_id = rr.code_seq_id
                where b.word_symbol_id = ?
                order by b.id, t.id, tp.parent_id
             ''', (fn_symbol_id,), ctor_factory = crud.row.factory_from_cur)
    triples = {}  # {id: row}
    for id, tps in itertools.groupby(rows, lambda r: (r.block_id, r.id)):
        id = id[1]
        tps = iter(tps)
        first_row = next(tps)
        #print("first_row for triple", id, first_row, file=sys.stderr)
        #print("abs_order_in_block", first_row.abs_order_in_block,
        #      file=sys.stderr)
        if first_row.abs_order_in_block is not None:
            triples[id] = first_row
            triples[id].tps = []
            for parent_id, rrs \
             in itertools.groupby(itertools.chain((first_row,), tps),
                                  lambda r: r.parent_id):
                rrs = iter(rrs)
                first_row = next(rrs)
                if first_row.parent_id is not None:
                    triples[id].tps.append(first_row)
                triples[id].rrs = {row.rr_reg_class: row.rr_num_needed
                                   for row in itertools.chain((first_row,), rrs)
                                   if row.rr_reg_class is not None}

    ordered_triples = sorted(triples.values(),
                             key=lambda r: (r.block_id, r.abs_order_in_block))
    for t in ordered_triples:
        for tp in t.tps:
            tp.parent = triples[tp.parent_id]
        t.tps.sort(key=lambda tp: tp.parent.abs_order_in_block)
        #print("triple", t.block_id, t.id, t.abs_order_in_block, file=sys.stderr)
        #print("  rrs", t.rrs, file=sys.stderr)
        #for tp in t.tps:
        #    print("  tp", tp.parent.id, tp.parent_id,
        #          tp.parent.abs_order_in_block, tp.ghost, file=sys.stderr)

    #brains = reg_map.fn_reg_map(fn_symbol_id, subsets, sizes)
    #for t in ordered_triples:
    #    brains.alloc(...)

def write_reg_map(reg_map):
    # FIX: implement this!
    pass

def pairs(it):
    r'''Generates pairs from seq.

        >>> tuple(pairs(()))
        ()
        >>> tuple(pairs((1,)))
        ()
        >>> tuple(pairs((1,2,3)))
        ((1, 2), (2, 3))
    '''
    it = iter(it)
    prior = next(it)
    for x in it:
        yield prior, x
        prior = x

