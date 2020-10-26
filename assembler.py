from vm import Instruction, Machine
from argparse import ArgumentParser
import sys
from binascii import unhexlify

class AssemblerError(Exception):
    pass

class Assembler:
    def __init__(self, m):
        self.instructions = {i.name: i for i in m.instruction_set}
        self.memsize = m.memsize
        self.prog = bytearray()
        self.lineno = 0
        self.labels = {}
        self.label_references = []
    
    def write(self, bt):
        if type(bt) == int:
            self.prog += bytes([bt])
        else:
            self.prog += bt
        if len(self.prog)> self.memsize:
                raise AssemblerError("Program is too large for memory")

    
    def read_arg(self, data):
        if data.startswith(":"):
            lblname = data[1:].lower()
            self.label_references.append((lblname, len(self.prog)))
            return 0
        elif not len(data) == 2:
            raise AssemblerError(f"Could not parse argument {data}")
        return int(data, 16)

    def assemble_line(self, line):
        line = line.strip()
        parts = line.split()
        if len(parts) == 0 or line[0].startswith('#'):
            return
        iname = parts[0]
        if iname.upper() == 'STR':
            self.write(line[4:].encode().decode('unicode-escape').encode() + b'\x00')
        elif iname.upper() == 'HEX':
            self.write(unhexlify(line[4:]))
        elif iname.endswith(":"):
            lblname = iname[:-1].lower()
            if lblname in self.labels:
                raise AssemblerError(f"Label {lblname} defined twice")
            self.labels[lblname] = len(self.prog)
        elif iname.upper() in self.instructions:
            instruction = self.instructions[iname.upper()]
            self.write(instruction.num)
            if instruction.has_arg():
                if len(parts) < 2:
                    raise AssemblerError("Expected argument")
                arg = self.read_arg(parts[1])
                self.write(arg)
        else:
            raise AssemblerError(f"Instruction {iname} not found")
        
    def resolve_references(self):
        for reflabel, refoffset in self.label_references:
            if not reflabel in self.labels:
                raise AssemblerError(f"Could not resolve label {reflabel}")
            lblloc = self.labels[reflabel]
            self.prog[refoffset] = lblloc

    def assemble_text(self, data):
        for line in data.split("\n"):
            self.lineno += 1
            self.assemble_line(line)
        self.resolve_references()
        return self.prog
    
    def assemble_file(self, filename, output_filename):
        with open(filename) as asm:
            assy = asm.read()
            prog=self.assemble_text(assy)
        
            output = sys.stdout.buffer if output_filename is None else open(output_filename, 'wb')
            output.write(prog)
            if output != sys.stdout:
                output.close() 


if __name__ == '__main__':
    m = Machine(bitwidth=8)
    assembler = Assembler(m)
    parser = ArgumentParser(description='Assemble a program.')
    parser.add_argument('file', help='File to assemble')
    parser.add_argument('--output', metavar='FILE',
                        help='Output file (stdout if ommitted)')

    args = parser.parse_args()
    try:
           
        assembler.assemble_file(args.file, args.output)
    except AssemblerError as e:
        sys.stderr.write(f"Error at line: {assembler.lineno}: {e}\n")
        sys.exit(1)