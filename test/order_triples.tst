# order_triples.tst

    >>> import os
    >>> from ucc.codegen import codegen, order_triples
    >>> from ucc.database import crud

Open a dummy database:

    >>> Db_file = '/tmp/ot_test.db'
    >>> if os.path.exists(Db_file): os.remove(Db_file)
    >>> crud.init(Db_file, load_gensym = False)
    >>> _ = crud.Db_cur.execute(
    ...       'attach database {!r} as architecture'
    ...         .format(os.path.join(os.path.dirname(codegen.__file__),
    ...                              'avr.db')))
    >>> crud.dummy_transaction()

We'll have the following triple structure for block1:

  block1
    1
      2
        6
        7
          5
          8
        9
      3
        5
      4
        6
    13
    14
        5
    15
        6

With the constraints that 6 preceeds 5 and 5 preceeds 13.

    >>> _ = crud.insert('symbol_table', id=1, label='foo', kind='function')
    >>> _ = crud.insert('blocks', id=1, name='block1', word_symbol_id=1)
    >>> _ = crud.insert('triples', id=1, block_id=1, operator='bogus')
    >>> _ = crud.insert('triples', id=2, block_id=1, operator='bogus')
    >>> _ = crud.insert('triples', id=3, block_id=1, operator='bogus')
    >>> _ = crud.insert('triples', id=4, block_id=1, operator='bogus')
    >>> _ = crud.insert('triple_parameters', parent_id=1, parameter_id=2,
    ...                                      parameter_num=1)
    >>> _ = crud.insert('triple_parameters', parent_id=1, parameter_id=3,
    ...                                      parameter_num=2)
    >>> _ = crud.insert('triple_parameters', parent_id=1, parameter_id=4,
    ...                                      parameter_num=3)
    >>> _ = crud.insert('triples', id=5, block_id=1, operator='bogus')
    >>> _ = crud.insert('triples', id=6, block_id=1, operator='bogus')
    >>> _ = crud.insert('triples', id=7, block_id=1, operator='bogus')
    >>> _ = crud.insert('triples', id=8, block_id=1, operator='bogus')
    >>> _ = crud.insert('triples', id=9, block_id=1, operator='bogus')
    >>> _ = crud.insert('triples', id=13, block_id=1, operator='bogus')
    >>> _ = crud.insert('triples', id=14, block_id=1, operator='bogus')
    >>> _ = crud.insert('triples', id=15, block_id=1, operator='bogus')
    >>> _ = crud.insert('triple_parameters', parent_id=2, parameter_id=6,
    ...                                      parameter_num=1)
    >>> _ = crud.insert('triple_parameters', parent_id=2, parameter_id=7,
    ...                                      parameter_num=2)
    >>> _ = crud.insert('triple_parameters', parent_id=2, parameter_id=9,
    ...                                      parameter_num=3)
    >>> _ = crud.insert('triple_parameters', parent_id=7, parameter_id=5,
    ...                                      parameter_num=1)
    >>> _ = crud.insert('triple_parameters', parent_id=7, parameter_id=8,
    ...                                      parameter_num=2)
    >>> _ = crud.insert('triple_parameters', parent_id=3, parameter_id=5,
    ...                                      parameter_num=1)
    >>> _ = crud.insert('triple_parameters', parent_id=4, parameter_id=6,
    ...                                      parameter_num=1)
    >>> _ = crud.insert('triple_parameters', parent_id=14, parameter_id=5,
    ...                                      parameter_num=1)
    >>> _ = crud.insert('triple_parameters', parent_id=15, parameter_id=6,
    ...                                      parameter_num=1)
    >>> _ = crud.insert('triple_order_constraints', predecessor=6, orig_pred=6,
    ...                                             successor=5, orig_succ=5)
    >>> _ = crud.insert('triple_order_constraints', predecessor=5, orig_pred=5,
    ...                                             successor=13, orig_succ=13)

And block2:

  block2
    10
      11
      12

    >>> _ = crud.insert('blocks', id=2, name='block2', word_symbol_id=1)
    >>> _ = crud.insert('triples', id=10, block_id=2, operator='bogus')
    >>> _ = crud.insert('triples', id=11, block_id=2, operator='bogus')
    >>> _ = crud.insert('triples', id=12, block_id=2, operator='bogus')
    >>> _ = crud.insert('triple_parameters', parent_id=10, parameter_id=11,
    ...                                      parameter_num=1)
    >>> _ = crud.insert('triple_parameters', parent_id=10, parameter_id=12,
    ...                                      parameter_num=2)

OK, the data is ready!

    >>> crud.Db_conn.commit()

First we need to:

    >>> codegen.update_use_counts()
    >>> crud.Db_conn.commit()

Check these results:

    #1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    >>> crud.read_column('triples', 'use_count', order_by='id')
    [0, 1, 1, 1, 3, 3, 1, 1, 1, 0, 1, 1, 0, 0, 0]

And now it's show time!

    >>> _ = order_triples.order_children()
    >>> crud.Db_conn.commit()

Check the results:

Register estimates:

    #1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    >>> crud.read_column('triples', 'register_est', order_by='id')
    [3, 3, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1]

    >>> crud.read_column('blocks', 'register_est', order_by='id')
    [3, 2]

    >>> crud.read1_column('symbol_table', 'register_est', id=1)
    3

Order constraints:

    >>> crud.read_as_tuples('triple_order_constraints', 'predecessor',
    ...                     'successor', 'depth',
    ...                     order_by=('predecessor', 'successor'))
    [(1, 13, 2), (1, 13, 1), (1, 14, 1), (2, 3, 1), (4, 3, 1), (6, 7, 1), (14, 13, 1), (15, 13, 2), (15, 14, 1)]

Assigned orders:

    # 1-15-14-13 and 10
    >>> crud.read_column('triples', 'order_in_block', order_by='id')
    [1, None, None, None, None, None, None, None, None, 1, None, None, 4, 3, 2]

    # 2,3,4
    >>> crud.read_column('triple_parameters', 'evaluation_order', parent_id=1,
    ...                  order_by='parameter_id')
    [1, 3, 2]

    # 6,7,9
    >>> crud.read_column('triple_parameters', 'evaluation_order', parent_id=2,
    ...                  order_by='parameter_id')
    [1, 2, 3]

    # 5,8
    >>> crud.read_column('triple_parameters', 'evaluation_order', parent_id=7,
    ...                  order_by='parameter_id')
    [1, 2]

    # 11,12
    >>> crud.read_column('triple_parameters', 'evaluation_order', parent_id=10,
    ...                  order_by='parameter_id')
    [1, 2]

    # Everything else should have 1:
    >>> crud.read_column('triple_parameters', 'evaluation_order',
    ...                  parent_id_=(1, 2, 7, 10))
    [1, 1, 1, 1]

    # Absolute order of triples in block 1:
    >>> crud.read_column('triples', 'id',
    ...                  block_id=1, order_by='abs_order_in_block')
    [6, 5, 8, 7, 9, 2, 4, 3, 1, 15, 14, 13]

    # Absolute order of triples in block 2:
    >>> crud.read_column('triples', 'id',
    ...                  block_id=2, order_by='abs_order_in_block')
    [11, 12, 10]

    >>> for row in crud.read_as_tuples('triple_parameters', 'parameter_id',
    ...                                'parent_id', 'abs_order_in_block',
    ...                                'parent_seq_num', 'last_parameter_use',
    ...                                order_by=('parameter_id',
    ...                                          'abs_order_in_block')):
    ...     print(row)
    (2, 1, 6, 1, 1)
    (3, 1, 10, 2, 1)
    (4, 1, 8, 3, 1)
    (5, 7, 2, 4, 0)
    (5, 3, 9, 5, 0)
    (5, 14, 14, 6, 1)
    (6, 2, 1, 7, 0)
    (6, 4, 7, 8, 0)
    (6, 15, 12, 9, 1)
    (7, 2, 4, 10, 1)
    (8, 7, 3, 11, 1)
    (9, 2, 5, 12, 1)
    (11, 10, 1, 13, 1)
    (12, 10, 2, 14, 1)

All done!

    >>> crud.fini(False)
