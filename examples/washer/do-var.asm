do-var:
    movw r30,r18  ; Z = pfa
    lpm r26,Z+    ; X = addr of var in Data Memory
    lpm r27,Z
    ldd r0,X+     ; push low byte of value
    push r0
    ldd r0,X      ; push high byte of value
    push r0
    jmp next

