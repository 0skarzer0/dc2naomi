/* Dreamcast games on the NAOMI: the resident part, standing in for
   the Dreamcast BIOS once the game runs (see resident.h).

   Built freestanding for the SH-4 without the FPU (the game calls the
   syscalls with its own FPSCR) and without divisions (no libgcc). Runs on
   the caller's stack: the game's, or its vblank interrupt's for the maple
   hook. Behaviour follows the BIOS as Flycast's HLE BIOS (reios) models it. */
#include "resident.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int32_t s32;

#define REG16(a) (*(volatile u16 *)(a))
#define REG32(a) (*(volatile u32 *)(a))
#define P2(a) ((void *)(((u32)(a) & 0x1fffffffu) | 0xa0000000u))
#define PHYS(a) ((u32)(a) & 0x1fffffffu)

/* ------------------------------------------------------------------ */
/* Small helpers                                                       */

static void *mset(void *d, int c, u32 n) {
    u8 *p = d;
    while (n--) *p++ = (u8)c;
    return d;
}

static void mcpy(void *d, const void *s, u32 n) {
    u8 *o = d;
    const u8 *i = s;
    while (n--) *o++ = *i++;
}

static inline u32 irq_off(void) {
    u32 sr, n;
    __asm__ volatile("stc sr,%0" : "=r"(sr));
    n = sr | 0xf0;
    __asm__ volatile("ldc %0,sr" : : "r"(n));
    return sr;
}

static inline void irq_restore(u32 sr) {
    __asm__ volatile("ldc %0,sr" : : "r"(sr));
}

/* Write back and invalidate the operand cache lines of [a, a+n): data we
   then write through P2 is what the game sees, whatever it had cached. */
static void cache_purge(u32 a, u32 n) {
    u32 end = a + n;
    a &= ~31u;
    for (; a < end; a += 32) __asm__ volatile("ocbp @%0" : : "r"(a) : "memory");
}

/* Debug log ring (for a later look with a debugger or a dump). */
#define LOG_N 256
static u32 log_pos;
static void dlog(u32 code, u32 a, u32 b, u32 c) {
    u32 *e = (u32 *)P2(RES_LOG + (log_pos & (LOG_N - 1)) * 16);
    e[0] = code;
    e[1] = a;
    e[2] = b;
    e[3] = c;
    log_pos++;
    REG32(P2(RES_LOG - 4)) = log_pos;
}

/* ------------------------------------------------------------------ */
/* On-screen debug: rows of bits drawn into the displayed frame buffer (white
   = 1) while the game starts, so that a photo of a hang says how far it got.
   Row 0 GD-ROM calls, 1 last GD call (r7 << 8 | r4), 2 maple polls,
   3 last sector read (low 16 bits), 4 other syscalls. Stops after the game
   has polled the controls for about 10 s. */
static u32 dbg_val[5];
static u32 dbg_pc[8], dbg_samples;
u32 dbg_countdown = 1;

static void dbg_row(u32 sof, u32 line, u32 r, u32 v, u32 bits) {
    for (u32 b = 0; b < bits; b++) {
        u32 w = (v >> (bits - 1 - b)) & 1 ? 0xffffffffu : 0x00000000u;
        for (u32 y = 0; y < 10; y++) {
            volatile u32 *p = (volatile u32 *)(0xa5000000u + sof + (32 + r * 14 + y) * line + (24 + b * 8 + (b >> 2) * 4) * 2);
            for (u32 x = 0; x < 3; x++) p[x] = (y == 0 || y == 9) ? 0x84108410u : w;
        }
    }
}

/* Every 2^20 instructions (the user break trap, head.S): the PC into a
   ring, and everything on the screen. */
static u32 patches_done, hook_hits;

void dbg_sample(u32 spc) {
    dbg_countdown = 1u << 20;
    dbg_pc[dbg_samples & 7] = spc;
    dbg_samples++;
    REG32(0xa05f8044) |= 1;            /* frame buffer read on */
    REG32(0xa05f80e8) &= ~0x8u;        /* video not blanked */
    u32 sof = REG32(0xa05f8050) & 0x00fffffc;
    u32 size = REG32(0xa05f805c);
    u32 line = (((size & 0x3ff) + 1) + (((size >> 20) & 0x3ff) - 1)) * 4;
    if (line < 640 || line > 4096) line = 1280;
    dbg_row(sof, line, 0, dbg_samples, 16);
    for (u32 r = 0; r < 5; r++) dbg_row(sof, line, 1 + r, dbg_val[r], 16);
    for (u32 i = 0; i < 8; i++) dbg_row(sof, line, 6 + i, dbg_pc[(dbg_samples - 1 - i) & 7], 32);
    dbg_row(sof, line, 14, (patches_done & 0xff) << 8 | (hook_hits & 0xff), 16); /* patches, program starts */
}

static void diag_draw(void);
static void dbg_draw(void) {
    diag_draw(); /* (DIMM_DIAG builds; the sampler draws on its own) */
}

/* ------------------------------------------------------------------ */
/* NetDIMM reads (the cartridge port, PIO)                             */

#define CART_OFFSETH 0xa05f7000u
#define CART_OFFSETL 0xa05f7004u
#define CART_DATA    0xa05f7008u

static struct dimm_header H;

/* len bytes from NetDIMM address src (even) to dst (even), 4 KB at a time
   with interrupts off; 32-bit stores when dst is 4-aligned. */
static void cart_read(void *dst, u32 src, u32 len) {
    u8 *o = dst;
    while (len) {
        u32 n = len > 4096 ? 4096 : len;
        u32 sr = irq_off();
        REG16(CART_OFFSETL) = (u16)src;
        REG16(CART_OFFSETH) = (u16)(0x8000 | ((src >> 16) & 0x1fff));
        u32 i = 0;
        if (((u32)o & 3) == 0) {
            for (; i + 4 <= n; i += 4) {
                u32 lo = REG16(CART_DATA);
                u32 hi = REG16(CART_DATA);
                *(u32 *)(o + i) = lo | hi << 16;
            }
        }
        for (; i + 2 <= n; i += 2) *(u16 *)(o + i) = REG16(CART_DATA);
        if (i < n) o[i] = (u8)REG16(CART_DATA); /* (odd length: the last byte) */
        irq_restore(sr);
        o += n;
        src += n;
        len -= n;
    }
}

/* The NetDIMM address of sector fad, or 0 if no range holds it. */
static u32 sector_addr(u32 fad) {
    for (u32 i = 0; i < H.nranges && i < DIMM_RANGES; i++) {
        const struct dimm_range *r = &H.ranges[i];
        if (fad >= r->fad && fad - r->fad < r->count)
            return H.archive_base + r->offset + (fad - r->fad) * 2048;
    }
    return 0;
}

/* count 2048-byte sectors from fad on to addr. dma: through P2, as the
   GD-ROM's DMA would write memory. */
static void read_sectors(u32 addr, u32 fad, u32 count, int dma) {
    while (count) {
        u8 *dst = dma ? P2(addr) : (u8 *)addr;
        u32 src = sector_addr(fad);
        if (dma) cache_purge((addr & 0x1fffffffu) | 0x80000000u, 2048);
        dbg_val[3] = fad;
        if (src)
            cart_read(dst, src, 2048);
        else
            mset(dst, 0, 2048);
        addr += 2048;
        fad++;
        count--;
    }
}

/* ------------------------------------------------------------------ */
/* GD-ROM syscalls (0x8c0000bc, and the entry at 0x8c0010f0)           */

enum {
    GDC_ERR = -1, GDC_OK, GDC_BUSY, GDC_COMPLETE, GDC_CONTINUE
};

enum {
    GDCC_PIOREAD = 0x10, GDCC_DMAREAD, GDCC_GETTOC, GDCC_GETTOC2, GDCC_PLAY, GDCC_PLAY2,
    GDCC_PAUSE, GDCC_RELEASE, GDCC_INIT, GDCC_READABORT, GDCC_OPEN, GDCC_SEEK,
    GDCC_DMA_READ_REQ, GDCC_GETQINFO, GDCC_REQ_MODE, GDCC_SET_MODE, GDCC_SCAN, GDCC_STOP,
    GDCC_GETSCD, GDCC_REQ_SES, GDCC_REQ_STAT, GDCC_PIOREADREQ, GDCC_MULTI_DMAREAD,
    GDCC_MULTI_PIOREAD, GDCC_GET_VERSION,
    GDCC_REQ_DMA_TRANS = 0x106, GDCC_REQ_PIO_TRANS = 0x10c
};

#define READ_CHUNK 32 /* sectors a DMA read copies each EXEC_SERVER call */

static struct {
    u32 last_id, next_id;
    s32 status;
    u32 command;
    u32 params[4];
    u32 result[4];
    u32 cur_sector;
    u32 read_fad, read_addr, read_count, read_total; /* DMA read in progress */
    u32 multi_sector, multi_offset, multi_count, multi_total;
    u32 callback, callback_arg;
    int dma_ended;
    u32 mode[4];
} gd;

static void gd_reset_state(void) {
    mset(&gd, 0, sizeof gd);
    gd.last_id = 0xffffffffu;
    gd.next_id = 2;
    gd.mode[0] = 0;      /* speed */
    gd.mode[1] = 0xb4;   /* standby */
    gd.mode[2] = 0x19;   /* read flags */
    gd.mode[3] = 0x08;   /* read retry */
}

static int in_ram(u32 a) {
    u32 p = a & 0x1fffffffu;
    return p >= 0x0c000000u && p < 0x0e000000u;
}

static void put32(u32 addr, u32 v) {
    if (in_ram(addr)) *(volatile u32 *)addr = v;
}

static void gd_toc(u32 area, u32 dest) {
    u32 toc[102];
    for (int i = 0; i < 102; i++) toc[i] = 0xffffffffu;
    if (area == 0) {
        /* single density: track 1 (data) and 2 (audio) */
        toc[0] = 0x41000000u | 150;
        toc[1] = 0x01000000u | 600;
        toc[99] = 0x41010000u;
        toc[100] = 0x01020000u;
        toc[101] = 0x01000000u | (600 + 44550);
    } else {
        u32 first = H.first_track, n = H.ntracks;
        if (n > DIMM_TRACKS) n = DIMM_TRACKS;
        for (u32 i = 0; i < n && first + i <= 99; i++) toc[first + i - 1] = H.tracks[i];
        toc[99] = (H.tracks[0] & 0xff000000u) | first << 16;
        toc[100] = (H.tracks[n - 1] & 0xff000000u) | (first + n - 1) << 16;
        toc[101] = (H.tracks[n - 1] & 0xff000000u) | H.leadout;
    }
    for (int i = 0; i < 102; i++) put32(dest + i * 4, toc[i]);
}

/* Copy from the multi-read position to dest, size bytes (MULTI_*READ). */
static void multi_xfer(u32 dest, u32 size, int dma) {
    static u8 sector[2048] __attribute__((aligned(32)));
    if (size > gd.multi_count) size = gd.multi_count;
    while (size) {
        read_sectors((u32)sector, gd.multi_sector, 1, 0);
        u32 left = 2048 - gd.multi_offset;
        u32 n = size < left ? size : left;
        u8 *d = dma ? P2(dest) : (u8 *)dest;
        if (dma) cache_purge((dest & 0x1fffffffu) | 0x80000000u, n);
        mcpy(d, sector + gd.multi_offset, n);
        dest += n;
        size -= n;
        gd.multi_count -= n;
        gd.multi_offset += n;
        if (gd.multi_offset >= 2048) {
            gd.multi_offset = 0;
            gd.multi_sector++;
        }
    }
}

static void gd_command(void) {
    u32 *p = gd.params;
    switch (gd.command) {
    case GDCC_GETTOC2:
        gd_toc(p[0], p[1]);
        break;
    case GDCC_INIT:
        gd.callback = 0;
        gd.multi_count = 0;
        break;
    case GDCC_PIOREAD:
        read_sectors(p[2], p[0] & 0xffffff, p[1], 0);
        gd.cur_sector = (p[0] & 0xffffff) + p[1] - 1;
        gd.result[2] = p[1] * 2048;
        gd.result[3] = 0;
        break;
    case GDCC_DMAREAD:
        if (gd.read_total == 0) { /* first call: set up */
            gd.read_fad = p[0] & 0xffffff;
            gd.read_count = p[1];
            gd.read_total = p[1];
            gd.read_addr = p[2];
            gd.result[2] = gd.result[3] = 0;
        }
        {
            u32 n = gd.read_count < READ_CHUNK ? gd.read_count : READ_CHUNK;
            read_sectors(gd.read_addr, gd.read_fad, n, 1);
            gd.read_fad += n;
            gd.read_addr += n * 2048;
            gd.read_count -= n;
            gd.cur_sector = gd.read_fad - 1;
            gd.result[2] = (gd.read_total - gd.read_count) * 2048;
        }
        if (gd.read_count) return; /* still busy; more on the next call */
        gd.read_total = 0;
        break;
    case GDCC_DMA_READ_REQ:
    case GDCC_MULTI_DMAREAD:
    case GDCC_MULTI_PIOREAD:
        gd.status = GDC_CONTINUE;
        gd.multi_sector = p[0] & 0xffffff;
        gd.multi_count = p[1] * 2048;
        gd.multi_total = gd.multi_count;
        gd.multi_offset = 0;
        gd.result[2] = gd.command == GDCC_DMA_READ_REQ ? 2048 : 0;
        gd.result[3] = gd.command == GDCC_DMA_READ_REQ && p[1] ? 1 : 0;
        break;
    case GDCC_REQ_MODE:
        for (int i = 0; i < 4; i++) put32(p[0] + i * 4, gd.mode[i]);
        gd.result[2] = 0xa;
        break;
    case GDCC_SET_MODE:
        for (int i = 0; i < 4; i++) gd.mode[i] = p[i];
        gd.result[2] = 0xa;
        break;
    case GDCC_GET_VERSION: {
        static const char ver[] = "GDC Version 1.10 1999-03-31 ";
        u8 *d = (u8 *)p[0];
        if (in_ram(p[0])) {
            for (int i = 0; ver[i]; i++) d[i] = (u8)ver[i];
            d[sizeof ver - 2] = 0x02;
        }
        break;
    }
    case GDCC_REQ_STAT:
        put32(p[0], 1);                          /* paused */
        put32(p[1], 3);                          /* track */
        put32(p[2], 0x41000000u | gd.cur_sector); /* fad, adr/control */
        put32(p[3], 1);                          /* index */
        gd.result[2] = 0xa;
        break;
    case GDCC_REQ_PIO_TRANS:
        multi_xfer(gd.params[0], gd.params[1], 0);
        gd.result[2] = gd.multi_total - gd.multi_count;
        gd.result[3] = 0;
        break;
    default:
        /* PLAY, PAUSE, SEEK, STOP, GETSCD, REQ_SES...: nothing to do */
        dlog(0x47430000u | gd.command, p[0], p[1], p[2]);
        break;
    }
    if (gd.status == GDC_BUSY) gd.status = GDC_COMPLETE;
    if (gd.status != GDC_CONTINUE) gd.command = 0;
}

typedef s32 (*callback_t)(u32);

static s32 gd_syscall_body(u32 r4, u32 r5, u32 r6, u32 r7);

/* The game calls in from its main loop and from interrupts: a call that
   comes in while another is copying sectors gets "busy" (as the BIOS's
   semaphore does) instead of running into it. */
static volatile int gd_inside;

static void patch_poll(void);

static s32 gd_syscall(u32 r4, u32 r5, u32 r6, u32 r7) {
    s32 r0;
    dbg_val[0]++;
    dbg_val[1] = r7 << 8 | (r4 & 0xff);
    dbg_draw();
    if (gd_inside) {
        dlog(0x4e455354u, r7, r4, 0);
        if (r6 == 0 && r7 == 1) { /* GET_CMD_STAT */
            for (int i = 0; i < 4; i++) put32(r5 + i * 4, gd.result[i]);
            return GDC_BUSY;
        }
        return 0;
    }
    gd_inside = 1;
    patch_poll();
    r0 = gd_syscall_body(r4, r5, r6, r7);
    gd_inside = 0;
    return r0;
}

static s32 gd_syscall_body(u32 r4, u32 r5, u32 r6, u32 r7) {
    if (r6 != 0) { /* the MISC superfunction: INIT, SETVECTOR */
        dlog(0x4d495343u, r4, r5, r7);
        return 0;
    }
    switch (r7) {
    case 0: /* REQ_CMD */
        if (gd.status != GDC_OK) return 0;
        for (int i = 0; i < 4; i++) gd.params[i] = in_ram(r5) ? ((volatile u32 *)r5)[i] : 0;
        mset(gd.result, 0, sizeof gd.result);
        if (gd.next_id == 0xffffffffu || gd.next_id == 0) gd.next_id = 1;
        gd.last_id = gd.next_id++;
        gd.status = GDC_BUSY;
        gd.command = r4;
        gd.multi_count = 0;
        gd.read_total = 0;
        dlog(0x52510000u | r4, gd.params[0], gd.params[1], gd.params[2]);
        return (s32)gd.last_id;
    case 1: { /* GET_CMD_STAT */
        s32 r0;
        for (int i = 0; i < 4; i++) put32(r5 + i * 4, gd.result[i]);
        if (gd.status == GDC_OK || gd.status == GDC_BUSY) return gd.status;
        if (r4 != gd.last_id) return GDC_OK;
        r0 = gd.status;
        if (gd.status == GDC_CONTINUE && gd.multi_count == 0) {
            gd.status = GDC_COMPLETE;
            gd.result[3] = 0;
        } else if (gd.status != GDC_CONTINUE) {
            gd.status = GDC_OK;
            gd.last_id = 0xffffffffu;
        }
        return r0;
    }
    case 2: /* EXEC_SERVER */
        if (gd.status == GDC_BUSY || (gd.status == GDC_CONTINUE && gd.command == GDCC_REQ_PIO_TRANS))
            gd_command();
        return 0;
    case 3: /* INIT_SYSTEM */
        gd_reset_state();
        return 0;
    case 4: /* GET_DRV_STAT */
        put32(r4, gd.status == GDC_CONTINUE ? 3 : 1); /* play / pause */
        put32(r4 + 4, 0x80);                          /* GD-ROM */
        return 0;
    case 5: /* G1_DMA_END */
        gd.callback = r4;
        gd.callback_arg = r5;
        if (gd.callback && gd.dma_ended) {
            gd.dma_ended = 0;
            return ((callback_t)gd.callback)(gd.callback_arg);
        }
        return 0;
    case 6: /* REQ_DMA_TRANS */
        gd.params[0] = ((volatile u32 *)r5)[0];
        gd.params[1] = ((volatile u32 *)r5)[1];
        if (gd.status != GDC_CONTINUE || gd.params[1] > gd.multi_count || gd.params[1] == 0) return GDC_ERR;
        multi_xfer(gd.params[0], gd.params[1], 1);
        gd.result[2] = 2048;
        gd.result[3] = gd.multi_count ? 1 : 0;
        gd.dma_ended = 1;
        if (gd.multi_count == 0) gd.status = GDC_COMPLETE;
        dlog(0x444d4154u, gd.params[0], gd.params[1], gd.multi_count); /* (no DMA interrupt to give) */
        return 0;
    case 7: /* CHECK_DMA_TRANS */
        put32(r5, gd.multi_count);
        return gd.status == GDC_CONTINUE ? GDC_OK : GDC_BUSY;
    case 8: /* READ_ABORT */
        if (r4 == gd.last_id && (gd.status == GDC_CONTINUE || gd.status == GDC_BUSY || gd.status == GDC_COMPLETE)) {
            gd.multi_count = 0;
            gd.read_total = 0;
            gd.read_count = 0;
            return GDC_OK;
        }
        return GDC_ERR;
    case 9: /* RESET */
        gd.last_id = 0xffffffffu;
        gd.status = GDC_OK;
        return 0;
    case 10: /* CHANGE_DATA_TYPE */
        return 0;
    case 11: /* SET_PIO_CALLBACK */
        gd.callback = r4;
        gd.callback_arg = r5;
        return 0;
    case 12: /* REQ_PIO_TRANS */
        gd.params[0] = ((volatile u32 *)r5)[0];
        gd.params[1] = ((volatile u32 *)r5)[1];
        if (gd.status != GDC_CONTINUE || gd.params[1] > gd.multi_count) return GDC_ERR;
        gd.command = GDCC_REQ_PIO_TRANS;
        return 0;
    case 13: /* CHECK_PIO_TRANS */
        if (gd.status != GDC_CONTINUE) return GDC_ERR;
        put32(r5, gd.multi_count);
        return GDC_OK;
    }
    dlog(0x47447878u, r4, r5, r7);
    return 0;
}

/* ------------------------------------------------------------------ */
/* System, font, flash and misc syscalls                               */

static u8 *const flash = (u8 *)RES_FLASH;

static s32 sys_syscall(u32 r4, u32 r5, u32 r6, u32 r7) {
    dbg_val[4]++;
    dbg_draw();
    (void)r5;
    (void)r6;
    switch (r7) {
    case 0: { /* SYSINFO_INIT */
        u8 *d = (u8 *)0x8c000068;
        mset(d, 0, 24);
        mcpy(d, flash + 0x1a056, 8);
        mcpy(d + 8, flash + 0x1a000, 5);
        return 0;
    }
    case 2: /* SYSINFO_ICON */
        return r4 > 9 ? -1 : 704;
    case 3: /* SYSINFO_ID */
        return 0x8c000068;
    }
    return -1;
}

static u8 font_dummy[64];

s32 font_syscall(u32 r1) {
    switch (r1) {
    case 0: return (s32)font_dummy; /* FONTROM_ADDRESS (no font: the game draws none) */
    case 1: return 0;               /* LOCK */
    case 2: return 0;               /* UNLOCK */
    }
    return -1;
}

static const u32 part_offset[5] = {0x1a000, 0x18000, 0x1c000, 0x10000, 0x00000};
static const u32 part_size[5] = {0x2000, 0x2000, 0x4000, 0x8000, 0x10000};

static s32 flash_syscall(u32 r4, u32 r5, u32 r6, u32 r7) {
    dbg_val[4]++;
    dbg_draw();
    switch (r7) {
    case 0: /* INFO */
        if (r4 >= 5) return -1;
        put32(r5, part_offset[r4]);
        put32(r5 + 4, part_size[r4]);
        return 0;
    case 1: /* READ */
        if (r4 + r6 > 0x20000) return -1;
        mcpy((void *)r5, flash + r4, r6);
        return 0;
    case 2: /* WRITE (flash: bits only clear) */
        if (r4 + r6 > 0x20000) return -1;
        for (u32 i = 0; i < r6; i++) flash[r4 + i] &= ((u8 *)r5)[i];
        return (s32)r6;
    case 3: /* DELETE */
        for (int i = 0; i < 5; i++)
            if (part_offset[i] == r4) {
                mset(flash + r4, 0xff, part_size[i]);
                return 0;
            }
        return -1;
    }
    return -1;
}

static u32 boot_sectors;

static s32 misc_syscall(u32 r4, u32 r5, u32 r6, u32 r7) {
    dbg_val[4]++;
    dbg_draw();
    (void)r5;
    (void)r6;
    (void)r7;
    switch (r4) {
    case 0: /* init */
        REG32(0xa05f7404) = 0x0c010000u + boot_sectors * 2048; /* SB_GDSTARD */
        REG32(0xa05f6910) = 0;                                  /* SB_IML2NRM */
        REG32(0xa05f8040) = 0x00c0bebcu;                        /* border colour */
        return 0x00c0bebc;
    case 2: /* check disc: reload part of IP.BIN */
        read_sectors(0x8c008100, H.ip_fad, 7, 0);
        return 0;
    }
    dlog(0x4d697363u, r4, r5, r6); /* exit to the BIOS menu etc.: ignored */
    return 0;
}

/* ------------------------------------------------------------------ */
/* Maple: the game's controller requests answered from the JVS inputs  */

/* Inputs from the last JVS fetch. */
static struct {
    u16 p1;        /* JVS player 1 switches (START 0x8000, UP 0x2000, DOWN 0x1000...) */
    u16 analog[3]; /* wheel, accelerator, brake */
    u8 test;
    int valid;
} jvs;

/* Calibration that widens as the controls move (from the cabinet's
   measured ranges: wheel 8448..60160, centre 33792; pedals as below). */
static struct {
    s32 lo, hi;
} cal[3] = {{8448, 60160}, {11776, 47104}, {14080, 47360}};

/* num * range / den without a division instruction */
static u32 div_scale(u32 num, u32 range, u32 den) {
    u32 n = num * range, q = 0;
    for (int b = 31; b >= 0; b--) {
        if ((n >> b) >= den) {
            n -= den << b;
            q |= 1u << b;
        }
    }
    return q > range ? range : q;
}

static u32 scale(int ch, u32 v, u32 range) {
    s32 x = (s32)v;
    if (x < cal[ch].lo) cal[ch].lo = x;
    if (x > cal[ch].hi) cal[ch].hi = x;
    s32 span = cal[ch].hi - cal[ch].lo;
    if (span < 256) return 0;
    /* (x - lo) * range / span without a division: span >> 8 steps */
    u32 num = (u32)(x - cal[ch].lo) * range;
    u32 den = (u32)span;
    u32 q = 0;
    for (int b = 31; b >= 0; b--) {
        if ((num >> b) >= den) {
            num -= den << b;
            q |= 1u << b;
        }
    }
    return q > range ? range : q;
}

/* The wheel either side of its centre (the cabinet's measured 33792). */
#define WHEEL_CENTRE 33792
static u32 wheel(u32 v) {
    static const s32 c = WHEEL_CENTRE;
    if ((s32)v < cal[0].lo) cal[0].lo = (s32)v;
    if ((s32)v > cal[0].hi) cal[0].hi = (s32)v;
    if ((s32)v <= c) {
        u32 span = (u32)(c - cal[0].lo), off = (u32)((s32)v - cal[0].lo);
        return span < 256 ? 128 : div_scale(off, 128, span);
    }
    u32 span = (u32)(cal[0].hi - c), off = (u32)((s32)v - c);
    u32 r = 128 + (span < 256 ? 0 : div_scale(off, 127, span));
    return r > 255 ? 255 : r;
}

#define DC_C 0x0001
#define DC_B 0x0002
#define DC_A 0x0004
#define DC_START 0x0008
#define DC_UP 0x0010
#define DC_DOWN 0x0020
#define DC_LEFT 0x0040
#define DC_RIGHT 0x0080
#define DC_Y 0x0200
#define DC_X 0x0400

static u32 start_frames;

static void pad_state(u16 *buttons, u8 *rtrig, u8 *ltrig, u8 *joyx, u8 *joyy) {
    u32 b = 0;
    u32 x = 128, acc = 0, brk = 0;
    if (jvs.valid) {
        x = wheel(jvs.analog[0]);
        acc = scale(1, jvs.analog[1], 255);
        brk = scale(2, jvs.analog[2], 255);
        /* small dead zones on the pedals */
        acc = acc < 15 ? 0 : acc;
        brk = brk < 15 ? 0 : brk;
        /* START: a short press is A (the menus confirm with A, and START
           there goes back); held for over half a second it becomes START
           (the title screen, pause) */
        if (jvs.p1 & 0x8000) {
            if (start_frames < 1000) start_frames++;
            b |= start_frames < 20 ? DC_A : DC_START;
        } else {
            start_frames = 0;
        }
        if (jvs.p1 & 0x2000) b |= DC_UP;   /* shifter forward: menus, view */
        if (jvs.p1 & 0x1000) b |= DC_DOWN; /* shifter back */
        if (jvs.p1 & 0x0800) b |= DC_LEFT;
        if (jvs.p1 & 0x0400) b |= DC_RIGHT;
        if (jvs.p1 & 0x0200) b |= DC_B;
        if (x < 16) b |= DC_LEFT;    /* the wheel at full lock: menus */
        if (x > 239) b |= DC_RIGHT;
        if (brk > 200 && (jvs.p1 & 0x8000)) b = (b & ~DC_A) | DC_B; /* brake + START: B (back) */
    }
    *buttons = (u16)~b;
    *rtrig = (u8)acc;
    *ltrig = (u8)brk;
    *joyx = (u8)x;
    *joyy = 128;
}

/* Standard controller DEVINFO (functions, function data, area, direction,
   name, licence, power). */
static void devinfo(u32 *w) {
    static const char name[30] = "Dreamcast Controller          ";
    static const char lic[60] = "Produced By or Under License From SEGA ENTERPRISES,LTD.     ";
    u8 *b = (u8 *)w;
    w[0] = 0x01000000u;
    w[1] = 0xfe060f00u;
    w[2] = 0;
    w[3] = 0;
    b[16] = 0xff;
    b[17] = 0;
    mcpy(b + 18, name, 30);
    mcpy(b + 48, lic, 60);
    b[108] = 0xae;
    b[109] = 0x01;
    b[110] = 0xf4;
    b[111] = 0x01;
}

/* Our own DMA list: the MIE poll (request, then fetch, as KOS's driver). */
#define MIE_REQ   0x17
#define MIE_FETCH 0x15
#define MIE_RESP  0x16
#define MIE_EMPTY 0x32
#define MIE_RESP_IO 0x87

static int mie_state; /* 0 idle (send a request), 1 request sent, 2 fetch sent */
static u32 *const my_list = (u32 *)RES_MAPLE;
static u32 *const my_recv = (u32 *)(RES_MAPLE + 0x400);

static u32 read_be16(const u8 *p) {
    return (u32)p[0] << 8 | p[1];
}

static void mie_parse(void) {
    u32 hdr = my_recv[0];
    if (mie_state == 0) return;
    dlog(0x4d494500u | mie_state, hdr, my_recv[1], my_recv[2]);
    if (hdr == 0xffffffffu || (hdr & 0xff) != MIE_RESP_IO) {
        mie_state = 0;
        return;
    }
    if (mie_state == 1) { /* request accepted: fetch next */
        mie_state = 2;
        return;
    }
    const u8 *d = (const u8 *)&my_recv[1];
    u32 words = hdr >> 24;
    { /* (debug: the last fetch answer) */
        u32 *keep = (u32 *)(RES_MAPLE + 0x800);
        for (u32 i = 0; i < 32; i++) keep[i] = my_recv[i];
    }
    if (d[0] == MIE_EMPTY || words < 8) return; /* not ready: fetch again */
    if (words * 4 >= 54 && d[0] == MIE_RESP && (d[18] & 0x80) && d[26] == 1) {
        jvs.p1 = (u16)read_be16(d + 28);
        for (int i = 0; i < 3; i++) jvs.analog[i] = (u16)read_be16(d + 38 + i * 2);
        jvs.test = (d[6] & 0x10) == 0;
        jvs.valid = 1;
    }
    mie_state = 0;
}

static u32 mie_build(void) {
    u32 *w = my_list;
    u8 *data = (u8 *)&w[3];
    u32 len;
    if (mie_state == 2) {
        len = 1;
        mset(data, 0, 4);
        data[0] = MIE_FETCH;
    } else {
        /* SWINP 2 players x 2 bytes, COININP 2 slots, ANLINP 8 channels */
        static const u8 req[15] = {MIE_REQ, 0x77, 0, 0, 0, 0, 1, 7, 0x20, 2, 2, 0x21, 2, 0x22, 8};
        len = 4;
        mset(data, 0, 16);
        mcpy(data, req, sizeof req);
        mie_state = 1;
    }
    w[0] = 0x80000000u | len;                         /* last, port A */
    w[1] = PHYS(my_recv);
    w[2] = 0x86u | 0x20u << 8 | 0x00u << 16 | len << 24; /* MIE IO, to A main unit */
    my_recv[0] = 0xffffffffu;
    return PHYS(my_list);
}

/* Called by the game's maple driver with its frame list, just before it
   starts the DMA: answer every frame into its receive buffer, and hand the
   hardware our MIE poll instead (its end interrupt is the game's). */
static u32 hook_calls, cond_calls;

u32 maple_hook(u32 list) {
    const u32 *in = (const u32 *)list;
    hook_calls++;
    dbg_val[2]++;
    dbg_draw();
    mie_parse();
    for (int guard = 0; guard < 64; guard++) {
        u32 w0 = in[0];
        u32 len = w0 & 0xff;
        u32 recv = in[1] | 0x80000000u;
        u32 hdr = in[2];
        u32 cmd = hdr & 0xff, dst = (hdr >> 8) & 0xff;
        u32 port = (dst >> 6) & 3;
        u32 out[32];
        u32 olen = 0;
        int answer = port == 0 && (dst & 0x20) && (w0 >> 8 & 7) == 0;
        if (answer) {
            u32 rcmd = 7; /* ACK */
            if (cmd == 1 || cmd == 2) { /* DEVINFO / ALLINFO */
                rcmd = 5;
                olen = 28;
                devinfo(&out[1]);
            } else if (cmd == 9) { /* GETCOND */
                cond_calls++;
                u8 *b = (u8 *)&out[2];
                rcmd = 8;
                olen = 3;
                out[1] = 0x01000000u;
                pad_state((u16 *)b, b + 2, b + 3, b + 4, b + 5);
                b[6] = b[7] = 128;
            }
            out[0] = rcmd | (port << 6) << 8 | (0x20u | (port << 6)) << 16 | olen << 24;
            olen++;
        } else {
            out[0] = 0xffffffffu; /* nothing connected */
            olen = 1;
        }
        cache_purge(recv, olen * 4);
        u32 *r = P2(recv);
        for (u32 i = 0; i < olen; i++) r[i] = out[i];
        if ((w0 >> 8 & 7) != 0) {
            in += 1;
        } else {
            in += 3 + len;
        }
        if (w0 & 0x80000000u) break;
    }
    return mie_build();
}

/* ------------------------------------------------------------------ */
/* Boot                                                                */

extern void font_stub(void);
extern void enter_game(u32 pc, u32 sp);

extern void icache_inval(void);

/* The patch list (see resident.h): at boot, and each time a program starts. */
extern void tramp0(void), tramp1(void), tramp2(void), tramp3(void);
u32 tramp_target[TRAMPS];

/* Diagnostics for the real board (DIMM_DIAG): every 16 calls into the
   resident (syscalls, maple hook), rows of bits into the displayed frame
   buffer, and if the game has left 31 kHz (VGA clock off, or interlace /
   NTSC / PAL sync), the VGA timings the loader had, so that a 31 kHz monitor
   shows something. Rows (white = 1, MSB first):
   0 heartbeat, 1 GD-ROM calls, 2 last GD call (r7 << 8 | r4), 3 maple polls,
   4 last sector (low 16), 5 other syscalls, 6 patches << 8 | trampolines,
   7 SPG_CONTROL, 8 FB_R_CTRL (32), 9 times back to VGA, 10 SPG_LOAD (32). */
static const u16 vga_reg_off[8] = {0xd0, 0xd4, 0xd8, 0xdc, 0xe0, 0xe8, 0xec, 0xf0};
static u32 vga_reg[8], vga_saved, vga_restores, diag_calls;

static void vga_save(void) {
    for (int i = 0; i < 8; i++) vga_reg[i] = REG32(0xa05f8000u + vga_reg_off[i]);
    vga_saved = (REG32(0xa05f8044) & 0x800000u) != 0;
}

static void diag_draw(void) {
    if (!(H.flags & DIMM_DIAG) || (++diag_calls & 15)) return;
    u32 spg = REG32(0xa05f80d0), fbr = REG32(0xa05f8044), load = REG32(0xa05f80d8);
    if (vga_saved && (!(fbr & 0x800000u) || (spg & 0xd0u))) {
        for (int i = 0; i < 8; i++) REG32(0xa05f8000u + vga_reg_off[i]) = vga_reg[i];
        REG32(0xa05f8044) = fbr | 0x800001u;   /* VGA clock, frame buffer read on */
        vga_restores++;
    }
    REG32(0xa05f80e8) &= ~0x8u;                /* video not blanked */
    u32 sof = REG32(0xa05f8050) & 0x00fffffc;
    u32 size = REG32(0xa05f805c);
    u32 line = (((size & 0x3ff) + 1) + (((size >> 20) & 0x3ff) - 1)) * 4;
    if (line < 640 || line > 4096) line = 1280;
    dbg_row(sof, line, 0, diag_calls >> 4, 16);
    dbg_row(sof, line, 1, dbg_val[0], 16);
    dbg_row(sof, line, 2, dbg_val[1], 16);
    dbg_row(sof, line, 3, dbg_val[2], 16);
    dbg_row(sof, line, 4, dbg_val[3], 16);
    dbg_row(sof, line, 5, dbg_val[4], 16);
    dbg_row(sof, line, 6, (patches_done & 0xff) << 8 | (hook_hits & 0xff), 16);
    dbg_row(sof, line, 7, spg, 16);
    dbg_row(sof, line, 8, fbr, 32);
    dbg_row(sof, line, 9, vga_restores, 16);
    dbg_row(sof, line, 10, load, 32);
}

static void apply_patches(void) {
    static void (*const tramp[TRAMPS])(void) = {tramp0, tramp1, tramp2, tramp3};
    int skip = 0, ntramp = 0;
    for (int i = 0; i < DIMM_PATCHES && H.patches[i].kind != PATCH_END; i++) {
        const struct dimm_patch *p = &H.patches[i];
        u32 kind = p->kind & 0x7f, always = p->kind & PATCH_ALWAYS;
        if (kind == PATCH_CHECK) {
            skip = *(volatile u32 *)p->addr != p->value;
            continue;
        }
        int t = kind == PATCH_TRAMP ? ntramp++ : 0; /* (fixed per entry, groups skipped or not) */
        if (skip) continue;
        u32 v = p->value == PATCH_HOOK ? (u32)maple_hook : p->value;
        if (kind == PATCH_TRAMP) {
            /* (numbered in list order, the same every time) */
            if (t >= TRAMPS) continue;
            tramp_target[t] = p->expect;
            volatile u32 *a = (volatile u32 *)p->addr;
            if (*a != p->expect) continue;
            *a = (u32)tramp[t];
        } else if (kind == PATCH_W16) {
            volatile u16 *a = (volatile u16 *)p->addr;
            if (!always && *a != (u16)p->expect) continue;
            *a = (u16)v;
        } else if (kind == PATCH_W32) {
            volatile u32 *a = (volatile u32 *)p->addr;
            if (!always && *a != p->expect) continue;
            *a = v;
        } else {
            continue;
        }
        __asm__ volatile("ocbwb @%0" : : "r"(p->addr & ~31u) : "memory");
        patches_done++;
    }
}

/* The user break controller stops right after the first instruction of a
   program at one of hook_pc[] (DBR, head.S): the program the game has just
   loaded is all in memory, so patch it before it runs. */
#define BARA  0xff200000u
#define BAMRA 0xff200004u
#define BBRA  0xff200008u
#define BARB  0xff20000cu
#define BAMRB 0xff200010u
#define BBRB  0xff200014u
#define BRCR  0xff200020u


/* The second way in: every GD-ROM syscall checks the list too (a program
   always loads its files right after it starts). For emulators without the
   user break controller (Flycast), and in case the break is missed. */
static void patch_poll(void) {
    if (H.flags & DIMM_NO_HOOK) return;
    u32 before = patches_done;
    apply_patches();
    if (patches_done != before) {
        dlog(0x504f4c4cu, patches_done - before, patches_done, 0); /* "POLL" */
        icache_inval();
    }
}

/* A program jumping to the next one through a trampoline (head.S): patch
   it before its first instruction, as the user break would. */
u32 tramp_go(u32 t) {
    hook_hits++;
    dlog(0x5452414du, t, tramp_target[t], patches_done); /* "TRAM" */
    apply_patches();
    icache_inval();
    return tramp_target[t];
}

void program_start(u32 spc) {
    hook_hits++;
    dlog(0x50524f47u, spc, hook_hits, patches_done); /* "PROG" */
    REG16(BRCR) &= (u16)~0xc000u;      /* CMFA, CMFB */
    apply_patches();
    icache_inval();
    dlog(0x50415443u, spc, hook_hits, patches_done); /* "PATC" */
}

static void ubc_setup(void) {
    extern void dbr_handler(void), dbr_hook(void);
    if (H.flags & DIMM_SAMPLER) {
        /* every instruction, after it runs: the sampler */
        u32 h = (u32)dbr_handler;
        __asm__ volatile("ldc %0,dbr" : : "r"(h));
        REG32(BARA) = 0;
        *(volatile u8 *)BAMRA = 0x07;     /* all address bits masked, ASID too */
        REG16(BBRA) = 0x0010;             /* instruction access */
        REG16(BRCR) = 0x0401;             /* channel A after execution, via DBR */
        return;
    }
    if (H.flags & (DIMM_NO_HOOK | DIMM_NO_UBC)) return;
    u32 h = (u32)dbr_hook;
    __asm__ volatile("ldc %0,dbr" : : "r"(h));
    REG32(BARA) = H.hook_pc[0];
    *(volatile u8 *)BAMRA = 0x04;         /* all address bits, no ASID */
    REG16(BBRA) = H.hook_pc[0] ? 0x0010 : 0;
    REG32(BARB) = H.hook_pc[1];
    *(volatile u8 *)BAMRB = 0x04;
    REG16(BBRB) = H.hook_pc[1] ? 0x0010 : 0;
    REG16(BRCR) = 0x0441;                 /* A and B after execution, via DBR */
}

void boot(const struct dimm_header *h) {
    mcpy(&H, h, sizeof H);
    vga_save();                 /* the loader's 31 kHz timings (DIMM_DIAG) */
    gd_reset_state();
    log_pos = 0;

    /* The BIOS area: 0xff, the syscall vectors, the GD-ROM entry */
    mset((void *)0x8c000000, 0xff, 0x8000);
    REG32(0x8c0000b0) = (u32)sys_syscall;
    REG32(0x8c0000b4) = (u32)font_stub;
    REG32(0x8c0000b8) = (u32)flash_syscall;
    REG32(0x8c0000bc) = (u32)gd_syscall;
    REG32(0x8c0000e0) = (u32)misc_syscall;
    REG16(0x8c0010f0) = 0xd001; /* mov.l @(4,pc),r0 */
    REG16(0x8c0010f2) = 0x402b; /* jmp @r0 */
    REG16(0x8c0010f4) = 0x0009;
    REG16(0x8c0010f6) = 0x0009;
    REG32(0x8c0010f8) = (u32)gd_syscall;

    /* An endless loop for the sound CPU until the game loads its driver */
    REG32(0xa0800000) = 0xeafffffe;

    /* IP.BIN and 1ST_READ.BIN */
    read_sectors(0x8c008000, H.ip_fad, 16, 0);
    boot_sectors = (H.boot_size + 2047) >> 11;
    read_sectors(0x8c010000, H.boot_fad, boot_sectors, 0);
    apply_patches();

    /* system id for SYSINFO (0x8c000068) */
    sys_syscall(0, 0, 0, 0);

    /* hardware as the BIOS leaves it */
    REG32(0xa070289c) = 0x48;      /* AICA SCIEB */
    REG32(0xa07028a8) = 0x18;      /* SCILV0 */
    REG32(0xa07028ac) = 0x50;      /* SCILV1 */
    REG32(0xa07028b0) = 0x08;      /* SCILV2 */
    REG32(0xffa00040) = 0x8201;    /* DMAC DMAOR */
    REG32(0xff80002c) = 0x000a03f0; /* PCTRA */

    /* flush everything we wrote to the program area (enter_game then
       invalidates the instruction cache) */
    for (u32 a = 0x8c000000; a < 0x8c010000 + boot_sectors * 2048; a += 32)
        __asm__ volatile("ocbwb @%0" : : "r"(a) : "memory");
    /* and our own data: the IP.BIN bootstrap invalidates the operand cache
       (CCR.OCI), which would drop anything of ours still only in it */
    for (u32 a = RES_BASE; a < RES_FLASH + 0x20000; a += 32)
        __asm__ volatile("ocbwb @%0" : : "r"(a) : "memory");

    ubc_setup();
    enter_game(0xac008300, 0x8d000000);
}
