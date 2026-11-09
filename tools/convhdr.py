"""Rewrite an old dc2naomi image (header with DIMM_RANGES 4, DIMM_TRACKS 8) for the current resident (32, 64),
with the current app/loader.bin. convhdr.py OLD.bin.gz NEW.bin.gz TITLE [PADMAP]"""
import gzip, os, struct, sys, shutil
APP = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'app')
sys.path.insert(0, APP); sys.argv, args = ['x'], sys.argv[1:]
import dc2naomi as D
src_p, dst_p, title = args[:3]
pad = int(args[3]) if len(args) > 3 else None
def base(x):
    so, _, sl = struct.unpack_from('<III', x, 0x360); return (so + sl + 0xffff) & ~0xffff
src = gzip.open(src_p, 'rb')
head = src.read(0x40000 + 0x1000)
bo = base(head)
h = head[bo:bo + 0x1000]
w = struct.unpack_from('<10I', h, 0)
o = 40
ranges = [struct.unpack_from('<3I', h, o + 12 * i) for i in range(4)]; o += 48
ft, nt, lo = struct.unpack_from('<3I', h, o); o += 12
tracks = list(struct.unpack_from('<8I', h, o)); o += 32
hook = struct.unpack_from('<2I', h, o); o += 8
padmap = struct.unpack_from('<I', h, o)[0]; o += 4 + 28
patches = [struct.unpack_from('<4I', h, o + 16 * i) for i in range(64)]
assert w[9] <= 4 and nt <= 8
print('ranges', [(hex(a), n, hex(c)) for a, n, c in ranges[:w[9]]], 'tracks', ft, nt, hex(lo), 'pad', padmap)
print('patches', [(hex(a), k, hex(v), hex(e)) for a, k, v, e in patches if k])
if pad is not None: padmap = pad
nh = struct.pack('<10I', *w)
for i in range(32): nh += struct.pack('<3I', *(ranges[i] if i < 4 else (0, 0, 0)))
nh += struct.pack('<3I', ft, nt, lo) + struct.pack('<64I', *(tracks + [0] * 56))
nh += struct.pack('<2I', *hook) + struct.pack('<I', padmap) + b'\0' * 28
for p in patches: nh += struct.pack('<4I', *p)
assert len(nh) <= 0x1000
nh += h[len(nh):] if len(nh) < 0x1000 else b''
nh = nh[:0x1000]
new = D.set_title(open(os.path.join(APP, 'loader.bin'), 'rb').read(), title)
assert base(new) == bo
with gzip.GzipFile(dst_p, 'wb', compresslevel=6, mtime=0) as out:
    out.write(new + b'\0' * (bo - len(new)))
    out.write(nh)
    out.write(head[bo + 0x1000:])
    shutil.copyfileobj(src, out, 1 << 20)
