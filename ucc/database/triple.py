# triple.py

from ucc.database import crud, symbol_table

class triple(object):
    id = None
    soft_predecessors_written = False
    writing = False

    def __init__(self, operator, int1=None, int2=None, string=None,
                       syntax_position_info=None):
        r'''Creates the object, but does not write it to the database (yet).

        int1 and int2 may be integers, other triples, or symbol_table.symbols
        '''
        self.operator = operator
        self.int1 = int1
        self.int2 = int2
        self.string = string
        self.line_start, self.column_start, self.line_end, self.column_end = \
          syntax_position_info or (None, None, None, None)
        self.labels = []  # All the symbol_ids to store this value into.
        self.soft_predecessors = []     # [triple]
        self.hard_predecessors = []     # [triple]

    def __repr__(self):
        return "<triple %s:%s(%s,%s)>" % \
                 (self.id, self.operator, self.int1, self.int2)

    def add_label(self, symbol_id):
        r'''Adds a label to this triple.

        This means that the results of this triple will be stored in the
        symbol_id variable (which could be either a local or global variable).

        This may be called multiple times with the same symbol_id.  It
        silently ignores all but the first call.
        '''
        if symbol_id not in self.labels:
            self.labels.append(symbol_id)

    def add_soft_predecessor(self, pred):
        r'''Adds a soft link between 'pred' and self.

        This means that the dependency is only recorded if some other triple
        requires 'pred', but this dependency alone is not enough to cause
        'pred' to be saved to the database.

        'pred' must be a triple.

        See also, add_hard_predecessor.
        '''
        self.soft_predecessors.append(pred)

    def add_hard_predecessor(self, pred):
        r'''Adds a hard link between 'pred' and self.

        This guarantees that self is needed, then 'pred' is also needed.

        'pred' must be a triple.

        See also, add_soft_predecessor.
        '''
        self.hard_predecessors.append(pred)

    def write(self, block_id):
        r'''Writes triple to database.

        Returns triple id.

        Be sure to also call write_soft_predecessors after all of the hard
        writes have been done for the block!
        '''
        if self.id is None:
            assert not self.writing
            self.writing = True
            if isinstance(self.int1, triple):
                int1 = self.int1.write(block_id)
            elif isinstance(self.int1, symbol_table.symbol):
                int1 = self.int1.id
            else:
                int1 = self.int1
            if isinstance(self.int2, triple):
                int2 = self.int2.write(block_id)
            elif isinstance(self.int2, symbol_table.symbol):
                int2 = self.int2.id
            else:
                int2 = self.int2
            self.id = crud.insert('triples',
                                  block_id=block_id,
                                  operator=self.operator,
                                  int1=int1,
                                  int2=int2,
                                  string=self.string,
                                  line_start=self.line_start,
                                  column_start=self.column_start,
                                  line_end=self.line_end,
                                  column_end=self.column_end,
                                 )
            for label in self.labels:
                crud.insert('gens', block_id=block_id, symbol_id=label,
                                    triple_id=self.id)
            for t0 in self.hard_predecessors:
                crud.insert('triple_order_constraints',
                            predecessor=t0.write(block_id),
                            successor=self.id)
            self.writing = False
        return self.id

    def write_soft_predecessors(self, block_id):
        r'''Writes soft_predecessor info to the database.

        This also calls write_soft_predecessors on all triples that this
        triple has a hard dependency on.

        Call this only after all of the required triples for the block have
        been written.  Calling this will not cause any more triples to be
        written, and will just ignore dependencies to unwritten triples.
        '''
        if not self.soft_predecessors_written:
            if isinstance(self.int1, triple):
                self.int1.write_soft_predecessors(block_id)
            if isinstance(self.int2, triple):
                self.int2.write_soft_predecessors(block_id)
            for t0 in self.hard_predecessors:
                t0.write_soft_predecessors(block_id)
            for t2 in self.soft_predecessors:
                if t2.id is not None:
                    crud.insert('triple_order_constraints',
                                predecessor=t2.id,
                                successor=self.id)
            self.soft_predecessors_written = True

