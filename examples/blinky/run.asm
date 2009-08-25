    # Set pin directions and pull-ups:
    out 0x05,0xBF  # PORTB, enable pull-ups on all pins except pin 5
    out 0x04,0x20  # DDRB, pin 5 output, all others input
    out 0x08,0xFF  # PORTC, enable pull-ups on all pins
    out 0x07,0     # DDRC
    out 0x0B,0xFF  # PORTD, enable pull-ups on all pins
    out 0x0A,0     # DDRD

    # Set system clock to 62.5 KHz:
    ldi r0,0x80
    ldi r2,0x08
    sts 0x61,r0    # enable setting system clock prescaler
    sts 0x61,r2    # set system clock prescaler to 256, clock is now 62.5 KHz

    ldi r2,0xFF    # turn on LED (and leave other pull-ups on)
    ldi r3,0x20    # bit to toggle in r2

outer_loop
    out  0x05,r2
    eor  r2,r3

    ldi  r24,0x84  # 1 cycle
    ldi  r25,0x1E  # 1 cycle  delay 31249 cycles

delay
    dec  r24       # 1 cycle
    sbci r25,0x00  # 1 cycle
    brne delay     # 2 cycles on branch, 1 on no branch

    rjmp outer_loop
