This is working document defining the order to implement the various features of each component in the compiler.  The goal is to get something running as quickly as possible and then build on it.

As we get down the road and learn more, there will undoubtedly be changes here, but this gives us a starting point.

No attempt is made to synchronize the steps between the various components.

## IDE ##

  1. add word, change answers, edit text with text editor
  1. run compiler, simple on-screen text editing/save
  1. rename word, delete word
  1. change questions
  1. packages
  1. present info from the database to the user

## Front End ##

  1. extensible syntax, load blocks and triples
  1. gather function information (variables used/set, pure?, call graph)

## Back End ##

  1. +, -, =, !=, int, task (static FAR)
  1. <, <=, >, >=, and, or, not
  1. io registers
  1. bit-and, bit-or, bit-xor, bit-not
  1. interrupt service routines, function (FAR on stack)
  1. arrays, `*`
  1. coroutines, pipes
  1. exception handling
  1. fixed point
  1. /, %
  1. add optimizer

## Runtime ##

  1. repeat, set, output-pin
  1. if, while
  1. input-pin (polling)
  1. initialize data, bss
  1. input-pin (interrupts)
  1. initialize io registers and override global variable initialization from eeprom
  1. USART, generators/consumers
  1. exception handling
  1. wait, usec
  1. I2C
  1. PWM