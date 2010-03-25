# order_triples.py

Best_score = None

def best_seq(nodes, graph, accum_score):
    r'''Returns sequence of nodes requiring the least registers.

    Nodes is a set of triples.
    Graph is {predecessor node: set of successors}
        The sequence returned must conform to the predecessor-successor
        constraints of this graph.
    Accum_score is a score object.

    Returns None if it can't beat a previous Best_score.
    '''
    global Best_score
    if not nodes:
        Best_score = accum_score
        return ()
    constrained = set()
    for succ_set in graph.values():
        constrained += succ_set
    best_seq = None
    for next in sorted(nodes - constrained,
                       key=lambda node: len(node.reg_classes),
                       reverse=True):
        graph = graph.copy()
        del graph[next]
        nodes = nodes.difference((next,))
        next_score = accum_score.add(next)
        if Best_score and next_score < Best_score:
            for rest in topo(nodes, graph, next_score):
                if rest is not None:
                    best_seq = (next,) + rest
    return best_seq

class score:
    r'''Tracks register usage after executing a sequence of triples.

    This object can be used more than once, trying to add different nodes
    (triples) to the sequence.  So the object must be immutable.
    '''

    def __init__(self, class_map, discarded, map, dup_map, moves, use_counts):
        r'''

        registers are just numbers starting at 0.

        class_map is list of reg_class (class_map[reg] is reg_class for reg)
        discarded is set of reg
        map is {(node, node_reg): my_reg}
        dup_map is {(node, node_reg): [num]}
        '''
        self.class_map = class_map
        self.discarded = discarded
        self.map = map
        self.dup_map = dup_map
        self.moves = moves
        self.use_counts = use_counts

    def __lt__(self, b):
        return self.min_needed < b.min_needed

    def add(self, node):
        r'''Add node to this sequence of triples.

        Returns a new score representing the new sequence.  Self is unmodified.

        node is expected to have the following attributes:
          reg_classes is list of reg_class for all registers used by node.
                         output registers are always first.
          num_outputs is number of initial registers (starting at 0) that are
                         output.
          children is seq of (child, list of (reg_num, trashes_flag))
        '''
        return merge_node(node, self.class_map[:], self.discarded.copy(),
                          self.map.copy(), self.dup_map.copy(),
                          self.use_counts.copy())

def merge_node(node, new_class_map, new_discarded, new_map, new_dup_map,
               new_use_counts):
    r'''Merge node into new_* data structures and return new score object.
    '''

    new_moves = []      # list of (src_reg, dest_reg)

    # (node, node_reg_num, node_reg_class, [from_reg_num, [dup_regs]])
    get_regs = []

    # Merge node.children into the picture
    node_regs_seen = merge_children(node, new_class_map, new_discarded,
                                    new_map, new_dup_map, new_use_counts)

    # Map other node registers needed as discarded registers:
    for node_reg_num, node_reg_class in enumerate(node.reg_classes):
        if node_reg_num not in node_regs_seen:
            get_regs.append((node, node_reg_num, node_reg_class))
            #reg = get_reg(node_reg_class)
            #new_map[node, node_reg_num] = reg

    # Make sure node's outputs are not discarded!
    for node_reg_num in range(node.num_outputs):
        new_discarded.discard(new_map[node, node_reg_num])

    allocate_regs(get_regs, new_discarded, new_class_map, new_map, new_moves)

    return score(new_class_map, new_discarded, new_map, new_dup_map,
                 new_moves, new_use_counts)

def merge_children(node, new_class_map, new_discarded, new_map, new_dup_map,
                   new_use_counts):
    node_regs_seen = set()
    for child, child_output_regs in node.children:
        new_use_counts[child] -= 1
        last_use_of_child = new_use_counts[child] == 0
        for child_reg_num, (node_reg_num, trashes) \
         in enumerate(child_output_regs):
            node_regs_seen.add(node_reg_num)
            my_reg_num = new_map[child, child_reg_num]
            my_reg_class = new_class_map[my_reg_num]
            node_reg_class = node.reg_classes[node_reg_num]
            if trashes and not last_use_of_child:
                get_regs.append((node, node_reg_num, node_reg_class,
                                 my_reg_num))
                #dup_reg = get_reg(node_reg_class)
                #new_map[node, node_reg_num] = dup_reg
                #new_moves.append((my_reg_num, dup_reg))
            elif my_reg_class <= node_reg_class:
                new_map[node, node_reg_num] = my_reg_num
            elif node_reg_class <= my_reg_class:
                new_map[node, node_reg_num] = my_reg_num
                new_class_map[my_reg_num] = node_reg_class
            else:
                # We need a copy of the child's output in node_reg_class.
                found = False
                if (child, child_reg_num) in new_dup_map:
                    dup_regs = new_dup_map[child, child_reg_num]
                    for dup_reg in dup_regs:
                        dup_reg_class = new_class_map[dup_reg]
                        if dup_reg_class <= node_reg_class:
                            new_map[node, node_reg_num] = dup_reg
                            found = True
                            break
                        elif node_reg_class <= dup_reg_class:
                            new_map[node, node_reg_num] = dup_reg
                            new_class_map[dup_reg] = node_reg_class
                            found = True
                            break
                    if not found:
                        dup_regs = dup_regs[:]
                else:
                    dup_regs = []
                    new_dup_map[child, child_reg_num] = dup_regs
                if not found:
                    get_regs.append((node, node_reg_num, node_reg_class,
                                     my_reg_num, dup_regs))
                    #dup_reg = get_reg(node_reg_class)
                    #new_map[node, node_reg_num] = dup_reg
                    #dup_regs.append(dup_reg)
                    #new_moves.append((my_reg_num, dup_reg))
        if last_use_of_child:
            # Discard child output registers (and dups)
            for i in range(child.num_outputs):
                new_discarded.add(new_map[child, i])
                if (child, i) in new_dup_map:
                    for dup_reg in new_dup_map[child, i]:
                        new_discarded.add(dup_reg)
    return node_regs_seen

def allocate_regs(get_reg_list, new_discarded, new_class_map, new_map,
                  new_moves):
    r'''Get_reg_list is a list of registers needed.
    
    Process get_regs_list and merge results into other arguments.
    '''
    get_regs_list.sort(key=lambda t: t[2].tsort_index)
    for node, node_reg_num, node_reg_class, *rest in get_regs_list:
        ans = None
        ans_class = None
        for reg in new_discarded:
            reg_class = new_class_map[reg]
            if reg_class <= node_reg_class and \
               (not ans_class or reg_class > ans_class):
                ans = reg
                ans_class = reg_class
        if not ans_class:
            # Allocate new register
            # FIX: check register overflow!
            ans = len(new_class_map)
            new_discarded.add(ans)
            new_class_map.append(node_reg_class)
        new_map[node, node_reg_num] = ans
        if rest: 
            new_moves.append((rest[0], ans))
            if len(rest) > 1:
                rest[1].append(ans)

