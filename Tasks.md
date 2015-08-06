Refer to the ProgramFlow page as a reference for these.

  1. GUI - **Assigned to Jason**
    * figure out what Python GUI framework to use. (done)
      * must be free (as in beer) and work on Linux/Mac/Windows.
    * re-write Tk gui in chosen GUI framework.
    * separate AVR compiler code from GUI code to make porting to another GUI framework easier.
    * support future requests for GUI enhancements as we figure out how this all should work.
  1. Words, Questions and Answers - **Assigned to Jason/Bruce** (done)
    * figure out merge-able text format. (done)
    * implement a one-size-fits-all set of classes for words, questions and answers that everybody else can use. (done)
  1. AbstractSyntaxTree (AST) database schema. - **Assigned to Bruce**
  1. Assembler
    * verify asm\_opcodes.py against Atmel docs.
    * figure out operand ordering (while verifying). (done)
    * finish generation code. (done)
    * write a simple parser, including the word.parse\_file method for assembler words on the ProgramFlow page. (done)
  1. Parser (and scanner) - **Assigned to Bruce** (done)
    * figure out what Python parser generator tool to use. (done)
    * write the scanner (done).
    * write the parser generation and file parsing process (including the word.parse\_file method for high-level words on the ProgramFlow page).  (done)
    * support future changes to grammar.
    * this task may involve translating from our own BNF syntax into the chosen tool's BNF syntax. (done)
  1. IntermediateCode Generation
    * this is the final step of the (Parsing) phase of ParsingAndCompiling.  It translates [AbstractSyntaxTrees](AbstractSyntaxTree.md) into a machine independent IntermediateCode.
  1. Code Generation
    * this is the back end (Compiling) phase of ParsingAndCompiling.  It translates the IntermediateCode into the assembler source code for the target microcontroller.
  1. Initial Built\_in Library
    * these are the words like `if`, `repeat`, `set`, `for`, `with`, etc.
    * these will be coded in Python.