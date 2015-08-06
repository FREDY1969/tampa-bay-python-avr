This is taken from the DragonBook, algorithm 14.9, pp 509, in the 1977 version.

This algorithm computes the set of global variables changed by each procedure, P, in the program.

# Inputs #

A collection of procedures, P<sub>1</sub>, P<sub>2</sub>, ..., P<sub>N</sub>, where _i_ is the DepthFirst number of P<sub>i</sub> in the calling graph of the procedures.

> The DepthFirst constraint here is an optimization to reduce the number of iterations in the outer loop of the algorithm below.  It only influences the efficiency of the algorithm, not the accuracy.

> The DepthFirst order is a preorder traversal of the call graph.  So the root procedure (_run_ in our case) is the first procedure in this ordering.

# Outputs #

`CHANGE[P]`, the set of global variables and formal parameters of P that are changed by P.

# Method #

  1. Compute `DEF[P]` for each procedure P by inspection.  `DEF[P]` is the set of global variables directly changed by P (not including the variables changed by procedures called by P).  We will extract `DEF[P]` from the AbstractSyntaxTree produced by the parser with a SQL call.
  1. Execute the following program to compute `CHANGE[P]`.

```
    for i in range(1, N + 1): CHANGE[Pi] = DEF[Pi]   # initialize

    while changes occur:
        for i in range(N, 0, -1):
            for each procedure Q called by Pi:
                add any global variables in CHANGE[Q] to CHANGE[Pi]
                for each formal parameter X (the j-th) of Q:
                    if X in CHANGE[Q]:
                        for each call of Q by Pi:
                            if A, the j-th actual parameter of the call, is a global or formal parameter of Pi:
                                add A to CHANGE[Pi]
```

# Notes #

  1. This needs to consider aliases of either global variables or formal parameters.
  1. I guess for us, the formal parameter stuff would only apply to array and function parameters, since we don't have reference parameters.