"""Read a GD-ROM dump (.gdi + track files): sectors of the high-density area
and its ISO9660 file system."""
import os
import struct


class Gdi:
    base = 45000   # LBA of IP.BIN and the ISO9660 volume (a CD image sets its own: tools/cdi.py)

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
        pvd = self.sector(self.base + 16)
        assert pvd[1:6] == b"CD001", "no ISO9660 volume at LBA %d" % (self.base + 16)
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

    def filler_files(self, min_size=4 << 20):
        """Files that are only padding: one byte value repeated (self-booting CDs carry one, e.g. 448 MB of 0x37
        in front of the game's files, to place them on the outer edge of the disc). No game reads them."""
        out = []
        for p, lba, size in self.walk():
            n = (size + 2047) // 2048
            if size < min_size:
                continue
            probes = [self.sector(lba + k) for k in sorted({0, 1, n // 4, n // 2, 3 * n // 4, n - 2})]
            first = probes[0][:1]
            if all(b == first * 2048 for b in probes):
                out.append(p)
        return out

    def used_ranges(self, gap=64):
        """Sector runs (lba, count) of the data tracks that hold anything:
        the system area and directories, and every file."""
        runs = [(self.base, self.base + 150)]  # IP.BIN, PVD, path tables, root (and some slack)
        pvd = self.sector(self.base + 16)
        runs.append((self.base + 16, self.base + 16 + 64))
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

    def track_sectors(self, track):
        """(lba, 2048 bytes) for every sector of a data track."""
        num, start, ctrl, ss, fn, n = track
        with open(fn, "rb") as f:
            for i in range(n):
                f.seek(i * ss + (16 if ss == 2352 else 0))
                yield start + i, f.read(2048)


class ChdGdi(Gdi):
    """The same interface over a GD-ROM CHD (tools/chd.py), with no extraction."""

    def __init__(self, path):
        from chd import Chd
        self.chd = Chd(path)
        self.dir = None
        self.tracks = []
        self._start = {}   # track number -> first CHD frame
        self._raw = {}
        lba = 0
        for num, typ, frames, first in self.chd.gd_tracks():
            if num == 3:
                lba = 45000          # the high-density area
            ctrl = 0 if typ == "AUDIO" else 4
            self.tracks.append((num, lba, ctrl, 2352, None, frames))
            self._start[num] = first
            self._raw[num] = typ.endswith("_RAW") or typ == "AUDIO"
            lba += frames
        self.files = {}

    def sector(self, lba):
        for t in reversed(self.tracks):
            num, start, ctrl, ss, fn, n = t
            if start <= lba < start + n:
                if ctrl != 4:
                    return bytes(2048)
                fr = self.chd.frame(self._start[num] + lba - start)
                return fr[16:2064] if self._raw[num] else fr[:2048]
        return bytes(2048)

    def track_sectors(self, track):
        num, start, ctrl, ss, fn, n = track
        for i in range(n):
            yield start + i, self.sector(start + i)


def open_disc(path):
    """A .gdi, a .chd or a .cdi (a self-booting CD: tools/cdi.py)."""
    low = path.lower()
    if low.endswith(".cdi"):
        from cdi import Cdi
        return Cdi(path)
    return ChdGdi(path) if low.endswith(".chd") else Gdi(path)
