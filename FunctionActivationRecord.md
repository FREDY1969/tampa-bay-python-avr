A _function activation record_ (FAR) is the data structure that contains all of the information related to the invocation of a function.  This includes the arguments, return address, return FAR and local variables (both programmer and compiler generated).

Since different functions have different numbers of arguments and local variables, FARs are not all the same size on a system wide level (though they are usually the same size for any given function).

## Where do we put these things? ##

The main question with function activation records is where are they placed in memory?  I'm thinking we support both stack based and static.

### On a stack ###

This is what the vast majority of programming languages do.  And this is why event programming or multi-tasking is so unnatural in most languages.

#### advantages: ####

  * It's easy and efficient to implement.
  * It supports recursive functions.  (But I don't think that micro-controller applications require recursive functions -- tell me if I'm wrong here!).
  * It requires less overall memory space, since the FARs for all of the functions don't need to all be in memory at the same time.

#### disadvantages: ####

  * It does not easily support multi-tasking, or event driven (e.g., interrupt driven) programming.  Imagine if event A occurs and function A is called to process this event.  A calls B and B suspends waiting for event B.  While B (and A) are suspended, event X occurs and function X is called to process event X. Then X calls Y, and Y suspends waiting for event Y.  The stack now looks like:
    * A
    * B
    * X
    * Y
> Now if event B occurs, then B can be resumed.  It returns to A, which then calls C, which calls D, which suspends waiting for event D.  What does the stack look like now?

### Statically ###

This is another easy approach.  Each function has one (or possibly more) static FARs that never go away.

#### advantages: ####

  * Easy and efficient to implement.
  * Allows multi-tasking and event-driven programming.

#### disadvantages: ####

  * Does not support any form of re-entrancy (recursion or multiple ongoing calls to the same function at the same time to handle multiple events).
    * And if the arguments are passed straight into the FAR, you would not be able to do `foo(x, foo(y, z))`, because the second call to `foo` would clobber `x` in the first call to `foo`.  The solution is to not pass arguments straight into the FAR.  This can be done in a number of ways:
      * Collect the arguments locally (in the caller) and then copy all of them into the FAR just prior to the function call.
      * Collect the arguments somewhere else (perhaps locally, or on a thread-based argument stack) and just pass the address of the arguments into the FAR.  This makes the FAR a little smaller because it no longer needs space for each argument, just a single address.  (But it still needs space for the return address and local variables).
      * Have the compiler recognize this and separate it into two calls:
        1. `temp = foo(y, z)`
        1. `foo(x, temp)`
      * Pass the arguments in registers and let the function copy the ones that it needs to preserve into its FAR.  (This is the chosen way for now).
  * Uses more memory because each FAR consumes memory space whether it's being used or not.

### In a heap ###

This is the most general approach, but requires heap management libraries and has more overhead.

It's ironic that Python uses this approach for Python functions, but because the underlying implementation is in C, the underlying C stack prevents Python from really taking advantage of this!  The [stackless](http://www.stackless.com/) project was born to fix this, but didn't really address the issue of C functions (like **map**) calling Python functions in a portable way, so was not adopted by the CPython group. :-(

#### advantages: ####

  * This implementation is fully general.  It supports event-driven multi-tasking, as well as full re-entrancy and recursion.

#### disadvantages: ####

  * Requires heap management libraries (though perhaps not a garbage collector).
  * Is less efficient (due to heap management overhead).
  * Some additional memory required for heap management and due to heap fragmentation, though probably not nearly as much as the static approach.

## FAR Layout ##

To make it easier when the FAR is on the stack, the layout is as follows:

| local variables | param1 | param2 | ... | paramN | ret FAR pointer | ret addr |
|:----------------|:-------|:-------|:----|:-------|:----------------|:---------|

This allows us to create functions that have optional parameters with multiple entry points depending on how many parameters are passed.  Parameters are passed in registers, so they can be pushed to the stack.  Let's say we have a function, `foo`, with two required parameters and two optional parameters.  To make the example easier, we'll assume that each parameter is one byte and they are passed in registers: [r2](https://code.google.com/p/tampa-bay-python-avr/source/detail?r=2), [r3](https://code.google.com/p/tampa-bay-python-avr/source/detail?r=3), [r4](https://code.google.com/p/tampa-bay-python-avr/source/detail?r=4), and [r5](https://code.google.com/p/tampa-bay-python-avr/source/detail?r=5).  The function prolog for `foo` would look like:

```
foo2   ldi r4,param3_default             # foo called with 2 params
foo3   ldi r5,param4_default             # foo called with 3 params
foo4   push r29                          # foo called with 4 params
       push r28                          # push ret FAR pointer (Y==r28:r29)
       push r5                           # push param 4
       push r4                           # push param 3
       push r3                           # push param 2
       push r2                           # push param 1
       subi sp,size_of_local_variables   # need to disable interrupts here...
       in r28,spl                        # FAR pointer (Y==r28:r29) == sp
       in r29,sph
```