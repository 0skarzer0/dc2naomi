#!/usr/bin/env python3
"""cddascan.py DISC... : which games have their music as CD audio tracks (silent on the NAOMI: the resident does not
play CD-DA), without converting anything. Reads only each disc's track table (78 CHDs in 32 s). Prints, per disc,
the audio tracks in the high-density area of a GD-ROM (or every audio track of a .cdi) and their size, the ones with
music first. User's rule (HANDOFF, recipe 8b): with 2 or more such tracks the game is not converted for now. A single
track of 1 MB is the usual "this is a GD-ROM" warning, not music.

    python3 tools/cddascan.py ~/mnt/dc2naomi/dreamcastisos/*.chd
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdi import open_disc  # noqa: E402


def scan(path):
    d = open_disc(path)
    cdi = path.lower().endswith(".cdi")
    au = [t for t in d.tracks if t[2] != 4 and (cdi or t[1] >= 45000)]
    return len(au), sum(t[5] for t in au) * 2352 >> 20


def main(paths):
    rows = []
    for p in paths:
        try:
            n, mb = scan(p)
            rows.append((n, mb, os.path.basename(p)))
        except Exception as e:                       # noqa: BLE001 - report and go on
            rows.append((-1, 0, f"{os.path.basename(p)}: {e}"))
    for n, mb, name in sorted(rows, key=lambda r: (-r[0], r[2])):
        verdict = "SIN MÚSICA (CD-DA)" if n >= 2 else ("error" if n < 0 else "ok")
        print(f"{verdict:19s} {max(n, 0):3d} pistas {mb:5d} MB  {name}")


if __name__ == "__main__":
    main(sys.argv[1:])
