#!/bin/bash
# build_mk64.sh BASEROM.z64 [OUT.bin]
#
# Mario Kart 64 for the NAOMI 2 (Crazy Taxi cabinet), from the Dreamcast port of the N64 decompilation:
#   https://github.com/jnmartin84/mk64-dc  (commit 1cbad2ef, 2026-08-23)
# built against KallistiOS 680d1862 with this folder's patch (NAOMI_HOST), then packed by dc2naomi
# (profile "mk64" in tools/games.py, rebuilt-disc layout). See HANDOFF.md, "Mario Kart 64".
#
# Nothing with copyright is in this repository: you need your own ROM, Mario Kart 64 (U) [!].z64,
# MD5 3a67d9986f54eb282924fca4cd5f6dff (the one mk64-dc asks for). The game's code is downloaded from
# its author's repository; ROM-derived files stay in $WORK.
#
# Needs: sh-elf GCC 13-15 in /opt/toolchains/dc/sh-elf (KallistiOS dc-chain), a KallistiOS with
# KOS_SUBARCH=naomi for dc2naomi's loader (KOS_NAOMI_ENV), git, python3, cmake, ninja, a host C/C++
# compiler, libbz2-dev, genisoimage. Tested on Ubuntu 22.04 with sh-elf-gcc 15.2.0.
#
# Environment (all optional):
#   WORK          where everything is cloned and built        (default: $HOME/mk64-build)
#   KOS_NAOMI_ENV environ.sh of the KOS_SUBARCH=naomi tree     (default: /opt/toolchains/dc/kos/environ.sh)
#   JOBS          parallel jobs                                 (default: 3)
#   PROFILE       dc2naomi profile: mk64, or mk64_dbg (on-screen log and diagnostics)
set -eo pipefail   # (not -u: KallistiOS's environ.sh reads unset variables)

BASEROM=$(realpath "${1:?usage: build_mk64.sh BASEROM.z64 [OUT.bin]}")
HERE=$(cd "$(dirname "$0")" && pwd)
D2N=$(cd "$HERE/../.." && pwd)
PROFILE=${PROFILE:-mk64}
OUT=$(realpath -m "${2:-$D2N/build/${PROFILE}_dc2naomict.bin}")
WORK=${WORK:-$HOME/mk64-build}
KOS_NAOMI_ENV=${KOS_NAOMI_ENV:-/opt/toolchains/dc/kos/environ.sh}
JOBS=${JOBS:-3}

MK64_URL=https://github.com/jnmartin84/mk64-dc.git
MK64_REV=1cbad2ef2d45c49f782ecadeddbbd49063a3507e
KOS_URL=https://github.com/KallistiOS/KallistiOS.git
KOS_REV=680d1862
PORTS_URL=https://github.com/KallistiOS/kos-ports.git
PORTS_REV=f4faacc42faaf552625777b7709e871a827e1055

say() { echo; echo "== $*"; }

[ "$(md5sum "$BASEROM" | cut -c1-32)" = 3a67d9986f54eb282924fca4cd5f6dff ] || {
    echo "$BASEROM is not Mario Kart 64 (U) [!].z64 (MD5 3a67d998...). For the Spanish patch see HANDOFF.md." >&2
    exit 1; }
[ -f "$KOS_NAOMI_ENV" ] || { echo "no $KOS_NAOMI_ENV (KallistiOS with KOS_SUBARCH=naomi, for the loader)" >&2; exit 1; }
mkdir -p "$WORK"

# 1. KallistiOS 680d1862 with the NAOMI_HOST patch, in its own tree (never the one the loader uses)
KOS=$WORK/kos-mk64
if [ ! -f "$KOS/lib/dreamcast/libkallisti.a" ]; then
    say "KallistiOS $KOS_REV + NAOMI_HOST"
    [ -d "$KOS/.git" ] || git clone -q "$KOS_URL" "$KOS"
    git -C "$KOS" checkout -q "$KOS_REV"
    git -C "$KOS" diff --quiet && git -C "$KOS" apply "$HERE/kos-680d1862-naomi_host.patch"
fi
# mk64-dc's own environ.sh, pointed at these trees, plus -DNAOMI_HOST (KOS itself and the game see it)
[ -d "$WORK/mk64-dc/.git" ] || git clone -q "$MK64_URL" "$WORK/mk64-dc"
git -C "$WORK/mk64-dc" checkout -q "$MK64_REV"
sed -e "s#KOS_BASE=\"/opt/toolchains/dc/kos\"#KOS_BASE=\"$KOS\"#" \
    -e "s#KOS_PORTS=\"\${KOS_BASE}/../kos-ports\"#KOS_PORTS=\"$WORK/kos-ports-mk64\"#" \
    "$WORK/mk64-dc/environ.sh" > "$KOS/environ.sh"
grep -q NAOMI_HOST "$KOS/environ.sh" || sed -i 's#^export KOS_CFLAGS="${KOS_CFLAGS} -O3#export KOS_CFLAGS="${KOS_CFLAGS} -DNAOMI_HOST"\n&#' "$KOS/environ.sh"
grep -q NAOMI_HOST "$KOS/environ.sh"
if [ ! -f "$KOS/lib/dreamcast/libkallisti.a" ]; then
    (cd "$KOS" && source ./environ.sh && make -j"$JOBS")
fi

# 2. kos-ports: only sh4zam (the game's math and mixer library)
if [ ! -f "$WORK/kos-ports-mk64/lib/libsh4zam.a" ]; then
    say "kos-ports: sh4zam"
    [ -d "$WORK/kos-ports-mk64/.git" ] || git clone -q "$PORTS_URL" "$WORK/kos-ports-mk64"
    git -C "$WORK/kos-ports-mk64" checkout -q "$PORTS_REV"
    (source "$KOS/environ.sh" && cd "$WORK/kos-ports-mk64/sh4zam" && make install)
fi

# 3. the host tools: Torch (asset extractor, HarbourMasters) and the decomp's tools
cd "$WORK/mk64-dc"
git submodule update --init tools/torch
if [ ! -x tools/torch/cmake-build-release/torch ]; then
    say "Torch"
    cmake -S tools/torch -B tools/torch/cmake-build-release -GNinja -DCMAKE_BUILD_TYPE=Release
    cmake --build tools/torch/cmake-build-release -j"$JOBS"
fi
make -C tools

# 4. assets from your ROM, then the game
cp "$BASEROM" baserom.us.z64
source "$KOS/environ.sh"
if [ ! -d dc_data ] || [ ! -f assets/character_select/mario/mario_face_00.png ]; then
    say "assets"
    make assets
fi
say "game"
# The .mio0 textures are prerequisites of the wrong objects in the asset makefiles, so a parallel make can
# assemble data/textures_0a.s before they exist ("file not found: assets/.../mario_face_00.mio0"). Build the
# objects those makefiles name first, then everything.
OBJS=$(grep -h -oE '\$\(BUILD_DIR\)/[A-Za-z0-9_$()/.-]+\.o' assets/include/*.mk assets/include/*/*.mk |
       sort -u | sed 's#\$(BUILD_DIR)#build/us#; s#\$(DATA_DIR)#data#')
make -j"$JOBS" $OBJS
rm -f build/mario-kart.elf mk64.bin loader.elf loader.bin
make -j"$JOBS"
make IP.BIN loader.bin mk64.bin
for f in build/mario-kart.elf loader.elf; do
    printf "%-22s naomi_live at 0x%s\n" "$f" "$("$KOS_CC_BASE/bin/$KOS_CC_PREFIX-nm" "$f" | awk '/ _naomi_live$/{print $1}')"
done

# 5. the disc as files (dc2naomi's "rebuild" layout): IP.BIN, 1ST_READ.BIN = loader.bin (not scrambled),
#    mk64.bin, the icons and dc_data/
DISC=$WORK/disc
rm -rf "$DISC"; mkdir -p "$DISC"
cp IP.BIN "$DISC/"; cp loader.bin "$DISC/1ST_READ.BIN"
cp mk64.bin ghost.ico kart.ico "$DISC/"; cp -r dc_data "$DISC/"

# 6. the NAOMI image (dc2naomi's loader is built with the KOS_SUBARCH=naomi tree)
say "dc2naomi: $PROFILE -> $OUT"
cd "$D2N"
mkdir -p "$(dirname "$OUT")"
(source "$KOS_NAOMI_ENV" && REBUILD=1 ./build.sh "$PROFILE" "$DISC" "$OUT")
python3 -I - "$OUT" <<'PY'
import gzip, os, sys
src = sys.argv[1]; name = os.path.basename(src)
with open(src + ".gz", "wb") as raw, gzip.GzipFile(filename=name, mode="wb", fileobj=raw, compresslevel=6, mtime=0) as gz:
    with open(src, "rb") as f:
        while (b := f.read(1 << 20)): gz.write(b)
print(src + ".gz", os.path.getsize(src + ".gz"), "bytes")
PY
echo "For the WiPi: /boot/roms/dc-${PROFILE}_dc2naomict.bin.gz and a row in romsinfo.csv (see HANDOFF.md)."
