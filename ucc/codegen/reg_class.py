# reg_class.py

from ucc.database import crud

class reg_class:
    def __init__(self, id, name, reg_size, num_registers):
        self.id = id
        self.name = name
        self.reg_size = reg_size
        self.num_registers = num_registers  # not included in subsets
        self.subsets = [self]               # smaller to larger, including self
                                            #   [subset_rc...]
        self.supersets = [self]             # smaller to larger, including self
                                            #   [superset_rc...]
    def __repr__(self):
        return "<reg_class {}>".format(self.name)

