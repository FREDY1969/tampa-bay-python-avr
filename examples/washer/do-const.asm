    movw r30,r18    # Z = pfa
    lpm r0,Z+       # push low value
    push r0
    lpm r0,Z        # push high value
    push r0
    jmp next
