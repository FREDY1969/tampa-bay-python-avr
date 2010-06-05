# spill_perms.py

import itertools

def gen1(uses = 'ABCD'):
    r'''Generate all permutations of starts and stops for uses.

    Starts are uppercase and stops are lowercase.

        >>> for t in gen1('A'): print(t)
        ('A', 'a')
        ('a', 'A')

        >>> for t in itertools.islice(gen1('AB'), 6): print(t)
        ('A', 'B', 'a', 'b')
        ('A', 'B', 'b', 'a')
        ('A', 'a', 'B', 'b')
        ('A', 'a', 'b', 'B')
        ('A', 'b', 'B', 'a')
        ('A', 'b', 'a', 'B')
    '''
    return itertools.permutations(uses.upper() + uses.lower(), 2 * len(uses))

def bad_start_stop(t):
    r'''True if there is a reversed start/stop in t.

        >>> bad_start_stop('ABCDabcd')
        False
        >>> bad_start_stop('ABCbcDda')
        False
        >>> bad_start_stop('ABCbcdDa')
        True
    '''
    seen = set()
    for x in t:
        if x.isupper(): seen.add(x)
        elif x.upper() not in seen:
            return True
    return False

def starts_not_ordered(t):
    r'''True if the starts are not in sequence.

        >>> starts_not_ordered('AaBbCc')
        False
        >>> starts_not_ordered('AaCcBb')
        True
    '''
    last_start = ' '
    for x in t:
        if x.isupper():
            if x < last_start: return True
            last_start = x
    return False

def gen2(filter_fns = (bad_start_stop, starts_not_ordered), uses = 'ABCD'):
    r'''Like gen1, but each start preceeds its stop.

        >>> for t in gen2((bad_start_stop,), 'AB'): print(t)
        ('A', 'B', 'a', 'b')
        ('A', 'B', 'b', 'a')
        ('A', 'a', 'B', 'b')
        ('B', 'A', 'a', 'b')
        ('B', 'A', 'b', 'a')
        ('B', 'b', 'A', 'a')

        >>> for t in gen2((starts_not_ordered,), 'AB'): print(t)
        ('A', 'B', 'a', 'b')
        ('A', 'B', 'b', 'a')
        ('A', 'a', 'B', 'b')
        ('A', 'a', 'b', 'B')
        ('A', 'b', 'B', 'a')
        ('A', 'b', 'a', 'B')
        ('a', 'A', 'B', 'b')
        ('a', 'A', 'b', 'B')
        ('a', 'b', 'A', 'B')
        ('b', 'A', 'B', 'a')
        ('b', 'A', 'a', 'B')
        ('b', 'a', 'A', 'B')

        >>> for t in gen2(uses = 'AB'): print(t)
        ('A', 'B', 'a', 'b')
        ('A', 'B', 'b', 'a')
        ('A', 'a', 'B', 'b')
    '''
    return itertools.filterfalse(lambda t: any(map(lambda f: f(t), filter_fns)),
                                 gen1(uses))

def max_count(t):
    r'''Returns the max overlap between uses in t.

    Assumes not bad_start_stop(t).

        >>> max_count('ABCDabcd')
        4
        >>> max_count('AaBbCcDd')
        1
    '''
    max = 0
    count = 0
    for x in t:
        if x.isupper():
            count += 1
            if count > max: max = count
        else: count -= 1
    return max

def gen3(min_count = 3, uses = 'ABCD'):
    r'''Like gen2, but only max_counts >= min_count.

        >>> for t in gen3(uses = 'ABC'): print(t)
        ('A', 'B', 'C', 'a', 'b', 'c')
        ('A', 'B', 'C', 'a', 'c', 'b')
        ('A', 'B', 'C', 'b', 'a', 'c')
        ('A', 'B', 'C', 'b', 'c', 'a')
        ('A', 'B', 'C', 'c', 'a', 'b')
        ('A', 'B', 'C', 'c', 'b', 'a')
    '''
    return gen2((lambda t: max_count(t) < min_count, bad_start_stop,
                 starts_not_ordered),
                uses)

def initial_starts(t):
    r'''Returns the number of initial starts.

        >>> initial_starts('AaBb')
        1
        >>> initial_starts('ABab')
        2
    '''
    return count(itertools.takewhile(lambda x: x.isupper(), t))

def final_stops(t):
    r'''Returns the number of stops at the end of t.

        >>> final_stops('AaBb')
        1
        >>> final_stops('ABab')
        2
    '''
    return count(itertools.takewhile(lambda x: x.islower(), t[::-1]))

def gen4(min_count = 3, uses = 'ABCD'):
    r'''Like gen3, but excluding lone_starts and lone_ends.
    '''
    return itertools.filterfalse(lambda t: initial_starts(t) < min_count or
                                           final_stops(t) < min_count,
                                 gen3(min_count, uses))

def count(it):
    ans = 0
    for _ in it: ans += 1
    return ans
