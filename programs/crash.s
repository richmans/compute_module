# Tries to write to memory that is not there
# Does nothing when run with --bidwidth 8
# Because ADD FF and 1 will result in 0 with the overflow flag set. 0 is a valid memory location
#
# Crashes when run with --bitwidth 16 or larger
# Because ADD FF and 1 will result in 0x100, which is not a valid memory address
SET FF
SWAP
SET 01
ADD
SWAP
SAVEI
HALT