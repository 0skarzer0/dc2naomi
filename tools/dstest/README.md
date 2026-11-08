# dstest: DreamShell's boot path with readable text on screen

Built against the DC-SWAT KallistiOS fork at the revision DreamShell 4.0.4 pinned (`14bc62b6`, Dreamcast build),
with `INIT_CDROM` off so each step is printed before it runs (8x16 font from DejaVu Sans Mono, `font.h`).
One change to the fork for the test: `int cdrom_skip_g1_unlock` in `hardware/cdrom.c` (skip the G1 bus protection
unlock in `cdrom_init`). Steps: system mode and G1 protection status, cdrom_init, TOC (both areas), PIO read of the
PVD, iso9660 mount and listings, `/cd/DS/lua/startup.lua`, a timed 1 MB read (unaligned buffers, as `fread`: the
sector cache path), raw DMA reads, then the G1 unlock done by hand and a PIO read after it.

    source KOSFORK/environ.sh   # KOS_SUBARCH=pristine, gcc13 + /opt/toolchains/dc/compat
    make
    # disc: IP.BIN + 1ST_READ.BIN (dstest.bin) + DS/ ; profile "dstest" in tools/games.py

Note found with it: KallistiOS's iso9660 reads into 32-byte aligned buffers by GD streaming (CMD_DMAREAD_STREAM +
DMA transfers) and waits for the G1 DMA end interrupt, which the resident never raises ("Previous DMA request is in
progress"). Unaligned reads go through the sector cache and work.
