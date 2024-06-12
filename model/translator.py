import sys, json, re

from isa import Opcode, Variable, write_code, is_register, INPUT_PORT_ADDRESS, OUTPUT_PORT_ADDRESS, MIN_NUMBER, MAX_NUMBER, MEMORY_SIZE
from machine import Register

SECTION_DATA = "section .data:"
SECTION_TEXT = "section .text:"
START_LABEL = ".start"

def get_meaningful_token(line):
    return line.split(";", 1)[0].strip()

def clean_assembly_code(assembly_code):
    # удаление комментариев
    code_no_comments = re.sub(r';.*', '', assembly_code)
    # удаление пустых строк и лишних пробелов
    cleaned_code = '\n'.join(line.strip() for line in code_no_comments.split('\n') if line.strip())
    return cleaned_code

def is_jump_command(command):
    return command in [Opcode.JMP, Opcode.JZ, Opcode.JNZ, Opcode.JN, Opcode.JNN]

def remove_commas(args):
    new_args = []
    for arg in args:
        new_args.append(arg.rstrip(","))
    return new_args

def build_json_data(address, var_name, data):
    args = data
    return {"index": address, "name": var_name, "args": args}

def build_json_instruction(address, command, command_args):
    args = [None, None, None, None]
    if len(command_args) == 1:
        if is_jump_command(command):
            args[3] = command_args[0]
        else:
            args[0] = command_args[0]
    elif len(command_args) == 2:
        args[0] = command_args[0]
        if is_register(command_args[1]): #is 2nd arg register
            if command in [Opcode.ST.value, Opcode.LD.value]:
                args[3] = command_args[1]
            else:
                args[1] = command_args[1]
        else:
            args[3] = command_args[1]
    elif len(command_args) == 3:
        for i in range(3):
            args[i] = command_args[i]

    #return f'{{"index": {address}, "name": "{command}", "args": {args}}}'
    return {"index": address, "name": command, "args": args}

def translate_variables(variables, code):
    for _, variable in variables.items():
        # if var_name in ["in", "out"]:
            # code.append(build_json_data(variable.address, var_name + "_port", variable.data))
        if len(variable.data) > 1: # это строка
            address = variable.address
            for cell in variable.data:
                code.append(build_json_data(address, variable.name, [cell]))
                address += 1
        else: # другие переменные
            code.append(build_json_data(variable.address, variable.name, variable.data))
    return code

def translate_section_text_stage_1(section_text, address, code):
    labels = {}

    for _, token in enumerate(section_text.splitlines(), 1):
        token_args = token.split()
        command = token_args[0]
        command_args = token_args[1:]
        command_args = remove_commas(command_args)

        if token.endswith(":"): # токен содержит метку
            label_name = token.strip(":")
            assert label_name not in labels, f"Redefinition of label_name: {label_name}"
            labels[label_name] = address
        elif len(command_args) == 3: # арифметические команды
            is_all_regs = True
            for arg in command_args:
                if not is_register(arg):
                    is_all_regs = False
            assert is_all_regs == True, "Arithmetic commands only can take registers as arguments"
            code.append(build_json_instruction(address, command, command_args))
            address+=1
        elif len(command_args) == 2: #store, load or cmp, move
            if not is_register(command_args[1]): #store or load
                pass #do some checks
            code.append(build_json_instruction(address, command, command_args))
            address+=1
        elif len(command_args) == 1: #jmp, jz, jnz, jn, jnn or op4
            opcode = Opcode(command)
            if opcode == Opcode.CALL:
                code.extend([build_json_instruction(address, Opcode.DEC.value, [Register.SP.reg_name]),
                             build_json_instruction(address + 1, Opcode.ST.value, [Register.IP.reg_name, Register.SP.reg_name]),
                             build_json_instruction(address + 2, Opcode.JMP.value, [command_args[0]])])
                address += 3
                # dec sp
                # st ip, sp 
                # jump .loop
            elif opcode == Opcode.PUSH:
                # dec sp
                # st reg, sp
                code.extend([build_json_instruction(address, Opcode.DEC.value, [Register.SP.reg_name]),
                            build_json_instruction(address + 1, Opcode.ST.value, [command_args[0], Register.SP.reg_name])])
                address += 2
            elif opcode == Opcode.POP:
                # ld reg, sp
                # inc sp
                code.extend([build_json_instruction(address, Opcode.LD.value, [command_args[0], Register.SP.reg_name]),
                             build_json_instruction(address + 1, Opcode.INC.value, [Register.SP.reg_name])])
                address += 2
            else:
                code.append(build_json_instruction(address, command, command_args))
                address+=1
        elif len(command_args) == 0: #halt or ret
            opcode = Opcode(command)
            assert opcode in [Opcode.HALT, Opcode.RET], "Only `halt` or `ret` instructions take no arguments"
            if opcode == Opcode.HALT:
                code.append(build_json_instruction(address, command, command_args))
                address+=1
            else:
                # ld r, sp
                # inc sp
                # jmp r
                code.extend([build_json_instruction(address, Opcode.LD.value, [Register.RR.reg_name, Register.SP.reg_name]),
                             build_json_instruction(address + 1, Opcode.INC.value, [Register.SP.reg_name]),
                             build_json_instruction(address + 2, Opcode.JMP.value, [Register.RR.reg_name])])
                address += 3

    return labels, code

def translate_section_text_stage_2(labels, variables, code, section_text_address):
    # list(dict("index": integer, "name": Opcode, "args": list))

    for index, instruction in enumerate(code):
        if index > 0 and index < section_text_address: # пропускаем секцию .data
            continue
        # print(f"{instruction["index"], instruction["name"], instruction["args"]}")
        fourth_arg = instruction["args"][3]
        if fourth_arg is None:
            continue
        if fourth_arg.startswith("."):
            instruction["args"][3] = str(labels[fourth_arg])
        elif fourth_arg in variables.keys():
            instruction["args"][3] = str(variables[fourth_arg].data[0])
        code[index] = instruction
    return code

def is_integer(value: str) -> bool:
    return bool(re.fullmatch(r"^-?\d+$", value))

def is_string(value: str) -> bool:
    return bool(re.fullmatch(r"^(\".*\")|(\'.*\')$", value))

def translate_section_data(section_data):
    variables = {
        "in": Variable("input_port", INPUT_PORT_ADDRESS, [0]),
        "out": Variable("output_port", OUTPUT_PORT_ADDRESS, [0]),
    }
    reference_variables = {}
    address = 3

    def parse_line(line):
        name, value = map(str.strip, line.split(":", 1))
        return name, value

    def handle_integer(name, value):
        value = int(value)
        assert MIN_NUMBER <= value <= MAX_NUMBER, f"Value {value} is out of bound"
        variables[name] = Variable(name, address, [value])
        return 1

    def handle_string(name, value):
        chars = [ord(char) for char in value[1:-1]] + [0]
        variables[name] = Variable(name, address, chars)
        return len(chars)

    def handle_buffer(name, value):
        size = int(value.split(" ", 1)[1])
        variables[name] = Variable(name, address, [0] * size)
        return size

    def handle_reference(name, value):
        variables[name] = Variable(name, address, [0])
        reference_variables[name] = value
        return 1

    handlers = {
        'integer': handle_integer,
        'string': handle_string,
        'buffer': handle_buffer,
        'reference': handle_reference
    }

    def get_value_type(value):
        if is_integer(value):
            return 'integer'
        elif is_string(value):
            return 'string'
        elif value.startswith("bf"):
            return 'buffer'
        else:
            return 'reference'

    for line in section_data.splitlines():
        name, value = parse_line(line)
        value_type = get_value_type(value)
        address += handlers[value_type](name, value)

    for reference_name, target_name in reference_variables.items():
        variables[reference_name].data = [variables[target_name].address]

    assert address < MEMORY_SIZE, "This program is too big for processor's memory"

    return variables, address

def translate(source):
    section_data_index = source.find(SECTION_DATA)
    section_text_index = source.find(SECTION_TEXT)
    section_data = source[section_data_index + len(SECTION_DATA) + 1 : section_text_index]
    section_text = source[section_text_index + len(SECTION_TEXT) + 1 :]

    variables, section_text_address = translate_section_data(section_data)

    # for name, value in variables.items():
    #     print(f"{name}={value.data}")

    code = []
    code.append(build_json_instruction(0, Opcode.JMP.value, [START_LABEL])) #add jmp instruction on program beginning

    code = translate_variables(variables, code)
    labels, code = translate_section_text_stage_1(section_text, section_text_address, code)
    code = translate_section_text_stage_2(labels, variables, code, section_text_address)
    
    for line in code:
        print(line)

    json_code = json.dumps(code, indent=4)

    return json_code, section_text_address


def main(source, target):
    with open(source, encoding="utf-8") as f:
        source = f.read()

    source = clean_assembly_code(source)
    code, section_text_address = translate(source)

    write_code(target, code)
    print("source LoC:", len(source.split("\n")), "code instr:", len(code.split("{")) - section_text_address)


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
