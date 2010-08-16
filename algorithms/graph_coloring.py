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

def color(graph, stack, num_colors, color_picker):
    r'''Unwinds stack to color the graph.

    Returns the number of spills needed.

        >>> color({1: set((2,)), 2: set((1,3)), 3: set((2,4,5)), 4: set((3,5)),
        ...        5: set((3,4))},
        ...       [[1],[2],[3],[4,5]],
        ...       2, pick_min_color)
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

def color_graph(graph, num_colors, stack_one_fn, color_picker):
    stack = stack_graph(graph, num_colors, stack_one_fn)
    return color(graph, stack, num_colors, color_picker)

def least_spills(graph, num_colors, color_picker):
    best_score = 100000000
    for nodes in itertools.permutations(range(1, len(graph) + 1)):
        spills = \
          color(graph, [[node] for node in nodes], num_colors, color_picker)
        if spills < best_score: best_score = spills
    return best_score

def do_tests(num_nodes, min_links, num_colors, num_tests):
    min_spills = 0
    max_spills = 0
    random_spills = 0
    lowest_spills = 0
    for i in xrange(num_tests):
        graph = gen_graph(num_nodes, min_links)
        min_spills += color_graph(graph, num_colors,
                                  functools.partial(stack_one, min),
                                  pick_min_color)
        max_spills += color_graph(graph, num_colors,
                                  functools.partial(stack_one, max),
                                  pick_min_color)
        random_spills += color_graph(graph, num_colors, stack_random,
                                     pick_min_color)
        lowest_spills += least_spills(graph, num_colors, pick_min_color)
    print("total min spills", min_spills)
    print("total max spills", max_spills)
    print("total random spills", random_spills)
    print("total least spills", lowest_spills)
