# expand_assembler.py

import sys  # for debug traces
import collections
import itertools

from ucc.database import crud

def expand_assembler():
    order_blocks()
    gen_instructions()

def order_blocks():
    it = crud.fetchall('''
        select fn.label, b.id, name, next, next_conditional
          from blocks b
               inner join symbol_table fn
                 on fn.id = b.word_symbol_id
         order by fn.label
      ''')
    for fn, blocks in itertools.groupby(it, lambda x: x[0]):
        order_blocks_in_fun(fn, blocks)

    it = crud.fetchall('''
        select caller_id, called_id
          from fn_calls
         where depth = 1
         order by caller_id
      ''')
    call_tree = {caller: tuple(cld for clr, cld in called)
                 for caller, called in itertools.groupby(it, lambda x: x[0])}
    with crud.db_transaction():
        crud.execute('''
            update symbol_table
               set fn_order = 0.0
             where kind in ('function', 'task')
          ''')
        def update_subtree(root, offset, span):
            nodes = list(call_tree.get(root, ()))
            nodes.insert(len(nodes)//2, root)
            subspan = span / len(nodes)
            for node in nodes:
                if node != root:
                    update_subtree(node, offset, subspan)
                else:
                    crud.execute('''
                        update symbol_table
                           set fn_order = fn_order + ?
                         where id = ?
                      ''', (offset + subspan / 2, node))
                offset += subspan

def order_blocks_in_fun(fn, blocks):
    with crud.db_transaction():
        block_dict = {}
        next_dict = collections.defaultdict(set)
        next_cond = collections.defaultdict(set)
        for _, id, name, next_block, next_conditional in blocks:
            block_dict[name] = id, next_block, next_conditional
            if next_block: next_dict[next_block].add(name)
            if next_conditional: next_cond[next_conditional].add(name)
        seen = set()
        sequencer = iter(itertools.count(1))
        def follow(name, stop = None):
            if name not in seen and name != stop:
                seen.add(name)
                id, next_block, next_conditional = block_dict[name]
                crud.update('blocks', {'id': id}, block_order = next(sequencer))
                if next_conditional and next_conditional not in seen:
                    follow(next_conditional, next_block)
                if next_block and next_block not in seen:
                    follow(next_block)
        follow(fn)

def gen_instructions():
    for fn in crud.read_column('symbol_table', 'id', kind=('function', 'task'),
                               order_by='fn_order'):
        with crud.db_transaction():
            for current_block, next_block \
             in with_next(crud.read_as_tuples('blocks', 'id', 'name', 'next',
                                              'next_conditional',
                                              word_symbol_id=fn,
                                              order_by='block_order')):
                gen_block(fn, current_block, next_block)

def with_next(it):
    r'''Yields elements of it with their next element as a 2-tuple.

    The last element is yielded as (x, None).

        >>> tuple(with_next(()))
        ()
        >>> tuple(with_next((1,)))
        ((1, None),)
        >>> tuple(with_next((1,2,3)))
        ((1, 2), (2, 3), (3, None))
    '''
    it = iter(it)
    prior = next(it)
    for x in it:
        yield prior, x
        prior = x
    yield prior, None

def gen_block(fn, current_block, next_block):
    id, label, next_name, next_conditional = current_block
    next_block_name = next_block[1] if next_block else None 
    assem_block = crud.insert('assembler_blocks',
                              section='code', label=label, next_label=next_name,
                              word_symbol_id=fn)
    inst_order = 1
    it = crud.fetchall('''
        select t.code_seq_id, t.int1, t.int2, t.string,
               t.line_start, t.column_start, t.line_end,
               t.column_end, ru1.assigned_register as ans,
               param.int1 as param_int1, param.assigned_register as param
          from triples t
               left join reg_use ru1
                 on ru1.kind = 'triple-output'
                 and t.id = ru1.ref_id
               left join (triple_parameters tp
                          inner join triples c
                            on tp.parameter_id = c.id
                          left join reg_use ru2
                            on ru2.kind = 'triple'
                            and ru2.position_kind = 'parameter'
                            and ru2.ref_id = tp.parent_id
                            and ru2.position = tp.parameter_num) param 
                 on t.id = param.parent_id
         where t.block_id = ?
           and (t.use_count = 0
                or exists (select null
                             from triple_parameters tp
                            where tp.parameter_id = t.id
                              and not tp.delink))
         order by t.abs_order_in_block, param.parameter_num
      ''', (id,), ctor_factory=crud.row.factory_from_cur)
    for t, params \
     in itertools.groupby(it, lambda x:
                                crud.row.from_kws(code_seq_id=x.code_seq_id,
                                                  int1=x.int1,
                                                  int2=x.int2,
                                                  string=x.string,
                                                  line_start=x.line_start,
                                                  column_start=x.column_start,
                                                  line_end=x.line_end,
                                                  column_end=x.column_end,
                                                  ans=x.ans)):
        inst_order = \
          gen_triple(assem_block, next_block[1], next_conditional, t,
                     tuple((p.param, p.param_int1) for p in params),
                     inst_order)

def gen_triple(assem_block, next_block, next_conditional, t, params,
               inst_order):
    expansions = {'next_block': next_block,
                  'next_conditional': next_conditional,
                  'ans': t.ans,
                  'int1': t.int1,
                  'int2': t.int2,
                  'string': t.string,
                 }
    #print(t.code_seq_id, "params", params, file = sys.stderr)
    if len(params) >= 1:
        expansions['left'] = params[0][0]
        expansions['left_int1'] = params[0][1]
    if len(params) >= 2:
        expansions['right'] = params[1][0]
        expansions['right_int1'] = params[1][1]

    def expand(s):
        #print(code.opcode, "expand", s, expansions, file=sys.stderr)
        if s is None: return None
        return s.format(**expansions)

    for code in crud.read_as_rows('code', code_seq_id=t.code_seq_id,
                                          order_by='inst_order'):
        crud.insert('assembler_code',
                    block_id=assem_block,
                    inst_order=inst_order,
                    label=code.label,
                    opcode=code.opcode,
                    operand1=expand(code.operand1),
                    operand2=expand(code.operand2),
                    min_length=1,
                    max_length=2,
                    line_start=t.line_start,
                    column_start=t.column_start,
                    line_end=t.line_end,
                    column_end=t.column_end)
        inst_order += 1
    return inst_order
