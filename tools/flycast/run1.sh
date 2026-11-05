#!/bin/bash
# run1.sh IMAGE SECONDS NAME : Flycast headless (NAOMI 2 BIOS), screenshots every 5 s -> NAME.png grid, log NAME.log
cd ${FCTEST:-$(dirname "$0")}
[ -n "$MIEPATCH" ] && export FC_MIE_NODEVINFO=1
export DISPLAY=:99 SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1 HOME=${FCTEST:-$(dirname "$0")}/home
[ -n "$NAOMI2" ] && export FC_NAOMI2=1 || unset FC_NAOMI2
pgrep -x Xvfb >/dev/null || { Xvfb :99 -screen 0 800x600x24 >/dev/null 2>&1 & sleep 1; }
rm -f /tmp/fc_dump_now
${FCBIN:-../flycast/build/flycast} -config config:Dynarec.Enabled=${DYNAREC:-yes} $EXTRA -config log:LogToConsole=yes -config log:Verbosity=${VERB:-3} "$1" > $3.log 2>&1 & FP=$!
# KEYS="t:key[:hold],...": key presses at second t (xdotool names: Return = START, c = coin, k = accel, j/l = steer)
IFS=',' read -ra EV <<< "${KEYS:-}"
L=""; for ((t=1; t<=$2; t++)); do sleep 1
  for e in "${EV[@]}"; do IFS=':' read -r et ek eh <<< "$e"
    [ "$et" == "$t" ] && { W=$(xdotool search --pid $FP | head -1); [ -n "$W" ] && xdotool windowactivate --sync $W 2>/dev/null; xdotool windowfocus $W 2>/dev/null; ( xdotool keydown $ek; sleep ${eh:-0.2}; xdotool keyup $ek ) & }; done
  if (( t % ${STEP:-5} == 0 )); then import -window root -resize 320x240 /tmp/$3_$t.png; L="$L /tmp/$3_$t.png"; fi
done
if [ -n "$DUMP" ]; then RAM=$(grep "RAM(32 MB)" $3.log | sed -E 's/.*RAM\(32 MB\) (0x[0-9a-f]+).*/\1/'); gdb -p $FP -batch -ex "dump binary memory /tmp/ram.bin $RAM $RAM+0x2000000" >/dev/null 2>&1; fi
kill $FP 2>/dev/null; sleep 1; kill -9 $FP 2>/dev/null
montage $L -tile 4x -geometry +2+2 $3.png 2>/dev/null || convert $L +append $3.png
