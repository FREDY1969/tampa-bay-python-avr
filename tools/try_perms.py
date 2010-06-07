#!/usr/local/bin/python3.1

# try_perms.py

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

from ucc.codegen import reg_map, reg_class
from tools import spill_perms

def do_perm(p):
    r'''Run permutation p through the reg_map function.

        >>> do_perm(('A', 'B', 'C', 'c', 'b', 'a'))
        ('A', 'B', 'C', 'c', 'b', 'a')
    '''
    print(p)
    rm = reg_map.fn_reg_map(1)
    rc = reg_class.reg_class(1, 'rc', 1, 2)
    use_map = {}
    for x in p:
        if x.isupper():
            use_map[x] = reg_map.reg_use(rm, x, 1, rc)
        else:
            use_map[x.upper()].reference(1)
            use_map[x.upper()].free()
    if rm.uses[rc]:
        print("reg_map.uses not empty at end:", rm.uses[rc])
    if rm.use_count[rc] != 0:
        print("reg_map.use_count != 0 at end:", rm.use_count[rc])
    for ss in rm.spill_reqs.values():
        for s in ss: print(s, "cost", s.cost)
    for use in rm.reg_uses:
        print("use", use, use.assigned_rc, use.assigned_nums, end='')
        if use.spilled: print(" spilled")
        else: print()

def do_it(min_count = 3, uses = 'ABCD'):
    for p in tuple(spill_perms.gen4(min_count, uses))[::-1]:
        do_perm(p)

def usage():
    print("usage: try_perms.py [min_count [uses]]", file=sys.stderr)
    sys.exit(2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1: do_it()
    elif len(sys.argv) == 2: do_it(int(sys.argv[1]))
    elif len(sys.argv) == 3: do_it(int(sys.argv[1]), sys.argv[2])
    else:
        usage()

