#!/usr/bin/env python3
"""sfdbatch.py ORIG NEW [FRAC MIN MAX] : tools/sfdre.py on every .SFD under ORIG (as tools/discfiles.py copies them),
into NEW at the same paths, then checks each new movie: same number of pictures and of ADX audio packets (C0) as the
original (tools/sfdinfo.py), and ffmpeg decodes it without errors. kbit/s = FRAC x the bitrate in the movie's header,
kept between MIN and MAX (default 0.9, 2500, 5500: the best quality that still fit for Demolition Racer, TNN Hardcore
Heat, Tokyo Xtreme Racer 2 and MSR). The size depends little on the figure: those movies were mostly bitrate padding
(TNN 583 -> 157 MB). A movie of another kind (no BF packet, MPEG audio in C0: TNN's EU_ROLL.SFD) is better left out
of NEW. Then: tools/withfiles.py NEW --cab ct --batch JUEGO.chd
"""
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def info(path):
    t = subprocess.run([sys.executable, os.path.join(HERE, "sfdinfo.py"), path], capture_output=True, text=True).stdout
    br = re.search(r"bitrate en cabecera ([\d.]+) Mbit", t)
    c0 = re.search(r"'C0': (\d+)", t)
    pics = re.search(r"imágenes: (\d+)", t)
    return (float(br.group(1)) * 1000 if br else 3600), (c0.group(1) if c0 else "0", pics.group(1) if pics else "?")


def main(src, dst, frac=0.9, lo=2500, hi=5500):
    t0 = t1 = bad = 0
    for f in sorted(glob.glob(os.path.join(src, "**", "*.SFD"), recursive=True)):
        rel = os.path.relpath(f, src)
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        br, before = info(f)
        if br > 15000:                      # the VBR marker, not a rate
            br = 3600
        k = int(max(lo, min(hi, br * frac)))
        if not (os.path.exists(out) and os.path.getsize(out) > 1000):
            subprocess.run([sys.executable, os.path.join(HERE, "sfdre.py"), f, out, str(k)], check=True,
                           capture_output=True)
        after = info(out)[1]
        err = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-f", "null", "-"], capture_output=True,
                             text=True).stderr.strip()
        ok = before == after and not err
        bad += not ok
        a, b = os.path.getsize(f), os.path.getsize(out)
        t0, t1 = t0 + a, t1 + b
        print(f"{rel}: {a / 1048576:.1f} -> {b / 1048576:.1f} MB @{k} kbps"
              + ("" if ok else f"  DIFERENTE {before} {after} {err[:120]}"), flush=True)
    print(f"TOTAL {t0 / 1048576:.1f} -> {t1 / 1048576:.1f} MB; con diferencias: {bad}")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], *(float(a[2]), int(a[3]), int(a[4])) if len(a) > 4 else ())
