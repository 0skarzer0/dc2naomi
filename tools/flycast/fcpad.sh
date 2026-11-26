#!/bin/bash
# fcpad.sh IMAGE CONTROLLERS NAME KEYS [SECONDS]: what a button combination gives the game (homebrew ports of N64
# decompilations, Mario Kart 64 2026-11-26). Runs IMAGE in Flycast with run1.sh, presses KEYS (run1.sh's format,
# e.g. '30:k:45,60:Return:12' = gas from 30 s for 45 s, START from 60 s for 12 s), dumps the RAM at the end (keep the
# keys held past SECONDS, default 66) and prints the game's first controller: struct Controller { s16 rawStickX,
# rawStickY; u16 button; ... } at CONTROLLERS (sh-elf-nm build/*.elf | grep gControllers).
# Needs the Flycast of flycast-dc2naomi-debug.patch: FC_PEDALS=1 (set here) = pedals idle, k = full gas;
# FC_PEDALS_BRK=1 (set it outside) = k is the brake instead. FCTEST, FCBIN as for run1.sh.
cd "$(dirname "$0")"
rm -f /tmp/ram.bin
KEYS="$4" FC_SYSM_RAM=1 FC_PEDALS=1 STEP=${STEP:-11} DUMP=1 bash run1.sh "$1" "${5:-66}" "$3" >/dev/null 2>&1
python3 - "$2" "$3" <<'PY'
import struct, sys
d = open("/tmp/ram.bin", "rb").read()
o = int(sys.argv[1], 0) - 0x8c000000
sx, sy, btn = struct.unpack("<hhH", d[o:o + 6])
names = {0x8000: "A", 0x4000: "B", 0x2000: "Z", 0x1000: "START", 0x0800: "D-up", 0x0400: "D-down", 0x0200: "D-left",
         0x0100: "D-right", 0x0020: "L", 0x0010: "R", 0x0008: "C-up", 0x0004: "C-down", 0x0002: "C-left",
         0x0001: "C-right"}
print(sys.argv[2], "stick", sx, sy, "buttons", " ".join(n for m, n in names.items() if btn & m) or "-")
PY
