jmp: movw r30,r2   ; Z = PC
     lpm r2,Z+     ; PC = (Z)
     lpm r3,Z
     jmp next
