from enum import Enum
from isa import MEMORY_SIZE, Opcode, Register, read_code, MAX_NUMBER, MIN_NUMBER
import logging, sys

REGISTER_AMOUNT = 8
INSTRUCTION_LIMIT = 200
    
GENERAL_PURPOSE_REGISTERS = [Register.R0, Register.R1, Register.R2, Register.R3,
                             Register.R4, Register.R5, Register.R6, Register.R7]

class ALU:
    z_flag = None
    n_flag = None

    def __init__(self):
        self.z_flag = 0
        self.n_flag = 0

    alu_opcode_binary_handlers = {
    Opcode.ADD: lambda left, right: int(left + right),
    Opcode.SUB: lambda left, right: int(left - right),
    Opcode.MUL: lambda left, right: int(left * right),
    Opcode.DIV: lambda left, right: int(left / right),
    Opcode.MOD: lambda left, right: int(left % right),
    Opcode.CMP: lambda left, right: int(left - right),
    }

    alu_opcode_unary_handlers = {
        Opcode.INC: lambda left: left + 1,
        Opcode.DEC: lambda left: left - 1,
        Opcode.MOV: lambda left: left,
        Opcode.LD: lambda left: left,    # поместить значение адреса на главную шину, выставить флаги
    }
    
    def process(self, left: int, right: int, opcode: Opcode) -> int:
        assert (
            opcode in self.alu_opcode_binary_handlers or opcode in self.alu_opcode_unary_handlers
        ), f"Unknown ALU command {opcode.value}"
        
        if opcode in self.alu_opcode_binary_handlers:
            handler = self.alu_opcode_binary_handlers[opcode]
            value = handler(left, right)
        else:
            handler = self.alu_opcode_unary_handlers[opcode]
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
        self.z_flag = value == 0
        self.n_flag = value < 0

class DataPath:
    input_buffer = None
    output_buffer = None
    memory = None

    def __init__(self, memory, input_buffer):
        self.memory = memory

        self.registers = [0] * REGISTER_AMOUNT
        self.sp = MEMORY_SIZE - 1
        self.ar = 0
        self.ip = 0

        self.alu = ALU()

        self.input_buffer = input_buffer
        self.output_buffer = []

        """
        main_bus обновляется значениями:
            1) Из выхода АЛУ
            2) При чтении данных из памяти
            3) При прямой прямой загрузке данных
        """
        self.main_bus = 0

    def is_zero(self):
        return self.alu.z_flag
    
    def is_negative(self):
        return self.alu.n_flag

    def signal_read_memory(self, address):
        return self.memory[address]

    def signal_write_memory(self, value):
        self.memory[self.ar] = value

    def signal_latch_register(self, register, value):
        if register is Register.SP:
            self.sp = value
        elif register is Register.IP:
            self.ip = value
        elif register in GENERAL_PURPOSE_REGISTERS:
            index = GENERAL_PURPOSE_REGISTERS.index(register)
            self.registers[index] = value

    def sel_register(self, register):
        if register is Register.SP:
            return self.sp
        elif register is Register.IP:
            return self.ip
        elif register in GENERAL_PURPOSE_REGISTERS:
            index = GENERAL_PURPOSE_REGISTERS.index(register)
            return self.registers[index]

class ControlUnit:
    def __init__(self, memory, data_path):
        # self.ip = 0
        self.memory = memory
        self.data_path = data_path
        self._tick = 0
        self.instruction_executors = {
            Opcode.INC: self.execute_unary_math_instruction,
            Opcode.DEC: self.execute_unary_math_instruction,
            Opcode.LD:  self.execute_load,
            Opcode.LI:  self.execute_load_immediately,
            Opcode.ST:  self.execute_store,
            Opcode.IN:  self.execute_input,
            Opcode.OUT: self.execute_output,
            Opcode.ADD: self.execute_binary_math_instruction,
            Opcode.SUB: self.execute_binary_math_instruction,
            Opcode.MUL: self.execute_binary_math_instruction,
            Opcode.DIV: self.execute_binary_math_instruction,
            Opcode.MOD: self.execute_binary_math_instruction,
            Opcode.CMP: self.execute_cmp,
            Opcode.MOV: self.execute_mov,
        }
    
    def execute_binary_math_instruction(self, opcode, args):
        left_reg = args[1]
        right_reg = args[2]
        left = self.data_path.sel_register(left_reg)
        right = self.data_path.sel_register(right_reg)
        alu_out = self.data_path.alu.process(left, right, opcode)
        self.data_path.main_bus = alu_out
        self.tick()

        res_reg = args[0]
        self.data_path.signal_latch_register(res_reg, self.data_path.main_bus)
        self.tick()

    def execute_unary_math_instruction(self, opcode):
        pass

    def execute_load(self, opcode):
        pass

    def execute_load_immediately(self, opcode):
        pass

    def execute_store(self, opcode):
        pass

    def execute_cmp(self, opcode):
        pass

    def execute_input(self, opcode):
        pass

    def execute_output(self, opcode):
        pass

    def execute_mov(self):
        pass
    
    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick
    
    def signal_latch_ip(self, sel_next):
        if sel_next:
            self.data_path.ip += 1
        else:
            instr = self.memory[self.data_path.ip]
            address = int(instr["args"][3])
            self.data_path.ip = address

    def decode_and_execute_control_flow_instruction(self, opcode):
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
        instr = self.data_path.signal_read_memory(self.data_path.ip)
        self.tick()
        opcode = Opcode(instr["name"])
        args = instr["args"]

        if self.decode_and_execute_control_flow_instruction(opcode):
            return
                    
        instruction_executor = self.instruction_executors[opcode]
        instruction_executor(opcode, args)

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
    # for cell in memory:
    #     print(cell)
    for index in range(len(memory), MEMORY_SIZE): # дополняем память пустыми ячейками до предела
        memory.append({"index": index, "name": "", "args": []})

    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)
    
    output, instr_counter, ticks = "", 0, 0 #simulation(memory, input_tokens=input_token)

    print("".join(output))
    print("instr_counter: ", instr_counter, "ticks: ", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
