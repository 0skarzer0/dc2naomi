/* dc2naomi: DreamShell boot path test, with readable text on screen.

   Runs the same KallistiOS (DC-SWAT fork, Dreamcast build) steps DreamShell takes before its menu:
   cdrom_init, TOC, sector reads by PIO and DMA, iso9660, /cd/DS/lua/startup.lua, a large file read.
   Every step is written on the screen (and to dbglog). Built against the fork with INIT_CDROM off so
   each step can be printed before it runs. */

#include <kos.h>
#include <dc/cdrom.h>
#include <dc/fs_iso9660.h>
#include <dc/video.h>
#include <arch/timer.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <dirent.h>
#include <fcntl.h>
#include <unistd.h>
#include "font.h"

KOS_INIT_FLAGS(INIT_IRQ | INIT_FS_ALL | INIT_MAPLE_ALL);

/* Keep KallistiOS's stack below the dc2naomi resident (0x8dc00000) if it sees 32 MB. */
uintptr_t arch_stack_32m = 0x8dc00000;

extern int cdrom_skip_g1_unlock;

#define COLS 80
#define ROWS 30
static int cx, cy;
static uint16_t fg = 0xffff;

static void put_char(int col, int row, char c) {
    if (c < 32 || c > 126) c = '?';
    const unsigned char *g = font8x16[c - 32];
    for (int y = 0; y < 16; y++) {
        uint16_t *p = vram_s + (row * 16 + y) * 640 + col * 8;
        for (int x = 0; x < 8; x++) p[x] = (g[y] & (0x80 >> x)) ? fg : 0x0000;
    }
}

static void scroll(void) {
    memmove(vram_s, vram_s + 16 * 640, (ROWS - 1) * 16 * 640 * 2);
    memset(vram_s + (ROWS - 1) * 16 * 640, 0, 16 * 640 * 2);
    cy = ROWS - 1;
}

static void out(const char *s) {
    for (; *s; s++) {
        if (*s == '\n' || cx >= COLS) {
            cx = 0;
            if (++cy >= ROWS) scroll();
            if (*s == '\n') continue;
        }
        put_char(cx++, cy, *s);
    }
}

static void say(const char *fmt, ...) {
    char b[256];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(b, sizeof b, fmt, ap);
    va_end(ap);
    out(b);
    dbglog(DBG_INFO, "%s", b);
}

static void hexline(const uint8_t *d, int n) {
    for (int i = 0; i < n; i++) say("%02x", d[i]);
    say(" ");
    for (int i = 0; i < n; i++) say("%c", d[i] >= 32 && d[i] < 127 ? d[i] : '.');
    say("\n");
}

static uint8_t sec[2048 * 4] __attribute__((aligned(32)));

static void list_dir(const char *path, int max) {
    DIR *d = opendir(path);
    if (!d) { fg = 0xf800; say("  opendir %s: FAILED\n", path); fg = 0xffff; return; }
    struct dirent *e;
    int n = 0;
    say("  %s:", path);
    while ((e = readdir(d)) && n < max) { say(" %s", e->d_name); n++; }
    say("%s\n", n == max ? " ..." : "");
    closedir(d);
}

int main(int argc, char **argv) {
    (void)argc; (void)argv;
    vid_set_mode(DM_640x480, PM_RGB565);
    vid_clear(0, 0, 0);
    fg = 0x07ff;
    say("dc2naomi DreamShell boot test (KOS DC-SWAT fork, Dreamcast build)\n");
    fg = 0xffff;

    uint32_t sysm = *(volatile uint32_t *)0xa05f74b0;
    uint32_t prot = *(volatile uint32_t *)0xa05f74ec;
    say("1 SYSMODE 5f74b0=%08lx  G1 prot status 5f74ec=%08lx (3=passed)\n", sysm, prot);
    say("  BIOS first word %04x  RAM top %08lx\n", *(volatile uint16_t *)0xa0000000, (unsigned long)_arch_mem_top);

    cdrom_skip_g1_unlock = 1;     /* as the emu2 image (no unlock) */
    say("2 cdrom_init (no G1 unlock)... ");
    cdrom_init();
    say("ok\n");

    int st = -1, ty = -1;
    int r = cdrom_get_status(&st, &ty);
    say("3 get_status rv=%d status=%d type=%d\n", r, st, ty);

    cd_toc_t toc;
    for (int hd = 0; hd < 2; hd++) {
        memset(&toc, 0xee, sizeof toc);
        r = cdrom_read_toc(&toc, hd);
        say("4 TOC(%s) rv=%d first=%08lx last=%08lx leadout=%08lx\n", hd ? "HD" : "SD", r,
            (unsigned long)toc.first, (unsigned long)toc.last, (unsigned long)toc.leadout_sector);
        say("  e0=%08lx e1=%08lx e2=%08lx data track LBA=%lu\n", (unsigned long)toc.entry[0],
            (unsigned long)toc.entry[1], (unsigned long)toc.entry[2], (unsigned long)cdrom_locate_data_track(&toc));
    }

    uint32_t pvd = 45000 + 16 + 150;
    memset(sec, 0xee, sizeof sec);
    uint64_t t0 = timer_ms_gettime64();
    r = cdrom_read_sectors_ex(sec, pvd, 1, false);
    say("5 PIO read FAD %lu rv=%d (%lu ms): ", (unsigned long)pvd, r, (unsigned long)(timer_ms_gettime64() - t0));
    hexline(sec, 12);

    say("8 fs_iso9660_init... ");
    fs_iso9660_init();
    say("ok\n");
    list_dir("/", 12);
    list_dir("/cd", 12);
    list_dir("/cd/DS", 16);

    int fd = open("/cd/DS/lua/startup.lua", O_RDONLY);
    say("9 open /cd/DS/lua/startup.lua: fd=%d\n", fd);
    if (fd >= 0) {
        memset(sec, 0, 64);
        int n = read(fd, sec + 1, 48);          /* unaligned, as fread's buffer: sector cache path */
        say("  read %d: ", n);
        hexline(sec + 1, 24);
        close(fd);
    }

    const char *big = "/cd/DS/modules/curl.klf";
    fd = open(big, O_RDONLY);
    if (fd >= 0) {
        static uint8_t buf[256 * 1024] __attribute__((aligned(32)));
        size_t total = 0;
        int n;
        t0 = timer_ms_gettime64();
        while ((n = read(fd, buf + 2, sizeof buf - 2)) > 0) total += n;   /* unaligned: cache path */
        uint32_t ms = (uint32_t)(timer_ms_gettime64() - t0);
        say("10 read %s: %u bytes in %lu ms (%lu KB/s)\n", big, (unsigned)total, (unsigned long)ms,
            ms ? (unsigned long)(total / ms) : 0);
        close(fd);
    } else say("10 no big file to time\n");

    memset(sec, 0xee, sizeof sec);
    t0 = timer_ms_gettime64();
    r = cdrom_read_sectors_ex(sec, pvd, 1, true);
    say("6 DMA read FAD %lu rv=%d (%lu ms): ", (unsigned long)pvd, r, (unsigned long)(timer_ms_gettime64() - t0));
    hexline(sec, 12);

    memset(sec, 0xee, sizeof sec);
    r = cdrom_read_sectors_ex(sec, pvd, 4, true);
    say("7 DMA 4 sectors rv=%d: ", r);
    hexline(sec + 2048 * 3, 12);

    /* 11: the G1 bus protection unlock KallistiOS does in cdrom_init (skipped above), then read again */
    say("11 G1 unlock: status before=%08lx ... ", *(volatile uint32_t *)0xa05f74ec);
    *(volatile uint32_t *)0xa05f74e4 = 0x1fffff;
    for (volatile uint32_t *b = (volatile uint32_t *)0xa0000000; b < (volatile uint32_t *)0xa0200000; b++) (void)*b;
    say("after=%08lx\n", *(volatile uint32_t *)0xa05f74ec);
    memset(sec, 0xee, sizeof sec);
    r = cdrom_read_sectors_ex(sec, pvd, 1, false);
    say("12 PIO read after unlock rv=%d: ", r);
    hexline(sec, 12);

    fg = 0x07e0;
    say("done. Heartbeat (GD status every second):\n");
    fg = 0xffff;
    for (int i = 0;; i++) {
        cdrom_get_status(&st, &ty);
        char b[40];
        snprintf(b, sizeof b, "%6d st=%d ty=%d   ", i, st, ty);
        int sx = cx, sy = cy;
        cx = 0; cy = ROWS - 1;
        out(b);
        cx = sx; cy = sy;
        thd_sleep(1000);
    }
    return 0;
}
