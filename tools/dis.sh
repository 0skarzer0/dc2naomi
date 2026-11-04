#!/bin/bash
# dis.sh START END  (hex) - disassemble a range of 1ST_READ
/opt/toolchains/dc/sh-elf/bin/sh-elf-objdump -D -b binary -m sh4 -EL --adjust-vma=0x8c010000 --start-address=0x$1 --stop-address=0x$2 /home/claude/work/dc-daytona/files/1ST_READ.BIN | tail -n +8
