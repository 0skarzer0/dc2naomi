#!/usr/bin/env python3
"""sfdinfo.py FILE.SFD ... : what a Sofdec movie is made of, to check it before and after tools/sfdre.py: pack sizes,
packets per stream (BB system header, BE padding, BF the "SofdecStream" private one, C0 ADX audio, E0 MPEG-1 video),
PES timestamp kinds, the video's size / rate / bitrate field, picture types in decode order, GOP pattern and the
first timestamps. The movies seen so far (Rainbow Cotton, Buzz Lightyear) are 2048-byte packs with one 2030-byte
packet each, three header packs, and a last pack of 000001B9 + 0xFF."""
import collections
import re
import struct
import sys


def ts(b):
    return ((b[0] >> 1) & 7) << 30 | (struct.unpack(">H", b[1:3])[0] >> 1) << 15 | struct.unpack(">H", b[3:5])[0] >> 1


def info(path):
    b = open(path, "rb").read()
    packs, streams, kinds, es, stamps = [], collections.Counter(), collections.Counter(), [], []
    i = 0
    while i < len(b) - 4:
        if b[i:i + 3] != b"\0\0\1":
            i += 1
            continue
        sid = b[i + 3]
        if sid == 0xBA:
            packs.append(i)
            i += 12
            continue
        if sid == 0xB9:
            streams["B9 fin"] += 1
            i += 4
            continue
        ln = struct.unpack(">H", b[i + 4:i + 6])[0]
        body = b[i + 6:i + 6 + ln]
        streams["%02X" % sid] += 1
        if sid in (0xC0, 0xE0):
            j = 0
            while body[j] == 0xFF:
                j += 1
            if body[j] & 0xC0 == 0x40:
                j += 2
            k = body[j] >> 4
            if k == 3:
                kinds["%02X PTS+DTS" % sid] += 1
                if sid == 0xE0:
                    stamps.append((ts(body[j:j + 5]), ts(body[j + 5:j + 10])))
                j += 10
            elif k == 2:
                kinds["%02X PTS" % sid] += 1
                if sid == 0xE0:
                    stamps.append((ts(body[j:j + 5]), None))
                j += 5
            else:
                kinds["%02X sin marca" % sid] += 1
                j += 1
            if sid == 0xE0:
                es.append(body[j:])
        i += 6 + ln
    es = b"".join(es)
    sizes = collections.Counter(packs[k + 1] - packs[k] for k in range(len(packs) - 1))
    print(f"== {path}: {len(b)} bytes, {len(packs)} packs, tamaños {dict(sizes.most_common(3))}")
    print("   paquetes:", dict(streams), "| marcas:", dict(kinds))
    k = es.find(b"\0\0\1\xb3")
    if k >= 0:
        w, h = (es[k + 4] << 4) | (es[k + 5] >> 4), ((es[k + 5] & 15) << 8) | es[k + 6]
        rate = {1: "23.976", 2: "24", 3: "25", 4: "29.97", 5: "30", 6: "50", 7: "59.94", 8: "60"}.get(es[k + 7] & 15, "?")
        br = ((es[k + 8] << 10) | (es[k + 9] << 2) | (es[k + 10] >> 6)) * 400
        print(f"   vídeo: {w}x{h}, {rate} fps, bitrate en cabecera {br / 1e6:.2f} Mbit/s")
    pics = [(m.start(), "IPBD"[((es[m.start() + 5] >> 3) & 7) - 1]) for m in re.finditer(b"\0\0\1\0", es)
            if m.start() + 5 < len(es)]
    types = "".join(t for _, t in pics)
    istarts = [n for n, t in enumerate(types) if t == "I"]
    gops = collections.Counter(istarts[n + 1] - istarts[n] for n in range(len(istarts) - 1))
    print(f"   imágenes: {len(pics)} ({dict(collections.Counter(types))}), GOP {dict(gops.most_common(3))}")
    print(f"   orden: {types[:40]}… | primeras marcas (PTS, DTS): {stamps[:6]}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        info(p)
