# Directed Acyclic Graph (DAG) #

A DAG is a _directed graph_ with no cycles.  A _graph_ consists of _nodes_, and _arcs_ linking those nodes together.  If the arcs have a direction to them (have an arrowhead on one end), it is a _directed_ graph.  If the graph has no cycles, it is an _acyclic_ graph.  A directed graph only has cycles if you can start at one node (pick a node, any node) and follow a sequence of arcs (all in the direction of the arrowhead) and arrive back at the node you started with.

DAGs are used in the DragonBook to represent the computations done within a BasicBlock.

In this case, the leaves (nodes with no arcs out of them) are labeled by unique identifiers: either variable names or constants.  The [l-value](LValue.md) of a variable uses a label like `addr(A)`, while `A` itself denotes the [r-value](RValue.md).

Interior nodes (nodes with arcs out of them pointing to other nodes) are labeled by an operator symbol.  The nodes pointed to are the operands for the operator.

Nodes are also optionally given an extra set of identifiers for labels.  These are the variables that the value computed by that node should be assigned to.  (There may be more than one).

See the [DAGConstruction](DAGConstruction.md) algorithm.