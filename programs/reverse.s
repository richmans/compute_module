# REVERSE
# reads a string from portin and writes it to portout in reverse
# limitations: a long enough string will overwrite the program and crash the machine

# Write a 0 byte at the end of memory
SET 00
SAVE FF
# Start at memory address FF in B
SET FF
SWAP

# Reads characters from portin until a 0 value is reached
# Characters are written to memory backwards starting at memory address FE
read:
# Subtract 1 from B
SET 01
SWAP
SUB
SWAP
# Read a character from the input
READ
# If we read a 0 byte, we're done reading
JUMPZ :write
# Save the character at index B
SAVEI
JUMP :read

# Writes characters from memory to portout until a 0 value is reached
write:
# Add 1 to B
SET 01
SWAP
ADD
SWAP
# read a byte from memory
LOADI
# write it to portout
WRITE
# if the byte was 0, that's the end of the string
JUMPZ :done
JUMP :write

done:
HALT