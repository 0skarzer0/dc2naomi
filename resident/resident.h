/* Daytona USA (Dreamcast) on the NAOMI: what the loader and the resident
   part share.

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
#define RES_LOG         0x8dd80000u   /* debug log ring */

#define RES_MAGIC       0x524c4344u   /* "DCLR" */

/* The archive the build script puts after the loader in the netboot image,
   at the end of the program rounded up to 64 KB. Offsets are from the start
   of the archive; the GD-ROM image holds the high-density track's sectors
   (2048 bytes each) from base_fad on. */
#define DIMM_MAGIC0     0x47434459u   /* "YDCG" */
#define DIMM_MAGIC1     0x31474d49u   /* "IMG1" */
#define DIMM_PATCHES    32

struct dimm_patch {
    uint32_t addr;                    /* in the loaded program (0x8c...) */
    uint32_t size;                    /* 2 or 4; 0 = end */
    uint32_t value;                   /* 0xffffffff with size 4: the maple hook */
};

struct dimm_header {
    uint32_t magic[2];
    uint32_t version;
    uint32_t archive_base;            /* filled in by the loader: NetDIMM address */
    uint32_t image_offset;            /* the GD-ROM image */
    uint32_t image_sectors;
    uint32_t base_fad;                /* first sector of the image (45150) */
    uint32_t leadout_fad;
    uint32_t boot_fad;                /* 1ST_READ.BIN */
    uint32_t boot_size;
    uint32_t flash_offset;            /* 128 KB flash ROM image */
    uint32_t reserved[5];
    struct dimm_patch patches[DIMM_PATCHES];
};

/* The table at RES_BASE (see head.S). */
typedef struct {
    uint32_t magic;
    void (*boot)(const struct dimm_header *);
    uint32_t maple_hook;              /* address the game's maple driver calls */
    uint32_t bss_start, bss_end;
} res_table_t;

