from enum import Enum
from isa import MEMORY_SIZE, Opcode, read_code
import logging, sys

REGISTER_AMOUNT = 8
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
    
    IP = (0, "ip")
    SP = (MEMORY_SIZE - 1, "sp")
    CR = (0, "cr")
    AR = (0, "ar")

    def __init__(self, reg_value: int, reg_name: str):
        self.reg_value = reg_value
        self.reg_name = reg_name

    def __str__(self):
        return f"{self.reg_name}={self.reg_value}"

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

class DataPath:
    pass

class ALU:
    z_flag = None

    def __init__(self):
        self.z_flag = 0
    
    def process(self, left: int, right: int, opcode: Opcode) -> int:
        pass
    

class ControlUnit:
    program = None

    pass

def simualtion(code, input_tokens):
    data_path = DataPath(code)
    control_unit = ControlUnit(data_path)
    instr_counter = 0

    logging.debug("%s", control_unit)
    try:
        while instr_counter < INSTRUCTION_LIMIT:
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if instr_counter >= INSTRUCTION_LIMIT:
        logging.warning("Limit exceeded!")
    logging.info("output_buffer: %s", repr("".join(data_path.output_buffer)))
    return "".join(data_path.output_buffer), instr_counter, control_unit.current_tick()

def main(code_file, input_file):
    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    output, instr_counter = simulation(
        code,
        input_tokens=input_token,
        limit=INSTRUCTION_LIMIT,
    )

    print("".join(output))
    print("instr_counter: ", instr_counter)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
