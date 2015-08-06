I'm using the term _package_ to mean a collection of [Words](Word.md) or
functions.  So it's more like a Python _module_.  Since the AVR processors are
so restricted on memory, I don't think that we are going to need higher level
abstractions (like Python's _package_).

There are two (and a half) types of packages:
  * Library
  * Program
  * Installation

# Library #

Libraries are designed to be _used by_ other libraries and programs.  They are
not complete programs by themselves.

There is a builtin Library that is automatically used by all other Packages.

## Uses ##

When a package _uses_ a library, the term is **uses** (rather than the Python **import**).

# Program #

A program is where the buck stops.  Programs may only be _used_ by installations.  It is the program that is compiled and loaded into the microcontroller.

# Questions and Answers #

Each package (both _libraries_ and _programs_, but not _installations_) may include a set of _questions_ to
be asked to each programmer that _uses_ that package.

And each package includes a (perhaps partial) set of _answers_ to the questions
from all of the packages it uses.  Questions that a package does not answer will be forwarded to the packages using that package, for them to answer.

[Words](Word.md) that act as declarations may also have _questions_ associated with them.

# Installation #

The _installation_ is a very limited package.  It corresponds to the
installation of a _program_ on a specific configuration of hardware.

The only thing that the installation has is the _program_ that it _uses_ and the set of answers to all questions that were left unanswered by that program.

This lets the program defer to the installation for the exact model chip and
pins used to connect to various hardware elements (for example).

An installation is the only kind of package that can _use_ a _program_.