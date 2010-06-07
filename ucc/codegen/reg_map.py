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
        self.reg_uses = []

    def alloc(self, use):
        self.reg_uses.append(use)
        if not self.alloc_use(use):
            self.conflict(use)

    def alloc_use(self, use):
        #print("alloc_use", use)
        # Check for free space first:
        for sub_rc in use.rc.subsets:  # bottom up
            if self.use_count[sub_rc] + use.regs_needed <= \
                 self.max_count[sub_rc]:
                use.assign_to(sub_rc,
                              count(self.use_count[sub_rc], use.regs_needed))
                print("took free_space: use_count was", self.use_count[sub_rc],
                      end=' ')
                self.use_count[sub_rc] += use.regs_needed
                print("now", self.use_count[sub_rc])
                self.uses[sub_rc].add(use)
                return True

        #print("alloc_use: no free space")
        # No free space, bump super reg_uses to higher rc:
        selected_sub_rc = None
        selected_use_list = None
        for sub_rc in use.rc.subsets:
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
                print("bumping: use_count was",
                      self.use_count[selected_sub_rc],
                      end=' ')
                self.use_count[selected_sub_rc] -= a_use.regs_needed
                print("now", self.use_count[selected_sub_rc])
                self.uses[selected_sub_rc].remove(selected_use_list)
            print("taking bumped: use_count was",
                  self.use_count[selected_sub_rc],
                  end=' ')
            self.use_count[selected_sub_rc] += use.regs_needed
            print("now", self.use_count[selected_sub_rc])
            self.uses[selected_sub_rc].add(use)
            succeeded = True
            for i, a_use in enumerate(selected_use_list):
                if not self.alloc_use(a_use):
                    succeeded = False
                    print("unbumping: use_count was",
                          self.use_count[selected_sub_rc],
                          end=' ')
                    self.use_count[selected_sub_rc] -= use.regs_needed
                    print("now", self.use_count[selected_sub_rc])
                    self.uses[selected_sub_rc].remove(a_use)
                    for a_use in selected_use_list[i:]:
                        if not self.alloc_use(a_use):
                            raise AssertionError("internal logic error")
            if succeeded:
                use.assign_to(selected_sub_rc,
                              count(self.use_count[selected_sub_rc] -
                                    use.regs_needed))
                return True

        #print("alloc_use: nothing to bump")
        # Nothing to bump, increase max_count looking in subsets from biggest
        # to smallest:
        for sub_rc in use.rc.subsets[::-1]:
            regs_needed = \
              use.regs_needed - \
                (self.max_count[sub_rc] - self.use_count[sub_rc])
            #print("alloc_use: sub_rc", sub_rc, "regs_needed", regs_needed,
            #      "max_count", self.max_count[sub_rc])
            if self.max_count[sub_rc] + regs_needed <= sub_rc.num_registers:
                use.assign_to(sub_rc,
                              count(self.use_count[sub_rc], use.regs_needed))
                print("adding regs: use_count was", self.use_count[sub_rc],
                      end=' ')
                self.use_count[sub_rc] += use.regs_needed
                print("now", self.use_count[sub_rc])
                self.uses[sub_rc].add(use)
                self.max_count[sub_rc] = self.use_count[sub_rc]
                return True

        #print("alloc_use: no room")
        # No room!
        return False

    def conflict(self, use):
        r'''Need to spill another reg_use to make room for this one.
        '''
        #print("conflict", use)
        for sub_rc in use.rc.subsets[::-1]:  # top down
            for s in self.spill_reqs[sub_rc]:
                if s.num_registers >= use.regs_needed:
                    s.alloc(use,
                      itertools.chain.from_iterable(self.uses[rc]
                                                    for rc in sub_rc.subsets))
                    self.spill_reqs[sub_rc].remove(s)
                    self.uses[sub_rc].add(use)
                    return
        self.uses[use.rc].add(use)
        spill_req(self, use,
                  itertools.filterfalse(
                    lambda u: u.spilled,
                    itertools.chain.from_iterable(self.uses[rc]
                                                  for rc in use.rc.subsets)))

    def release(self, use, rc):
        r'''Called when use is freed.
        '''
        print("release: use_count was", self.use_count[rc], end=' ')
        self.use_count[rc] -= use.regs_needed
        print("now", self.use_count[rc])
        self.uses[rc].remove(use)

    def write(self):
        # FIX: Implement this!
        pass

def count(start, number):
    r'''Return a tuple of 'number' numbers starting at 'start'.

        >>> count(3, 2)
        (3, 4)
        >>> count(3, 3)
        (3, 4, 5)
        >>> count(3, 1)
        (3,)
        >>> count(3, 0)
        ()
    '''
    return tuple(range(start, start + number))

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
        self.references = []      # [(triple_id, triple_reg_num, rc, [reg_num])]
        self.spill_references = []
        self.active = True
        reg_map.alloc(self)

    def __repr__(self):
        return "<reg_use {}[{}]>".format(self.triple_id, self.triple_reg_num)

    @property
    def regs_needed(self):
        return self.num * self.rc.reg_size

    def reference(self, triple_parameter_id):
        #print("reference", self, triple_parameter_id)
        self.references.append(triple_parameter_id)
        for s in tuple(self.pending_spills):
            s.end_use(self, triple_parameter_id)

    def free(self):
        self.active = False
        if not self.spill_obj and not self.pending_spills:
            self.reg_map.release(self, self.assigned_rc)
        else:
            if self.spill_obj:
                self.spill_obj.available()
            for s in tuple(self.pending_spills):
                s.available()

    def set_spill(self, reference_id):
        self.spill_references.append(reference_id)
        cost = self.regs_needed
        if self.spilled:
            return cost
        self.spilled = True
        return 2 * cost

    def spilled_to(self, s):
        r'''Spill_obj making room for me.
        '''
        self.spill_obj = s
        self.assigned_rc = s.rc
        self.assigned_nums = []

    def assign_to(self, rc, nums):
        self.assigned_rc = rc
        self.assigned_nums = nums

    def add_assigns(self, nums):
        self.assigned_nums.extend(nums)

    @property
    def assigns_needed(self):
        return self.regs_needed - len(self.assigned_nums)

class spill_req:
    r'''This represents a request (or need) to spill reg_use(s).

    There is an attempt to reuse the same spill_req for several reg_uses that
    need space.  The restriction is that these reg_uses do not overlap in
    time.  Thus, freeing one register may be able to satisfy all of their
    needs.

    Also, an attempt is made to find a reg_use to spill with a lifetime long
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

    count = 1

    def __init__(self, reg_map, new_reg, regs):
        self.reg_map = reg_map
        self.rc = new_reg.rc
        self.which = self.count
        self.count += 1
        self.new_regs = []
        self.alloc(new_reg, regs)
        self.cost = 0

    def __repr__(self):
        return "<spill_req {}.{}>".format(self.rc, self.which)

    def alloc(self, new_reg, regs):
        r'''Called to make room for new_reg, with regs currently in-use.
        '''
        self.current_regs_needed = [new_reg]
        self.new_regs.append(new_reg)
        self.num_registers = new_reg.regs_needed
        self.candidate_reg_uses = set(regs)
        #print("alloc", self, new_reg, self.candidate_reg_uses)
        new_reg.spilled_to(self)
        for u in self.candidate_reg_uses:
            u.pending_spills.add(self)

    def end_use(self, reg, reference_id):
        r'''Called when an overlapping reg_use hits a reference.
        '''
        #print("clear", reg, reference_id)
        remainder = sum(u.regs_needed
                        for u in self.candidate_reg_uses
                          if u != reg)
        if remainder < self.num_registers:
            #print("clear: setting spill", reg)
            self.cost += reg.set_spill(reference_id)
            num_freed = reg.regs_needed
            num_used = 0
            for r in self.current_regs_needed[:]:
                if r.assigns_needed <= num_freed:
                    r.add_assigns(
                      reg.assigned_nums[num_used:num_used + r.assigns_needed])
                    self.current_regs_needed.remove(r)
                    self.candidate_reg_uses.add(r)
                    num_used += r.assigns_needed
                else:
                    r.add_assigns(reg.assigned_nums[num_used:])
            if self.current_regs_needed:
                self.current_regs_needed.append(reg)

    def available(self):
        r'''Called when a reg_use is freed.

        This is called for both the new_reg and overlapping reg_uses.
        '''
        #print("available")
        for use in self.candidate_reg_uses:
            use.pending_spills.remove(self)
        self.candidate_reg_uses = set()
        self.reg_map.spill_reqs[self.rc].add(self)

