#!/bin/bash
# dis.sh FILE BASE START END
sh-elf-objdump -D -b binary -m sh4 -EL --adjust-vma=0x$2 --start-address=0x$3 --stop-address=0x$4 $1 | tail -n +8
