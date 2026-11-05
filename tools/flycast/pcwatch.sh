#!/bin/bash
# pcwatch.sh IMAGE SECONDS STEP : debug Flycast (interpreter), PC/PR every STEP s, screenshot at the end
cd ${FCTEST:-$(dirname "$0")}
export DISPLAY=:99 SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1 HOME=${FCTEST:-$(dirname "$0")}/home
[ -n "$NAOMI2" ] && export FC_NAOMI2=1 || unset FC_NAOMI2
[ -n "$MIEPATCH" ] && export FC_MIE_NODEVINFO=1
pgrep -x Xvfb >/dev/null || { Xvfb :99 -screen 0 800x600x24 >/dev/null 2>&1 & sleep 1; }
${FCDBG:-../flycast/build-dbg/flycast} -config config:Dynarec.Enabled=${DYNAREC:-no} -config log:LogToConsole=yes -config log:Verbosity=${VERB:-3} "$1" > pc.log 2>&1 & FP=$!
for ((t=$3; t<=$2; t+=$3)); do sleep $3
  echo "t=$t $(gdb -p $FP -batch -ex 'p/x p_sh4rcb->cntx.pc' -ex 'p/x p_sh4rcb->cntx.pr' 2>/dev/null | grep '^\$' | tr '\n' ' ')"
done
import -window root -resize 400x300 pcw.png
RAM=$(grep "RAM(32 MB)" pc.log | sed -E 's/.*RAM\(32 MB\) (0x[0-9a-f]+).*/\1/')
[ -n "$DUMP" ] && gdb -p $FP -batch -ex "dump binary memory /tmp/ram.bin $RAM $RAM+0x2000000" >/dev/null 2>&1
kill -9 $FP
