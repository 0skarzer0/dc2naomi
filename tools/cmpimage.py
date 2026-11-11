#!/usr/bin/env python3
"""cmpimage.py DISC IMAGE.bin[.gz] : checks a built image against its source disc (.chd, .gdi, .cdi), the way the
resident will serve it: header (IP.BIN FAD, boot file, TOC), IP.BIN, the ISO9660 volume, and every file's sectors
(files the profile left out, and padding files, are expected to read as zeros). Prints what differs."""
import gzip
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdi import open_disc  # noqa: E402
from gensig import ImageDisc  # noqa: E402


def main(src, image):
    disc = open_disc(src)
    if image.endswith(".gz"):                         # random access needs the plain file
        tmp = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
        with gzip.open(image, "rb") as g:
            shutil.copyfileobj(g, tmp, 1 << 22)
        tmp.close()
        image = tmp.name
    img = ImageDisc(image)
    bad = 0

    def check(what, ok):
        nonlocal bad
        print(("ok    " if ok else "MAL   ") + what)
        bad += not ok

    check(f"IP.BIN en la LBA {img.base} (disco: {disc.base})", img.base == disc.base)
    check("IP.BIN igual", img.sectors(img.base, 16) == disc.sectors(disc.base, 16))
    check("volumen ISO9660 igual", img.sectors(img.base + 16, 32) == disc.sectors(disc.base + 16, 32))
    boot = disc.boot_file() if hasattr(disc, "boot_file") else "1ST_READ.BIN"
    blba, bsize = disc.find(boot)
    check(f"{boot}: FAD {img.boot_fad} y {img.boot_size} bytes", img.boot_fad == blba + 150 and img.boot_size == bsize)
    check(f"{boot} igual (el que corre la consola)", img.read_file(boot) == disc.read_file(boot))
    print(f"      TOC: primera pista {img.first_track}, " + ", ".join(f"{e:#010x}" for e in img.toc)
          + f", fin {img.leadout_fad}")
    toc_fad = img.toc[0] & 0xFFFFFF
    check(f"la primera pista de la TOC contiene el IP.BIN (FAD {toc_fad} <= {img.base + 150})",
          toc_fad <= img.base + 150 < img.leadout_fad)
    filler = set(disc.filler_files()) if hasattr(disc, "filler_files") else set()
    n = same = zero = 0
    diff = []
    for path, lba, size in disc.walk():
        n += 1
        a = img.sectors(lba, (size + 2047) // 2048)[:size]
        if a == disc.read_file(path):
            same += 1
        elif not a.strip(b"\0") and path in filler:
            zero += 1
        else:
            diff.append(path)
    check(f"archivos: {n}, iguales {same}, relleno omitido {zero}, distintos {len(diff)}", not diff)
    for p in diff[:10]:
        print("      distinto:", p)
    if image != sys.argv[2]:
        os.unlink(image)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
