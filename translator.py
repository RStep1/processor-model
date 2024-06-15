import re
import sys

from isa import (
    INPUT_PORT_ADDRESS,
    MAX_NUMBER,
    MEMORY_SIZE,
    MIN_NUMBER,
    OUTPUT_PORT_ADDRESS,
    Opcode,
    Variable,
    is_register,
    write_code,
)
from machine import Register, is_jump_command

SECTION_DATA = "section .data:"
SECTION_TEXT = "section .text:"
START_LABEL = ".start"


def get_meaningful_token(line):
    return line.split(";", 1)[0].strip()


def clean_assembly_code(assembly_code):
    # удаление комментариев
    code_no_comments = re.sub(r";.*", "", assembly_code)
    # удаление пустых строк и лишних пробелов
    return "\n".join(line.strip() for line in code_no_comments.split("\n") if line.strip())


def remove_commas(args):
    new_args = []
    for arg in args:
        new_args.append(arg.rstrip(","))
    return new_args


def build_json_data(address, var_name, data):
    args = data
    return {"index": address, "name": var_name, "args": args}


def build_json_0_args(args, _, __):
    return args


def build_json_1_args(args, command, command_args):
    if len(command_args) == 1:
        if is_jump_command(command):
            args[3] = command_args[0]
        else:
            args[0] = command_args[0]
    return args


def build_json_2_args(args, command, command_args):
    args[0] = command_args[0]
    if is_register(command_args[1]):  # is 2nd arg register
        if command in [Opcode.ST.value, Opcode.LD.value]:
            args[3] = command_args[1]
        else:
            args[1] = command_args[1]
    else:
        args[3] = command_args[1]
    return args


def build_json_3_args(args, _, command_args):
    for i in range(3):
        args[i] = command_args[i]
    return args


def build_json_instruction(address, command, command_args):
    arg_handlers = [
        build_json_0_args,
        build_json_1_args,
        build_json_2_args,
        build_json_3_args,
    ]

    args = [None, None, None, None]
    arg_handlers[len(command_args)](args, command, command_args)

    return {"index": address, "name": command, "args": args}


def translate_variables(variables, code):
    for _, variable in variables.items():
        if len(variable.data) > 1:  # это строка или буфер
            address = variable.address
            for cell in variable.data:
                code.append(build_json_data(address, variable.name, [cell]))
                address += 1
        else:  # другие переменные
            code.append(build_json_data(variable.address, variable.name, variable.data))
    return code

def translate_3_args_command(address, command, command_args, code):
    is_all_regs = True
    for arg in command_args:
        if not is_register(arg):
            is_all_regs = False
    assert is_all_regs is True, "Arithmetic commands only can take registers as arguments"
    code.append(build_json_instruction(address, command, command_args))
    address += 1
    return address, code

def translate_2_args_command(address, command, command_args, code):
    code.append(build_json_instruction(address, command, command_args))
    address += 1
    return address, code

def translate_1_args_command(address, command, command_args, code):
    opcode = Opcode(command)
    match opcode:
        case Opcode.CALL:
            code.extend(
                [
                    build_json_instruction(address, Opcode.DEC.value, [Register.SP.reg_name]),
                    build_json_instruction(
                        address + 1, Opcode.ST.value, [Register.IP.reg_name, Register.SP.reg_name]
                    ),
                    build_json_instruction(address + 2, Opcode.JMP.value, [command_args[0]]),
                ]
            )
            address += 3
        case Opcode.PUSH:
            code.extend(
                [
                    build_json_instruction(address, Opcode.DEC.value, [Register.SP.reg_name]),
                    build_json_instruction(address + 1, Opcode.ST.value, [command_args[0], Register.SP.reg_name]),
                ]
            )
            address += 2
        case Opcode.POP:
            code.extend(
                [
                    build_json_instruction(address, Opcode.LD.value, [command_args[0], Register.SP.reg_name]),
                    build_json_instruction(address + 1, Opcode.INC.value, [Register.SP.reg_name]),
                ]
            )
            address += 2
        case _:
            code.append(build_json_instruction(address, command, command_args))
            address += 1
    return address, code

def translate_0_args_command(address, command, command_args, code):
    opcode = Opcode(command)
    assert opcode in [Opcode.HALT, Opcode.RET], "Only `halt` or `ret` instructions take no arguments"
    if opcode == Opcode.HALT:
        code.append(build_json_instruction(address, command, command_args))
        address += 1
    else:
        code.extend(
            [
                build_json_instruction(address, Opcode.LD.value, [Register.RR.reg_name, Register.SP.reg_name]),
                build_json_instruction(address + 1, Opcode.INC.value, [Register.SP.reg_name]),
                build_json_instruction(address + 2, Opcode.INC.value, [Register.RR.reg_name]),
                build_json_instruction(address + 3, Opcode.INC.value, [Register.RR.reg_name]),
                build_json_instruction(address + 4, Opcode.JMP.value, [Register.RR.reg_name]),
            ]
        )
        address += 5
    return address, code

def translate_section_text_stage_1(section_text, address, code):
    labels = {}

    for _, token in enumerate(section_text.splitlines(), 1):
        token_args = token.split()
        command = token_args[0]
        command_args = token_args[1:]
        command_args = remove_commas(command_args)

        if token.endswith(":"):  # токен содержит метку
            label_name = token.strip(":")
            assert label_name not in labels, f"Redefinition of label_name: {label_name}"
            labels[label_name] = address
            continue

        match len(command_args):
            case 3:
                address, code = translate_3_args_command(address, command, command_args, code)
            case 2:
                address, code = translate_2_args_command(address, command, command_args, code)
            case 1:
                address, code = translate_1_args_command(address, command, command_args, code)
            case 0:
                address, code = translate_0_args_command(address, command, command_args, code)

    return labels, code


def translate_section_text_stage_2(labels, variables, code, section_text_address):
    for index, instruction in enumerate(code):
        if index != 0 and index < section_text_address:
            continue  # пропускаем секцию .data и первую инструкцию
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


def parse_line(line):
    name, value = map(str.strip, line.split(":", 1))
    return name, value

def get_variable_type(value):
    if is_integer(value):
        return "integer"
    if is_string(value):
        return "string"
    if value.startswith("bf"):
        return "buffer"
    return "reference"

def translate_section_data(section_data):
    variables = {
        "in": Variable("input_port", INPUT_PORT_ADDRESS, [0]),
        "out": Variable("output_port", OUTPUT_PORT_ADDRESS, [0]),
    }
    reference_variables = {}
    address = 3

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
        "integer": handle_integer,
        "string": handle_string,
        "buffer": handle_buffer,
        "reference": handle_reference,
    }

    for line in section_data.splitlines():
        name, value = parse_line(line)

        value_type = get_variable_type(value)
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

    code = []
    # добавляем инструкцию безусловного перехода на начало программы в нулевую ячейку памяти
    code.append(build_json_instruction(0, Opcode.JMP.value, [START_LABEL]))

    code = translate_variables(variables, code)
    labels, code = translate_section_text_stage_1(section_text, section_text_address, code)
    code = translate_section_text_stage_2(labels, variables, code, section_text_address)

    return code, section_text_address


def main(source, target):
    with open(source, encoding="utf-8") as f:
        source = f.read()

    source = clean_assembly_code(source)
    code, section_text_address = translate(source)

    write_code(target, code)
    print("source LoC:", len(source.split("\n")), "code instr:", len(code) - section_text_address + 1)


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
