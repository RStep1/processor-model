from enum import Enum
import json

MEMORY_SIZE = 2048
MAX_NUMBER = 1 << 31 - 1
MIN_NUMBER = -(1 << 31)
INPUT_PORT_ADDRESS = 1
OUTPUT_PORT_ADDRESS = 2

def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())
    return code

def write_code(filename: str, code: str):
    with open(filename, mode="bw") as f:
        f.write(code.encode("utf-8"))

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
