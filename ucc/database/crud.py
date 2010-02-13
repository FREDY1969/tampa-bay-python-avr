# crud.py

r'''This module offers simple generic database access routines.

The routines are table agnostic, and are not capable of doing joins or complex
queries.  You're on your own for that.

This also provides routines to connect to the database and provide transaction
support to automatically commit database transactions, or do a rollback if an
exception is generated.

Most of the crud routines use keyword arguments to specify the SQL 'where'
clause.  See the `doctor_test` examples for how this works.
'''

from __future__ import with_statement

import os.path
import itertools
import sqlite3 as db

Debug = False           # the doctests will fail when this is True
Db_conn = None          #: The sqlite3 database connection object.
Db_filename = 'ucc.db'
_Gensyms = {}
In_transaction = False

class db_transaction(object):
    r'''Python *Context Manager* for database transactions.

    Use this in a Python 'with' statement to bracket the code that makes up a
    database transaction.

    This returns the database cursor which can be assigned to the 'as' variable
    in the 'with' statement.  But this cursor is also assigned to the internal
    'Db_cur' variable which is automatically used by all of the crud routines
    here, so you can ignore this.

    On exit, does a 'commit' if there are no exceptions, 'rollback' otherwise.
    '''

    def __enter__(self):
        global In_transaction
        In_transaction = True
        return Db_cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        global In_transaction
        if exc_type is None and exc_val is None and exc_tb is None:
            Db_conn.commit()
        else:
            Db_conn.rollback()
        In_transaction = False
        return False    # don't ignore exception (if any)

class db_connection(object):
    r'''Python *Context Manager* for database connections.

    This calls init and returns the Db_conn (which is assigned to the 'as'
    variable in the 'with' statement).

    On exit, does a commit if there are no exceptions, rollback otherwise;
    then calls `fini`.
    '''

    def __init__(self, directory):
        init(directory)

    def __enter__(self):
        return Db_conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and exc_val is None and exc_tb is None:
            if Debug: print "crud: commit"
            Db_conn.commit()
        else:
            if Debug: print "crud: rollback"
            Db_conn.rollback()
        fini()
        return False    # don't ignore exception (if any)

def init(directory):
    r'''Initialize the module.

    Opens a database connection to the 'ucc.db' file in 'directory' and sets
    'Db_conn' to this connection.

    If the 'ucc.db' file does not exist, it creates it and sets up the schema
    by feeding 'ucc.dll' to it.

    Also initializes the `gensym` function from the information stored in the
    database from the last run.
    '''
    global Db_conn, Db_cur, Enums, _Gensyms
    if Db_conn is None:
        db_path = os.path.join(directory, Db_filename)
        if not os.path.exists(db_path):
            Db_conn = db.connect(db_path)
            Db_cur = Db_conn.cursor()
            ddl_path = os.path.join(os.path.dirname(__file__), 'ucc.ddl')
            try:
                ddl = __loader__.get_data(ddl_path)
            except NameError:
                with open(ddl_path) as f:
                    ddl = f.read()
            commands = ddl.split(';')
            with db_transaction() as db_cur:
                for command in commands:
                    db_cur.execute(command)
        else:
            Db_conn = db.connect(os.path.join(directory, Db_filename))
            Db_cur = Db_conn.cursor()
        Db_cur.execute("select prefix, last_used_index from gensym_indexes")
        _Gensyms = dict(Db_cur)

def fini():
    r'''Saves the `gensym` info in the database and closes the connection.
    '''
    global Db_conn
    save_gensym_indexes()
    Db_cur.close()
    Db_conn.close()
    Db_conn = None

def save_gensym_indexes():
    r'''Save the `gensym` info in the database.
    '''
    with db_transaction() as db_cur:
        db_cur.execute("delete from gensym_indexes")
        db_cur.executemany(
          "insert into gensym_indexes (prefix, last_used_index) values (?, ?)",
          _Gensyms.iteritems())

def gensym(root_name):
    r'''Generates a unique name that starts with root_name.

    >>> gensym('a')
    'a_0001'
    >>> gensym('A')
    'A_0002'
    >>> gensym('bob')
    'bob_0001'
    '''
    lower_root_name = root_name.lower()
    if lower_root_name not in _Gensyms: _Gensyms[lower_root_name] = 0
    _Gensyms[lower_root_name] += 1
    return "%s_%04d" % (root_name, _Gensyms[lower_root_name])

class db_cur_test(object):
    r'''Proxy database cursor for doctests...

    Use `set_answers` to set what `fetchall` should return.

    Use the 'cols' parameter to `__init__` to specify the columns in the table
    for use with the `read_as_dicts` function called without any 'cols'.
    '''

    def __init__(self, *cols):
        r'''
        'cols' are the columns in the table.  This is only needed for
        `read_as_dicts` without any 'cols'.
        '''
        global Db_cur
        if cols:
            self.description = tuple((c,) + (None,) * 6 for c in cols)
        Db_cur = self

    def execute(self, query, parameters = None):
        print "query:", query
        if parameters is not None:
            print "parameters:", parameters

    def set_answers(self, *answers):
        r'''Sets the answers that the next `fetchall` will return.
        '''
        self.answers = answers

    def fetchall(self):
        return list(self.answers)

Strings = {}

def string_lookup(s):
    r'''Returns the same string instance when given an equal string.

    This is used for sql command string to trigger prepare logic in the
    database adaptor that only checks the string's address rather than its
    contents.  Note sure if this is really needed for sqlite3???

        >>> a = 'a' * 1000
        >>> b = 'a' * 1000
        >>> a is b
        False
        >>> string_lookup(a) is a
        True
        >>> string_lookup(b) is a
        True
    '''
    ans = Strings.get(s, None)
    if ans is not None: return ans
    Strings[s] = s
    return s

def doctor_test(item, values):
    r'''Returns the SQL test for a given key 'item'.

    This is called from other crud functions and is not intented to be
    called directly.
    
    The 'item' is a (key, value) pair.

    Also appends SQL parameters to 'values'.

        >>> values = []
        >>> doctor_test(('col', None), values)
        'col is null'
        >>> values
        []
        >>> doctor_test(('col_', None), values)
        'col is not null'
        >>> values
        []
        >>> doctor_test(('col', 44), values)
        'col = ?'
        >>> values
        [44]
        >>> doctor_test(('col_', 45), values)
        'col <> ?'
        >>> values
        [44, 45]
        >>> doctor_test(('col', (1, 2)), values)
        'col in (?, ?)'
        >>> values
        [44, 45, 1, 2]
        >>> doctor_test(('col_', (3, 4, 5)), values)
        'col not in (?, ?, ?)'
        >>> values
        [44, 45, 1, 2, 3, 4, 5]
        >>> doctor_test(('col', (10,)), values)
        'col = ?'
        >>> values
        [44, 45, 1, 2, 3, 4, 5, 10]
    '''
    key, value = item
    if value is None:
        if key.endswith('_'): return key[:-1] + ' is not null'
        return key + ' is null'
    if hasattr(value, '__iter__'):
        t = tuple(value)
        assert t, "crud key tuples can't be empty"
        if len(t) == 1:
            value = t[0]
        else:
            values.extend(t)
            if key.endswith('_'):
                return '%s not in (%s)' % (key[:-1], ', '.join(('?',) * len(t)))
            return '%s in (%s)' % (key, ', '.join(('?',) * len(t)))
    values.append(value)
    if key.endswith('_'): return key[:-1] + ' <> ?'
    return key + ' = ?'

def create_where(keys):
    r'''Returns sql 'where' and 'order by' clauses and parameters.

        This is called from other crud functions and is not intented to be
        called directly.

        'keys' is a dictionary of {key: value} mappings.  See `doctor_test` for
        a description of how the keys are interpreted.

        The key 'order_by' is treated specially to trigger the inclusion of a
        SQL 'order by' clause.

        >>> create_where({'a': 44})
        (' where a = ?', [44])
        >>> create_where({'a': None})
        (' where a is null', [])
        >>> create_where({})
        ('', [])
        >>> create_where({'order_by': ('a', 'b')})
        (' order by a, b', [])
        >>> create_where({'a': 44, 'order_by': ('a', 'b')})
        (' where a = ? order by a, b', [44])
    '''
    if 'order_by' in keys:
        order_by_clause = " order by " + ', '.join(keys['order_by'])
        del keys['order_by']
    else:
        order_by_clause = ''
    if keys:
        values = []
        tests = tuple(doctor_test(item, values) for item in keys.items())
        return " where " + ' and '.join(tests) + order_by_clause, \
               values
    else:
        return order_by_clause, []

def run_query(table, cols, keys):
    r'''Creates and executes a query.

        This is called from other crud functions and is not intented to be
        called directly.

        >>> _ = db_cur_test()
        >>> run_query('a', ('b', 'c'), {'d': 44})
        query: select b, c from a where d = ?
        parameters: [44]
        >>> run_query('a', (), {})
        query: select * from a
        parameters: []
    '''
    where, params = create_where(keys)
    command = string_lookup("select %s from %s%s" % 
                              (', '.join(cols) if cols else '*',
                               table,
                               where))
    if Debug:
        print "crud:", command
        print "  params:", params
    Db_cur.execute(command, params)

def read_as_tuples(table, *cols, **keys):
    r'''Reads rows from table, returning a sequence of tuples.

    'cols' are just the names of the columns to return.

    'keys' are used to build the SQL 'where' clause (see `doctor_test`).

    A key of 'order_by' contains a list of columns to sort by.

        >>> cur = db_cur_test()
        >>> cur.set_answers((1, 2), (3, 4))
        >>> read_as_tuples('a', 'b', 'c')
        query: select b, c from a
        parameters: []
        [(1, 2), (3, 4)]
        >>> read_as_tuples('a', 'b', 'c', id=4, order_by=('a', 'b'))
        query: select b, c from a where id = ? order by a, b
        parameters: [4]
        [(1, 2), (3, 4)]
    '''
    if not cols:
        raise ValueError("read_as_tuples requires columns to be specified")
    run_query(table, cols, keys)
    return Db_cur.fetchall()

def return1(rows, zero_ok = False):
    r'''Returns the first row in 'rows'.

    This is called from other crud functions and is not intented to be
    called directly.

    Generates an exception if len(rows) > 1.

    Also generates an exception if len(rows) == 0 and not 'zero_ok'.  If
    'zero_ok' is True, None is returned.
    '''
    if zero_ok:
        assert len(rows) <= 1, \
               "query returned %d rows, expected 0 or 1 row" % len(rows)
    else:
        assert len(rows) == 1, \
               "query returned %d rows, expected 1 row" % len(rows)
    if rows: return rows[0]
    return None

def read1_as_tuple(table, *cols, **keys):
    r'''Reads 1 row as a tuple.

    'cols' are just the names of the columns to return.

    'keys' are used to build the SQL 'where' clause (see the `doctor_test`
    examples).

    A key of 'zero_ok' set to True will return None if no rows are found
    rather than raising an exception.
    '''
    zero_ok = False
    if 'zero_ok' in keys:
        zero_ok = keys['zero_ok']
        del keys['zero_ok']
    return return1(read_as_tuple(table, *cols, **keys), zero_ok)

def read_as_dicts(table, *cols, **keys):
    r'''Reads rows from table, returning a sequence of dicts.

    'cols' are just the names of the columns to return.  If no 'cols' are
    specified, all columns are returned.

    'keys' are used to build the SQL 'where' clause (see `doctor_test`).

    A key of 'order_by' contains a list of columns to sort by.

        >>> cur = db_cur_test('b')
        >>> cur.set_answers((1,), (3,))
        >>> read_as_dicts('a', 'b')
        query: select b from a
        parameters: []
        [{'b': 1}, {'b': 3}]
    '''
    run_query(table, cols, keys)
    col_names = map(lambda x: x[0], Db_cur.description)
    return [dict(zip(col_names, row)) for row in Db_cur.fetchall()]

def read1_as_dict(table, *cols, **keys):
    r'''Reads 1 row as a dict.

    Calls `read_as_dicts` and returns the first answer.  Raises an exception
    if not exactly one answer was found.

    A key of 'zero_ok' set to True will return None if no rows are found
    rather than raising an exception.
    '''
    zero_ok = False
    if 'zero_ok' in keys:
        zero_ok = keys['zero_ok']
        del keys['zero_ok']
    return return1(read_as_dicts(table, *cols, **keys), zero_ok)

def read_column(table, column, **keys):
    r'''Reads one column from table.
    
    Returns a sequence of values (1 per result row).

    'keys' are used to build the SQL 'where' clause (see `doctor_test`).

    A key of 'order_by' contains a list of columns to sort by.

        >>> cur = db_cur_test()
        >>> cur.set_answers((1,), (2,), (3,))
        >>> read_column('a', 'b')
        query: select b from a
        parameters: []
        [1, 2, 3]
    '''
    run_query(table, (column,), keys)
    return [row[0] for row in Db_cur.fetchall()]

def read1_column(table, column, **keys):
    r'''Reads one column from one row.

    Calls `read_column` and returns the first answer.  Raises an exception
    if not exactly one answer was found.

    A key of 'zero_ok' set to True will return None if no rows are found
    rather than raising an exception.
    '''
    zero_ok = False
    if 'zero_ok' in keys:
        zero_ok = keys['zero_ok']
        del keys['zero_ok']
    return return1(read_column(table, column, **keys), zero_ok)

def count(table, **keys):
    r'''Returns a count of the number of rows in a table.

    'keys' are used to build the SQL 'where' clause (see `doctor_test`).
    '''
    return read1_column(table, 'count(*)', **keys)

def update(table, where, **set):
    r'''Updates rows in a table.

    'where' is a dictionary of {key: value} pairs (see the `doctor_test`
    examples).

    Doesn't return anything.

        >>> cur = db_cur_test()
        >>> dummy_transaction()
        >>> update('a', {'b': 44}, c=7, d=8)
        query: update a set c = ?, d = ? where b = ?
        parameters: [7, 8, 44]
    '''
    assert In_transaction, "crud.update done outside of transaction"
    where_clause, params = create_where(where)
    command = string_lookup("update %s set %s%s" %
                              (table,
                               ', '.join(c + ' = ?' for c in set.keys()),
                               where_clause))
    if Debug:
        print "crud:", command
        print "  params:", set.values() + params
    Db_cur.execute(command, set.values() + params)

def delete(table, **keys):
    r'''Deletes rows in a table.

    'keys' are used to build the SQL 'where' clause (see `doctor_test`).

    Doesn't return anything.

        >>> cur = db_cur_test()
        >>> dummy_transaction()
        >>> delete('a', c=7, d=8)
        query: delete from a where c = ? and d = ?
        parameters: [7, 8]
    '''
    assert In_transaction, "crud.delete done outside of transaction"
    where_clause, params = create_where(keys)
    command = string_lookup("delete from %s%s" % (table, where_clause))
    if Debug:
        print "crud:", command
        print "  params:", params
    Db_cur.execute(command, params)

def insert(table, option = None, **cols):
    r'''Inserts a row in table.

    Returns the id of the new row.

    'cols' are the columns to insert (name=value as keyword parameters).

    'option' is any string that can be used in an 'or' clause with the SQL
    insert statement::

        insert or <option> into ...

    Specifically, 'option' may be one of:

        - 'rollback'
        - 'abort'
        - 'replace'
        - 'fail'
        - 'ignore'

    Examples:

        >>> cur = db_cur_test()
        >>> dummy_transaction()
        >>> cur.lastrowid = 123
        >>> insert('a', c=7, d=8)
        query: insert into a (c, d) values (?, ?)
        parameters: [7, 8]
        123
        >>> insert('a', 'replace', c=7, d=8)
        query: insert or replace into a (c, d) values (?, ?)
        parameters: [7, 8]
        123
    '''
    assert In_transaction, "crud.insert done outside of transaction"
    keys = sorted(cols.keys())
    command = string_lookup("insert %sinto %s (%s) values (%s)" %
                              ("or %s " % option if option else '',
                               table,
                               ', '.join(keys),
                               ', '.join('?' for c in keys)))
    if Debug:
        print "crud:", command
        print "  params:", [cols[key] for key in keys]
    Db_cur.execute(command, [cols[key] for key in keys])
    if Debug:
        print "  id:", Db_cur.lastrowid
    return Db_cur.lastrowid

def dummy_transaction():
    r'''Used in doctests to fake a transaction.
    '''
    global In_transaction
    In_transaction = True

