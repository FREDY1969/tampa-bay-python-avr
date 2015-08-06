This is taken from [here](http://www.nongnu.org/avr-libc/user-manual/FAQ.html#faq_reg_usage).

Registers that subroutines may clobber: `r18-27`, `r30-31` (Note, this includes X and Z, but not Y).

Registers that subroutines must preserve: `r2-r17`, `r28-r29` (Note, this includes Y, which is used as a frame (FunctionActivationRecord) pointer).  "The requirement for the callee to save/preserve the contents of these registers even applies in situations where the compiler assigns them for argument passing".

Special registers:

  * `r0` -- temporary register.
  * `r1` -- always 0!  (must be reset to 0 after `MUL` instructions, with `clr r1`).

Function arguments:

Allocated left to right into `r25-r8`.  "All arguments are aligned to start in even-numbered registers (odd-sized arguments, including char, have one free register above them). This allows making better use of the movw instruction on the enhanced core".  If too many, those that don't fit are passed on the stack (except for vararg functions, then all args are passed on stack and char is extended to int).

First arg in `r25:r24`, second in `r23:r22`, etc.  Single byte args only set low-order register (`r24`, `r22`, etc).

Return values:

  * 8-bits in `r24` (zero/sign-extended to 16 bits by the called function (unsigned char is more efficient than signed char - just `clr r25`)).
  * 16-bits in `r25:r24`
  * up to 32 bits in `r22-r25`
  * up to 64 bits in `r18-r25`