
import collections

example1 = {
 'a': ('b', 'e'),
 'b': ('c', 'd'),
 'e': ('f',),
 'f': ('b',),
}

def dump(graph, root):
    '''
        >>> dump(example1, 'a')
        a
          b
            c
            d
          e
            f
              b*
    '''
    def dump_branch(n, indent = 0):
        if n in seen:
            print("{}{}*".format(' ' * indent, n))
        else:
            seen.add(n)
            print("{}{}".format(' ' * indent, n))
            for x in graph.get(n, ()): dump_branch(x, indent + 2)
    seen = set()
    dump_branch(root)

def dragon_version(G, root):
    r'''
        >>> T, DFN = dragon_version(example1, 'a')
        >>> dump(T, 'a')
        a
          b
            c
            d
          e
            f
        >>> [x[0] for x in sorted(DFN.items(), key=lambda x: x[1])]
        ['a', 'e', 'f', 'b', 'd', 'c']
    '''
    def search(n, i):
        visited.add(n)
        for s in G.get(n, ()):
            if s not in visited:
                T[n].append(s)
                i = search(s, i)
        DFN[n] = i
        return i - 1
    T = collections.defaultdict(list)
    visited = set()
    DFN = {}
    search(root, len(G))
    return T, DFN

def bruce_version(G, root):
    r'''
        >>> list(reversed(tuple(bruce_version(example1, 'a'))))
        ['a', 'e', 'f', 'b', 'd', 'c']
    '''
    def gen(n):
        visited.add(n)
        for s in G.get(n, ()):
            if s not in visited:
                for x in gen(s): yield x
        yield n
    visited = set()
    return gen(root)


