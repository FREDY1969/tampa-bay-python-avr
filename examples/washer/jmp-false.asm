     pop r19       # r18:r19 = condition
     pop r18
     cp r18,r1     # r18:r19 == 0?
     cpc r19,r1
     brne .true
     movw r30,r2    # Z = PC
     lpm r2,Z+      # PC = (Z)
     lpm r3,Z
     jmp next
.true:
     ldi r0,2       # PC += 2
     add r2,r0
     adc r3,r1
     jmp next

