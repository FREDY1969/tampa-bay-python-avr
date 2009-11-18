# block.py

import collections
from ucc.database import crud

Current_block = None

Block_ids = {}                                        # {block_name: block_id}
Block_predecessors = collections.defaultdict(list)    # {block_name: [pred_id]}

class block(object):
    compare_triple = None
    next_conditional = None

    def __init__(self, name):
        global Current_block

        assert not Current_block, \
               "%s: previous block(%s) not written" % (name, Current_block.name)

        self.name = name

        # The final labels left in this dict when the block is written are
        # added as labels to the indicated triples.  These can be either
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
        # to that global variable.
        #
        # All triples here are written to the database when the block write is
        # done.
        self.labels = {}             # {symbol_id: triple}

        # This is used to find previous triples that are duplicates of the
        # triple being created.  Information here is never changed or deleted.
        # But not all triples here may be written out at the end...
        self.triples = {}            # {(operator, int1, int2, string): triple}

        # This stores the last triple that has side effects.  When a new
        # triple comes along that also has side effects, a dependency is
        # established between them to guarantee that the side effects happen
        # in the proper sequence.  The last triple here is always included in
        # the final block write to the database.
        self.side_effects = None

        # The triples that use each global variable since the last time it was
        # set.
        #
        # When a new triple is added that sets a global variable, a dependency
        # is established between each of the triples here and the new triple
        # to ensure that the new triple doesn't run until after all of the
        # triples here have run.  These are "soft" dependencies that are not
        # enough, in themselves, to cause the triples here to be written to
        # the database when the final block write is done.
        #
        # Each time a new triple is created that sets a global variable, this
        # entry is cleared (after creating the above dependencies).
        #
        # Triples in this dict may not be written to the database when the
        # block write is done.
        #
        # This dict is: {symbol_id: [triple]}
        self.uses_global = collections.defaultdict(list)

        # The triple the last set each global variable.  When a new triple is
        # created that uses or sets a global variable, a "hard" dependency is
        # created between this triple and the new triple.
        #
        # These triples will always be written to the database when the final
        # block write is done.
        self.sets_global = {}        # {symbol_id: triple}

        self.predecessors = set([])  # [block_id]

        self.write_pending = False

        Current_block = self

    def __repr__(self):
        return "<block %s>" % self.name

    def add_predecessor(self, pred_id):
        assert pred_id not in self.predecessors
        self.predecessors.add(pred_id)

    def true_to(self, cond_id, name_t):
        r'''Branch to name_t if cond_id is true.
        
        False falls through.
        '''
        assert not self.write_pending, \
               "%s: block missing label after jump" % self.name
        self.compare_triple = triple.triple('if-true', cond_id, string=name_t)
        self.next_conditional = name_t
        self.write_pending = True

    def false_to(self, cond_id, name_f):
        assert not self.write_pending, \
               "%s: block missing label after jump" % self.name
        self.compare_triple = triple.triple('if-false', cond_id, string=name_f)
        self.next_conditional = name_f
        self.write_pending = True

    def unconditional_to(self, name):
        global Current_block
        assert not self.write_pending, \
               "%s: block missing label after jump" % self.name
        self.write_pending = True
        self.write(name)
        Current_block = None

    def new_label(self, name):
        global Current_block
        assert self.write_pending, \
               "%s: block not terminated properly" % self.name
        self.write_pending = True
        self.write(name)
        Current_block = block(name)

    def block_end(self):
        global Current_block
        assert not self.write_pending, \
               "%s: block missing label after jump" % self.name
        self.write_pending = True
        self.write()
        Current_block = None

    def gen_triple(self, operator, int1=None, int2=None, string=None,
                         syntax_position_info=None):
        assert not self.write_pending, \
               "%s: block missing label after jump" % self.name
        if operator in ('global', 'local'):
            if int1 in self.labels: return self.labels[int1]
        if operator == 'call_direct':
            fn_symbol = symbol_table.get_by_id(int1)
            ans = triple.triple(operator, int1, int2, string,
                                syntax_position_info)
            uses_vars, sets_vars = fn_xref.get_var_uses(int1)
            for var_id in uses_vars.intersection(self.labels):
                self.labels[var_id].add_label(var_id)
            if fn_symbol.side_effects:
                if self.side_effects is not None:
                    ans.add_hard_predecessor(self.side_effects)
                self.side_effects = ans
            for var_id in sets_vars.intersection(self.uses_global):
                for t in self.uses_global[var_id]:
                    ans.add_soft_predecessor(t)
                del self.uses_global[var_id]
            for var_id \
             in uses_vars.union(sets_vars).intersection(self.sets_global):
                ans.add_hard_dependency(self.sets_global[var_id])
            for var_id in uses_vars:
                self.uses_globals[var_id].append(ans)
            for var_id in sets_vars:
                self.sets_globals[var_id] = ans
                if var_id in self.labels: del self.labels[var_id]
            return ans
        if operator == 'call_indirect':
            raise AssertionError("call_indirect not yet implemented")
        if operator not in ('param', 'var_data', 'const_data', 'bss',
                            'ioreg_init', 'eeprom'):
            key = operator, int1, int2, string
            if key not in self.triples:
                self.triples[key] = triple.triple(operator, int1, int2, string,
                                                  syntax_position_info)
            return self.triples[key]
        ans = triple.triple(operator, int1, int2, string, syntax_position_info)
        if operator == 'global':
            self.uses_global[int1].append(ans)
        return ans

    def label(self, symbol_id, triple):
        self.labels[symbol_id] = triple

    def write(self, next = None):
        r'''Writes the block and triples to the database.

        Returns the id assigned to the block.
        '''
        assert self.write_pending, \
               "%s: block not terminated properly" % self.name
        id = crud.insert('blocks',
                         name=self.name,
                         compare_triple_id=self.compare_triple.id
                                             if self.compare_triple
                                             else None,
                         next=next,
                         next_conditional=self.name_conditional)

        # add final labels to their associated triples:
        for var_id, t in self.labels.iteritems():
            t.add_label(var_id)

        # write out triples:
        #
        # first figure out the set of all triples that will be forcably
        # written:
        forced_triples = set(self.labels.values())
        if self.side_effects is not None:
            forced_triples.add(self.side_effects)
        forced_triples.update(self.sets_global.values())
        if self.compare_triple is not None:
            forced_triples.add(self.compare_triple)
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

        if name_t is not None:
            Block_predecessors[name_t].append(id)
        if name_f is not None:
            Block_predecessors[name_f].append(id)

        return id

def write_block_successors():
    r'''Writes all of the block successor info to the database.

    This must be called once after all of the blocks have been written.
    '''
    for name, pred_ids in Block_predecessors.iteritems():
        succ_id = Block_ids[name]
        for pred_id in pred_ids:
            crud.insert('block_successors',
                        predecessor=pred_id,
                        successor=succ_id)
