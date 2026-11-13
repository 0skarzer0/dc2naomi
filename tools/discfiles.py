#!/usr/bin/env python3
"""discfiles.py DISC [OUT_DIR SUFFIX...] : what a game's files take, and copies of some of them.

    discfiles.py JUEGO.chd                  total, by extension, by folder, the 8 biggest files (does it fit in 512 MB?)
    discfiles.py JUEGO.chd ORIG .SFD .AFS   copies every file ending in one of the suffixes to ORIG/<its disc path>
                                            (for tools/sfdbatch.py, afsmono.py, rushstr.py, then withfiles.py)
The total is the sum of the files; the image comes out about that size (filler files left out make it smaller).
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gdi  # noqa: E402


def main(disc, out=None, suffixes=()):
    d = gdi.open_disc(disc)
    files = list(d.walk())
    if out is None:
        mb = 1048576
        print(f"{disc}: {len(files)} archivos, {sum(s for _, _, s in files) / mb:.1f} MB")
        ext, top = collections.Counter(), collections.Counter()
        for p, _, s in files:
            ext[os.path.splitext(p)[1].upper() or "(sin)"] += s
            top[p.split("/")[0] if "/" in p else "(raíz)"] += s
        print("  por extensión:", ", ".join(f"{k} {v / mb:.0f} MB" for k, v in ext.most_common(8)))
        print("  por carpeta:", ", ".join(f"{k} {v / mb:.0f}" for k, v in top.most_common(8)))
        for p, _, s in sorted(files, key=lambda x: -x[2])[:8]:
            print(f"   {s / mb:7.1f} MB  {p}")
        return
    for p, lba, size in files:
        if any(p.upper().endswith(x.upper()) for x in suffixes):
            o = os.path.join(out, p)
            os.makedirs(os.path.dirname(o), exist_ok=True)
            with open(o, "wb") as f:
                for i in range((size + 2047) // 2048):
                    f.write(d.sector(lba + i))
                f.truncate(size)
            print(p, size)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1] if len(a) > 1 else None, a[2:])
