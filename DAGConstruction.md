This is taken from the DragonBook, algorithm 12.2, pp 420, of the 1977 version.

# Input #

A BasicBlock.

# Output #

A [DAG](DirectedAcyclicGraph.md) with the following information:

  1. A _label_ for each node.  For leaves, the label is an identifier (constants permitted), and for interior nodes, an operator symbol.
  1. For each node a (possibly empty) list of _attached identifiers_ (constants not permitted here).

# Method #

This assumes nodes with one or two children, called _left_ and _right_ in the latter case.

We assume the existence of a dictionary `NODE[IDENTIFIER]` which, as we build the DAG, returns the most recently created node associated with IDENTIFIER.  Intuitively, `NODE[IDENTIFIER]` is the node of the DAG which represents the value which IDENTIFIER has at the current point the DAG construction process.

The DAG construction process is to do the following steps (1) through (3) for each statement of the block, in turn.  Initially, we assume that there are no nodes, and `NODE[]` is empty.

Suppose the "current" ThreeAddressStatement is either:

<ol type='i'>
<li>A = B op C</li>
<li>A = op B</li>
<li>A = B</li>
</ol>

We refer to these as cases (i), (ii), and (iii).  We treat a relational operator like `if I <= 20 goto` as case (i), with A undefined.

  1. If `NODE[B]` is undefined, create a leaf labeled B, and let `NODE[B]` be this node.  In case (i), if `NODE[C]` is undefined, create a leaf labeled C and let that leaf be `NODE[C]`.
  1. Depending on which of the three cases are involved for the "current" statement:
    * In case (i), determine if there is a node labeled `op`, whose left child is `NODE[B]` and whose right child is `NODE[C]`.  (This is to catch common subexpressions.)  If not, create such a node.  In either event, let _n_ be the node found or created.
    * In case (ii), determine whether there is a node labeled `op`, whose lone child is `NODE[B]`.  If not, create such a node, and let _n_ be the node found or created.
    * In case (iii), let _n_ be `NODE[B]`.
  1. Append A to the list of attached indentifiers for the node _n_ found in (2).  Delete A from the list of attached identifiers for `NODE[A]`.  Finally, set `NODE[A]` to _n_.

# Notes #

We will be constructing the DAG directly from the AbstractSyntaxTree (AST), rather than the ThreeAddressStatements described above.  The difference is that intermediate nodes in the AST have A undefined.

So `set A to B + C * D` is treated as the following three "statements", where the first two statements has an undefined A:

  1. `<undefined>` = B
  1. `<undefined>` = C `*` D
  1. A = (1) + (2)

We will also have to record order dependencies between the subexpressions where a later expression kills a value used by an earlier expression in the syntax.