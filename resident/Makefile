CC = /opt/toolchains/dc/sh-elf/bin/sh-elf-gcc
OBJCOPY = /opt/toolchains/dc/sh-elf/bin/sh-elf-objcopy
CFLAGS = -m4-single -ml -Os -ffreestanding -fno-builtin -nostdlib -Wall -Wextra -fno-pic -fomit-frame-pointer
all: resident.bin
resident.elf: head.S resident.c resident.h link.ld
	$(CC) $(CFLAGS) -T link.ld -o $@ head.S resident.c
resident.bin: resident.elf
	$(OBJCOPY) -O binary $< $@
	/opt/toolchains/dc/sh-elf/bin/sh-elf-nm $< | grep -E " _(maple_hook|boot_entry|res_table)$$"
clean:
	rm -f resident.elf resident.bin
