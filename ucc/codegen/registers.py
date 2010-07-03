# registers.py

r'''Helper functions and classes for dealing with registers.

These are machine independant, taking their information from the machine
database.

    >>> from ucc.codegen import registers
    >>> import os
    >>> with crud.db_connection(os.path.join(os.path.dirname(__file__),
    ...                                      'avr.db'),
    ...                         False, False):
    ...     registers.init()
    >>> a = registers.reg_usage.make(single=4, immed=2)
    >>> a
    <reg_usage immed=2 single=4>
    >>> b = registers.reg_usage.make(single=2, immed=4)
    >>> b
    <reg_usage immed=4 single=2>
    >>> a.merge(b)
    <reg_usage immed=4 single=2>
'''

import collections
import itertools

from ucc.database import crud

Debug = False

def init():
    global reg_usage, Reg_classes

    for d in crud.read_as_dicts('vertex'): vertex(d)
    for v in Vertex_by_id.values():
        v.parent_vertex = Vertex_by_id[v.parent] if v.parent else None
        if v.parent_vertex:
            v.parent_vertex.add_child(v)

    for i, v in enumerate(topo_sort(Vertex_by_id.values(),
                                    lambda v: (v.parent,) if v.parent else ())):
        v.topo_order = i + 1

    Reg_classes = {d['name']: reg_class(d)
                   for d in crud.read_as_dicts('reg_class')}

    for rc in Reg_classes.values():
        # These are in order from biggest to smallest in size
        rc.subclasses = \
          tuple(
            sorted(
              itertools.chain.from_iterable(
                v.reg_classes for v in rc.vertex.deep_children),
              key = lambda rc: len(rc.registers),
              reverse = True))

    # These are in order from smallest to biggest in size
    temp_ordered_reg_classes = tuple(sorted(Reg_classes.values(),
                                            key = lambda rc: len(rc.registers)))

    # Can't put doctests in this class!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    class reg_usage(collections.namedtuple('reg_usage',
                                           (d.name
                                            for d
                                             in temp_ordered_reg_classes))):
        ordered_reg_classes = temp_ordered_reg_classes

        @classmethod
        def make(cls, **counts):
            fields = dict(zip(cls._fields, itertools.repeat(0)))
            fields.update(counts)
            return cls(**fields)

        def __repr__(self):
            args = ['reg_usage']
            for f in self._fields:
                n = getattr(self, f)
                if n: args.append("{}={}".format(f, n))
            return "<{}>".format(' '.join(args))

        def __lt__(self, reg_usage_b):
            return sum(self) < sum(reg_usage_b)

        def __gt__(self, reg_usage_b):
            return reg_usage_b < self

        def merge(self, reg_usage_b):
            r'''Merges the reg_usage between self and reg_usage_b.

            Registers may be moved to different subclasses to even out the
            usage and make for lower total register usage figures.
            '''
            ans = dict(zip(self._fields, itertools.repeat(0)))
            self_holes = {}     # {reg_class: num_holes}
            b_holes = {}        # {reg_class: num_holes}
            for rc in self.ordered_reg_classes:
                self_count = getattr(self, rc.name)
                b_count = getattr(reg_usage_b, rc.name)
                if Debug and (self_count or b_count):
                    print("{}: self {}, b {}"
                            .format(rc.name, self_count, b_count))
                if self_count < b_count:
                    for subclass_rc in rc.subclasses:
                        delta = min(b_holes.get(subclass_rc.name, 0),
                                    b_count - self_count)
                        if Debug:
                            print("delta for {}: {}"
                                    .format(subclass_rc.name, delta))
                        if delta:
                            b_count -= delta
                            b_holes[subclass_rc.name] -= delta
                            if b_count == self_count:
                                break
                    ans[rc.name] = b_count
                    if b_count > self_count:
                        self_holes[rc.name] = b_count - self_count
                elif self_count > b_count:
                    for subclass_rc in rc.subclasses:
                        delta = min(self_holes.get(subclass_rc.name, 0),
                                    self_count - b_count)
                        if Debug:
                            print("delta for {}: {}"
                                    .format(subclass_rc.name, delta))
                        if delta:
                            self_count -= delta
                            self_holes[subclass_rc.name] -= delta
                            if self_count == b_count:
                                break
                    ans[rc.name] = self_count
                    if self_count > b_count:
                        b_holes[rc.name] = self_count - b_count
                else:
                    ans[rc.name] = self_count
            return self.make(**ans)

class reg_class:
    def __init__(self, fields):
        for attr_name, value in fields.items():
            setattr(self, attr_name, value)
        self.registers = \
          frozenset(crud.read_column('reg_in_class', 'reg', reg_class=self.id))
        self.aliases = \
          frozenset(crud.read_column('class_alias', 'reg', reg_class=self.id))
        self.vertex = Vertex_by_id[self.v]
        self.vertex.add_reg_class(self)

    def __repr__(self):
        return "<reg_class {}>".format(self.name)

Vertex_by_id = {}       # {id: vertex object}

class vertex:
    vertex_by_bm = {}   # {vertex_set: vertex object}

    def __init__(self, fields):
        for attr_name, value in fields.items():
            setattr(self, attr_name, value)
        self.vertex_by_bm[self.vertex_set] = self
        Vertex_by_id[self.id] = self
        self.reg_classes = []
        self.children = []
        self.deep_children = []

    def __repr__(self):
        return "<vertex {}>".format(self.id)

    def add_reg_class(self, reg_class):
        self.reg_classes.append(reg_class)

    def add_child(self, child):
        self.children.append(child)
        self.add_deep_child(child)

    def add_deep_child(self, child):
        self.deep_children.append(child)
        if self.parent_vertex:
            self.parent_vertex.add_deep_child(child)

    def intersection(self, vertex_b):
        r'''Returns the vertex for the intersection between self and vertex_b.

        Returns None if self and vertex_b do not intersect.
        '''
        new_set = self.vertex_set & vertex_b.vertex_set
        if new_set:
            return self.vertex_by_bm[new_set]
        return None

def topo_sort(items, successor_fn):
    r'''Generates items in topological order based on successor_fn.

    Successor_fn(item) returns the sequence of successors for item.

        >>> tuple(topo_sort((1,2,3), lambda n: (n+1,) if n < 3 else ()))
        (1, 2, 3)
        >>> tuple(topo_sort((1,2,3), lambda n: (n-1,) if n > 0 else ()))
        (3, 2, 1)
    '''
    items = tuple(items)

    # {item: {successor}}
    successors = collections.defaultdict(set)

    # {item: {predecessor}}
    predecessors = collections.defaultdict(set)

    for item in items:
        for successor in successor_fn(item):
            predecessors[successor].add(item)
            successors[item].add(successor)

    all_items = set(items)

    while all_items:
        next_set = all_items - predecessors.keys()
        assert next_set, "internal error: cycle in topo_sort"
        for item in next_set:
            yield item
            for successor in successors[item]:
                predecessors[successor].remove(item)
                if not predecessors[successor]:
                    del predecessors[successor]
        all_items.difference_update(next_set)

