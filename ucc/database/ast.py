# ast.py

from __future__ import with_statement

import itertools

from ucc.database import crud

def delete_word_by_label(word_label):
    r'''Deletes the word and all of it's ast nodes from the ast table.

    This does not report an error if the word is not in the database.
    '''
    id = crud.read1_column('symbol_table', 'id',
                           context=None, label=word_label, zero_ok=True)
    if id is not None:
        delete_word_by_id(id)

def delete_word_by_id(id):
    r'''Delete node, and all subordinate nodes, from database.

    This deletes both macro expansions of the deleted node and child nodes.
    '''
    crud.delete('ast', word_symbol_id=id)

class ast(object):
    r'''Internal AST representation (prior to going to database).

    This is the AST representation created by the parser.  At the end of the
    parse, this structure is stored into the database and then discarded.
    '''

    # Values passed as keyword args and stored as attributes that describe
    # this ast node (and are set to None on macro_expand):
    attr_cols_node = (
        'kind', 'label', 'opcode', 'symbol_id', 'int1', 'int2', 'str1', 'str2',
    )

    # All values passed as keyword args and stored as attributes.
    attr_cols = attr_cols_node + (
        'expect', 'line_start', 'column_start', 'line_end', 'column_end',
    )

    # Values passed as parameters to the save method:
    arg_cols = (
        'word_symbol_id', 'parent_node', 'parent_arg_num', 'arg_order',
    )

    # default attribute values:
    kind = 'call'
    expect = 'value'
    word_symbol_id = label = opcode = symbol_id = None
    int1 = int2 = str1 = str2 = None
    line_start = column_start = line_end = column_end = None

    def __init__(self, *args, **kws):
        self.args = args
        for name, value in kws.iteritems():
            if name not in self.attr_cols:
                raise KeyError("ast: illegal attribute: %s" % name)
            setattr(self, name, value)

    @classmethod
    def from_parser(cls, syntax_position_info, *args, **kws):
        ans = cls(*args, **kws)
        ans.line_start, ans.column_start, ans.line_end, ans.column_end = \
          syntax_position_info
        return ans

    def get_syntax_position_info(self):
        return (self.line_start, self.column_start,
                self.line_end, self.column_end)

    def macro_expand(self, args, **kws):
        self.args = args
        for key, value in kws.iteritems():
            setattr(self, key, value)
        for key in self.attr_cols_node:
            if key not in kws:
                setattr(self, key, None)
        return self

    def __repr__(self):
        if self.kind == 'word':
            return "<ast word:%s>" % self.symbol_id
        return "<ast %s%s%s>" % \
                 (self.kind,
                  ''.join(" %s:%r" % (attr, getattr(self, attr))
                          for attr in ('int1', 'int2', 'str1', 'str2')
                          if getattr(self, attr) is not None),
                  ' ' + repr(self.args) if self.args else '')

    def prepare(self, words_by_label):
        if self.kind == 'call':
            if self.args and isinstance(self.args[0], ast) and \
               self.args[0].kind == 'word':
                word_obj = words_by_label[self.args[0].label]
                prepare_method = word_obj.get_method('prepare', self.expect)
                return prepare_method(self, words_by_label)
            self.prepare_args(words_by_label)
        return self

    def prepare_args(self, words_by_label):
        self.args = prepare_args(self.args, words_by_label)

    def save(self, word_symbol_id,
             parent = None, parent_arg_num = None, arg_order = None):
        kws = dict(itertools.chain(
                     map(lambda attr: (attr, getattr(self, attr)),
                         self.attr_cols),
                     zip(self.arg_cols,
                         (word_symbol_id, parent, parent_arg_num,
                          arg_order))))
        #print "save", kws
        my_id = crud.insert('ast', **kws)
        save_args(self.args, word_symbol_id, my_id)

def save_args(args, word_symbol_id, parent = None):
    for arg_num, arg in enumerate(args):
        if arg is None:
            arg = ast(kind = 'None', expect = None)
        if isinstance(arg, ast):
            arg.save(word_symbol_id, parent, arg_num, 0)
        else:
            for position, x in enumerate(arg):
                x.save(word_symbol_id, parent, arg_num, position)

def prepare_args(args, words_by_label):
    return tuple(arg.prepare(words_by_label)
                   if isinstance(arg, ast)
                   else prepare_args(arg, words_by_label)
                 for arg in args)

def save_word(label, symbol_id, args):
    delete_word_by_label(label)
    save_args(args, symbol_id)

