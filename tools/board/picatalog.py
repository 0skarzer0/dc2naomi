#!/usr/bin/env python3
"""picatalog.py [STATUS.csv] > docs/piXXX-juegos.md: the list of games on a netbooter Raspberry, as Markdown.

Reads over SSH (paramiko) /boot/config/romsinfo.csv and the names in /boot/roms/ of the Raspberry in PIHOST
(environment: PIHOST, PIPASS; never write the password in a file) and writes one table per kind of image (by the
file name prefix): file, description from the CSV, controls, whether it has a .vmu, and a status column. The
status comes from STATUS.csv (lines "file name without .bin.gz,status,note"; status: ok, test, warn, or empty)
when given; otherwise it is left as "?" to be filled by hand from the HANDOFF. Rows whose file is missing and
files with no row are listed at the end.

Made for the standard cabinet's Raspberry (.250, docs/pi250-juegos.md), the same as naomi-wheel-games'
docs/pi60-juegos.md for the Crazy Taxi cabinet. Example:
    PIHOST=192.168.68.250 PIPASS=... python3 tools/board/picatalog.py docs/pi250-estado.csv > docs/pi250-juegos.md
"""
import csv
import datetime
import io
import os
import sys

import paramiko

KINDS = [
    ("dc-", "Juegos de Dreamcast convertidos con dc2naomi"),
    ("h-", "Ports y homebrew"),
    ("n1-", "Originales de NAOMI"),
    ("n2-", "Originales de NAOMI 2"),
    ("aw-", "Atomiswave convertidos"),
    ("ch-", "Chihiro"),
    ("tf-", "Triforce"),
    ("", "Otros"),
]
MARK = {"ok": "✅", "test": "🧪", "warn": "⚠️", "": "?"}


def run(c, cmd):
    _, o, _ = c.exec_command(cmd, timeout=60)
    return o.read().decode(errors="replace")


def main():
    status = {}
    if len(sys.argv) > 1:
        for r in csv.reader(open(sys.argv[1], encoding="utf-8")):
            if r and not r[0].startswith("#"):
                status[r[0]] = (r[1] if len(r) > 1 else "", r[2] if len(r) > 2 else "")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(os.environ["PIHOST"], username="root", password=os.environ["PIPASS"], timeout=8,
              look_for_keys=False, allow_agent=False)
    rows = list(csv.reader(io.StringIO(run(c, "cat /boot/config/romsinfo.csv"))))[1:]
    roms = set(run(c, "ls /boot/roms").split())
    listed = {r[1] for r in rows if len(r) > 1}
    print("# Juegos cargados en la Raspberry %s (%s)\n" % (os.environ["PIHOST"], datetime.date.today()))
    print("Generado con `tools/board/picatalog.py` (lee el CSV y la carpeta de juegos de la Raspberry). "
          "Leyenda: ✅ funciona en la placa · 🧪 subido, sin probar en placa · ⚠️ con problemas conocidos · "
          "? sin dato. Las credenciales de acceso no se guardan en ningún repositorio.\n")
    done = set()
    for prefix, title in KINDS:
        sel = [r for r in rows if len(r) > 11 and r[1] in roms and r[1] not in done and r[1].startswith(prefix)]
        if not sel:
            continue
        print("## %s\n\n| Fichero | Juego | Mandos | VMU | Estado |\n|---|---|---|---|---|" % title)
        for r in sorted(sel, key=lambda r: r[4].lower()):
            done.add(r[1])
            stem = r[1][:-len(".bin.gz")] if r[1].endswith(".bin.gz") else r[1]
            st, note = status.get(stem, ("", ""))
            vmu = "sí" if stem + ".vmu" in roms else ""
            print("| `%s` | %s | %s | %s | %s%s |" % (stem, r[4], r[11], vmu, MARK.get(st, st),
                                                     " " + note if note else ""))
        print()
    orphan = sorted(r[1] for r in rows if len(r) > 1 and r[1] not in roms)
    unlisted = sorted(x for x in roms if x.endswith(".bin.gz") and x not in listed)
    if orphan or unlisted:
        print("## Revisar\n")
        for x in orphan:
            print("- Fila del CSV sin fichero: `%s`" % x)
        for x in unlisted:
            print("- Fichero sin fila en el CSV (no sale en el menú): `%s`" % x)


if __name__ == "__main__":
    main()
