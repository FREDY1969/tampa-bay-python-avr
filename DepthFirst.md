This is algorithm 13.3 on pp 450 of the 1977 DragonBook.

This computes a depth-first spanning tree (DFST) and assigns a depth-first number (DFN), from 1 to N, to each of the functions in a call graph.

I'm not sure we really need the DFST.  Most of the algorithms are interested in the ordering defined by DFN, as this serves as an optimization of the algorithms.

# Inputs #

A call graph _G_.

> A "call graph" is just a graph of function calls (who calls who).

# Outputs #

A DFST _T_ of _G_ and a `DFN[N]` for each node, _N_, of _G_.

# Method #

n0 is the root function (_run_ in our case).

```
def search(n):
    mark n "visited"
    for each successor s of n:
        if s is "unvisited":
            add edge n -> s to T
            search(s)
    DFN[n] = i
    i -= 1

T = <empty>
for each node n of G: mark n "unvisited"
i = number of nodes of G
search(n0)
```

# Example #

The following call graph

```
a
 b
  c
  d
 e
  f
   b
    c
    d
```

could be represented by the following Python dictionary recording a tuple of the calls made by each function:

```
{'a': ('b', 'e'),
 'b': ('c', 'd'),
 'c': (),
 'd': (),
 'e': ('f',),
 'f': ('b',),
}
```

This would produce the following DFN:

```
{'a': 1,
 'b': 4,
 'c': 6,
 'd': 5,
 'e': 2,
 'f': 3,
}
```

This could be linearized into the following tuple which places each function at it's assigned DFN position within the tuple:

```
('a', 'e', 'f', 'b', 'd', 'c')
```