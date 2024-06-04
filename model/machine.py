from enum import Enum
from isa import MEMORY_SIZE, Opcode

REGISTER_AMOUNT = 4
INSTRUCTION_LIMIT = 2000

class Register(Enum):
    R0 = (0, "r0")
    R1 = (0, "r1")
    R2 = (0, "r2")
    R3 = (0, "r3")
    R4 = (0, "r4")
    R5 = (0, "r5")
    R6 = (0, "r6")
    R7 = (0, "r7")
    R8 = (0, "r8")
    
    IP = (0, "ip")
    SP = (MEMORY_SIZE - 1, "sp")
    CR = (0, "cr")
    AR = (0, "ar")

    def __init__(self, reg_value: int, reg_name: str):
        self.reg_value = reg_value
        self.reg_name = reg_name

    def __str__(self):
        return f"{self.reg_name}={self.reg_value}"
    
    INSTRUCTION_LIMIT = 1500

ALU_OPCODE_BINARY_HANDLERS = {
    Opcode.ADD: lambda left, right: int(left + right),
    Opcode.SUB: lambda left, right: int(left - right),
    Opcode.MUL: lambda left, right: int(left * right),
    Opcode.DIV: lambda left, right: int(left / right),
    Opcode.MOD: lambda left, right: int(left % right),
    Opcode.CMP: lambda left, right: int(left - right),
}

ALU_OPCODE_SINGLE_HANDLERS = {
    Opcode.INC: lambda left: left + 1,
    Opcode.DEC: lambda left: left - 1,
}