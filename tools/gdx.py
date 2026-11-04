# gdx.py GAME.gdi OUTDIR - extract the files of a GD-ROM dump (all high-density data tracks)
# Extract the ISO9660 file system of a GD-ROM high-density area spread over several data tracks (GDI).
import sys, os, struct
gdi, out = sys.argv[1], sys.argv[2]
d = os.path.dirname(gdi)
tracks = []
for line in open(gdi).read().split('\n')[1:]:
    p = line.split()
    if len(p) >= 5 and p[2] == '4' and int(p[1]) >= 45000:
        tracks.append((int(p[1]), int(p[3]), open(os.path.join(d, p[4]), 'rb')))
tracks.sort()
def sec1(lba):
    for start, ss, f in reversed(tracks):
        if lba >= start:
            f.seek((lba - start) * ss + (16 if ss == 2352 else 0)); return f.read(2048)
def sec(lba, n=1): return b''.join(sec1(lba + i) for i in range(n))
os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'IP.BIN'), 'wb').write(sec(45000, 16))
pvd = sec(45016); assert pvd[1:6] == b'CD001'
root = pvd[156:190]
def walk(lba, size, path):
    data = sec(lba, (size + 2047)//2048); i = 0
    while i < len(data):
        l = data[i]
        if l == 0: i = (i//2048 + 1)*2048; continue
        r = data[i:i+l]; i += l
        elba, esize, flags = struct.unpack_from('<I', r, 2)[0], struct.unpack_from('<I', r, 10)[0], r[25]
        name = r[33:33+r[32]]
        if name in (b'\0', b'\1'): continue
        name = name.decode().split(';')[0]; p = os.path.join(path, name)
        if flags & 2: os.makedirs(p, exist_ok=True); walk(elba, esize, p)
        else:
            with open(p, 'wb') as o:
                left, l2 = esize, elba
                while left > 0:
                    n = min(left, 2048*512); o.write(sec(l2, (n+2047)//2048)[:n]); left -= n; l2 += 512
            print(f'{elba:7d} {esize:10d} {p[len(out):]}')
walk(struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0], out)
