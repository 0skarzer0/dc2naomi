# lits.py FILE[,FILE...] HEX[,HEX...] - aligned 32-bit literals with those values
# Find 32-bit literals (aligned) in binaries and the mov.l instructions that load them.
import struct, sys
lits = [int(x,16) for x in sys.argv[2].split(',')]
for fn in sys.argv[1].split(','):
    b = open(fn,'rb').read()
    for i in range(0, len(b)-3, 4):
        v = struct.unpack_from('<I', b, i)[0]
        if v in lits:
            print(f'{fn} off {i:#08x} {v:#010x}')
