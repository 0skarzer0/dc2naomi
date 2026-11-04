#!/usr/bin/env python3
"""Daytona USA (Dreamcast) for the NAOMI: the NetDIMM archive.

    build_image.py <files dir from the disc> <work dir> <loader prog.bin> <out.bin>

Re-encodes the music (ADXB_*.ADX, 44.1 kHz) at 32 kHz so the whole disc fits
the 512 MB NetDIMM, rebuilds the high-density track as a compact ISO9660 image
(sector 0 = LBA 45000 = FAD 45150, IP.BIN in the system area), makes a
Dreamcast flash ROM image (US region, English), and appends the archive
(see resident/resident.h) to the loader's netboot image.
"""
import os
import shutil
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ALIGN = 0x10000
BASE_LBA = 45000
BASE_FAD = BASE_LBA + 150
MUSIC_RATE = 32000

# Patches applied after loading (address, size, value); value 0xffffffff
# with size 4 = the resident maple hook.
PATCHES = [
    (0x8c008382, 2, 0xe000),   # IP.BIN bootstrap: cable type 0 (VGA): mov #0,r0
    (0x8c1d21ee, 2, 0x000b),   # syCblCheck (copy 1): rts
    (0x8c1d21f0, 2, 0xe000),   #   mov #0,r0 -> VGA
    (0x8c1f6866, 2, 0x000b),   # syCblCheck (copy 2)
    (0x8c1f6868, 2, 0xe000),
    (0x8c1e966c, 4, 0xffffffff),  # maple driver's "address to physical" call: our hook
    # The hardware init table would set the G1 bus timings for a GD-ROM drive;
    # on the NAOMI they are the NetDIMM's, as the BIOS left them: aim those two
    # entries at spare RAM instead.
    (0x8c1f3764, 4, 0xac00fe00),  # (was 0xa05f7484: G1RWC..G1CWC)
    (0x8c1f3778, 4, 0xac00fe40),  # (was 0xa05f74a0: G1GDRC, G1GDWC)
    (0x8c1f3784, 4, 0xac00fe80),  # (was 0xa05f74b4: G1CRDYC and the next one)
]


def reencode(src, dst):
    if os.environ.get("SMALL_MUSIC"):  # (diagnostic builds: the first 64 KB of each song)
        with open(src, "rb") as i, open(dst, "wb") as o:
            o.write(i.read(65536))
        return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ar", str(MUSIC_RATE),
                    "-c:a", "adpcm_adx", "-f", "adx", dst], check=True)


def make_tree(files, tree):
    if os.path.exists(tree):
        shutil.rmtree(tree)
    jobs = []
    for root, _dirs, names in os.walk(files):
        rel = os.path.relpath(root, files)
        out = os.path.join(tree, rel) if rel != "." else tree
        os.makedirs(out, exist_ok=True)
        for n in names:
            if rel == "." and n == "IP.BIN":
                continue
            s, d = os.path.join(root, n), os.path.join(out, n)
            if n.upper().startswith("ADXB_") and n.upper().endswith(".ADX"):
                jobs.append((s, d))
            else:
                os.link(s, d)
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        list(ex.map(lambda j: reencode(*j), jobs))
    print(f"{len(jobs)} music files at {MUSIC_RATE} Hz")


def make_iso(tree, ip_bin, iso):
    subprocess.run(["genisoimage", "-quiet", "-iso-level", "2", "-l", "-C", f"0,{BASE_LBA}",
                    "-G", ip_bin, "-V", "DAYTONAUSA", "-o", iso, tree], check=True)


def iso_find(iso, path):
    """LBA and size of a file in the root directory of the image."""
    with open(iso, "rb") as f:
        def sec(lba, n=1):
            f.seek((lba - BASE_LBA) * 2048)
            return f.read(2048 * n)
        pvd = sec(BASE_LBA + 16)
        assert pvd[1:6] == b"CD001"
        root = pvd[156:190]
        lba, size = struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0]
        data = sec(lba, (size + 2047) // 2048)
        i = 0
        while i < len(data):
            n = data[i]
            if n == 0:
                i = (i // 2048 + 1) * 2048
                continue
            r = data[i:i + n]
            i += n
            name = r[33:33 + r[32]].split(b";")[0].decode(errors="replace")
            if name == path:
                return struct.unpack_from("<I", r, 2)[0], struct.unpack_from("<I", r, 10)[0]
    raise SystemExit(f"{path} not in the image")


def crc_block(b):
    n = 0xffff
    for x in b[:62]:
        n ^= x << 8
        for _ in range(8):
            n = ((n << 1) ^ 4129) if n & 0x8000 else (n << 1)
            n &= 0xffff
    return n


def make_flash():
    fl = bytearray(b"\xff" * 0x20000)
    sysinfo = b"00100Dreamcast  "  # (region '1': USA)
    fl[0x1a000:0x1a010] = sysinfo
    fl[0x1a0a0:0x1a0b0] = sysinfo
    fl[0x1a056:0x1a05e] = bytes([0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0])  # system id
    for part, off, size in ((2, 0x1c000, 0x4000), (3, 0x10000, 0x8000), (4, 0x00000, 0x10000)):
        hdr = bytearray(b"\xff" * 64)
        hdr[0:16] = b"KATANA_FLASH____"
        hdr[16] = part
        hdr[17] = 0
        fl[off:off + 64] = hdr
    # user partition: the system settings block (logical 5) in physical block 1
    off, size = 0x1c000, 0x4000
    blocks = size // 64
    bitmap_blocks = (size + 32767) // 32768
    user_blocks = blocks - bitmap_blocks - 1
    blk = bytearray(64)
    secs = (2026 - 1950) * 365 * 86400  # (roughly)
    struct.pack_into("<HHHbBBB", blk, 0, 5, secs & 0xffff, (secs >> 16) & 0xffff, 0, 1, 0, 1)
    struct.pack_into("<H", blk, 62, crc_block(blk))
    fl[off + 64:off + 128] = blk
    bm = bytearray(b"\xff" * 64)
    bm[0] = 0x7f  # physical block 1 allocated
    bid = 1 + user_blocks
    fl[off + bid * 64:off + bid * 64 + 64] = bm
    return bytes(fl)


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    files, work, prog, out = sys.argv[1:]
    os.makedirs(work, exist_ok=True)
    tree = os.path.join(work, "tree")
    iso = os.path.join(work, "track3.iso")
    ip_bin = os.path.join(files, "IP.BIN")
    if not os.path.exists(iso) or os.environ.get("REBUILD"):
        make_tree(files, tree)
        make_iso(tree, ip_bin, iso)
    sectors = os.path.getsize(iso) // 2048
    boot_lba, boot_size = iso_find(iso, "1ST_READ.BIN")
    print(f"image: {sectors} sectors ({sectors * 2048 / 1048576:.1f} MB), 1ST_READ.BIN at LBA {boot_lba}, {boot_size} bytes")

    image = bytearray(open(prog, "rb").read())
    assert image[:5] == b"NAOMI"
    seg_offset, _addr, seg_length = struct.unpack_from("<III", image, 0x360)
    base = (seg_offset + seg_length + ALIGN - 1) & ~(ALIGN - 1)
    assert len(image) <= base
    image += b"\0" * (base - len(image))

    flash_offset = 0x1000
    image_offset = 0x40000
    hdr = struct.pack("<8I", 0x47434459, 0x31474d49, 1, 0, image_offset, sectors, BASE_FAD,
                      BASE_FAD + sectors)
    hdr += struct.pack("<3I", boot_lba + 150, boot_size, flash_offset) + b"\0" * 20
    pt = b""
    for a, s, v in PATCHES:
        pt += struct.pack("<3I", a, s, v)
    pt += b"\0" * (32 * 12 - len(pt))
    hdr += pt
    archive = bytearray(hdr)
    archive += b"\0" * (flash_offset - len(archive))
    archive += make_flash()
    archive += b"\0" * (image_offset - len(archive))
    with open(out, "wb") as o:
        o.write(image)
        o.write(archive)
        with open(iso, "rb") as f:
            shutil.copyfileobj(f, o, 1 << 20)
    total = len(image) + len(archive) + sectors * 2048
    print(f"{out}: archive at 0x{base:08x}, {total} bytes ({total / 1048576:.1f} MB)")
    if total > 512 * 1048576:
        print("warning: larger than the 512 MB NetDIMM")


if __name__ == "__main__":
    main()
