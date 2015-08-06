# ud-chaining #

The "ud" stands for [Use](Use.md)-[Definition](Definition.md) chaining.  This is the result of determining for each _use_ of a variable, what are all of the _definitions_ that may have reached this point.

Once the [IN](IN.md)`[B]` information is known, the ud-chaining can be computed as follows:

  * If the [Use](Use.md) of a variable A is preceded in its [block](BasicBlock.md) by a [Definition](Definition.md) of A, then only the last definition of A in the block prior to this use reaches this use.  Thus, the ud-chain for this use consists of only this one definition.
  * Otherwise, if a use of A is not preceded in its block B by a definition of A, then the ud-chain for this use consists of all definitions of A in [IN](IN.md)`[B]`.

Compare to [du-chaining](DUChaining.md).