section .data:
    greeting: "Hello World!"
    ptr: greeting

section .text:
    .loop:
        load r0, ptr
        jz .end
        output r0
        inc ptr
        jmp .loop
    .end:
        halt