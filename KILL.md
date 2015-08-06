# `KILL[B]` #

The set of [Definitions](Definitions.md) outside of BasicBlock B that define identifiers that also have definitions within B.

These are the definitions killed by B.

## Notes ##

It looks like it would be OK to substitute _all_ of the definitions that define identifiers that have definitions within B, including the definitions within B ([GEN](GEN.md)`[B]`).