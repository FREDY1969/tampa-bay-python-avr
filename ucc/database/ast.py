# ast.py

from __future__ import with_statement

import itertools

from ucc.database import block, crud, fn_xref, symbol_table

def delete_word_by_label(word_label):
    r'''Deletes the word and all of it's ast nodes from the ast table.

    This does not report an error if the word is not in the database.
    '''
    sym = symbol_table.get(word_label, default=None)
    if sym is not None:
        delete_word_by_id(sym.id)

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
        'kind', 'label', 'symbol_id', 'int1', 'int2', 'str1', 'str2',
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
    word_symbol_id = label = symbol_id = None
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

    def macro_expand(self, fn_symbol, words_needed, args, **kws):
        self.args = args
        for key, value in kws.iteritems():
            setattr(self, key, value)
        for key in self.attr_cols_node:
            if key not in kws:
                setattr(self, key, None)
        return self.prepare(fn_symbol, words_needed)

    def __repr__(self):
        if self.kind == 'word':
            return "<ast word:%s>" % self.symbol_id
        return "<ast %s%s%s>" % \
                 (self.kind,
                  ''.join(" %s:%r" % (attr, getattr(self, attr))
                          for attr in ('int1', 'int2', 'str1', 'str2')
                          if getattr(self, attr) is not None),
                  ' ' + repr(self.args) if self.args else '')

    def prepare(self, fn_symbol, words_needed):
        if self.kind == 'call':
            self.prepare_args(fn_symbol, words_needed)
            if self.args and isinstance(self.args[0], ast) and \
               self.args[0].kind == 'word':
                word_obj = symbol_table.get(self.args[0].label).word_obj
                fn_xref.calls(fn_symbol.id, word_obj.ww.symbol.id)
                prepare_method = word_obj.get_method('prepare', self.expect)
                return prepare_method(fn_symbol, self, words_needed)
        if self.kind == 'word':
            sym = symbol_table.get_by_id(self.symbol_id)
            if sym.context is None:
                words_needed.add(sym.label)
                if self.expect == 'lvalue':
                    fn_xref.sets(fn_symbol.id, self.symbol_id)
                else:
                    fn_xref.uses(fn_symbol.id, self.symbol_id)
        return self

    def prepare_args(self, fn_symbol, words_needed):
        self.args = \
          prepare_args(fn_symbol, self.args, words_needed)

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

    def compile(self):
        #print "%s.compile" % self.kind
        if self.kind in ('approx', 'int', 'ratio'):
            return block.Current_block.gen_triple(
                     self.kind, self.int1, self.int2,
                     syntax_position_info= self.get_syntax_position_info())

        if self.kind == 'string':
            name = crud.gensym('strlit')
            sym = symbol_table.symbol.create(name, 'const')
            assembler.block('flash', name).write((
                assembler.inst('int16', str(len(self.str1)), length=2),
                assembler.inst('bytes', repr(self.str1), length=len(self.str1)),
            ))
            return block.Current_block.gen_triple(
                     'global', sym.id,
                     syntax_position_info= self.get_syntax_position_info())

        if self.kind == 'call':
            if self.args and isinstance(self.args[0], ast) and \
               self.args[0].kind == 'word':
                word_obj = symbol_table.get(self.args[0].label).word_obj
                compile_method = word_obj.get_method('compile', self.expect)
                return compile_method(self)
            else:
                raise AssertionError("call indirect not supported yet")

        if self.kind == 'word':
            word_obj = symbol_table.get(self.label).word_obj
            compile_method = word_obj.get_method('compile', self.expect)
            return compile_method(self)

        if self.kind in ('no-op', 'None'):
            return None

        if self.kind == 'label':
            block.new_label(self.label)
            return None

        if self.kind == 'jump':
            block.Current_block.unconditional_to(self.label)
            return None

        if self.kind == 'if-true':
            arg_triples = self.compile_args()
            block.Current_block.true_to(arg_triples[0].id, self.label)
            return None

        if self.kind == 'if-false':
            arg_triples = self.compile_args()
            block.Current_block.false_to(arg_triples[0].id, self.label)
            return None

        if self.kind == 'series':
            self.compile_args()
            return None

    def compile_args(self):
        return compile_args(self.args)

def prepare_args(fn_symbol, args, words_needed):
    r'''Prepares each of the args.

    This involves setting the 'expect' and 'type_id' attributes for each ast
    and macro expansion.

    It also sets the 'side_effects' and 'suspends' attributes on the symbols
    for functions, and records xref info using the ucc.database.fn_xref
    'calls', 'uses', and 'sets' functions.

    The labels of the words needed by these args are added to the
    'words_needed' set.

    Returns a tuple of the new args to use in place of the args passed in.
    '''
    return tuple(arg.prepare(fn_symbol, words_needed)
                   if isinstance(arg, ast)
                   else prepare_args(fn_symbol, arg, words_needed)
                 for arg in args)

def save_args(args, word_symbol_id, parent = None):
    for arg_num, arg in enumerate(args):
        if arg is None:
            arg = ast(kind = 'None', expect = None)
        if isinstance(arg, ast):
            arg.save(word_symbol_id, parent, arg_num, 0)
        else:
            for position, x in enumerate(arg):
                x.save(word_symbol_id, parent, arg_num, position)

def compile_args(args):
    r'''Compiles each of the args.

    Returns a tuple of triples.
    '''
    return tuple(arg.compile()
                   if isinstance(arg, ast)
                   else compile_args(arg)
                 for arg in args)

def save_word(label, symbol_id, args):
    r'''Writes the ast for word 'symbol_id' to the database.
    '''
    delete_word_by_label(label)
    save_args(args, symbol_id)

