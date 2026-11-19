# img_box.py [RAM.bin]: the black box (flags 0x20000) of a Flycast RAM dump (run1.sh DUMP=1): exceptions, maple hooks, VMU frames
import struct, sys
m = open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/ram.bin', 'rb').read()
B = lambda i: struct.unpack_from('<I', m, 0x1da0000 + 4 * i)[0]
print('magic %08x exc %d hooks %d out %d vmuframes %d bad %d' % (B(0), B(1), B(2), B(3), B(4), B(5)))
for i in range(min(B(4), 32)):
    print('  vmu hdr %08x func %08x recv %08x call/loc %08x' % tuple(B(0x100 + i * 4 + k) for k in range(4)))
for n in range(min(B(1), 8)):
    print('  exc', ' '.join('%08x' % B(8 + n * 8 + k) for k in range(8)))
