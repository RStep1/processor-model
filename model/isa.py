from enum import Enum
import json

MEMORY_SIZE = 1024
MAX_NUMBER = 1 << 31 - 1
MIN_NUMBER = -(1 << 31)
INPUT_PORT_ADDRESS = 0
OUTPUT_PORT_ADDRESS = 1

def write_code(filename: str, code: str):
    with open(filename, mode="bw") as f:
        f.write(code.encode("utf-8"))

class Variable:
    def __init__(self, name, address, data, is_string):
        self.name = name
        self.address = address
        self.data = data
        self.is_string = is_string

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
    CMP = "cmp"
    ASL = "asl"
    HALT = "halt"
    MOV = "mov"
    CALL = "call"
    RET = "ret"
    PUSH = "push"
    POP = "pop"
    

    def __str__(self):
        return str(self.value)


class Command:
    def __init__(self, opcode: Opcode, operand=None):
        self.opcode = opcode
        self.operand = operand
    
def read_opcode(filename):
    '''
    Read machine code from file
    '''

def write_opcode(filename):
    ''' 
    Write machinde code into file
    '''

