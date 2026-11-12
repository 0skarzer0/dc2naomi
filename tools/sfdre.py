#!/usr/bin/env python3
"""sfdre.py ORIG.SFD OUT.SFD KBPS : re-encode the MPEG-1 video of a Sofdec movie at the same size and frame rate,
keeping the header packs and every ADX audio packet (and its pack SCR) byte for byte. The new video packets take
the slots of the original video packets, at the same pace of pictures, with the original's PES layout (12-byte
header: STD 0x602e + PTS/DTS on the packet where a picture starts, payload 2018 bytes)."""
import os, re, struct, subprocess, sys

PACK, PES_BODY, HDR = 2048, 2030, 12
PAY = PES_BODY - HDR

def ts_bytes(prefix, t):
    return bytes([(prefix << 4) | (((t >> 30) & 7) << 1) | 1,
                  (t >> 22) & 0xFF, (((t >> 15) & 0x7F) << 1) | 1, (t >> 7) & 0xFF, ((t & 0x7F) << 1) | 1])

def pictures(es):
    """[(chunk_start, type, tref, gop_index)] in decode order; a chunk includes the sequence/GOP headers before it."""
    out, gop, last = [], -1, 0
    marks = [(m.start(), es[m.start() + 3]) for m in re.finditer(b"\0\0\1[\x00\xb3\xb8]", es)]
    pending = None
    for pos, code in marks:
        if code in (0xB3, 0xB8):
            if code == 0xB8:
                gop += 1
            if pending is None:
                pending = pos
            continue
        t = "IPB"[((es[pos + 5] >> 3) & 7) - 1]
        tref = (es[pos + 4] << 2) | (es[pos + 5] >> 6)
        out.append((pending if pending is not None else pos, pos, t, tref, gop))
        pending = None
    return out

def stamps(pics, tick=3750):
    """(pts, dts or None) per picture, as the MPEG-1 decoder model wants them: DTS one frame (3750 at 24 fps) per
    picture in decode order, PTS = (display index + 1) frames (a B picture's PTS equals its DTS: PTS only)."""
    gop_len = {}
    for _, _, _, _, g in pics:
        gop_len[g] = gop_len.get(g, 0) + 1
    before, acc = {}, 0
    for g in sorted(gop_len):
        before[g] = acc; acc += gop_len[g]
    res = []
    for i, (_, _, t, tref, g) in enumerate(pics):
        pts, dts = (before[g] + tref + 1) * tick, i * tick
        assert dts <= pts, (i, t, pts, dts)
        res.append((pts, None) if t == "B" else (pts, dts))
    return res

def orig_packs(path):
    b = open(path, "rb").read()
    return b, [b[i:i + PACK] for i in range(0, len(b), PACK)]

def probe(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "csv=p=0", src], capture_output=True, text=True,
                         check=True).stdout.strip().split(",")
    num, den = map(int, out[2].split("/"))
    return int(out[0]), int(out[1]), out[2], round(90000 * den / num)

def main(src, dst, kbps):
    raw, packs = orig_packs(src)
    w, h, rate, tick = probe(src)
    num, den = (rate.split("/") + ["1"])[:2]               # each decoded picture numbered in turn: no picture
                                                           # added or dropped (the originals' timestamps jump)
    std = next(pk[18:] for pk in packs if pk[12:16] == b"\0\0\1\xe0")
    j = 0
    while std[j] == 0xFF:
        j += 1
    std = std[j:j + 2]                                     # the original's STD buffer field (0x60 0x2e)
    # the original's picture pattern: GOP length and whether it uses B pictures (Rainbow Cotton: 15 with B; Buzz
    # Lightyear: 12, I and P only); its bitrate as the ceiling
    oes = b"".join(pk[30:] for pk in packs if pk[12:16] == b"\0\0\1\xe0")
    otypes = ["IPB"[((oes[m.start() + 5] >> 3) & 7) - 1] for m in re.finditer(b"\0\0\1\0", oes[:4 << 20])
              if m.start() + 5 < len(oes)]
    istarts = [i for i, t in enumerate(otypes) if t == "I"]
    gop = max(1, min(30, istarts[1] - istarts[0])) if len(istarts) > 1 else 15
    bframes = 2 if "B" in otypes else 0
    vbr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=bit_rate",
                          "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
    maxrate = max(int(vbr) // 1000 if vbr.isdigit() else 0, 3600, kbps)   # 3600: what Rainbow Cotton used
    m1v = dst + ".m1v"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-c:v", "mpeg1video", "-b:v", f"{kbps}k",
                    "-maxrate", f"{maxrate}k", "-bufsize", "327680", "-g", str(gop), "-bf", str(bframes), "-s", f"{w}x{h}",
                    "-vf", f"setpts=N*{den}/({num}*TB)", "-r", rate, "-sc_threshold", "1000000000", "-f", "mpeg1video", m1v], check=True)
    es = open(m1v, "rb").read(); os.unlink(m1v)
    pics = pictures(es); st = stamps(pics, tick)
    starts = [p[1] for p in pics]                          # picture start code offsets (for PTS placement)
    ends = [p[0] for p in pics[1:]] + [len(es)]            # end of each picture's chunk
    # original: how many pictures have started by the end of each video packet
    out = bytearray(); emitted = 0; seen = 0; pi = 0; last_hdr = None
    orig_pics = 0
    def video_packet(hdr12):
        nonlocal emitted, pi
        chunk = es[emitted:emitted + PAY]
        while pi < len(starts) and starts[pi] < emitted:
            pi += 1
        if pi < len(starts) and starts[pi] < emitted + len(chunk):
            pts, dts = st[pi]
            h = std + (ts_bytes(3, pts) + ts_bytes(1, dts) if dts is not None else b"\xff" * 5 + ts_bytes(2, pts))
            if dts is None:
                h = b"\xff" * 5 + std + ts_bytes(2, pts)
        else:
            h = b"\xff" * 9 + std + b"\x0f"
        assert len(h) == HDR
        body = h + chunk
        if len(chunk) < PAY:                               # the last one: shorter packet + padding packet
            pes = b"\0\0\1\xe0" + struct.pack(">H", len(body)) + body
            rest = PACK - 12 - len(pes)
            pad = (b"\0\0\1\xbe" + struct.pack(">H", rest - 6) + b"\xff" * (rest - 6)) if rest >= 6 else b"\xff" * rest
            pkt = hdr12 + pes + pad
        else:
            pkt = hdr12 + b"\0\0\1\xe0" + struct.pack(">H", PES_BODY) + body
        assert len(pkt) == PACK, len(pkt)
        emitted += len(chunk)
        return pkt
    tail = b""
    vidx = [n for n, pk in enumerate(packs) if pk[12:16] == b"\0\0\1\xe0"]
    pays, offs, acc = [], [], 0
    for n in vidx:
        pk = packs[n]; body = pk[18:18 + struct.unpack(">H", pk[16:18])[0]]; j = 0
        while body[j] == 0xFF:
            j += 1
        if body[j] & 0xC0 == 0x40:
            j += 2
        k = body[j] >> 4
        j += 10 if k == 3 else 5 if k == 2 else 1
        offs.append(acc); pays.append(body[j:]); acc += len(body) - j
    oes = b"".join(pays)
    import bisect
    started = [0] * len(vidx)                              # pictures started in each original video packet
    for m in re.finditer(b"\0\0\1\0", oes):
        started[bisect.bisect_right(offs, m.start()) - 1] += 1
    vpos = {n: i for i, n in enumerate(vidx)}
    for n, pk in enumerate(packs):
        if pk[:4] == b"\0\0\1\xb9":                        # the end pack (end code + 0xFF)
            tail = pk; continue
        if n in vpos:
            last_hdr = pk[:12]
            orig_pics += started[vpos[n]]
            target = ends[min(orig_pics, len(pics)) - 1] if orig_pics else 0
            while emitted < target:
                out += video_packet(last_hdr)
        else:
            out += pk                                      # headers, Sofdec private stream, ADX audio: as they are
    while emitted < len(es):
        out += video_packet(last_hdr)
    out += tail
    open(dst, "wb").write(out)
    print(f"{os.path.basename(src)}: {len(raw)/1048576:.1f} -> {len(out)/1048576:.1f} MB, pictures {len(pics)} "
          f"(original {orig_pics}), {w}x{h} {rate} GOP {gop}{' B' if bframes else ''}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
