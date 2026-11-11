#!/bin/bash
# run_seq.sh GDI SECONDS NAME T0 "key key ..." [gap] : type a key sequence quickly at T0, dump RAM at the end
cd /home/claude/fctest
export DISPLAY=:99 SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1 HOME=/home/claude/fctest/home
pgrep -x Xvfb >/dev/null || { Xvfb :99 -screen 0 800x600x24 >/dev/null 2>&1 & sleep 1; }
/home/claude/flycast/build/flycast -config config:Dynarec.Enabled=yes $EXTRA -config log:LogToConsole=yes -config log:Verbosity=3 "$1" > $3.log 2>&1 & FP=$!
sleep $4
W=$(xdotool search --pid $FP | head -1); xdotool windowactivate --sync $W 2>/dev/null; xdotool windowfocus $W 2>/dev/null
for k in $5; do xdotool keydown $k; sleep ${6:-0.15}; xdotool keyup $k; sleep ${6:-0.15}; done
sleep 2; import -window root -resize 320x240 $3.png
REM=$(( $2 - $4 - 5 )); [ $REM -gt 0 ] && sleep $REM
import -window root -resize 320x240 $3b.png
RAM=$(grep "RAM(16 MB)" $3.log | tail -1 | sed -E 's/.*RAM\(16 MB\) (0x[0-9a-f]+).*/\1/'); gdb -p $FP -batch -ex "dump binary memory /tmp/ram_$3.bin $RAM $RAM+0x1000000" >/dev/null 2>&1
kill $FP 2>/dev/null; sleep 1; kill -9 $FP 2>/dev/null
