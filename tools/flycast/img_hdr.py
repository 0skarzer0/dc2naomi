# img_hdr.py IMAGE.bin: dimm_header of an unpacked image: flags, pad map, VMU slot, patch table
import struct, sys
f = open(sys.argv[1], 'rb'); raw = f.read(0x400)
so, _, sl = struct.unpack_from('<III', raw, 0x360)
base = (so + sl + 0xffff) & ~0xffff
f.seek(base); h = f.read(0x4000)
W = lambda i: struct.unpack_from('<I', h, 4 * i)[0]
print('flags %x hook_pc %08x %08x pad %d vmu %x chunk %d' % (W(4), W(173), W(174), W(175), W(176), W(177)))
o = 183 * 4
while True:
    a, k, v, e = struct.unpack_from('<4I', h, o); o += 16
    if not a and not k: break
    print('  %08x kind %02x value %08x expect %08x' % (a, k, v, e))
