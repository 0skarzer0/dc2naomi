#!/usr/bin/env python3
"""addvmu_stream.py IN.bin.gz OUT.bin.gz LOADER.bin PADMAP: tools/addvmu.py without holding the image in RAM
(for the Raspberry Pi), and sets pad_map."""
import gzip, struct, sys, zlib
src, dst, ldr, pad = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
with open(src, "rb") as f:
    f.seek(-4, 2); total = struct.unpack("<I", f.read(4))[0]
fi = gzip.open(src, "rb")
head = bytearray(fi.read(0x100000))
so, _, sl = struct.unpack_from("<III", head, 0x360)
base = (so + sl + 0xffff) & ~0xffff
assert struct.unpack_from("<2I", head, base) == (0x47434459, 0x32474d49)
addr, kind = struct.unpack_from("<2I", head, base + 183 * 4)
assert kind == 1 and (addr >> 24) in (0x8c, 0x0c), "old header"
new = bytearray(open(ldr, "rb").read())
so2, _, sl2 = struct.unpack_from("<III", new, 0x360)
assert ((so2 + sl2 + 0xffff) & ~0xffff) == base
new[0x30:0x130] = head[0x30:0x130]
head[:base] = bytes(new) + bytes(base - len(new))
flags = struct.unpack_from("<I", head, base + 16)[0] | 0x8000
struct.pack_into("<I", head, base + 16, flags)
struct.pack_into("<I", head, base + 175 * 4, pad)
assert struct.unpack_from("<I", head, base + 176 * 4)[0] == 0
struct.pack_into("<I", head, base + 176 * 4, total - base)
fo = gzip.open(dst, "wb", 6)
fo.write(head); n = len(head)
while True:
    b = fi.read(1 << 22)
    if not b: break
    fo.write(b); n += len(b)
assert n == total, (n, total)
fo.write(bytes(0x20000)); fo.close()
print("ok flags %#x pad %d vmu slot at %#x size %d" % (flags, pad, total, total + 0x20000))
