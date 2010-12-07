# breaking_links.py

r'''This studies algorithms for breaking links.

There are (unassigned) "register_groups" (RG) that each have a set of
"rg_neighbors" (RN) forming a many-to-one relationship.  For each RG, one RN
must be broken.

Each RN is linked to several "reg_use_linkages" (RUL) in a many-to-many
relationship.  Breaking an RN requires breaking all of its RULs.  But each RUL
may be shared by more than one RN.

This code assumes one register class and all RULs have the same spill cost.

So we will start with a list of register_groups.  Each element in this list is
a list of rg_neighbors.  Each element in the rg_neighbors list is a set of
reg_use_linkages.

Each rg_neighbor has a list of reg_use_linkages, which will be represented
here by simple integers.  (We can skip overlaps and reg_uses).

Thus:

    [                           # for each unassigned register_group (RG)
        [                       # for each rg_neighbor
            frozenset(int)      # set of reg_use_linkages
        ]
    ]

or: [[frozenset(int)]]

This must be run on Python3 for the collections.Counter!
'''

import random
import itertools
import collections
import operator
import functools

def gen_problem(num_rg, rn_avg, rn_sd, rul_avg, rul_sd, max_rul):
    return [gen_rn(normal(rn_avg, rn_sd, 1), rul_avg, rul_sd, max_rul)
            for _ in range(num_rg)]

def normal(avg, sd, min = None, max = None):
    r'''Returns an integer on a normal distribution.
    '''
    ans = int(round(random.normalvariate(avg, sd)))
    if max is not None and ans > max:
        return normal(avg, sd, min, max)
    if min is not None and ans < min:
        return normal(avg, sd, min, max)
    return ans

def test_normal(avg, sd, n):
    for n, seq \
     in itertools.groupby(sorted(normal(avg, sd) for _ in range(n))):
        print(n, seq_len(seq))

def seq_len(seq):
    return sum(1 for _ in seq)

def gen_rn(num_rns, rul_avg, rul_sd, max_rul):
    return sorted((gen_rul_set(normal(rul_avg, rul_sd, 1, max_rul), max_rul)
                   for _ in range(num_rns)),
                  key=lambda s: len(s))

def gen_rul_set(num_ruls, max_rul):
    return frozenset(random.sample(range(max_rul), num_ruls))

def best_pick(problem):
    return best_rest(sorted(problem, key=lambda rn: len(rn[0]), reverse=True))

def best_rest(problem, start=0, union=frozenset(), best_ruls=None):
    for s in problem[start]:
        u2 = union.union(s)
        if best_ruls is None or len(u2) < len(best_ruls):
            if start + 1 == len(problem):
                best_ruls = u2
            else:
                best_ruls = best_rest(problem, start + 1, u2, best_ruls)
    return best_ruls

def count_unique(sets):
    r'''Returns the number of unique members of sets.

    These members represent RULs, so this is a count of the number of RULs to
    be broken.

        >>> count_unique(({1,2},{2,3},{3,4}))
        4
    '''
    return len(union_of_sets(sets))

def union_of_sets(seq_of_sets):
    r'''Returns the union of a sequence of sets.

    The result is a frozenset.

        >>> union_of_sets(({1,2},{2,3},{3,4}))
        frozenset({1, 2, 3, 4})
    '''
    return frozenset(itertools.chain.from_iterable(seq_of_sets))

def planA(problem):
    r'''Take set of least weight, weight = 1/count across all sets.

        >>> #     3/2      1/2+2/3=7/6  2 2/3      2 2/3
        >>> p = [({1,2,3}, {4,5,6},     {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> #     3           4/2
        >>> planA(p)
        6
    '''
    rul_weights = {rul: 1/count
                     for rul, count
                      in collections.Counter(rul
                                               for rn in problem
                                                 for s in rn
                                                   for rul in s)
                                    .items()}
    #print("rul_weights", rul_weights)
    return count_unique(
             sorted(rn, key=lambda s: sum(rul_weights[i] for i in s))[0]
             for rn in problem)

def planB(problem):
    r'''Take set of least weight, weight = 1/count across all sets - dups in rn.

        >>> #     3/2      2 1/2    4          4
        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> #     3           4/2
        >>> planB(p)
        4
    '''
    rul_weights = {
      rul: 1/count
        for rul, count
         in collections.Counter(rul
                                  for rn in problem
                                    for rul in union_of_sets(rn))
                       .items()}
    #print("rul_weights", rul_weights)
    return count_unique(
             sorted(rn, key=lambda s: sum(rul_weights[i] for i in s))[0]
             for rn in problem)

def planC(problem):
    r'''Take the smallest set, no weighting.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> planC(p)
        6
    '''
    return count_unique(rn[0] for rn in problem)

def planD(problem):
    r'''Rank pairs of rns by shared RULs, for each pair take best combination.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> planD(p)
        4
    '''
    combined_ruls = [union_of_sets(rn) for rn in problem]
    overlaps = sorted(((a_i, b_i, len(a.intersection(b)))
                         for (a_i, a), (b_i, b) \
                          in itertools.combinations(enumerate(combined_ruls),
                                                    2)),
                      key=operator.itemgetter(2),
                      reverse=True)
    def gen_sets():
        seen = set()
        not_seen = set()
        for a_i, b_i, overlap in overlaps:
            if overlap == 0:
                not_seen.add(a_i)
                not_seen.add(b_i)
            elif a_i not in seen and b_i not in seen:
                yield min((a.union(b)
                           for a, b
                            in itertools.product(problem[a_i], problem[b_i])),
                          key=len)
                seen.add(a_i)
                seen.add(b_i)
            else:
                if a_i not in seen: not_seen.add(a_i)
                if b_i not in seen: not_seen.add(b_i)
        for i in not_seen.difference(seen): yield problem[i][0]

    return count_unique(gen_sets())

def planE(problem):
    r'''Divide problem into non-overlaps subproblems, and do best_pick on each.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> planE(p)
        number of groups 1
        0
    '''
    combined_ruls = [union_of_sets(rn) for rn in problem]

    groups = []         # list of ([index], set of RULs)

    def regroup(i, s, groups):
        combined_indices = [i]
        combined_ruls = set(s.copy())
        for indices, ruls in groups:
            if s.intersection(ruls):
                combined_indices.extend(indices)
                combined_ruls.update(ruls)
            else:
                yield indices, ruls
        yield combined_indices, combined_ruls

    for i, s in enumerate(combined_ruls):
        groups = regroup(i, s, groups)

    groups = tuple(groups)
    print("number of groups", len(groups))

    if len(groups) > 1:
        return sum(len(best_pick(problem[i] for i in indices))
                   for indices, _ in groups)
    return 0

def planF(problem):
    r'''Stepwise, picking rn with least smallest set.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> planF(p)
        4
    '''
    return len(stepwise(problem[:], pick_least))

def planG(problem):
    r'''Stepwise, picking rn with greatest smallest set.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> planG(p)
        4
    '''
    return len(stepwise(problem[:], pick_greatest))

def planH(problem):
    r'''Stepwise, sorting rn ascending ahead of time.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> planH(p)
        4
    '''
    problem = sorted(problem, key=lambda rn: len(rn[0]))
    return len(stepwise(problem, pick_first))

def planI(problem):
    r'''Stepwise, sorting rn descending ahead of time.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> planI(p)
        4
    '''
    problem = sorted(problem, key=lambda rn: len(rn[0]), reverse=True)
    return len(stepwise(problem, pick_first))

def planJ(problem):
    r'''Stepwise, sorting rn ascending ignoring dup RULs.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> planJ(p)
        4
    '''
    return len(stepwise(problem, pick_least_no_dups))

def planK(problem):
    r'''Stepwise, sorting rn descending ignoring dup RULs.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> planK(p)
        4
    '''
    return len(stepwise(problem, pick_greatest_no_dups))

def pick_smallest(rn, state):
    r'''Pick the smallest rn, not counting ruls in state.

        >>> pick_smallest(({1,2,3}, {4,5,6,7}), {4,5,6})
        ({4, 5, 6, 7}, {4, 5, 6, 7})
    '''
    ans = min(rn, key=lambda s: len(s.difference(state)))
    return ans, state.union(ans)

def stepwise(problem, rn_picker, ruls_selector = pick_smallest,
             state = frozenset(), ans = frozenset()):
    while problem:
        rn = rn_picker(problem, state)
        ruls, state = ruls_selector(rn, state)
        ans = ans.union(ruls)
        problem.remove(rn)
    return ans

def pick_first(problem, state):
    r'''Pick the first rn.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9},)]
        >>> state = {4,5,6}
        >>> pick_first(p, state) == p[0]
        True
    '''
    return problem[0]

def pick_least(problem, state):
    r'''Pick the rn, with the smallest ruls -- not counting ruls in state.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9},)]
        >>> state = {4,5,6}
        >>> pick_least(p, state) == p[0]
        True
    '''
    return min(problem,
               key=lambda rn: min(len(s.difference(state)) for s in rn))

def pick_greatest(problem, state):
    r'''Pick the rn, with the greatest smallest ruls.
    
    Not counting ruls in state.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9},)]
        >>> state = {4,5,6}
        >>> pick_greatest(p, state) == p[1]
        True
    '''
    return max(problem,
               key=lambda rn: min(len(s.difference(state)) for s in rn))

def pick_least_no_dups(problem, state):
    r'''Pick the rn, with the smallest ruls.
    
    Not counting ruls in state or in remaining problems.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9},)]
        >>> state = {4,5,6}
        >>> pick_least_no_dups(p, state) == p[0]
        True
    '''
    return min(enumerate(problem),
               key=functools.partial(min_len_no_dups, problem, state))[1]

def pick_greatest_no_dups(problem, state):
    r'''Pick the rn, with the greatest smallest ruls.
    
    Not counting ruls in state or in remaining problems.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9,10},)]
        >>> state = {4,5,6}
        >>> pick_greatest_no_dups(p, state) == p[1]
        True
    '''
    return max(enumerate(problem),
               key=functools.partial(min_len_no_dups, problem, state))[1]

def min_len_no_dups(problem, state, i_rn):
    r'''Return len of min set in i_rn ignoring state and dups with other rns.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9,10},)]
        >>> min_len_no_dups(p, {4,5,6}, (0, p[0]))
        0
    '''
    return min(len(s.difference(
                     state.union(
                       union_of_sets(
                         s for j in range(len(problem))
                           if j != i_rn[0]
                           for s in problem[j]))))
               for s in i_rn[1])

# From recipes section of itertools man page.
def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

def best_combination(problem):
    r'''Try all combinations and pick the best one.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4})]
        >>> best_combination(p)
        4
    '''
    return len(best_pick(problem))

def run_plans(num_rg, rn_avg, rn_sd, rul_avg, rul_sd, max_rul):
    p = gen_problem(num_rg, rn_avg, rn_sd, rul_avg, rul_sd, max_rul)
    for n, fn in sorted(((fn(p), fn)
                         for fn
                          in (best_combination, planA, planB, planC, planD,
                              planE, planF, planG, planH, planI, planJ, planK)),
                        key=operator.itemgetter(0)):
        print("%3d" % n, fn.__doc__.split('\n')[0].strip())

