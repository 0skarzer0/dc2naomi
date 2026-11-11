"""Read a DiscJuggler image (.cdi) of a self-booting Dreamcast CD: the same interface as gdi.Gdi.

A self-booting CD (the usual form of fan translations and homebrew) has an audio session first and a data session
second; the data track starts at its own LBA (often 11702), and its ISO9660 file system and the game's reads use
LBAs from the start of the disc, as a GD-ROM's do from 45000. The Dreamcast BIOS descrambles the boot file of a
CD before running it (the MIL-CD scrambling); `descrambled_boot()` does the same (see `descramble`).

The CDI layout (DiscJuggler 2.0, 3.0 and 3.5) is the one documented by DeXT's cdirip and read the same way by the
emulators: the last 8 bytes are the version and where the descriptor is; the descriptor lists the sessions and
their tracks; the tracks' sectors are stored one after the other from the start of the file, pregap first.
"""
import os
import struct

from gdi import Gdi

CDI_V2, CDI_V3, CDI_V35 = 0x80000004, 0x80000005, 0x80000006
TRACK_MARK = bytes([0, 0, 1, 0, 0, 0, 0xFF, 0xFF, 0xFF, 0xFF])
SECTOR_SIZES = {0: 2048, 1: 2336, 2: 2352, 4: 2448}


class CdiError(Exception):
    pass


def parse(path):
    """[(session, number, mode, lba, sectors, sector_size, file_offset)] for every track; lba (FAD - 150) and
    file_offset are those of index 1 (after the pregap). mode: 0 audio, 1 mode 1, 2 mode 2."""
    size = os.path.getsize(path)
    f = open(path, "rb")
    f.seek(size - 8)
    version, where = struct.unpack("<II", f.read(8))
    if version not in (CDI_V2, CDI_V3, CDI_V35):
        raise CdiError("no es una imagen CDI (versión %#x)" % version)
    f.seek(size - where if version == CDI_V35 else where)

    def rd(n):
        b = f.read(n)
        if len(b) != n:
            raise CdiError("descriptor CDI cortado")
        return b

    def u16():
        return struct.unpack("<H", rd(2))[0]

    def u32():
        return struct.unpack("<I", rd(4))[0]

    tracks = []
    pos = 0          # where the next track's sectors start in the file
    number = 0
    sessions = u16()
    for session in range(1, sessions + 1):
        ntracks = u16()
        for _ in range(ntracks):
            if u32() != 0:
                f.seek(8, 1)                       # DiscJuggler 3.00.780 and later
            if rd(10) != TRACK_MARK or rd(10) != TRACK_MARK:
                raise CdiError("pista CDI sin su marca")
            f.seek(4, 1)
            f.seek(rd(1)[0], 1)                    # the image's file name
            f.seek(11 + 4 + 4, 1)
            if u32() == 0x80000000:
                f.seek(8, 1)                       # DiscJuggler 4
            f.seek(2, 1)
            pregap, length = u32(), u32()
            f.seek(6, 1)
            mode = u32()
            f.seek(12, 1)
            lba, total = u32(), u32()
            f.seek(16, 1)
            ss_code = u32()
            f.seek(29, 1)
            if version != CDI_V2:
                f.seek(5, 1)
                if u32() == 0xFFFFFFFF:
                    f.seek(78, 1)                  # DiscJuggler 3.00.780 and later
            if ss_code not in SECTOR_SIZES:
                raise CdiError("tamaño de sector CDI desconocido (%d)" % ss_code)
            ss = SECTOR_SIZES[ss_code]
            number += 1
            # the descriptor's LBA is already the track's own (index 1); its pregap is stored before it
            tracks.append((session, number, mode, lba, length, ss, pos + pregap * ss))
            pos += total * ss
        f.seek(4 + 8 + (1 if version != CDI_V2 else 0), 1)   # the session's trailer
    if pos > size:
        raise CdiError("las pistas del CDI ocupan más que el archivo")
    return tracks


def _user_data_offset(mode, ss, raw):
    """Where the 2048 bytes of user data are in a stored sector."""
    if ss == 2048:
        return 0
    if ss == 2336:
        return 8                                   # mode 2 without sync and header: subheader first
    if mode == 1:
        return 16                                  # sync, header
    return 24 if raw[15] == 2 or mode == 2 else 16  # mode 2 form 1: sync, header, subheader


def descramble(data):
    """Undo the MIL-CD scrambling the Dreamcast BIOS undoes for a CD's boot file (Marcus Comstedt's algorithm, as
    KallistiOS's utils/scramble does it backwards): chunks of 2 MB down to 32 bytes, each a permutation of
    32-byte blocks drawn from a 16-bit generator seeded with the file's size."""
    size = len(data)
    out = bytearray(size)
    src = memoryview(data)
    seed = size & 0xFFFF
    pos = 0

    def rnd():
        nonlocal seed
        seed = (seed * 2109 + 9273) & 0x7FFF
        return (seed + 0xC000) & 0xFFFF

    def chunk(n):
        nonlocal pos
        blocks = n // 32
        idx = list(range(blocks))
        k = 0                                      # the blocks are stored in the order they are drawn
        for i in range(blocks - 1, -1, -1):
            x = (rnd() * i) >> 16
            idx[i], idx[x] = idx[x], idx[i]
            out[pos + idx[i] * 32:pos + idx[i] * 32 + 32] = src[pos + k * 32:pos + k * 32 + 32]
            k += 1
        pos += n

    left = size
    n = 0x200000
    while n >= 32:
        while left >= n:
            chunk(n)
            left -= n
        n >>= 1
    out[pos:] = src[pos:]                          # the tail under 32 bytes is not scrambled
    return bytes(out)


class Cdi(Gdi):
    """A self-booting CD in a .cdi, seen like a Gdi: `base` is the LBA of the data track (IP.BIN, the ISO9660
    volume), the tracks keep their own LBAs."""

    def __init__(self, path):
        self.path = path
        self.dir = os.path.dirname(os.path.abspath(path))
        self._f = open(path, "rb")
        self._boot = None
        self.cdi = parse(path)
        data = [t for t in self.cdi if t[2] != 0]
        if not data:
            raise CdiError("el CDI no tiene pista de datos")
        last = data[-1]                            # the last data track holds the boot session
        self.base = last[3]
        # tracks as Gdi keeps them: (number, lba, ctrl, sector_size, path, sectors); path None (read via _where)
        self.tracks = [(t[1], t[3], 4 if t[2] else 0, t[5], None, t[4]) for t in self.cdi]
        self._where = {t[1]: t for t in self.cdi}
        self.files = {}
        self._boot = None                          # (first lba, last lba, plain bytes) of a scrambled boot file
        head = self.sector(self.base)
        if head[:16] != b"SEGA SEGAKATANA ":
            raise CdiError("la pista de datos no empieza por el IP.BIN de Dreamcast")
        # the boot file, descrambled as the BIOS would: every reader (identification, patch search, the image's
        # sectors) then sees the program the console runs
        self.scrambled = False
        try:
            lba, size = self.find(self.boot_file())
        except (KeyError, AssertionError):
            return
        data = self.sectors(lba, (size + 2047) // 2048)[:size]
        if self.boot_is_scrambled(data):
            plain = descramble(data)
            plain += bytes(-len(plain) % 2048)
            self._boot = (lba, lba + len(plain) // 2048, plain)
            self.scrambled = True

    def hd_tracks(self):
        """The tracks the game sees: all of them (a CD has a single area)."""
        return list(self.tracks)

    def data_tracks(self):
        return [t for t in self.tracks if t[2] == 4]

    def sector(self, lba):
        if self._boot and self._boot[0] <= lba < self._boot[1]:
            o = (lba - self._boot[0]) * 2048
            return self._boot[2][o:o + 2048]
        return self._raw_sector(lba)

    def _raw_sector(self, lba):
        for num, start, ctrl, ss, fn, n in reversed(self.tracks):
            if start <= lba < start + n:
                if ctrl != 4:
                    return bytes(2048)
                session, _, mode, _, _, _, off = self._where[num]
                self._f.seek(off + (lba - start) * ss)
                raw = self._f.read(min(ss, 2352))
                o = _user_data_offset(mode, ss, raw)
                return raw[o:o + 2048]
        return bytes(2048)

    def track_sectors(self, track):
        num, start, ctrl, ss, fn, n = track
        for i in range(n):
            yield start + i, self.sector(start + i)

    def boot_file(self):
        """The boot file IP.BIN names (normally 1ST_READ.BIN)."""
        name = self.sector(self.base)[0x60:0x70].split(b"\0")[0].decode("ascii", "replace").strip()
        return name or "1ST_READ.BIN"

    def boot_is_scrambled(self, data):
        """True when the boot file is scrambled. The scrambling moves 32-byte blocks, so text runs much longer than
        a block (48 bytes and up) only survive in the plain file; a plain Katana program also starts with nops
        (0x0009). A game "binhacked" for CD-R usually carries it plain (its IP.BIN loads it itself)."""
        import re

        def long_text(b):
            return len(re.findall(rb"[ -~]{48,}", b[:0x100000]))
        if data[:8] == bytes.fromhex("0900090009000900"):
            return False
        return long_text(descramble(data)) > 2 * long_text(data) + 2
