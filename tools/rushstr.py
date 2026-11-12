#!/usr/bin/env python3
"""rushstr.py IN.STR OUT.STR : San Francisco Rush 2049's music streams (*.STR, 18 songs, 905 MB) made mono, half the
size, so that the game fits in the NetDIMM.

The format (seen on the USA disc; every file has the same parameters): a 2048-byte header of little-endian words
    0 version (1), 1 sample rate (44100), 2 bits (16), 3 bytes per channel block (16384), 4 blocks, 5 bytes of data,
    6 channels (2), 7 blocks again, zeros
then the blocks from byte 2048: raw 16-bit PCM, one block of 16384 bytes per channel in turn (left, right, left...).
Mono: each pair of blocks averaged into one, channels = 1, data bytes halved; the block size and count stay. Whether
the game reads the channel count from the header (and not a fixed "stereo") is NOT known: test it on the board; if
the music sounds wrong, use the version that shares songs instead (HANDOFF, "Rush 2049").
"""
import struct
import sys

import numpy as np


def main(src, dst):
    b = open(src, "rb").read()
    h = list(struct.unpack_from("<8I", b, 0))
    ver, rate, bits, blk, nblk, nbytes, ch = h[:7]
    assert (ver, bits, ch) == (1, 16, 2), f"formato inesperado {h}"
    body = np.frombuffer(b, dtype="<i2", offset=2048, count=(len(b) - 2048) // 2)
    per = blk // 2                                   # samples per channel block
    n = len(body) // (2 * per)
    pairs = body[:n * 2 * per].reshape(n, 2, per).astype(np.int32)
    mono = ((pairs[:, 0] + pairs[:, 1]) // 2).astype("<i2").reshape(-1)
    hd = bytearray(b[:2048])
    struct.pack_into("<I", hd, 20, nbytes // 2)
    struct.pack_into("<I", hd, 24, 1)
    out = bytes(hd) + mono.tobytes()
    out += bytes(-len(out) % 2048)
    open(dst, "wb").write(out)
    print(f"{src}: {nblk} bloques, {len(b) / 1048576:.1f} -> {len(out) / 1048576:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
