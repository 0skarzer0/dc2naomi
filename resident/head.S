/* The resident part's entry table and the bits that need assembly. */
    .section .vectors, "ax"
    .global _res_table
_res_table:
    .long 0x524c4344        /* "DCLR" */
    .long _boot_entry
    .long _maple_hook
    .long __bss_start
    .long __bss_end

    .text
    .align 2
/* boot_entry(header): onto our own stack, clear our bss, boot(). */
    .global _boot_entry
_boot_entry:
    mov.l   .Lstack, r15
    mov.l   .Lbss_start, r0
    mov.l   .Lbss_end, r1
    mov     #0, r2
1:  cmp/hs  r1, r0
    bt      2f
    mov.l   r2, @r0
    bra     1b
    add     #4, r0
2:  mov.l   .Lboot, r0
    jmp     @r0             /* boot() never returns */
    nop
    .align 2
.Lstack:     .long 0x8dcffff0
.Lbss_start: .long __bss_start
.Lbss_end:   .long __bss_end
.Lboot:      .long _boot

/* The font syscall takes its command in r1. */
    .global _font_stub
_font_stub:
    mov.l   .Lfont, r0
    jmp     @r0
    mov     r1, r4
    .align 2
.Lfont: .long _font_syscall

/* enter_game(pc, sp): from P2, invalidate the instruction cache, set the
   registers as the BIOS leaves them, jump to the game's bootstrap. */
    .global _enter_game
_enter_game:
    mov     r4, r8
    mov     r5, r9
    mova    .Ltail, r0
    mov.l   .Lp2mask, r1
    and     r1, r0
    mov.l   .Lp2, r1
    or      r1, r0
    jmp     @r0
    nop
    .align 2
.Lp2mask: .long 0x1fffffff
.Lp2:     .long 0xa0000000
.Ltail:
    mov.l   .Lccr, r1
    mov.l   @r1, r0
    mov.w   .Lici, r2
    or      r2, r0
    mov.l   r0, @r1
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    mov.l   .Lsr, r0
    ldc     r0, sr
    mov.l   .Lvbr, r0
    ldc     r0, vbr
    mov.l   .Lgbr, r0
    ldc     r0, gbr
    mov.l   .Lfpscr, r0
    lds     r0, fpscr
    mov.l   .Lpr, r0
    lds     r0, pr
    mov     r9, r15
    jmp     @r8
    nop
    .align 2
.Lici:   .word 0x0800
    .align 2
.Lccr:   .long 0xff00001c
.Lsr:    .long 0x400000f0
.Lvbr:   .long 0x8c000000
.Lgbr:   .long 0x8c000000
.Lfpscr: .long 0x00040001
.Lpr:    .long 0xac00043c

/* Diagnostics: the user break controller traps every instruction (after it
   runs) to here, through DBR. BL=1 and RB=1: r0-r7 are bank 1; the game's
   stack takes what we save. Every 2^20 instructions, sample(spc). */
    .global _dbr_handler
    .align 2
_dbr_handler:
    mov.l   r0, @-r15
    mov.l   r1, @-r15
    mov.l   .Lcnt, r0
    mov.l   @r0, r1
    dt      r1
    bf/s    1f
    mov.l   r1, @r0
    mov.l   r2, @-r15
    mov.l   r3, @-r15
    mov.l   r4, @-r15
    mov.l   r5, @-r15
    mov.l   r6, @-r15
    mov.l   r7, @-r15
    sts.l   pr, @-r15
    sts.l   mach, @-r15
    sts.l   macl, @-r15
    stc     spc, r4
    mov.l   .Lsample, r0
    jsr     @r0
    nop
    lds.l   @r15+, macl
    lds.l   @r15+, mach
    lds.l   @r15+, pr
    mov.l   @r15+, r7
    mov.l   @r15+, r6
    mov.l   @r15+, r5
    mov.l   @r15+, r4
    mov.l   @r15+, r3
    mov.l   @r15+, r2
1:  mov.l   @r15+, r1
    mov.l   @r15+, r0
    rte
    nop
    .align 2
.Lcnt:    .long _dbg_countdown
.Lsample: .long _dbg_sample

/* Program-start hook: the user break controller stops right after the first
   instruction at one of the hook addresses (channels A and B, see
   ubc_setup). BL=1 and RB=1: r0-r7 are bank 1; the program's stack takes
   what we save. program_start(spc) patches what the game has just loaded. */
    .global _dbr_hook
    .align 2
_dbr_hook:
    mov.l   r0, @-r15
    mov.l   r1, @-r15
    mov.l   r2, @-r15
    mov.l   r3, @-r15
    mov.l   r4, @-r15
    mov.l   r5, @-r15
    mov.l   r6, @-r15
    mov.l   r7, @-r15
    sts.l   pr, @-r15
    sts.l   mach, @-r15
    sts.l   macl, @-r15
    stc     spc, r4
    mov.l   .Lprog, r0
    jsr     @r0
    nop
    lds.l   @r15+, macl
    lds.l   @r15+, mach
    lds.l   @r15+, pr
    mov.l   @r15+, r7
    mov.l   @r15+, r6
    mov.l   @r15+, r5
    mov.l   @r15+, r4
    mov.l   @r15+, r3
    mov.l   @r15+, r2
    mov.l   @r15+, r1
    mov.l   @r15+, r0
    rte
    nop
    .align 2
.Lprog:   .long _program_start

/* icache_inval(): the whole instruction cache, from P2 (CCR.ICI). */
    .global _icache_inval
    .align 2
_icache_inval:
    mova    1f, r0
    mov.l   .Lp2mask_i, r1
    and     r1, r0
    mov.l   .Lp2_i, r1
    or      r1, r0
    jmp     @r0
    nop
    .align 2
1:  mov.l   .Lccr_i, r1
    mov.l   @r1, r0
    mov.w   .Lici_i, r2
    or      r2, r0
    mov.l   r0, @r1
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    rts
    nop
    .align 2
.Lici_i:    .word 0x0800
    .align 2
.Lp2mask_i: .long 0x1fffffff
.Lp2_i:     .long 0xa0000000
.Lccr_i:    .long 0xff00001c

/* Trampolines: a patched jump literal sends the program here instead of to
   the next program; tramp_go(n) patches what is in memory and returns where
   the jump was going. Registers other than r0/r4/pr as the jump left them
   (the next program's entry needs none of r0-r7). */
    .global _tramp0, _tramp1, _tramp2, _tramp3
    .align 2
_tramp0: bra 1f
    mov     #0, r4
_tramp1: bra 1f
    mov     #1, r4
_tramp2: bra 1f
    mov     #2, r4
_tramp3: mov #3, r4
1:  mov.l   .Ltgo, r0
    jsr     @r0
    nop
    jmp     @r0
    nop
    .align 2
.Ltgo:    .long _tramp_go
