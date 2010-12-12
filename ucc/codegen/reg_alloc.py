# reg_alloc.py

r'''Register allocation code.

The only function called here from outside is alloc_reg (called from
gen_assembler in ucc/codegen/codegen.py).
'''

import sys   # for debug traces
import itertools

from ucc.database import crud
from ucc.codegen import code_seq, extend_sqlite, populate_register_groups

def alloc_regs():
    # Set up sqlite3 user functions:
    extend_sqlite.register_functions()

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

    for attempt_number in itertools.count(1):
        if populate_register_groups.attempt_register_allocation(attempt_number):
            break

def get_reg_class_sizes():
    r'''Returns the number of registers in each reg_class.

    The return value is {reg_class: number_of_registers}
    '''
    return dict(crud.fetchall('''
                    select reg_class, count(reg)
                      from reg_in_class
                     group by reg_class
                  '''))

def delete():
    with crud.db_transaction():
        crud.delete('overlaps')
        crud.delete('reg_use')
        crud.delete('reg_use_linkage')
        crud.delete('rg_neighbors')
        crud.delete('rawZ')
        crud.delete('register_group')

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

def group_summary(it, summary_fn, key = None):
    for key, detail in itertools.groupby(it, key):
        yield summary_fn(key, detail)

