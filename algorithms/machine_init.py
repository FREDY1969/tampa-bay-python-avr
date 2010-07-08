# machine_init.py


import itertools

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

from ucc.database import crud

def init():
    db_conn = crud.db_connection('avr.db')
    try:
        # insert 0's for m=0:

        db_conn.execute("""
          insert into worst (N, C, m, value)
            select N.id, C.id, 0, 0 from reg_class N cross join reg_class C
        """)

        db_conn.commit()

        registers = db_conn.read_column('register', 'name')
        aliases = {}
        for R in registers:
            aliases[R] = frozenset(db_conn.read_column('alias', 'r2', r1=R))

        reg_classes = db_conn.read_column('reg_class', 'id')
        regs_in_class = {}
        for C in reg_classes:
            regs_in_class[C] = \
              frozenset(db_conn.read_column('reg_in_class', 'reg', reg_class=C))
        print('reg_classes', reg_classes)

        for N in reg_classes:
            print('N', N)
            N_regs = regs_in_class[N]
            for C in reg_classes:
                C_regs = regs_in_class[C]
                print('C', C, C_regs)

                # {set of S: set of registers}
                worsts0 = {frozenset(): frozenset()}

                for m in range(1, len(C_regs) + 1):
                    print('m', m)
                    worsts1 = {}
                    for R in C_regs:
                        for S0, regs in worsts0.items():
                            if R not in S0:
                                worsts1[S0.union((R,))] = \
                                    regs.union(aliases[R]).intersection(N_regs)
                    db_conn.insert('worst', N=N, C=C, m=m,
                                   value=max(len(regs)
                                             for regs in worsts1.values()))
                    worsts0 = worsts1
            db_conn.commit()
        worst0 = worst1 = None
    except:
        db_conn.rollback()
        raise
    finally:
        db_conn.close()

def class_compares():
    db_conn = crud.db_connection('avr.db')
    try:
        reg_classes = db_conn.read_column('reg_class', 'id')
        aliases = {}
        for C in reg_classes:
            aliases[C] = \
              frozenset(db_conn.read_column('class_alias', 'reg', reg_class=C))

        for C1, C2 in itertools.combinations(reg_classes, 2):
            if aliases[C1] == aliases[C2]:
                print(C1, 'alias-equivalent', C2)
            elif aliases[C1].issubset(aliases[C2]):
                print(C1, 'alias-contained in', C2)
            elif aliases[C2].issubset(aliases[C1]):
                print(C2, 'alias-contained in', C1)
            elif not aliases[C1].isdisjoint(aliases[C2]):
                print(C1, '*** UNKNOWN ***', C2)

    finally:
        db_conn.close()

