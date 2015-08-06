This is algorithm 12.3, pp 433, in the DragonBook, 1977 version.

# Inputs #

A FlowGraph for which [KILL](KILL.md)`[B]` and [GEN](GEN.md)`[B]` have been computed for each BasicBlock B.

# Outputs #

[IN](IN.md)`[B]` and [OUT](OUT.md)`[B]` for each BasicBlock B.

# Method #

We use an iterative approach, starting with the "estimate" `IN[B] = {}` for all B and converging to the desired values of [IN](IN.md) and [OUT](OUT.md).

```
for each block B:
    IN[B] = set()
    OUT[B] = GEN[B].copy()

change = True
while change:
    change = False
    for each block B:
        newin = union over all P, a predecessor of B, of OUT[P]
        if newin != IN[B]:
            change = True
            IN[B] = newin
            OUT[B] = (IN[B] - KILL[B]).union(GEN[B])
```

# Notes #

This is later modified, in algorithm 14.1, pp 479, of the DragonBook, 1977 version, to do the second `for` loop in DepthFirst order.  This is done to improve the performance of the algorithm.