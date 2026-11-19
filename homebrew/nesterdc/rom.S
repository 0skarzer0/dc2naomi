	.section .rodata
	.balign 32
	.global _rom_start
	.global _rom_end
_rom_start:
	.incbin "game.nes"
_rom_end:
