#!/usr/bin/env python3
"""addprograms.py IMAGE.bin.gz DISC [OUT.bin.gz] : adds to a dc2naomi image already made the patches of the other
Katana programs of its disc (app/dc2naomi.py other_programs), without converting the disc again.

For images made before 2026-11-19, when the automatic profile patched only 1ST_READ.BIN: games whose 1ST_READ.BIN
is a loader and the game another program loaded over it at 0x8c010000 (Wacky Races: WACKY.BIN + MOVIE.BIN; Test
Drive Le Mans: FMV.BIN + LEMANS24.BIN; MSR: MSR.BIN + 2_DP.BIN; SF Rush 2049: 2_DP.BIN) ran that program with its
own maple driver talking to the MIE: no controller ("insert a controller in Port A"), no buttons after START, or
a black screen. Only the patch table of the image header changes; the files the image was made with (re-encoded
videos, mono music) stay. Writes OUT (default: IMAGE with _fix before .bin.gz); GZIP_LEVEL as dc2naomi (default 6).
    python3 tools/addprograms.py dc-msr_dc2naomict.bin.gz "MSR - Metropolis Street Racer (USA) (Rev A).chd"
"""
import gzip
import importlib.util
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "app")]
import build_image  # noqa: E402

spec = importlib.util.spec_from_file_location("dc2naomi_app", os.path.join(HERE, "..", "app", "dc2naomi.py"))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

PATCHES_AT = 183 * 4          # struct dimm_header.patches


class DiscFiles:
    def __init__(self, disc):
        self.d = disc

    def file(self, name):
        return self.d.read_file(name)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, discpath = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else src.replace(".bin.gz", "_fix.bin.gz")
    disc = app.open_disc(discpath)
    ip = disc.sectors(disc.base, 16)
    groups = app.other_programs(disc, ip)
    if not groups:
        sys.exit("No hay otros programas que parchear en " + discpath)
    raw = bytearray(gzip.open(src).read())
    so, _, sl = struct.unpack_from("<III", raw, 0x360)
    base = (so + sl + 0xffff) & ~0xffff
    assert struct.unpack_from("<2I", raw, base) == (0x47434459, 0x32474d49), "no es una imagen de dc2naomi"
    pt = base + PATCHES_AT
    n = 0
    have = set()
    while struct.unpack_from("<2I", raw, pt + 16 * n) != (0, 0):
        have.add(struct.unpack_from("<I", raw, pt + 16 * n)[0])
        n += 1
    new = build_image.build_patches(DiscFiles(disc), groups)
    if any(a in have for a, k, v, e in new if k != build_image.PATCH_CHECK):
        sys.exit("La imagen ya tiene parches en esas direcciones (¿ya arreglada?)")
    assert n + len(new) <= build_image.DIMM_PATCHES, "no caben los parches"
    for i, p in enumerate(new):
        struct.pack_into("<4I", raw, pt + 16 * (n + i), *p)
    with gzip.open(out, "wb", compresslevel=int(os.environ.get("GZIP_LEVEL", "6"))) as f:
        f.write(raw)
    print("%s: %d parches añadidos (%s) -> %s" % (os.path.basename(src), len(new),
                                                  ", ".join(g["file"] for g in groups), out))


if __name__ == "__main__":
    main()
