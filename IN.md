# `IN[B]` #

The set of all [Definitions](Definitions.md) reaching the point just before the first statement of BasicBlock B.

For all blocks, B:

> `IN[B] = union over all P, a predecessor of B, of OUT[P]`

Both `IN[B]` and [OUT](OUT.md)`[B]` are computed by the ReachingDefinitions algorithm.

Compare to [OUT](OUT.md)`[B]`.