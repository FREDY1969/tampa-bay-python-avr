# graph_coloring.py

r'''Generates random graphs and tries different graph coloring algorithms.
'''

import random
import collections
import functools
import itertools

Num_nodes = 9
Num_colors = 3

def gen_graph(num_nodes, min_links):
    r'''A graph is just a dict of links.
    
    {node: {node...}}
    '''
    # create the nodes:
    graph = dict((node, set()) for node in range(1, num_nodes + 1))
    changed = True
    while changed:
        changed = False
        for node, links in graph.items():
            while len(links) < min_links:
                d = random.randint(1, num_nodes)
                while d == node or d in links:
                    d = random.randint(1, num_nodes)
                links.add(d)
                graph[d].add(node)
                changed = True
    return graph

def stack_safe(stack, graph, num_colors):
    r'''Stacks safe nodes onto 'stack'.

        >>> stack = []
        >>> stack_safe(stack, {1: set((2,)), 2: set((1,3)), 3: set((2,4,5)),
        ...                    4: set((3,5)), 5: set((3,4))},
        ...            2)
        >>> stack
        [[1], [2]]
    '''
    while sum(map(len, stack)) < len(graph):
        safe_items = [node for node, links in graph.items()
                            if not node_in_stack(node, stack) and
                               count_links(stack, links) < num_colors]
        if not safe_items: break
        stack.append(safe_items)

def count_links(stack, links):
    r'''Returns the number of links not in stack.

        >>> count_links([[1],[2,3]], set((1,2,3,4,5)))
        2
    '''
    return len(links.difference(itertools.chain.from_iterable(stack)))

def node_in_stack(node, stack):
    r'''Returns bool.

        >>> node_in_stack(1, [[1],[2,3]])
        True
        >>> node_in_stack(3, [[1],[2,3]])
        True
        >>> node_in_stack(4, [[1],[2,3]])
        False
    '''
    return any(map(lambda nodes: node in nodes, stack))

def stack_one(selector_fn, stack, graph):
    stack.append([selector_fn(((count_links(stack, links), node)
                               for node, links in graph.items()
                                if not node_in_stack(node, stack)))[1]])

def stack_random(stack, graph):
    stack.append([random.choice(
                    tuple(node for node in graph
                                if not node_in_stack(node, stack)))])

def stack_graph(graph, num_colors, stack_one_fn):
    r'''Stacks the graph using stack_one_fn to stack one unsafe node.

    Returns the resulting stack.

        >>> stack_graph({1: set((2,)), 2: set((1,3)), 3: set((2,4,5)),
        ...              4: set((3,5)), 5: set((3,4))},
        ...             2, functools.partial(stack_one, min))
        [[1], [2], [3], [4, 5]]
    '''
    stack = []
    stack_safe(stack, graph, num_colors)
    while sum(map(len, stack)) < len(graph):
        stack_one_fn(stack, graph)
        stack_safe(stack, graph, num_colors)
    return stack

def color(graph, stack, num_colors, color_picker):
    r'''Unwinds stack to color the graph.

    Returns the number of spills needed.

        >>> color({1: set((2,)), 2: set((1,3)), 3: set((2,4,5)), 4: set((3,5)),
        ...        5: set((3,4))},
        ...       [[1],[2],[3],[4,5]],
        ...       2, pick_min_color)
        1
        >>> color({1: set((2,)), 2: set((1,3)), 3: set((2,4,5)), 4: set((3,5)),
        ...        5: set((3,4))},
        ...       [[1],[2],[3],[4,5]],
        ...       2, pick_dup_color)
        1
    '''
    spills = 0
    all_colors = frozenset(range(1, num_colors + 1))
    colors = {}         # {node: color}
    for nodes in stack[::-1]:
        for node in nodes:
            try:
                selected_color = color_picker(node, graph, colors, all_colors)
                #print("assigned", selected_color, "to node", node)
                colors[node] = selected_color
            except ValueError:
                #print("spilled node", node)
                spills += 1
    return spills

def pick_min_color(node, graph, colors, all_colors):
    return min(all_colors.difference(colors[link] for link in graph[node]
                                                   if link in colors))

def pick_dup_color(node, graph, colors, all_colors):
    available_colors = all_colors.difference(colors[link]
                                               for link in graph[node]
                                                if link in colors)
    for color, _ in collections.Counter(color
                      for link in graph[node] if link not in colors
                        for color in frozenset(colors[link_link]
                                               for link_link in graph[link]
                                                if link_link in
                                                colors)) \
                    .most_common():
        if color in available_colors:
            return color
    return min(available_colors)

def color_graph(graph, num_colors, stack_one_fn):
    stack = stack_graph(graph, num_colors, stack_one_fn)
    return color(graph, stack, num_colors, pick_min_color), \
           color(graph, stack, num_colors, pick_dup_color)

def least_spills(graph, num_colors):
    best_min = 100000000
    best_dup = 100000000
    for nodes in itertools.permutations(range(1, len(graph) + 1)):
        spills_min = \
          color(graph, [[node] for node in nodes], num_colors, pick_min_color)
        if spills_min < best_min: best_min = spills_min
        spills_dup = \
          color(graph, [[node] for node in nodes], num_colors, pick_dup_color)
        if spills_dup < best_dup: best_dup = spills_dup
    return best_min, best_dup

def do_tests(num_nodes, min_links, num_colors, num_tests):
    min_spills = [0, 0]
    max_spills = [0, 0]
    random_spills = [0, 0]
    lowest_spills = [0, 0]
    for i in range(num_tests):
        graph = gen_graph(num_nodes, min_links)

        min_min, min_dup = color_graph(graph, num_colors,
                                       functools.partial(stack_one, min))
        min_spills[0] += min_min
        min_spills[1] += min_dup

        max_min, max_dup = color_graph(graph, num_colors,
                                       functools.partial(stack_one, max))
        max_spills[0] += max_min
        max_spills[1] += max_dup

        random_min, random_dup = color_graph(graph, num_colors, stack_random)
        random_spills[0] += random_min
        random_spills[1] += random_dup

        lowest_min, lowest_dup = least_spills(graph, num_colors)
        lowest_spills[0] += lowest_min
        lowest_spills[1] += lowest_dup
    print("total min spills", min_spills)
    print("total max spills", max_spills)
    print("total random spills", random_spills)
    print("total least spills", lowest_spills)
