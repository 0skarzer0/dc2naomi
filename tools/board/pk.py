#!/usr/bin/env python3
"""pk.py IP ADDR[:COUNT] ... : 32-bit peeks through the dc2naomi resident (RAM, or Holly/SH4 through its window).
Runs ON the Raspberry (needs /sbin/piforce/dm_netboot). Only works while a dc2naomi game is running and calling
its controller or GD-ROM routines; with the game hung every peek times out (rubbish after 15-30 s)."""
import sys
sys.path.append('/sbin/piforce/dm_netboot')
from netdimm import NetDimm, PeekPokeTypeEnum as T
d = NetDimm(sys.argv[1]); WIN = 0x01fffffc; cur = None
def peek(a):
    global cur
    ram = 0x0c000000 <= (a & 0x1fffffff) < 0x0e000000 and a < 0xff000000
    base = 0 if ram else (0xff000000 if a >= 0xff000000 else 0xa0000000 | (a & 0x1e000000))
    if base != cur:
        d.poke(WIN, T.TYPE_LONG, base); cur = base
    return d.peek(a & 0x01ffffff, T.TYPE_LONG)
for arg in sys.argv[2:]:
    a, _, n = arg.partition(':'); a = int(a, 0)
    vals = [peek(a + 4 * i) for i in range(int(n or 1))]
    print('%08x: %s' % (a, ' '.join('%08x' % v for v in vals)), flush=True)
if cur: d.poke(WIN, T.TYPE_LONG, 0)
