/* dc2naomi: DreamShell's video path (KOS DC-SWAT fork, Dreamcast build) with text on screen.
   Text first (written straight to the frame buffer), then 3D: a coloured square moving on blue.
   If the 3D works it covers the text; if a step never ends, the last line shows where. */
#include <kos.h>
#include <dc/pvr.h>
#include <dc/video.h>
#include <arch/timer.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include "font.h"

KOS_INIT_FLAGS(INIT_IRQ | INIT_FS_ALL | INIT_MAPLE_ALL);
uintptr_t arch_stack_32m = 0x8dc00000;

static int cx, cy;
static uint16_t fg = 0xffff;
#define REG(a) (*(volatile uint32_t *)(a))

static void put_char(int col, int row, char c) {
    if (c < 32 || c > 126) c = '?';
    const unsigned char *g = font8x16[c - 32];
    uint32_t sof = REG(0xa05f8050) & 0x00fffffc;
    uint16_t *base = (uint16_t *)(0xa5000000 + sof);
    for (int y = 0; y < 16; y++) {
        uint16_t *p = base + (row * 16 + y) * 640 + col * 8;
        for (int x = 0; x < 8; x++) p[x] = (g[y] & (0x80 >> x)) ? fg : 0x0000;
    }
}
static void out(const char *s) {
    for (; *s; s++) {
        if (*s == '\n' || cx >= 80) { cx = 0; if (++cy >= 30) cy = 0; if (*s == '\n') continue; }
        put_char(cx++, cy, *s);
    }
}
static void say(const char *fmt, ...) {
    char b[256]; va_list ap; va_start(ap, fmt); vsnprintf(b, sizeof b, fmt, ap); va_end(ap);
    out(b); dbglog(DBG_INFO, "%s", b);
}
static void regs(void) {
    say("   FB_R_CTRL=%08lx SOF1=%08lx SOF2=%08lx ISTNRM=%08lx ISTERR=%08lx\n", REG(0xa05f8044),
        REG(0xa05f8050), REG(0xa05f8054), REG(0xa05f6900), REG(0xa05f6908));
}

static uint16_t tex_src[64 * 64] __attribute__((aligned(32)));
static volatile uint32_t vbl;
static void vbl_cb(uint32_t c, void *d) { (void)c; (void)d; vbl++; }
static void irqinfo(const char *tag) {
    uint32_t sr; __asm__ volatile("stc sr,%0" : "=r"(sr));
    say("%s ISTNRM=%08lx EXT=%08lx ERR=%08lx SR=%08lx ICR=%04x\n", tag, REG(0xa05f6900), REG(0xa05f6904),
        REG(0xa05f6908), sr, *(volatile uint16_t *)0xffd00000);
    say("   IML2 %08lx %08lx %08lx  IML4 %08lx %08lx %08lx  IML6 %08lx %08lx %08lx\n", REG(0xa05f6910),
        REG(0xa05f6914), REG(0xa05f6918), REG(0xa05f6920), REG(0xa05f6924), REG(0xa05f6928), REG(0xa05f6930),
        REG(0xa05f6934), REG(0xa05f6938));
}
static void elaninfo(void) {
    uint32_t id = REG(0xa8800000);
    if (id != 0xe1ad0000) { say("   ELAN: none (id=%08lx)\n", id); return; }
    say("   ELAN: rev=%08lx IFCTL=%08lx IRQSTAT=%08lx IRQMASK=%08lx\n", REG(0xa8800004), REG(0xa8800010),
        REG(0xa8800074), REG(0xa8800078));
}

int main(int argc, char **argv) {
    (void)argc; (void)argv;
    uint64_t t0;
    vid_set_mode(DM_640x480, PM_RGB565);
    vid_clear(0, 0, 0);
    fg = 0x07ff; say("dc2naomi DreamShell video test (KOS DC-SWAT fork, Dreamcast build)\n"); fg = 0xffff;
    say("1 SYSMODE=%08lx  PVR ID=%08lx REV=%08lx\n", REG(0xa05f74b0), REG(0xa05f8000), REG(0xa05f8004));
    regs();

    vblank_handler_add(vbl_cb, NULL);
    irqinfo("1b"); elaninfo();
    { uint64_t t = timer_ms_gettime64(); uint32_t v0 = vbl; while (timer_ms_gettime64() - t < 1000) {}
      say("1c vblank IRQs in 1 s: %lu\n", (unsigned long)(vbl - v0)); }
    say("2 pvr_init_defaults... ");
    int r = pvr_init_defaults();
    say("rv=%d\n", r); regs();

    say("3 pvr_dma_init... ");
    pvr_dma_init();
    say("ok\n");

    for (int i = 0; i < 64 * 64; i++) tex_src[i] = ((i >> 3) ^ (i >> 9)) & 1 ? 0xffe0 : 0xf800;
    pvr_ptr_t tex = pvr_mem_malloc(64 * 64 * 2);
    say("4 pvr_mem_malloc tex=%08lx\n", (unsigned long)tex);

    say("5 pvr_txr_load (CPU/SQ)... ");
    pvr_txr_load(tex_src, tex, 64 * 64 * 2);
    say("ok\n");

    say("6 pvr_txr_load_dma (ch2 DMA, no block)... ");
    dcache_flush_range((uintptr_t)tex_src, sizeof tex_src);
    r = pvr_txr_load_dma(tex_src, tex, 64 * 64 * 2, false, NULL, NULL);
    t0 = timer_ms_gettime64();
    while (!pvr_dma_ready() && timer_ms_gettime64() - t0 < 2000) {}
    say("rv=%d ready=%d after %lu ms  DMAOR=%08lx CHCR2=%08lx\n", r, pvr_dma_ready(),
        (unsigned long)(timer_ms_gettime64() - t0), REG(0xffa00040), REG(0xffa0002c));
    regs();

    say("   QACR0=%08lx QACR1=%08lx MMUCR=%08lx CCR=%08lx LMMODE0=%08lx LMMODE1=%08lx\n", REG(0xff000038),
        REG(0xff00003c), REG(0xff000010), REG(0xff00001c), REG(0xa05f6884), REG(0xa05f6888));
    pvr_set_bg_color(0.0f, 0.0f, 0.6f);
    for (int mode = 0; mode < 2; mode++) {
        if (mode == 1) {
            static uint8_t vbuf[2][128 * 1024] __attribute__((aligned(32)));
            pvr_init_params_t prm = { { PVR_BINSIZE_16, PVR_BINSIZE_0, PVR_BINSIZE_16, PVR_BINSIZE_0, PVR_BINSIZE_0 },
                                      256 * 1024, 1, 0, 0, 3, 0 };
            say("8 switching to DMA vertex mode (as Katana): pvr_shutdown + pvr_init(dma)... ");
            pvr_shutdown();
            r = pvr_init(&prm);
            pvr_set_vertbuf(PVR_LIST_OP_POLY, vbuf[0], sizeof vbuf[0]);
            pvr_set_vertbuf(PVR_LIST_TR_POLY, vbuf[1], sizeof vbuf[1]);
            pvr_set_bg_color(0.0f, 0.4f, 0.0f);   /* green background in DMA mode */
            tex = pvr_mem_malloc(64 * 64 * 2);
            pvr_txr_load(tex_src, tex, 64 * 64 * 2);
            say("rv=%d\n", r);
        }
        say("%d %s: frames (square on %s covers the text if rendering works)\n", 7 + mode, mode ? "DMA" : "direct (SQ)", mode ? "GREEN" : "BLUE");
        pvr_poly_cxt_t cxt; pvr_poly_hdr_t hdr;
        pvr_poly_cxt_txr(&cxt, PVR_LIST_OP_POLY, PVR_TXRFMT_RGB565 | PVR_TXRFMT_NONTWIDDLED, 64, 64, tex, PVR_FILTER_NONE);
        pvr_poly_compile(&hdr, &cxt);
        int done = 0;
        uint64_t start = timer_ms_gettime64();
        for (int f = 0; ; f++) {
            t0 = timer_ms_gettime64();
            while (pvr_check_ready() != 0 && timer_ms_gettime64() - t0 < 3000) {}
            if (pvr_check_ready() != 0) {
                fg = 0xf800; say("  frame %d: NOT READY after 3 s\n", f); fg = 0xffff;
                say("   TA_OPB_POS=%08lx TA_VERTBUF_POS=%08lx ISTNRM=%08lx ISTERR=%08lx\n", REG(0xa05f8134),
                    REG(0xa05f8138), REG(0xa05f6900), REG(0xa05f6908));
                break;
            }
            pvr_scene_begin();
            pvr_list_begin(PVR_LIST_OP_POLY);
            pvr_prim(&hdr, sizeof hdr);
            float x = 100 + (f * 2) % 400, y = 150, sz = 160;
            pvr_vertex_t v;
            v.flags = PVR_CMD_VERTEX; v.z = 1; v.argb = 0xffffffff; v.oargb = 0;
            v.x = x;      v.y = y + sz; v.u = 0; v.v = 1; pvr_prim(&v, sizeof v);
            v.x = x;      v.y = y;      v.u = 0; v.v = 0; pvr_prim(&v, sizeof v);
            v.x = x + sz; v.y = y + sz; v.u = 1; v.v = 1; pvr_prim(&v, sizeof v);
            v.flags = PVR_CMD_VERTEX_EOL;
            v.x = x + sz; v.y = y;      v.u = 1; v.v = 0; pvr_prim(&v, sizeof v);
            pvr_list_finish();
            pvr_scene_finish();
            if (f == 0) {
                uint32_t seen = 0; uint64_t t = timer_ms_gettime64();
                while (timer_ms_gettime64() - t < 300) seen |= REG(0xa05f6900);
                say("  frame 0 sent: ISTNRM bits seen %08lx  TA_OPB_POS=%08lx TA_VERTBUF_POS=%08lx\n", seen,
                    REG(0xa05f8134), REG(0xa05f8138));
            }
            done = f + 1;
            if (mode == 0 && start && timer_ms_gettime64() - start > 5000) {
                say("  direct: %d frames in 5 s: direct mode works (keeps drawing)\n", done);
                start = 0;
            }
        }
        say("  %s: %d frames\n", mode ? "DMA" : "direct", done);
        if (mode == 0 && done > 100) { say("  direct mode works; staying here\n"); for (;;) thd_sleep(1000); }
    }
    for (;;) thd_sleep(1000);
    return 0;
}
