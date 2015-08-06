Compilers traditionally divide the compilation process into two parts:

  1. A front-end which does the scanning (grouping characters into tokens) and parsing (grouping tokens into nested syntactic phrases).  This generates a machine independent IntermediateCode.
  1. A back-end which optimizes and converts the IntermediateCode into the target machine code.

Usually these two steps are packaged together into one program and run at the same time so that the user is unaware of the distinction.

But our compiler will separate these two steps into different programs, run at different times.  This will give our GUI much more information to share with the user.

The front-end will be run by the GUI as changes for each word are saved, reporting syntax errors immediately.  This keeps the database up to date so that the GUI always has up to date cross reference information to show the user.

**Note**: The early GUI will actually not run the front-end automatically like this and will not show cross reference information to the user.  So the final compile (back-end) script run by the GUI will initially include running the front-end for the time being.  But the front-end and back-end will still be packaged from the start as two separate entities.

# Parsing #

Parsing consists of a scanner and a parser.  The scanner is fixed and can't be modified by [Words](Word.md) wishing to add new syntax (except for adding new reserved words).

But the parser may be extended by individual Words, which may add additional grammar rules for `raw_statement` (see [SYNTAX](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/parser/SYNTAX) file) to the default set of rules defined for the language.

So the first step to parsing is to create the parser.  The grammar rules for all [Words](Word.md) in the [Package](Package.md) and all "used" Packages are added to the default set of grammar rules to create a parser for each Package.

  * Note that the same parser is not used for the whole Program.  This is to prevent later Packages, that _use_ this Package, from invalidating the syntax that was used to write this Package.

Once the parser has been created, it is then used to parse each of the [Word](Word.md) source files in the Package.  The output of this parsing is a SymbolTable and AbstractSyntaxTree which are both stored in the [Database](Database.md) for that Package (called _ucc.db_).

The AbstractSyntaxTree is then translated into a machine independent IntermediateCode which is also stored in the [Database](Database.md).

See ParsingDesign, MetaSyntax

# Compiling #

By the _compiling_ phase, I mean the back-end of the compilation process.  Except that for this language, the front-end (parsing) and back-end (compiling) are run at different times.

The compiling phase is where the IntermediateCode is (optionally) optimized and converted into machine code.

The compiling phase is done for the whole [Installation](Package#Installation.md) treated as a single unit.  This is another area that differs from traditional compilers.

Traditional compilers compile one function at a time with no knowledge of how or where that function is used, and no knowledge about the functions that the function being compiled calls.  There is then a link edit pass to cobble all of pieces of object code for each compiled function together to make the whole program.  Generally libraries are compiled in advance, and the compiled version of the library shared by all programs using that library.

Our compiler will work differently.  It will have access to information about how and where each function is used, as well as information about the functions being called.  It will generate code for the whole program as a single unit, including compiling from scratch all libraries used by the program, and generate up to two [.hex files](http://en.wikipedia.org/wiki/Intel_Hex): one for the code and data to be loaded into the flash memory, and one for the data to be loaded into the eeprom memory.

The first step is to create a Context that will hold all of the information related to the compile process. The answers to all of the questions for all of the Packages used are placed into this Context. Then each Package's init word (if any) is run, which may add more information to the Context.  (Note this may have already been done by the GUI, e.g., as a registry or session object).

The IntermediateCode is then compiled into blocks of assembler instructions that are then gathered up and assembled into the .hex file(s) to be uploaded to the micro-controller.  This also results in additional information (such as address assignments, run times and memory sizes) to be recorded in the SymbolTable.

This compile process is performed by a `compile_file` method on the Word being compiled.  This allows different Words to produce different types of compiled objects.

In the future, I would like to also be able to produce an optional matching Python program to run on the PC that communicates with the micro-controller.  This would allow the PC program to do the heavy lifting for the micro-controller.  We might also be able to use different PC programs for different tasks, like a command prompt that lets us run individual Words on the micro-controller from a command prompt, or a unit test driver program that reads unit test scripts on the PC, runs the tests on the micro-controller and compares the results to what is expected in the script.  Another PC program might be a debugger program that helps us debug the micro-controller code.  The details of how this PC program would be generated are yet to be determined, and will probably be a "release 2" capability.