# setpad.py IMAGE.bin PAD: change dimm_header.pad_map in an unpacked image (0 ct, 2 joy, 4 wheel...)
import struct, sys
f = open(sys.argv[1], 'r+b'); raw = f.read(0x400)
so, _, sl = struct.unpack_from('<III', raw, 0x360)
base = (so + sl + 0xffff) & ~0xffff
f.seek(base); h = f.read(16); assert struct.unpack_from('<2I', h) == (0x47434459, 0x32474d49), h
f.seek(base + 175 * 4); print('pad_map was', struct.unpack('<I', f.read(4))[0])
f.seek(base + 175 * 4); f.write(struct.pack('<I', int(sys.argv[2])))
