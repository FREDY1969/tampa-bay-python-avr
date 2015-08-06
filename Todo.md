# Todo List #

These are smaller subtasks that you can volunteer for and knock off for the project without having to understand the whole world.

  * Refactor the assembler to place the info in [asm\_opcodes.py](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/asm_opcodes.py) into the [machine database](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/machine.ddl).
  * A bit more challenging task would be to figure out how to order the [assembler\_blocks](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/database/ucc.ddl#377) to maximize the use of conditional branch, rjmp and rcall instructions.
  * Separate parsing into separate ucc.db for each package.
    * Right now the parsing for all of the words used by a program is done at compile time and deposited into that program's ucc.db.
    * Add file modification times to ucc.db so we can quickly check to see what's changed.
    * Keep track of which words add syntax so that we don't have to regenerate the parser.py file all of the time (it should be very rare to have to do this).  We can compare the most recent modification time for all of the words contributing syntax to the parser.py modification time.
    * Can we generate IntermediateCode for packages independently (without knowledge of the entire program)?  Or can we only do the [AbstractSyntaxTrees](AbstractSyntaxTree.md)?  (This will probably depend mostly on macro expansions, which should work, I think).  Would have to figure out which modification times to record to trigger recompiles when the defining words change that do this stuff.