#!/bin/bash
# ./build.sh GAME SOURCE [OUT.bin]
#   GAME   daytona | ysgw (tools/games.py)
#   SOURCE the .gdi of your dump (ysgw) or the directory of the disc's files (daytona)
# Needs KallistiOS (KOS_SUBARCH=naomi) for the loader; any sh-elf-gcc for the resident part.
set -e
cd "$(dirname "$0")"
GAME=${1:?game}; SRC=${2:?source}; OUT=${3:-build/$GAME.bin}
mkdir -p build/$GAME
TITLE=$(python3 -c "import sys; sys.path.insert(0,'tools'); from games import GAMES; print(GAMES['$GAME']['title'])")
make -s -C resident
[ -n "$KOS_BASE" ] || source /opt/toolchains/dc/kos/environ.sh
make -s -C loader clean >/dev/null; make -s -C loader TITLE="$TITLE"
python3 tools/build_image.py "$GAME" "$SRC" build/$GAME loader/loader.bin "$OUT"
