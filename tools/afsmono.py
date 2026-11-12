#!/usr/bin/env python3
"""afsmono.py IN.AFS OUT.AFS [--half-rate] : the same AFS archive (CRI's file pack: "AFS\\0", count, then offset/size of
each entry) with every stereo ADX in it made mono by tools/adxmono (built on first use with gcc), so that a game's
music and voices take half as much. Entries keep their order and number; they are laid out again from the same first
offset (the table area the game reads stays the same size), each aligned to 2048 bytes like the original, and the
table gets their new offsets and sizes. Entries that are not ADX are copied as they are. An attribute table (names)
after the entries, if there is one, is copied after the last entry with its pointer updated.
Used for Metropolis Street Racer: SOUND/{VOICE,TOKYO,LONDON,SANFRAN}.AFS, 248 stereo ADX at 44.1 kHz (430 MB).

    python3 tools/afsmono.py ORIG/SOUND/TOKYO.AFS NEW/SOUND/TOKYO.AFS
    python3 tools/withfiles.py NEW --cab ct --batch "MSR.chd"
"""
import os
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def adxmono_bin():
    exe = os.path.join(tempfile.gettempdir(), "adxmono_dc2naomi")
    src = os.path.join(HERE, "adxmono.c")
    if not os.path.exists(exe) or os.path.getmtime(exe) < os.path.getmtime(src):
        subprocess.run(["gcc", "-O2", "-o", exe, src, "-lm"], check=True)
    return exe


def main(src, dst, half=False):
    b = open(src, "rb").read()
    assert b[:4] == b"AFS\0", "no es un AFS"
    n = struct.unpack_from("<I", b, 4)[0]
    ent = [struct.unpack_from("<II", b, 8 + 8 * i) for i in range(n)]
    attr = struct.unpack_from("<II", b, 8 + 8 * n)
    first = min(o for o, s in ent)
    exe = adxmono_bin()
    out = bytearray(b[:first])
    tmp = tempfile.mkdtemp()
    news, done = [], 0
    for i, (o, s) in enumerate(ent):
        data = b[o:o + s]
        if data[:2] == b"\x80\x00" and data[4] == 3 and (data[7] == 2 or half):
            fi, fo = os.path.join(tmp, "i.adx"), os.path.join(tmp, "o.adx")
            open(fi, "wb").write(data)
            subprocess.run([exe, fi, fo] + (["--half-rate"] if half else []), check=True)
            data = open(fo, "rb").read()
            done += 1
        out += bytes(-len(out) % 2048)
        news.append((len(out), len(data)))
        out += data
    out += bytes(-len(out) % 2048)
    for i, (o, s) in enumerate(news):
        struct.pack_into("<II", out, 8 + 8 * i, o, s)
    if attr[0] and attr[1]:
        struct.pack_into("<II", out, 8 + 8 * n, len(out), attr[1])
        out += b[attr[0]:attr[0] + attr[1]]
        out += bytes(-len(out) % 2048)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst, "wb").write(out)
    print(f"{os.path.basename(src)}: {n} entradas, {done} ADX a mono, {len(b) / 1048576:.1f} -> {len(out) / 1048576:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--half-rate" in sys.argv[3:])
