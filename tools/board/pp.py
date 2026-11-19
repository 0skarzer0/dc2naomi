#!/usr/bin/env python3
"""pp.py IP ADDR=VALUE ... : 32-bit pokes into the game's RAM (0x8c000000-0x8dffffff) through the dc2naomi resident,
the twin of pk.py. Runs ON the Raspberry (needs /sbin/piforce/dm_netboot), only while a dc2naomi game is running.
Example: read_chunk of the running resident (address from `sh-elf-nm resident/resident.elf | grep read_chunk`, of the
same build as the image's loader) to 4 sectors: pp.py 10.0.0.4 0x8dc05174=4"""
import sys
sys.path.append('/sbin/piforce/dm_netboot')
from netdimm import NetDimm, PeekPokeTypeEnum as T
d = NetDimm(sys.argv[1])
d.poke(0x01fffffc, T.TYPE_LONG, 0)          # window register: plain RAM
for arg in sys.argv[2:]:
    a, _, v = arg.partition('=')
    a, v = int(a, 0), int(v, 0)
    assert 0x0c000000 <= (a & 0x1fffffff) < 0x0e000000, "solo RAM"
    d.poke(a & 0x01ffffff, T.TYPE_LONG, v)
    print('%08x <- %08x, ahora %08x' % (a, v, d.peek(a & 0x01ffffff, T.TYPE_LONG)), flush=True)
