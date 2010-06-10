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

        # {rc: use_count}
        self.use_count = collections.defaultdict(int)

        # {rc: max_count}
        self.max_count = collections.defaultdict(int)

        # {rc: {reg_use: ref_index}}
        self.assigned_uses = collections.defaultdict(dict)

        # [(reg_use, ref_index, {reg_use: ref_index})]
        self.unassigned_uses = []

        self.reg_uses = []

    def alloc(self, use, ref_index = None):
        if ref_index is None:
            self.reg_uses.append(use)
        if not self.alloc_use(use, ref_index):
            self.conflict(use, ref_index)

    def alloc_use(self, use, ref_index = None):
        #print("alloc_use", use)
        # Check for free space first:
        for sub_rc in use.rc.subsets:  # bottom up
            if self.use_count[sub_rc] + use.regs_needed <= \
                 self.max_count[sub_rc]:
                use.assign_to((sub_rc,
                               count(self.use_count[sub_rc], use.regs_needed)),
                              ref_index)
                print("took free_space: use_count was", self.use_count[sub_rc],
                      end=' ')
                self.use_count[sub_rc] += use.regs_needed
                print("now", self.use_count[sub_rc])
                self.assigned_uses[sub_rc][use] = ref_index
                return True

        #print("alloc_use: no free space")
        # No free space, bump super reg_uses to higher rc:
        selected_sub_rc = None
        selected_use_list = None
        for sub_rc in use.rc.subsets:
            super_uses = sorted(((a_use, a_ref_index)
                                 for a_use, a_ref_index
                                  in self.assigned_uses[sub_rc].items()
                                   if a_use.rc != use.rc and
                                      use.rc in a_use.rc.subsets),
                                key = lambda u: u[0].regs_needed,
                                reverse = True)
            sum = self.max_count[sub_rc] - self.use_count[sub_rc]
            for i, (a_use, a_ref_index) in enumerate(super_uses):
                sum += a_use.regs_needed
                if sum >= use.regs_needed:
                    selected_sub_rc = sub_rc
                    selected_use_list = super_uses[:i + 1]
                    break
            if selected_sub_rc is not None:
                break
        if selected_sub_rc is not None:
            # Remove selected_use_list from selected_sub_rc:
            for a_use, a_ref_index in selected_use_list:
                print("bumping: use_count was",
                      self.use_count[selected_sub_rc],
                      end=' ')
                self.use_count[selected_sub_rc] -= a_use.regs_needed
                print("now", self.use_count[selected_sub_rc])
                del self.assigned_uses[selected_sub_rc][a_use]
            # Assign new use:
            print("taking bumped: use_count was",
                  self.use_count[selected_sub_rc],
                  end=' ')
            self.use_count[selected_sub_rc] += use.regs_needed
            print("now", self.use_count[selected_sub_rc])
            self.assigned_uses[selected_sub_rc][use] = ref_index
            for i, (a_use, a_ref_index) in enumerate(selected_use_list):
                if not self.alloc_use(a_use, a_ref_index):
                    print("unbumping: use_count was",
                          self.use_count[selected_sub_rc],
                          end=' ')
                    self.use_count[selected_sub_rc] -= use.regs_needed
                    print("now", self.use_count[selected_sub_rc])
                    del self.assigned_uses[selected_sub_rc][use]
                    for a_use, a_ref_index in selected_use_list[i:]:
                        if not self.alloc_use(a_use, a_ref_index):
                            raise AssertionError("internal logic error")
                    break
            else:
                use.assign_to((selected_sub_rc,
                               count(self.use_count[selected_sub_rc] -
                                     use.regs_needed,
                                     use.regs_needed)),
                              ref_index)
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
                use.assign_to((sub_rc,
                               count(self.use_count[sub_rc], use.regs_needed)),
                              ref_index)
                print("adding regs: use_count was", self.use_count[sub_rc],
                      end=' ')
                self.use_count[sub_rc] += use.regs_needed
                print("now", self.use_count[sub_rc])
                self.assigned_uses[sub_rc][use] = ref_index
                self.max_count[sub_rc] = self.use_count[sub_rc]
                return True

        #print("alloc_use: no room")
        # No room!
        return False

    def conflict(self, use, ref_index = None):
        r'''Need to spill another reg_use to make room for this one.
        '''
        #print("conflict", use, ref_index)
        self.unassigned_uses.append((use, ref_index, dict(
          itertools.chain.from_iterable(self.assigned_uses[rc].items()
                                        for rc in use.rc.subsets))))

    def ref(self, reg_use, ref_index):
        r'''Called by reg_use.reference.
        '''
        if reg_use.current_assignment:
            # [(reg_use, ref_index, {reg_use: ref_index})]
            prior_unassigned = {}  # {u_reg_use: num_registers}
            for i, (u_use, u_ref_index, overlaps) \
             in enumerate(self.unassigned_uses):
                needed = u_use.regs_needed
                for use in overlaps.keys():
                    if use in prior_unassigned:
                        needed += use.regs_needed
                    elif use != reg_use:
                        needed -= use.regs_needed
                    else:
                        pass
            examine_combinations(combs, reg_use)

    def done(self, reg_use):
        r'''Called by reg_use.free.
        '''
        if reg_use.current_assignment:
            rc = reg_use.current_assignment[0]
            del self.assigned_uses[rc][reg_use]
            self.use_count[rc] -= reg_use.regs_needed

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

def combinations(u_uses, num_registers):
    r'''Generates the combinations of u_uses that can supply num_registers.

    u_uses is {reg_use: ref_index}.

    Yields a tuple of reg_uses.
    '''
    return tuple(generate_combinations(num_registers,
                                       sorted(u_uses.keys(),
                                              key=lambda u: u.regs_needed,
                                              reverse=True)))

def generate_combinations(num_registers, uses, start=0):
    r'''Yields all combinations of uses[start:] whose sum is >= num_registers.

        >>> class reg_use:
        ...     def __init__(self, name, regs_needed):
        ...         self.name = name
        ...         self.regs_needed = regs_needed
        ...     def __repr__(self): return self.name
        >>> A1 = reg_use('A1', 1)
        >>> B1 = reg_use('B1', 1)
        >>> C1 = reg_use('C1', 1)
        >>> D2 = reg_use('D2', 2)
        >>> E2 = reg_use('E2', 2)
        >>> tuple(generate_combinations(2, [D2, E2, A1, B1]))
        ((D2,), (E2,), (A1, B1))
        >>> tuple(generate_combinations(3, [D2, E2, A1, B1, C1]))
        ((D2, E2), (D2, A1), (D2, B1), (D2, C1), (E2, A1), (E2, B1), (E2, C1), (A1, B1, C1))
    '''
    if num_registers <= 0:
        yield ()
        return
    for i in range(start, len(uses)):
        use = uses[i]
        for rest in generate_combinations(num_registers - use.regs_needed,
                                          uses, i + 1):
            yield (use,) + rest

def examine_combinations(combs, reg_use):
    r'''Figures out what to do with reg_use.

    combs is [(rc, u_use, u_ref_index, ((reg_use...)...))]
    '''
    history = {}        # {reg_use: {used for reg_use}}

def use_needed(combs, reg_use):
    history = {}        # {reg_use: {used for reg_use}}
    for rc, u_use, u_ref_index, overlaps in combs:
        ok = False
        for comb in overlaps:
            if reg_use not in comb:
                # FIX: !!!
                pass

class temp_reg_use:
    r'''Each instance corresponds to one use of a register.

    The instance is created at the point where the register is set to a value.
    This is the only place in the reg_use lifetime that the register can be
    set.  But if a triple has multiple parents, the temp_reg_use could have
    multiple references.

    However, the register may be referenced multiple times.
    '''

    def __init__(self, reg_map, reg_map_key, rc, num = 1):
        r'''The object is created where the register is set.

        This is the point of first use.
        '''
        self.reg_map = reg_map
        self.reg_map_key = reg_map_key
        self.rc = rc
        self.num = num
        self.references = []      # list of list of reg_map_key, optional fn_key
        self.active = True
        self.spilled = False
        self.current_assignment = None
        reg_map.alloc(self)

    def __repr__(self):
        return "<temp_reg_use {}>".format(self.reg_map_key)

    @property
    def regs_needed(self):
        return self.num * self.rc.reg_size

    def reference(self, reg_map_key):
        #print("reference", self, reg_map_key)
        ref_index = len(self.references)
        self.references.append([reg_map_key])
        self.reg_map.ref(self, ref_index)

    def free(self):
        self.active = False
        self.reg_map.done(self)

    def set_spill(self):
        cost = self.regs_needed
        self.current_assignment = None
        if self.spilled:
            return cost
        self.spilled = True
        return 2 * cost

    def assign_to(self, fn_key, ref_index = None):
        if ref_index is None:
            self.assigned = fn_key
        else:
            assert len(self.refernces[ref_index]) == 1, \
                   "{}: duplicate assign_ref on {}".format(self, ref_index)
            self.references[ref_index].append(fn_key)
        self.current_assignment = fn_key

    @property
    def assigns_needed(self):
        return self.regs_needed - len(self.current_assignment[1])

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

