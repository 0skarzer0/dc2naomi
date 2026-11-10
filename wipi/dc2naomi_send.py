#!/usr/bin/env python3
"""dc2naomi_send.py IP JUEGO_dc2naomi.bin.gz: sends a dc2naomi image as netdimm_send does (same NetDIMM calls,
--disable-crc), with the game's Visual Memory.

If the image has a Visual Memory slot (built with the VMU: tools/addvmu.py, or "vmu" in its profile), the card in
JUEGO_dc2naomi.vmu next to the image (an empty formatted one if there is no file yet) is put into the slot on the
fly, and dc2naomi_vmu.py is left watching the game to bring back what it saves. Any other image is sent unchanged.
For WiPi Netbooter: /sbin/piforce, called from wipiloader.py (see wipi/README.md)."""
import io
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/sbin/piforce/dm_netboot')
sys.path.append(HERE)
import dc2naomi_vmu as vmu    # noqa: E402

VMU_OFFSET_AT = 176 * 4       # struct dimm_header.vmu_offset


def slot_of(raw):
    """Image offset of the Visual Memory slot, or 0."""
    if raw[:5] != b'NAOMI' or len(raw) < 0x400:
        return 0
    so, _, sl = struct.unpack_from('<III', raw, 0x360)
    base = (so + sl + 0xffff) & ~0xffff
    if len(raw) < base + 0x1000 or struct.unpack_from('<2I', raw, base) != (0x47434459, 0x32474d49):
        return 0
    flags = struct.unpack_from('<I', raw, base + 16)[0]
    off = struct.unpack_from('<I', raw, base + VMU_OFFSET_AT)[0]
    if not (flags & 0x8000) or not off or base + off + vmu.SIZE > len(raw):
        return 0
    return base + off


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ip, image = sys.argv[1], sys.argv[2]
    from arcadeutils import FileBytes
    from netdimm import NetDimm, NetDimmVersionEnum

    vmu.stop(ip)                                    # the game running now may have a save to bring back
    p = subprocess.Popen(['pigz', '-cd', '-p', '8', image], stdout=subprocess.PIPE, close_fds=True)
    raw = p.communicate()[0]
    slot = slot_of(raw)
    card_path = image[:-len('.bin.gz')] + '.vmu' if image.endswith('.bin.gz') else image + '.vmu'
    with io.BytesIO(raw) as fp:
        data = FileBytes(fp)
        if slot:
            card = vmu.load(card_path)
            if card is None:
                if os.path.exists(card_path):       # not a card: keep it aside, start an empty one
                    os.replace(card_path, card_path + '.bad')
                    vmu.log(card_path, 'is not a formatted 128 KB card: renamed to .bad')
                card = vmu.blank()
            data[slot:slot + vmu.SIZE] = bytes(card)
            vmu.log('sending', image, 'with', card_path, 'at', hex(slot))
        netdimm = NetDimm(ip, version=NetDimmVersionEnum.VERSION_4_01, log=print)
        netdimm.send(data, None, disable_crc_check=True)
        netdimm.reboot()
    if slot:
        subprocess.Popen([sys.executable, os.path.join(HERE, 'dc2naomi_vmu.py'), 'watch', ip, card_path],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
