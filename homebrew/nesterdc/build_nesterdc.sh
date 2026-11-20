#!/bin/bash
# build_nesterdc.sh ROMS [OUT.bin]      ROMS = one .nes, a folder of .nes, or several .nes separated by commas
#
# NesterDC (NES emulator, https://github.com/pqrs-org/NesterDC) for the NAOMI 2 (Crazy Taxi cabinet).
# Nester's core (CPU, PPU, APU, mappers) is compiled with the current sh-elf-gcc; the Dreamcast frontend of
# NesterDC (KallistiOS 1.1.8, its own AICA firmware, menus) is NOT used: ndc_main.cpp is a minimal new one
# (PVR video, snd_stream audio, maple pads, ROM menu) written for KallistiOS 680d1862 + the NAOMI_HOST patch of
# ../mk64. The ROMs are linked into the program (fs_ramdisk): the image holds the games you give it (menu at boot;
# START + wheel to the right in a game = back to the menu). Pads profile "nes" (resident.c).
#
# Nothing with copyright is in the repository. UNTESTED ON THE BOARD at the time of writing (see HANDOFF.md).
#
# Needs: sh-elf GCC in /opt/toolchains/dc/sh-elf, KOS_NAOMI_ENV (environ.sh of the KOS_SUBARCH=naomi tree, for
# dc2naomi's loader), git, patch, python3, genisoimage.
# Environment: WORK (default $HOME/ndc-build), KOS_NAOMI_ENV (default /opt/toolchains/dc/kos/environ.sh), JOBS (3).
set -eo pipefail
ROMS=${1:?usage: build_nesterdc.sh ROMS [OUT.bin]}
HERE=$(cd "$(dirname "$0")" && pwd)
D2N=$(cd "$HERE/../.." && pwd)
OUT=$(realpath -m "${2:-$D2N/build/nesterdc_dc2naomict.bin}")
WORK=${WORK:-$HOME/ndc-build}
KOS_NAOMI_ENV=${KOS_NAOMI_ENV:-/opt/toolchains/dc/kos/environ.sh}
JOBS=${JOBS:-3}
SHBIN=/opt/toolchains/dc/sh-elf/bin
say() { echo; echo "== $*"; }
mkdir -p "$WORK"
if [ -d "$ROMS" ]; then LIST=$(find "$ROMS" -iname '*.nes' | sort); else LIST=$(echo "$ROMS" | tr ',' '\n'); fi
[ -n "$LIST" ] || { echo "no .nes found in $ROMS" >&2; exit 1; }
while read -r r; do [ "$(head -c4 "$r")" = $'NES\x1a' ] || { echo "$r is not an iNES file" >&2; exit 1; }; done <<< "$LIST"

# 1. KallistiOS 680d1862 + NAOMI_HOST (own tree), built as a Dreamcast (pristine) target
KOS=$WORK/kos-ndc
if [ ! -f "$KOS/lib/dreamcast/libkallisti.a" ]; then
    say "KallistiOS 680d1862 + NAOMI_HOST"
    [ -d "$KOS/.git" ] || git clone -q --filter=blob:none https://github.com/KallistiOS/KallistiOS.git "$KOS"
    git -C "$KOS" checkout -q 680d1862
    git -C "$KOS" diff --quiet && git -C "$KOS" apply "$D2N/homebrew/mk64/kos-680d1862-naomi_host.patch"
    sed -e "s#^export KOS_BASE=.*#export KOS_BASE=\"$KOS\"#" -e "s#^export KOS_PORTS=.*#export KOS_PORTS=\"$WORK/kos-ports\"#" \
        "$KOS/doc/environ.sh.sample" > "$KOS/environ.sh"
    sed -i 's#^export KOS_CFLAGS="${KOS_CFLAGS} -O2"#export KOS_CFLAGS="${KOS_CFLAGS} -DNAOMI_HOST"\n&#' "$KOS/environ.sh"
    grep -q NAOMI_HOST "$KOS/environ.sh"
    (source "$KOS/environ.sh" && cd "$KOS" && make -j"$JOBS")
fi

# 2. NesterDC sources + our changes
if [ ! -d "$WORK/NesterDC/.git" ]; then git clone -q --depth 1 https://github.com/pqrs-org/NesterDC "$WORK/NesterDC"; fi
SRC=$WORK/src; mkdir -p "$SRC"
if [ ! -f "$SRC/compat.h" ]; then
    N=$WORK/NesterDC/nester
    cp -r "$N/nes" "$N/debug" "$N/types.h" "$N/nester.h" "$N/screen_mgr.h" "$N/sound_mgr.h" "$N/null_sound_mgr.h" "$N/version.h" "$SRC/"
    patch -s -p1 -d "$SRC" < "$HERE/nester-kos-modern.patch"
fi

# 3. the core (fragments that other files #include are not compiled on their own)
say "Nester core"
source "$KOS/environ.sh" >/dev/null 2>&1
INC="-I$SRC -I$SRC/debug -I$SRC/nes -I$SRC/nes/ppu -I$SRC/nes/apu -I$SRC/nes/cpu -I$SRC/nes/external_device -I$SRC/nes/libsnss -I$SRC/nes/mapper"
OBJ=$WORK/obj; mkdir -p "$OBJ"
(cd "$SRC" && find nes debug \( -name '*.c' -o -name '*.cpp' \) | grep -v -E 'sound_tables|nes_exsound|nes_mmc5|nes_fds|nes_vrc7|nes_vrc6|nes_fme7|nes_n106|nes_rom_correct|nes_set_controller|nes_set_cycles|nes_emulate_frame|do_scanline|render_' | sort) |
while read -r f; do
    n=$(echo "$f" | tr / _)
    case $f in *.cpp) cc="$SHBIN/sh-elf-g++ -std=gnu++14 -fpermissive";; *) cc="$SHBIN/sh-elf-gcc";; esac
    $cc -w -O2 -ml -m4-single-only -fno-exceptions -fno-rtti -include "$SRC/compat.h" -include "$SRC/types.h" $INC -D__DREAMCAST__ -c "$SRC/$f" -o "$OBJ/$n.o"
done

# 4. frontend + ROM + link
say "frontend and ROM"
APP=$WORK/app; rm -rf "$APP"; mkdir -p "$APP"; cp "$HERE/ndc_main.cpp" "$HERE/font8x16.h" "$APP/"
cd "$APP"
$SHBIN/sh-elf-g++ $KOS_CFLAGS -std=gnu++14 -fpermissive -w -fno-exceptions -fno-rtti $INC -c ndc_main.cpp -o ndc_main.o
kos-c++ -o ndc.elf $KOS_START ndc_main.o "$OBJ"/*.o $KOS_LIBS

# 5. disc as files, then dc2naomi
DISC=$WORK/disc; rm -rf "$DISC"; mkdir -p "$DISC"
$SHBIN/sh-elf-objcopy -R .stack -O binary ndc.elf "$DISC/1ST_READ.BIN"
# the ROMs go on the disc as files (read when chosen), not inside the program: 1ST_READ.BIN is read by PIO at boot
mkdir -p "$DISC/ROMS"
# ROMS.TXT keeps the folder structure of the collection: "d|f <TAB> id <TAB> parent id (-1 = root) <TAB> name"
python3 -I - "$ROMS" "$DISC" <<'PY'
import os, re, shutil, sys
root, disc = sys.argv[1], sys.argv[2]
def clean(n):
    n = re.sub(r" ?\([^)]*\)", "", n); n = re.sub(r" ?\[[^\]]*\]", "", n)
    return re.sub(r"[^A-Za-z0-9 ._!'+-]", "_", n)[:54]
rows = []; nid = [0]
def walk(d, parent):
    for e in sorted(os.listdir(d), key=str.lower):
        p = os.path.join(d, e)
        if os.path.isdir(p):
            i = nid[0]; nid[0] += 1; rows.append("d\t%d\t%d\t%s" % (i, parent, clean(e))); walk(p, i)
        elif e.lower().endswith(".nes"):
            i = nid[0]; nid[0] += 1
            shutil.copy(p, os.path.join(disc, "ROMS", "%03d.NES" % i))
            rows.append("f\t%d\t%d\t%s" % (i, parent, clean(os.path.splitext(e)[0])))
if os.path.isdir(root): walk(root, -1)
else:
    for p in root.split(","):
        i = nid[0]; nid[0] += 1
        shutil.copy(p, os.path.join(disc, "ROMS", "%03d.NES" % i))
        rows.append("f\t%d\t-1\t%s" % (i, clean(os.path.splitext(os.path.basename(p))[0])))
open(os.path.join(disc, "ROMS.TXT"), "w").write("\n".join(rows) + "\n")
PY
"$KOS/utils/makeip/makeip" "$HERE/ip.txt" "$DISC/IP.BIN" 2>/dev/null || /opt/toolchains/dc/kos/utils/makeip/makeip "$HERE/ip.txt" "$DISC/IP.BIN"
say "dc2naomi: nesterdc -> $OUT"
cd "$D2N"; mkdir -p "$(dirname "$OUT")"
(source "$KOS_NAOMI_ENV" && REBUILD=1 ./build.sh nesterdc "$DISC" "$OUT")
python3 -I - "$OUT" <<'PY'
import gzip, os, sys
src = sys.argv[1]; name = os.path.basename(src)
with open(src + ".gz", "wb") as raw, gzip.GzipFile(filename=name, mode="wb", fileobj=raw, compresslevel=6, mtime=0) as gz:
    with open(src, "rb") as f:
        while (b := f.read(1 << 20)): gz.write(b)
print(src + ".gz", os.path.getsize(src + ".gz"), "bytes")
PY
