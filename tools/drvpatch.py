# drvpatch.py IMAGE [OFFSET] : keep the AICA in 8 MB RAM mode (bit 9 of 0x2800) in Ikaruga's MANATEE.DRV
# (the ARM sound driver), inside a built netboot image. The driver writes 0 / 15 to 0x00802800 at start
# (2 MB mode); KallistiOS keeps that bit set on non-retail hardware (spu_ram_mode).
# mov r1,#0 / #15 -> mov r1,#0x200. Without OFFSET the driver is searched for (Ikaruga: 0x96000).
import sys, struct
WORDS = ((0x140, 0xe3a01000), (0x174, 0xe3a0100f), (0x760, 0xe3a01000))
img = sys.argv[1]
d = bytearray(open(img, 'rb').read())
if len(sys.argv) > 2:
    base = int(sys.argv[2], 0)
else:
    base, i = None, -1
    while True:
        i = d.find(struct.pack('<I', 0xe3a0100f), i + 1)
        if i < 0:
            break
        b = i - 0x174
        if b >= 0 and all(struct.unpack_from('<I', d, b + o)[0] == v for o, v in WORDS):
            base = b
            break
    assert base is not None, 'MANATEE.DRV not found (already patched?)'
for off, old in WORDS:
    v = struct.unpack_from('<I', d, base + off)[0]
    assert v == old, (hex(off), hex(v))
    struct.pack_into('<I', d, base + off, 0xe3a01c02)
    print(hex(base + off), hex(old), '-> 0xe3a01c02')
open(img, 'wb').write(d)
