# reg_map.py

r'''The code the populates the reg_map database table.

This code also decides which register usages to spill when there are not
enough registers.

Notes on spilling:

This is the order that ties are broken (pick first on list in case of tie).

1.  Local variables (and parameters).
  - to spill, dump variable into memory
  - hard to tell where uses start/stop for save/restore
  - pick vars w/least usage first
  - cost is usage count (including sets), plus 1 if parameter (for initial
    store into memory).
  - possible to interchange vars assigned to different reg_classes to spill
    lower usage var in different reg_class.

2. Temps
  - can tell start/stop for save/restore (their complete lifetime is within
    one block).
  - save spilled temp immediately after assignment, and restore immediately
    before each reference that has a conflicting use since the last reference
    (or initial set).
  - cost of 2 per save/restore, more if spilled temp needed before end-of-life
    on conflicting temp.
  - interchanging two temps more difficult due to different lifetimes.
  - you don't want a reference from the spilled reg_use during the conflicting
    reg_use lifetime.  This would mean that some other reg_use (possibly the
    conflicting one) would have to be spilled to open the register for the
    reference.  Unless some other reg_use ended prior to the spilled reference
    that would open up a register.
  - note that the register used in the reference may have to be different than
    the register originally assigned to for the spilled reg_use.

3. Function calls
  - simply save immediately before call, and restore immediately after call.
  - cost of 2
  - done in fn prolog/epilog if needed by 2+ callers, else by caller to save
    this overhead for other callers.
'''

import collections
import itertools

class fn_reg_map:
    r'''Juggles all of the register assignments for one function.
    '''

    def __init__(self, symbol_id):
        self.symbol_id = symbol_id
        self.use_count = collections.defaultdict(int)   # {rc: use_count}
        self.max_count = collections.defaultdict(int)   # {rc: max_count}
        self.uses = collections.defaultdict(set)        # {rc: set(reg_use)}
        self.spill_reqs = collections.defaultdict(set)  # {rc: set(spill_req)}

    def alloc(self, use):
        if not self.alloc_use(use):
            self.conflict(use)

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
        r'''Need to spill another reg_use to make room for this one.
        '''
        for sub_rc in use.rc.subsets[::-1]:  # top down
            for s in self.spill_reqs[sub_rc]:
                if s.size >= use.num:
                    s.attach(use,
                      itertools.chain.from_iterable(self.uses[rc]
                                                    for rc in sub_rc.subsets))
                    self.spill_reqs[sub_rc].remove(s)
                    return
        spill_req(self, use,
                  itertools.chain.from_iterable(self.uses[rc]
                                                for rc in use.rc.subsets))

    def release(self, use):
        self.use_count[use.rc] -= use.num

    def write(self):
        # FIX: Implement this!
        pass

class reg_use:
    r'''Each instance corresponds to one use of a register.

    The instance is created at the point where the register is set to a value.
    This is the only place in the reg_use lifetime that the register can be
    set.

    However, the register may be referenced multiple times.
    '''

    def __init__(self, reg_map, triple_id, triple_reg_num, rc, num = 1):
        r'''The object is created where the register is set.

        This is the point of first use.
        '''
        self.reg_map = reg_map
        self.triple_id = triple_id
        self.triple_reg_num = triple_reg_num
        self.rc = rc
        self.num = num
        self.spilled = False
        self.pending_spills = set()
        self.spill_obj = None
        self.references = []    # [triple_parameter_id] in chronological order.
        self.spill_references = []
        reg_map.alloc(self)

    def reference(self, triple_parameter_id):
        self.references.append(triple_parameter_id)
        for s in tuple(self.pending_spills):
            s.clear(self)

    def free(self):
        if self.spill_obj:
            self.spill_obj.available()
        self.reg_map.release(self)

    def set_spill(self):
        self.spilled = True

    def spilled_to(self, s):
        self.spill_obj = s

class spill_req:
    r'''This represents a request (or need) to spill reg_use(s).

    There is an attempt to reuse the same spill_req for several reg_uses that
    need space.  The restriction is that these reg_uses do not overlap in
    time.  Thus, freeing one register may be able to satisfy all of their
    needs.

    Also, an attempt is made to find one reg_use to spill with a lifetime long
    enough to overlap the lifetimes of all needed reg_uses.

    A cost is maintained for how many saves and restores (combined) are
    required in the plan developed by the spill_req.  This measures the cost
    if temporary reg_uses are spilled to make room.  At the end of the
    function, the costs of all spill_reqs will be compared to the costs of
    moving local variables into memory and the lesser costs chosen for each
    spill_req.  This is done by sorting the spill_req in a descending cost
    order, sorting the local variables in an increasing cost order and then
    merging the two lists taking the lower value from each pair of elements.
    Where a local variable has a lower cost that the corresponding spill_req,
    the spill plan of the spill_req is abandoned and replaced by the plan to
    store that local variable in memory.

    The cost for local variables is the number of times they are accessed
    (both set and referenced).  If the variable is a parameter, then 1 is
    added to this (for the initial copy to memory).

    The reg_class assigned to each spill_req can not change.  If the spill_req
    is created for the super reg_class, a reg_use spilled there will not work
    for a sub reg_class.  So the reg_class can not be made smaller.  And if
    the spill_req is created for the sub reg_class, and then changed to a
    super reg_class, a reg_use spilled later will not fill the first need.
    '''

    def __init__(self, reg_map, new_reg, regs):
        self.reg_map = reg_map
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
        self.reg_map.spills[self.rc].add(self)

