#!/usr/bin/env python
"""patch_gz.py IN.bin.gz OUT.bin.gz OFFSET OLDHEX NEWHEX : change bytes inside a gzipped image without loading
it in RAM (works on the Raspberry itself, Python 2 or 3). OFFSET is in the uncompressed image. Checks the old bytes."""
import sys, gzip, binascii, hashlib
src, dst, off, old, new = sys.argv[1:6]
off = int(off, 0); old = binascii.unhexlify(old); new = binascii.unhexlify(new)
assert len(old) == len(new)
i = gzip.open(src, "rb"); o = gzip.open(dst, "wb", 6); h = hashlib.md5(); pos = 0
while True:
    b = i.read(1 << 20)
    if not b:
        break
    if pos <= off < pos + len(b):
        k = off - pos
        assert k + len(new) <= len(b), "patch across a block edge"
        assert b[k:k + len(old)] == old, "old bytes do not match"
        b = b[:k] + new + b[k + len(new):]
    h.update(b); o.write(b); pos += len(b)
o.close()
assert pos > off, "offset past the end"
print("ok %d bytes, md5 of the uncompressed image %s" % (pos, h.hexdigest()))
