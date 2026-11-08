#!/usr/bin/env python3
"""dc2naomi: the NetDIMM image for a Dreamcast game.

    build_image.py GAME SOURCE WORK LOADER.BIN OUT.BIN

GAME is one of games.py (daytona, ysgw). SOURCE is the disc:
- layout "gdi": the .gdi of your own dump (chdman extractcd -i game.chd -o game.gdi).
  Every sector of the high-density area that holds anything is kept at its
  original FAD (files keep their LBAs, nothing is rebuilt).
- layout "rebuild": a directory with the files of the disc (and IP.BIN); the
  high-density track is rebuilt as a compact ISO9660 image (sector 0 = LBA
  45000), music re-encoded to fit.

The archive (resident/resident.h) goes after the loader's netboot image.
SAMPLER=1: diagnostics build (rows of bits drawn on screen; no program hook). NOUBC=1: no user break.
"""
import os
import shutil
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from games import GAMES, HOOK, TRAMP, R4FIX, TEXPATH  # noqa: E402
from gdi import Gdi  # noqa: E402

ALIGN = 0x10000
BASE_LBA = 45000
FLASH_OFFSET = 0x1000
DATA_OFFSET = 0x40000
DIMM_RANGES, DIMM_TRACKS, DIMM_PATCHES = 4, 32, 64
PATCH_CHECK, PATCH_W16, PATCH_W32, PATCH_TRAMP, PATCH_R4FIX = 1, 2, 4, 8, 16


# ---------------------------------------------------------------- disc: gdi

def nonzero_runs(gdi, gap=256):
    """(lba, count) runs of non-zero sectors in the high-density data tracks."""
    runs = []
    for num, start, ctrl, ss, fn, n in gdi.data_tracks():
        with open(fn, "rb") as f:
            for i in range(n):
                f.seek(i * ss + (16 if ss == 2352 else 0))
                s = f.read(2048)
                if s.count(0) == 2048:
                    continue
                lba = start + i
                if runs and lba <= runs[-1][1] + gap:
                    runs[-1][1] = lba + 1
                else:
                    runs.append([lba, lba + 1])
    return [(a, b - a) for a, b in runs]


class GdiDisc:
    def __init__(self, path, boot_name="1ST_READ.BIN"):
        self.gdi = Gdi(path)
        self.boot_name = boot_name          # the boot file IP.BIN names (Windows CE discs: 0WINCEOS.BIN)
        self.runs = nonzero_runs(self.gdi)
        if len(self.runs) > DIMM_RANGES:
            # merge the closest runs until they fit
            while len(self.runs) > DIMM_RANGES:
                gaps = [self.runs[i + 1][0] - sum(self.runs[i]) for i in range(len(self.runs) - 1)]
                i = gaps.index(min(gaps))
                a, b = self.runs[i], self.runs[i + 1]
                self.runs[i:i + 2] = [(a[0], b[0] + b[1] - a[0])]

    def file(self, name):
        if name == "IP.BIN":
            return self.gdi.sectors(BASE_LBA, 16)
        return self.gdi.read_file(name)

    def boot(self):
        lba, size = self.gdi.find(self.boot_name)
        return lba + 150, size

    def toc(self):
        tracks = self.gdi.hd_tracks()
        entries = [((0x41 if ctrl == 4 else 0x01) << 24) | (lba + 150) for num, lba, ctrl, ss, fn, n in tracks]
        return tracks[0][0], entries, self.gdi.leadout() + 150

    def ranges(self):
        return [(lba + 150, n) for lba, n in self.runs]

    def write_sectors(self, out):
        for lba, n in self.runs:
            for i in range(0, n, 512):
                out.write(self.gdi.sectors(lba + i, min(512, n - i)))


# ------------------------------------------------------ disc: rebuilt ISO

class RebuiltDisc:
    def __init__(self, files, work, game):
        self.files_dir = files
        self.iso = os.path.join(work, "track3.iso")
        if not os.path.exists(self.iso) or os.environ.get("REBUILD"):
            tree = os.path.join(work, "tree")
            make_tree(files, tree, game.get("music_rate"))
            rr = ["-R"] if game.get("rock_ridge") else []   # (lower-case and long names: KallistiOS programs)
            subprocess.run(["genisoimage", "-quiet", "-iso-level", "2", "-l"] + rr + ["-C", f"0,{BASE_LBA}",
                            "-G", os.path.join(files, "IP.BIN"), "-V", game.get("volume", "DISC"),
                            "-o", self.iso, tree], check=True)
        self.sectors = os.path.getsize(self.iso) // 2048

    def file(self, name):
        return open(os.path.join(self.files_dir, name), "rb").read()

    def boot(self):
        lba, size = iso_find(self.iso, "1ST_READ.BIN")
        return lba + 150, size

    def toc(self):
        return 3, [0x41000000 | (BASE_LBA + 150)], BASE_LBA + 150 + self.sectors

    def ranges(self):
        return [(BASE_LBA + 150, self.sectors)]

    def write_sectors(self, out):
        with open(self.iso, "rb") as f:
            shutil.copyfileobj(f, out, 1 << 20)


def reencode(src, dst, rate):
    if os.environ.get("SMALL_MUSIC"):  # (diagnostic builds: the first 64 KB of each song)
        with open(src, "rb") as i, open(dst, "wb") as o:
            o.write(i.read(65536))
        return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ar", str(rate),
                    "-c:a", "adpcm_adx", "-f", "adx", dst], check=True)


def make_tree(files, tree, music_rate):
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
            if music_rate and n.upper().startswith("ADXB_") and n.upper().endswith(".ADX"):
                jobs.append((s, d))
            else:
                os.link(s, d)
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        list(ex.map(lambda j: reencode(j[0], j[1], music_rate), jobs))
    print(f"{len(jobs)} music files at {music_rate} Hz")


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


# ------------------------------------------------------------------ flash

def crc_block(b):
    n = 0xffff
    for x in b[:62]:
        n ^= x << 8
        for _ in range(8):
            n = ((n << 1) ^ 4129) if n & 0x8000 else (n << 1)
            n &= 0xffff
    return (~n) & 0xffff   # (inverted, as the BIOS/KallistiOS flashrom code: without it the settings block is
                           #  invalid and Katana games fall back to Japanese)


def make_flash(region, language):
    fl = bytearray(b"\xff" * 0x20000)
    sysinfo = b"00" + bytes([0x30 + region]) + b"00Dreamcast  "  # (region digit: 0 Japan, 1 USA, 2 Europe)
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
    struct.pack_into("<HHHbBBB", blk, 0, 5, secs & 0xffff, (secs >> 16) & 0xffff, 0, language, 0, 1)
    struct.pack_into("<H", blk, 62, crc_block(blk))
    fl[off + 64:off + 128] = blk
    bm = bytearray(b"\xff" * 64)
    bm[0] = 0x7f  # physical block 1 allocated
    bid = 1 + user_blocks
    fl[off + bid * 64:off + bid * 64 + 64] = bm
    return bytes(fl)


# ---------------------------------------------------------------- patches

def build_patches(disc, groups):
    """(addr, kind, value, expect) entries, original values read from the disc."""
    out = []
    for g in groups:
        data = disc.file(g["file"])
        base = g["base"]

        def word(addr, size):
            o = addr - base
            assert 0 <= o and o + size <= len(data), f"{g['file']}: {addr:#x} outside the file"
            return int.from_bytes(data[o:o + size], "little")

        touched = set()
        for a, s, _v in g["patches"]:
            touched.update(range(a, a + s))
        check = g.get("check")
        if check is None:  # an aligned word near the first patch that no patch touches
            a0 = g["patches"][0][0] & ~3
            for d in (-8, -12, -16, -4, 8, 12, 16, -20, -24, 20, 24):
                c = a0 + d
                if not touched & set(range(c, c + 4)) and word(c, 4) not in (0, 0xffffffff, 0x00090009):
                    check = c
                    break
        out.append((check, PATCH_CHECK, word(check, 4), 0))
        print(f"  {g['file']:<14} check {check:#010x} = {word(check, 4):#010x}")
        for a, s, v in g["patches"]:
            old = word(a, s)
            if os.environ.get("NOFIX") and (v == R4FIX or v == TEXPATH):  # diagnostics: no texture-path fix
                continue
            if os.environ.get("NOR4FIX") and v == R4FIX:
                continue
            if v == R4FIX:
                print(f"    {a:#010x} {s}: {old:#0{2 + 2 * s}x} -> texture-path stub")
                out.append((a, PATCH_R4FIX, 0, old))
                continue
            if v == TRAMP:
                print(f"    {a:#010x} {s}: {old:#0{2 + 2 * s}x} -> trampoline")
                out.append((a, PATCH_TRAMP, 0, old))
                continue
            new = "hook" if v == HOOK else f"{v:#x}"
            assert v == HOOK or old != v, f"{g['file']} {a:#x}: already {v:#x}"
            print(f"    {a:#010x} {s}: {old:#0{2 + 2 * s}x} -> {new}")
            out.append((a, PATCH_W16 if s == 2 else PATCH_W32, v, old))
    assert len(out) <= DIMM_PATCHES, "too many patches"
    return out


# ------------------------------------------------------------------- main

def main():
    if len(sys.argv) != 6:
        sys.exit(__doc__)
    name, source, work, prog, out = sys.argv[1:]
    game = dict(GAMES[name])
    if game.get("vmu"):  # emulated Visual Memory behind the port A controller
        game["flags"] = game["flags"] | 0x8000
    if os.environ.get("SAMPLER"):  # diagnostics: the on-screen PC sampler instead of the program hook
        game["flags"] = game["flags"] | 0x0001
    if os.environ.get("DIAG"):  # rows of bits on screen, back to VGA timings if the game leaves them
        game["flags"] = game["flags"] | 0x0008
    if os.environ.get("MASKERR"):  # keep the ASIC error interrupts masked
        game["flags"] = game["flags"] | 0x0010
    if os.environ.get("CH2TEST"):  # test DMA channel 2 to the texture paths before the game
        game["flags"] = game["flags"] | 0x0020
    if os.environ.get("DMA"):  # NetDIMM reads by G1 DMA, like the NAOMI library (PIO as the fallback)
        game["flags"] = game["flags"] | 0x0040
    if os.environ.get("PCSAMPLE"):  # PC sampler on TMU2 (rows 16-25)
        game["flags"] = game["flags"] | 0x0200
    if os.environ.get("G2IDLE"):  # NetDIMM PIO only while no G2 DMA runs
        game["flags"] = game["flags"] | 0x0100
    if os.environ.get("READTEST"):  # read the whole image twice by PIO and compare, before the game
        game["flags"] = game["flags"] | 0x0080
    if os.environ.get("SYNCREAD"):  # GD DMA reads done in one call (KallistiOS programs)
        game["flags"] = game["flags"] | 0x0400
    if os.environ.get("CONSOLE"):  # KallistiOS programs: their log drawn on screen (fake dcload)
        game["flags"] = game["flags"] | 0x0800
    if os.environ.get("NOIPBOOT"):  # no IP.BIN bootstrap: straight to 1ST_READ.BIN
        game["flags"] = game["flags"] | 0x1000
    if os.environ.get("NOPCTRA"):  # leave PCTRA alone
        game["flags"] = game["flags"] | 0x2000
    if os.environ.get("NOBIOSHW"):  # skip AICA SCI*/DMAOR/PCTRA writes
        game["flags"] = game["flags"] | 0x4000
    if os.environ.get("NOUBC"):  # no user break controller hook
        game["flags"] = game["flags"] | 0x0004
    os.makedirs(work, exist_ok=True)
    disc = GdiDisc(source, game.get("boot", "1ST_READ.BIN")) if game["layout"] == "gdi" else RebuiltDisc(source, work, game)

    boot_fad, boot_size = disc.boot()
    first_track, tracks, leadout = disc.toc()
    ranges = disc.ranges()
    print(f"{name}: 1ST_READ.BIN at FAD {boot_fad}, {boot_size} bytes")
    print("  TOC: tracks " + ", ".join(f"{first_track + i}:{t:#010x}" for i, t in enumerate(tracks))
          + f", leadout {leadout}")
    offset = DATA_OFFSET
    rtab = []
    for fad, n in ranges:
        rtab.append((fad, n, offset))
        print(f"  sectors FAD {fad}+{n} ({n * 2048 / 1048576:.1f} MB) at +{offset:#x}")
        offset += n * 2048
    assert len(rtab) <= DIMM_RANGES and len(tracks) <= DIMM_TRACKS
    patches = build_patches(disc, game["groups"])

    image = bytearray(open(prog, "rb").read())
    assert image[:5] == b"NAOMI"
    seg_offset, _addr, seg_length = struct.unpack_from("<III", image, 0x360)
    base = (seg_offset + seg_length + ALIGN - 1) & ~(ALIGN - 1)
    assert len(image) <= base
    image += b"\0" * (base - len(image))

    hdr = struct.pack("<10I", 0x47434459, 0x32474d49, 2, 0, game["flags"], FLASH_OFFSET,
                      boot_fad, boot_size, BASE_LBA + 150, len(rtab))
    for i in range(DIMM_RANGES):
        hdr += struct.pack("<3I", *(rtab[i] if i < len(rtab) else (0, 0, 0)))
    hdr += struct.pack("<3I", first_track, len(tracks), leadout)
    hdr += struct.pack(f"<{DIMM_TRACKS}I", *(tracks + [0] * (DIMM_TRACKS - len(tracks))))
    hook = list(game.get("hook_pc", [])) + [0, 0]
    hdr += struct.pack("<2I", *hook[:2]) + struct.pack("<I", {"ct": 0, "menu": 1, "joy": 2}[game.get("pads", "ct")]) + b"\0" * 28
    for p in patches:
        hdr += struct.pack("<4I", *p)
    hdr += b"\0" * (16 * (DIMM_PATCHES - len(patches)))
    assert len(hdr) <= FLASH_OFFSET
    archive = bytearray(hdr)
    archive += b"\0" * (FLASH_OFFSET - len(archive))
    archive += make_flash(game["region"], game["language"])
    archive += b"\0" * (DATA_OFFSET - len(archive))

    with open(out, "wb") as o:
        o.write(image)
        o.write(archive)
        disc.write_sectors(o)
    total = os.path.getsize(out)
    print(f"{out}: archive at 0x{base:08x}, {total} bytes ({total / 1048576:.1f} MB)")
    if total > 512 * 1048576:
        print("warning: larger than the 512 MB NetDIMM")


if __name__ == "__main__":
    main()
