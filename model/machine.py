from enum import Enum
from isa import MEMORY_SIZE, Opcode, read_code, MAX_NUMBER, MIN_NUMBER
import logging, sys

REGISTER_AMOUNT = 8
INSTRUCTION_LIMIT = 2000

class Signal:
    NEXT_IP = "next ip"
    JMP_ARG = "jmp arg"
    DATA_IP = "data ip"

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
    Opcode.MOV: lambda left: left,
    Opcode.ST: lambda left: left,   # поместить значение адреса на главную шину
    Opcode.LD: lambda left: left    # поместить значение адреса на главную шину
}

# class RegiterFile:
#     def __init__(self):
#         self.R0 = 0
#         self.R1 = 0
#         self.R2 = 0
#         self.R3 = 0
#         self.R4 = 0
#         self.R5 = 0
#         self.R6 = 0
#         self.R7 = 0

class ALU:
    z_flag = None
    n_flag = None

    def __init__(self):
        self.z_flag = 0
        self.n_flag = 0
    
    def process(self, left: int, right: int, opcode: Opcode) -> int:
        assert (
            opcode in ALU_OPCODE_BINARY_HANDLERS or opcode in ALU_OPCODE_SINGLE_HANDLERS
        ), f"Unknown ALU command {opcode.value}"
        
        if opcode in ALU_OPCODE_BINARY_HANDLERS:
            handler = ALU_OPCODE_BINARY_HANDLERS[opcode]
            value = handler(left, right)
        else:
            handler = ALU_OPCODE_SINGLE_HANDLERS[opcode]
            value = handler(left)
        value = self.handle_overflow(value)
        self.set_flags(value)
        return value
    
    def handle_overflow(self, value: int) -> int:
        if value > MAX_NUMBER:
            value %= MAX_NUMBER
        elif value < MIN_NUMBER:
            value %= abs(MIN_NUMBER)
        return value

    def set_flags(self, value) -> None:
        self.z_flag = (value == 0)
        self.n_flag = (value < 0)

class DataPath:
    input_buffer = None
    output_buffer = None
    memory = None

    def __init__(self, memory, input_buffer):
        self.memory = memory
        self.memory_out = 0

        self.registers = [0] * REGISTER_AMOUNT
        self.sp = 0
        self.ar = 0

        self.alu = ALU()

        self.input_buffer = input_buffer
        self.output_buffer = []

        """
        main_bus обновляется значениями:
            1) Из выхода АЛУ
            2) При чтении данных из памяти
            3) При прямой загрузке данных
        """
        self.main_bus = 0

    def is_zero(self):
        return self.alu.z_flag
    
    def is_negative(self):
        return self.alu.n_flag

    def signal_latch_register(self, sel):
        pass

    def signal_read(self, sel):
        pass

    def signal_write(self, sel):
        pass

class ControlUnit:
    def __init__(self, memory, data_path):
        self.ip = 0
        self.memory = memory
        self.data_path = data_path
        self._tick = 0
    
    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick
    
    def signal_latch_ip(self, sel_next):
        if sel_next:
            self.ip += 1
        else:
            instr = self.memory[self.ip]
            address = int(instr["args"][3])
            self.ip = address

    def decode_and_execute_control_flow_instruction(self, instr, opcode):
        if opcode is Opcode.HALT:
            raise StopIteration()

        flow_instructions = {
            Opcode.JMP: lambda: (self.signal_latch_ip(sel_next=False)),
            Opcode.JZ: lambda: (self.signal_latch_ip(sel_next=not self.data_path.is_zero())),
            Opcode.JNZ: lambda: (self.signal_latch_ip(sel_next=self.data_path.is_zero())),
            Opcode.JN: lambda: (self.signal_latch_ip(sel_next=not self.data_path.is_negative())),
            Opcode.JNN: lambda: (self.signal_latch_ip(sel_next=self.data_path.is_negative())),
        }

        if opcode in flow_instructions:
            flow_instructions[opcode]()
            self.tick()
            return True
        
        return False

    def decode_and_execute_instruction(self):
        instr = self.memory[self.ip]
        opcode = Opcode(instr["name"])

        if self.decode_and_execute_control_flow_instruction(instr, opcode):
            return
        
        # decode other commmands


    def __repr__(self):
        pass

def simulation(memory, input_tokens):
    data_path = DataPath(memory, input_tokens)
    control_unit = ControlUnit(memory, data_path)
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
    memory = read_code(code_file)

    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)
    
    output, instr_counter, ticks = simulation(memory, input_tokens=input_token)

    print("".join(output))
    print("instr_counter: ", instr_counter, "ticks: ", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
