from enum import Enum
from isa import MEMORY_SIZE, Opcode, Register, read_code, MAX_NUMBER, MIN_NUMBER, INPUT_PORT_ADDRESS, OUTPUT_PORT_ADDRESS
import logging, sys

REGISTER_AMOUNT = 8
INSTRUCTION_LIMIT = 200

GENERAL_PURPOSE_REGISTERS = [Register.R0, Register.R1, Register.R2, Register.R3,
                             Register.R4, Register.R5, Register.R6, Register.R7]

def is_jump_command(command):
    return command in [Opcode.JMP, Opcode.JZ, Opcode.JNZ, Opcode.JN, Opcode.JNN]

class SignalIP:
    NEXT_IP = "next_ip"
    JMP_LABEL = "jmp_label"
    JMP_REG = "jmp_reg"

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
        Opcode.MOV: lambda left: left,   # -|
        Opcode.LD: lambda left: left,    #  | поместить значение регистра на главную шину, выставить флаги
        Opcode.JMP: lambda left: left,   # -|
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
        self.rr = 0

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

    def signal_latch_register(self, register):
        match register:
            case Register.SP:
                self.sp = self.main_bus
            case Register.RR:
                self.rr = self.main_bus
            case _ if register in GENERAL_PURPOSE_REGISTERS:
                index = GENERAL_PURPOSE_REGISTERS.index(register)
                self.registers[index] = self.main_bus
            case _:
                raise ValueError(f"Inaccessible or non-existent register {register}")
    
    def signal_latch_ar(self):
        self.ar = self.main_bus

    def sel_register(self, register):
        match register:
            case Register.SP:
                return self.sp
            case Register.RR:
                return self.rr
            case Register.IP:
                return self.ip
            case _ if register in GENERAL_PURPOSE_REGISTERS:
                index = GENERAL_PURPOSE_REGISTERS.index(register)
                return self.registers[index]
            case _:
                raise ValueError(f"Inaccessible or non-existent register {register}")


class ControlUnit:
    def __init__(self, memory, data_path):
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
        self.data_path.signal_latch_register(res_reg)
        self.tick()

    def execute_unary_math_instruction(self, opcode, args):
        left_reg = args[0]
        left = self.data_path.sel_register(left_reg)
        alu_out = self.data_path.alu.process(left, Register.R0, opcode)
        self.data_path.main_bus = alu_out
        self.tick()

        self.data_path.signal_latch_register(left_reg)
        self.tick()

    def execute_store(self, opcode, args):
        if args[3] in Register:
            left = self.data_path.sel_register(args[3])
            self.data_path.main_bus = self.data_path.alu.process(left, Register.R0, opcode)
        else:
            self.data_path.main_bus = int(args[3])

        self.data_path.signal_latch_ar()
        self.tick()

        reg_to_store = args[0]
        value = self.data_path.sel_register(reg_to_store)
        self.data_path.signal_write_memory(value)
        self.tick()

    def execute_load(self, opcode, args):
        if args[3] in Register:
            left = self.data_path.sel_register(args[3])
            self.data_path.main_bus = self.data_path.alu.process(left, Register.R0, opcode)
        else:
            self.data_path.main_bus = int(args[3])

        self.data_path.signal_latch_ar()
        self.tick()

        self.data_path.main_bus = self.data_path.signal_read_memory(self.data_path.ar)
        reg_to_load = args[0]
        self.data_path.signal_latch_register(reg_to_load)
        self.tick()

    def execute_load_immediately(self, opcode, args):
        register = args[0]
        value = int(args[3])
        self.data_path.main_bus = value
        self.data_path.signal_latch_register(register)
        self.tick()

    def execute_cmp(self, opcode, args):
        left_reg = args[1]
        right_reg = args[2]
        left = self.data_path.sel_register(left_reg)
        right = self.data_path.sel_register(right_reg)
        alu_out = self.data_path.alu.process(left, right, opcode)
        self.data_path.main_bus = alu_out
        self.tick()

    def execute_mov(self, opcode, args):
        reg_to_load = args[0]
        reg_to_copy = args[1]
        left = self.data_path.sel_register(reg_to_copy)
        alu_out = self.data_path.alu.process(left, Register.R0, opcode)
        self.data_path.main_bus = alu_out
        self.tick()

        self.data_path.signal_latch_register(reg_to_load)
        self.tick()

    def execute_input(self, opcode, args):
        if len(self.data_path.input_buffer) == 0:
            raise EOFError()
        symbol = self.data_path.input_buffer.pop(0)
        symbol_code = ord(symbol)
        self.memory[INPUT_PORT_ADDRESS]["args"][0] = symbol_code

        self.data_path.main_bus = INPUT_PORT_ADDRESS
        self.data_path.signal_latch_ar()
        self.tick()

        register = args[0]
        self.data_path.main_bus = self.data_path.signal_read_memory(self.data_path.ar)
        self.data_path.signal_latch_register(register)
        self.tick()

    def execute_output(self, opcode, args):
        self.data_path.main_bus = OUTPUT_PORT_ADDRESS
        self.data_path.signal_latch_ar()
        self.tick()

        register = args[0]
        value = self.data_path.sel_register(register)
        self.data_path.signal_write_memory(value)
        self.tick()

        symbol = chr(self.memory[OUTPUT_PORT_ADDRESS]["args"][0])
        self.data_path.output_buffer.append(symbol)

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def signal_latch_ip(self, sel_next):
        match sel_next:
            case SignalIP.NEXT_IP:
                self.data_path.ip += 1
            case SignalIP.JMP_LABEL:
                instr = self.memory[self.data_path.ip]
                address = int(instr["args"][3])
                self.data_path.ip = address
            case SignalIP.JMP_REG:
                address = self.data_path.main_bus
                self.data_path.ip = address

    def decode_and_execute_control_flow_instruction(self, opcode, args):
        if opcode is Opcode.HALT:
            raise StopIteration()

        if is_jump_command(opcode):
            sel_next = SignalIP.NEXT_IP
            match opcode:
                case Opcode.JMP:
                    if args[3] in Register:
                        reg = args[3]
                        self.data_path.main_bus = self.data_path.alu.process(reg, Register.R0, Opcode.JMP)
                        self.tick()

                    sel_next = SignalIP.JMP_REG if args[3] == Register.RR.reg_name else SignalIP.NEXT_IP
                case Opcode.JZ:
                    sel_next = SignalIP.JMP_LABEL if not self.data_path.is_zero() else SignalIP.NEXT_IP
                case Opcode.JNZ:
                    sel_next = SignalIP.JMP_LABEL if self.data_path.is_zero() else SignalIP.NEXT_IP
                case Opcode.JN:
                    sel_next = SignalIP.JMP_LABEL if not self.data_path.is_negative() else SignalIP.NEXT_IP
                case Opcode.JNN:
                    sel_next = SignalIP.JMP_LABEL if self.data_path.is_negative() else SignalIP.NEXT_IP
                case _:
                    logging.warning("Unknown jump opcode %s", opcode)

            self.signal_latch_ip(sel_next=sel_next)
            self.tick()

            return True

        return False


    def decode_and_execute_instruction(self):
        instr = self.data_path.signal_read_memory(self.data_path.ip)
        self.tick()
        opcode = Opcode(instr["name"])
        args = instr["args"]

        if self.decode_and_execute_control_flow_instruction(opcode, args):
            return

        instruction_executor = self.instruction_executors[opcode]
        instruction_executor(opcode, args)
        self.signal_latch_ip(sel_next=SignalIP.NEXT_IP)

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

    # output, instr_counter, ticks = "", 0, 0 #simulation(memory, input_tokens=input_token)
    output, instr_counter, ticks = simulation(memory, input_tokens=input_token)


    print("".join(output))
    print("instr_counter: ", instr_counter, "ticks: ", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
