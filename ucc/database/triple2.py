# triple2.py

r'''Triple processing for gen_assembler.

This reads the triples back in from the database, but into a new `triple` class
(rather than `ucc.database.triple.triple`) to support gen_assembler.  This ends
up setting the reverse_children, order_in_block and reg_class columns for each
triple.
'''

import sys   # temp for debugging...

from ucc.database import crud

class triple(object):
    def __init__(self, row, triple_id_map):
        for key, value in row.items():
            setattr(self, key, value)
        self.labels = tuple(crud.read_column('triple_labels', 'symbol_id',
                                             triple_id=self.id))

        # FIX: Is this used anywhere?
        self.predecessors = tuple(crud.read_column('triple_order_constraints',
                                                   'predecessor',
                                                   successor=self.id))

        triple_id_map[self.id] = self
        self.parents = []
        self.updated_attributes = []
        self.deep_children = set([self])

    def connect_children(self, triple_id_map):
        self.children = \
          [triple_id_map[id]
           for id in crud.read_column('triple_parameters', 'parameter_id',
                                      parent_id=self.id,
                                      order_by='parameter_num')]
        for child in self.children:
            child.add_parent(self)

    def add_parent(self, parent):
        self.parents.append(parent)

    def get_children(self):
        self.deep_children.update(*(child.get_children()
                                    for child in self.children))
        return self.deep_children

    def order_children(self, predecessors):
        r'''Figures out the order to evaluate the child nodes.

        Also returns a 3 tuple:
        
            temp_register_est
            [set([parent, ...]), ...]
            set([node_seen, ...])

        Each [parent, ...] element in the second return value requires a save
        register.  As the parents are seen, they are deleted from the lists
        and as the lists become empty, the save registers are no longer
        needed.

        The nodes seen are all of this node's children and itself.
        '''

        # FIX: This needs to be re-examined after adding triple_parameters
        #      table.

        nodes_seen = set((self,))
        if not isinstance(self.int1, triple):
            left_temp_est, left_saves = 0, []
        else:
            left_temp_est, left_saves, left_seen = \
              self.int1.order_children(predecessors)
            del_node(self, left_saves)
            nodes_seen.update(left_seen)
        if not isinstance(self.int2, triple):
            right_temp_est, right_saves = 0, []
        else:
            right_temp_est, right_saves, right_seen = \
              self.int2.order_children(predecessors)
            del_node(self, right_saves)
            nodes_seen.update(right_seen)
        self.reverse_children = \
          right_temp_est + len(right_saves) > left_temp_est + len(left_seen)
        if len(self.parents) > 1:
            pass

        if left_temp_set == right_temp_set:
            return left_temp_set + 1, 
        return max(left_temp_set, right_temp_set)

def del_node(node, lists):
    for l in lists: l.discard(node)
    return [_f for _f in lists if _f]

def read_triples(block_id):
    r'''Reads and returns list of all `triple` objects in block_id.
    '''
    #print >> sys.stderr, "read_triples", block_id
    triple_id_map = {}
    triples = [triple(row, triple_id_map)
               for row in crud.read_as_dicts('triples', block_id=block_id)]
    #print >> sys.stderr, "read_triples: triples", triples
    for t in triples:
        t.connect_children(triple_id_map)
    for t in triples:
        t.get_children()
    return triples

