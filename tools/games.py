"""Per-game settings for build_image.py.

Patches come in groups, one per program as it sits in memory: `file` is the
file on the disc (IP.BIN = the 16 sectors of the system area), `base` the
address it is loaded at (written through P1, 0x8c...). Every patch is
(address, size, new value); the build script reads the original value from
the file, so the resident part only patches memory that still holds it, and
each group starts with a check word taken from the same file. HOOK = the
resident maple hook. The disc files never go into this repository: the
values here are addresses and instruction words only.

How to find the three things a Katana game needs patched (see HANDOFF.md):
- cable type: the read of PDTRA (0xff800030, or @(4,PCTRA 0xff80002c)) ->
  mov #0,Rn (VGA);
- maple: the literal with the "address to physical" function the driver
  calls right before writing SB_MDSTAR (base+4) and SB_MDST (base+24) -> HOOK;
- G1 bus timings (0xa05f7484.., 0xa05f7490/94, 0xa05f74a0, 0xa05f74b4) in
  hardware init tables -> aimed at spare RAM (SCRATCH).
"""

HOOK = 0xFFFFFFFF
G2CHK0 = 0xFFFFFFFE  # resident G2 FIFO check with a timeout (SB_FFST bit 0)
G2CPU = 0xFFFFFFFC   # resident g2cpu: G2 DMA start done by the CPU
G2CHK4 = 0xFFFFFFFD  # the same for bit 4
HOOKST = 0xFFFFFFFB  # KallistiOS maple_dma_addr(): the maple hook, and its result written to SB_MDSTAR
TRAMP = "tramp"  # value for a jump literal: through the resident (patches the next program first)
# The channel 2 DMA to the direct texture path at 0x11000000 (LMMODE0 = 0) writes nothing to VRAM on a
# NAOMI 2 (measured on the board, CH2TEST); its mirror at 0x13000000 (LMMODE1 = 0) works, and is the
# same path on a Dreamcast. Texture DMA bases 0x11000000 -> 0x13000000.
TEXPATH = 0x13000000
# A call literal of a function taking such a destination in r4: through a resident stub that turns
# 0x11xxxxxx into 0x13xxxxxx (only one shared function per program: up to 4 different targets).
R4FIX = "r4fix"
SCRATCH = 0xADD7F000  # RES_SCRATCH in resident.h


def mov_imm0(reg):
    """mov #0,Rn"""
    return 0xE000 | reg << 8


GAMES = {
    # Daytona USA 2001 (US). First attempt: black screen on the real board.
    "daytona": {
        "title": "DAYTONA USA DC",
        "pads": "menu",       # START (on release), START + lever = up/down, lever = B/A, wheel lock = left/right
        "region": 1,          # USA
        "language": 1,        # English
        "layout": "rebuild",  # needs re-encoded music to fit 512 MB
        "volume": "DAYTONAUSA",
        "music_rate": 32000,
        "flags": 0x0004,      # no user break (the UBC hangs the real board: the old 0x0001 sampler
                              # used it, which is probably why Daytona was black on the board)
        "hook_pc": [],
        "groups": [
            {"file": "IP.BIN", "base": 0x8C008000, "patches": [
                (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type: VGA
                (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
                (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
            ]},
            {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
                (0x8C1D21EE, 2, 0x000B),               # syCblCheck (copy 1): rts
                (0x8C1D21F0, 2, mov_imm0(0)),          #   mov #0,r0 -> VGA
                (0x8C1F6866, 2, 0x000B),               # syCblCheck (copy 2)
                (0x8C1F6868, 2, mov_imm0(0)),
                (0x8C1E966C, 4, HOOK),                 # maple: address-to-physical call
                # (2026-11-09: aimed at SCRATCH, not at 0xac00fe00.. in the Katana system area as before)
                (0x8C1F3764, 4, SCRATCH + 0x20),       # G1RWC.. (0xa05f7484) -> RAM
                (0x8C1F3778, 4, SCRATCH + 0x30),       # G1GDRC, G1GDWC (0xa05f74a0)
                (0x8C1F3784, 4, SCRATCH + 0x40),       # G1CRDYC.. (0xa05f74b4)
            ]},
        ],
    },

    # Yu Suzuki Game Works Vol. 1 (Japan; the Shenmue II bonus disc).
    # 1ST_READ.BIN = a 64 KB monitor (copied to 0x8c004000, own VBR at
    # 0x8c00f400) + the menu YSC.BIN at 0x8c020000, which runs OutRun,
    # Hang-On, After Burner II and Space Harrier as overlays with its own
    # drivers. Power Drift is a program of its own: the menu puts LOADER.BIN
    # at 0x8c800000, copies PD.BIN to 0x8c010000 and jumps there; on exit
    # PD goes through mon.bin and LOADER.BIN (at 0x0c800000), which loads
    # 1ST_READ.BIN again and jumps to 0x0c010000.
    "ysgw": {
        "title": "YU SUZUKI GAME WORKS",
        "pads": "ysgw",       # default wheel controls; START + wheel full right/left = plane/driving controls
        "region": 0,          # Japan
        "language": 0,        # Japanese
        "layout": "gdi",      # original sector layout (213 MB: track 6 + system area)
        # no user break (0x0004): on the real board the program-start break (DBR) hung right as
        # 1ST_READ.BIN started (license screen, then black). Trampolines + GD-ROM polls instead.
        "flags": 0x0004,
        "hook_pc": [0x8C010000, 0x0C010000],
        "groups": [
            {"file": "IP.BIN", "base": 0x8C008000, "patches": [
                (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type: mov.w @(4,r3),r0 -> VGA
                (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490 (GD PIO timing)
                (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0 (GD DMA timing)
            ]},
            {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
                (0x8C1F58C6, 2, mov_imm0(2)),          # YSC cable: mov.w @r1,r2 (PDTRA) -> mov #0,r2
                (0x8C1F1F60, 4, HOOK),                 # YSC maple: literal of the call before SB_MDSTAR
                (0x8C053688, 4, TRAMP),                # YSC: jmp to PD.BIN at 0x8c010000 -> trampoline
                (0x8C2151B0, 4, TEXPATH),              # YSC texture DMA: 0x11000000 + VRAM offset
                # YSC: every call of the ch2 DMA queue function 0x8c2122a0 (destination in r4)
                (0x8C206338, 4, R4FIX), (0x8C2065F4, 4, R4FIX), (0x8C2098F0, 4, R4FIX),
                (0x8C20CDCC, 4, R4FIX), (0x8C214698, 4, R4FIX), (0x8C2151B4, 4, R4FIX),
            ]},
            {"file": "PD.BIN", "base": 0x8C010000, "patches": [
                (0x8C01B766, 2, mov_imm0(4)),          # Power Drift cable: mov.w @r3,r4 -> mov #0,r4
                (0x8C032D44, 4, HOOK),                 # Power Drift maple
                (0x8C02A404, 4, TEXPATH),              # Power Drift texture DMA
            ]},
            {"file": "LOADER.BIN", "base": 0x8C800000, "patches": [
                (0x8C80BCA6, 2, mov_imm0(2)),          # loader cable (runs at 0x0c80bca6)
                (0x8C8112DC, 4, HOOK),                 # loader maple
                (0x8C800480, 4, TRAMP),                # loader: jsr to 1ST_READ.BIN at 0x0c010000 -> trampoline
                (0x8C822B4C, 4, TEXPATH),              # loader texture DMA
            ]},
        ],
    },
    # Namco Museum (USA, 2000; Mass Media). One program: 1ST_READ.BIN at 0x8c010000,
    # Shinobi 1.43 + KAMUI2 (1999), no G1 timing writes of its own. Has Pole Position.
    "nmus": {
        "title": "NAMCO MUSEUM",
        "pads": "pole",       # menu controls + Pole Position: gas = A, brake = B, lever = R (Low/High)
        # no VMU: with the emulated VMU the board stays black after the SEGA logo (nmus5); without, it plays (2026-11-09)       # plain START (on release), START + lever = up/down, wheel lock = left/right
        "region": 1,          # USA
        "language": 1,        # English
        "layout": "gdi",
        "flags": 0x0004,      # no user break
        "hook_pc": [],
        "groups": [
            {"file": "IP.BIN", "base": 0x8C008000, "patches": [
                (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type -> VGA
                (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
                (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
            ]},
            {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
                (0x8C0A8782, 2, mov_imm0(4)),          # cable: mov.w @r3,r4 (PDTRA) -> mov #0,r4
                (0x8C02E860, 4, HOOK),                 # maple: address-to-physical call before SB_MDSTAR
                (0x8C01A0C0, 4, TEXPATH),              # KAMUI2 texture DMA: 0x11000000 | VRAM offset
                # (2026-11-09) The SB_FFST bit 5 patch (0x8C0A9944 tst #32 -> tst #0) is now only in
                # "nmus_ffst": the real hang was most likely the resident's PCTRA write (removed).
            ]},
        ],
    },
    # Crazy Taxi 2 (USA, 2001; Hitmaker). One program: 1ST_READ.BIN at 0x8c010000, Shinobi 1.76.
    # Only boot patches: the maple driver calls its address-to-physical routine (0x8c16852e) with bsr,
    # so there is no literal for the hook yet (controls not adapted).
    "ct2": {
        "title": "CRAZY TAXI 2",
        "region": 1,          # USA
        "language": 1,        # English
        "layout": "gdi",
        "flags": 0x0004,      # no user break
        "hook_pc": [],
        "groups": [
            {"file": "IP.BIN", "base": 0x8C008000, "patches": [
                (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type -> VGA
                (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
                (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
            ]},
            {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
                (0x8C15E656, 2, mov_imm0(4)),          # cable: mov.w @r3,r4 (PDTRA) -> mov #0,r4
            ]},
        ],
    },
    # Ikaruga (Japan, 2002; Treasure). One program: 1ST_READ.BIN 1 MB at 0x8c010000, Shinobi (cvFs/gdCi 1.03).
    # Boot patches only (controls not adapted). SB_FFST waits test bits 0 and 4.
    "ikaruga": {
        "title": "IKARUGA",
        "pads": "joy",        # standard NAOMI cabinet: 2 sticks, 6 buttons per player, 2 STARTs
        "region": 0,          # Japan
        "language": 0,        # Japanese
        "layout": "gdi",
        "flags": 0x0004,      # no user break
        "hook_pc": [],
        "groups": [
            {"file": "IP.BIN", "base": 0x8C008000, "patches": [
                (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type -> VGA
                (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
                (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
            ]},
            {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
                (0x8C04D0E4, 2, mov_imm0(0)),          # cable: mov.w @r3,r0 (PDTRA) -> mov #0,r0
                # The game first asks the cable type the Dreamcast BIOS leaves in the AICA register
                # 0xa0702c00 (bits 9:8; function 0x8c04d03c: shlr8; and #3,r0). A NAOMI never wrote it,
                # and a 3 there sends the game on to a "composite" (15 kHz) mode, which a VGA monitor
                # cannot show. and #3,r0 -> mov #0,r0: always VGA.
                (0x8C04D05C, 2, mov_imm0(0)),
                # maple: literal of the "address to physical" call (0x8c04ae50, and 0x0fffffff) right
                # before the start of the maple DMA (r8 = SB_MDSTAR, then 1 -> SB_MDST) -> resident hook,
                # so the game talks to the resident's controller (JVS inputs) instead of the MIE.
                (0x8C048758, 4, HOOK),
            ]},
        ],
    },
}

# Ikaruga with the G2 FIFO watch (diagnostics): the two Shinobi "G2 FIFO empty?" checks
# (0x8c044c28: SB_FFST bit 0, 0x8c045308: bit 4; each `mov.l @(12,pc),r2; mov.l @r2,r0; tst #n,r0;
# movt r3; rts; mov.l r3,@r4`) become `mov.l @(4,pc),r0; jmp @r0; nop; nop; .long resident`, so a
# wait that never ends gives up after ~1 s and draws rows 16-19 (see resident.c, g2chk).
import copy as _copy
GAMES["ikaruga_g2"] = _copy.deepcopy(GAMES["ikaruga"])
GAMES["ikaruga_g2"]["groups"][1]["patches"] += [
    (0x8C044C28, 2, 0xD001), (0x8C044C2A, 2, 0x402B), (0x8C044C2C, 2, 0x0009), (0x8C044C2E, 2, 0x0009),
    (0x8C044C30, 4, G2CHK0),
    (0x8C045308, 2, 0xD001), (0x8C04530A, 2, 0x402B), (0x8C04530C, 2, 0x0009), (0x8C04530E, 2, 0x0009),
    (0x8C045310, 4, G2CHK4),
]

# Ikaruga without the sound uploads (test): the G2 DMA start function of the sound library
# (0x8c04522c, the only caller 0x8c04f8de) returns 0 at once: no sound bank ever goes to the AICA.
# Hangs in Flycast too (no end callback: the .MLT loader waits for it forever). Superseded by g2cpu.
GAMES["ikaruga_nosnd"] = _copy.deepcopy(GAMES["ikaruga"])
GAMES["ikaruga_nosnd"]["groups"][1]["patches"] += [
    (0x8C04522C, 2, 0x000B),   # mov.l r14,@-r15 -> rts
    (0x8C04522E, 2, 0xE000),   # mov.l r13,@-r15 -> mov #0,r0
]

# Ikaruga with the sound library's G2 DMA start (0x8c04522c) sent to the resident g2cpu: the data
# goes to the AICA by CPU and the game's end-of-DMA handler (0x8c044cbc) runs a few ms later from
# TMU2, as the interrupt would (on the board the AICA G2 DMA never ends: ADST stays 1). Reaches the
# title in Flycast with no real G2 DMA at all. Build with tools/drvpatch.py (AICA 8 MB mode) on top.
GAMES["ikaruga_g2cpu"] = _copy.deepcopy(GAMES["ikaruga"])
GAMES["ikaruga_g2cpu"]["groups"][1]["patches"] += [
    (0x8C04522C, 2, 0xD001), (0x8C04522E, 2, 0x402B), (0x8C045230, 2, 0x0009), (0x8C045232, 2, 0x0009),
    (0x8C045234, 4, G2CPU),
]

# Ikaruga with the AICA G2 DMA started by the CPU alone: ADTSEL = 0 (the library writes 5 = hardware
# trigger | suspend enable). On the board ADSUSP bit 4 (DMA request input from the AICA) read 0, while
# in Flycast it is 1 from the second transfer on: with suspend enabled the DMA may wait for a request
# that never comes. The earlier CPU-trigger test wrote 4 and kept suspend enable.
GAMES["ikaruga_tsel0"] = _copy.deepcopy(GAMES["ikaruga"])
GAMES["ikaruga_tsel0"]["groups"][1]["patches"] += [
    (0x8C0452A6, 2, 0xE100),   # mov.l @(20,r14),r1 (desc TSEL) -> mov #0,r1
    (0x8C0452A8, 2, 0xE300),   # or r1,r3 -> mov #0,r3
]

# Virtua Tennis (USA; Hitmaker). One program: 1ST_READ.BIN 2 MB at 0x8c010000. Its sound goes to the
# AICA by CPU, not by G2 DMA (Flycast trace: only the G2 DMA library's setup transfer), so it tells
# whether the G2 DMA stall Ikaruga hits is what stops every game on the board. Boot patches only.
GAMES["vt"] = {
    "title": "VIRTUA TENNIS",
    "region": 1,          # USA
    "language": 1,        # English
    "layout": "gdi",
    "flags": 0x0004,      # no user break
    "hook_pc": [],
    "groups": [
        {"file": "IP.BIN", "base": 0x8C008000, "patches": [
            (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type -> VGA
            (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
            (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
        ]},
        {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
            (0x8C1EA8AA, 2, mov_imm0(4)),          # cable: mov.w @r3,r4 (PDTRA) -> mov #0,r4
        ]},
    ],
}

# Virtua Athlete 2000 (USA; Hitmaker, 2000). Made for Dreamcast first, ported to NAOMI in 2002 (Virtua
# Athletics, GDS-0019). One program: 1ST_READ.BIN 1.7 MB at 0x8c010000, Shinobi 1.69, sd for DC 2.02.07,
# CRI ADX. The NAOMI version runs the same code on "Kunoichi for NAOMI 0.96" (syG2 1.02.01, sd 2.02.11);
# its G2 DMA start function is the same as the Dreamcast one. Boot patches only.
GAMES["va"] = {
    "title": "VIRTUA ATHLETE 2000",
    "region": 1,          # USA
    "language": 1,        # English
    "layout": "gdi",
    "flags": 0x0004,      # no user break
    "hook_pc": [],
    "groups": [
        {"file": "IP.BIN", "base": 0x8C008000, "patches": [
            (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type -> VGA
            (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
            (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
        ]},
        {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
            (0x8C19325A, 2, mov_imm0(4)),          # cable: mov.w @r3,r4 (PDTRA) -> mov #0,r4
        ]},
    ],
}

# Virtua Athlete with the AICA G2 DMA started by the CPU alone (ADTSEL 0), as ikaruga_tsel0.
GAMES["va_tsel0"] = _copy.deepcopy(GAMES["va"])
GAMES["va_tsel0"]["groups"][1]["patches"] += [
    (0x8C1943FA, 2, 0xE100),   # mov.l @(20,r14),r1 (desc TSEL) -> mov #0,r1
    (0x8C1943FC, 2, 0xE300),   # or r1,r3 -> mov #0,r3
]

# Midway's Greatest Arcade Hits Vol. 2 (USA, 2001; Digital Eclipse). A Windows CE disc: IP.BIN boots
# 0WINCEOS.BIN (the CE kernel, at 0x8c010000), which loads its DLLs and the emulators (Spy Hunter,
# 720°, Gauntlet, Paperboy, Rampage...). 28 high-density tracks (data 3 and 30, 26 CDDA music tracks
# the resident does not play). CE reads the cable type from the AICA register 0x2c00, which the
# resident now sets to VGA at boot. Boot patches only (no maple hook: Windows CE has MAPLE.DLL).
GAMES["mw2"] = {
    "title": "MIDWAY ARCADE HITS 2",
    "region": 1,          # USA
    "language": 1,        # English
    "layout": "gdi",
    "boot": "0WINCEOS.BIN",
    "flags": 0x0004,      # no user break
    "hook_pc": [],
    "groups": [
        {"file": "IP.BIN", "base": 0x8C008000, "patches": [
            (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type -> VGA
            (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
            (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
        ]},
    ],
}

# Re-Volt (USA, 1999; Acclaim). One program: 1ST_READ.BIN 2.9 MB at 0x8c010000, Shinobi 1.43 with the
# Audio64 sound driver (SFX/AUDIO64.DRV). Music in 14 CDDA tracks (not played by the resident).
# Boot patches only.
GAMES["rv"] = {
    "title": "RE-VOLT",
    "region": 1,          # USA
    "language": 1,        # English
    "layout": "gdi",
    "flags": 0x0004,      # no user break
    "hook_pc": [],
    "groups": [
        {"file": "IP.BIN", "base": 0x8C008000, "patches": [
            (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type -> VGA
            (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
            (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
        ]},
        {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
            (0x8C0F2082, 2, mov_imm0(4)),          # cable: mov.w @r3,r4 (PDTRA) -> mov #0,r4
            # Shinobi 1.43 G2 library: the same SB_FFST bit 5 wait as Namco Museum (0x8c0a9944):
            # tst #32,r0 -> tst #0,r0
            (0x8C0F2FE4, 2, 0xC800),
        ]},
    ],
}

# Crazy Taxi 2 with the maple hook: the DMA start (0x8c166e40..5e: r8 = SB_MDSTAR, jsr to the
# address-to-physical function 0x8c16852e through the literal 0x8c166ee0) -> resident hook, so the
# game talks to the resident (JVS inputs) instead of the MIE. On the board the plain ct2 got past the
# logo to the memory card screen about 1 time in 6: the maple scan of the MIE is a suspect.
GAMES["ct2h"] = _copy.deepcopy(GAMES["ct2"])
GAMES["ct2h"]["groups"][1]["patches"] += [
    (0x8C166EE0, 4, HOOK),
]


# DreamShell (DC-SWAT, https://github.com/DC-SWAT/DreamShell) by netboot: a KallistiOS program, so the loader
# and the resident just play the Dreamcast BIOS. SOURCE is a directory with IP.BIN (a standard SEGA one, here
# taken from the user's own disc: the boot patches below are those of Virtua Tennis), 1ST_READ.BIN = DS_CORE.BIN
# with KallistiOS's top of RAM lowered from 0x8e000000 to 0x8dc00000 (the resident lives there) and the DS/
# folder of the release. DreamShell finds its root at /cd/DS (KallistiOS iso9660 through the GD syscalls).
GAMES["ds"] = {
    "title": "DREAMSHELL",
    "region": 1,          # USA
    "language": 1,        # English
    "layout": "rebuild",
    "rock_ridge": True,
    "volume": "DREAMSHELL",
    "flags": 0x0404,      # no user break, GD DMA reads in one call
    "hook_pc": [],
    "groups": [
        {"file": "IP.BIN", "base": 0x8C008000, "patches": [
            (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type -> VGA
            (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
            (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
        ]},
        {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
            (0x8C25D4C4, 4, 0x8DC00000),           # arch_stack_32m (4.0.4 release): top of RAM below the resident
        ]},
    ],
}


# The same with EMU_DS_CORE.BIN of the release (built with DS_EMU: no IDE/SD probe at start, so nothing pokes the
# G1 ATA registers, which on NAOMI are the cartridge port) and without KallistiOS's G1 bus protection unlock in
# cdrom_init (write 0x1fffff to 0xa05f74e4 and read the whole BIOS so the bus checks it): on NAOMI that bus is the
# NetDIMM's, and with a multibios the check may fail and lock it. First seen on the board: DreamShell alive (GD
# calls going on) but black, as if every read came back as garbage.
GAMES["ds_emu"] = dict(GAMES["ds"], groups=[
    GAMES["ds"]["groups"][0],
    {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
        (0x8C25D4C4, 4, 0x8DC00000),           # arch_stack_32m: top of RAM below the resident
        (0x8C15BA1E, 2, 0x0018),               # cdrom_init: cmp/eq #3,r0 (protection passed?) -> sett: skip the unlock
    ]},
])


# dc2naomi/tools/dstest (built against the DC-SWAT KallistiOS fork, Dreamcast build): DreamShell's boot steps
# with readable text on the screen. Same disc layout as "ds" (the DS/ folder), its own 1ST_READ.BIN.
GAMES["dstest"] = dict(GAMES["ds"], title="DSTEST", groups=[GAMES["ds"]["groups"][0]])


# DEBUG_DS_CORE.BIN of the release (DS_DEBUG: KallistiOS log level KDEBUG, timings; IDE/SD probes on). With
# CONSOLE=1 the whole log is drawn on the screen.
GAMES["ds_dbg"] = dict(GAMES["ds"], groups=[
    GAMES["ds"]["groups"][0],
    {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
        (0x8C25D504, 4, 0x8DC00000),           # arch_stack_32m (DEBUG core): top of RAM below the resident
    ]},
])

# Namco Museum with the old SB_FFST bit 5 patch (Shinobi 1.43 G2 library waits, interrupts masked, for bit 5 to
# clear; newer libraries and KOS test bits 0 and 4): tst #32,r0 -> tst #0,r0.
GAMES["nmus_ffst"] = dict(GAMES["nmus"], groups=[
    GAMES["nmus"]["groups"][0],
    dict(GAMES["nmus"]["groups"][1], patches=GAMES["nmus"]["groups"][1]["patches"] + [(0x8C0A9944, 2, 0xC800)]),
])

# F355 Challenge: Passione Rossa (USA, 2000; AM2). One program: 1ST_READ.BIN 1.6 MB at 0x8c010000 (KAMUI 1.11,
# Shinobi maple driver with the context at +0x10bc/+0x10f4 as Power Drift). Its startup also writes the G1 GD
# timings (0x8c011046, only in one config mode) and sets SB_MDAPRO = 0x6155404f (the resident reopens it).
def _katana_drive(title, cable, hook):
    return {
        "title": title,
        "pads": "menu",       # START (on release), START + lever = up/down, lever = B/A, wheel lock = left/right
        # no VMU: the emulated VMU fails on the board (Namco Museum black, F355 stuck at Now Loading, 2026-11-09)
        "region": 1,          # USA
        "language": 1,        # English
        "layout": "gdi",
        "flags": 0x0004,      # no user break
        "hook_pc": [],
        "groups": [
            {"file": "IP.BIN", "base": 0x8C008000, "patches": [
                (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type -> VGA
                (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
                (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
            ]},
            {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
                (cable, 2, mov_imm0(2)),               # cable: mov.w @r1,r2 (PDTRA 0xff800030) -> mov #0,r2
                (hook, 4, HOOK),                       # maple: literal of the "to physical" call before SB_MDSTAR
                (0x8C011128, 4, SCRATCH + 0x20),       # startup G1 timings: 0xa05f7490/94
                (0x8C01112C, 4, SCRATCH + 0x30),       #   0xa05f74a0
                (0x8C011130, 4, SCRATCH + 0x40),       #   0xa05f707c
            ]},
        ],
    }


GAMES["f355"] = _katana_drive("FERRARI 355 DC",  # no title starting "F355": Flycast takes it for the arcade F355 (own BIOS)
                                  0x8C0DE946, 0x8C0EC81C)
# 18 Wheeler: American Pro Trucker (USA, 2001; AM2). Same startup and maple driver (KAMUI2, Shinobi).
GAMES["w18"] = _katana_drive("18 WHEELER DC", 0x8C15B2A6, 0x8C16A580)
# Board, 2026-11-10: the "menu" map has no X/Y, so the view (Y) could not be changed; "wheel" gives
# START + gas = Y (change view) and START + brake = X (horn).
GAMES["w18"]["pads"] = "wheel"

# Namco Museum without the emulated VMU (to tell a VMU problem from a maple one on the board).
GAMES["nmus_novmu"] = dict(GAMES["nmus"], vmu=False)


# Fighting games for the standard NAOMI cabinet (2 sticks, 6 buttons per player, 2 STARTs): mandos `joy`.
# Patch points found with tools/findpatch.py (cable read of PDTRA, maple "to physical" literal), checked by hand.
def _katana_joy(title, region, language, patches):
    return {
        "title": title,
        "pads": "joy",
        "region": region,
        "language": language,
        "layout": "gdi",
        "flags": 0x0004,      # no user break
        "hook_pc": [],
        "groups": [
            {"file": "IP.BIN", "base": 0x8C008000, "patches": [
                (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type -> VGA
                (0x8C00DAB4, 4, SCRATCH + 0x00),       # init table: 0xa05f7490
                (0x8C00DAC0, 4, SCRATCH + 0x10),       # init table: 0xa05f74a0
            ]},
            {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": patches},
        ],
    }


# The King of Fighters: Dream Match 1999 (USA). 42 CDDA tracks (music): the resident plays no CDDA.
GAMES["kof99"] = _katana_joy("KOF DREAM MATCH 1999", 1, 1, [
    (0x8C1109F2, 2, mov_imm0(4)),   # cable: mov.w @r3,r4 (PDTRA) -> mov #0,r4
    (0x8C1D28B0, 4, HOOK),          # maple: to-physical 0x8c1d3f06, result to @r8 = SB_MDSTAR
])
# The Last Blade 2 (USA). To-physical 0x8c033230 (`mov.l @r15,r0; and r3,r0`, not found by findpatch).
GAMES["lb2"] = _katana_joy("LAST BLADE 2 DC", 1, 1, [
    (0x8C014EB0, 2, mov_imm0(0)),   # cable: mov.w @r3,r0 (PDTRA) -> mov #0,r0
    (0x8C014E28, 2, mov_imm0(0)),   # cable bits the DC BIOS leaves in AICA 0xa0702c00: and #3,r0 -> mov #0,r0
    (0x8C030DE4, 4, HOOK),          # maple: literal loaded at 0x8c030d4a, then SB_MDST = 1
])
# 911 MB of data. To fit the 512 MB NetDIMM the 29 character story movies (ZSFD/NN_*.SFD) all point at the shortest
# one (25_SHIGEN2.SFD, 6 MB) and their data is left out. Left out as zeros instead, the opening hangs (Flycast).
GAMES["lb2"]["alias"] = (["ZSFD/[0-2][0-9]_*.SFD"], "ZSFD/25_SHIGEN2.SFD")
# Street Fighter III: 3rd Strike (USA). 1ST_READ.BIN is 14 MB (up to 0x8cdeaa00).
GAMES["sf3ts"] = _katana_joy("SF3 THIRD STRIKE DC", 1, 1, [
    (0x8CD6A7A6, 2, mov_imm0(4)),   # cable
    (0x8CD89DE8, 4, HOOK),          # maple: to-physical 0x8cd8b436
])
# Street Fighter III: Double Impact (USA).
GAMES["sf3di"] = _katana_joy("SF3 DOUBLE IMPACT DC", 1, 1, [
    (0x8C08210A, 2, mov_imm0(4)),   # cable
    (0x8C091A10, 4, HOOK),          # maple: to-physical 0x8c09305e
])
# Super Puzzle Fighter II X for Matching Service (Japan).
GAMES["spf2x"] = _katana_joy("SUPER PUZZLE FIGHTER IIX", 0, 0, [
    (0x8C1AB24E, 2, mov_imm0(4)),   # cable
    (0x8C1D0BE4, 4, HOOK),          # maple: to-physical 0x8c1d2232
])
# Super Street Fighter II X for Matching Service (Japan).
GAMES["ssf2x"] = _katana_joy("SUPER STREET FIGHTER IIX", 0, 0, [
    (0x8C2310CA, 2, mov_imm0(4)),   # cable
    (0x8C26C150, 4, HOOK),          # maple: to-physical 0x8c26d79e
])
# The King of Fighters 2002 (Japan, En/Ja) and Garou: Mark of the Wolves (USA): the SNK engine of Last Blade 2
# (same cable code at the same addresses, AICA cable read too).
GAMES["kof02"] = _katana_joy("KOF 2002 DC", 0, 1, [
    (0x8C015838, 2, mov_imm0(0)),   # cable: mov.w @r3,r0 (PDTRA) -> mov #0,r0
    (0x8C0157B0, 2, mov_imm0(0)),   # AICA cable bits: and #3,r0 -> mov #0,r0
    (0x8C032B54, 4, HOOK),          # maple: to-physical 0x8c034fa0, then SB_MDST = 1
])
GAMES["motw"] = _katana_joy("MARK OF THE WOLVES DC", 1, 1, [
    (0x8C015838, 2, mov_imm0(0)),   # cable
    (0x8C0157B0, 2, mov_imm0(0)),   # AICA cable bits
    (0x8C032B2C, 4, HOOK),          # maple: to-physical 0x8c034f78
])


# OutRun 2006 Coast 2 Coast, fan demo for Dreamcast (homebrew, KallistiOS 2.x; "OUTRUN DC DEMO", v24, 2026-11-09).
# Not a Katana game: KOS does its own hardware set-up. Same treatment as DreamShell (SYNCREAD, top of RAM below the
# resident), plus our maple hook in KOS's own maple driver. 598 MB of data: the attract movie and five songs are
# aliased to fit 512 MB.
GAMES["or2006"] = {
    "title": "OUTRUN 2006 C2C",
    "region": 2,          # Europe (the disc says JUE)
    "language": 1,        # English
    "layout": "gdi",
    "pads": "wheel",
    "flags": 0x1404,      # no user break, GD DMA reads in one call, 1ST_READ.BIN started directly (homebrew IP.BIN)
    "hook_pc": [],
    "alias": [(["MVATTR.VQV"], "MVTS.VQV"),
              (["MUS18.ADP", "MUS16.ADP", "MUS17.ADP", "MUS5.ADP", "MUS4.ADP"], "MUS3.ADP")],
    "groups": [
        {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
            (0x8C0862F4, 4, 0x8DC00000),   # arch_stack_32m 0x8e000000 -> top of RAM below the resident
            (0x8C04FBCC, 4, HOOKST),       # maple_dma_addr(): literal 0x1fffffff -> maple_hook_mdstar
            (0x8C04FBC2, 2, 0x412B),       #   and r1,r4 -> jmp @r1
            (0x8C04FBC4, 2, 0x0009),       #   mov.l (SB_MDSTAR),r1 -> nop (delay slot)
            (0x8C04B6BA, 2, 0x0018),       # cdrom_init: cmp/eq #3,r0 -> sett (skip the G1 bus unlock)
            (0x8C0581F4, 2, 0x0008),       # vid_check_cable(): tst r0,r0 -> clrt: VGA, no PCTRA write
            (0x8C058512, 2, 0x0008),       # vid_set_mode(): the same inlined check
            (0x8C0588D2, 2, 0x0008),       # vid_init(): the same
        ]},
    ],
}

# Sega Rally 2 (USA, 1999; Sega). A Windows CE disc like mw2: IP.BIN boots 0WINCEOS.BIN. Music in 17 CDDA
# tracks (4-20; not played by the resident). Boot patches only, to start the study of Windows CE.
CEMAPLE = 0xFFFFFFFA       # PATCH_CEMAPLE: the resident's ce_maple_isr
GAMES["sr2"] = dict(GAMES["mw2"], title="SEGA RALLY 2 DC", pads="wheel", vmu=True, groups=GAMES["mw2"]["groups"] + [
    # 0WINCEOS.BIN is a container with a 0x800-byte header (see GdiDisc.boot in build_image.py), so base =
    # 0x8c010000 - 0x800. The kernel's interrupt handler for ISTNRM & IML4NRM (0x8c02e0ac): the branch for bits
    # 12/13 (maple DMA end, SYSINTR 18) at 0x8c02e114 becomes a jump to the resident (see ce_maple_poll).
    {"file": "0WINCEOS.BIN", "base": 0x8C00F800, "patches": [
        (0x8C02E194, 4, CEMAPLE),   # literal 0xffffcfff (used only there) -> ce_maple_isr
        (0x8C02E116, 2, 0x432B),    # and r3,r2 -> jmp @r3
        (0x8C02E118, 2, 0x0009),    # mov #18,r0 -> nop
    ]},
])
