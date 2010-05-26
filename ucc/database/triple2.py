# triple2.py

r'''Triple processing for gen_assembler.

This reads the triples back in from the database, but into a new `triple` class
(rather than `ucc.database.triple.triple`) to support gen_assembler.  This is
used after the order_triples to do the register allocation.
'''

import sys   # temp for debugging...
import collections
import itertools

from ucc.database import crud

class triple:
    def __init__(self, row, triple_id_map):
        for key, value in row.items():
            setattr(self, key, value)
        self.labels = tuple(crud.read_column('triple_labels', 'symbol_id',
                                             triple_id=self.id))

        triple_id_map[self.id] = self
        self.parents = []
        self.updated_attributes = []

    def connect_children(self, triple_id_map):
        self.children = \
          [triple_parameter(row, triple_id_map)
           for row in crud.read_as_dicts('triple_parameters',
                                         parent_id=self.id,
                                         order_by='evaluation_order')]

    def add_parent(self, parent):
        self.parents.append(parent)

class triple_parameter:
    def __init__(self, row, triple_id_map):
        for key, value in row.items():
            setattr(self, key, value)
        if self.parent_id is not None:
            self.parent = triple_id_map[self.parent_id]
        self.parameter = triple_id_map[self.parameter_id]
        if not self.ghost:
            self.parameter.add_parent(self)

def read_triples(block_id):
    r'''Reads and returns list of all `triple` objects in block_id.
    '''
    #print >> sys.stderr, "read_triples", block_id
    triple_id_map = {}
    triples = [triple(row, triple_id_map)
               for row in crud.read_as_dicts('triples', block_id=block_id,
                                             order_by='abs_order_in_block')]
    #print >> sys.stderr, "read_triples: triples", triples
    for t in triples:
        t.connect_children(triple_id_map)
    return triples

