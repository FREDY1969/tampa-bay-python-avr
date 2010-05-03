# triple2.py

r'''Triple processing for gen_assembler.

This reads the triples back in from the database, but into a new `triple` class
(rather than `ucc.database.triple.triple`) to support gen_assembler.  This ends
up setting the reverse_children, order_in_block and reg_class columns for each
triple. (FIX: Check previous statement when done).
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

        self.predecessors = tuple(crud.read_column('triple_order_constraints',
                                                   'predecessor',
                                                   successor=self.id))

        triple_id_map[self.id] = self
        self.parents = []
        self.updated_attributes = []
        self.deep_children = set([self])
        self.deep_predecessors = set(self.predecessors)

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

    def get_deep_children(self):
        self.deep_children.update(*(child.get_deep_children()
                                    for child in self.children))
        return self.deep_children

    def get_deep_predecessors(self):
        self.deep_predecessors.update(*(child.get_deep_predecessors()
                                        for child in self.children))

        # While we're at it, generate all legal orders of self.children
        # considering the predecessor constraints:
        self.child_orders = []
        for child_order \
         in itertools.permutations(self.children, len(self.children)):
            if all(map(lambda a, b:
                         a.deep_predecessors.disjoint(b.deep_children),
                   # itertools.combinations produces a, b pairs with a and b 
                   # in the same order as they are in child_order.
                   itertools.combinations(child_order, 2))):
                self.child_orders.append(child_order)
        assert not self.children or self.child_orders

        return self.deep_predecessors

    def get_shared_triples(self):
        r'''Returns a dict mapping shared_triples to internal_use_counts.

        Only triples whose internal_use_count is less than their total
        use_count are included.

        Also sets self.shared_triples to the answer for later use.
        '''
        ans = collections.defaultdict(lambda: 0)
        ans.update(zip(self.children, itertools.repeat(1)))
        child_shares = collections.defaultdict(list) # {shared_triple: [child]}
        for child in self.children:
            for shared_triple, count in child.get_shared_triples():
                child_shares[shared_triples].append(child)
                ans[shared_triple] += count

        # {(child1, child2): [shared_triple]}
        self.child_shares = collections.defaultdict(list)
        for shared_triple, children in child_shares.items():
            for key in itertools.permutations(children, 2):
                self.child_shares[key].append(shared_triple)

        for shared_triple, count in tuple(ans.items()):
            if shared_triple.use_count == count:
                del ans[shared_triple]
        self.shared_triples = ans
        return ans

    def get_reg_usage(self, shared_left, shared_right):
        r'''Returns {reg_class: number_used}, child_order.

        Child_order is a list of (child, child_order) tuples.

        Shared_left and shared_right are iterables yielding triples.
        '''
        shared_left = frozenset(shared_left)

        # {triple: num_internal_links_remaining}
        starting_child_shared_left = dict((shared, self.shared_triples[shared])
                                          for shared in shared_left)

        # {triple: num_internal_links_remaining}
        starting_child_shared_right = {}

        for shared_both in shared_left.union(shared_right):
            # don't want either of these to ever hit 0:
            child_shared_left[shared_both] += 1
            child_shared_right[shared_both] = \
              self.shared_triples[shared_both] + 1

        starting_max_counts = collections.defaultdict(lambda: 0)
        # FIX: Now what?

        best_counts = None
        for child_order in self.child_orders:
            child_shared_left = starting_child_shared_left.copy()
            child_shared_right = starting_child_shared_right.copy()
            max_counts = starting_max_counts.copy()
            order = []
            for child in child_order:
                # FIX: Accumulate prior sibling's outputs
                for shared_triple, count in child.shared_triples.items():
                    accounted_for = False
                    if shared_triple in child_shared_left:
                        child_shared_left[shared_triple] -= count
                        accounted_for = True
                    if shared_triple in child_shared_right:
                        child_shared_right[shared_triple] -= count
                        if child_shared_right[shared_triple] == 0:
                            del child_shared_right[shared_triple]
                        accounted_for = True
                    new_shared_left = {}
                    if not accounted_for:
                        new_shared_left[shared_triple] = \
                          child_shared_right[shared_triple] = \
                            shared_triple.use_count - count
                reg_counts, child_order = \
                  child.get_reg_usage(child_shared_left.keys(),
                                      child_shared_right.keys())
                max_counts = max_regs(max_counts, reg_counts)
                order.append((child, child_order))
                for shared_triple \
                 in tuple(filter(lambda key: child_shared_left[k] == 0,
                                 child_shared_left.keys())):
                    del child_shared_left[shared_triple]
                for shared_triple, count in new_shared_left.items():
                    child_shared_left[shared_triple] = count
            if reg_less(max_counts, best_counts):
                best_counts = max_counts
                best_order = order
        # FIX: Add my outputs

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
    for root in filter(lambda t: not t.parents, triples):
        root.get_deep_children()
        root.get_shared_triples()
        root.get_deep_predecessors()
    return triples

