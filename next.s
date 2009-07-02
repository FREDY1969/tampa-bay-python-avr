;;;
;;; Let's say that the PC is stored in r3:r2
;;; And the Frame Pointer (FP) is stored in Y
;;; The new FP is stored in r5:r4, (which has the return FP)
;;; The new args addr is stored in X
;;; The num_args left are stored in r6

;;; A Frame looks like:
;;;
;;;                                    FP
;;;                                    |
;;;                                    V
;;; +---+----+----+-----+--------------+---+---+------+------+-------------- ...
;;; | ret FP | ret args | ret num_args | my PC | dyn FP addr | args and vars ...
;;; +---+----+----+-----+--------------+---+---+------+------+-------------- ...
;;;
;;; Var_arg functions have the num_args passed as their first arg.

;;; This leaves the pointer to the word in Z on entry to the CFA routine.
next:   MOVW    r30, r2         ; Z = PC
        LPM     r4, Z+          ; r4 = word index
        MOVW    r2, r30         ; PC = Z
        LDI     r5, 5           ; 5 is sizeof word entries
        MUL     r4, r5
        ADD     r0, lo8(wtable)
        ADC     r1, hi8(wtable)
        MOVW    r30, r0         ; Z = CF of word
        IJMP                    ; which is a JMP instruction

;;; Here the first word of the PF points to the my FP, and the next byte
;;; in the PF has my num_args.  So the call to this word only takes one byte
;;; in the caller.
fixed_word_fixed_num_args:
        ADIW    r30, 3          ; advance Z to the PFA
        LPM     r0, Z+
        LPM     r31, Z
        MOV     r30, r0         ; Z now points to PF
        MOVW    r0, r26         ; r1:r0 = X
        LPM     r26, Z+
        LPM     r27, Z+         ; X now points to my FP
        ST      X+, r4          ; save ret FP
        ST      X+, r5
        ST      X+, r0          ; save old X in FP
        ST      X+, r1
        ST      X+, r6          ; save num_args in FP
        LPM     r6, Z+          ; r6 has my num_args
        MOVW    r4, r26         ; r5:r4 = X (FP)
        ST      X+, r30         ; save Z (PC) in FP
        ST      X+, r31
        ADIW    r26, 2          ; X += 2, skip over dynamic FP address
        JMP     next

;;; Here the first word of the PF points to the my FP, and the next byte in
;;; the caller has the num_args.  So the call to this word takes two bytes in
;;; the caller.
fixed_word_var_num_args:
        ADIW    r30, 3          ; advance Z to the PFA
        LPM     r0, Z+
        LPM     r31, Z
        MOV     r30, r0         ; Z now points to PF
        MOVW    r0, r26         ; r1:r0 = X
        LPM     r26, Z+
        LPM     r27, Z+         ; X now points to my FP
        ST      X+, r4          ; save ret FP
        ST      X+, r5
        ST      X+, r0          ; save old X in FP
        ST      X+, r1
        ST      X+, r6          ; save num_args in FP
        MOVW    r4, r26         ; r5:r4 = X (FP)
        ST      X+, r30         ; save Z (PC) in FP
        ST      X+, r31
        ADIW    r26, 2          ; X += 2, skip over dynamic FP address
        MOVW    r30, r2         ; Z = caller PC
        LPM     r6, Z+          ; r6 has my num_args
        MOVW    r2, r30         ; caller PC = Z
        ST      X+, r6          ; store num_args in my FP
        JMP     next

;;; Here the first word of the PF has my FP size, and the next byte in the PF
;;; has my num_args.  So the call to this word only takes one byte in the
;;; caller.
reentrant_word_fixed_num_args:
        ADIW    r30, 3          ; advance Z to the PFA
        LPM     r0, Z+
        LPM     r31, Z
        MOV     r30, r0         ; Z now points to PF
        MOVW    r0, r26         ; r1:r0 = X
        LD      r26, (Y+2)
        LD      r27, (Y+3)      ; X now points to my FP
        ST      X+, r4          ; save ret FP
        ST      X+, r5
        ST      X+, r0          ; save old X in FP
        ST      X+, r1
        ST      X+, r6          ; save num_args in FP
        MOVW    r4, r26         ; r5:r4 = X (FP)
        LPM     r0, Z+          ; r1:r0 = my FP size
        LPM     r1, Z+
        LPM     r6, Z+          ; r6 has my num_args
        ADD     r0, r30         ; r1:r0 += my FP, to get dyn FP addr
        ADC     r1, r31
        ST      X+, r30         ; save Z (PC) in FP
        ST      X+, r31
        ST      X+, r0          ; store FP size
        ST      X+, r1
        JMP     next

;;; Here the first word of the PF has my FP size, and the next byte in the
;;; caller has the num_args.  So the call to this word takes two bytes in the
;;; caller.
reentrant_word_var_num_args:
        ADIW    r30, 3          ; advance Z to the PFA
        LPM     r0, Z+
        LPM     r31, Z
        MOV     r30, r0         ; Z now points to PF
        MOVW    r0, r26         ; r1:r0 = X
        LD      r26, (Y+2)
        LD      r27, (Y+3)      ; X now points to my FP
        ST      X+, r4          ; save ret FP
        ST      X+, r5
        ST      X+, r0          ; save old X in FP
        ST      X+, r1
        ST      X+, r6          ; save num_args in FP
        MOVW    r4, r26         ; r5:r4 = X (FP)
        LPM     r0, Z+          ; r1:r0 = my FP size
        LPM     r1, Z+
        ADD     r0, r30         ; r1:r0 += my FP, to get dyn FP addr
        ADC     r1, r31
        ST      X+, r30         ; save Z (PC) in FP
        ST      X+, r31
        ST      X+, r0          ; store FP size
        ST      X+, r1
        MOVW    r30, r2         ; Z = caller PC
        LPM     r6, Z+          ; r6 has my num_args
        MOVW    r2, r30         ; caller PC = Z
        ST      X+, r6          ; store num_args in my FP
        JMP     next
