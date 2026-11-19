# mkbin.py IMAGE.bin.gz OUT.bin [CARD.vmu]: unpack and put the card in the VMU slot (as dc2naomi_send.py)
import gzip, sys
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..', '..', 'wipi'))
import dc2naomi_send as s
raw = bytearray(gzip.open(sys.argv[1]).read())
slot = s.slot_of(raw)
if len(sys.argv) > 3 and slot:
    raw[slot:slot + 0x20000] = open(sys.argv[3], 'rb').read()
print('slot', hex(slot), len(raw))
open(sys.argv[2], 'wb').write(raw)
