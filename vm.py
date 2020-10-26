import time
from queue import Queue, Empty
from argparse import ArgumentParser
import sys

class Instruction:
    def __init__(self, num, name, handler):
        self.num = num
        self.name = name
        self.handler = handler
    def has_arg(self):
        return self.num & 0x80


class Machine:
    """
    This machine has:
    * two registers: A and B (16bits)
    * 256 bytes memory
    * 1 input port: portin
    * 1 output port: portout
    * 8 or 16 byte instructions


    Instructions: 
    in general: the first bit determines the amount of bytes that the instruction takes.
    0: 1 byte instruction
    1: 2 byte instruction
    
    0x00: NOP
    0x01: SWAP            # swaps the value of registers A and B
    0x02: ADD             # adds the value of B to A and stores the result in A
    0x03: SUB             # subtracts the value of B from A and stores the result in A
    0x04: WRITE           # writes the value of A to portout
    0x05: READ            # reads the value from portin into A
    0x06: HALT            # stops the computer
    0x07: LOADI           # Load indexed. Loads the value at mem addr B into A
    0x08: SAVEI           # Save indexed. Writes the lowest 8 bits of A into mem addr B
    0x80: LOAD [mem addr] # loads 8 bits at mem addr into A
    0x81: SAVE [mem addr] # writes the lowest 8 bits of A into mem addr
    0x92: JUMP [mem addr] # resume execution on memory address
    0x93: JZ   [mem addr] # jumps to mem addr if A is 0
    0x94: JNZ  [mem addr] # jumps to mem addr if A is not 0
    0x95: JO   [mem addr] # jumps to mem addr if overflow flag is set
    0xa0: ADDL [value]    # adds value to A
    0xa1: SUBL [value]    # subtract value from A
    0xa2: ADDLB[value]    # adds value to B
    0xA6: SET  [value]    # sets A to literal 8 bit value 
    0xa7: SETB [value]    # sets B to a literal 8 bit value
    """


    def __init__(self, bitwidth=16, memsize=256):
        self.memsize = memsize
        self.mem = [0] * self.memsize
        self.bitwidth = bitwidth
        self.modulus = 2 ** self.bitwidth
        self.maxint = self.modulus - 1
        self.ra = 0
        self.rb = 0
        self.pc = 0
        self.instruction = 0
        self.arg1 = 0
        self.arg2 = 0
        self.portin = Queue()
        self.portout = Queue()
        self.f_portout_was_written = False
        self.f_halted = False
        self.f_overflow = False
        self.f_fault = False
        self.instruction_set = [
            Instruction(0x00, "NOP", self.i_nop),
            Instruction(0x01, "SWAP", self.i_swap),
            Instruction(0x02, "ADD", self.i_add),
            Instruction(0x03, "SUB", self.i_sub),
            Instruction(0x04, "WRITE", self.i_write),
            Instruction(0x05, "READ", self.i_read),
            Instruction(0x06, "HALT", self.i_halt),
            Instruction(0x07, "LOADI", self.i_loadi),
            Instruction(0x08, "SAVEI", self.i_savei),
            
            Instruction(0x80, "LOAD", self.i_load),
            Instruction(0x81, "SAVE", self.i_save),
            Instruction(0x92, "JUMP", self.i_jump),
            Instruction(0x93, "JUMPZ", self.i_jumpz),
            Instruction(0x94, "JUMPNZ", self.i_jumpnz),
            Instruction(0x95, "JUMPO", self.i_jumpo),
            Instruction(0xa0, "ADDL", self.i_addl),
            Instruction(0xa1, "SUBL", self.i_subl),
            Instruction(0xa2, "ADDLB", self.i_addlb),
            
            Instruction(0xa6, "SET", self.i_set),
            Instruction(0xa7, "SETB", self.i_setb),
        ]
        self.instructions = {i.num: i for i in self.instruction_set}

    def load(self, data:bytes,  offset:int=0):
        """
        set a range of bytes in memory. 
        offset needs to be defined low enough to allow for the amount of bytes in data
        """
        if offset < 0 or len(data) + offset > self.memsize:
            raise IndexError("Invalid memory offset")
        i = offset
        for bt in data:
            self.mem[i] = bt
            i += 1

    def tick(self):
        self.f_portout_was_written = False
        self.f_halted = False
        self.f_fault = False
        self.execute_instruction()
        self.read_instruction()
    
    def execute_instruction(self):
        if not self.instruction in self.instructions:
            return
        handler = self.instructions[self.instruction].handler
        handler()

    def read_pc_byte(self):
        result = self.mem[self.pc]
        self.pc = (self.pc + 1) % self.memsize
        return result

    def read_instruction(self):
        self.instruction = self.read_pc_byte()
        self.arg1 = self.read_pc_byte() if self.instruction & 0x80 else 0
        
    def is_halted(self):
        return self.f_halted

    def is_faulted(self):
        return self.f_fault
        
    def fault(self):
        self.f_fault = True
        self.f_halted = True

    def i_nop(self):
        pass
    
    def i_swap(self):
        self.ra, self.rb = self.rb, self.ra
    
    def i_add(self):
        res = self.ra + self.rb
        self.f_overflow = res > self.maxint
        self.ra = res % self.modulus
    
    def i_sub(self):
        res = self.ra - self.rb
        self.f_overflow = res < 0
        self.ra = res % self.modulus

    def i_write(self):
        self.portout.put(self.ra)
        self.f_portout_was_written = True
    
    def i_read(self):
        try:
            self.ra = int(self.portin.get(False)) % self.modulus
        except Empty:
            self.ra = 0

    def i_load(self):
        self.ra = self.mem[self.arg1]

    def i_save(self):
        self.mem[self.arg1] = self.ra % 256 # Only write 1 byte to memory

    def i_jump(self):
        self.pc = self.arg1
    
    def i_jumpz(self):
        if self.ra == 0: self.i_jump()

    def i_jumpnz(self):
        if self.ra != 0: self.i_jump()
    
    def i_jumpo(self):
        if self.f_overflow: self.i_jump()

    def i_halt(self):
        self.f_halted = True
    
    def i_set(self):
        self.ra = self.arg1

    def i_setb(self):
        self.rb = self.arg1

    def i_loadi(self):
        if self.rb >= self.memsize:
            return self.fault()
        self.ra = self.mem[self.rb]
    
    def i_savei(self):
        if self.rb >= self.memsize:
            return self.fault()
        self.mem[self.rb] = self.ra % self.modulus
    
    def i_addl(self):
        res = self.ra + self.arg1
        self.f_overflow = res > self.maxint
        self.ra = res % self.modulus

    def i_addlb(self):
        res = self.rb + self.arg1
        self.f_overflow = res > self.maxint
        self.rb = res % self.modulus

    def i_subl(self):
        res = self.ra - self.arg1
        self.f_overflow = res < 0
        self.ra = res % self.modulus
        
    def __repr__(self):
        iname = self.instructions[self.instruction].name
        return f"A: {self.ra} B: {self.rb} I: {iname},{self.arg1} PC: {self.pc}"
    
if __name__ == '__main__':
    parser = ArgumentParser(description='Run the amazing computer')
    parser.add_argument('program', metavar='FILE', help='Program file to execute (use - to read the program from stdin)')
    parser.add_argument('--bitwidth', type=int, choices=[4,8,16,32,64], default=8)
    parser.add_argument('--memsize', type=int, default=256)
    parser.add_argument('--slow', action='store_true', help='Run the machine at max 2 instructions per second')
    parser.add_argument('--debug', action='store_true', help='Show the machine state before every tick')
    parser.add_argument('--number-mode', action='store_true', help='Portin and portout data is treated as numbers instead of bytes')
    parser.add_argument('--portin', help='data to push into portin. if --number-mode is defined, the format is numbers separated by commas')
    args = parser.parse_args()

    m = Machine(bitwidth=args.bitwidth, memsize=args.memsize)
    # Read the program from a file or stdin
    progfile = args.program
    if progfile == '-':
        prog = sys.stdin.buffer.read()
    else:
        with open(progfile, 'rb') as f:
            prog = f.read()
    # Load the program into the memory of the machine
    m.load(prog)
    # Push the provided bytes into the portin queue
    if args.number_mode and args.portin:
        try:
            data_in = [m.portin.put(int(i)) for i in args.portin.split(",")]
        except ValueError:
            print("Could not parse portin data in number mode. You need to provide a list of numbers separated by commas.", file=sys.stderr)
            sys.exit(1)
    elif args.portin:
        data_in = [m.portin.put(ord(i)) for i in args.portin]
    # main loop
    while not m.is_halted():
        # Print the current machine state
        if args.debug:
            print(m)
        # Execute instruction && read next instruction
        m.tick()
        # If something was written to portout, print it to stdout, formatting depending on --number-mode and --debug
        if m.f_portout_was_written:
            data = m.portout.get(False)
            data = chr(data % 256) if not args.number_mode else str(data) + " "
            if args.debug:
                print(f">> {data}")
            else:
                sys.stdout.write(data)
        
        if args.slow:
            time.sleep(0.1)
    if m.is_faulted():
        print("Virtual machine gave an error!", file=sys.stderr)
        sys.exit(1)
