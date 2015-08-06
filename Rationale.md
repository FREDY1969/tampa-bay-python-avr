## Support Event Driven Code ##

When programming languages were being developed, programs had all of their input when the program started, and went through a series of steps to produce all of their output and then terminated.  These were called "batch" programs.

During this time, it made sense to allocate [FunctionActivationRecords](FunctionActivationRecord.md) on a stack because the program could only be doing one thing at a time.

But today, programs are often long running and responding to external events that they have no control over.  (Consider server apps, GUI apps, and microcontroller apps).

In this environment, the stack gets in the way of going back and forth between two or more threads of execution.

This project explores using static [FunctionActivationRecords](FunctionActivationRecord.md) to allow more natural programming of event driven systems.

## Support "Programming in the Large" or MetaProgramming ##

Traditional languages only allow you to write code that is executed at run-time.  As we continue to look for ways to increase programmer productivity, we must explore explicit ways of "programming in the large" -- that is, writing code that is executed at compile-time to provide much higher level abstractions as libraries.  This might also be called "metaprogramming" or programming about programming.

This project explores the use of metaprogramming.

### Reducing "Surface Area" by Using Questions and Answers ###

Traditional languages are entirely text based using a format grammar or syntax.  If language extensions were only able to get options through an extension of the syntax, the language complexity (or "surface area") would grow without bounds.

This project explores the use of questions and answers as an alternative to syntax.  This allows the creation of language extensions that are like declarations, but have no syntax.  Instead, the extension has a set of questions attached to it.  When the programmer wishes to use this extension to declare something in his program, these questions are presented to him so that he doesn't have to learn or remember new syntax for this language extension.

## Integrate GUI/IDE with Compiler ##

Traditionally compilers only operate on one function at a time and discard the intermediate data that they have produced in order to compile that function.  The compilers run as separate programs taking files as input and output, and generating output files in obscure formats (e.g., .o files).  These are then linked together by a second program to produce the resulting executable program.

This project will explore all of the following:

  1. Making the compiler run as a subroutine, rather than a separate program.
  1. Storing the compiler intermediate data in a sqlite3 database so that the GUI/IDE can access this data to provide cross-reference type information to the developer.
  1. Allowing the compiler itself to access this intermediate information so that it can consider both sides of a function call (caller and function) when it generates code for both of them.
  1. Thus, the compiler compiles the entire program as a single unit, rather than as a series of small functions to later be bundled together.