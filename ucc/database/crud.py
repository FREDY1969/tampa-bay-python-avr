# crud.py

r'''This module offers simple database access routines.

The routines are table agnostic, but are not capable of doing joins or complex
queries.  You're on your own for that.
'''

from __future__ import with_statement

import os.path
import itertools
import sqlite3 as db

Db_conn = None
Db_filename = 'ucl.db'
_Gensyms = {}

class db_transaction(object):
    r'''Context Manager for database transactions.

    This returns the Db_cur which is assigned to the 'as' variable in the
    'with' statement.

    On exit, does a commit if there are no exceptions, rollback otherwise.
    '''
    def __enter__(self):
        return Db_cur
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and exc_val is None and exc_tb is None:
            Db_conn.commit()
        else:
            Db_conn.rollback()
        return False    # don't ignore exception (if any)

class db_connection(object):
    r'''Context Manager for database connections.

    This calls init and returns the Db_conn (which is assigned to the 'as'
    variable in the 'with' statement).

    On exit, does a commit if there are no exceptions, rollback otherwise;
    then calls fini().
    '''
    def __init__(self, directory):
        init(directory)
    def __enter__(self):
        return Db_conn
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and exc_val is None and exc_tb is None:
            Db_conn.commit()
        else:
            Db_conn.rollback()
        fini()
        return False    # don't ignore exception (if any)

def init(directory):
    global Db_conn, Db_cur, Enums, _Gensyms
    if Db_conn is None:
        db_path = os.path.join(directory, Db_filename)
        if not os.path.exists(db_path):
            Db_conn = db.connect(db_path)
            Db_cur = Db_conn.cursor()
            ddl_path = os.path.join(os.path.dirname(__file__), 'ast.ddl')
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
    global Db_conn
    save_gensym_indexes()
    Db_cur.close()
    Db_conn.close()
    Db_conn = None

def save_gensym_indexes():
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
    '''
    def __init__(self, *cols):
        global Db_cur
        if cols:
            self.description = tuple((c,) + (None,) * 6 for c in cols)
        Db_cur = self
    def execute(self, query, parameters = None):
        print "query:", query
        if parameters is not None:
            print "parameters:", parameters
    def set_answers(self, *answers):
        self.answers = answers
    def fetchall(self):
        return list(self.answers)

Strings = {}

def string_lookup(s):
    r'''Returns the same string instance when given an equal string.

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

def doctor_test(item):
    r'''Returns the SQL test for a given key item ((key, value) pair).

        >>> doctor_test(('col', None))
        'col is null'
        >>> doctor_test(('col_', None))
        'col is not null'
        >>> doctor_test(('col', 44))
        'col = ?'
        >>> doctor_test(('col_', 44))
        'col <> ?'
    '''
    key, value = item
    if value is None:
        if key.endswith('_'): return key[:-1] + ' is not null'
        else: return key + ' is null'
    else:
        if key.endswith('_'): return key[:-1] + ' <> ?'
        else: return key + ' = ?'

def create_where(keys):
    r'''Returns where and order by clauses and parameters.

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
        return " where " + ' and '.join(doctor_test(item)
                                        for item in keys.items()) \
                 + order_by_clause, \
               filter(lambda x: x is not None, keys.values())
    else:
        return order_by_clause, []

def run_query(table, cols, keys):
    r'''Creates and executes a query.

        >>> _ = db_cur_test()
        >>> run_query('a', ('b', 'c'), {'d': 44})
        query: select b, c from a where d = ?
        parameters: [44]
        >>> run_query('a', (), {})
        query: select * from a
        parameters: []
    '''
    where, params = create_where(keys)
    Db_cur.execute(string_lookup("select %s from %s%s" % 
                                   (', '.join(cols) if cols else '*',
                                    table,
                                    where)),
                   params)

def read_as_tuples(table, *cols, **keys):
    r'''Reads rows from table, returning a sequence of tuples.

    cols are just the names of the columns to return.

    keys are column=value or column=None or column_=value for !=.

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
    if zero_ok:
        assert len(rows) <= 1, \
               "query returned %d rows, expected 0 or 1 row" % len(rows)
    else:
        assert len(rows) == 1, \
               "query returned %d rows, expected 1 row" % len(rows)
    if rows: return rows[0]
    return None

def read1_as_tuple(table, *cols, **keys):
    zero_ok = False
    if 'zero_ok' in keys:
        zero_ok = keys['zero_ok']
        del keys['zero_ok']
    return return1(read_as_tuple(table, *cols, **keys), zero_ok)

def read_as_dicts(table, *cols, **keys):
    r'''Reads rows from table, returning a sequence of tuples.

    cols are just the names of the columns to return.  If no cols are
    specified, all cols are returned.

    keys are column=value or column=None or column_=value for !=.

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
    zero_ok = False
    if 'zero_ok' in keys:
        zero_ok = keys['zero_ok']
        del keys['zero_ok']
    return return1(read_as_dicts(table, *cols, **keys), zero_ok)

def read_column(table, column, **keys):
    r'''Reads one column from table.
    
    Returns a sequence of values (1 per result row).

    keys are column=value or column=None or column_=value for !=.

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
    zero_ok = False
    if 'zero_ok' in keys:
        zero_ok = keys['zero_ok']
        del keys['zero_ok']
    return return1(read_column(table, column, **keys), zero_ok)

def update(table, where, **set):
    r'''Updates row in table.

    Doesn't return anything.

        >>> cur = db_cur_test()
        >>> update('a', {'b': 44}, c=7, d=8)
        query: update a set c = ?, d = ? where b = ?
        parameters: [7, 8, 44]
    '''
    where_clause, params = create_where(where)
    Db_cur.execute(string_lookup("update %s set %s%s" %
                                   (table,
                                    ', '.join(c + ' = ?' for c in set.keys()),
                                    where_clause)),
                   set.values() + params)

def delete(table, **keys):
    r'''Deletes rows in table.

    Doesn't return anything.

        >>> cur = db_cur_test()
        >>> delete('a', c=7, d=8)
        query: delete from a where c = ? and d = ?
        parameters: [7, 8]
    '''
    where_clause, params = create_where(keys)
    Db_cur.execute(string_lookup("delete from %s%s" % (table, where_clause)),
                   params)

def insert(table, replace = False, **cols):
    r'''Inserts a row in table.

    Returns the id of the new row.

        >>> cur = db_cur_test()
        >>> cur.lastrowid = 123
        >>> insert('a', c=7, d=8)
        query: insert into a (c, d) values (?, ?)
        parameters: [7, 8]
        123
        >>> insert('a', True, c=7, d=8)
        query: insert or replace into a (c, d) values (?, ?)
        parameters: [7, 8]
        123
    '''
    Db_cur.execute(string_lookup("insert %sinto %s (%s) values (%s)" %
                                   ("or replace " if replace else '',
                                    table,
                                    ', '.join(cols.keys()),
                                    ', '.join('?' for c in cols.keys()))),
                   cols.values())
    return Db_cur.lastrowid
