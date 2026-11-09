#!/usr/bin/env python3
"""gensig.py PROFILE=SOURCE ... : SHA-1 of the program files each games.py profile patches, for catalog.py.

SOURCE is a .chd, a .gdi or an image this project built (.bin or .bin.gz: the disc sectors are read back
from it). Prints lines to paste into SIGNATURES in tools/catalog.py (hashes only: nothing from the disc).
"""
import gzip
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from games import GAMES  # noqa: E402
from gdi import Gdi, open_disc  # noqa: E402


class ImageDisc(Gdi):
    """The disc sectors kept in a dc2naomi image (header: resident/resident.h)."""

    def __init__(self, path):
        self.f = gzip.open(path, "rb") if path.endswith(".gz") else open(path, "rb")
        head = self.f.read(0x400)
        seg_offset, _a, seg_length = struct.unpack_from("<III", head, 0x360)
        base = (seg_offset + seg_length + 0xFFFF) & ~0xFFFF
        self.f.seek(base)
        hdr = self.f.read(0x1000)
        assert struct.unpack_from("<I", hdr, 0)[0] == 0x47434459
        n = struct.unpack_from("<I", hdr, 36)[0]
        self.ranges = [struct.unpack_from("<3I", hdr, 40 + 12 * i) for i in range(n)]
        self.base = base
        self.tracks = []

    def sector(self, lba):
        fad = lba + 150
        for f0, n, off in self.ranges:
            if f0 <= fad < f0 + n:
                self.f.seek(self.base + off + (fad - f0) * 2048)
                return self.f.read(2048)
        return bytes(2048)


def main():
    for arg in sys.argv[1:]:
        prof, src = arg.split("=", 1)
        g = GAMES[prof]
        d = ImageDisc(src) if ".bin" in os.path.basename(src) else open_disc(src)
        out = []
        for grp in [x for x in g["groups"] if x["file"] != "IP.BIN"]:   # (IP.BIN: the standard bootstrap, checked word by word)
            data = d.sectors(45000, 16) if grp["file"] == "IP.BIN" else d.read_file(grp["file"])
            out.append((grp["file"], hashlib.sha1(data).hexdigest()))
        print(f'    "{prof}": {out!r},')


if __name__ == "__main__":
    main()
