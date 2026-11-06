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
        "region": 1,          # USA
        "language": 1,        # English
        "layout": "rebuild",  # needs re-encoded music to fit 512 MB
        "volume": "DAYTONAUSA",
        "music_rate": 32000,
        "flags": 0x0001,      # the PC sampler (diagnostics), as before
        "hook_pc": [],
        "groups": [
            {"file": "IP.BIN", "base": 0x8C008000, "patches": [
                (0x8C008382, 2, mov_imm0(0)),          # bootstrap cable type: VGA
            ]},
            {"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": [
                (0x8C1D21EE, 2, 0x000B),               # syCblCheck (copy 1): rts
                (0x8C1D21F0, 2, mov_imm0(0)),          #   mov #0,r0 -> VGA
                (0x8C1F6866, 2, 0x000B),               # syCblCheck (copy 2)
                (0x8C1F6868, 2, mov_imm0(0)),
                (0x8C1E966C, 4, HOOK),                 # maple: address-to-physical call
                (0x8C1F3764, 4, 0xAC00FE00),           # G1RWC.. (0xa05f7484) -> RAM
                (0x8C1F3778, 4, 0xAC00FE40),           # G1GDRC, G1GDWC (0xa05f74a0)
                (0x8C1F3784, 4, 0xAC00FE80),           # G1CRDYC.. (0xa05f74b4)
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
                # Shinobi 1.43 G2 library: CPU access to the AICA waits, with interrupts masked, for
                # SB_FFST (0xa05f688c) bit 5 to clear (newer libraries and KOS test bits 0 and 4).
                # Hang suspect on the NAOMI 2: tst #32,r0 -> tst #0,r0 (always ready).
                (0x8C0A9944, 2, 0xC800),
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
            ]},
        ],
    },
}
