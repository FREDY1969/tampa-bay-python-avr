# reg_class.py

from ucc.database import crud

class reg_class:
    def __init__(self,):
        self.id
        self.name
        self.reg_size
        self.num_registers      # not included in subsets
        self.subsets            # smaller to larger, including self
                                #   old: [(subset_rc, map)...]
                                #   new: [subset_rc...]

