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
    r'''Return the best union of RULs from problem.

        >>> oprint(best_rest([({1,2,3},{4,5,6}), ({1,2,4}, {6,7,8})]))
        {1, 2, 3, 4}
        >>> oprint(best_rest([({1,2,3},{4,5,6}), ({1,4,5}, {6,7,8})]))
        {1, 4, 5, 6}
    '''
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

        >>> count_unique(({1,2},{3,4},{5,6}))
        6
        >>> count_unique(({1,2},{2,3},{3,4}))
        4
    '''
    return len(union_of_sets(sets))

def union_of_sets(seq_of_sets):
    r'''Returns the union of a sequence of sets.

    The result is a frozenset.

        >>> oprint(union_of_sets(({1,2},{3,4},{5,6})))
        {1, 2, 3, 4, 5, 6}
        >>> oprint(union_of_sets(({1,2},{2,3},{3,4})))
        {1, 2, 3, 4}
    '''
    return frozenset(itertools.chain.from_iterable(seq_of_sets))

def planA(problem, debug=False):
    r'''Take set of least weight, weight = 1/count across all sets.

        >>> #     3/2      1/2+2/3=7/6  2 2/3      2 2/3
        >>> p = [({1,2,3}, {4,5,6},     {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12,13}, {1,2,3,4})]
        >>> #     4              4/2
        >>> planA(p, True)
        'rul_weights' {1: 0.5, 2: 0.5, 3: 0.5, 4: 0.5, 5: 0.333333, 6: 0.333333, 7: 1, 8: 1, 9: 1, 10: 0.5, 11: 1, 12: 1, 13: 1}
        6
    '''
    rul_weights = {rul: 1/count
                     for rul, count
                      in collections.Counter(rul
                                               for rn in problem
                                                 for s in rn
                                                   for rul in s)
                                    .items()}
    if debug: oprint("rul_weights", rul_weights)
    return count_unique(
             sorted(rn, key=lambda s: sum(rul_weights[i] for i in s))[0]
             for rn in problem)

def planB(problem, debug=False):
    r'''Take set of least weight, weight = 1/count across all sets - dups in rn.

        >>> #     3/2      2 1/2    4          3 1/2
        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12,13}, {1,2,3,4})]
        >>> #     3 1/2           4/2
        >>> planB(p, True)
        'rul_weights' {1: 0.5, 2: 0.5, 3: 0.5, 4: 0.5, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 0.5, 11: 1, 12: 1, 13: 1}
        4
    '''
    rul_weights = {
      rul: 1/count
        for rul, count
         in collections.Counter(rul
                                  for rn in problem
                                    for rul in union_of_sets(rn))
                       .items()}
    if debug: oprint("rul_weights", rul_weights)
    return count_unique(
             sorted(rn, key=lambda s: sum(rul_weights[i] for i in s))[0]
             for rn in problem)

def planC(problem):
    r'''Take the smallest set, no weighting.

        >>> p = [({1,2,3,14}, {4,5,6}, {5,6,7,8,9,10}, {5,6,9,10,11}),
        ...      ({10,11,12,13}, {1,2,3,4})]
        >>> planC(p)
        8
    '''
    return count_unique(rn[0] for rn in problem)

def planD(problem, debug=False):
    r'''Rank pairs of rns by shared RULs, for each pair take best combination.

        >>> p = [({1,2,3}, {4,5,6}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12}, {1,2,3,4}),
        ...      ({1,2,3,5,6}, {4,5,6}, {5,6,7,8}, {1,2,10,11}),
        ...      ({1,5,10,11,12}, {7,6,3,4})]
        >>> planD(p, True)
        'overlaps' [(0, 2, 9), (2, 3, 8), (0, 3, 7), (1, 2, 6), (1, 3, 6), (0, 1, 5)]
        'gen_set' {4, 5, 6}
        'gen_set' {1, 5, 10, 11, 12}
        7
    '''
    combined_ruls = [union_of_sets(rn) for rn in problem]
    overlaps = sorted(((a_i, b_i, len(a.intersection(b)))
                         for (a_i, a), (b_i, b) \
                          in itertools.combinations(enumerate(combined_ruls),
                                                    2)),
                      key=operator.itemgetter(2),
                      reverse=True)
    if debug: oprint('overlaps', overlaps)
    def gen_sets():
        seen = set()
        not_seen = set()
        for a_i, b_i, overlap in overlaps:
            if overlap == 0:
                not_seen.add(a_i)
                not_seen.add(b_i)
            elif a_i not in seen and b_i not in seen:
                ans = min((a.union(b)
                           for a, b
                            in itertools.product(problem[a_i], problem[b_i])),
                          key=len)
                if debug: oprint('gen_set', ans)
                yield ans
                seen.add(a_i)
                seen.add(b_i)
            else:
                if a_i not in seen: not_seen.add(a_i)
                if b_i not in seen: not_seen.add(b_i)
        for i in not_seen.difference(seen):
            if debug: oprint('gen_set', problem[i][0])
            yield problem[i][0]

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

def planF(problem, debug=False):
    r'''Stepwise, picking rn with least smallest set.

        >>> p = [({1,2,3}, {4,5,6,7}, {5,6,7,8}, {5,6,9,10}),
        ...      ({10,11,12,13}, {1,2,3,4,5})]
        >>> planF(p, True)
        {1, 2, 3, 4, 5}
        5
    '''
    ans = stepwise(problem[:], pick_least)
    if debug: oprint(ans)
    return len(ans)

def planG(problem, debug=False):
    r'''Stepwise, picking rn with greatest smallest set.

        >>> p = [({1,2,3}, {4,5,6,7}, {5,6,7,8}, {5,6,10}),
        ...      ({10,11,12,13}, {1,2,3,4,5})]
        >>> planG(p, True)
        {5, 6, 10, 11, 12, 13}
        6
    '''
    ans = stepwise(problem[:], pick_greatest)
    if debug: oprint(ans)
    return len(ans)

def planH(problem, debug=False):
    r'''Stepwise, sorting rn ascending ahead of time.

        >>> p = [({1,2,3}, {4,5,6,7}, {5,6,7,8}, {5,6,10}),
        ...      ({10,11,12,13}, {1,2,3,4,5})]
        >>> planH(p, True)
        {1, 2, 3, 4, 5}
        5
    '''
    problem = sorted(problem, key=lambda rn: len(rn[0]))
    ans = stepwise(problem, pick_first)
    if debug: oprint(ans)
    return len(ans)

def planI(problem, debug=False):
    r'''Stepwise, sorting rn descending ahead of time.

        >>> p = [({1,2,3}, {4,5,6,7}, {5,6,7,8}, {5,6,10}),
        ...      ({10,11,12,13}, {1,2,3,4,5})]
        >>> planI(p, True)
        {5, 6, 10, 11, 12, 13}
        6
    '''
    problem = sorted(problem, key=lambda rn: len(rn[0]), reverse=True)
    ans = stepwise(problem, pick_first)
    if debug: oprint(ans)
    return len(ans)

def planJ(problem, debug=False):
    r'''Stepwise, sorting rn ascending ignoring dup RULs.

        >>> p = [({1,7,8}, {4,5,6,7}, {2,6,7,8}, {5,6,10,14}),
        ...      ({10,11,12,13}, {1,2,3,4})]
        >>> planJ(p, True)
        'stepwise got' 1 {1, 2, 3, 4}
        'stepwise got' 0 {1, 7, 8}
        {1, 2, 3, 4, 7, 8}
        6
    '''
    ans = stepwise(problem[:], pick_least_no_dups, debug)
    if debug: oprint(ans)
    return len(ans)

def planK(problem, debug=False):
    r'''Stepwise, sorting rn descending ignoring dup RULs.

        >>> p = [({1,7,8}, {4,5,6,7}, {2,3,6,7,8}, {5,6,10,14}),
        ...      ({10,11,12,13,14}, {1,2,3,4})]
        >>> planK(p, True)
        'stepwise got' 0 {1, 7, 8}
        'stepwise got' 0 {1, 2, 3, 4}
        {1, 2, 3, 4, 7, 8}
        6
    '''
    ans = stepwise(problem[:], pick_greatest_no_dups, debug)
    if debug: oprint(ans)
    return len(ans)

def planL(problem, debug=False):
    r'''Stepwise, random rn order.

        >>> p = [({1,2,3}, {4,5,6,7}, {5,6,7,8}, {5,6,10}),
        ...      ({10,11,12,13}, {1,2,3,4,5})]
        >>> planL(p, True)
        {1, 2, 3, 4, 5}
        5
        >>> p = [({10,11,12,13}, {1,2,3,4,5}),
        ...      ({1,2,3}, {4,5,6,7}, {5,6,7,8}, {5,6,10})]
        >>> planL(p, True)
        {5, 6, 10, 11, 12, 13}
        6
    '''
    ans = stepwise(problem[:], pick_first)
    if debug: oprint(ans)
    return len(ans)

def pick_smallest(rn, state):
    r'''Pick the smallest rn, not counting ruls in state.

        >>> oprint(pick_smallest(({1,2,3}, {4,5,6,7}), {4,5,6}))
        ({4, 5, 6, 7}, {7})
    '''
    return min(((ruls, ruls.difference(state)) for ruls in rn),
               key=lambda ruls_subset: len(ruls_subset[1]))

def stepwise(problem, rn_picker, debug=False):
    ans = frozenset()
    while problem:
        i, ruls = rn_picker(problem, ans)
        if debug: oprint('stepwise got', i, ruls)
        ans = ans.union(ruls)
        del problem[i]
    return ans

def pick_first(problem, state):
    r'''Pick the first rn.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9},)]
        >>> state = {4,5,6}
        >>> oprint(pick_first(p, state))
        (0, {4, 5, 6, 7})
    '''
    return 0, pick_smallest(problem[0], state)[0]

def pick_least(problem, state):
    r'''Pick the rn, with the smallest ruls -- not counting ruls in state.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9},)]
        >>> state = {4,5,6}
        >>> oprint(pick_least(p, state))
        (0, {4, 5, 6, 7})
    '''
    i, (ruls, subset) = min(gen_smallest(problem, state),
                            key=lambda i_ruls: len(i_ruls[1][1]))
    return i, ruls

def gen_smallest(problem, state):
    r'''Generate the smallest set of ruls for each rn.

    Also yields the problem index.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9},)]
        >>> state = {4,5,6}
        >>> for i, ruls in gen_smallest(p, state): oprint(i, ruls)
        0 ({4, 5, 6, 7}, {7})
        1 ({7, 8, 9}, {7, 8, 9})
    '''
    for i, rn in enumerate(problem):
        yield i, pick_smallest(rn, state)

def pick_greatest(problem, state):
    r'''Pick the rn, with the greatest smallest ruls.
    
    Not counting ruls in state.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9},)]
        >>> state = {4,5,6}
        >>> oprint(pick_greatest(p, state))
        (1, {7, 8, 9})
    '''
    i, (ruls, subset) = max(gen_smallest(problem, state),
                            key=lambda i_ruls: len(i_ruls[1][1]))
    return i, ruls

def pick_least_no_dups(problem, state, debug=False):
    r'''Pick the rn, with the smallest ruls.
    
    Not counting ruls in state or in remaining problems.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9,10},)]
        >>> state = {4,5}
        >>> oprint(pick_least_no_dups(p, state, True))
        0 ({4, 5, 6, 7}, {6})
        1 ({7, 8, 9, 10}, {8, 9, 10})
        (0, {4, 5, 6, 7})
    '''
    i, (ruls, subset) = min(gen_smallest_no_dups(problem, state, debug),
                            key=lambda i_ruls: len(i_ruls[1][1]))
    return i, ruls

def pick_greatest_no_dups(problem, state, debug=False):
    r'''Pick the rn, with the greatest smallest ruls.

    Not counting ruls in state or in remaining problems.

        >>> p = [({1,2,3}, {4,5,6,7}), ({7,8,9,10},)]
        >>> state = {4,5}
        >>> oprint(pick_greatest_no_dups(p, state, True))
        0 ({4, 5, 6, 7}, {6})
        1 ({7, 8, 9, 10}, {8, 9, 10})
        (1, {7, 8, 9, 10})
    '''
    i, (ruls, subset) = max(gen_smallest_no_dups(problem, state, debug),
                            key=lambda i_ruls: len(i_ruls[1][1]))
    return i, ruls

def gen_smallest_no_dups(problem, state, debug=False):
    r'''Generates smallest ruls set with no dups with rest of problem.

    Also yields the problem index.

        >>> p = [({1,2,3}, {4,5,6,7,8}), ({7,8,9,10},)]
        >>> for i, ruls in gen_smallest_no_dups(p, {4}): oprint(i, ruls)
        0 ({4, 5, 6, 7, 8}, {5, 6})
        1 ({7, 8, 9, 10}, {9, 10})
    '''
    for i, rn in enumerate(problem):
        ans = pick_smallest_no_dups(rn, state, problem, i)
        if debug: oprint(i, ans)
        yield i, ans

def pick_smallest_no_dups(rn, state, problem, i_of_rn):
    r'''Pick the smallest rn, not counting ruls in state.

        >>> p = [({1,2,3}, {4,5,6,7,8}), ({7,8,9,10},)]
        >>> oprint(pick_smallest_no_dups(p[0], {4}, p, 0))
        ({4, 5, 6, 7, 8}, {5, 6})
    '''
    state_plus_rest = \
      state.union(union_of_sets(s for i, rn in enumerate(problem)
                                  if i != i_of_rn
                                  for s in rn))
    return pick_smallest(rn, state_plus_rest)

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

def oprint(*args, end='\n', sep=' '):
    r'''Ordered print.

        >>> oprint(('a', {7,8,9}))
        ('a', {7, 8, 9})
        >>> oprint(('a',))
        ('a',)
        >>> oprint({'b': 0.3333333333333, 'a': {7,8,9}})
        {'a': {7, 8, 9}, 'b': 0.333333}
    '''
    for i, arg in enumerate(args, start=1):
        if isinstance(arg, (frozenset, set)):
            print("{", end='')
            oprint(*sorted(arg), sep=', ', end='}')
        elif isinstance(arg, dict):
            print("{", end='')
            first = True
            for key in sorted(arg.keys()):
                if first: first = False
                else: print(', ', end='')
                oprint(key, end=': ')
                oprint(arg[key], end='')
            print("}", end='')
        elif isinstance(arg, tuple):
            print("(", end='')
            if len(arg) == 1:
                oprint(arg[0], end=',)')
            else:
                oprint(*arg, sep=', ', end=')')
        elif isinstance(arg, list):
            print("[", end='')
            oprint(*arg, sep=', ', end=']')
        elif isinstance(arg, float):
            print("%g" % arg, end='')
        else:
            print(repr(arg), end='')
        if i < len(args): print(end=sep)
    print(end=end)

def run_plans(num_rg, rn_avg, rn_sd, rul_avg, rul_sd, max_rul, n=1):
    r'''Run all plans against random input data and report results.

    The parameters for the final deciding run were:

        run_plans(50, 16, 5, 3, 2, 1000, 50)

    These were the results:

        2648(1.00) Stepwise, picking rn with least smallest set.
     ** 2650(1.00) Stepwise, sorting rn ascending ahead of time.
        2655(1.00) Stepwise, random rn order.
        2664(1.01) Stepwise, sorting rn descending ahead of time.
        2664(1.01) Stepwise, picking rn with greatest smallest set.
        2761(1.04) Rank pairs of rns by shared RULs, for each pair take best
                   combination.
        2785(1.05) Take the smallest set, no weighting.
        2820(1.06) Take set of least weight,
                   weight = 1/count across all sets - dups in rn.
        2827(1.07) Take set of least weight, weight = 1/count across all sets.
        2930(1.11) Stepwise, sorting rn descending ignoring dup RULs.
        2952(1.11) Stepwise, sorting rn ascending ignoring dup RULs.

    The one with the asterisks is the selected one!
    '''
    results = {fn: 0 for fn in (planA, planB, planC, planD,
                                #planE,
                                planF, planG, planH, planI, planJ, planK, planL,
                                # best_combination,
                               )}
    for _ in range(n):
        p = gen_problem(num_rg, rn_avg, rn_sd, rul_avg, rul_sd, max_rul)
        for fn in results.keys():
            results[fn] += fn(p)

    first = None
    for fn, n in sorted(results.items(), key=operator.itemgetter(1)):
        if n:
            if first is None: first = n
            print("%3d(%.2f)" % (n, n/first), fn.__doc__.split('\n')[0].strip())

