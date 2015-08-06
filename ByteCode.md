Whether we support byte code (vs native code) is still an open issue in my mind.  I'm currently leaning towards it; and leaving native code for later to allow us to get something up and running more quickly.

## Advantages: ##

The advantages of byte code are:

  * easier to implement (I see this as the main advantage, since it seems like we have enough else to do, at least initially).
  * more compact, so can accommodate large programs (but I don't imagine doing terribly complicated code on a microcontroller).
  * more portable to other processors and instruction sets.

## Disadvantages: ##

The disadvantages are:

  * runs slower, probably by about 10 times.

## Implementation ##

The implementation would be modeled after the language, _forth_.  The byte codes making up a high-level [Word](Word.md) would simply be a series of 2-byte addresses.  The byte code interpretor in _forth_ is called the _inner interpretor_.  It is the code that walks down the list of addresses and executes each Word.  Some Words read the following 2 bytes as additional data (for example, _lit_ reads the next 2 bytes in the byte code stream and pushes those on the stack, whereas _jmp_ reads the next 2 bytes to see where to jump to).

Each [Word](Word.md) in the micro-controller would have two parts:

  1. A _code field address_ (cfa), which points to the machine code to execute when this Word is run.
  1. A _parameter field_ (pfa), which contains other data.  Different types of Words use this for different purposes.  Byte code Words store the byte codes here.  Constant Words store the constant value here.  Variable Words store the address of the variable in data storage.  Assembler Words store the machine instructions here.  Etc.

In general, a Word looks like:

```
              +--- pfa
              |
              V
        +-----+---------------- ...
  Word: | cfa | parameter field ...
        +--|--+---------------- ...
           |
           |   +------------- ...
           +-->| machine code ...
               +------------- ...
```

Assembler (machine code) Words look like:

```
        +-----+------------- ...
  Word: | cfa | machine code ...
        +--|--+------------- ...
           |  ^
           |  |
           +--+
```

Forth implements the inner interpretor with a Word called _next_.  Every machine code Word ends with a _jmp next_.  (Note that this prevents machine code Words from directly calling other machine code Words as functions; but this doesn't seem to be a problem in forth).

Here's what _next_ would look like on the AVR.  The Program Counter (PC) for the byte codes is stored in `r2:r3`.  The FunctionActivationRecord (FAR) is stored in `Y`.  The address of the Word's pfa is left in `r18:r19` for the Word's code to utilize.

```
next: movw  r30,r2   ; Z = PC
      lpm   r18,Z+   ; r18:r19 = address of Word
      lpm   r19,Z+
      movw  r2,r30   ; PC = Z
      movw  r30,r18  ; Z = address of Word
      lpm   r20,Z+   ; r20:r21 = cfa of Word
      lpm   r21,Z+
      movw  r18,r30  ; r18:r19 = pfa of Word
      movw  r30,r20  ; Z = cfa
      ijmp           ; jump to cfa
```

## FunctionActivationRecord Layout ##

The layout of the FAR is dictated mainly by:

  1. Wanting to put some of these on the stack, and the stack grows down.
  1. Wanting to evaluate the arguments to a function in the order that they are passed (unlike many C compilers, because of #1).

The Y register is always used to point to the FAR for the currently running function.

This layout and use of the Y register is the same, regardless of whether the FAR is stack-based or static.

```
         Y register ---+ 
                       |
                       V
       +---------------+---------+--------+-----+------+------+
  FAR: | local vars... | ret FAR | ret PC | ... | arg2 | arg1 |
       +---------------+---------+--------+-----+------+------+
       <---- stack growth (push goes this direction)
```

### Stack based FAR ###

For ByteCode Words that build their FAR on the stack, the cfa would point to:

```
start: push r2      ; save return PC in new FAR
       push r3
       movw r2,r18  ; PC = pfa
       push r28     ; save return FAR in new FAR
       push r29
       in r28,SPL   ; Y = SP
       in r29,SPH
       jmp next
```

And the `return` Word would have this code:

```
ret:   pop r24      ; r24:r25 = return value on top of stack
       pop r25
       in r0,SREG   ; save interrupt enable status
       cli          ; disable interrupts while SP is broken
       out SPH,r29  ; SP = Y
       out SREG,r0  ; restore interrupt status
       out SPL,r28  ; interrupts still disabled for 1 inst after interrupt enable...
       pop r29      ; Y = return FAR
       pop r28
       pop r3       ; restore return PC
       pop r2
       jmp next
```

### Static FAR ###

A static FAR would be allocated as another Word.  So we'd have the Word being executed (the function), and the Word representing the static FAR as two separate Words.  We could have as many static FARs for the same function Word as we need.

The static FAR Word is stored in flash memory, and so isn't actually the true FAR.  It points to the true FAR in the data space (SRAM).  It also points to the function Word that it executes.

The static FAR Word is the Word that is included in the ByteCode stream by the caller to the function.  So the cfa of the static FAR Word is where the action is.  (The cfa of the function Word is not used; eventually this might be used to get FARs allocated in the heap, by calling the function Word directly, which should allow the same function Word to be used with both static FARs and heap-based FARs).

Thus, a static FAR Word is 3 words (word == 2 bytes) long:
  1. The cfa run by callers of this Word
  1. The address in SRAM of the true FAR
  1. The pfa of the function Word that needs to be executed

The cfa of all static FARs (no matter what function Word they represent) points to:

```
static: movw r26,r18       ; X = pfa of static FAR Word
        ld r30,X+          ; Z = pfa[0] = static FAR in SRAM
        ld r31,X+
        std Z+retFAR,r28   ; new FAR.retFAR = Y = old FAR
        std Z+retFAR+1,r29
        std Z+retPC,r2     ; new FAR.retPC = old PC
        std Z+retPC+1,r3
        ld r2,X+           ; PC = pfa[1] = pfa of function Word to be called
        ld r3,X
        movw r28,r30       ; Y = Z = new FAR
        jmp next
```

Static FAR Words require a different `return` to unwind this.  This is not shown here.

The first ByteCode in the function Word copies the arguments from the stack to the FAR.