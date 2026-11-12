#!/usr/bin/env python3
"""findsave.py SAVES_DIR WORD... : candidate saves for a game in a clone of bucanero/dreamcast-saves (the user's
rule: every new game gets a save with everything unlocked, of the same region). For each folder whose name contains
one of the words it lists every .VMI with the save's file name, its short and long titles and its line of
SAVELIST.TXT. Choosing the region: the file name the game writes tells it (Soulcalibur SCALIBUR_MBU = USA, _MBE =
Europe; Dynamite Cop D_COP_US / D_COP_PL; Japanese titles in Shift-JIS = Japan); a save of another region is usually
not seen by the game.

    git clone --depth 1 --filter=blob:none --no-checkout https://github.com/bucanero/dreamcast-saves saves
    cd saves && git sparse-checkout set --no-cone FOLDER... && git checkout   (git ls-tree -d --name-only HEAD: folders)
    python3 tools/findsave.py saves garou kof
    python3 tools/vmutool.py import JUEGO_dc2naomi.vmu saves/garou/garou1.VMI --batch
"""
import glob
import os
import sys


def main(root, words):
    for d in sorted(os.listdir(root)):
        if not os.path.isdir(os.path.join(root, d)) or not any(w.lower() in d.lower() for w in words):
            continue
        notes = {}
        sl = os.path.join(root, d, "SAVELIST.TXT")
        if os.path.exists(sl):
            for line in open(sl, encoding="latin-1"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    notes[k.strip().upper()] = v.strip()
        print(f"## {d}")
        for p in sorted(glob.glob(os.path.join(root, d, "*.[Vv][Mm][Ii]"))):
            vmi = open(p, "rb").read()
            fname = vmi[0x58:0x64].split(b"\0")[0].decode("latin-1")
            vms = [q for q in os.listdir(os.path.dirname(p)) if q.upper() == os.path.basename(p)[:-4].upper() + ".VMS"]
            head = open(os.path.join(os.path.dirname(p), vms[0]), "rb").read(48) if vms else b""
            short = head[:16].decode("shift_jis", "replace").strip()
            long_ = head[16:48].decode("shift_jis", "replace").strip()
            print(f"  {os.path.basename(p):14s} {fname:13s} | {short:16s} | {long_:32s} | "
                  f"{notes.get(os.path.basename(p).upper(), '')[:90]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
