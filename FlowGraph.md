# Flow Graph #

A set of [BasicBlocks](BasicBlock.md) along with their successor relationships.  This is a _directed graph_, where the nodes are the basic blocks, and the arcs are the successor relationships.  Where a basic block ends in a conditional jump, it has two successors.

As this graph may contain loops, it is not _acyclic_, therefore, not a DAG (DirectedAcyclicGraph).