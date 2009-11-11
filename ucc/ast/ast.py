# ast.py

from __future__ import with_statement

import itertools

from ucc.ast import crud

Translation_dict = {}

def delete_word_by_name(word_name):
    r'''Deletes the word and all of it's ast nodes from the ast table.

    This does not report an error if the word is not in the database.
    '''
    id = crud.read1_column('symbol_table', 'id',
                           context=None, name=word_name, zero_ok=True)
    if id is not None:
        delete_word_by_id(id)

def delete_word_by_id(id):
    r'''Delete node, and all subordinate nodes, from database.

    This deletes both macro expansions of the deleted node and child nodes.
    '''
    crud.delete('ast', word_body_id=id)

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

    def save(self, word_body_id,
             parent = None, parent_arg_num = None, arg_order = None):
        my_id = crud.insert('ast',
                  **dict(itertools.chain(
                           map(lambda attr: (attr, getattr(self, attr)),
                               self.attr_cols),
                           zip(self.arg_cols,
                               (word_body_id, parent, parent_arg_num,
                                arg_order)))))
        save_args(self.args, word_body_id, my_id)

def save_args(args, word_body_id, parent = None):
    for arg_num, arg in enumerate(args):
        if arg is None:
            arg = ast(kind = 'None', expect = None)
        if isinstance(arg, ast):
            arg.save(word_body_id, parent, arg_num, 0)
        else:
            for position, x in enumerate(arg):
                x.save(word_body_id, parent, arg_num, position)

def save_word(name, symbol_id, args):
    delete_word_by_name(name)
    save_args(args, symbol_id)

