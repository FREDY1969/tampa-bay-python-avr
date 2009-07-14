# ast.py

from __future__ import with_statement

import os.path
import sqlite3 as db

Db_filename = 'ucc_ast.db'
_Gensyms = {}

def init(directory):
    global Db_conn, Db_cur, Enums, _Gensyms
    Db_conn = db.connect(os.path.join(directory, Db_filename))
    Db_cur = Db_conn.cursor()
    _Gensyms = {}

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

def delete_id(id):
    r'''Delete node, and all subordinate nodes, from database.

    This deletes both macro expansions of the deleted node and child nodes.
    '''
    Db_cur.execute("select id from node where id_replaced = ?", (id,))
    for id, in Db_cur: delete_id(id)
    Db_cur.execute("select id from node where parent_node = ?", (id,))
    for id, in Db_cur: delete_id(id)
    Db_cur.execute("delete from node where id = ?", (id,))

def from_tuple(t):
    pass

