#!/usr/bin/env python3
"""newloader.py OLD.bin.gz OUT.bin.gz : puts the current loader and resident (app/loader.bin) on a dc2naomi image
made with an older one, keeping its title, header, patch table and disc data (no disc needed).

For images that miss later fixes of the resident: Super Puzzle Fighter II X (made 2026-11-09) hung on the board
after the CAPCOM and ADX logos, as SSF2X did before the resident cleared the game's RAM before booting (6c95d60).
The archive format (dimm_header) is the same; fields added later (read_chunk) read as 0 = the default.
FLAGS=0x... in the environment: OR'ed into dimm_header.flags (MSR: FLAGS=0x80000, DIMM_DMAIRQ).
PAD=n: dimm_header.pad_map (DIMM_PAD_*; 9 = lever up/down, START + lever B/A).
READ_CHUNK=n: dimm_header.read_chunk, sectors a DMA read copies per EXEC_SERVER call (Test Drive 6: READ_CHUNK=4;
with the default 32 the 3 MB FRONTEND.TEX read after START left the board stuck with the title music playing).
GZIP_LEVEL as dc2naomi (default 6)."""
import gzip
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def front(raw):
    so, _, sl = struct.unpack_from("<III", raw, 0x360)
    return (so + sl + 0xffff) & ~0xffff


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    raw = bytearray(gzip.open(sys.argv[1]).read())
    new = bytearray(open(os.path.join(HERE, "..", "app", "loader.bin"), "rb").read())
    old_base = front(raw)
    assert struct.unpack_from("<2I", raw, old_base) == (0x47434459, 0x32474d49), "no es una imagen de dc2naomi"
    new[0x30:0x130] = raw[0x30:0x130]            # the game's title (8 languages x 32 bytes)
    new += b"\0" * (front(new) - len(new))
    assert front(new) == len(new) == old_base, "el cargador nuevo no ocupa lo mismo que el viejo"
    raw[:old_base] = new
    if os.environ.get("PAD"):                       # dimm_header.pad_map (Test Drive 6: PAD=9, DIMM_PAD_WHEELUD)
        struct.pack_into("<I", raw, old_base + 175 * 4, int(os.environ["PAD"], 0))
        print("pad_map = %s" % os.environ["PAD"])
    if os.environ.get("READ_CHUNK"):
        struct.pack_into("<I", raw, old_base + 177 * 4, int(os.environ["READ_CHUNK"], 0))
        print("read_chunk = %s" % os.environ["READ_CHUNK"])
    if os.environ.get("FLAGS"):
        f = struct.unpack_from("<I", raw, old_base + 16)[0] | int(os.environ["FLAGS"], 0)
        struct.pack_into("<I", raw, old_base + 16, f)
        print("flags = %#x" % f)
    with gzip.open(sys.argv[2], "wb", compresslevel=int(os.environ.get("GZIP_LEVEL", "6"))) as f:
        f.write(raw)
    print("%s -> %s: cargador y residente actuales" % (sys.argv[1], sys.argv[2]))


if __name__ == "__main__":
    main()
