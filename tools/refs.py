# refs.py FILE BASE LIT... : instructions (mov.l/mov.w @(disp,pc)) that load from the given literal address
import struct, sys
b = open(sys.argv[1],'rb').read(); base = int(sys.argv[2],16)
for a in sys.argv[3:]:
    lit = int(a,16); out = []
    for i in range(0, len(b)-1, 2):
        op = struct.unpack_from('<H', b, i)[0]; pc = base + i
        if op >> 12 == 0xD and (pc & ~3) + 4 + (op & 0xff)*4 == lit: out.append(pc)
        elif op >> 12 == 0x9 and pc + 4 + (op & 0xff)*2 == lit: out.append(pc)
    print(a, [hex(x) for x in out])
