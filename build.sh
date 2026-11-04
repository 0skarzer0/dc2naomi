#!/bin/bash
# rebuild resident + loader + image
set -e
cd /home/claude/work/dc-daytona/naomi
make -s -C resident 2>&1 | grep -E "error" || true
source /opt/toolchains/dc/kos/environ.sh >/dev/null
make -s -C loader 2>&1 | grep -E "error|warning" || true
python3 tools/build_image.py ../files ../build loader/loader.bin ../build/daytona_dc_naomi.bin | tail -1
