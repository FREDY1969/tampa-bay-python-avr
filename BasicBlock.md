# Basic Block #

A _basic block_ is a sequence of instructions that are only ever entered at the top, and always run all the way to the end of the block (never jumping out of the middle of the block).

Thus only one jump is allowed per basic block, which is always at the end of the block.  This may be a conditional or unconditional jump.  If it is a conditional jump, the basic block has two successors.  If it is an unconditional jump, the basic block has one successor.