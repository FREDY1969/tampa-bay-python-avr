# order_triples.py

r'''Order triples and register allocation code.

node is expected to have the following attributes:
  parents is seq of node
  reg_classes is list of reg_class for all registers used by node.
    (output registers are always first).
  num_outputs is number of initial registers (starting at 0) that are output.
  children is seq of (child, list of node_reg_num)
  trashes_children(triple_seq) returns seq of True/False for each child
'''

import itertools

# This looks messed up.  Is this something I started and changed my mind on???
def best_seq(nodes, graph, accum_score, best_score = None):
    r'''Determines the sequence of nodes requiring the least registers.

    Nodes is a set of triples.
    Graph is {predecessor node: set of successors}
        The sequence returned must conform to the predecessor-successor
        constraints of this graph.
    Accum_score is a score object.

    Returns the accum_score for the best sequence of nodes, or None if it
    can't beat a previous best_score.
    '''
    if not nodes:
        return accum_score
    constrained = set()
    for succ_set in graph.values():
        constrained += succ_set
    for next in sorted(nodes - constrained,
                       key=lambda node:
                             max(len(p.reg_classes) for p in parents(node)),
                       reverse=True):
        graph = graph.copy()
        del graph[next]
        nodes = nodes.difference((next,))
        next_score = accum_score.add(next)
        if not best_score or next_score < best_score:
            best_score = best_seq(nodes, graph, next_score, best_score)
    return best_score

def parents(node, ignore = None):
    r'''Recursively generates all parents of node.

        Set up:
            node_X
                node_Y
                    node_Z
                node_Z

        >>> from doctest_tools import mock
        >>> node_Z = mock.obj("node Z")
        >>> node_Y = mock.obj("node Y")
        >>> node_X = mock.obj("node X")
        >>> node_Z.parents = [node_Y, node_X]
        >>> node_Y.parents = [node_X]
        >>> node_X.parents = []

        >>> tuple(parents(node_Z))
        (<mock.obj node Z>, <mock.obj node Y>, <mock.obj node X>)

    '''
    if ignore is None: ignore = set()
    if node not in ignore:
        ignore.add(node)
        yield node
        for p in node.parents:
            for pp in parents(p, ignore): yield pp

class triple_seq:
    def __init__(self, prior_seq, next_triple):
        self.prior_seq = prior_seq
        self.next_triple = next_triple
        self.reg_allocation = self.prior_seq.reg_allocation.copy_for(self)
        self.index = self.prior_seq.index + 1

    def add(self, next_triple):
        return triple_seq(self, next_triple,
                          self.reg_allocation.add(next_triple))

class reg_allocation:
    r'''

        Set up:
            -
                X
                1

        >>> from doctest_tools import mock
        >>> node_minus = mock.obj("minus")
        >>> node_X = mock.obj("X")
        >>> node_X.parents = [node_minus]
        >>> node_X.reg_classes = ['single', 'single']
        >>> node_X.num_outputs = 2
        >>> node_X.children = ()
        >>> node_X.trashes_children = mock.const((False, False))
        >>> node_1 = mock.obj("1")
        >>> node_1.parents = [node_minus]
        >>> node_1.reg_classes = ['single', 'single']
        >>> node_1.num_outputs = 2
        >>> node_1.children = ()
        >>> node_minus.parents = []
        >>> node_minus.reg_classes = \
        ...   ['immed-word', 'immed-word', 'single', 'single']
        >>> node_minus.num_outputs = 2
        >>> node_minus.children = ((node_X, [0, 1]), (node_1, [2, 3]))
        >>> node_minus.trashes_children = mock.const((True, True))

        >>> ts = mock.obj("triple_seq")
        >>> ts.get_index.response(1, node_minus)
        >>> ts.get_index.response(2, node_X)
        >>> ts.get_index.response(3, node_1)
        >>> ts.map_output.response(None, 2, 0, 1, 0, True)
        >>> ts.map_output.response(None, 2, 1, 1, 1, True)
        >>> ts.map_output.response(None, 3, 0, 1, 2, True)
        >>> ts.map_output.response(None, 3, 1, 1, 3, True)
        >>> ts.dec_use_count.response(None, 2)
        >>> ts.dec_use_count.response(None, 3)
        >>> ra = reg_allocation(ts)
        >>> ra.add(node_minus)
    '''

    def __init__(self, triple_seq, prior_allocation = None):
        self.triple_seq = triple_seq

    def copy_for(self, triple_seq):
        return reg_allocation(triple_seq, self)

    def add(self, next_triple):
        # Map the child output registers:
        regs_seen = set()
        next_index = self.triple_seq.get_index(next_triple)
        trashes_flags = next_triple.trashes_children(self.triple_seq)
        for param_num, ((child_triple, child_regs), trashes) \
         in enumerate(itertools.zip_longest(next_triple.children,
                                            trashes_flags,
                                            fillvalue=False)):
            child_index = self.triple_seq.get_index(child_triple)
            for child_reg_num, node_reg_num in enumerate(child_regs):
                assert child_reg_num < child_triple.num_outputs, \
                       "{}[{}]: expects too many outputs from param {}" \
                       .format(next_triple.operator, next_triple.id,
                               param_num + 1)
                regs_seen.add(node_reg_num)
                self.triple_seq.map_output(child_index, child_reg_num,
                                           next_index, node_reg_num, trashes)
            self.triple_seq.dec_use_count(child_index)

        # Map the other remaining registers:
        for i, node_reg_class \
         in enumerate(next_triple.reg_classes[next_triple.num_outputs:]):
            node_reg_num = next_triple.num_outputs + i
            if node_reg_num not in regs_seen:
                self.map(next_triple, node_reg_num,
                         None, self.allocate(node_reg_class))

    def allocate(self, reg_class, first_index = None):
        r'''Allocates a register over the interval first_index to the end of
        the sequence.

        Returns the block_reg_num.
        '''

    def map(self, from_triple, from_reg_num, to_triple, to_reg_num):
        pass

