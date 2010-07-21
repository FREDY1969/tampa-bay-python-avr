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

import os.path
import itertools
import functools
import sqlite3 as db

Db_conn = None
Debug = False           # the doctests will fail when this is True
Db_filename = 'ucc.db'

class db_connection:
    r'''Python *Context Manager* for database connections.

    This initializes the database (if needed) and represents the database
    connection.  This is the object assigned to the 'as' variable in the
    'with' statement.

    On exit, saves the gensym info and closes the connection.
    '''

    bogus_cursor = None

    @classmethod
    def test(cls, *cols):
        db_conn = cls(None)
        db_conn.bogus_cursor = db_cur_test(*cols)
        return db_conn, db_conn.bogus_cursor

    def __init__(self, directory,
                 create = False, load_gensym = False, delete = False):
        r'''Create a database connection.

        Opens a database connection to the 'ucc.db' file in 'directory'.

        If the 'ucc.db' file does not exist, it creates it and sets up the
        schema by feeding 'ucc.dll' to it.

        Also initializes the `gensym` function from the information stored in
        the database from the last run.

        If directory is None, then no database connection is done, but other
        global variables are initialized (for testing).
        '''

        global Db_conn

        self.load_gensym = load_gensym
        self.in_transaction = False
        if directory is None:
            self._gensyms = {}
        else:
            if directory.endswith('.db'):
                db_path = directory
            else:
                db_path = os.path.join(directory, Db_filename)
            if os.path.exists(db_path) and not delete:
                self.db_conn = db.connect(db_path)
            else:
                if os.path.exists(db_path): os.remove(db_path)
                if not create:
                    raise AssertionError(
                            "Database {} does not exist".format(db_path))
                self.db_conn = db.connect(db_path)
                ddl_path = os.path.join(os.path.dirname(__file__),
                                        'ucc.ddl')
                try:
                    ddl = __loader__.get_data(ddl_path)
                except NameError:
                    with open(ddl_path) as f:
                        ddl = f.read()
                with self.db_transaction():
                    for command in ddl.split(';'):
                        self.execute(command)
            if load_gensym:
                self._gensyms = dict(self.fetchall(
                                  '''select prefix, last_used_index 
                                       from gensym_indexes
                                  '''))
            else:
                self._gensyms = {}
        Db_conn = self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False    # don't ignore exception (if any)

    def close(self):
        if self.in_transaction:
            raise AssertionError("db_connection closed in transaction")
        if self.load_gensym: self.save_gensym_indexes()
        self.db_conn.close()

    def cursor(self):
        return self.bogus_cursor or self.db_conn.cursor()

    def attach(self, database, name):
        r'''Attaches database as name.

        Doesn't return anything.
        '''
        cur = self.cursor()
        #cur.execute('attach database {!r} as {}'.format(database, name))
        cur.execute('attach database ? as ?', (database, name))
        cur.close()

    def execute(self, str, params = ()):
        r'''Executes an insert/update/delete.

        Returns rowcount, lastrowid.
        '''
        if not self.in_transaction:
            raise AssertionError(
                    "{} done outside db_transaction".format(str.split()[0]))
        cur = self.cursor()
        cur.execute(str, params)
        ans = cur.rowcount, cur.lastrowid
        cur.close()
        return ans

    def executemany(self, str, seq):
        r'''Executes an insert/update/delete on many parameter sets.
        
        Returns the rowcount (which doesn't work for update commands).
        '''
        if not self.in_transaction:
            raise AssertionError(
                    "{} done outside db_transaction".format(str.split()[0]))
        cur = self.cursor()
        cur.executemany(str, seq)
        ans = cur.rowcount
        cur.close()
        return ans

    def fetchall(self, str, params = (), ctor = None, ctor_factory = None):
        cur = self.cursor()
        cur.execute(str, params)
        if ctor_factory is not None:
            ctor = ctor_factory(cur)
        if ctor is None: ctor = lambda x: x
        for row in cur: yield ctor(row)
        cur.close()

    def save_gensym_indexes(self):
        r'''Save the `gensym` info in the database.
        '''
        with self.db_transaction():
            self.execute("delete from gensym_indexes")
            self.executemany(
              '''insert into gensym_indexes (prefix, last_used_index)
                                     values (?, ?)
              ''',
              iter(self._gensyms.items()))

    def db_transaction(self):
        return db_transaction_cls(self)

    def commit(self):
        self.db_conn.commit()
        self.in_transaction = False

    def rollback(self):
        self.db_conn.rollback()
        self.in_transaction = False

    def run_query(self, table, cols, keys):
        r'''Creates and executes a query.

            This is called from other crud functions and is not intented to be
            called directly.

            >>> db_conn = db_connection.test()[0]
            >>> db_conn.run_query('a', ('b', 'c'), {'d': 44})
            ...   # doctest: +ELLIPSIS
            query: select b, c from a where d = ?
            parameters: [44]
            <ucc.database.crud.db_cur_test object at 0x...>
            >>> db_conn.run_query('a', (), {}) # doctest: +ELLIPSIS
            query: select * from a
            parameters: []
            <ucc.database.crud.db_cur_test object at 0x...>
        '''
        where, params = create_where(keys)
        command = string_lookup("select {} from {}{}"
                                  .format(', '.join(cols) if cols else '*',
                                          table,
                                          where))
        if Debug:
            print("crud:", command)
            print("  params:", params)
        cur = self.cursor()
        cur.execute(command, params)
        return cur

    def ret_multi(self, table, cols, keys, ctor = None, ctor_factory = None):
        cur = self.run_query(table, cols, keys)
        if ctor_factory is not None:
            ctor = ctor_factory(cur)
        if ctor is None: ctor = lambda x: x
        for row in cur:
            yield ctor(row)
        cur.close()

    def ret_single(self, table, cols, keys, ctor = None, ctor_factory = None, 
                         zero_ok = False):
        cur = self.run_query(table, cols, keys)
        if ctor_factory is not None:
            ctor = ctor_factory(cur)
        if ctor is None: ctor = lambda x: x
        row = return1(cur, zero_ok)
        if row is None: return row
        return ctor(row)

    def read_as_tuples(self, table, *cols, **keys):
        r'''Reads rows from table, returning a sequence of tuples.

        'cols' are just the names of the columns to return.

        'keys' are used to build the SQL 'where' clause (see `doctor_test`).

        A key of 'order_by' contains a list of columns to sort by.

            >>> db_conn, cur = db_connection.test()
            >>> cur.set_answers((1, 2), (3, 4))
            >>> list(db_conn.read_as_tuples('a', 'b', 'c'))
            query: select b, c from a
            parameters: []
            [(1, 2), (3, 4)]
            >>> list(db_conn.read_as_tuples('a', 'b', 'c', id=4,
            ...                             order_by=('a', 'b')))
            query: select b, c from a where id = ? order by a, b
            parameters: [4]
            [(1, 2), (3, 4)]
        '''
        if not cols:
            raise ValueError("read_as_tuples requires columns to be specified")
        return self.ret_multi(table, cols, keys, tuple)

    def read1_as_tuple(self, table, *cols, **keys):
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
        return self.ret_single(table, cols, keys, tuple, zero_ok=zero_ok)

    def read_as_rows(self, table, *cols, **keys):
        r'''Reads rows from table, returning a sequence of 'row' objects.

        'cols' are just the names of the columns to return.  If no 'cols' are
        specified, all columns are returned.

        'keys' are used to build the SQL 'where' clause (see `doctor_test`).

        A key of 'order_by' contains a list of columns to sort by.

            >>> db_conn, cur = db_connection.test('b')
            >>> cur.set_answers((1,), (3,))
            >>> list(db_conn.read_as_rows('a', 'b'))
            query: select b from a
            parameters: []
            [<row b=1>, <row b=3>]
        '''
        return self.ret_multi(table, cols, keys,
                              ctor_factory = row.factory_from_cur)

    def read1_as_row(self, table, *cols, **keys):
        r'''Reads 1 row as a row object.

        Calls `read_as_rows` and returns the first answer.  Raises an exception
        if not exactly one answer was found.

        A key of 'zero_ok' set to True will return None if no rows are found
        rather than raising an exception.
        '''
        zero_ok = False
        if 'zero_ok' in keys:
            zero_ok = keys['zero_ok']
            del keys['zero_ok']
        return self.ret_single(table, cols, keys,
                               ctor_factory = row.factory_from_cur,
                               zero_ok = zero_ok)

    def read_as_dicts(self, table, *cols, **keys):
        r'''Reads rows from table, returning a sequence of dicts.

        'cols' are just the names of the columns to return.  If no 'cols' are
        specified, all columns are returned.

        'keys' are used to build the SQL 'where' clause (see `doctor_test`).

        A key of 'order_by' contains a list of columns to sort by.

            >>> db_conn, cur = db_connection.test('b')
            >>> cur.set_answers((1,), (3,))
            >>> list(db_conn.read_as_dicts('a', 'b'))
            query: select b from a
            parameters: []
            [{'b': 1}, {'b': 3}]
        '''
        return self.ret_multi(table, cols, keys,
                              ctor_factory = dict_factory_from_cur)

    def read1_as_dict(self, table, *cols, **keys):
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
        return self.ret_single(table, cols, keys,
                               ctor_factory = dict_factory_from_cur,
                               zero_ok = zero_ok)

    def read_column(self, table, column, **keys):
        r'''Reads one column from table.
        
        Returns a sequence of values (1 per result row).

        'keys' are used to build the SQL 'where' clause (see `doctor_test`).

        A key of 'order_by' contains a list of columns to sort by.

            >>> db_conn, cur = db_connection.test()
            >>> cur.set_answers((1,), (2,), (3,))
            >>> list(db_conn.read_column('a', 'b'))
            query: select b from a
            parameters: []
            [1, 2, 3]
        '''
        return self.ret_multi(table, (column,), keys,
                              ctor = lambda row: row[0])

    def read1_column(self, table, column, **keys):
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
        return self.ret_single(table, (column,), keys,
                               ctor = lambda row: row[0],
                               zero_ok = zero_ok)

    def count(self, table, **keys):
        r'''Returns a count of the number of rows in a table.

        'keys' are used to build the SQL 'where' clause (see `doctor_test`).
        '''
        return self.ret_single(table, ('count(*)',), keys,
                               ctor = lambda row: row[0])

    def update(self, table, where, **set):
        r'''Updates rows in a table.

        'where' is a dictionary of {key: value} pairs (see the `doctor_test`
        examples).

        Doesn't return anything.

            >>> db_conn, cur = db_connection.test()
            >>> db_conn.dummy_transaction()
            >>> cur.rowcount = 12
            >>> db_conn.update('a', {'b': 44}, c=7, d=8)
            query: update a set c = ?, d = ? where b = ?
            parameters: [7, 8, 44]
            12
        '''
        assert self.in_transaction, \
               "db_connection.update done outside of transaction"
        where_clause, params = create_where(where)
        command = string_lookup("update {} set {}{}"
                                  .format(table,
                                          ', '.join(c + ' = ?'
                                                    for c in list(set.keys())),
                                          where_clause))
        if Debug:
            print("crud:", command)
            print("  params:", list(set.values()) + params)
        return self.execute(command,
                            doctor_value(list(set.values())) + params)[0]

    def delete(self, table, **keys):
        r'''Deletes rows in a table.

        'keys' are used to build the SQL 'where' clause (see `doctor_test`).

        Doesn't return anything.

            >>> db_conn, cur = db_connection.test()
            >>> cur.rowcount = 12
            >>> db_conn.dummy_transaction()
            >>> db_conn.delete('a', c=7, d=8)
            query: delete from a where c = ? and d = ?
            parameters: [7, 8]
            12
        '''
        assert self.in_transaction, "crud.delete done outside of transaction"
        where_clause, params = create_where(keys)
        command = string_lookup("delete from {}{}".format(table, where_clause))
        if Debug:
            print("crud:", command)
            print("  params:", params)
        return self.execute(command, params)[0]

    def insert(self, table, option = None, **cols):
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

            >>> db_conn, cur = db_connection.test()
            >>> db_conn.dummy_transaction()
            >>> cur.lastrowid = 123
            >>> db_conn.insert('a', c=7, d=8)
            query: insert into a (c, d) values (?, ?)
            parameters: [7, 8]
            123
            >>> db_conn.insert('a', 'replace', c=7, d=8)
            query: insert or replace into a (c, d) values (?, ?)
            parameters: [7, 8]
            123
        '''
        assert self.in_transaction, "crud.insert done outside of transaction"
        keys = sorted(cols.keys())
        command = string_lookup("insert {}into {} ({}) values ({})"
                                  .format("or {} ".format(option) if option
                                                                  else '',
                                          table,
                                          ', '.join(keys),
                                          ', '.join(('?',) * len(keys))))
        if Debug:
            print("crud:", command)
            print("  params:", [cols[k] for k in keys])
        rowid = self.execute(command, doctor_value(cols[k] for k in keys))[1]
        if Debug:
            print("  id:", rowid)
        return rowid

    def dummy_transaction(self):
        r'''Used in doctests to fake a transaction.
        '''
        self.in_transaction = True

    def gensym(self, root_name):
        r'''Generates a unique name that starts with root_name.

            >>> db_conn, _ = db_connection.test()
            >>> db_conn.gensym('a')
            'a_0001'
            >>> db_conn.gensym('A')
            'A_0002'
            >>> db_conn.gensym('bob')
            'bob_0001'
        '''
        lower_root_name = root_name.lower()
        if lower_root_name not in self._gensyms:
            self._gensyms[lower_root_name] = 0
        self._gensyms[lower_root_name] += 1
        return "{}_{:04d}".format(root_name, self._gensyms[lower_root_name])

def dict_factory_from_cur(cur):
    col_names = [x[0] for x in cur.description]
    return lambda row: dict(zip(col_names, row))

class db_transaction_cls:
    r'''Python *Context Manager* for database transactions.

    Use this in a Python 'with' statement to bracket the code that makes up a
    database transaction.

    This does not return anything to be assigned to the 'as' variable in the
    'with' statement.

    On exit, does a 'commit' if there are no exceptions, 'rollback' otherwise.
    '''

    def __init__(self, db_conn):
        self.db_connection = db_conn

    def __enter__(self):
        self.db_connection.in_transaction = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and exc_val is None and exc_tb is None:
            self.db_connection.commit()
        else:
            self.db_connection.rollback()
        return False    # don't ignore exception (if any)

class db_cur_test:
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
        if cols:
            self.description = tuple((c,) + (None,) * 6 for c in cols)
        self.rowcount = -1
        self.lastrowid = None

    def __iter__(self):
        return iter(self.answers)

    def execute(self, query, parameters = None):
        print("query:", query)
        if parameters is not None:
            print("parameters:", parameters)

    def set_answers(self, *answers):
        r'''Sets the answers that the next `fetchall` will return.
        '''
        self.answers = answers

    def fetchall(self):
        return list(self.answers)

    def close(self):
        pass

class row:
    @classmethod
    def factory_from_cur(cls, cur):
        col_names = [x[0] for x in cur.description]
        return lambda row: cls(col_names, row)

    @classmethod
    def from_kws(cls, **kws):
        return cls(tuple(kws.keys()), tuple(kws.values()))

    def __init__(self, names, values):
        assert len(names) == len(values)
        super().__setattr__('_names', sorted(names))
        for name, value in zip(names, values):
            super().__setattr__(name, value)

    def __repr__(self):
        return "<row {}>".format(
                            ' '.join("{}={}".format(name, getattr(self, name))
                                     for name in self._names))

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name not in self._names:
            self._names.append(name)
            self._names.sort()

    def __eq__(self, b):
        if not isinstance(b, row) or self._names != b._names:
            return False
        for c in self._names:
            if getattr(self, c) != getattr(b, c): return False
        return True

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
        'col isnull'
        >>> values
        []
        >>> doctor_test(('col_', None), values)
        'col notnull'
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
        if key.endswith('_'): return key[:-1] + ' notnull'
        return key + ' isnull'
    if hasattr(value, '__iter__') and not isinstance(value, str):
        t = tuple(value)
        assert t, "crud where key tuple values can't be empty"
        if len(t) == 1:
            value = doctor_value(t[0])
        else:
            values.extend(doctor_value(t))
            if key.endswith('_'):
                return '{} not in ({})'.format(key[:-1],
                                               ', '.join(('?',) * len(t)))
            return '{} in ({})'.format(key, ', '.join(('?',) * len(t)))
    values.append(doctor_value(value))
    if key.endswith('_'): return key[:-1] + ' <> ?'
    return key + ' = ?'

def doctor_value(value):
    r'''Returns value unless it's an object, then returns value.id.

        >>> doctor_value(33)
        33
        >>> class dummy: pass
        >>> obj = dummy()
        >>> obj.id = 34
        >>> doctor_value(obj)
        34
        >>> doctor_value((33, obj))
        [33, 34]
    '''
    if value is None or isinstance(value, (int, float, str)):
        return value
    if hasattr(value, '__iter__'):
        return list(map(doctor_value, value))
    return value.id

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
        (' where a isnull', [])
        >>> create_where({})
        ('', [])
        >>> create_where({'order_by': 'a'})
        (' order by a', [])
        >>> create_where({'order_by': ('a', 'b')})
        (' order by a, b', [])
        >>> create_where({'a': 44, 'order_by': (('a', 'desc'), 'b')})
        (' where a = ? order by a desc, b', [44])
    '''
    if 'order_by' in keys:
        value = keys['order_by']
        del keys['order_by']
        if isinstance(value, str):
            order_by_clause = " order by " + value
        else:
            order_by_clause = " order by " + ', '.join((v if isinstance(v, str)
                                                          else ' '.join(v))
                                                       for v in value)
    else:
        order_by_clause = ''
    if keys:
        values = []
        tests = tuple(doctor_test(item, values) for item in list(keys.items()))
        return " where " + ' and '.join(tests) + order_by_clause, \
               values
    else:
        return order_by_clause, []

def return1(rows, zero_ok = False):
    r'''Returns the first row in 'rows'.

    This is called from other crud functions and is not intented to be
    called directly.

    Raises an AssertionError if there is more than 1 row.

    Also raises an AssertionError if there are no rows and not 'zero_ok'.  If
    'zero_ok' is True, None is returned.
    '''
    rows = iter(rows)
    try:
        ans = next(rows)
    except StopIteration:
        if not zero_ok:
            raise AssertionError("query returned 0 rows, expected 0 or 1 row")
        return None
    else:
        try:
            next(rows)
        except StopIteration:
            return ans
        else:
            raise AssertionError("query returned more than 1 row")
    finally:
        if hasattr(rows, 'close'): rows.close()

def cursor():
    return Db_conn.cursor()

def execute(str, params = ()):
    return Db_conn.execute(str, params)

def executemany(str, seq):
    return Db_conn.executemany(str, seq)

def fetchall(str, params = (), ctor = None, ctor_factory = None):
    return Db_conn.fetchall(str, params, ctor, ctor_factory)

def db_transaction():
    return Db_conn.db_transaction()

def commit():
    Db_conn.commit()

def rollback():
    Db_conn.rollback()

def read_as_tuples(table, *cols, **keys):
    return Db_conn.read_as_tuples(table, *cols, **keys)

def read1_as_tuple(table, *cols, **keys):
    return Db_conn.read1_as_tuple(table, *cols, **keys)

def read_as_rows(table, *cols, **keys):
    return Db_conn.read_as_rows(table, *cols, **keys)

def read1_as_row(table, *cols, **keys):
    return Db_conn.read1_as_row(table, *cols, **keys)

def read_as_dicts(table, *cols, **keys):
    return Db_conn.read_as_dicts(table, *cols, **keys)

def read1_as_dict(table, *cols, **keys):
    return Db_conn.read1_as_dict(table, *cols, **keys)

def read_column(table, column, **keys):
    return Db_conn.read_column(table, column, **keys)

def read1_column(table, column, **keys):
    return Db_conn.read1_column(table, column, **keys)

def count(table, **keys):
    return Db_conn.count(table, **keys)

def update(table, where, **set):
    return Db_conn.update(table, where, **set)

def delete(table, **keys):
    return Db_conn.delete(table, **keys)

def insert(table, option = None, **cols):
    return Db_conn.insert(table, option=option, **cols)

def gensym(root_name):
    return Db_conn.gensym(root_name)

