# reg_alloc.py

r'''Register allocation code.

The only function called here from outside is alloc_reg (called from
gen_assembler in ucc/codegen/codegen.py).

The underlying algorithm here is taken from:

    A Generalized Algorithm for Graph-Coloring Register Allocation
        Michael D. Smith, Norman Ramsey, and Glenn Holloway
            Division of Engineering and Applied Sciences
            Harvard University

printed in Proceedings of the ACM SIGPLAN ’04 Conference on Programming
Language Design and Implementation

see: http://www.cs.tufts.edu/~nr/pubs/gcra-abstract.html
'''

import time  # for testing query execution times
import sys   # for debug traces
import itertools
import collections
import operator

from ucc.database import crud
from ucc.codegen import code_seq

class aggr_rc_subset:
    r'''Sqlite3 aggregate function for aggr_rc_subset.
    
    Produces the rc that is a subset of each of the submitted entries.

        >>> subsets = {(1, 1): 1, (1, 3): 1, (3, 1): 1, 
        ...            (2, 2): 2, (2, 3): 2, (3, 2): 2, (3, 3): 3}
        >>> rcs = aggr_rc_subset(subsets)
        >>> rcs.finalize()       # NULL for 0 rows.
        >>> rcs = aggr_rc_subset(subsets)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(3)
        >>> rcs.finalize()
        2
        >>> rcs = aggr_rc_subset(subsets)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(3)
        >>> rcs.step(1)
        >>> rcs.step(1)
        >>> rcs.finalize()
        Traceback (most recent call last):
           ...
        AssertionError: aggr_rc_subset -- no subset possible
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

        # Return subset of all rc's:
        ans = None
        for rc in self.rc_counts:
            if ans is None: ans = rc
            else:
                ans = self.subsets.get((ans, rc))
                assert ans is not None, "aggr_rc_subset -- no subset possible"
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
    # Set up sqlite3 user functions:
    global Subsets
    Subsets = get_reg_class_subsets()  # needed by rc_subset and aggr_rc_subset
    crud.Db_conn.db_conn.create_function("rc_subset", 2, rc_subset)
    crud.Db_conn.db_conn.create_function("chk_num_regs", 2, chk_num_regs)
    crud.Db_conn.db_conn.create_aggregate("aggr_rc_subset", 1, aggr_rc_subset)
    crud.Db_conn.db_conn.create_aggregate("aggr_num_regs", 1, aggr_num_regs)

    figure_out_register_groups()

    # FIX: Are these actually used anywhere?
    sizes = get_reg_class_sizes()
    code_seqs = code_seq.get_code_seq_info()

    create_reg_map(Subsets, sizes, code_seqs)

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

def figure_out_register_groups():
    r'''Creates reg_uses, reg_use_linkages and register_groups.
    '''

    # start from a clean slate
    delete()

    # copy information to and from triples and triple_parameters for easier
    # access.
    prepare_triples()

    # Who all needs a register?
    populate_reg_use()

    # Which pairs of reg_uses represent the same value and should be put into
    # the same register?
    populate_reg_use_linkage()

    # Each register group represents a set of linked reg_uses.  The goal will
    # be to assign a register to each register_group.
    populate_register_group()

    # Split register_groups that include conflicting reg_uses.  A conflict
    # could be due to incompatible register classes, or two reg_uses for the
    # same kind and ref_id.
    eliminate_conflicts()

    # Sets the reg_class and num_registers in each register_group.
    set_reg_classes()

def prepare_triples():
    r'''Do some prep work on the triples.

    This is just copying information between triple_parameters and triples to
    make it easier to access (without having to join to the other table).
    '''

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

    # Copy reg_class_for_parent, num_regs_for_parent, trashed and delink from
    # code_seq_parameter.
    with crud.db_transaction():
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

def populate_reg_use():
    r'''This populates the reg_use table.

    The reg_use table brings all of the various situations where a register is
    needed together into one place in preperation for register allocation.

    This is a list of the different places where a register is needed:
        - triple output for normal operators
        - triple output for reference to global and local variable
        - triple parameter (input to triple)
        - 'call_direct' triple-output
        - 'call_direct' triple/parameter
        - triple/temp
        - function
        - function-return
        - block-start-marker
        - block-end-marker
    '''

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
                 and (   exists (select null
                                   from triple_parameters tp
                                  where t.id = tp.parameter_id
                                    and not tp.delink)
                      or exists (select null
                                   from triple_labels tl
                                  where t.id = tl.triple_id))
          ''')

        # Populate reg_use for triple-output for 'global' and 'local'
        crud.execute('''
            insert into reg_use
              (kind, ref_id, initial_reg_class, num_registers, is_definition,
               block_id, abs_order_in_block)
              select 'triple-output', t.id, sym.reg_class, sym.num_registers, 1,
                     t.block_id, t.abs_order_in_block
                from triples t
                     inner join symbol_table sym
                       on t.symbol_id = sym.id
               where t.operator in ('global', 'local')
                 and (   exists (select null
                                   from triple_parameters tp
                                  where t.id = tp.parameter_id
                                    and not tp.delink)
                      or exists (select null
                                   from triple_labels tl
                                  where t.id = tl.triple_id))
          ''')

        # Populate reg_use for triple/parameter
        crud.execute('''
            insert into reg_use
              (kind, ref_id, position_kind, position,
               initial_reg_class, num_registers,
               block_id, abs_order_in_block)
              select 'triple', t.id, 'parameter', csp.parameter_num,
                     csp.reg_class, csp.num_registers,
                     t.block_id, t.abs_order_in_block
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
                 and not tp.delink
          ''')

        # Populate reg_use for 'call_direct' triple-output
        crud.execute('''
            insert into reg_use
              (kind, ref_id, is_definition, block_id, abs_order_in_block)
              select 'triple-output', t.id, 1, t.block_id, t.abs_order_in_block
                from triples t
               where t.operator = 'call_direct'
                 and (   exists (select null
                                   from triple_parameters tp
                                  where t.id = tp.parameter_id
                                    and not tp.delink)
                      or exists (select null
                                   from triple_labels tl
                                  where t.id = tl.triple_id))
          ''')

        # Populate reg_use for 'call_direct' triple/parameter
        crud.execute('''
            insert into reg_use
              (kind, ref_id, position_kind, position,
               block_id, abs_order_in_block)
              select 'triple', t.id, 'parameter', tp.parameter_num,
                     t.block_id, t.abs_order_in_block
                from triples t
                     inner join triple_parameters tp
                       on t.id = tp.parent_id
               where t.operator = 'call_direct'
                 and not tp.delink
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
                     local.num_registers
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

        # Populate reg_use for block-start-marker:
        crud.execute('''
            insert into reg_use
              (kind, ref_id, position_kind, position, num_registers, block_id,
               abs_order_in_block)
              select 'block-start-marker', b.id, fn_ru.position_kind,
                     fn_ru.position, fn_ru.num_registers, b.id, 0
                from reg_use fn_ru
                     inner join blocks b
                       on fn_ru.ref_id = b.word_symbol_id
               where fn_ru.kind = 'function'
          ''')

        # Populate reg_use for block-end-marker:
        crud.execute('''
            insert into reg_use
              (kind, ref_id, position_kind, position, num_registers, block_id,
               abs_order_in_block)
              select 'block-end-marker', ru.ref_id, ru.position_kind,
                     ru.position, ru.num_registers, ru.block_id, 999999999
                from reg_use ru
               where ru.kind = 'block-start-marker'
          ''')

def populate_reg_use_linkage():
    r'''Populate the reg_use_linkage table.

    This table pairs the reg_uses that should try to be placed into the same
    register.
    '''

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

        # triple-output -> block-start-marker linkages
        #   binding block-start-marker to triple-output of 'local' triples.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2, is_segment)
              select ru1.id, ru2.id, 1
                from reg_use ru1
                     inner join triples t
                       on ru1.ref_id = t.block_id
                     inner join symbol_table local
                       on local.id = t.symbol_id
                     inner join reg_use ru2
                       on ru2.ref_id = t.id
               where ru1.kind = 'block-start-marker'
                 and t.operator = 'local'
                 and case ru1.position_kind
                       when 'parameter' then ru1.position = local.int1
                       else ru1.position = local.id
                     end
                 and ru2.kind = 'triple-output'
          ''')

        print("done triple-output -> block-start-marker", file = sys.stderr)

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

        # Gather last references to locals
        it = crud.fetchall('''
                 -- get labels
                 select t.block_id as block_id, tl.symbol_id as symbol_id,
                        ifnull(p.id, t.id) as triple_id,
                        tp.parameter_num as parameter_id,
                        ifnull(p.abs_order_in_block, t.abs_order_in_block)
                          as abs_order_in_block
                   from triples t
                        inner join triple_labels tl
                          on tl.triple_id = t.id
                        inner join symbol_table var
                          on tl.symbol_id = var.id
                          and var.kind in ('parameter', 'var')
                        left join triple_parameters tp
                          on tp.parameter_id = t.id
                        left join triples p
                          on tp.parent_id = p.id

                 union

                 -- get locals
                 select t.block_id, t.symbol_id as symbol_id,
                        p.id as triple_id, tp.parameter_num,
                        p.abs_order_in_block
                   from triples t
                        inner join triple_parameters tp
                          on tp.parameter_id = t.id
                        inner join triples p
                          on tp.parent_id = p.id
                  where t.operator = 'local'

                  order by block_id, symbol_id,
                           abs_order_in_block desc, parameter_num desc
          ''')
        crud.executemany('''
            insert into last_locals
                     (block_id, symbol_id, triple_id, tp_parameter_num)
              values (?, ?, ?, ?)
          ''', group_summary(it, lambda _, detail: next(iter(detail))[:-1],
                             key = lambda x: (x[0], x[1])))

        # triple/parameter -> block-end-marker linkages
        #   links last triple/parameter in last_locals to block-end-marker.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2, is_segment)
              select ru1.id, ru2.id, 1
                from last_locals l
                     inner join symbol_table sym
                       on l.symbol_id = sym.id
                     inner join reg_use ru1
                       on ru1.kind = 'triple'
                       and ru1.position_kind = 'parameter'
                       and l.triple_id = ru1.ref_id
                       and l.tp_parameter_num = ru1.position
                     inner join reg_use ru2
                       on ru2.kind = 'block-end-marker'
                       and ru2.ref_id = l.block_id
                       and ru2.position_kind = sym.kind
                       and case ru2.position_kind
                             when 'parameter' then ru2.position = sym.int1
                             else ru2.position = sym.id
                           end
               where l.tp_parameter_num notnull
          ''')

        print("done triple/parameter -> block-end-marker", file = sys.stderr)

        # triple-output -> block-end-marker linkages
        #   links last triple-output in last_locals to block-end-marker.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2, is_segment)
              select ru1.id, ru2.id, 1
                from last_locals l
                     inner join symbol_table sym
                       on l.symbol_id = sym.id
                     inner join reg_use ru1
                       on ru1.kind = 'triple-output'
                       and l.triple_id = ru1.ref_id
                     inner join reg_use ru2
                       on ru2.kind = 'block-end-marker'
                       and ru2.ref_id = l.block_id
                       and ru2.position_kind = sym.kind
                       and case ru2.position_kind
                             when 'parameter' then ru2.position = sym.int1
                             else ru2.position = sym.id
                           end
               where l.tp_parameter_num isnull
          ''')

        print("done triple-output -> block-end-marker", file = sys.stderr)

        # block-start-marker -> block-end-marker linkages
        #   links block-start-marker to block-end-marker if var not set or
        #   referenced in block.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2, is_segment)
              select ru1.id, ru2.id, 1
                from reg_use ru1
                     inner join reg_use ru2
                       on ru2.kind = 'block-end-marker'
                       and ru1.ref_id = ru2.ref_id
                       and ru1.position_kind = ru2.position_kind
                       and ru1.position = ru2.position
               where ru1.kind = 'block-start-marker'
                 and not exists (select null
                                   from last_locals l
                                        inner join symbol_table sym
                                          on sym.id = l.symbol_id
                                  where l.block_id = ru1.ref_id
                                    and case ru1.position_kind
                                          when 'parameter'
                                            then sym.int1 = ru1.position
                                          else sym.id = ru1.position
                                        end)
          ''')

        print("done block-start-marker -> block-end-marker", file = sys.stderr)

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

        # delete unused block-*-marker reg_uses
        crud.execute('''
            delete from reg_use
             where kind in ('block-start-marker', 'block-end-marker')
               and not exists (select null
                                 from reg_use_linkage rul
                                where reg_use_1 = reg_use.id
                                   or reg_use_2 = reg_use.id)
          ''')

        print("done deleting unused block-*-marker reg_uses", file = sys.stderr)

        # function -> block-*-marker linkages
        #   function local variable linkage to block-*-markers for those
        #   variables.
        crud.execute('''
            insert into reg_use_linkage (reg_use_1, reg_use_2)
              select ru1.id, ru2.id
                from reg_use ru1
                     inner join blocks b
                       on ru1.ref_id = b.word_symbol_id
                     inner join reg_use ru2
                       on b.id = ru2.ref_id
                       and ru1.position_kind = ru2.position_kind
                       and ru1.position = ru2.position
               where ru1.kind = 'function'
                 and ru2.kind in ('block-start-marker', 'block-end-marker')
          ''')

        print("done function -> block-*-marker", file = sys.stderr)

def populate_register_group():
    r'''Populate the register_group table.

    This table has one row per set of linked reg_uses.

    This function can be called repeatedly.  It deletes all prior
    register_groups each time and starts over scratch, but it observes the
    'broken' flag in the reg_use_linkage; which may lead to different results.

    The algorithm here does not end up assigning consecutive ids to the
    register_groups.  Rather, there will be missing ids; but nobody cares.
    
    First, each reg_use is given unique reg_group_id, by simply copying it's
    own id to its reg_group_id.

    Then we want to select a unique reg_group_id amoung each set of linked
    reg_uses.  We do this by selecting the min reg_group_id within each set and
    updating all of the reg_use.reg_group_ids to this min value.  Since the
    links are only pairwise, this update is done by repeatedly updating the
    reg_group_id of each reg_use to the min of all of its linked reg_uses.
    This will eventually propogate the min value to all of reg_uses in the set
    through transitive closure.
    '''

    with crud.db_transaction():
        # Delete any prior register_groups
        crud.delete('register_group')

        # And set all broken 1's back to 0 for now.  These will be
        # recalculated later by eliminate_conflicts.  Leave other broken
        # values unchanged (these were set due to graph coloring conflicts on
        # a prior pass).
        crud.update('reg_use_linkage', {'broken': 1}, broken=0)

    with crud.db_transaction():
        # Tentatively assign all reg_use.reg_group_ids as simply the reg_use.id
        # (a simple source of unique numbers).
        crud.execute('''
            update reg_use
               set reg_group_id = id
          ''')

        # Now set the reg_group_ids of all pairs of reg_uses that are linked
        # through a reg_use_linkage to be the same number.  Do this by setting
        # the one with the greater number to match the one with the smaller
        # number.  Repeat this until no more reg_uses are updated.
        rowcount = 1
        while rowcount:
            rowcount = crud.execute('''
                update reg_use
                   set reg_group_id =
                     -- Set reg_group_id to min reg_group_id of all directly
                     -- linked reg_uses.
                     (select min(min(ru1.reg_group_id), min(ru2.reg_group_id))
                        from reg_use_linkage
                             inner join reg_use ru1
                               on reg_use_1 = ru1.id
                             inner join reg_use ru2
                               on reg_use_2 = ru2.id
                       where not broken
                         and ru1.reg_group_id != ru2.reg_group_id
                         and (   ru1.reg_group_id = reg_use.reg_group_id
                              or ru2.reg_group_id = reg_use.reg_group_id))
                 where exists (
                         select null
                           from reg_use_linkage
                                inner join reg_use ru1
                                  on reg_use_1 = ru1.id
                                inner join reg_use ru2
                                  on reg_use_2 = ru2.id
                          where not broken
                            and ru1.reg_group_id != ru2.reg_group_id
                            and (   ru1.reg_group_id = reg_use.reg_group_id
                                 or ru2.reg_group_id = reg_use.reg_group_id)
                            and min(ru1.reg_group_id, ru2.reg_group_id) <
                                  reg_use.reg_group_id)
              ''')[0]
            print("updated", rowcount, "reg_use.reg_group_ids",
                  file = sys.stderr)
        print("done updating reg_group_ids", file = sys.stderr)

        # Gather the remaining reg_group_ids into register_group
        crud.execute('''
            insert into register_group (id)
              select distinct reg_group_id from reg_use
          ''')

        print("done populating register_group", file = sys.stderr)

def eliminate_conflicts():
    r'''Eliminate conflicts between reg_uses in the same register_group.

    The two causes of conflict are incompatible register classes, and two
    reg_uses for the same kind and ref_id.

    This function sets the 'broken' flag in affected reg_use_linkages to 1.
    If no other function sets uses 1 for the broken value, this function can
    be re-run.
    '''
    with crud.db_transaction():
        # all links as two-tuples
        links1 = tuple(crud.read_as_tuples('reg_use_linkage',
                                           'reg_use_1', 'reg_use_2',
                                           broken=0))
        # include reverse links, and sort by first id
        links = sorted(itertools.chain(links1, ((b, a) for a, b in links1)))

        # {id: {neighbor_id: link_count}} based on links
        neighbors = dict((use, collections.Counter(u[1] for u in uses))
                         for use, uses
                          in itertools.groupby(links,
                                               key=operator.itemgetter(0)))
        #print("neighbors", neighbors, file=sys.stderr)

        # reg_group_id, id1, id2 of all conflicts (id1 < id2).
        # sorted by reg_group_id.
        it = crud.fetchall('''
                 select ru1.reg_group_id, ru1.id as id1, ru2.id as id2
                   from reg_use ru1
                        inner join reg_use ru2
                          on ru1.reg_group_id = ru2.reg_group_id
                          and ru1.id < ru2.id
                  where ru1.initial_reg_class notnull
                    and ru2.initial_reg_class notnull
                    and not exists (select null
                                      from reg_class_subsets
                                     where rc1 = ru1.initial_reg_class
                                       and rc2 = ru2.initial_reg_class)
                     or ru1.kind = ru2.kind
                    and ru1.ref_id = ru2.ref_id
                  order by ru1.reg_group_id
               ''', ctor_factory=crud.row.factory_from_cur)

        # split conflicts within each reg_group_id, this will replace the
        # register_group with conflicting reg_uses with a set of
        # register_groups with non-conflicting reg_uses.
        for reg_group_id, conflicts \
         in itertools.groupby(it, operator.attrgetter('reg_group_id')):

            # only for print ..., comment out with print
            conflicts = tuple(conflicts)
            print("reg_group_id", reg_group_id, "conflicts", conflicts,
                  file=sys.stderr)

            # split yields groups of non-conflicting ru_ids
            for ru_ids in split(conflicts, neighbors):
                # create new register_group (let sqlite assign reg_group_id)
                ru_qmarks = ', '.join(('?',) * len(ru_ids))
                new_group_id = crud.execute('''
                    insert into register_group (reg_class, num_registers)
                    select aggr_rc_subset(initial_reg_class),
                           aggr_num_regs(num_registers)
                      from reg_use
                     where id in ({})
                  '''.format(ru_qmarks),
                  ru_ids)[1]
                print("new_group_id", new_group_id, file=sys.stderr)

                # update reg_group_id to new_group_id in all ru_ids
                crud.execute('''
                    update reg_use
                       set reg_group_id = ?
                     where id in ({})
                  '''.format(ru_qmarks),
                  (new_group_id,) + ru_ids)

            # delete old register_group
            crud.delete('reg_group', id=reg_group_id)

        # set broken flag on all reg_use_linkages for reg_uses now in
        # different register_groups.
        crud.execute('''
            update reg_use_linkage
               set broken = 1
             where not broken
               and (select ru1.reg_group_id != ru2.reg_group_id
                      from reg_use ru1, reg_use ru2
                     where ru1.id = reg_use_linkage.reg_use_1
                       and ru2.id = reg_use_linkage.reg_use_2)
         ''')

        # set reg_group_id in all reg_use_linkages to reg_use_1.reg_group_id.
        crud.execute('''
            update reg_use_linkage
               set reg_group_id = (select reg_group_id
                                     from reg_use ru
                                    where ru.id = reg_use_linkage.reg_use_1)
             where not broken
         ''')

def set_reg_classes():
    r'''Sets the reg_class and num_registers in each register_group.
    '''
    with crud.db_transaction():
        crud.execute('''
            update register_group
               set reg_class = (select aggr_rc_subset(initial_reg_class)
                                  from reg_use ru1
                                 where ru1.reg_group_id = register_group.id),
                   num_registers = (select aggr_num_regs(num_registers)
                                      from reg_use ru2
                                     where ru2.reg_group_id = register_group.id)
         ''')

def group_summary(it, summary_fn, key = None):
    for key, detail in itertools.groupby(it, key):
        yield summary_fn(key, detail)

def split(conflicts, neighbors):
    r'''Yields disjoint sets of ru_ids containing no conflicts between them.

        'conflicts' is a sequence of objects with 'id1' and 'id2' attributes.
        'neighbors' shows all ru_id linkage as {id: {neighbor_id: link_count}}

        >>> class conflict:
        ...     def __init__(self, id1, id2):
        ...         self.id1, self.id2 = id1, id2
        ...     def __repr__(self):
        ...         return "conflict({}, {})".format(self.id1, self.id2)
        >>> def pp(it):
        ...     return sorted(sorted(x) for x in it)
        >>> pp(split((conflict(1, 2), conflict(1, 3),
        ...           conflict(2, 4), conflict(3, 4)),
        ...          {}))
        [[1, 4], [2, 3]]
        >>> pp(split((conflict(1, 2), conflict(3, 4)),
        ...          {1: {2:1, 3:1, 4:0}, 2: {1:1, 3:0, 4:1},
        ...           3: {1:1, 2:0, 4:1}, 4: {1:0, 2:1, 3:1}}))
        [[1, 3], [2, 4]]
        >>> pp(split((conflict(1, 2), conflict(1, 3), conflict(1, 4),
        ...           conflict(1, 5), conflict(2, 3), conflict(2, 5),
        ...           conflict(3, 4), conflict(4, 5)),
        ...          {}))
        [[1], [2, 4], [3, 5]]
        >>> pp(split((conflict(1, 2), conflict(1, 3), conflict(1, 4),
        ...           conflict(1, 5), conflict(2, 3), conflict(2, 5),
        ...           conflict(3, 4)),
        ...          {}))
        [[1], [2, 4], [3, 5]]
        >>> pp(split((conflict(1, 2),),
        ...          {1: {2:1, 3:1, 4:0}, 2: {1:1, 3:0, 4:1},
        ...           3: {1:1, 2:0, 4:1}, 4: {1:0, 2:1, 3:1}}))
        [[1, 3], [2, 4]]
    '''

    # d1 = {ru_id: {conflicting_ru_id}}
    d1 = collections.defaultdict(set)
    for c in conflicts:
        d1[c.id1].add(c.id2)
        d1[c.id2].add(c.id1)

    def pick_color(colors, id):
        r'''Pick the best color from colors for id.

        Picks the color assigned to the greatest number of links to id.
        '''
        if len(colors) == 1: return colors.pop()
        n = neighbors.get(id, collections.Counter())
        return max(((c, sum(n[id] for id in ids_by_color[c])) for c in colors),
                   key=lambda t: t[1])[0]

    # colors are numbered starting at 1
    colors = {}                         # {id: color}
    ids_by_color = {}                   # {color: {id}}
    num_colors = 0

    # stack conflicting ru_ids, picking the one with the least conflicts each
    # time.
    stack = collections.deque()         # [(id, {conflicting_ru_id})]
    while d1:
        k, v = item = min(d1.items(), key=lambda item: len(item[1]))
        stack.appendleft(item)
        del d1[k]
        for x in v: d1[x].remove(k)

    # assign colors
    for k, v in stack:
        #print("split: unstacking", k, v, file=sys.stderr)
        ok_colors = ids_by_color.keys() - (colors[id] for id in v)
        if ok_colors:
            color = pick_color(ok_colors, k)
        else:
            num_colors += 1
            color = num_colors
            ids_by_color[color] = set()
        colors[k] = color
        ids_by_color[color].add(k)

    print("split: stack is", tuple(stack), file=sys.stderr)
    print("split: ids_by_color", ids_by_color, file=sys.stderr)

    def pick_best_color(id):
        neighbor_ids = neighbors[id]
        color, colored_sum = max(((c, sum(neighbor_ids[nid] for nid in ids))
                                  for c, ids in ids_by_color.items()),
                                 key=operator.itemgetter(1))
        uncolored_sum = sum(neighbor_ids[nid]
                            for nid in neighbor_ids.keys() - colors.keys())
        return color, colored_sum, uncolored_sum

    nonconflicting_ids = neighbors.keys() - colors.keys()
    while nonconflicting_ids:
        # pick the next_id and color to assign with the greatest number of
        # neighbors with that color.  If a tie, pick the one with the greatest
        # number of uncolored neighbors.
        next_id, (color, colored_sum, uncolored_sum) = \
            max(((id, pick_best_color(id)) for id in nonconflicting_ids),
                key=lambda t: t[1][1:2])

        if not colored_sum: color = 1
        colors[next_id] = color
        ids_by_color[color].add(next_id)
        nonconflicting_ids.remove(next_id)

    return ids_by_color.values()

def create_reg_map(subsets, sizes, code_seqs):
    figure_out_rg_neighbors()

    with crud.db_transaction():
        # {vertex_id: parent_vertex_id}
        parent_vertex = dict(crud.read_as_tuples('vertex', 'id', 'parent'))
        def gen_parents(x):
            while x:
                yield x
                x = parent_vertex[x]
        parents_of_vertex = {x: tuple(gen_parents(x)) for x in parent_vertex}
        print("parents_of_vertex", parents_of_vertex, file=sys.stderr)

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

        # perform final Z(n, R) calculation for register_groups.
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

    with crud.db_transaction():
        # stack register_groups
        stacking_order = iter(itertools.count(1))
        row_count = 1  # force first iteration
        while row_count:
            i = next(stacking_order)
            row_count = crud.execute('''
                update register_group
                   set stacking_order = ?
                 where stacking_order isnull
                   and Z < 
                   (select class_size
                      from reg_class rc
                     where rc.id = register_group.reg_class)
              ''', (i,))[0]
            print("stacking", i, "got", row_count, file=sys.stderr)
            if row_count == 0:
                max_stacking_order = i - 1
                break

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

def figure_out_rg_neighbors():
    r'''Figures out rg_neighbors.

    First figures out overlaps, then uses this for rg_neighbors.

    This function deletes all overlaps and rg_neighbors first so that it can
    be run multiple times.
    '''

    # Delete overlaps and rg_neighbors
    with crud.db_transaction():
        crud.delete('overlaps')
        crud.delete('rg_neighbors')

    with crud.db_transaction():
        # Figure out overlaps between reg_use_linkages and reg_uses in other
        # register_groups.  These go in the overlaps table.
        crud.execute('''
            insert into overlaps (linkage_id, reg_use_id)
            select rul.id, ru3.id
              from reg_use_linkage rul
                   inner join reg_use ru1
                     on ru1.id = reg_use_1
                   inner join reg_use ru2
                     on ru2.id = reg_use_2
                     and ru1.block_id = ru2.block_id
                   inner join reg_use ru3
                     on ru1.block_id = ru3.block_id
                     and ru1.abs_order_in_block <= ru3.abs_order_in_block
                     and ru2.abs_order_in_block >= ru3.abs_order_in_block
             where ru1.block_id notnull
               and ru1.abs_order_in_block notnull
               and ru2.block_id notnull
               and ru2.abs_order_in_block notnull
               and ru3.block_id notnull
               and ru3.abs_order_in_block notnull
               and not rul.broken
               and ru3.reg_group_id != ru1.reg_group_id
          ''')

        # Figure out rg_neighbors.  These are the conflicting register_groups.
        crud.execute('''
            insert into rg_neighbors (rg1, rg2)
            select distinct min(rul.reg_group_id, ru.reg_group_id),
                            max(rul.reg_group_id, ru.reg_group_id)
              from overlaps ov
                   inner join reg_use_linkage rul
                     on ov.linkage_id = rul.id
                   inner join reg_use ru
                     on ov.reg_use_id = ru.id
          ''')

        # Link overlaps to rg_neighbors.
        crud.execute('''
            update overlaps
               set rg_neighbor_id = (
                   select rgn.id
                     from rg_neighbors rgn
                          inner join reg_use_linkage rul
                            on rul.reg_group_id in (rg1, rg2)
                          inner join reg_use ru
                            on ru.reg_group_id in (rg1, rg2)
                            and ru.reg_group_id != rul.reg_group_id
                    where overlaps.linkage_id = rul.id
                      and overlaps.reg_use_id = ru.id)
          ''')

#def create_reg_map(subsets, sizes, code_seqs):
#    for next_fn_layer in get_functions():
#        for symbol_id in next_fn_layer:
#            reg_map = reg_map_for_fun(symbol_id, subsets, sizes, code_seqs)
#            write_reg_map(reg_map)
#        # FIX: What needs to happen between fn layers?

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

def delete():
    with crud.db_transaction():
        crud.delete('reg_use')
        crud.delete('reg_use_linkage')
        crud.delete('register_group')

