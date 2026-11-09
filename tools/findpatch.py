#!/usr/bin/env python3
"""findpatch.py FILES_DIR : find the dc2naomi patch points of a Katana game (IP.BIN + 1ST_READ.BIN at 0x8c010000).

Prints, for tools/games.py:
- IP.BIN: whether the standard bootstrap cable read (0x8c008382) and G1 timing table (0x8c00dab4/dac0) are there;
- cable: every read of PDTRA (literal 0xff800030 loaded, then mov.w @Rm,Rn) -> (addr, 2, mov #0,Rn);
- maple: literals of an "address to physical" function (and 0x0fffffff on r4) that are loaded right before a jsr
  whose result goes to @(4,Rn) (SB_MDSTAR) -> (literal, 4, HOOK);
- G1 timings: aligned literals 0xa05f7484/90/94/a0/b4 and 0xa05f707c in 1ST_READ.BIN -> SCRATCH.
Only addresses and instruction words are printed (nothing from the disc goes into the repository).
"""
import os
import struct
import sys

BASE = 0x8C010000


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def movl_target(op, pc):
    """mov.l @(disp,pc),Rn -> (literal address, n) or None"""
    if op >> 12 == 0xD:
        return ((pc & ~3) + 4 + (op & 0xFF) * 4, (op >> 8) & 15)
    return None


def main(d):
    ip = open(os.path.join(d, "IP.BIN"), "rb").read()
    print("IP.BIN 0x382 = %#06x (0x8532 = mov.w @(4,r3),r0 expected), 0x5ab4 = %#010x, 0x5ac0 = %#010x"
          % (u16(ip, 0x382), u32(ip, 0x5AB4), u32(ip, 0x5AC0)))
    b = open(os.path.join(d, "1ST_READ.BIN"), "rb").read()
    n = len(b)
    end = BASE + n

    def lit(a):
        o = a - BASE
        return u32(b, o) if 0 <= o <= n - 4 else None

    # cable
    print("# cable (PDTRA reads)")
    for i in range(0, n - 3, 2):
        t = movl_target(u16(b, i), BASE + i)
        if t and lit(t[0]) == 0xFF800030:
            m = t[1]
            for k in range(1, 4):
                if i + 2 * k + 1 >= n:
                    break
                op = u16(b, i + 2 * k)
                if op & 0xF00F == 0x6001 and (op >> 4) & 15 == m:      # mov.w @Rm,Rn
                    rn = (op >> 8) & 15
                    print("    (0x%08X, 2, mov_imm0(%d)),   # cable: mov.w @r%d,r%d (PDTRA) -> mov #0,r%d"
                          % (BASE + i + 2 * k, rn, m, rn, rn))
                    break
            else:
                print("    ? PDTRA loaded at 0x%08X, no mov.w @r%d,Rn right after" % (BASE + i, m))

    # cable type the Dreamcast BIOS leaves in the AICA (0xa0702c00 bits 9:8: shlr8; and #3,r0), as Ikaruga
    print("# cable (AICA 0xa0702c00 bits 9:8)")
    for i in range(0, n - 3, 2):
        t = movl_target(u16(b, i), BASE + i)
        if t and lit(t[0]) == 0xA0702C00:
            for k in range(1, 16):
                if i + 2 * k + 3 >= n:
                    break
                if u16(b, i + 2 * k) == 0x4019 and u16(b, i + 2 * k + 2) == 0xC903:   # shlr8 r0 ; and #3,r0
                    print("    (0x%08X, 2, mov_imm0(0)),   # AICA cable bits: and #3,r0 -> mov #0,r0"
                          % (BASE + i + 2 * k + 2))
                    break

    # "to physical" functions
    phys = set()
    for i in range(0, n - 1, 2):
        t = movl_target(u16(b, i), BASE + i)
        if t and lit(t[0]) == 0x0FFFFFFF:
            rx = t[1]
            win = [u16(b, i + 2 * k) for k in range(-3, 4) if 0 <= i + 2 * k < n - 1]
            if ((0x2009 | rx << 4) in win and (0x6043 in win or 0x60F2 in win)) or (rx == 0 and 0x2049 in win):  # and Rx,r0 + mov r4,r0 / and r4,r0
                for s in range(i - 8, i + 2, 2):                       # function start: a few candidates
                    phys.add(BASE + s)
    print("# maple (literal of the to-physical call before SB_MDSTAR)")
    strict, loose = [], []
    for i in range(0, n - 3, 4):
        v = u32(b, i)
        if (v & 0x1FFFFFFF) | 0x80000000 in phys and (v >> 29) in (0, 4, 5):
            la = BASE + i
            # who loads it
            for j in range(max(0, i - 1024), min(n - 1, i + 4), 2):
                t = movl_target(u16(b, j), BASE + j)
                if t and t[0] == la:
                    rr = t[1]
                    for k in range(1, 24):
                        if j + 2 * k >= n - 1:
                            break
                        op = u16(b, j + 2 * k)
                        if op == (0x400B | rr << 8):                    # jsr @rr
                            after = [u16(b, j + 2 * k + 2 * q) for q in range(1, 24) if j + 2 * k + 2 * q < n - 1]
                            if any(x & 0xF0FF == 0x1001 for x in after[:12]):     # mov.l r0,@(4,Rn)
                                strict.append("    (0x%08X, 4, HOOK),   # -> %#010x, loaded at 0x%08X, jsr at 0x%08X"
                                              % (la, v, BASE + j, BASE + j + 2 * k))
                            elif any(x & 0xF0FF == 0x2002 for x in after[:3]) and any(x & 0xF00F == 0x1006 for x in after[:10]):
                                # mov.l r0,@Rn (Rn = base+4), then mov.l Rm,@(24,Rn) (SB_MDST = 1)
                                loose.insert(0, "    (0x%08X, 4, HOOK),   # -> %#010x, loaded at 0x%08X, jsr at 0x%08X (r0,@Rn; MDST)"
                                             % (la, v, BASE + j, BASE + j + 2 * k))
                            elif any(x & 0xF0FF == 0x2002 for x in after[:3]):    # mov.l r0,@Rn (Rn = base+4)
                                loose.append("    (0x%08X, 4, HOOK),   # -> %#010x, loaded at 0x%08X, jsr at 0x%08X (r0,@Rn)"
                                             % (la, v, BASE + j, BASE + j + 2 * k))
                            break
    for line in strict or loose:
        print(line)
    if not (strict or loose):
        print("    ? none found (bsr call or another driver): look by hand")

    print("# G1 timings in 1ST_READ.BIN")
    slot = 0x20
    for i in range(0, n - 3, 4):
        v = u32(b, i)
        if v in (0xA05F7484, 0xA05F7488, 0xA05F748C, 0xA05F7490, 0xA05F7494, 0xA05F74A0, 0xA05F74B4, 0xA05F707C):
            print("    (0x%08X, 4, SCRATCH + 0x%02x),   # %#010x" % (BASE + i, slot, v))
            slot += 0x10


if __name__ == "__main__":
    main(sys.argv[1])
