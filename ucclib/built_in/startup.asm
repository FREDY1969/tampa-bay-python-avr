    # Interrupt vector (26 entries):
reset
    jmp  startup2
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset
    jmp  reset

startup2
    clr  r1
    out  io.sreg,r1     # make sure interrupts are disabled!
    ser  r28
    ldi  r29,0x08
    out  io.sph,r29
    out  io.spl,r28
    # need to add data, bss and eeprom initialization here...
    call run
termination_loop
    rjmp termination_loop
