import json
from enum import Enum

MEMORY_SIZE = 2048
MAX_NUMBER = 1 << 31 - 1
MIN_NUMBER = -(1 << 31)
INPUT_PORT_ADDRESS = 1
OUTPUT_PORT_ADDRESS = 2


class Register(Enum):
    R0 = "r0"
    R1 = "r1"
    R2 = "r2"
    R3 = "r3"
    R4 = "r4"
    R5 = "r5"
    R6 = "r6"
    R7 = "r7"
    IP = "ip"
    SP = "sp"
    RR = "rr"  # return register

    def __init__(self, reg_name: str):
        self.reg_name = reg_name

    def __str__(self):
        return f"{self.reg_name}"


def is_register(arg):
    return any(arg == register.value for register in Register)


def build_register_object(reg_name):
    return Register(reg_name)


def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        for arg in instr["args"]:
            if is_register(arg):
                arg_idx = instr["args"].index(arg)
                code[instr["index"]]["args"][arg_idx] = build_register_object(arg)

    return code


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as f:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        f.write("[" + ",\n ".join(buf) + "]")


class Variable:
    def __init__(self, name, address, data):
        self.name = name
        self.address = address
        self.data = data


class Opcode(str, Enum):
    INC = "inc"
    DEC = "dec"
    LD = "ld"
    LI = "li"
    ST = "store"
    IN = "input"
    OUT = "output"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    JMP = "jmp"
    JZ = "jz"
    JNZ = "jnz"
    JN = "jn"
    JNN = "jnn"
    CMP = "cmp"
    HALT = "halt"
    MOV = "mov"
    CALL = "call"
    RET = "ret"
    PUSH = "push"
    POP = "pop"

    def __str__(self):
        return str(self.value)
