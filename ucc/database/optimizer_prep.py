# optimizer_prep.py

r'''Create the database cross reference tables needed by the optimizer.

This isn't used yet...
'''

import itertools

from ucc.database import crud

def reaching_definitions():
    crud.delete('ins')
    crud.delete('outs')
    crud.delete('kills')

    # Kills is just the starting gens table:
    crud.execute("""
        insert into kills (block_id, symbol_id)
        select distinct block_id, symbol_id from gens
    """)

    # Add gens for global variables in fn calls to calling blocks:
    #
    # E.g. if block B calls FOO, add all gens of global variables inside FOO to
    #      the gens of B.
    #
    # These aren't included in kills, because there may be paths in FOO that
    # don't kill a variable set along another path.
    #
    # FIX: This should exclude declarations in FOO that are killed by later
    #      code in B.
    crud.execute("""
        insert into gens (block_id, symbol_id, triple_id)
        select t.block_id, g.symbol_id, g.triple_id
          from triple t
               inner join block b on t.int_1 = b.word_symbol_id
               inner join gens g on g.block_id = b.id
               inner join symbol_table st
                 on g.symbol_id = st.id and st.context is null
         where t.operator = 'call_direct'
    """)

    # Starting outs simply taken from gens:
    crud.execute("""insert into outs (block_id, symbol_id, triple_id)
                    select block_id, symbol_id, triple_id
                      from gens
    """)

    # Iterate as long as changes are made:
    for depth in itertools.count(0):
        rowcount = crud.execute("""
          insert or ignore into ins (block_id, symbol_id, triple_id)
          select bs.successor, outs.symbol_id, outs.triple_id
            from outs inner join block_successors bs
              on outs.block_id = bs.predecessor
        """)[0]
        if not rowcount:
            print("reaching_definitions: did", 2 * depth + 1, "database calls")
            break
        rowcount = crud.execute("""
          insert or ignore into outs (block_id, symbol_id, triple_id)
          select block_id, symbol_id, triple_id
            from ins
           where symbol_id not in (select symbol_id from kills
                                    where kills.block_id = ins.block_id)
        """)[0]
        if not rowcount:
            print("reaching_definitions: did", 2 * depth + 2, "database calls")
            break
