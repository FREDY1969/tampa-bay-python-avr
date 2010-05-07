# codegen.py

import sys
import itertools

from ucc.database import crud, triple2
from ucc.codegen import order_triples

Debug = True

def gen_assembler(processor):
    r'''Translate intermediate code into assembler.

    Note: This function is _not_ run inside a "with crud.db_transaction()".
    '''
    update_use_counts()
    order_triples.order_children()

    # assign code_seq_id's to triples.
    crud.Db_cur.execute('''
        update triples
           set code_seq_id = (
              select p.code_seq_id
                from pattern p
                       inner join pattern_by_processor pp
                         on p.id = pp.pattern_id
               where pp.processor = ?

                 and (p.left_opcode isnull and p.left_multi_use isnull or
                      exists (select null
                         from triple_parameters tp inner join triples p1
                           on tp.parameter_id = p1.id
                        where tp.parent_id = triples.id
                          and tp.parameter_num = 1
                          and (p.left_opcode isnull or
                               p.left_opcode = p1.operator)
                          and (p.left_const_min isnull or
                               p.left_const_min <= p1.int1)
                          and (p.left_const_max isnull or
                               p.left_const_max >= p1.int1)
                          and (p.left_multi_use isnull or
                               p.left_multi_use and p1.use_count > 1 or
                               not p.left_multi_use and p1.use_count <= 1)))

                 and (p.right_opcode isnull and p.right_multi_use isnull or
                      exists (select null
                         from triple_parameters tp2 inner join triples p2
                           on tp2.parameter_id = p2.id
                        where tp2.parent_id = triples.id
                          and tp2.parameter_num = 2
                          and (p.right_opcode isnull or
                               p.right_opcode = p2.operator)
                          and (p.right_const_min isnull or
                               p.right_const_min <= p2.int1)
                          and (p.right_const_max isnull or
                               p.right_const_max >= p2.int1)
                          and (p.right_multi_use isnull or
                               p.right_multi_use and p2.use_count > 1 or
                               not p.right_multi_use and p2.use_count <= 1)))

               order by p.preference
               limit 1)
    ''', (processor,))


def update_use_counts():
    r'''Update use_counts of all triples.
    '''
    with crud.db_transaction():
        crud.Db_cur.execute('''
            update triples
               set use_count = (select count(*) from triple_parameters tp
                                 where tp.parameter_id = triples.id)
          ''')

