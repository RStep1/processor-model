import sys, json

from isa import Opcode, write_code
from machine import Register

SECTION_DATA = "section .data:"
SECTION_TEXT = "section .text:"


def get_meaningful_token(line):
    return line.split(";", 1)[0].strip()

def is_register(arg):
    return arg.startswith("r")

def is_jump_command(command):
    return command in [Opcode.JMP, Opcode.JZ, Opcode.JNZ]

def remove_commas(args):
    new_args = []
    for arg in args:
        new_args.append(arg.rstrip(","))
    return new_args

def build_json_instruction(pc, command, command_args):
    args = [None, None, None, None]
    if len(command_args) == 1:
        if is_jump_command(command):
            args[3] = command_args[0]
        else:
            args[0] = command_args[0]
    elif len(command_args) == 2:
        args[0] = command_args[0]
        if is_register(command_args[1]): #is 2nd arg is register
            args[1] = command_args[1]
        else:
            args[3] = command_args[1]
    elif len(command_args) == 3:
        for i in range(3):
            args[i] = command_args[i]

    #return f'{{"index": {pc}, "opcode": "{command}", "args": {args}}}'
    return {"index": pc, "opcode": command, "args": args}


def translate_stage_1(text):
    code = []
    labels = {}

    for line_num, raw_line in enumerate(text.splitlines(), 1):
        token = get_meaningful_token(raw_line)
        if token == "":
            continue

        pc = len(code)

        token_args = token.split()
        command = token_args[0]
        command_args = token_args[1:]
        command_args = remove_commas(command_args)

        if token.endswith(":"): # токен содержит метку
            label_name = token.strip(":")
            assert label_name not in labels, "Redefinition of label_name: {}".format(label_name)
            labels[label_name] = pc
        elif len(command_args) == 3: # арифметические команды
            is_all_regs = True
            for arg in command_args:
                if not is_register(arg):
                    is_all_regs = False
            assert is_all_regs == True, "Arithmetic commands only can take registers as argumens"
            code.append(build_json_instruction(pc, command, command_args))
        elif len(command_args) == 2: #store, load or cmp, move
            if not is_register(command_args[1]): #store or load
                pass #do some checks
            code.append(build_json_instruction(pc, command, command_args))
        elif len(command_args) == 1: #jmp, jz, jnz or op4
            opcode = Opcode(command)
            if opcode == Opcode.CALL:
                code.append(build_json_instruction(pc, Opcode.DEC.value, [Register.SP.reg_name]))
                pc+=1
                code.append(build_json_instruction(pc, Opcode.ST.value, [Register.IP.reg_name, Register.SP.reg_name]))
                pc+=1
                code.append(build_json_instruction(pc, Opcode.LI.value, [Register.IP.reg_name, command_args[0]]))
                pc+=1
                # dec sp
                # st ip, sp 
                # li ip, .loop
            elif opcode == Opcode.PUSH:
                # dec sp
                # st reg, sp
                code.append(build_json_instruction(pc, Opcode.DEC.value, [Register.SP.reg_name]))
                pc+=1
                code.append(build_json_instruction(pc, Opcode.ST.value, [command_args[0], Register.SP.reg_name]))
                pc+=1
            elif opcode == Opcode.POP:
                # ld reg, sp
                # inc sp
                code.append(build_json_instruction(pc, Opcode.LD.value, [command_args[0], Register.SP.reg_name]))
                pc+=1
                code.append(build_json_instruction(pc, Opcode.INC.value, [Register.SP.reg_name]))
            else:
                code.append(build_json_instruction(pc, command, command_args))
        elif len(command_args) == 0: #halt or ret
            opcode = Opcode(command)
            assert opcode in [Opcode.HALT, Opcode.RET], "Only `halt` or `ret` instructions take no arguments"
            if opcode == Opcode.HALT:
                code.append(build_json_instruction(pc, command, command_args))
            else:
                # ld ip, sp
                # inc sp
                code.append(build_json_instruction(pc, Opcode.LD.value, [Register.IP.reg_name, Register.SP.reg_name]))
                pc+=1
                code.append(build_json_instruction(pc, Opcode.INC.value, [Register.SP.reg_name]))
                pc+=1            

    return labels, code


def translate_stage_2(labels, code):
    # for instruction in code:
    #     if "arg" in instruction:
    #         label_name = instruction["arg"]
    #         assert label_name in labels, "label_name not defined: " + label_name
    #         instruction["arg"] = labels[label_name]
    return code


def translate(text):
    labels, code = translate_stage_1(text)
    code = translate_stage_2(labels, code)
    
    for line in code:
        print(line)

    json_code = json.dumps(code, indent=4)

    return json_code


def main(source, target):
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translate(source)

    write_code(target, code)
    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)