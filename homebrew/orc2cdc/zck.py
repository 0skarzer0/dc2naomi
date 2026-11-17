#!/usr/bin/env python3
"""zck.py ENTRADA SALIDA : un fichero del disco de ORC2CDC en formato ZCK1, el que lee comun/gd.c con GD_ZCK (el
parche de este directorio): trozos de 64 KB comprimidos cada uno por separado con zlib (nivel 9), para que el juego
pueda leer cualquier sector sin descomprimir el fichero entero (SEGS.PAK y UNIONES.PAK se leen a ventanas).

    "ZCK1", tamano original, 65536, n trozos, n + 1 desplazamientos (u32 LE, desde el principio del fichero),
    relleno hasta 2048 bytes, los trozos seguidos. Un trozo que no gana se guarda tal cual.

Sale de tus datos: no se distribuye."""
import struct
import sys
import zlib

TROZO = 65536


def comprime(datos):
    n = (len(datos) + TROZO - 1) // TROZO
    cab = 16 + 4 * (n + 1)
    cab += -cab % 2048
    cuerpos, off, p = [], [], cab
    for i in range(n):
        t = datos[i * TROZO:(i + 1) * TROZO]
        z = zlib.compress(t, 9)
        if len(z) >= len(t):
            z = t
        off.append(p)
        cuerpos.append(z)
        p += len(z)
    off.append(p)
    h = b"ZCK1" + struct.pack("<3I", len(datos), TROZO, n) + struct.pack("<%dI" % (n + 1), *off)
    return h + bytes(cab - len(h)) + b"".join(cuerpos)


def descomprime(z):
    """la comprobacion: lo que lee gd.c"""
    assert z[:4] == b"ZCK1"
    tam, tr, n = struct.unpack_from("<3I", z, 4)
    off = struct.unpack_from("<%dI" % (n + 1), z, 16)
    out = []
    for i in range(n):
        ul = tr if i + 1 < n or tam % tr == 0 else tam % tr
        c = z[off[i]:off[i + 1]]
        out.append(c if len(c) == ul else zlib.decompress(c))
    return b"".join(out)


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    z = comprime(d)
    assert descomprime(z) == d
    open(sys.argv[2], "wb").write(z)
    print(f"{sys.argv[1]}: {len(d)} -> {len(z)} ({100 * len(z) / max(len(d), 1):.0f} %)")
