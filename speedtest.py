from vm import Instruction, Machine
from assembler import Assembler
from time import time


m = Machine(bitwidth=8)
assembler = Assembler(m)
asm = open('programs/hello.s').read()
prog = assembler.assemble_text(asm)


start_time = time()
ticks = 0
for i in range(20000):
  m.reset()
  m.load(prog)
  while not m.is_halted():
    ticks += 1
    m.tick()

end_time = time()

if m.is_faulted():
  print("Virtual machine gave an error!", file=sys.stderr)
  sys.exit(1)
  
duration = end_time - start_time
tps = ticks / duration 
print(f'done {ticks} ticks in {duration:.05} seconds ( {tps:.1f} tps )')
