#!/bin/bash
# build_nesterse.sh RELEASE_DIR ROMS [OUT.bin]
#
# NesterDC SE (Scherzo, 2005: NES emulator for Dreamcast with JavaScript menus) for the NAOMI 2 (Crazy Taxi
# cabinet), REBUILT from its sources against the current KallistiOS. SE's own binary (KallistiOS 1.3, no NAOMI
# fixes) gave a black screen on the board.
#
#   RELEASE_DIR  the "plain files" folder of NesterDC SE v1.1 (Christuserloeser, 2008: NesterSEv11/), whose menus
#                (.js), fonts and graphics go on the disc. Its 1ST_READ.BIN, IP.BIN and NES/ are NOT used.
#   ROMS         a folder of .nes (sub-folders kept: the file browser shows them) or one .nes
#   OUT.bin      default build/nesterse_dc2naomict.bin (+ .gz)
#
# What it does:
#   1. KallistiOS 680d1862 + ../mk64/kos-680d1862-naomi_host.patch (own tree) and the kos-ports SE links with
#      (zlib, bzip2, libpng, libjpeg, kmg, imageload, parallax, modplug, oggvorbis, mp3).
#   2. SE's sources from 0skarzer0/NesterDC (NesterDCSE/, the 2005-12-24 source release) + nesterse-kos-modern.patch
#      (current gcc and KallistiOS; see the comments in it and HANDOFF.md) + nse_compat.h / nse_timer.c.
#   3. libdreamscript (the JavaScript engine, kjs) and the emulator, linked; 1ST_READ.BIN unscrambled.
#   4. Disc: RELEASE_DIR + our 1ST_READ.BIN + IP.BIN from makeip + the ROMs in NES/ (names without (..) / [..],
#      46 characters at most, as the release's readme asks), then dc2naomi with the profile nesterse.
#
# The AICA firmware is SE's prebuilt sound/aica_fw.h (no ARM toolchain needed). Nothing with copyright is in this
# repository. Needs: sh-elf GCC 13-15 in /opt/toolchains/dc/sh-elf, KOS_NAOMI_ENV (environ.sh of a KOS_SUBARCH=naomi
# tree, for dc2naomi's loader), git, curl, python3, genisoimage.
# Environment: WORK (default $HOME/nse-build), KOS_NAOMI_ENV (default /opt/toolchains/dc/kos/environ.sh), JOBS (3),
#              PROFILE (nesterse, or nesterse_dbg: KallistiOS log and diagnostics on screen).
set -eo pipefail   # (not -u: KallistiOS's environ.sh reads unset variables)
REL=$(realpath "${1:?usage: build_nesterse.sh RELEASE_DIR ROMS [OUT.bin]}")
ROMS=$(realpath "${2:?usage: build_nesterse.sh RELEASE_DIR ROMS [OUT.bin]}")
HERE=$(cd "$(dirname "$0")" && pwd)
D2N=$(cd "$HERE/../.." && pwd)
PROFILE=${PROFILE:-nesterse}
OUT=$(realpath -m "${3:-$D2N/build/${PROFILE}_dc2naomict.bin}")
WORK=${WORK:-$HOME/nse-build}
KOS_NAOMI_ENV=${KOS_NAOMI_ENV:-/opt/toolchains/dc/kos/environ.sh}
JOBS=${JOBS:-3}

KOS_URL=https://github.com/KallistiOS/KallistiOS.git
KOS_REV=680d1862
PORTS_URL=https://github.com/KallistiOS/kos-ports.git
PORTS_REV=f4faacc42faaf552625777b7709e871a827e1055
NDC_URL=https://github.com/0skarzer0/NesterDC.git
NDC_REV=c47eb5063f7cf7cf3fe36648f909abeddc337f23
PORTS="zlib libbz2 libpng libjpeg libkmg libimageload libparallax libmodplug liboggvorbisplay libmp3"

say() { echo; echo "== $*"; }
[ -f "$REL/main2.js" ] && [ -d "$REL/graphics" ] || { echo "$REL is not NesterDC SE's release folder (main2.js, graphics/)" >&2; exit 1; }
[ -f "$KOS_NAOMI_ENV" ] || { echo "no $KOS_NAOMI_ENV (KallistiOS with KOS_SUBARCH=naomi, for the loader)" >&2; exit 1; }
mkdir -p "$WORK"

# 1. KallistiOS + NAOMI_HOST, own tree; kos-ports in their own tree too
KOS=$WORK/kos
if [ ! -f "$KOS/lib/dreamcast/libkallisti.a" ] ||
   ! git -C "$KOS" apply -R --check "$D2N/homebrew/mk64/kos-680d1862-naomi_host.patch" 2>/dev/null; then
    say "KallistiOS $KOS_REV + NAOMI_HOST"
    [ -d "$KOS/.git" ] || git clone -q "$KOS_URL" "$KOS"
    git -C "$KOS" checkout -q -f "$KOS_REV"
    git -C "$KOS" apply "$D2N/homebrew/mk64/kos-680d1862-naomi_host.patch"
    sed -e "s#^export KOS_BASE=.*#export KOS_BASE=\"$KOS\"#" -e "s#^export KOS_PORTS=.*#export KOS_PORTS=\"$WORK/kos-ports\"#" \
        "$KOS/doc/environ.sh.sample" > "$KOS/environ.sh"
    sed -i 's#^export KOS_CFLAGS="${KOS_CFLAGS} -O2"#export KOS_CFLAGS="${KOS_CFLAGS} -DNAOMI_HOST"\n&#' "$KOS/environ.sh"
    grep -q NAOMI_HOST "$KOS/environ.sh"
    rm -f "$KOS/lib/dreamcast/libkallisti.a"
    (source "$KOS/environ.sh" && cd "$KOS" && make -j"$JOBS")
fi
source "$KOS/environ.sh" >/dev/null 2>&1
[ -d "$WORK/kos-ports/.git" ] || git clone -q "$PORTS_URL" "$WORK/kos-ports"
git -C "$WORK/kos-ports" checkout -q "$PORTS_REV"
# zlib.net keeps only the latest zlib: 1.3.2 from its GitHub releases (kos-ports checks size and SHA-256)
Z=$WORK/kos-ports/zlib/dist/zlib-1.3.2.tar.gz
if [ ! -f "$KOS_PORTS/lib/libz.a" ] && [ "$(stat -c %s "$Z" 2>/dev/null)" != 1502830 ]; then
    mkdir -p "$(dirname "$Z")"; curl -sfL -o "$Z" https://github.com/madler/zlib/releases/download/v1.3.2/zlib-1.3.2.tar.gz
fi
for p in $PORTS; do
    lib=$p.a; [ $p = zlib ] && lib=libz.a
    [ -f "$KOS_PORTS/lib/$lib" ] && continue
    say "kos-ports: $p"; (cd "$KOS_PORTS/$p" && make install clean)
done

# 2. SE's sources + our changes (fresh copy every time)
[ -d "$WORK/NesterDC/.git" ] || git clone -q "$NDC_URL" "$WORK/NesterDC"
git -C "$WORK/NesterDC" fetch -q origin 2>/dev/null || true
git -C "$WORK/NesterDC" checkout -q -f "$NDC_REV"
SRC=$WORK/src; rm -rf "$SRC"; mkdir -p "$SRC"
cp -r "$WORK/NesterDC/NesterDCSE/new_nesterdcse" "$WORK/NesterDC/NesterDCSE/libdreamscript" "$SRC/"
(cd "$SRC" && git init -q && git apply "$HERE/nesterse-kos-modern.patch")
cp "$HERE/nse_compat.h" "$HERE/nse_timer.c" "$SRC/new_nesterdcse/"

# 3. libdreamscript (installs into $KOS/addons/lib) and the emulator
say "libdreamscript"
CXXF="$KOS_CPPFLAGS -fpermissive -std=gnu++14"
make -C "$SRC/libdreamscript" -j"$JOBS" \
    KOS_CFLAGS="$KOS_CFLAGS -w -include ../new_nesterdcse/nse_compat.h -I. -Icore -Ikjs -I$KOS_PORTS/include" KOS_CPPFLAGS="$CXXF"
say "NesterDC SE"
cd "$SRC/new_nesterdcse"
OBJS="$(make -s --eval='printobjs: ; @echo $(OBJS)' printobjs) nse_timer.o"
make -j"$JOBS" $OBJS KOS_CPPFLAGS="$CXXF" KOS_CFLAGS="$KOS_CFLAGS -w -include nse_compat.h -D__DREAMCAST__ -I. \
    -I../libdreamscript -I$KOS_PORTS/include -I$KOS_BASE/kernel/arch/dreamcast/include/arch -O2"
kos-c++ -o nesterdcse.elf $KOS_START $OBJS -L"$KOS_PORTS/lib" -ldreamscript -lz -lstdc++ -lm -lkosutils -limageload \
    -lparallax -ljpeg -lkmg -lpng -lz -lbz2 -loggvorbisplay -lvorbis -logg -lmodplug -lmp3 $KOS_LIBS

# 4. disc and dc2naomi
DISC=$WORK/disc; rm -rf "$DISC"; mkdir -p "$DISC"
(cd "$REL" && find . -mindepth 1 -maxdepth 1 ! -iname 1ST_READ.BIN ! -iname IP.BIN ! -iname NES -exec cp -r {} "$DISC/" \;)
sh-elf-objcopy -R .stack -O binary nesterdcse.elf "$DISC/1ST_READ.BIN"
printf '%s\n' "Device Info   : CD-ROM1/1" "Area Symbols  : JUE" "Peripherals   : E000F10" "Product No    : T0000" \
    "Version       : V1.000" "Release Date  : 20261126" "Boot Filename : 1ST_READ.BIN" "SW Maker Name : NESTERSE NAOMI" \
    "Game Title    : NESTERDC SE" > "$WORK/ip.txt"
"$KOS/utils/makeip/makeip" "$WORK/ip.txt" "$DISC/IP.BIN" >/dev/null
python3 -I - "$ROMS" "$DISC/NES" <<'PY'
import os, re, shutil, sys
src, dst = sys.argv[1], sys.argv[2]
def clean(n, ext=""):
    n = re.sub(r" ?\([^)]*\)", "", n); n = re.sub(r" ?\[[^\]]*\]", "", n)
    return re.sub(r"[^A-Za-z0-9 ._!'+&,-]", "_", n).strip()[:46] + ext
def put(path, d):
    os.makedirs(d, exist_ok=True)
    base = clean(os.path.splitext(os.path.basename(path))[0]); name = base + ".nes"; i = 2
    while os.path.exists(os.path.join(d, name)): name = base[:43] + "~%d.nes" % i; i += 1
    shutil.copy(path, os.path.join(d, name))
n = 0
if os.path.isfile(src): put(src, dst); n = 1
for root, dirs, files in os.walk(src):
    dirs.sort(key=str.lower)
    rel = os.path.relpath(root, src)
    d = dst if rel == "." else os.path.join(dst, *[clean(p) for p in rel.split(os.sep)])
    for f in sorted(files, key=str.lower):
        if f.lower().endswith(".nes"): put(os.path.join(root, f), d); n += 1
print(n, "ROMs in NES/")
PY
say "dc2naomi: $PROFILE -> $OUT"
cd "$D2N"; mkdir -p "$(dirname "$OUT")"
(source "$KOS_NAOMI_ENV" && REBUILD=1 ./build.sh "$PROFILE" "$DISC" "$OUT")
python3 -I - "$OUT" <<'PY'
import gzip, os, sys
src = sys.argv[1]; name = os.path.basename(src)
with open(src + ".gz", "wb") as raw, gzip.GzipFile(filename=name, mode="wb", fileobj=raw, compresslevel=6, mtime=0) as gz:
    with open(src, "rb") as f:
        while (b := f.read(1 << 20)): gz.write(b)
print(src + ".gz", os.path.getsize(src + ".gz"), "bytes")
PY
