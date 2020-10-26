# FIBONACCI
# Outputs the fibonacci series to portout
# Stops when the output > maxint
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