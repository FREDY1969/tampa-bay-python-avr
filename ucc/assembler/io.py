# io.py

r'''This is a list of the ATMega328P IO registers.

These are presented simply as module variables.  The value of the variable is
the equivalent RAM address for the IO register (not the IO register number,
which doesn't apply to all IO registers).
'''

clkpr = 0x61

sreg = 0x5F
sph = 0x5E
spl = 0x5D

portd = 0x2B
ddrd = 0x2A
pind = 0x29
portc = 0x28
ddrc = 0x27
pinc = 0x26
portb = 0x25
ddrb = 0x24
pinb = 0x23
