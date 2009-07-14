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
