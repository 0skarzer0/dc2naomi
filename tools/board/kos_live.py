#!/usr/bin/env python3
"""kos_live.py IP ADDR [WAIT [STEP]]: read a KallistiOS program built with NAOMI_HOST over the NetDIMM.

Runs ON the Raspberry (needs /sbin/piforce/dm_netboot). ADDR is the address of the program's
`naomi_live` structure (printed by homebrew/mk64/build_mk64.sh, or `sh-elf-nm prog.elf | grep naomi_live`),
e.g. 0x0c10d868 for Mario Kart 64's game and 0x0c0734e4 for its loader (they change with every build).
Polls the structure every STEP seconds (default 2) until the program halts or WAIT seconds pass (default
120), then prints the exception it recorded, if any, and everything KallistiOS printed (8 KB ring).

The patched KallistiOS (homebrew/mk64/kos-680d1862-naomi_host.patch) answers the NetDIMM's peeks from a
thread of its own every 2 ms and every vblank, so this works while the program runs, and also after it
crashed: arch_abort/exit/reboot stop there and keep answering instead of resetting the board.

Do not leave timehack.py running while reading (wipiloader with "hackoff", or kill it): with both talking
to the NetDIMM, peeks came back with stale values.

naomi_live (kernel/arch/dreamcast/hardware/maple/maple_utils.c), little endian, offsets in bytes:
  0x00 magic "LIVE"  0x04 vbls  0x08 served  0x0c last_cmd  0x10 istext
  0x14 irq_pc 0x18 irq_pr 0x1c irq_sr  (what the last vblank interrupted)
  0x20 main_pc 0x24 main_pr            (thread 1's saved context)
  0x28 pc_ring[16]                     (irq_pc of the last 16 vblanks: a sampling profiler)
  0x68 thd_polls 0x6c halted 0x70 halt_pr 0x74 halt_why (1 abort, 2 exit, 3 reboot) 0x78 log_pos
  0x7c exc_code exc_evt exc_pc exc_pr exc_sr  0x90 exc_r[16]  0xd0 EXPEVT INTEVT TEA
  0xdc log[8192]
"""
import struct
import sys
import time

sys.path.append('/sbin/piforce/dm_netboot')
from netdimm import NetDimm, PeekPokeTypeEnum as T    # noqa: E402

ip, base = sys.argv[1], int(sys.argv[2], 0)
wait = int(sys.argv[3]) if len(sys.argv) > 3 else 120
step = int(sys.argv[4]) if len(sys.argv) > 4 else 2
d = NetDimm(ip)
d.poke(0x01fffffc, T.TYPE_LONG, 0)          # address window = main RAM
pk = lambda off: d.peek((base + off) & 0x01ffffff, T.TYPE_LONG)
names = "magic vbls served last_cmd istext irq_pc irq_pr irq_sr main_pc main_pr".split()
t0 = time.time()
last = None
v = [0]
tail = [0] * 5
while time.time() - t0 < wait:
    try:
        v = [pk(4 * i) for i in range(10)]
        tail = [pk(0x68 + 4 * i) for i in range(5)]
    except Exception as e:
        print("t+%3ds  no answer (%s)" % (time.time() - t0, type(e).__name__), flush=True)
        time.sleep(step)
        continue
    line = " ".join("%s=%08x" % (n, x) for n, x in zip(names, v)) + \
        "  thd=%d halted=%d pr=%08x why=%d logpos=%d" % tuple(tail)
    if line != last:
        print("t+%3ds  %s" % (time.time() - t0, line), flush=True)
        last = line
    if v[0] == 0x4556494c and tail[1] == 1:
        break
    time.sleep(step)
if v[0] != 0x4556494c:
    sys.exit("no naomi_live at %#x (wrong address, or the program has not started yet)" % base)
ex = [pk(0x7c + 4 * i) for i in range(24)]
if ex[0] or ex[2]:
    print("exception code=%d evt=%04x PC=%08x PR=%08x SR=%08x" % tuple(ex[:5]))
    print("  R0-R7  " + " ".join("%08x" % x for x in ex[5:13]))
    print("  R8-R15 " + " ".join("%08x" % x for x in ex[13:21]))
    print("  EXPEVT=%08x INTEVT=%08x TEA=%08x" % tuple(ex[21:24]))
n = min(tail[4], 8192)
raw = b"".join(struct.pack("<I", pk(0xdc + 4 * i)) for i in range(2048))
start = tail[4] & 8191
log = (raw[start:] + raw[:start]) if tail[4] > 8192 else raw[:n]
print("----- log (%d bytes) -----" % n)
print(log.decode("latin-1"))
