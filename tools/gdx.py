# Extract the ISO9660 file system of a GD-ROM high-density track (raw 2352 sectors).
import sys, os, struct
track, start, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
f = open(track, 'rb')
def sec(lba, n=1):
    b = b''
    for i in range(n):
        f.seek((lba - start + i) * 2352 + 16); b += f.read(2048)
    return b
os.makedirs(out, exist_ok=True)
f.seek(0); open(os.path.join(out, 'IP.BIN'), 'wb').write(b''.join(sec(start + i) for i in range(16)))
pvd = sec(start + 16)
assert pvd[1:6] == b'CD001'
root = pvd[156:156+34]
def walk(lba, size, path):
    data = sec(lba, (size + 2047) // 2048)
    i = 0
    while i < len(data):
        l = data[i]
        if l == 0: i = (i // 2048 + 1) * 2048; continue
        r = data[i:i+l]; i += l
        elba, esize, flags = struct.unpack_from('<I', r, 2)[0], struct.unpack_from('<I', r, 10)[0], r[25]
        name = r[33:33+r[32]]
        if name in (b'\0', b'\1'): continue
        name = name.decode().split(';')[0]
        p = os.path.join(path, name)
        if flags & 2:
            os.makedirs(p, exist_ok=True); walk(elba, esize, p)
        else:
            with open(p, 'wb') as o:
                left = esize; l2 = elba
                while left > 0:
                    n = min(left, 2048 * 512); o.write(sec(l2, (n + 2047)//2048)[:n]); left -= n; l2 += 512
            print(f'{elba:7d} {esize:10d} {p[len(out):]}')
walk(struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0], out)
