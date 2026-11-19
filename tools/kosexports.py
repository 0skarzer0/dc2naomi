#!/usr/bin/env python3
"""List KallistiOS's kernel export table (name, address) from a plain 1ST_READ.BIN loaded at 0x8c010000."""
import struct, sys
d = open(sys.argv[1], "rb").read(); base = 0x8c010000
def s_at(a):
    o = a - base
    if not (0 <= o < len(d)): return None
    e = d.find(b"\0", o)
    s = d[o:e]
    return s.decode() if s and all(32 <= c < 127 for c in s) else None
# find the table by the entry for a name we know
key = d.find(b"cdrom_cdda_play\0") + base
ref = d.find(struct.pack("<I", key))
# walk backwards and forwards over {name, ptr} pairs
i = ref
while s_at(struct.unpack("<I", d[i-8:i-4])[0]): i -= 8
out = []
while True:
    n, p = struct.unpack("<II", d[i:i+8])
    s = s_at(n)
    if not s: break
    out.append((s, p)); i += 8
for s, p in out: print("%08x %s" % (p, s))
