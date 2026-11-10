/* Dreamcast games on the NAOMI: the loader the BIOS starts.

   KallistiOS brings the hardware up (the MIE and the JVS I/O board on the
   maple bus among it), then we put the resident part (the stand-in for the
   Dreamcast BIOS, see ../resident) in the upper 16 MB with the flash ROM
   image, stop KallistiOS and hand over: the resident part loads IP.BIN and
   1ST_READ.BIN from the NetDIMM and starts the game as the BIOS would. */
#include <kos.h>
#include <string.h>
#include <arch/cache.h>
#include "../resident/resident.h"

extern const uint8_t resident_bin[], resident_bin_end[];

#ifdef NOSPU
/* Leave the sound chip (AICA) and the G2 DMA as the NAOMI BIOS left them, as a NAOMI game would find
   them: KallistiOS would otherwise reset the ARM, switch the AICA to 8 MB mode, start an ARM loop and
   set up the G2 DMA channels and their interrupts.
   Built with -Wl,--wrap=spu_init -Wl,--wrap=g2_dma_init (build.sh, NOSPU=1). */
int __wrap_spu_init(void) { return 0; }
int __wrap_g2_dma_init(void) { return 0; }
#endif

#define CART_OFFSETH (*(volatile uint16_t *)0xA05F7000)
#define CART_OFFSETL (*(volatile uint16_t *)0xA05F7004)
#define CART_DATA    (*(volatile uint16_t *)0xA05F7008)

static void cart_read(void *dst, uint32_t src, uint32_t len) {
    uint16_t *o = dst;
    irq_mask_t old = irq_disable();
    CART_OFFSETL = src & 0xffff;
    CART_OFFSETH = 0x8000 | ((src >> 16) & 0x1fff);
    for (uint32_t i = 0; i < len; i += 2)
        *o++ = CART_DATA;
    irq_restore(old);
}

static struct dimm_header hdr __attribute__((aligned(32)));
static uint8_t naomi_hdr[0x400] __attribute__((aligned(32)));

static void fail(const char *why) {
    printf("\n  FAILED: %s\n", why);
    for (;;) thd_sleep(1000);
}

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;
    dbgio_dev_select("fb");
    printf("\n\n  dc2naomi: Dreamcast game on NAOMI\n\n");

    cart_read(naomi_hdr, 0, sizeof naomi_hdr);
    if (memcmp(naomi_hdr, "NAOMI", 5) != 0) fail("no NAOMI header in the NetDIMM");
    uint32_t seg_offset, seg_length;
    memcpy(&seg_offset, &naomi_hdr[0x360], 4);
    memcpy(&seg_length, &naomi_hdr[0x368], 4);
    uint32_t base = (seg_offset + seg_length + 0xffff) & ~0xffffu;
    cart_read(&hdr, base, sizeof hdr);
    if (hdr.magic[0] != DIMM_MAGIC0 || hdr.magic[1] != DIMM_MAGIC1) fail("no disc image after the program");
    hdr.archive_base = base;
    for (uint32_t i = 0; i < hdr.nranges && i < DIMM_RANGES; i++)
        printf("  sectors: FAD %lu+%lu at 0x%08lx\n", (unsigned long)hdr.ranges[i].fad,
               (unsigned long)hdr.ranges[i].count, (unsigned long)(base + hdr.ranges[i].offset));
    printf("  1ST_READ.BIN: FAD %lu, %lu bytes\n", (unsigned long)hdr.boot_fad, (unsigned long)hdr.boot_size);

    /* the resident part and the flash ROM image */
    size_t res_size = resident_bin_end - resident_bin;
    memcpy((void *)RES_BASE, resident_bin, res_size);
    cart_read((void *)RES_FLASH, base + hdr.flash_offset, 0x20000);
    /* the Visual Memory the image brings (the netbooter puts the game's .vmu file in the slot while sending):
       taken only if it is a formatted card; otherwise the one still in RAM, or a new one (resident) */
    *(volatile uint32_t *)(RES_VMU_INFO + 8) = 0;
    if ((hdr.flags & DIMM_VMU) && hdr.vmu_offset) {
        static uint8_t card[0x20000] __attribute__((aligned(32)));
        cart_read(card, base + hdr.vmu_offset, sizeof card);
        const uint8_t *root = card + 255 * 512;
        int ok = root[0x46] == 0xfe;                  /* FAT at block 254 */
        for (int i = 0; i < 16; i++) ok = ok && root[i] == 0x55;
        if (ok) {
            memcpy((void *)RES_VMU, card, sizeof card);
            *(volatile uint32_t *)(RES_VMU_INFO + 8) = 0x494d4731;
        }
        printf("  Visual Memory: %s\n", ok ? "from the image" : "no card in the image");
    }
    const res_table_t *t = (const res_table_t *)RES_BASE;
    if (t->magic != RES_MAGIC) fail("resident part");
    printf("  resident part: %u bytes, maple hook at %08lx\n", (unsigned)res_size, (unsigned long)t->maple_hook);
    dcache_wback_range(RES_BASE, 0x200000);
    dcache_wback_range(RES_VMU, 0x21000);
    icache_sync_range(RES_BASE, res_size);

    /* a moment for the JVS board, then off we go */
    printf("\n  starting...\n");
    thd_sleep(1500);

    irq_disable();
    *(volatile uint32_t *)0xa05f6c14 = 0;            /* maple DMA off */
    while (*(volatile uint32_t *)0xa05f6c18 & 1) ;
    *(volatile uint8_t *)0xffd80004 = 0;             /* TMU stopped */
    for (int i = 0; i < 3; i++) {                     /* ASIC interrupts masked */
        *(volatile uint32_t *)(0xa05f6910 + i * 4) = 0;
        *(volatile uint32_t *)(0xa05f6920 + i * 4) = 0;
        *(volatile uint32_t *)(0xa05f6930 + i * 4) = 0;
    }
    t->boot(&hdr);
    return 0;
}
