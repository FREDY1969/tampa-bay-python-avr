    # Set pin directions and pull-ups:
    ldi r18,0xDF
    out io.portb,r18  # PORTB, enable pull-ups on all pins except pin 5
    ldi r18,0x20
    out io.ddrb,r18   # DDRB, pin 5 output, all others input
    ldi r18,0xFF
    out io.portc,r18  # PORTC, enable pull-ups on all pins
    ldi r18,0
    out io.ddrc,r18   # DDRC
    ldi r18,0xFF
    out io.portd,r18  # PORTD, enable pull-ups on all pins
    ldi r18,0
    out io.ddrd,r18   # DDRD

    # Set system clock to 62.5 KHz:
    ldi r18,0x80
    ldi r19,0x08
    cli
    sts io.clkpr,r18  # enable setting system clock prescaler
    sts io.clkpr,r19  # set system clock prescaler to 256, clock is now 62.5 KHz
    sei

    ldi r18,0xFF    # turn on LED (and leave other pull-ups on)
    ldi r19,0x20    # bit to toggle in r18

outer_loop
    out  io.portb,r18
    eor  r18,r19

    ldi  r20,0x84  # 1 cycle
    ldi  r21,0x1E  # 1 cycle  delay 31249 cycles

delay
    subi r20,1     # 1 cycle
    sbci r21,0     # 1 cycle
    brne delay     # 2 cycles on branch, 1 on no branch

    rjmp outer_loop
