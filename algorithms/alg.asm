section .data:
section .text:
    .start:
        li r0, 100
        call .func
        halt

    .func:
        li r0, 74
        output r0
        ret