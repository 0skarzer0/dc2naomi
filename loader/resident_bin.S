    .section .rodata
    .balign 32
    .global _resident_bin
    .global _resident_bin_end
_resident_bin:
    .incbin "../resident/resident.bin"
_resident_bin_end:
