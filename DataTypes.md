# Numbers #

There are three kinds of numbers recognized:
  1. Integers
  1. Ratios (only used at compile-time, not run-time)
  1. Approximate Numbers (used for fractional values)

These are described in [Numbers](Numbers.md).

# Arrays #

You can have an array of any type (including arrays).  All arrays are declared with a fixed size.  You can't add and delete elements to them like you can with Python lists.  (Though you can change elements, thus, they are not immutable like Python tuples either).

Arrays of bytes (8 bit unsigned integers) are used for strings.  Thus, strings are not a separate type.  (Neither are characters).  Though both character and string literals are provided.  (But string literals _are_ immutable, unlike string literals in C).

# Packages #

These serve both as modules and as structs (or records).  Basically, a module is a singleton package; while a struct can be instantiated multiple times.  The syntax to use the package is the same either way.

Note that while functions are allowed in structs, there is no inheritance mechanism, and no dynamic binding (or dynamic method lookup).

NOTE: Using packages as structs has yet to be implemented and is subject to change!

See [Package](Package.md).