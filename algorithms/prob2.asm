section .data:
    LIMIT_VALUE: 4000000
    DIVIDER: 2
section .text:
    .start:
        li r4, 0            ; sum of even-valued terms

        li r0, 1            ; first fib value
        mov r1, r0          ; save to r1 for function
        call .sum_if_even
        li r1, 2            ; second fib value
                            ; r3 - even or odd
        call .sum_if_even

    .loop:
        add r2, r1, r0
        mov r0, r1
        mov r1, r2
        
        li r5, LIMIT_VALUE
        cmp r1, r5
        jz .end             ; if term > 4000000 go to halt
        call .sum_if_even
        jmp .loop
    
    .end:
        ; output r4 ; set output cell, expected answer = 4613732
        call .print_int
        halt

    .sum_if_even:
        li r5, DIVIDER
        mod r3, r1, r5      ; check if r3 % 2
        li r6, 0
        cmp r3, r6          ; r3 == 0 ?
        jnz .quit           ; if no - skip operation
        add r4, r4, r1      ; if yes - update sum
    .quit:
        ret

    .print_int:             ; print sequetially each symbol in number
                            ; 4613732 -> 4 6 1 3 7 3 2
        li r0, 1            ; number for separation, each iteration it will be devided by 10
        li r2, 10           ; divider and multiplier for r0 number
                            ; r4 - result

        .sep_loop:          ; build r0 number, it should have same amout of digits as in the result 
            mul r0, r0, r2  ; r0 *= 10
            cmp r4, r0      ; r4 - r0 = ?
            jnn .sep_loop   ; if r4 - r0 >= 0: continue looping
        div r0, r0, r2      ; r0 correction

        li r1, 48           ; for translation in ASCII
                            ; r3 - use for symbol code, will be printed

        .loop1:
            div r3, r4, r0 ; r3 = r4 / r0 -> get left digit of number
            add r3, r3, r1 ; r4 += 48 -> to ASCII code
            mod r4, r4, r0 ; r4 %= r0 -> remove first digit
            div r0, r0, r2 ; r0 /= 10
            output r3
            li r5, 0       ; for comparison r0
            cmp r0, r5
            jz .quit_print_int  ; if r0 == 0: end cycle and function
            jmp .loop1
        .quit_print_int:
            ret