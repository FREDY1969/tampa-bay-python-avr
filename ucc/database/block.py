# block.py

r'''The helper class for blocks of intermediate code.

A block of code is only entered at the top, and only exited at the bottom.
Thus, there are never any jumps into the middle of a block, or jumps out of
the middle of a block.

The code for each block is represented by a directed acyclic graph whose nodes
are `triple` objects.  This places the least constraints on the order that the
triples must be evaluated in to maximize the ability of the optimizer and code
generator to play games with instruction ordering.  The final assembler code
generation process decides on the final ordering for the triples.

    >>> init()
'''

import collections
from ucc.database import crud, fn_xref, symbol_table, triple

#Current_block = None \
  #: Only used during the `compile` process (e.g., Current_block.gen_triple(...)).

#Block_ids = {}         #: {block_name: block_id}

def init():
    global Current_block, Block_ids
    Current_block = None
    Block_ids = {}

def new_label(name, word_symbol_id):
    r'''Terminate the Current_block and create a new block.

    The way that the Current_block is terminated depends on which of the
    following methods were called on it prior to calling new_label:

        - `block.true_to`
        - `block.false_to`
        - `block.unconditional_to`
        - `block.block_end`

    'name' is used as the next block to terminate the Current_block.

    If none of these have been called, `block.unconditional_to` is done
    automatically.

    'name' and 'word_symbol_id' are for the new block.
    '''
    global Current_block
    if Current_block:
        if Current_block.state == 'end_fall_through':
            Current_block.write(name)
        if Current_block.state == 'end_absolute':
            Current_block.write()
        else:
            Current_block.unconditional_to(name)
    block(name, word_symbol_id)

class block(object):
    last_triple = None
    next_conditional = None

    def __init__(self, name, word_symbol_id):
        global Current_block

        assert not Current_block, \
               "{}: previous block({}) not written" \
                 .format(name, Current_block.name)

        self.name = name
        self.word_symbol_id = word_symbol_id

        # The final labels left in this dict when the block is written are
        # added as is_gen labels to the indicated triples.  These can be either
        # global or local (including parameter) variables.
        #
        # Each time a 'set' is done to a variable, the triple setting that
        # variable is updated (replacing any previous triple).  So at any
        # point in time, the triple in this dict is the last one to set the
        # indicated variable.
        #
        # When a triple is associated with a global variable that is used
        # indirectly by a subsequent triple, the global variable is added to
        # the first triple's labels list.  Thus, these triples will always
        # store to the global variable, even if a later triple also stores
        # to that global variable.  Also a "hard" dependency is established.
        #
        # When a triple is associated with a global variable that may be set
        # indirectly by a subsequent triple, a "soft" dependency is
        # established.  The labels entry remains here, but is also entered as a
        # dirty_label to prevent gen_triple from using it.
        #
        # When a gen_triple is called for the rvalue of this global variable,
        # the triple here is used.
        #
        # All triples here are written to the database when the block write is
        # done.
        self.labels = {}             # {symbol_id: triple}
        self.dirty_labels = set()    # symbol_ids for gen_triple to ignore.

        # This is used to find previous triples that are duplicates of the
        # triple being created.  Information here is never changed or deleted.
        # But not all triples here may be written out at the end...
        self.triples = {}            # {(operator, int1, int2, string): triple}

        # This stores the last triple that has side effects.  When a new
        # triple comes along that also has side effects, a hard dependency is
        # established between them to guarantee that the side effects happen
        # in the proper sequence.  The last triple here is always included in
        # the final block write to the database.
        self.side_effects = None

        # The triples that (may have) used each global variable since the last
        # time it may have been set.
        #
        # When a new triple is added that may set a global variable, a
        # dependency is established between each of the triples here and the
        # new triple to ensure that the new triple doesn't run until after all
        # of the triples here have run.  These are "soft" dependencies that are
        # not enough, in themselves, to cause the triples here to be written to
        # the database when the final block write is done.
        #
        # Each time a new triple is created that may set a global variable,
        # this entry is cleared (after creating the above dependencies).  (The
        # new triple will also be entered in sets_global, below).
        #
        # Triples in this dict may not be written to the database when the
        # block write is done.
        #
        # This dict is: {symbol_id: [triple]}
        self.uses_global = collections.defaultdict(list)

        # The triple that (may have) last set each global variable.  When a new
        # triple is created that uses or sets a global variable, a "hard"
        # dependency is created between this triple and the new triple.
        #
        # These triples will always be written to the database when the final
        # block write is done.
        self.sets_global = {}        # {symbol_id: triple}

        self.state = 'not_ended'

        Current_block = self

    def __repr__(self):
        return "<block {}>".format(self.name)

    def more(self):
        global Current_block
        assert self.state != 'end_absolute', \
               "{}: block missing label after jump".format(self.name)
        if self.state == 'end_fall_through':
            name = crud.gensym('block')
            self.write(name)
            Current_block = block(name, self.word_symbol_id)
            return True
        return False

    def true_to(self, cond, name_t):
        r'''Branch to 'name_t' if `triple` 'cond' is true.

        False falls through.

        This method is only called on Current_block.
        '''
        if self.more(): Current_block.true_to(cond, name_t)
        else:
            self.last_triple = triple.triple('if-true', (cond,), string=name_t)
            self.next_conditional = name_t
            self.state = 'end_fall_through'

    def false_to(self, cond, name_f):
        r'''Branch to 'name_f' if `triple` 'cond' is false.

        True falls through.

        This method is only called on Current_block.
        '''
        if self.more(): Current_block.false_to(cond, name_f)
        else:
            self.last_triple = triple.triple('if-false', (cond,), string=name_f)
            self.next_conditional = name_f
            self.state = 'end_fall_through'

    def unconditional_to(self, name):
        r'''Unconditionally branch to the block named 'name'.

        This method is only called on Current_block.
        '''
        if self.more(): Current_block.unconditional_to(name)
        else:
            self.state = 'end_fall_through'
            self.write(name)

    def block_end(self, last_triple):
        r'''Mark the block as having no successor block.

        For example, when the block ends in a 'return' or by raising an
        exception.

        This method is only called on Current_block.
        '''
        assert self.state == 'not_ended', \
               "{}: double block end".format(self.name)
        self.state = 'end_absolute'
        self.last_triple = last_triple
        self.write()

    def gen_triple(self, operator, parameters=None, int1=None, int2=None,
                         symbol=None, string=None, syntax_position_info=None):
        r'''Create a new triple for this block.

        This method is only called on Current_block.
        '''
        #print self.name, "gen_triple", operator, int1, int2, string
        if self.more():
            return Current_block.gen_triple(operator, parameters, int1, int2,
                                            symbol, string,
                                            syntax_position_info)
        if operator in ('global', 'local'):
            if symbol.id in self.labels and symbol.id not in self.dirty_labels:
                return self.labels[symbol.id]
        if operator == 'call_direct':
            assert isinstance(symbol, symbol_table.symbol)
            fn_symbol = symbol
            ans = triple.triple(operator, parameters, symbol=fn_symbol,
                                syntax_position_info=syntax_position_info)
            uses_vars, sets_vars = fn_xref.get_var_uses(fn_symbol.id)
            uses_or_sets_vars = uses_vars.union(sets_vars)
            for var_id in uses_vars.intersection(self.labels):
                self.labels[var_id].add_label(var_id, False)
            if fn_symbol.side_effects:
                if self.side_effects is not None:
                    ans.add_hard_predecessor(self.side_effects)
                self.side_effects = ans
            for var_id in sets_vars.intersection(self.uses_global):
                for t in self.uses_global[var_id]:
                    ans.add_soft_predecessor(t)
                del self.uses_global[var_id]
            for var_id in uses_or_sets_vars.intersection(self.sets_global):
                ans.add_hard_dependency(self.sets_global[var_id])
            for var_id in uses_vars:
                self.uses_global[var_id].append(ans)
            for var_id in sets_vars:
                self.sets_global[var_id] = ans
                if var_id in self.labels: self.dirty_labels.add(var_id)
            return ans
        if operator == 'call_indirect':
            raise AssertionError("call_indirect not yet implemented")
        if operator not in ('input', 'input-bit',
                            'output', 'output-bit-set', 'output-bit-clear'):
            key = operator, parameters, int1, int2, symbol, string
            if key not in self.triples:
                self.triples[key] = \
                  triple.triple(operator, parameters, int1, int2,
                                symbol, string, syntax_position_info)
            return self.triples[key]
        ans = triple.triple(operator, parameters, int1, int2, symbol, string,
                            syntax_position_info)
        if operator == 'global':
            self.uses_global[symbol.id].append(ans)
            if symbol.id in self.sets_global:
                ans.add_hard_predecessor(self.sets_global[symbol.id])
            if symbol.id in self.labels:
                self.labels[symbol.id].add_label(symbol.id, False)
        if operator in ('input', 'input-bit',
                        'output', 'output-bit-set', 'output-bit-clear'):
            #print self.name, "got", operator, "storing in side_effects"
            if self.side_effects is not None:
                ans.add_hard_predecessor(self.side_effects)
            self.side_effects = ans
        return ans

    def label(self, symbol_id, triple):
        r'''Attach 'symbol_id' as a "label" for 'triple'.

        A "label" is a symbol (variable) that the result of the `triple` must
        be stored into.  One triple may have multiple labels attached to it,
        meaning that the result must be stored into multiple places.
        '''
        self.labels[symbol_id] = triple
        if symbol_id in self.dirty_labels: self.dirty_labels.remove(symbol_id)
        if symbol_table.get_by_id(symbol_id).context is None:
            # This is a global variable!
            if symbol_id in self.sets_global:
                triple.add_hard_predecessor(self.sets_global[symbol_id])
            self.sets_global[symbol_id] = triple
            if symbol_id in self.uses_global:
                for t in self.uses_global[symbol_id]:
                    triple.add_soft_predecessor(t)
                del self.uses_global[symbol_id]

    def write(self, next = None):
        r'''Writes the block and associated triples to the database.

        Returns the id assigned to the block.
        '''

        global Current_block

        #print self.name, "write"

        if self.state == 'end_absolute':
            next = None
        else:
            assert next is not None

        id = crud.insert('blocks',
                         name=self.name,
                         word_symbol_id=self.word_symbol_id,
                         last_triple_id=self.last_triple.id
                                          if self.last_triple
                                          else None,
                         next=next,
                         next_conditional=self.next_conditional)

        # add final labels to their associated triples:
        for var_id, t in self.labels.items():
            t.add_label(var_id, True)

        # write out triples:
        #
        # first figure out the set of all triples that will be forcably
        # written:
        forced_triples = set(self.labels.values())
        if self.side_effects is not None:
            #print self.name, "adding", self.side_effects, "due to side_effects"
            forced_triples.add(self.side_effects)
        forced_triples.update(list(self.sets_global.values()))
        if self.last_triple is not None:
            #print self.name, "adding", self.last_triple, "as last_triple"
            forced_triples.add(self.last_triple)
        #
        # then write them all:
        #
        for t in forced_triples:
            t.write(id)
        #
        # then call write_soft_predecessors for all of them:
        #
        for t in forced_triples:
            t.write_soft_predecessors(id)

        assert self.name not in Block_ids
        Block_ids[self.name] = id

        Current_block = None
        #print self.name, "write returning", id
        return id

def delete(symbol):
    r'''Deletes all of the blocks associated with 'symbol' from the database.

    This also deletes all associated information in the database for the
    deleted blocks.

    This is used to delete the results from a prior compile run.
    '''
    block_ids = crud.read_column('blocks', 'id', word_symbol_id=symbol)
    if block_ids:
        crud.delete('gens', block_id=block_ids)
        crud.delete('kills', block_id=block_ids)
        crud.delete('ins', block_id=block_ids)
        crud.delete('outs', block_id=block_ids)
        triple.delete(block_ids)
        crud.delete('block_successors', predecessor=block_ids)
        crud.delete('block_successors', successor=block_ids)
        crud.delete('blocks', id=block_ids)
