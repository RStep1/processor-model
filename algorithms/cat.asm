section .data:
section .text:
    .start:
        li r1, 0 ; for comparation
    .loop:
        input r0
        cmp r0, r1
        jz .end
        output r0
        jmp .loop
    .end:
        halt