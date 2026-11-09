"""Read a GD-ROM CHD (MAME's Compressed Hunks of Data, version 5) without chdman.

Only what dc2naomi needs: the track list (CHGD metadata) and the 2048-byte user data of the data
sectors. Hunks are decompressed with the CD codecs chdman uses for GD-ROMs: cdlz (LZMA), cdzl
(deflate) and cdfl (FLAC: audio only, read as silence, never needed). Uncompressed hunks and
"copy of another hunk" entries are handled; parent CHDs are not.
Format: MAME src/lib/util/chd.cpp, chdcodec.cpp, cdrom.cpp (BSD-3-Clause).
"""
import lzma
import struct
import zlib

FRAME = 2448          # 2352 bytes of sector + 96 of subcode
SECTOR = 2352

# map entry types (v5)
C0, C1, C2, C3, NONE, SELF, PARENT, RLE_SMALL, RLE_LARGE, SELF_0, SELF_1, PARENT_SELF, PARENT_0, PARENT_1 = range(14)


class ChdError(Exception):
    pass


class _Bits:
    """MSB-first bit reader (chd.cpp bitstream_in); reads past the end give zeros."""

    def __init__(self, data):
        self.data = data
        self.pos = 0  # in bits

    def read(self, n):
        v = 0
        for _ in range(n):
            byte = self.pos >> 3
            bit = (self.data[byte] >> (7 - (self.pos & 7))) & 1 if byte < len(self.data) else 0
            v = (v << 1) | bit
            self.pos += 1
        return v


class _Huffman:
    """huffman_decoder<numcodes, maxbits> with import_tree_rle (canonical codes)."""

    def __init__(self, bits, numcodes=16, maxbits=8):
        nb = 5 if maxbits >= 16 else 4 if maxbits >= 8 else 3
        lens = []
        while len(lens) < numcodes:
            n = bits.read(nb)
            if n != 1:
                lens.append(n)
            else:
                n = bits.read(nb)
                if n == 1:
                    lens.append(1)
                else:
                    rep = bits.read(nb) + 3
                    lens.extend([n] * rep)
        if len(lens) != numcodes:
            raise ChdError("bad huffman tree")
        histo = [0] * 33
        for n in lens:
            if n > maxbits:
                raise ChdError("bad huffman tree")
            histo[n] += 1
        start = 0
        for ln in range(32, 0, -1):
            nxt = (start + histo[ln]) >> 1
            if ln != 1 and nxt * 2 != start + histo[ln]:
                raise ChdError("bad huffman tree")
            histo[ln] = start
            start = nxt
        self.codes = {}
        for code, n in enumerate(lens):
            if n > 0:
                self.codes[(n, histo[n])] = code
                histo[n] += 1
        self.maxbits = maxbits

    def decode(self, bits):
        v = 0
        for n in range(1, self.maxbits + 1):
            v = (v << 1) | bits.read(1)
            c = self.codes.get((n, v))
            if c is not None:
                return c
        raise ChdError("bad huffman code")


def _fourcc(v):
    return struct.pack(">I", v).decode("latin-1") if v else ""


class Chd:
    def __init__(self, path):
        self.f = open(path, "rb")
        h = self.f.read(124)
        if h[:8] != b"MComprHD":
            raise ChdError("not a CHD file")
        version = struct.unpack_from(">I", h, 12)[0]
        if version != 5:
            raise ChdError(f"CHD version {version}: only version 5 is supported (convert it with a recent chdman)")
        self.codecs = [_fourcc(x) for x in struct.unpack_from(">4I", h, 16)]
        self.logical, self.mapoff, self.metaoff = struct.unpack_from(">3Q", h, 32)
        self.hunkbytes, self.unitbytes = struct.unpack_from(">2I", h, 56)
        if any(h[104:124]):
            raise ChdError("this CHD needs a parent CHD (not supported)")
        self.hunks = (self.logical + self.hunkbytes - 1) // self.hunkbytes
        self._read_map()
        self._cache = {}

    # ------------------------------------------------------------ map
    def _read_map(self):
        n = self.hunks
        self.map = []  # (type, length, offset)
        if not self.codecs[0]:
            self.f.seek(self.mapoff)
            raw = self.f.read(4 * n)
            for i in range(n):
                off = struct.unpack_from(">I", raw, 4 * i)[0]
                self.map.append((NONE, self.hunkbytes, off * self.hunkbytes) if off else (C0, 0, 0))
            self._uncompressed = True
            return
        self._uncompressed = False
        self.f.seek(self.mapoff)
        mh = self.f.read(16)
        mapbytes = struct.unpack_from(">I", mh, 0)[0]
        firstoffs = int.from_bytes(mh[4:10], "big")
        lengthbits, selfbits, parentbits = mh[12], mh[13], mh[14]
        bits = _Bits(self.f.read(mapbytes))
        huff = _Huffman(bits)
        types = []
        last, rep = 0, 0
        for _ in range(n):
            if rep > 0:
                types.append(last)
                rep -= 1
                continue
            v = huff.decode(bits)
            if v == RLE_SMALL:
                types.append(last)
                rep = 2 + huff.decode(bits)
            elif v == RLE_LARGE:
                types.append(last)
                rep = 2 + 16 + (huff.decode(bits) << 4)
                rep += huff.decode(bits)
            else:
                types.append(v)
                last = v
        cur = firstoffs
        last_self = last_parent = 0
        for i, t in enumerate(types):
            length, off = 0, 0
            if t in (C0, C1, C2, C3):
                length = bits.read(lengthbits)
                off = cur
                cur += length
                bits.read(16)
            elif t == NONE:
                length = self.hunkbytes
                off = cur
                cur += length
                bits.read(16)
            elif t == SELF:
                last_self = off = bits.read(selfbits)
            elif t == PARENT:
                last_parent = off = bits.read(parentbits)
            elif t == SELF_1:
                last_self += 1
                t, off = SELF, last_self
            elif t == SELF_0:
                t, off = SELF, last_self
            elif t in (PARENT_SELF, PARENT_0, PARENT_1):
                t = PARENT
            self.map.append((t, length, off))

    # ------------------------------------------------------------ hunks
    def hunk(self, i):
        c = self._cache.get(i)
        if c is not None:
            return c
        t, length, off = self.map[i]
        if t == SELF:
            data = self.hunk(off)
        elif t == PARENT:
            raise ChdError("this CHD needs a parent CHD (not supported)")
        elif t == NONE:
            self.f.seek(off)
            data = self.f.read(self.hunkbytes)
        elif self._uncompressed:
            data = bytes(self.hunkbytes)
        else:
            self.f.seek(off)
            data = self._decompress(self.codecs[t], self.f.read(length))
        if len(self._cache) > 64:
            self._cache.clear()
        self._cache[i] = data
        return data

    def _decompress(self, codec, src):
        """CD codecs: [ecc flags][base length][base data: frames*2352][subcode]. Only the sector part is
        rebuilt; the sync/ECC chdman removed are not put back (dc2naomi reads bytes 16-2063 only)."""
        hb = self.hunkbytes
        frames = hb // FRAME
        if codec == "cdfl":
            return bytes(hb)  # audio (FLAC): never read by dc2naomi
        if codec not in ("cdlz", "cdzl"):
            raise ChdError(f"CHD codec '{codec}' not supported here: re-create it with chdman createcd")
        lenbytes = 2 if hb < 65536 else 3
        eccbytes = (frames + 7) // 8
        base = int.from_bytes(src[eccbytes:eccbytes + lenbytes], "big")
        comp = src[eccbytes + lenbytes:eccbytes + lenbytes + base]
        want = frames * SECTOR
        if codec == "cdlz":
            d = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=[
                {"id": lzma.FILTER_LZMA1, "dict_size": 1 << 24, "lc": 3, "lp": 0, "pb": 2}])
            sec = d.decompress(comp, want)
        else:
            sec = zlib.decompressobj(-15).decompress(comp, want)
        if len(sec) < want:
            sec += bytes(want - len(sec))
        out = bytearray(hb)
        for k in range(frames):
            out[k * FRAME:k * FRAME + SECTOR] = sec[k * SECTOR:(k + 1) * SECTOR]
        return bytes(out)

    def frame(self, n):
        """2448-byte frame n (logical unit) of the CHD."""
        per = self.hunkbytes // FRAME
        h = self.hunk(n // per)
        o = (n % per) * FRAME
        return h[o:o + FRAME]

    # ------------------------------------------------------------ metadata
    def metadata(self):
        out = []
        off = self.metaoff
        while off:
            self.f.seek(off)
            tag, flen, nxt = struct.unpack(">IIQ", self.f.read(16))
            out.append((_fourcc(tag), self.f.read(flen & 0xFFFFFF)))
            off = nxt
        return out

    def gd_tracks(self):
        """[(number, type, frames, first CHD frame)] from the CHGD metadata (tracks padded to 4 frames)."""
        tracks = []
        for tag, data in self.metadata():
            if tag not in ("CHGD", "CHT2", "CHTR"):
                continue
            kv = {}
            for p in data.rstrip(b"\0").decode("latin-1").split():
                if ":" in p:
                    k, v = p.split(":", 1)
                    kv[k] = v
            tracks.append((int(kv["TRACK"]), kv["TYPE"], int(kv["FRAMES"]), tag))
        if not tracks or tracks[0][3] != "CHGD":
            raise ChdError("not a GD-ROM CHD (no GD-ROM track list): is it a Dreamcast disc?")
        tracks.sort()
        out = []
        pos = 0
        for num, typ, frames, _tag in tracks:
            out.append((num, typ, frames, pos))
            pos += (frames + 3) & ~3
        return out
