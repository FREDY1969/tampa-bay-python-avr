# populate_register_groups.py

r'''Creates the register_groups and assigns registers to each of them.

The only function called here from outside is attempt_register_allocation
(called from alloc_reg in ucc/codegen/reg_alloc.py).
'''

import sys   # for debug traces
import itertools
import collections
import operator

from ucc.database import crud
from ucc.codegen import assign_registers, stack_register_groups

def attempt_register_allocation(attempt_number):
    r'''This assigns the actual registers to each register_group.

    If this is not possible, it will break reg_use_linkages (spill) to try to
    make it work.  But these changes ripple throughout the algorithm, so after
    breaking reg_use_linkages, this function needs to be called again to take
    a fresh look at things.

    Note the reg_use_linkages are never restored after being broken (except
    for those broken by eliminate_conflicts).

    It returns True if successful, False if it needs to be re-run.
    '''

    # Each register group represents a set of linked reg_uses.  The goal will
    # be to assign a register to each register_group.
    num_register_groups = populate_register_group(attempt_number)

    # Split register_groups that include conflicting reg_uses.  A conflict
    # could be due to incompatible register classes, or two reg_uses for the
    # same kind and ref_id.
    num_register_groups += eliminate_conflicts(attempt_number)

    # Sets the reg_class and num_registers in each register_group.
    set_reg_classes(attempt_number)

    populate_rg_neighbors(attempt_number)

    stack_register_groups.initialize_rawZ_and_Z(attempt_number)

    max_stacking_order = stack_register_groups.stack_register_groups(
                           attempt_number,
                           num_register_groups)

    return assign_registers.assign_registers(attempt_number, max_stacking_order)

def populate_register_group(attempt_number):
    r'''Populate the register_group table.

    This table has one row per set of linked reg_uses.

    This function can be called repeatedly with different attempt_numbers.
    Each time it starts over scratch, but it observes the 'broken' flag in the
    reg_use_linkage; which may lead to different results.
    '''

    with crud.db_transaction():
        # Set all broken -1's back to 0 for now.  These will be
        # recalculated later by eliminate_conflicts.  Leave other broken
        # values unchanged (these were set due to graph coloring conflicts on
        # a prior pass).
        crud.update('reg_use_linkage', {'broken': -1}, broken=0)

    with crud.db_transaction():
        # Gather reg_uses into shared sets based on reg_use_linkage:
        ru_to_set = {}          # {ru_id: set_id}
        set_to_rus = {}         # {set_id: {ru_id}}
        next_set_id = 0
        for ru1, ru2 in crud.read_as_tuples('reg_use_linkage',
                                            'reg_use_1', 'reg_use_2',
                                            broken=0):
            if ru1 in ru_to_set:
                if ru2 in ru_to_set:
                    ru1_set = ru_to_set[ru1]
                    ru2_set = ru_to_set[ru2]
                    if ru1_set != ru2_set:
                        # merge one set into the other
                        if len(set_to_rus[ru1_set]) < len(set_to_rus[ru2_set]):
                            # transfer ru1_set to ru2_set
                            for ru in set_to_rus[ru1_set]:
                                ru_to_set[ru] = ru2_set
                            set_to_rus[ru2_set].update(set_to_rus[ru1_set])
                            del set_to_rus[ru1_set]
                        else:
                            # transfer ru2_set to ru1_set
                            for ru in set_to_rus[ru2_set]:
                                ru_to_set[ru] = ru1_set
                            set_to_rus[ru1_set].update(set_to_rus[ru2_set])
                            del set_to_rus[ru2_set]
                else:
                    # add ru2 to ru1 set
                    ru_to_set[ru2] = ru_to_set[ru1]
                    set_to_rus[ru_to_set[ru1]].add(ru2)
            else:
                # ru1 not in ru_to_set
                if ru2 in ru_to_set:
                    # add ru1 to ru2 set
                    ru_to_set[ru1] = ru_to_set[ru2]
                    set_to_rus[ru_to_set[ru2]].add(ru1)
                else:
                    # create new set
                    set_to_rus[next_set_id] = {ru1, ru2}
                    ru_to_set[ru1] = ru_to_set[ru2] = next_set_id
                    next_set_id += 1

        # Make sure that all ru_ids are accounted for:
        for ru_id in crud.read_column('reg_use', 'id'):
            if ru_id not in ru_to_set:
                # create new set just for ru_id
                set_to_rus[next_set_id] = {ru_id}
                ru_to_set[ru_id] = next_set_id
                next_set_id += 1

        # Create register_groups
        for ru_ids in set_to_rus.values():
            rg_id = crud.insert('register_group', attempt_number=attempt_number)
            crud.execute('''
                update reg_use
                   set reg_group_id = ?
                 where id in ({})
              '''.format(','.join(('?',)*len(ru_ids)),),
              (rg_id,) + tuple(ru_ids))

        print("created", len(set_to_rus), "register_groups",
              file = sys.stderr)
    return len(set_to_rus)

def eliminate_conflicts(attempt_number):
    r'''Eliminate conflicts between reg_uses in the same register_group.

    The two causes of conflict are incompatible register classes, and two
    reg_uses for the same kind and ref_id.

    This function sets the 'broken' flag in affected reg_use_linkages to -1.
    If no other function uses -1 for the broken value, this function can
    be re-run.
    '''
    with crud.db_transaction():
        # all links as two-tuples
        links1 = tuple(crud.read_as_tuples('reg_use_linkage',
                                           'reg_use_1', 'reg_use_2',
                                           broken=0))
        # include reverse links, and sort by first id
        links = sorted(itertools.chain(links1, ((b, a) for a, b in links1)))

        # {id: {neighbor_id: link_count}} based on links
        neighbors = dict((use, collections.Counter(u[1] for u in uses))
                         for use, uses
                          in itertools.groupby(links,
                                               key=operator.itemgetter(0)))
        #print("neighbors", neighbors, file=sys.stderr)

        # reg_group_id, id1, id2 of all conflicts (id1 < id2).
        # sorted by reg_group_id.
        it = crud.fetchall('''
                 select ru1.reg_group_id, ru1.id as id1, ru2.id as id2
                   from reg_use ru1
                        inner join reg_use ru2
                          on ru1.reg_group_id = ru2.reg_group_id
                          and ru1.id < ru2.id
                  where ru1.initial_reg_class notnull
                    and ru2.initial_reg_class notnull
                    and not exists (select null
                                      from reg_class_subsets
                                     where rc1 = ru1.initial_reg_class
                                       and rc2 = ru2.initial_reg_class)
                     or ru1.kind = ru2.kind
                    and ru1.ref_id = ru2.ref_id
                  order by ru1.reg_group_id
               ''', ctor_factory=crud.row.factory_from_cur)

        # split conflicts within each reg_group_id, this will replace the
        # register_group with conflicting reg_uses with a set of
        # register_groups with non-conflicting reg_uses.
        num_new_register_groups = 0
        for reg_group_id, conflicts \
         in itertools.groupby(it, operator.attrgetter('reg_group_id')):

            # only for print ..., comment out with print
            conflicts = tuple(conflicts)
            print("reg_group_id", reg_group_id, "conflicts", conflicts,
                  file=sys.stderr)

            # split yields groups of non-conflicting ru_ids
            for ru_ids in split(conflicts, neighbors):
                # create new register_group (let sqlite assign reg_group_id)
                ru_qmarks = ', '.join(('?',) * len(ru_ids))
                new_group_id = crud.execute('''
                    insert into register_group
                           (attempt_number, reg_class, num_registers)
                    select ?, aggr_rc_subset(initial_reg_class),
                           aggr_num_regs(num_registers)
                      from reg_use
                     where id in ({})
                  '''.format(ru_qmarks),
                  [attempt_number] + ru_ids)[1]
                print("new_group_id", new_group_id, file=sys.stderr)
                num_new_register_groups += 1

                # update reg_group_id to new_group_id in all ru_ids
                crud.execute('''
                    update reg_use
                       set reg_group_id = ?
                     where id in ({})
                  '''.format(ru_qmarks),
                  (new_group_id,) + ru_ids)

            # delete old register_group
            crud.delete('register_group', id=reg_group_id)
            num_new_register_groups -= 1

        # set broken flag on all reg_use_linkages for reg_uses now in
        # different register_groups.
        crud.execute('''
            update reg_use_linkage
               set broken = -1
             where not broken
               and (select ru1.reg_group_id != ru2.reg_group_id
                      from reg_use ru1, reg_use ru2
                     where ru1.id = reg_use_linkage.reg_use_1
                       and ru2.id = reg_use_linkage.reg_use_2)
         ''')

        # set reg_group_id in all reg_use_linkages to reg_use_1.reg_group_id.
        crud.execute('''
            update reg_use_linkage
               set reg_group_id = (select reg_group_id
                                     from reg_use ru
                                    where ru.id = reg_use_linkage.reg_use_1)
             where not broken
         ''')
    return num_new_register_groups

def set_reg_classes(attempt_number):
    r'''Sets the reg_class and num_registers in each register_group.
    '''
    with crud.db_transaction():
        crud.execute('''
            update register_group
               set reg_class = (select aggr_rc_subset(initial_reg_class)
                                  from reg_use ru1
                                 where ru1.reg_group_id = register_group.id),
                   num_registers = (select aggr_num_regs(num_registers)
                                      from reg_use ru2
                                     where ru2.reg_group_id = register_group.id)
             where attempt_number = ?
         ''', (attempt_number,))

def split(conflicts, neighbors):
    r'''Yields disjoint sets of ru_ids containing no conflicts between them.

        'conflicts' is a sequence of objects with 'id1' and 'id2' attributes.
        'neighbors' shows all ru_id linkage as {id: {neighbor_id: link_count}}

        >>> class conflict:
        ...     def __init__(self, id1, id2):
        ...         self.id1, self.id2 = id1, id2
        ...     def __repr__(self):
        ...         return "conflict({}, {})".format(self.id1, self.id2)
        >>> def pp(it):
        ...     return sorted(sorted(x) for x in it)
        >>> pp(split((conflict(1, 2), conflict(1, 3),
        ...           conflict(2, 4), conflict(3, 4)),
        ...          {}))
        [[1, 4], [2, 3]]
        >>> pp(split((conflict(1, 2), conflict(3, 4)),
        ...          {1: {2:1, 3:1, 4:0}, 2: {1:1, 3:0, 4:1},
        ...           3: {1:1, 2:0, 4:1}, 4: {1:0, 2:1, 3:1}}))
        [[1, 3], [2, 4]]
        >>> pp(split((conflict(1, 2), conflict(1, 3), conflict(1, 4),
        ...           conflict(1, 5), conflict(2, 3), conflict(2, 5),
        ...           conflict(3, 4), conflict(4, 5)),
        ...          {}))
        [[1], [2, 4], [3, 5]]
        >>> pp(split((conflict(1, 2), conflict(1, 3), conflict(1, 4),
        ...           conflict(1, 5), conflict(2, 3), conflict(2, 5),
        ...           conflict(3, 4)),
        ...          {}))
        [[1], [2, 4], [3, 5]]
        >>> pp(split((conflict(1, 2),),
        ...          {1: {2:1, 3:1, 4:0}, 2: {1:1, 3:0, 4:1},
        ...           3: {1:1, 2:0, 4:1}, 4: {1:0, 2:1, 3:1}}))
        [[1, 3], [2, 4]]
    '''

    # d1 = {ru_id: {conflicting_ru_id}}
    d1 = collections.defaultdict(set)
    for c in conflicts:
        d1[c.id1].add(c.id2)
        d1[c.id2].add(c.id1)

    def pick_color(colors, id):
        r'''Pick the best color from colors for id.

        Picks the color assigned to the greatest number of links to id.
        '''
        if len(colors) == 1: return colors.pop()
        n = neighbors.get(id, collections.Counter())
        return max(((c, sum(n[id] for id in ids_by_color[c])) for c in colors),
                   key=lambda t: t[1])[0]

    # colors are numbered starting at 1
    colors = {}                         # {id: color}
    ids_by_color = {}                   # {color: {id}}
    num_colors = 0

    # stack conflicting ru_ids, picking the one with the least conflicts each
    # time.
    stack = collections.deque()         # [(id, {conflicting_ru_id})]
    while d1:
        k, v = item = min(d1.items(), key=lambda item: len(item[1]))
        stack.appendleft(item)
        del d1[k]
        for x in v: d1[x].remove(k)

    # assign colors
    for k, v in stack:
        #print("split: unstacking", k, v, file=sys.stderr)
        ok_colors = ids_by_color.keys() - (colors[id] for id in v)
        if ok_colors:
            color = pick_color(ok_colors, k)
        else:
            num_colors += 1
            color = num_colors
            ids_by_color[color] = set()
        colors[k] = color
        ids_by_color[color].add(k)

    print("split: stack is", tuple(stack), file=sys.stderr)
    print("split: ids_by_color", ids_by_color, file=sys.stderr)

    def pick_best_color(id):
        neighbor_ids = neighbors[id]
        color, colored_sum = max(((c, sum(neighbor_ids[nid] for nid in ids))
                                  for c, ids in ids_by_color.items()),
                                 key=operator.itemgetter(1))
        uncolored_sum = sum(neighbor_ids[nid]
                            for nid in neighbor_ids.keys() - colors.keys())
        return color, colored_sum, uncolored_sum

    nonconflicting_ids = neighbors.keys() - colors.keys()
    while nonconflicting_ids:
        # pick the next_id and color to assign with the greatest number of
        # neighbors with that color.  If a tie, pick the one with the greatest
        # number of uncolored neighbors.
        next_id, (color, colored_sum, uncolored_sum) = \
            max(((id, pick_best_color(id)) for id in nonconflicting_ids),
                key=lambda t: t[1][1:2])

        if not colored_sum: color = 1
        colors[next_id] = color
        ids_by_color[color].add(next_id)
        nonconflicting_ids.remove(next_id)

    return ids_by_color.values()

def populate_rg_neighbors(attempt_number):
    r'''Populates rg_neighbors.

    First populates overlaps, then uses this for rg_neighbors.

    This function can be run multiple times with different attempt_numbers.
    '''

    with crud.db_transaction():
        # Figure out overlaps between reg_use_linkages and reg_uses in other
        # register_groups.  These go in the overlaps table.
        crud.execute('''
            insert into overlaps (attempt_number, linkage_id, reg_use_id)
            select ?, rul.id, ru3.id
              from reg_use_linkage rul
                   inner join reg_use ru1
                     on ru1.id = reg_use_1
                   inner join reg_use ru2
                     on ru2.id = reg_use_2
                     and ru1.block_id = ru2.block_id
                   inner join reg_use ru3
                     on ru1.block_id = ru3.block_id
                     and ru1.abs_order_in_block <= ru3.abs_order_in_block
                     and ru2.abs_order_in_block >= ru3.abs_order_in_block
             where ru1.block_id notnull
               and ru1.abs_order_in_block notnull
               and ru2.block_id notnull
               and ru2.abs_order_in_block notnull
               and ru3.block_id notnull
               and ru3.abs_order_in_block notnull
               and not rul.broken
               and ru3.reg_group_id != ru1.reg_group_id
          ''', (attempt_number,))

        # Figure out rg_neighbors.  These are the conflicting register_groups.
        crud.execute('''
            insert into rg_neighbors (attempt_number, rg1, rg2)
            select distinct ?, min(rul.reg_group_id, ru.reg_group_id),
                               max(rul.reg_group_id, ru.reg_group_id)
              from overlaps ov
                   inner join reg_use_linkage rul
                     on ov.linkage_id = rul.id
                   inner join reg_use ru
                     on ov.reg_use_id = ru.id
             where ov.attempt_number = ?
          ''', (attempt_number, attempt_number))

        # Link overlaps to rg_neighbors.
        crud.execute('''
            update overlaps
               set rg_neighbor_id = (
                   select rgn.id
                     from rg_neighbors rgn
                          inner join reg_use_linkage rul
                            on rul.reg_group_id in (rg1, rg2)
                          inner join reg_use ru
                            on ru.reg_group_id in (rg1, rg2)
                            and ru.reg_group_id != rul.reg_group_id
                    where rgn.attempt_number = ?
                      and overlaps.linkage_id = rul.id
                      and overlaps.reg_use_id = ru.id)
             where attempt_number = ?
          ''', (attempt_number, attempt_number))

""" DO WE STILL NEED THIS STUFF?
#def create_reg_map(subsets, sizes, code_seqs):
#    for next_fn_layer in get_functions():
#        for symbol_id in next_fn_layer:
#            reg_map = reg_map_for_fun(symbol_id, subsets, sizes, code_seqs)
#            write_reg_map(reg_map)
#        # FIX: What needs to happen between fn layers?

def get_functions():
    r'''Yields sets of functions in a bottom-up order.

    Each set is all of the functions that don't call any functions not yet
    yielded.

    Each function in the set is simply its symbol_id.
    '''
    fns = set()
    calls = collections.defaultdict(set)
    called_by = collections.defaultdict(set)
    for caller_id, called_id \
     in crud.read_as_tuples('fn_calls', 'caller_id', 'called_id', depth=1):
        fns.add(called_id)
        fns.add(caller_id)
        calls[caller_id].add(called_id)
        called_by[called_id].add(caller_id)
    while fns:
        bottom = fns - calls.keys()
        yield bottom
        fns -= bottom
        for fn in bottom:
            for caller in called_by[fn]:
                calls[caller].remove(fn)
                if not calls[caller]: del calls[caller]

def reg_map_for_fun(symbol_id, subsets, sizes, code_seqs):
    fn_name, kind, suspends = crud.read1_as_tuple('symbol_table',
                                                  'label', 'kind', 'suspends',
                                                  id=symbol_id)
    locals = gather_locals(symbol_id, subsets, sizes)

    #print(fn_name, "locals", locals, file=sys.stderr)

    temp_map = map_temporaries(symbol_id, locals, kind, suspends, sizes)

    # FIX: figure out reg_map for fn and return it!


def gather_locals(fn_symbol_id, subsets, sizes):
    r'''Returns {symbol_id: (reg_class, num_regs, use_count, total_definitions)}
    '''

    params = frozenset(crud.read_column('symbol_table', 'id',
                                        context=fn_symbol_id,
                                        kind='parameter'))

    it = crud.fetchall('''
             select u.symbol_id, u.reg_class,
                    count(*), max(u.num_regs), sum(definition)
               from blocks b
                      inner join (  select t.block_id, t.symbol_id,
                                           0 as definition,
                                           needed_reg_class as reg_class,
                                           num_needed_regs as num_regs
                                      from triples t
                                     where operator = 'local'
                                  union
                                    select t2.block_id, tl.symbol_id, 1,
                                           t2.reg_class, t2.num_regs_output
                                      from triples t2
                                             inner join triple_labels tl
                                               on t2.id = tl.triple_id
                                             inner join symbol_table st
                                               on tl.symbol_id = st.id
                                               and st.context = ?
                                 ) u
                        on b.id = u.block_id
              where b.word_symbol_id = ?
              group by u.symbol_id, u.reg_class
              order by u.symbol_id
       ''', (fn_symbol_id, fn_symbol_id))

    ans = {}  # {symbol_id: (reg_class, num_regs, use_count, total_definitions)}

    #print('sizes', sizes, file=sys.stderr)

    for id, reg_iter in itertools.groupby(it, lambda t: t[0]):
        reg_classes = collections.defaultdict(int)  # {rc: num_uses}
        max_regs = 0
        total_definitions = 0
        saved_reg_iter = tuple(info for info in reg_iter if info[1] is not None)
        for _, reg_class, count, max_needed, definitions in saved_reg_iter:
            reg_classes[reg_class] = count
            if max_needed > max_regs: max_regs = max_needed
            total_definitions += definitions
        for (_, rc1, count1, _, _), (_, rc2, count2, _, _) \
         in itertools.combinations(saved_reg_iter, 2):
            sub_rc = subsets.get((rc1, rc2))
            if sub_rc is not None:
                if sub_rc != rc1:
                    reg_classes[sub_rc] += count1
                if sub_rc != rc2:
                    reg_classes[sub_rc] += count2

        # Select max count:
        rc, count = sorted(reg_classes.items(),
                           key=lambda i: (i[1], sizes[i[0]]),
                           reverse=True) \
                      [0]
        if id in params: count += 1
        ans[id] = (rc, max_regs, count, total_definitions)
    return ans

def map_temporaries(fn_symbol_id, locals, kind, suspends, sizes):
    r'''Returns {symbol_id: (reg_class, num_regs, use_count, total_definitions)}
    '''
    rows = crud.fetchall('''
               select b.id block_id, t.id, t.abs_order_in_block,
                      t.needed_reg_class t_needed_reg_class,
                      t.num_needed_regs t_num_needed_regs,
                      t.reg_class t_reg_class,
                      t.num_regs_output t_num_regs_output,
                      tp.parent_id, tp.ghost, tp.parameter_num,
                      tp.reg_class_for_parent, tp.num_regs_for_parent,
                      tp.needed_reg_class tp_needed_reg_class,
                      tp.move_prior_to_needed, tp.move_needed_to_parent,
                      tp.move_needed_to_next,
                      rr.reg_class rr_reg_class, rr.num_needed rr_num_needed
                 from blocks b
                      inner join triples t
                        on b.id = t.block_id
                      left outer join triple_parameters tp
                        on t.id = tp.parameter_id
                      left outer join reg_requirements rr
                        on t.code_seq_id = rr.code_seq_id
                where b.word_symbol_id = ?
                order by b.id, t.id, tp.parent_id
             ''', (fn_symbol_id,), ctor_factory = crud.row.factory_from_cur)
    triples = {}  # {id: row}
    for id, tps in itertools.groupby(rows, lambda r: (r.block_id, r.id)):
        id = id[1]
        tps = iter(tps)
        first_row = next(tps)
        #print("first_row for triple", id, first_row, file=sys.stderr)
        #print("abs_order_in_block", first_row.abs_order_in_block,
        #      file=sys.stderr)
        if first_row.abs_order_in_block is not None:
            triples[id] = first_row
            triples[id].tps = []
            for parent_id, rrs \
             in itertools.groupby(itertools.chain((first_row,), tps),
                                  lambda r: r.parent_id):
                rrs = iter(rrs)
                first_row = next(rrs)
                if first_row.parent_id is not None:
                    triples[id].tps.append(first_row)
                triples[id].rrs = {row.rr_reg_class: row.rr_num_needed
                                   for row in itertools.chain((first_row,), rrs)
                                   if row.rr_reg_class is not None}

    ordered_triples = sorted(triples.values(),
                             key=lambda r: (r.block_id, r.abs_order_in_block))
    for t in ordered_triples:
        for tp in t.tps:
            tp.parent = triples[tp.parent_id]
        t.tps.sort(key=lambda tp: tp.parent.abs_order_in_block)
        #print("triple", t.block_id, t.id, t.abs_order_in_block, file=sys.stderr)
        #print("  rrs", t.rrs, file=sys.stderr)
        #for tp in t.tps:
        #    print("  tp", tp.parent.id, tp.parent_id,
        #          tp.parent.abs_order_in_block, tp.ghost, file=sys.stderr)

    #brains = reg_map.fn_reg_map(fn_symbol_id, subsets, sizes)
    #for t in ordered_triples:
    #    brains.alloc(...)

def write_reg_map(reg_map):
    # FIX: implement this!
    pass
"""
