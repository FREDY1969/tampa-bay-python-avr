# Exact Number #

The only type of exact numbers supported are ratios and integers.  In theory numbers like _pi_ and the _square root of 2_ could be considered exact, as they can be represented to any desired level of precision.  But we don't go that far here.  I don't think that exact irrational numbers would be useful to microcontrollers.

## Ratio ##

Ratios (or rational numbers) are only used within the compile-time environment.  When moved to the run-time environment, they are converted to approximate numbers with an accuracy sufficient for their use.

## Integer ##

Integers can be thought of as a special case of ratios.  These are the only exact numbers within the run-time environment.

Integer types are indicated by a minimum and maximum value.

# Approximate Number #

The language supports FixedPoint numbers, rather than floating point numbers for fractional values.  We can do arithmetic faster on these (since there is no floating point hardware).

These are fixed point _binary_ numbers.  So, for example, 1.2 (decimal) would be stored as 1.0011 (binary) to give roughly the same accuracy as the decimal representation.  We assume, in both cases (decimal and binary) that the true value could be half way to the next digit.  Thus, when we say 1.2, we mean that the true value is somewhere between 1.15 and 1.25, or 1.2 +/- 0.05.  And 1.0011 means that the true value is somewhere between 1.00101 and 1.00111, or within +/- `2**-5`, or +/- 0.03125 (slightly smaller than the 0.05 accuracy we had in decimal form).  Since we are dealing with approximate numbers, converting 1.0011 binary back to decimal gives 1.1875 (exactly), rather than 1.2; but this is still within the range 1.15 and 1.25.  Indeed, 1.00101 is 1.15625 decimal and 1.00111 is 1.21875 -- both with the target 1.15 to 1.25 range.

Like integers, approximate numbers have a minimum and maximum value.  This requires a certain number of bits to the left of the binary point, which is the number of bits to represent max(abs(maximum value), abs(minimum value)).

There is also a certain number of bits to the right of the binary point required to represent the desired accuracy.

Thus, the size of an approximate number can be written as L.R, where L (R) is the number of bits to the left (right) of the binary point.  So 5.3 means XXXXX.XXX.  Note that either L or R (but not both) may be negative: -2.10 is .00XXXXXXXX and 10.-2 is XXXXXXXX00.  So all three of these examples require 8 bits to store the number (the 8 X's).

The compiler tracks the accuracy of the numbers involved in arithmetic and generates a result that has the correct accuracy.  The rules for this are as follows:

To calculate the max and min values for addition, subtraction and multiplication of A and B giving C:
  * C.max = max(A.max OP B.max, A.max OP B.min, A.min OP B.max, A.min OP B.min)
  * C.min = min(A.max OP B.max, A.max OP B.min, A.min OP B.max, A.min OP B.min)
where OP is `+`, `-`, or `*`.

To calculate C.R:
  * For addition and subtraction: C.R = min(A.R, B.R)
  * For multiplication: C.R = min(A.R - B.L, B.R - A.L)

Note that this means that for multiplication the size of C is the smaller of the sizes of A and B.

Division is trickier.  There will probably have to be 2 rules: one for division by of A by an exact number, B giving C.  Then C.R = A.R + log2(min(abs(B))).  C.L can be calculated if B is a constant.

Otherwise the C.L and C.R values may have to come from the declaration of the variable being assigned to.