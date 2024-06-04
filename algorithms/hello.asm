section .data:
    greeting: "Hello World!"
    ptr: greeting

section .text:
    .start:
        li r1, ptr ; save address of first character in string
    .loop:
        load r0, r1 ; get character by address in register
        jz .end ; if it's 0-terminator, finish the programm
        output r0
        inc r1
        jmp .loop
    .end:
        halt