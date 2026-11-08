/* dc2naomi: which PVR (TA) registers keep what KallistiOS writes, on the NAOMI 2 (text on screen). */
#include <kos.h>
#include <dc/pvr.h>
#include <arch/timer.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include "font.h"
KOS_INIT_FLAGS(INIT_IRQ | INIT_FS_ALL | INIT_MAPLE_ALL);
uintptr_t arch_stack_32m = 0x8dc00000;
#define REG(a) (*(volatile uint32_t *)(a))
static int cx, cy; static uint16_t fg = 0xffff;
static void put_char(int col, int row, char c) {
    if (c < 32 || c > 126) c = '?';
    const unsigned char *g = font8x16[c - 32];
    uint16_t *base = (uint16_t *)(0xa5000000 + (REG(0xa05f8050) & 0x00fffffc));
    for (int y = 0; y < 16; y++) { uint16_t *p = base + (row * 16 + y) * 640 + col * 8;
        for (int x = 0; x < 8; x++) p[x] = (g[y] & (0x80 >> x)) ? fg : 0; }
}
static void out(const char *s) { for (; *s; s++) {
    if (*s == '\n' || cx >= 80) { cx = 0; if (++cy >= 30) cy = 0; if (*s == '\n') continue; }
    put_char(cx++, cy, *s); } }
static void say(const char *fmt, ...) { char b[256]; va_list ap; va_start(ap, fmt); vsnprintf(b, sizeof b, fmt, ap);
    va_end(ap); out(b); dbglog(DBG_INFO, "%s", b); }

static const struct { uint16_t off; const char *n; } R[] = {
    {0x000,"ID"},{0x004,"REV"},{0x008,"SOFTRST"},{0x020,"PARAM_B"},{0x02c,"REGION_B"},{0x030,"SPANSORT"},
    {0x044,"FB_RCTRL"},{0x048,"FB_WCTRL"},{0x060,"FB_WSOF1"},{0x07c,"FPU_PARAM"},{0x098,"ISP_FEED"},
    {0x0a0,"SDRAM_REF"},{0x0a4,"SDRAM_ARB"},{0x0a8,"SDRAM_CFG"},{0x124,"TA_OL_B"},{0x128,"TA_ISP_B"},
    {0x12c,"TA_OL_LIM"},{0x130,"TA_ISP_LIM"},{0x134,"TA_OPB_POS"},{0x138,"TA_ITP_CUR"},{0x13c,"TA_TILECLIP"},
    {0x140,"TA_ALLOC"},{0x164,"TA_OPBINIT"},
};
static void dump(const char *tag) {
    say("%s\n", tag);
    for (unsigned i = 0; i < sizeof R / sizeof R[0]; i++) {
        say("%-10s%08lx%s", R[i].n, REG(0xa05f8000 + R[i].off), (i % 4) == 3 ? "\n" : " ");
    }
    say("\n");
}
static void rw(uint16_t off, uint32_t v) {
    volatile uint32_t *r = (volatile uint32_t *)(0xa05f8000 + off);
    uint32_t old = *r; *r = v; uint32_t got = *r; *r = old;
    static int n;
    say(" %03x: w %08lx r %08lx %s%s", off, v, got, got == v ? "ok  " : "BAD!", (++n & 1) ? "" : "\n");
}
int main(void) {
    vid_set_mode(DM_640x480, PM_RGB565);
    pvr_init_defaults();                 /* (sets the frame buffer used for the text) */
    vid_clear(0, 0, 0);
    fg = 0x07ff; say("dc2naomi PVR register test (KOS DC-SWAT fork)  SYSMODE=%08lx ELAN id=%08lx\n",
        REG(0xa05f74b0), REG(0xa8800000)); fg = 0xffff;
    dump("A after pvr_init_defaults:");
    say("B write/read back (TA registers):\n");
    rw(0x124, 0x00500000); rw(0x128, 0x00400000); rw(0x12c, 0x00580000); rw(0x130, 0x00480000);
    rw(0x13c, 0x000e0013); rw(0x140, 0x00100002); rw(0x164, 0x00500000); rw(0x020, 0x00300000);
    /* one frame */
    pvr_poly_cxt_t cxt; pvr_poly_hdr_t hdr;
    pvr_poly_cxt_col(&cxt, PVR_LIST_OP_POLY); pvr_poly_compile(&hdr, &cxt);
    pvr_scene_begin(); pvr_list_begin(PVR_LIST_OP_POLY); pvr_prim(&hdr, sizeof hdr);
    pvr_vertex_t v; v.flags = PVR_CMD_VERTEX; v.z = 1; v.argb = 0xffff0000; v.oargb = 0;
    v.x = 100; v.y = 300; pvr_prim(&v, sizeof v); v.x = 100; v.y = 100; pvr_prim(&v, sizeof v);
    v.x = 300; v.y = 300; pvr_prim(&v, sizeof v); v.flags = PVR_CMD_VERTEX_EOL; v.x = 300; v.y = 100; pvr_prim(&v, sizeof v);
    pvr_list_finish();
    uint32_t seen = 0; uint64_t t = timer_ms_gettime64();
    while (timer_ms_gettime64() - t < 300) seen |= REG(0xa05f6900);
    say("C after the opaque list (before render): ISTNRM seen %08lx\n", seen);
    dump("  registers now:");
    pvr_scene_finish();
    t = timer_ms_gettime64(); seen = 0;
    while (timer_ms_gettime64() - t < 300) seen |= REG(0xa05f6900);
    say("D after scene_finish: ISTNRM seen %08lx  ISTERR %08lx\n", seen, REG(0xa05f6908));
    fg = 0x07e0; say("done\n");
    for (;;) thd_sleep(1000);
}
