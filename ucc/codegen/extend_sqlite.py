# extend_sqlite.py

r'''User functions for sqlite.

The only function called here from Python outside this module is
register_functions (called from alloc_reg in ucc/codegen/reg_alloc.py).

The sqlite functions registered here are:
    rc_subset(reg_class_A, reg_class_B)
        - Returns common reg_class.  Treats NULL arguments as "don't care".
          So only returns NULL if both arguments are NULL.
    chk_num_regs(num_regs_A, num_regs_B)
        - Checks to see that num_regs_A == num_regs_B, but treats NULL as
          "don't care".  Only returns NULL if both arguments are NULL.

There are also aggregate versions of each of these:
    aggr_rc_subset(reg_class)
    aggr_num_regs(num_regs)
'''

import collections

from ucc.database import crud

class aggr_rc_subset:
    r'''Sqlite3 aggregate function for aggr_rc_subset.
    
    Produces the rc that is a subset of each of the submitted entries.

        >>> subsets = {(1, 1): 1, (1, 3): 1, (3, 1): 1, 
        ...            (2, 2): 2, (2, 3): 2, (3, 2): 2, (3, 3): 3}
        >>> rcs = aggr_rc_subset(subsets)
        >>> rcs.finalize()       # NULL for 0 rows.
        >>> rcs = aggr_rc_subset(subsets)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(3)
        >>> rcs.finalize()
        2
        >>> rcs = aggr_rc_subset(subsets)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(2)
        >>> rcs.step(3)
        >>> rcs.step(1)
        >>> rcs.step(1)
        >>> rcs.finalize()
        Traceback (most recent call last):
           ...
        AssertionError: aggr_rc_subset -- no subset possible
    '''
    def __init__(self, subsets = None):
        if subsets: self.subsets = subsets
        else: self.subsets = Subsets
        self.rc_counts = collections.defaultdict(int)

    def step(self, rc):
        if rc is not None:
            self.rc_counts[rc] += 1

    def finalize(self):
        if not self.rc_counts: return None

        # Return subset of all rc's:
        ans = None
        for rc in self.rc_counts:
            if ans is None: ans = rc
            else:
                ans = self.subsets.get((ans, rc))
                assert ans is not None, "aggr_rc_subset -- no subset possible"
        return ans

class aggr_num_regs:
    r'''Sqlite3 aggregate function for aggr_num_regs.

    All num_regs seen should match.  If not, an AssertionError is raised.

        >>> nr = aggr_num_regs()
        >>> nr.finalize()       # NULL for 0 rows.
        >>> nr = aggr_num_regs()
        >>> nr.step(2)
        >>> nr.step(2)
        >>> nr.step(2)
        >>> nr.step(2)
        >>> nr.finalize()
        2
        >>> nr = aggr_num_regs()
        >>> nr.step(2)
        >>> nr.step(1)
        >>> nr.step(2)
        >>> nr.finalize()
        Traceback (most recent call last):
          ...
        AssertionError: non-conforming num_regs: {1, 2}
    '''
    def __init__(self):
        self.num_regs = set()

    def step(self, num_regs):
        if num_regs is not None:
            self.num_regs.add(num_regs)

    def finalize(self):
        if not self.num_regs: return None
        if len(self.num_regs) == 1: return next(iter(self.num_regs))
        raise AssertionError(
                "non-conforming num_regs: {}".format(self.num_regs))

class get_max:
    r'''Sqlite3 aggregate function for get_max.

    Returns the second argument associated with the greatest first argument.

        >>> gm = get_max()
        >>> gm.finalize()       # NULL for 0 rows.
        >>> gm = get_max()
        >>> gm.step(1, 'a')
        >>> gm.step(2, 'b')
        >>> gm.step(3, 'c')
        >>> gm.step(4, 'd')
        >>> gm.finalize()
        'd'
        >>> gm = get_max()
        >>> gm.step(3, 'c')
        >>> gm.step(4, 'd')
        >>> gm.step(1, 'a')
        >>> gm.step(2, 'b')
        >>> gm.finalize()
        'd'
    '''
    def __init__(self):
        self.max_value = None
        self.result = None

    def step(self, value, result):
        if value is not None and result is not None and \
           (self.max_value is None or self.max_value < value):
            self.max_value = value
            self.result = result

    def finalize(self):
        return self.result

class get_min:
    r'''Sqlite3 aggregate function for get_min.

    Returns the second argument associated with the greatest first argument.

        >>> gm = get_min()
        >>> gm.finalize()       # NULL for 0 rows.
        >>> gm = get_min()
        >>> gm.step(1, 'a')
        >>> gm.step(2, 'b')
        >>> gm.step(3, 'c')
        >>> gm.step(4, 'd')
        >>> gm.finalize()
        'a'
        >>> gm = get_min()
        >>> gm.step(3, 'c')
        >>> gm.step(4, 'd')
        >>> gm.step(1, 'a')
        >>> gm.step(2, 'b')
        >>> gm.finalize()
        'a'
    '''
    def __init__(self):
        self.min_value = None
        self.result = None

    def step(self, value, result):
        if value is not None and result is not None and \
           (self.min_value is None or value < self.min_value):
            self.min_value = value
            self.result = result

    def finalize(self):
        return self.result

def rc_subset(rc1, rc2):
    if rc1 is None: return rc2
    if rc2 is None: return rc1
    return Subsets.get((rc1, rc2))

def chk_num_regs(nr1, nr2):
    if nr1 is None: return nr2
    if nr2 is None: return nr1
    if nr1 == nr2: return nr1
    raise AssertionError("non-conforming num_regs: {{{}, {}}}".format(nr1, nr2))

def register_functions():
    # Set up sqlite3 user functions:
    global Subsets
    Subsets = get_reg_class_subsets()  # needed by rc_subset and aggr_rc_subset
    crud.Db_conn.db_conn.create_function("rc_subset", 2, rc_subset)
    crud.Db_conn.db_conn.create_function("chk_num_regs", 2, chk_num_regs)
    crud.Db_conn.db_conn.create_aggregate("aggr_rc_subset", 1, aggr_rc_subset)
    crud.Db_conn.db_conn.create_aggregate("aggr_num_regs", 1, aggr_num_regs)
    crud.Db_conn.db_conn.create_aggregate("get_max", 2, get_max)
    crud.Db_conn.db_conn.create_aggregate("get_min", 2, get_min)

def get_reg_class_subsets():
    r'''Returns {(reg_class1, reg_class2): subset_reg_class}.
    '''
    return {(rc1, rc2): subset
            for rc1, rc2, subset
             in crud.read_as_tuples('reg_class_subsets',
                                    'rc1', 'rc2', 'subset')}

