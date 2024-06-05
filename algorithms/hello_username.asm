section .data:
    username: bf 40
    request: "What is your name?"
    greeting: "Hello, "
    username_ptr: username
    request_ptr: request
    greeting_ptr: greeting

section .text:
    .start:
        li r1, request_ptr ; print request
        call .print_string
        call .new_line

        call .input_username ; user input

        li r1, greeting_ptr ; print 'Hello, '
        call .print_string

        li r1, username_ptr ; print username
        call .print_string
        call .new_line

        halt

    .input_username:
        li r1, username_ptr
        .loop2:
            input r0
            jz .end_input
            store r0, r1
            inc r1
            jmp .loop2
        .end_input:
            ret

    .print_string: ; r1 - pointer on str
        .loop:
            ld r0, r1
            output r0
            jz .end
            inc r1
            jmp .loop
        .end:
            ret

    .new_line:
        li r0, 10
        output r0
        ret
