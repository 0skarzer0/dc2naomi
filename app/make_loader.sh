#!/bin/bash
# Rebuilds app/loader.bin (KallistiOS loader + resident) after a change in resident/ or loader/.
# The program patches the game title into it; the image is otherwise the same for every game.
set -e
cd "$(dirname "$0")/.."
make -s -C resident
[ -n "$KOS_BASE" ] || source /opt/toolchains/dc/kos/environ.sh
make -s -C loader clean >/dev/null
make -s -C loader TITLE="DC2NAOMI"
cp loader/loader.bin app/loader.bin
echo "app/loader.bin: $(stat -c %s app/loader.bin) bytes"
