#!/usr/bin/env python3
"""The Visual Memory of a dc2naomi game, kept in a file next to its image (WiPi Netbooter, /sbin/piforce).

  dc2naomi_vmu.py watch IP JUEGO.vmu   stays with the game: when it saves, the changed blocks are read from the
                                       NAOMI over the NetDIMM (peeks answered by the dc2naomi resident) into the file
  dc2naomi_vmu.py stop IP              before another game is sent: ends the watcher after a last look
  dc2naomi_vmu.py blank FILE           writes an empty formatted card (128 KB, 200 free blocks)

The file is a plain 128 KB dump of the card (the format emulators use). dc2naomi_send.py puts it into the image's
Visual Memory slot while sending, so the game starts with it. What the game saves reaches the file some seconds
later (24 blocks: about a minute): switching the cabinet off before that loses that save.
Log: /var/log/dc2naomi_vmu.log"""
import os
import signal
import struct
import sys
import time

sys.path.append('/sbin/piforce/dm_netboot')

SIZE = 0x20000
RAM_VMU = 0x01e00000        # RES_VMU as an offset into the NAOMI's RAM (what the NetDIMM sends of an address)
RAM_INFO = 0x01e20000       # RES_VMU_INFO: "VMUS", block writes since boot, 1 = card taken from the image
RAM_SEQ = RAM_INFO + 0x40   # per block: the write count at its last write
WINDOW = 0x01fffffc         # the resident's window register: 0 = RAM
MAGIC = 0x53554d56
POLL = 3                    # seconds between looks
SLOW = 2.0                  # a peek nobody answers comes back late with rubbish
LOG = '/var/log/dc2naomi_vmu.log'


def log(*a):
    line = time.strftime('%Y-%m-%d %H:%M:%S ') + ' '.join(str(x) for x in a)
    try:
        with open(LOG, 'a') as f:
            f.write(line + '\n')
    except OSError:
        pass


def blank():
    """An empty card, as the resident formats it (resident.c, vmu_format)."""
    v = bytearray(SIZE)
    root = 255 * 512
    v[root:root + 16] = b'\x55' * 16
    v[root + 0x30:root + 0x38] = bytes([0x20, 0x26, 0x11, 0x09, 0, 0, 0, 0])
    struct.pack_into('<12H', v, root + 0x40, 0xff, 0, 0xff, 0xfe, 1, 0xfd, 13, 0, 200, 0x1f, 0, 0)
    for b in range(256):
        e = 0xfffc
        if 242 <= b <= 253:
            e = b - 1
        if b in (241, 254, 255):
            e = 0xfffa
        struct.pack_into('<H', v, 254 * 512 + b * 2, e)
    return v


def valid(card):
    root = 255 * 512
    return len(card) == SIZE and card[root:root + 16] == b'\x55' * 16 and card[root + 0x46] == 0xfe


def load(path):
    """The card in the file, or None (no file, or not a formatted 128 KB card)."""
    try:
        with open(path, 'rb') as f:
            card = bytearray(f.read())
    except OSError:
        return None
    return card if valid(card) else None


def save(path, card):
    tmp = path + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(card)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


class Gone(Exception):
    """The resident did not answer (another game, the BIOS, the cabinet off)."""


class Board:
    def __init__(self, ip):
        from netdimm import NetDimm, PeekPokeTypeEnum
        self.d = NetDimm(ip)
        self.long = PeekPokeTypeEnum.TYPE_LONG

    def peek(self, off):
        t = time.time()
        try:
            v = self.d.peek(off, self.long)
        except Exception as e:
            raise Gone(str(e))
        if time.time() - t > SLOW:
            raise Gone('slow answer')
        return v

    def check(self):
        try:
            self.d.poke(WINDOW, self.long, 0)
        except Exception as e:
            raise Gone(str(e))
        if self.peek(RAM_INFO) != MAGIC:
            raise Gone('no dc2naomi Visual Memory there')

    def count(self):
        return self.peek(RAM_INFO + 4)


def sync(board, path, synced):
    """Blocks written after write number `synced` -> the file. Returns the write number the file is now at."""
    board.check()
    count = board.count()
    if count == synced:
        return synced
    seq = [board.peek(RAM_SEQ + 4 * i) for i in range(256)]
    dirty = [b for b in range(256) if seq[b] > synced]
    card = load(path) or blank()
    t = time.time()
    for b in dirty:
        words = [board.peek(RAM_VMU + b * 512 + 4 * i) for i in range(128)]
        card[b * 512:(b + 1) * 512] = struct.pack('<128I', *words)
    board.check()                                   # still the same game after all those peeks
    if board.count() < count:
        raise Gone('the game restarted')
    save(path, card)
    log('saved', path, 'blocks', dirty, 'write', count, '%.1f s' % (time.time() - t))
    return count


def state_file(ip):
    return '/var/log/dc2naomi_vmu_%s.state' % ip


def write_state(ip, path, synced):
    with open(state_file(ip), 'w') as f:
        f.write('%d\n%d\n%s\n' % (os.getpid(), synced, path))


def watch(ip, path, wait):
    write_state(ip, path, 0)
    log('watching', ip, path)
    time.sleep(wait)                                # the game is starting
    board = Board(ip)
    synced, seen, misses = 0, 0, 0
    first = True
    while True:
        try:
            board.check()
            if first:
                first = False
                if board.peek(RAM_INFO + 8) != 1:   # the game did not take the card we sent: read all of it
                    log('the game is not using the card from the image: reading the whole card')
                    card = bytearray()
                    for b in range(256):
                        card += struct.pack('<128I', *[board.peek(RAM_VMU + b * 512 + 4 * i) for i in range(128)])
                    if valid(card):
                        save(path, card)
            count = board.count()
            if count != synced and count == seen:   # nothing new since the last look: the save is over
                synced = sync(board, path, synced)
                write_state(ip, path, synced)
            seen = count
            misses = 0
        except Gone as e:
            misses += 1
            log('no answer (%d): %s' % (misses, e))
            if misses >= 6:
                log('giving up')
                break
        time.sleep(POLL)
    try:
        os.remove(state_file(ip))
    except OSError:
        pass


def stop(ip):
    try:
        with open(state_file(ip)) as f:
            pid, synced, path = f.read().split('\n')[:3]
    except (OSError, ValueError):
        return
    try:
        os.kill(int(pid), signal.SIGKILL)
    except (OSError, ValueError):
        pass
    try:
        os.remove(state_file(ip))
    except OSError:
        pass
    try:                                            # a last look: a save the watcher had not fetched yet
        if sync(Board(ip), path, int(synced)) != int(synced):
            log('last look before the next game: saved')
    except Gone as e:
        log('last look: no answer (%s)' % e)
    except Exception as e:
        log('last look failed:', e)


def main():
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'stop':
        stop(a[1])
    elif len(a) in (3, 4) and a[0] == 'watch':
        try:
            watch(a[1], a[2], float(a[3]) if len(a) == 4 else 30)
        except Exception as e:
            log('watcher died:', repr(e))
            raise
    elif len(a) == 2 and a[0] == 'blank':
        save(a[1], blank())
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
