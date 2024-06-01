section .data:
    LIMIT_VALUE: 4000000
    DIVIDER: 2
section .text:
    start:
        li r4, 0 ; sum of even-valued terms

        li r0, 1 ; first fib value
        mov r1, r0 ; save to r1 for function
        call sum_if_even
        li r1, 2 ; second fib value
                    ; r3 - even or odd
        call sum_if_even

    loop:
        add r2, r1, r0
        mov r0, r1
        mov r1, r2
        
        li r5, LIMIT_VALUE
        cmp r1, r5
        jz end ; if term > 4000000 go to halt
        call sum_if_even
        jmp loop
    
    end:
        out r4 ; set output cell, expected answer = 4613732
        halt

    sum_if_even:
        li r5, DEVIDER
        mod r3, r1, r5 ; check if r3 % 2
        jnz quit ;if no - skip operation
        add r4, r4, r1 ; if yes - update sum
    quit:
        ret