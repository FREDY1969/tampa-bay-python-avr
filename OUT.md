# `OUT[B]` #

The set of all [Definitions](Definitions.md) reaching the point just after the last statement of BasicBlock B.

For all blocks, B:

> `OUT[B] = (IN[B] - KILL[B]) union GEN[B]`

Both [IN](IN.md)`[B]` and `OUT[B]` are computed by the ReachingDefinitions algorithm.

Compare to [IN](IN.md)`[B]`.