# reg_alloc.py

import itertools
import collections

Registers = {}
Trivial_nodes = collections.deque()
Reg_classes = {}

class register:
    def __init__(self, name):
        self.name = name
        self.aliases = set((self,))
        Registers[name] = self
    def set_aliases(self, *b):
        self.aliases.update(b)

class reg_class(frozenset):
    @classmethod
    def of_regs(cls, name, *regs):
        ans = cls(regs)
        Reg_classes[name] = ans
        return ans
    def alias(self):
        r'''All of the aliases of this class.
        '''
        if hasattr(self, 'alias_set'): return self.alias_set
        self.alias_set = frozenset()
        for r in self:
            self.alias_set = self.alias_set.union(r.aliases)
        return self.alias_set
    def aliases(self, b):
        r'''Does this reg_class alias reg_class b?
        '''
        return self.alias().intersection(b) or self.intersection(b.alias())

class candidate:
    def __init__(self, reg_cls):
        self.reg_cls = reg_cls
        self.degree = 0
        self.edges = []
        self.rawZ_cache = {}    # {v: rawZ(n, v)}
    def interferes(self, b):
        if b not in self.edges:
            self.edges.append(b)
            b.edges.append(self)
            self.degree += 1
            b.degree += 1
    def stack(self):
        Trivial_nodes.append(self)
        self.degree = 0
        for b in self.edges:
            if b.degree > 0: b.degree -= 1
    def squeeze(self):
        # FIX: ...
        pass

