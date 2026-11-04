"""Read a GD-ROM dump (.gdi + track files): sectors of the high-density area
and its ISO9660 file system."""
import os
import struct


class Gdi:
    def __init__(self, path):
        self.dir = os.path.dirname(os.path.abspath(path))
        self.tracks = []  # (number, lba, ctrl, sector_size, path, sectors)
        lines = open(path).read().split("\n")
        for line in lines[1:]:
            p = line.split()
            if len(p) < 5:
                continue
            num, lba, ctrl, ss = int(p[0]), int(p[1]), int(p[2]), int(p[3])
            fn = os.path.join(self.dir, p[4].strip('"'))
            self.tracks.append((num, lba, ctrl, ss, fn, os.path.getsize(fn) // ss))
        self.files = {t[4]: open(t[4], "rb") for t in self.tracks}

    def hd_tracks(self):
        return [t for t in self.tracks if t[1] >= 45000]

    def data_tracks(self):
        return [t for t in self.hd_tracks() if t[2] == 4]

    def leadout(self):
        t = self.tracks[-1]
        return t[1] + t[5]

    def sector(self, lba):
        for num, start, ctrl, ss, fn, n in reversed(self.tracks):
            if start <= lba < start + n:
                if ctrl != 4:
                    return bytes(2048)
                f = self.files[fn]
                f.seek((lba - start) * ss + (16 if ss == 2352 else 0))
                return f.read(2048)
        return bytes(2048)

    def sectors(self, lba, n):
        return b"".join(self.sector(lba + i) for i in range(n))

    def _dir(self, lba, size):
        data = self.sectors(lba, (size + 2047) // 2048)
        i = 0
        while i < len(data):
            n = data[i]
            if n == 0:
                i = (i // 2048 + 1) * 2048
                continue
            r = data[i:i + n]
            i += n
            name = r[33:33 + r[32]]
            if name in (b"\0", b"\1"):
                continue
            yield (name.decode(errors="replace").split(";")[0], struct.unpack_from("<I", r, 2)[0],
                   struct.unpack_from("<I", r, 10)[0], bool(r[25] & 2))

    def walk(self):
        """(path, lba, size) for every file, path like 'OUTRUN/OUTRUN.BIN'."""
        pvd = self.sector(45016)
        assert pvd[1:6] == b"CD001", "no ISO9660 volume at LBA 45016"
        root = pvd[156:190]
        todo = [("", struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0])]
        while todo:
            path, lba, size = todo.pop()
            for name, elba, esize, is_dir in self._dir(lba, size):
                p = path + name
                if is_dir:
                    todo.append((p + "/", elba, esize))
                else:
                    yield p, elba, esize

    def find(self, path):
        for p, lba, size in self.walk():
            if p.upper() == path.upper():
                return lba, size
        raise KeyError(path)

    def read_file(self, path):
        lba, size = self.find(path)
        return self.sectors(lba, (size + 2047) // 2048)[:size]

    def used_ranges(self, gap=64):
        """Sector runs (lba, count) of the data tracks that hold anything:
        the system area and directories, and every file."""
        runs = [(45000, 45000 + 150)]  # IP.BIN, PVD, path tables, root (and some slack)
        pvd = self.sector(45016)
        runs.append((45016, 45016 + 64))
        for p, lba, size in self.walk():
            runs.append((lba, lba + (size + 2047) // 2048))
        # directories
        root = pvd[156:190]
        todo = [(struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0])]
        while todo:
            lba, size = todo.pop()
            runs.append((lba, lba + (size + 2047) // 2048))
            for name, elba, esize, is_dir in self._dir(lba, size):
                if is_dir:
                    todo.append((elba, esize))
        runs.sort()
        out = []
        for a, b in runs:
            if out and a <= out[-1][1] + gap:
                out[-1][1] = max(out[-1][1], b)
            else:
                out.append([a, b])
        return [(a, b - a) for a, b in out]
