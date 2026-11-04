OUTPUT_ARCH(sh)
ENTRY(_res_table)
SECTIONS
{
    . = 0x8dc00000;
    .vectors : { KEEP(*(.vectors)) }
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    . = ALIGN(4);
    __bss_start = .;
    .bss : { *(.bss .bss.* COMMON) }
    . = ALIGN(4);
    __bss_end = .;
    /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
