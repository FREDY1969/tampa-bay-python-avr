# ast.py

r'''The helper classes for the AST information in the database.
'''



import itertools

from ucc.database import assembler, block, crud, fn_xref, symbol_table

def delete_word_by_label(word_label):
    r'''Delete all ast nodes associated with word_label from the database.

    This does not report an error if the word is not in the database.
    '''
    sym = symbol_table.get(word_label, default=None)
    if sym is not None:
        delete_word_by_id(sym.id)

def delete_word_by_id(id):
    r'''Delete all ast nodes associated with word_symbol_id 'id'.
    '''
    crud.delete('ast', word_symbol_id=id)

class ast:
    r'''Internal AST representation (prior to going to database).

    This is the AST representation created by the parser.  At the end of the
    parse, this structure is stored into the database and then discarded.

    It is a generic one-size-fits-all object that stores the column values as
    attributes on the object, and the child ast nodes in self.args. 
    '''

    attr_cols_node = (
        #: Values passed as keyword args and stored as attributes that describe
        #: this ast node (and are set to None on `macro_expand`).
        'kind', 'label', 'symbol_id', 'int1', 'int2', 'str1', 'str2', 'type_id',
    )

    attr_cols = attr_cols_node + (
        #: All values passed as keyword args and stored as attributes.
        'expect', 'expected_type',
        'line_start', 'column_start', 'line_end', 'column_end',
    )

    arg_cols = (
        #: Values passed as parameters to the save method.
        'word_symbol_id', 'parent_node', 'parent_arg_num', 'arg_order',
    )

    # default attribute values:
    kind = 'call'
    expect = 'value'
    expected_type = type_id = None
    label = symbol_id = None
    int1 = int2 = str1 = str2 = None
    line_start = column_start = line_end = column_end = None

    def __init__(self, *args, **kws):
        r'''Generic init function.

        Generally objects are created by calling `from_parser`, `call` or
        `word` instead.

        The 'args' are the child ast nodes, and 'kws' are the attributes for
        this node.
        '''
        self.args = args
        for name, value in kws.items():
            if name not in self.attr_cols:
                raise KeyError("ast: illegal attribute: {}".format(name))
            setattr(self, name, value)

    @classmethod
    def from_parser(cls, syntax_position_info, *args, **kws):
        r'''Called from the `ucc.parser` to generate ast nodes.

        The 'args' are the child ast nodes, and 'kws' are the attributes for
        this node.
        '''
        ans = cls(*args, **kws)
        ans.line_start, ans.column_start, ans.line_end, ans.column_end = \
          syntax_position_info
        return ans

    @classmethod
    def call(cls, fn_symbol_id, *args, **kws):
        r'''Returns a call to fn_symbol_id with 'args' as its arguments.

        'fn_symbol_id' may be either the integer id, or the label of the global
        word as a string.

        'kws' may optionally include 'syntax_position_info'.  Otherwise the
        'kws' are simply passed to __init__ as attributes.
        '''
        if 'syntax_position_info' in kws:
            line_start, column_start, line_end, column_end = \
              kws['syntax_position_info']
            del kws['syntax_position_info']
        else:
            line_start = column_start = line_end = column_end = None
        return cls(ast.word(fn_symbol_id),
                   args,
                   line_start=line_start, column_start=column_start,
                   line_end=line_end, column_end=column_end,
                   **kws)

    @classmethod
    def word(cls, symbol_id, syntax_position_info = (None, None, None, None),
             **kws):
        r'''Returns an ast node for the 'symbol_id' word.

        'symbol_id' may be either the integer id, or the label of the global
        word as a string.

        'kws' are simply passed to __init__ as attributes, along with the
        'kind' and the 'label' attributes.
        '''
        line_start, column_start, line_end, column_end = syntax_position_info
        if isinstance(symbol_id, str):
            symbol_id = symbol_table.get(symbol_id).id
        return cls(kind='word',
                   label=symbol_table.get_by_id(symbol_id).label,
                   symbol_id=symbol_id,
                   line_start=line_start, column_start=column_start,
                   line_end=line_end, column_end=column_end,
                   **kws)

    def get_syntax_position_info(self):
        return (self.line_start, self.column_start,
                self.line_end, self.column_end)

    def macro_expand(self, fn_symbol, words_needed, args, **kws):
        r'''Replaces this ast node with the expanded node.

        Also replaces the node's children ('args').

        All attribute names in self.attr_cols_node that are not included in
        'kws' are set to None.

        Finally, it calls `prepare` on the updated node (itself) and returns
        the prepared node.
        '''
        self.args = args
        for key, value in kws.items():
            setattr(self, key, value)
        for key in self.attr_cols_node:
            if key not in kws:
                setattr(self, key, None)
        return self.prepare(fn_symbol, words_needed)

    def __repr__(self):
        if self.kind == 'word':
            return "<ast word:{}>".format(self.symbol_id)
        return "<ast {}{}{}>" \
                 .format(self.kind,
                         ''.join(" {}:{!r}".format(attr, getattr(self, attr))
                                 for attr in ('int1', 'int2', 'str1', 'str2')
                                 if getattr(self, attr) is not None),
                         ' ' + repr(self.args) if self.args else '')

    def prepare(self, fn_symbol, words_needed):
        r'''Called immediately after parsing, before writing to the database.

        Calls `prepare_args` on itself first, then prepare_<expect> on the
        word in the first arg.

        Also updates `fn_xref` and `symbol_table.symbol.side_effects` info so
        that these data will be known during the intermediate code generation
        phase that follows parsing.  See prepare_args_ function for more info.

        .. _prepare_args: ucc.database.ast-module.html#prepare_args
        '''
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
        if self.kind in ('ioreg', 'ioreg-bit'):
            fn_symbol.side_effects = 1
        return self

    def prepare_args(self, fn_symbol, words_needed):
        r'''Replaces self.args with the prepared args.
        '''
        self.args = \
          prepare_args(fn_symbol, self.args, words_needed)

    def save(self, word_symbol,
             parent = None, parent_arg_num = None, arg_order = None):
        r'''Writes itself and its children (args) to the database.
        '''
        kws = dict(itertools.chain(
                     [(attr, getattr(self, attr)) for attr in self.attr_cols],
                     list(zip(self.arg_cols,
                         (word_symbol.id, parent, parent_arg_num,
                          arg_order)))))
        self.word_symbol = word_symbol
        self.id = crud.insert('ast', **kws)
        save_args(self.args, word_symbol, self.id)

    def compile(self):
        r'''Generates intermediate code for this AST node.
        '''
        if self.kind in ('approx', 'int', 'ratio'):
            return block.Current_block.gen_triple(
                     self.kind, int1=self.int1, int2=self.int2,
                     syntax_position_info=self.get_syntax_position_info())

        if self.kind == 'string':
            name = crud.gensym('strlit')
            sym = symbol_table.symbol.create(name, 'const')
            asm_block = assembler.block(self.word_symbol.id, 'flash', name)
            asm_block.append_inst('int16', str(len(self.str1)))
            asm_block.append_inst('bytes', repr(self.str1))
            asm_block.write()
            return block.Current_block.gen_triple(
                     'global', symbol=sym,
                     syntax_position_info=self.get_syntax_position_info())

        if self.kind == 'call':
            if self.args and isinstance(self.args[0], ast) and \
               self.args[0].kind == 'word':
                word_obj = symbol_table.get(self.args[0].label).word_obj
                compile_method = word_obj.get_method('compile', self.expect)
                return compile_method(self)
            else:
                raise AssertionError("call indirect not supported yet")

        if self.kind == 'word':
            sym = symbol_table.get_by_id(self.symbol_id)
            if sym.context is None:
                word_obj = symbol_table.get_by_id(self.symbol_id).word_obj
                compile_method = word_obj.get_method('compile', self.expect)
                ans = compile_method(self)
                return ans
            if sym.kind in ('parameter', 'var'):
                return block.Current_block.gen_triple('local', symbol=sym,
                         syntax_position_info=self.get_syntax_position_info())
            raise ValueError("{}.compile: unknown symbol.kind {!r}"
                               .format(sym.kind))

        if self.kind in ('no-op', 'None'):
            return None

        if self.kind == 'label':
            block.new_label(self.label, self.word_symbol.id)
            return None

        if self.kind == 'jump':
            block.Current_block.unconditional_to(self.label)
            return None

        if self.kind == 'if-true':
            arg_triples = self.compile_args()
            block.Current_block.true_to(arg_triples[0], self.label)
            return None

        if self.kind == 'if-false':
            arg_triples = self.compile_args()
            block.Current_block.false_to(arg_triples[0], self.label)
            return None

        if self.kind == 'series':
            self.compile_args()
            return None

        if self.kind in ('ioreg', 'ioreg-bit'):
            if self.expect in ('value', 'condition'):
                return block.Current_block.gen_triple(
                         'input' if self.kind == 'ioreg' else 'input-bit',
                         string=self.label, int1=self.int1,
                         syntax_position_info=self.get_syntax_position_info())
            else:
                raise AssertionError("ast node[{}]: expect {} not supported "
                                     "for {}"
                                       .format(self.id, self.expect, self.kind))

        raise AssertionError("ast node[{}]: unknown ast kind -- {}"
                               .format(self.id, self.kind))

    def compile_args(self):
        r'''Returns a tuple of triples by compiling each arg.
        '''
        return compile_args(self.args)

def prepare_args(fn_symbol, args, words_needed):
    r'''Prepares each of the args.

    This involves setting the 'expect' and 'type_id' attributes for each `ast`
    and doing macro expansion.

    It also sets the 'side_effects' and 'suspends' attributes on the symbols
    for functions, and records xref info using the `fn_xref.calls`,
    'fn_xref.uses', and 'fn_xref.sets' functions.

    The labels of the words needed by these args are added to the
    'words_needed' set.

    Returns a tuple of the new args to use in place of the args passed in.
    '''
    return tuple(arg.prepare(fn_symbol, words_needed)
                   if isinstance(arg, ast)
                   else prepare_args(fn_symbol, arg, words_needed)
                 for arg in args)

def save_args(args, word_symbol, parent = None):
    r'''Writes args as children to word_symbol in the database.

    'args' is a sequence of: None, `ast` node, or sequence of these.
    '''
    for arg_num, arg in enumerate(args):
        if arg is None:
            arg = ast(kind = 'None', expect = None)
        if isinstance(arg, ast):
            arg.save(word_symbol, parent, arg_num, 0)
        else:
            for position, x in enumerate(arg):
                x.save(word_symbol, parent, arg_num, position)

def compile_args(args):
    r'''Compiles each of the args.

    Each 'arg' is either an `ast` node or sequence of `ast` nodes.

    Returns a tuple of triples.
    '''
    return tuple(arg.compile()
                   if isinstance(arg, ast)
                   else compile_args(arg)
                 for arg in args)

def save_word(label, word_symbol, args):
    r'''Writes 'args' as the ast for word_symbol to the database.

    Uses 'label' to delete all ast nodes associated with that label first.
    These would the ast nodes saved from a prior compile.
    '''
    delete_word_by_label(label)
    save_args(args, word_symbol)

