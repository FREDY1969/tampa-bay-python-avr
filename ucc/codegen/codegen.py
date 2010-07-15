# codegen.py

import sys
import itertools

from ucc.database import crud
from ucc.codegen import order_triples, reg_alloc, expand_assembler

Debug = True

def gen_assembler(processor):
    r'''Translate intermediate code into assembler.

    Note: This function is _not_ run inside a "with crud.db_transaction()".
    '''
    update_use_counts()
    order_triples.order_children()
    assign_code_seq_ids(processor)
    reg_alloc.alloc_regs()
    expand_assembler.expand_assembler()

def update_use_counts():
    r'''Update use_counts of all triples.
    '''
    with crud.db_transaction():
        crud.execute('''
            update triples
               set use_count = (select count(*) from triple_parameters tp
                                 where tp.parameter_id = triples.id)
          ''')

def assign_code_seq_ids(processor):
    with crud.db_transaction():
        # assign code_seq_id's to triples.
        crud.execute('''
            update triples
               set code_seq_id = (
                  select cs.id
                    from code_seq cs
                         inner join code_seq_by_processor csbp
                           on cs.id = csbp.code_seq_id
                   where csbp.processor = ?
                     and cs.operator = triples.operator
                     and not exists
                           (select null
                              from code_seq_parameter csp
                                   left outer join
                                       (triple_parameters tp
                                          inner join triples p
                                            on tp.parameter_id = p.id) as tpp
                                     on parent_id = triples.id
                                     and csp.parameter_num = tpp.parameter_num
                             where csp.code_seq_id = cs.id
                               and (tpp.parent_id isnull       -- missing param
                                    or csp.opcode != tpp.operator
                                    or csp.const_min > tpp.int1
                                    or csp.const_max < tpp.int1
                                    or csp.last_use != tpp.last_parameter_use))
                   order by cs.preference)  -- only first row taken
          ''', (processor,))

    with crud.db_transaction():
        # and make the code_seq_id available to the triple's parameters.
        crud.execute('''
            update triple_parameters
               set parent_code_seq_id = 
                     (select code_seq_id
                        from triples t
                       where t.id = triple_parameters.parent_id)
          ''')
