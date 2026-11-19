# setflag.py IMAGE.bin OR_MASK: dimm_header.flags |= mask
import struct, sys
f = open(sys.argv[1], 'r+b'); raw = f.read(0x400)
so, _, sl = struct.unpack_from('<III', raw, 0x360)
base = (so + sl + 0xffff) & ~0xffff
f.seek(base + 16); v = struct.unpack('<I', f.read(4))[0]; print('flags', hex(v))
f.seek(base + 16); f.write(struct.pack('<I', v | int(sys.argv[2], 0)))
