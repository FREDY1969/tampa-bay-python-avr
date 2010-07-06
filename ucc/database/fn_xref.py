# fn_xref.py

r'''The helper functions for function cross reference info in the database.
'''

import itertools
from ucc.database import crud, symbol_table

def calls(caller_id, called_id):
    r'''Function caller_id directly calls function called_id.

    Both caller_id and called_id are the symbol_id of the function.
    '''
    crud.insert('fn_calls', 'ignore', caller_id=caller_id, called_id=called_id)

def uses(fn_id, var_id):
    r'''Function fn_id directly references global variable var_id.

    Fn_id and var_id are the symbol_ids of the function and global variable,
    respectively.
    '''
    crud.insert('fn_global_var_uses', 'ignore',
                fn_id=fn_id, var_id=var_id, sets=False)

def sets(fn_id, var_id):
    r'''Function fn_id directly sets global variable var_id.

    Fn_id and var_id are the symbol_ids of the function and global variable,
    respectively.
    '''
    crud.insert('fn_global_var_uses', 'ignore',
                fn_id=fn_id, var_id=var_id, sets=True)

def expand(quiet = False):
    r'''Expand the fn_global_var_uses and symbol_table.side_effects/suspends.

    To include all called functions, recursively.
    '''
    # Fill out fn_calls table to full depth:
    for depth in itertools.count(1):
        rowcount = crud.execute("""
          insert or ignore into fn_calls (caller_id, called_id, depth)
            select top.caller_id, bottom.called_id, top.depth + 1
              from fn_calls top inner join fn_calls bottom
                on top.called_id = bottom.caller_id
             where top.depth = ? and bottom.depth = 1
          """,
          (depth,))[0]
        if not rowcount:
            if not quiet:
                print("fn_xref.expand: did", depth + 1, \
                      "database calls for fn_calls")
            break

    # Fill out the fn_global_var_uses table:
    crud.execute("""
      insert or ignore into fn_global_var_uses (fn_id, var_id, sets, depth)
        select calls.caller_id,
               uses.var_id, uses.sets, calls.depth + uses.depth
          from fn_calls calls inner join fn_global_var_uses uses
            on calls.called_id = uses.fn_id
      """)

    # Fill out symbol_table.side_effects:
    symbol_table.write_symbols()   # flush attribute changes to database
    crud.execute("""
      update symbol_table
         set side_effects = 1
       where side_effects = 0
         and exists (select null
                       from fn_calls inner join symbol_table st
                         on fn_calls.called_id = st.id
                      where id = fn_calls.caller_id
                        and st.side_effects = 1)
       """)

    # Fill out symbol_table.suspends:
    crud.execute("""
      update symbol_table
         set suspends = 1
       where suspends = 0
         and exists (select null
                       from fn_calls inner join symbol_table st
                         on fn_calls.called_id = st.id
                      where id = fn_calls.caller_id
                        and st.suspends = 1)
       """)

    symbol_table.update()

def get_var_uses(fn_id):
    r'''Get global variables usage for function fn_id.

    Returns vars_used, vars_set as two frozensets of symbol_ids.
    '''
    uses_vars = []
    sets_vars = []
    for var_id, sets in crud.read_as_tuples('fn_global_var_uses',
                                            'sets', 'var_id',
                                            fn_id=fn_id):
        if sets: sets_vars.append(var_id)
        else: uses_vars.append(var_id)
    return frozenset(uses_vars), frozenset(sets_vars)

