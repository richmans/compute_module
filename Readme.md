# The compute module
This is an implementation of an 8 bit computer  and assembler that can be used to teach assembly programming and/or computer architecture.

## Quick facts
The computer is 8 bit. It has:

* two registers: A and B
* 256 bytes memory
* 1 input port: portin
* 1 output port: portout
* 8 or 16 byte instructions

## TL;DR
Here's a quick tour of how to use this program.

First things first:

```
$ python3 assembler.py programs/hello.s| python3 vm.py - 
Hello world!
$
```

Let's try something more interesting:

```
# fibonacci.s
SET 01
WRITE
loop:
SWAP
ADD
JUMPO :end
WRITE
JUMP :loop
end:
HALT
```

```
$ python3 assembler.py programs/fibonacci.s| python3 vm.py -  --number-mode
1 1 2 3 5 8 13 21 34 55 89 144 233
$
```

is 8 bits not enough for you?

```
python3 assembler.py fibonacci.s| python3 vm.py - --bitwidth=16 --number-mode
1 1 2 3 5 8 13 21 34 55 89 144 233 377 610 987 1597 2584 4181 6765 10946 17711 28657 46368 
```

Want to see the thing work? Check out the `--debug` and `--slow` flags!

## VM
```
usage: vm.py [-h] [--bitwidth {4,8,16,32,64}] [--memsize MEMSIZE] [--slow] [--debug] [--number-mode] [--portin PORTIN] FILE

Run the amazing computer

positional arguments:
  FILE                  Program file to execute (use - to read the program from stdin)

optional arguments:
  -h, --help            show this help message and exit
  --bitwidth {4,8,16,32,64}
  --memsize MEMSIZE
  --slow                Run the machine at max 2 instructions per second
  --debug               Show the machine state before every tick
  --number-mode         Portin and portout data is treated as numbers instead of bytes
  --portin PORTIN       ascii data to push into portin. if --number-mode is defined, the format is numbers separated by commas
```
## Instruction set
in general: the first bit determines the amount of bytes that the instruction takes. If the bit is 0, the instruction is just 1 byte. If the bit is 1, the instruction is 2 bytes. The second byte is used as the argument.

```
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
```

## Bitwidth
The machine can be configured to do 8, 16, 32 or 64 bit arythmatic. This means the A and B registers and portin and portout will be wider. However, addresses and literal values are still limited to 1 byte. If you run in 16 bit mode and do a `load`, it will only load the lower 8 bits of the register, and set the higher bits to 0. If you do a `save`, only the lower 8 bits of the register are written to memory.

Allthough this might not be a great design choice in a real computer, it works to keep the instruction set simple, but expand the capabilities further than 8 bit numbers.

Use the `--bitwidth` option to set the width of the arythmetic.


## Number mode and the ports
The portin and portout channels are `Queue`'s that transport ints. Most programs we write have to do with text. So, `vm.py` will translate the value of `--portin` to a list of ascii values and feed that to the vm. Similarly, it will translate all numbers coming out of portout into ascii characters and print those to stdout.

If your program is not about text, you can run it in `--number-mode`. In this mode, `vm.py` will expect the `--portin` value to be a list of numbers separated by comma's. Any numbers that come out of portout will be printed to stdout separated by spaces.

`--number-mode` does not influence the working of the machine, only the way that the data is treated that goes in and out.

A nice way to see the difference is using the reverse program:
```
$ python3 assembler.py programs/reverse.s| python3 vm.py - --portin="1,2,30" 
03,2,1
$ python3 assembler.py programs/reverse.s| python3 vm.py - --portin="1,2,30" --number-mode  
30 2 1 0
```

## Assembler
An assembler is implemented to ease writing programs for the computer. It is very basic. An example program implementing the fibonacci series has been provided.

### Language
The language is simple. Each line contains 1 instruction. Empty lines are ignored, as well as lines starting with `#`

### Literals
Literal values are written as 2 hex characters.

### Labels
you can define a label by using a single word and adding a colon. When referencing a label in a jump instruction, you __prepend__ the colon.

After writing your assembly file, you can use the assembler to convert it into a binary file that the vm can execute.
```
usage: assembler.py [-h] [--output FILE] file

Assemble a program.

positional arguments:
  file           File to assemble

optional arguments:
  -h, --help     show this help message and exit
  --output FILE  Output file (stdout if ommitted)
```

