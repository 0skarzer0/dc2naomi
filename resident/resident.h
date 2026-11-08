/* Dreamcast games on the NAOMI: what the loader and the resident part share.

   The resident part stays in the NAOMI's upper 16 MB (the Dreamcast has only
   16 MB, so the game never touches it) and stands in for the Dreamcast BIOS:
   the syscalls (GD-ROM reads served from the NetDIMM, system info, flash),
   and a maple hook that answers the game's controller requests from the
   NAOMI's JVS inputs. */
#pragma once
#include <stdint.h>

#define RES_BASE        0x8dc00000u   /* resident code and data */
#define RES_STACK       0x8dcffff0u   /* stack for boot() */
#define RES_FLASH       0x8dd00000u   /* the Dreamcast flash ROM image, 128 KB */
#define RES_MAPLE       0xadd40000u   /* maple DMA buffers (uncached) */
#define RES_SCRATCH     0xadd7f000u   /* where neutralised register writes land */
#define RES_LOG         0x8dd80000u   /* debug log ring */

#define RES_MAGIC       0x524c4344u   /* "DCLR" */

/* The archive the build script puts after the loader in the netboot image,
   at the end of the program rounded up to 64 KB. Offsets are from the start
   of the archive.

   The disc's high-density area is served from sector ranges: each range
   holds `count` 2048-byte sectors from `fad` on, at `offset` in the archive.
   Sectors outside every range read as zeros. With the original layout
   (a GDI's data tracks) every file keeps its own LBA. */
#define DIMM_MAGIC0     0x47434459u   /* "YDCG" */
#define DIMM_MAGIC1     0x32474d49u   /* "IMG2" */
#define DIMM_VERSION    2
#define DIMM_RANGES     4
#define DIMM_TRACKS     32            /* Windows CE discs (Midway Vol. 2) have 28 */
#define DIMM_PATCHES    64

/* pad_map: how the cabinet (wheel, pedals, lever, START) becomes a Dreamcast pad, per game */
#define DIMM_PAD_CT     0             /* Crazy Taxi 2: START = Y (hop), held 1 s = START; lever = B/A; wheel lock = d-pad */
#define DIMM_PAD_MENU   1             /* Yu Suzuki GW: START plain (sent on release); START + lever = up/down; lever = B/A;
                                         wheel lock = left/right */

/* flags */
#define DIMM_SAMPLER    0x0001u       /* diagnostics: sample the PC every 2^20 instructions */
#define DIMM_NO_HOOK    0x0002u       /* no program-start hook (patches at boot only) */
#define DIMM_NO_UBC     0x0004u       /* no user break: patches on GD-ROM calls and trampolines only */
#define DIMM_DIAG       0x0008u       /* rows of bits on screen from the syscalls and the maple hook,
                                         and back to the loader's VGA timings if the game leaves them */
#define DIMM_MASKERR    0x0010u       /* keep the ASIC error interrupts masked (IML2/4/6ERR = 0) */
#define DIMM_CH2TEST    0x0020u       /* before the game: test DMA channel 2 to the texture paths, rows on screen */
#define DIMM_PCSAMPLE   0x0200u       /* PC sampler on TMU2 through the game dispatcher, rows 16-25 */
#define DIMM_G2IDLE     0x0100u       /* NetDIMM PIO only while no G2 DMA runs */
#define DIMM_READTEST   0x0080u       /* before the game: read the whole image twice by PIO and compare, rows on screen */
#define DIMM_SYNCREAD   0x0400u       /* KallistiOS programs: GD DMA reads finish in one EXEC_SERVER call (KOS
                                         waits for a G1 DMA interrupt we never give when a read is still busy),
                                         and the single-density TOC is the high-density one */
#define DIMM_CONSOLE    0x0800u       /* KallistiOS programs: play dcload (magic 0xdeadbeef at 0x8c004004, syscall at
                                         0x8c004008) so their dbglog/printf is drawn on the screen as text */
#define DIMM_NOIPBOOT   0x1000u       /* start 1ST_READ.BIN at 0x8c010000 directly, without the IP.BIN bootstrap */
#define DIMM_NOPCTRA    0x2000u       /* (test) DO write PCTRA = 0x000a03f0 as the Dreamcast BIOS: kills the NAOMI 2 TA */
#define DIMM_NOBIOSHW   0x4000u       /* skip the "as the Dreamcast BIOS leaves it" writes (AICA SCI*, DMAOR, PCTRA) */
#define DIMM_DMA        0x0040u      /* game reads from the NetDIMM by G1 DMA (as the NAOMI library does), not PIO */

/* Patch kinds. The list is read in order every time a program starts (and
   once at boot). A CHECK opens a group: if the word at addr is not `value`
   the rest of the group (up to the next CHECK) is skipped, so each group only
   touches the program it was written for. A write happens only if the
   current contents equal `expect`, unless the kind has PATCH_ALWAYS. */
#define PATCH_END       0
#define PATCH_CHECK     1
#define PATCH_W16       2
#define PATCH_W32       4
#define PATCH_ALWAYS    0x80
#define PATCH_TRAMP     8             /* W32 on a jump literal: through the resident, which
                                         patches the next program, then on to `expect` */
#define PATCH_R4FIX     16            /* W32 on a call literal: through a stub that turns an r4 of
                                         0x11xxxxxx into 0x13xxxxxx, then on to `expect` */
#define PATCH_HOOK      0xffffffffu   /* value for W32: the resident maple hook */
#define PATCH_G2CHK0    0xfffffffeu   /* value for W32: g2chk0, a G2 FIFO check (SB_FFST bit 0) with a timeout */
#define PATCH_G2CHK4    0xfffffffdu   /* value for W32: g2chk4, the same for bit 4 */
#define PATCH_G2CPU     0xfffffffcu   /* value for W32: g2cpu, a G2 DMA start done by the CPU (Ikaruga) */
#define TRAMPS          4

struct dimm_patch {
    uint32_t addr;
    uint32_t kind;
    uint32_t value;
    uint32_t expect;
};

struct dimm_range {
    uint32_t fad;
    uint32_t count;
    uint32_t offset;
};

struct dimm_header {
    uint32_t magic[2];
    uint32_t version;
    uint32_t archive_base;            /* filled in by the loader: NetDIMM address */
    uint32_t flags;
    uint32_t flash_offset;            /* 128 KB flash ROM image */
    uint32_t boot_fad;                /* 1ST_READ.BIN */
    uint32_t boot_size;
    uint32_t ip_fad;                  /* IP.BIN (16 sectors) */
    uint32_t nranges;
    struct dimm_range ranges[DIMM_RANGES];
    /* high-density TOC: tracks first_track.. (entry = ctrl/adr << 24 | fad) */
    uint32_t first_track, ntracks, leadout;
    uint32_t tracks[DIMM_TRACKS];
    uint32_t hook_pc[2];              /* program entry points that re-apply the patches */
    uint32_t pad_map;                 /* cabinet controls: DIMM_PAD_* */
    uint32_t reserved[7];
    struct dimm_patch patches[DIMM_PATCHES];
};

/* The table at RES_BASE (see head.S). */
typedef struct {
    uint32_t magic;
    void (*boot)(const struct dimm_header *);
    uint32_t maple_hook;              /* address the game's maple driver calls */
    uint32_t bss_start, bss_end;
} res_table_t;
