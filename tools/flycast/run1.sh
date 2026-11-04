#!/bin/bash
# run1.sh IMAGE SECONDS NAME : Flycast headless (NAOMI 2 BIOS), screenshots every 5 s -> NAME.png grid, log NAME.log
cd ${FCTEST:-$(dirname "$0")}
[ -n "$MIEPATCH" ] && export FC_MIE_NODEVINFO=1
export DISPLAY=:99 SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1 HOME=${FCTEST:-$(dirname "$0")}/home FC_NAOMI2=${FC_NAOMI2-1}
pgrep -x Xvfb >/dev/null || { Xvfb :99 -screen 0 800x600x24 >/dev/null 2>&1 & sleep 1; }
rm -f /tmp/fc_dump_now
${FCBIN:-../flycast/build/flycast} -config config:Dynarec.Enabled=${DYNAREC:-yes} $EXTRA -config log:LogToConsole=yes -config log:Verbosity=${VERB:-3} "$1" > $3.log 2>&1 & FP=$!
L=""; for ((t=${STEP:-5}; t<=$2; t+=${STEP:-5})); do sleep ${STEP:-5}; import -window root -resize 320x240 /tmp/$3_$t.png; L="$L /tmp/$3_$t.png"; done
kill $FP 2>/dev/null; sleep 1; kill -9 $FP 2>/dev/null
montage $L -tile 4x -geometry +2+2 $3.png 2>/dev/null || convert $L +append $3.png
