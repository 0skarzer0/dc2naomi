#!/bin/bash
# piup.sh FILE... : uploads files to /boot/roms/ of a netbooter Raspberry, resumably: each goes to NAME.part,
# appended from where it stopped (tail -c + ssh "cat >>"; the Pi has no rsync), then its md5 is checked against the
# local one and it is renamed over NAME. Stops itself after UP_SECONDS (default 150) so that it fits in a shell with
# a time limit per command: run it again with the same files until it prints TODO_SUBIDO.
# Environment: PIHOST, PIPASS (see pissh.sh). Over the user's Wi-Fi it went from 3 MB/s to 0.15 MB/s (2026-11-11).
D=$(cd "$(dirname "$0")" && pwd); T0=$(date +%s); LIMIT=${UP_SECONDS:-150}
pi() { "$D/pissh.sh" "$@" 2>/dev/null; }
for f in "$@"; do
  n=$(basename "$f"); size=$(stat -c %s "$f")
  [ "$(pi "cat /tmp/piup_done_$n 2>/dev/null")" = "$(md5sum < "$f" | cut -c1-32)" ] && { echo "$n: ya subido"; continue; }
  have=$(pi "stat -c %s /boot/roms/$n.part 2>/dev/null || echo 0")
  left=$(( LIMIT - ($(date +%s) - T0) )); [ $left -lt 15 ] && { echo "PAUSA: $n en $have/$size"; exit 0; }
  if [ "$have" -lt "$size" ]; then
    tail -c +$((have + 1)) "$f" | PISSH_OPTS="-c chacha20-poly1305@openssh.com" timeout $left "$D/pissh.sh" "cat >> /boot/roms/$n.part" 2>/dev/null
    have=$(pi "stat -c %s /boot/roms/$n.part")
  fi
  if [ "$have" -eq "$size" ]; then
    want=$(md5sum < "$f" | cut -c1-32); got=$(pi "md5sum < /boot/roms/$n.part | cut -c1-32")
    if [ "$want" = "$got" ]; then pi "mv -f /boot/roms/$n.part /boot/roms/$n && echo $got > /tmp/piup_done_$n"; echo "$n: OK md5 $got"
    else echo "$n: MD5 MAL ($got != $want): se borra y se repite"; pi "rm -f /boot/roms/$n.part"; fi
  else echo "PAUSA: $n en $have/$size ($(( have * 100 / size ))%)"; exit 0; fi
done
echo TODO_SUBIDO
