section .data:
    greeting: "Hello World!"
    ptr: greeting

section .text:
    .start:
        li r1, ptr  ; save address of first character in string
        li r2, 0    ; for comparison
    .loop:
        ld r0, r1   ; get character by address in register
        cmp r0, r2
        jz .end     ; if it's 0-terminator, finish the program
        output r0
        inc r1
        jmp .loop
    .end:
        halt