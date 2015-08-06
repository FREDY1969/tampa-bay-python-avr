A **Word** loosely corresponds to a function; or, more accurately, a declaration
(which might be a function, variable, constant, or new syntactic element,
etc).  (The term **Word** comes from the language [Forth](http://en.wikipedia.org/wiki/Forth_(programming_language)), which this language
borrows from lexically).

Words that represent functions will have _bodies_, which will be files on the filesystem that you edit with your favorite text editor.  I imagine that you'd be able to invoke the text editor from the IDE.  I also imagine that you'd be able to view the body through the IDE, and perhaps edit it there (not requiring editing there to keep things simple).

Words (representing functions) may have subordinate Words for the arguments and local variables.  But I'm not currently planning on supported nested functions (defining one function inside another).

Words are collected into [Packages](Package.md).

## ParsingAndCompiling ##

Words may also have scanner tokens assigned to them.  This is how reserved
words are defined.

They may also define a syntax (set of grammar rules) for their usage and choose to get
involved in how the word gets compiled by the compiler.  In fact, some words
only affect the compiler and have no run-time counterpart on the micro-controller itself.  For example, the 'if' word only affects the compiler, and does not appear as a function in the micro-controller.

## Defining Words ##

Some Words are defining Words.  These Words may be used to define new Words.  To do so, the defining Word may have questions attached to it that the IDE user would answer when they use this Word to define a new Word.  The defining Word uses the answers to these questions to compile the new instance Word.