# ast.py

from __future__ import with_statement

import os.path
import itertools
import sqlite3 as db

Db_conn = None
Db_filename = 'ast.db'
Translation_dict = {}
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

def delete_word_by_name(word_name):
    r'''Deletes the word and all of it's ast nodes from the ast table.

    This does not report an error if the word is not in the database.
    '''
    Db_cur.execute("select id from ast where kind = 'word_body' and word = ?",
                   (word_name,)) 
    ans = Db_cur.fetchone()
    if ans:
        delete_word_by_id(ans[0])

def delete_word_by_id(id):
    r'''Delete node, and all subordinate nodes, from database.

    This deletes both macro expansions of the deleted node and child nodes.
    '''
    Db_cur.execute("delete from ast where id = ? or word_body_id = ?",
                   (id, id))

class ast(object):
    r'''Internal AST representation (prior to going to database).

    This is the AST representation created by the parser.  At the end of the
    parse, this structure is stored into the database and then discarded.
    '''
    attr_cols = (
        'kind', 'expect', 'label', 'word', 'int1', 'int2', 'str1', 'str2',
        'line_start', 'column_start', 'line_end', 'column_end',
    )

    arg_cols = (
        'word_body_id', 'parent_node', 'parent_arg_num', 'arg_order',
    )

    insert_sql = "insert into ast (%s) values (%s)" % \
                   (', '.join(attr_cols + arg_cols),
                    ', '.join('?' * (len(attr_cols) + len(arg_cols))))

    # default attribute values:
    kind = 'fn_call'
    expect = 'value'
    word_body_id = label = word = int1 = int2 = str1 = str2 = None
    line_start = column_start = line_end = column_end = None

    def __init__(self, *args, **kws):
        self.args = args
        for name, value in kws.iteritems():
            setattr(self, name, (Translation_dict.get(value, value)
                                 if name == 'word'
                                 else value))

    @classmethod
    def from_parser(cls, syntax_position_info, *args, **kws):
        ans = cls(*args, **kws)
        ans.line_start, ans.column_start, ans.line_end, ans.column_end = \
          syntax_position_info
        return ans

    def save(self, db_cur, word_body_id = None,
             parent = None, parent_arg_num = None, arg_order = None):
        db_cur.execute(self.insert_sql,
                       map(lambda attr: getattr(self, attr), self.attr_cols) +
                         [word_body_id, parent, parent_arg_num, arg_order])
        my_id = db_cur.lastrowid
        if getattr(self, 'kind', None) == 'word_body':
            assert word_body_id is None
            word_body_id = my_id
        for arg_num, arg in enumerate(self.args):
            if arg is None:
                arg = ast(kind = 'None', expect = None)
            if isinstance(arg, ast):
                arg.save(db_cur, word_body_id, my_id, arg_num, 0)
            else:
                for position, x in enumerate(arg):
                    x.save(db_cur, word_body_id, my_id, arg_num, position)
        return my_id

