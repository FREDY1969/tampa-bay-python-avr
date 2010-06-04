# reg_map.py

import collections
import itertools

class fn_reg_map:
    def __init__(self, symbol_id, subsets, sizes, code_seqs):
        self.symbol_id = symbol_id
        self.subsets = subsets          # {(rc1, rc2): subset_rc}
        self.sizes = sizes              # {rc: num_registers}
        self.code_seqs = code_seqs      # {code_seq_id: code_seq obj}
                                        # ... see code_seq.py
        self.use_count = collections.defaultdict(int)   # {rc: use_count}
        self.max_count = collections.defaultdict(int)   # {rc: max_count}
        self.uses = collections.defaultdict(set)        # {rc: set(reg_use)}
        self.spills = collections.defaultdict(set)      # {rc: set(spill)}

    def alloc(self, triple_id, triple_reg_num, rc, num = 1):
        ans = reg_use(triple_id, triple_reg_num, rc, num)
        if not self.alloc_use(ans):
            self.conflict(ans)
        return ans

    def alloc_use(self, use):
        # Check for free space first:
        for sub_rc in use.rc.subsets:  # bottom up
            if self.use_count[sub_rc] + use.num <= self.max_count[sub_rc]:
                self.use_count[sub_rc] += use.num
                self.uses[sub_rc].add(use)
                return True

        # No free space, bump super reg_uses to higher rc:
        selected_sub_rc = None
        selected_use_list = None
        for sub_rc in rc.subsets:
            super_uses = sorted((a_use for a_use in self.uses[sub_rc]
                                       if a_use.rc != use.rc and
                                          use.rc in a_use.rc.subsets),
                                key = lambda u: u.num,
                                reverse = True)
            sum = 0
            for i, a_use in enumerate(super_uses):
                sum += a_use.num
                if sum >= num:
                    selected_sub_rc = sub_rc
                    selected_use_list = super_uses[:i + 1]
                    break
            if selected_sub_rc is not None:
                break
        if selected_sub_rc is not None:
            for a_use in selected_use_list:
                self.use_count[selected_sub_rc] -= a_use.num
                self.uses[selected_sub_rc].remove(selected_use_list)
            self.use_count[selected_sub_rc] += use.num
            succeeded = True
            for i, a_use in enumerate(selected_use_list):
                if not self.alloc_use(a_use):
                    succeeded = False
                    self.use_count[selected_sub_rc] -= use.num
                    for a_use in selected_use_list[i:]:
                        assert self.alloc_use(a_use), "internal logic error"
            return succeeded

        # Nothing to bump, increase max_count looking in subsets from biggest
        # to smallest:
        for sub_rc in use.rc.subsets[::-1]:
            regs_needed = use.num - self.use_count[sub_rc]
            if self.max_count[sub_rc] + regs_needed <= sub_rc.num_registers:
                self.use_count[sub_rc] += use.num
                self.max_count[sub_rc] = self.use_count[sub_rc]
                return True

        # No room!
        return False

    def conflict(self, use):
        # Spill another reg_use
        for sub_rc in use.rc.subsets[::-1]:  # top down
            for s in self.spills[sub_rc]:
                if s.size >= use.num:
                    s.attach(use,
                      itertools.chain.from_iterable(self.uses[rc]
                                                    for rc in sub_rc.subsets))
                    self.spills[sub_rc].remove(s)
                    return
        spill(self, use,
              itertools.chain.from_iterable(self.uses[rc]
                                            for rc in use.rc.subsets))

    def access(self, use):
        use.used()

    def free(self, *uses):
        for use in uses:
            self.use_count[use.rc] -= use.num
            self.access(use)
            use.free()

    def write(self):
        # FIX: Implement this!
        pass

class reg_use:
    def __init__(self, triple_id, triple_reg_num, rc, num = 1):
        self.triple_id = triple_id
        self.triple_reg_num = triple_reg_num
        self.rc = rc
        self.num = num
        self.spill = False
        self.pending_spills = set()
        self.spill_obj = None

    def used(self):
        for s in tuple(self.pending_spills):
            s.clear(self)

    def set_spill(self):
        self.spill = True

    def spilled_to(self, s):
        self.spill_obj = s

    def free(self):
        if self.spill_obj:
            self.spill_obj.available()

class spill:
    def __init__(self, the_spill, new_reg, regs):
        self.the_spill = the_spill
        self.rc = new_reg.rc
        self.new_regs = []
        self.alloc(new_reg, regs)
        self.cost = 0

    def alloc(self, new_reg, regs):
        self.new_regs.append(new_reg)
        self.num_registers = new_reg.num
        self.candidate_reg_uses = set(regs)
        new_reg.spilled_to(self)
        for r in regs: r.pending_spills.add(self)

    def clear(self, reg):
        self.candidate_reg_uses.remove(reg)
        reg.pending_spills.remove(self)
        if len(self.candidate_reg_uses) == 0:
            reg.set_spill()
            self.cost += 2 * self.num_registers

    def available(self):
        self.the_spill.spills[self.rc].add(self)

