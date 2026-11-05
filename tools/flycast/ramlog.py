# ramlog.py RAMDUMP : resident state in a 32 MB RAM dump (0x0c000000..)
import struct, sys
m = open(sys.argv[1], 'rb').read()
w = lambda a: struct.unpack_from('<I', m, a & 0x1ffffff)[0]
print('resident magic %08x  log_pos %d' % (w(0x0dc00000), w(0x0dd80000 - 4)))
n = w(0x0dd80000 - 4)
for i in range(max(0, n - int(sys.argv[2] if len(sys.argv) > 2 else 40)), n):
    e = struct.unpack_from('<4I', m, (0x0dd80000 + (i & 255) * 16) & 0x1ffffff)
    c = e[0]
    tag = ''.join(chr(b) if 32 <= b < 127 else '.' for b in c.to_bytes(4, 'big'))
    print('%5d %08x %s  %08x %08x %08x' % (i, c, tag, *e[1:]))
print('IP.BIN', m[0x8000:0x8010], ' 1ST_READ word %08x  YSC %08x' % (w(0x0c010000), w(0x0c020000)))
print('VBR area 0x8c00f400 %08x, syscall vectors b0..bc: %s' % (w(0x0c00f400), ' '.join('%08x' % w(0x0c0000b0 + 4 * i) for i in range(4))))
