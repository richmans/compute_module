# STRINGS
# A better hello world using STR the pseudo-instruction and B register instructions
SETB :data

loop:
LOADI
JUMPZ :end
WRITE
ADDLB 01
JUMP :loop

end:
HALT
data:
STR Hello, world!
