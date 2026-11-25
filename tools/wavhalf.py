#!/usr/bin/env python3
"""wavhalf.py IN.WAV OUT.WAV [--mono] : a 16-bit PCM WAV at half its sample rate (and optionally in mono), so that a
game that streams WAV files reading their header (Sega Rally 2: MISC/*.WAV at 44.1 kHz stereo next to BGM/*.WAV at
22.05 kHz mono, same player) still plays it while the disc fits in the 512 MB NetDIMM. The new file is about half the
size (a quarter with --mono) and keeps its length in time. Low-pass FIR (windowed sinc, cut at 0.45 of the new rate)
before dropping every other sample. Needs numpy.

Then put the new files at their disc paths in a folder and build with it (tools/withfiles.py; with a profile of
tools/games.py: WITHFILES=FOLDER ./build.sh PROFILE DISC.gdi OUT.bin).
"""
import struct
import sys

import numpy as np


def read_wav(path):
    d = open(path, "rb").read()
    assert d[:4] == b"RIFF" and d[8:12] == b"WAVE", f"{path}: not a WAV"
    i, fmt, data = 12, None, None
    while i + 8 <= len(d):
        cid, n = d[i:i + 4], struct.unpack_from("<I", d, i + 4)[0]
        if cid == b"fmt ":
            fmt = struct.unpack_from("<HHIIHH", d, i + 8)
        elif cid == b"data":
            data = d[i + 8:i + 8 + n]
        i += 8 + n + (n & 1)
    tag, ch, rate, _bps, _align, bits = fmt
    assert tag == 1 and bits == 16, f"{path}: only 16-bit PCM"
    s = np.frombuffer(data[:len(data) // (2 * ch) * 2 * ch], dtype="<i2").reshape(-1, ch).astype(np.float64)
    return rate, s


def half(s, taps=95):
    n = np.arange(taps) - (taps - 1) / 2
    fc = 0.45 / 2                                    # of the old rate: 0.45 x the new Nyquist
    h = 2 * fc * np.sinc(2 * fc * n) * np.blackman(taps)
    h /= h.sum()
    out = np.stack([np.convolve(s[:, c], h, mode="same") for c in range(s.shape[1])], axis=1)
    return out[::2]


def write_wav(path, rate, s):
    ch = s.shape[1]
    pcm = np.clip(np.round(s), -32768, 32767).astype("<i2").tobytes()
    hdr = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
    hdr += b"fmt " + struct.pack("<IHHIIHH", 16, 1, ch, rate, rate * ch * 2, ch * 2, 16)
    hdr += b"data" + struct.pack("<I", len(pcm))
    open(path, "wb").write(hdr + pcm)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    rate, s = read_wav(args[0])
    s = half(s)
    if "--mono" in sys.argv:
        s = s.mean(axis=1, keepdims=True)
    write_wav(args[1], rate // 2, s)
    print(f"{args[0]}: {rate} Hz -> {rate // 2} Hz, {s.shape[1]} channel(s), {len(s) / (rate // 2):.1f} s")


if __name__ == "__main__":
    main()
