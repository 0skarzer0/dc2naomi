#!/usr/bin/env python3
"""addvmu.py IN.bin.gz OUT.bin.gz [LOADER.bin]: an image already built, with the emulated Visual Memory.

Sets the VMU flag (0x8000), appends the 128 KB slot the netbooter fills from JUEGO.vmu and, with LOADER.bin,
replaces the loader (the VMU needs the resident of 2026-11-10 or later: app/loader.bin). The header must have the
current layout (tools/convhdr.py converts the old ones)."""
import gzip
import struct
import sys

HDR = 0x1000
VMU_OFFSET_AT = 176 * 4      # struct dimm_header.vmu_offset
PATCHES_AT = 183 * 4
VMU_SIZE = 0x20000


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    with gzip.open(sys.argv[1], "rb") as f:
        data = bytearray(f.read())
    assert data[:5] == b"NAOMI", "not a NAOMI image"
    so, _, sl = struct.unpack_from("<III", data, 0x360)
    base = (so + sl + 0xffff) & ~0xffff
    assert struct.unpack_from("<2I", data, base) == (0x47434459, 0x32474d49), "not a dc2naomi image"
    addr, kind = struct.unpack_from("<2I", data, base + PATCHES_AT)
    assert kind == 1 and (addr >> 24) in (0x8c, 0x0c), "old header layout: convert it with tools/convhdr.py first"
    if len(sys.argv) == 4:
        new = bytearray(open(sys.argv[3], "rb").read())
        so2, _, sl2 = struct.unpack_from("<III", new, 0x360)
        assert ((so2 + sl2 + 0xffff) & ~0xffff) == base, "the loader's size class changed"
        new[0x30:0x130] = data[0x30:0x130]          # the game title
        data[:base] = bytes(new) + bytes(base - len(new))
    flags = struct.unpack_from("<I", data, base + 16)[0] | 0x8000
    struct.pack_into("<I", data, base + 16, flags)
    if struct.unpack_from("<I", data, base + VMU_OFFSET_AT)[0] == 0:
        struct.pack_into("<I", data, base + VMU_OFFSET_AT, len(data) - base)
        data += bytes(VMU_SIZE)
    off = struct.unpack_from("<I", data, base + VMU_OFFSET_AT)[0]
    with gzip.open(sys.argv[2], "wb", 6) as f:
        f.write(data)
    print(f"{sys.argv[2]}: flags {flags:#x}, Visual Memory slot at image offset {base + off:#x}, {len(data)} bytes")


if __name__ == "__main__":
    main()
