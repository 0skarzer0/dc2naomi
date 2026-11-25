#!/usr/bin/env python3
"""traza_mk64.py NETDIMM_IP ADDR [FOTOS] : lee las fotos de naomi_traza (imagenes fuera de ritmo en carrera; las hace
el juego compilado con la traza, ver docs/juegos/mario-kart-64.md) desde la Raspberry y las imprime alineadas: por
cada cuadro, el vblank y los ms (desde ese vblank) en que empezo, acabo la CPU y se mando a la GPU; por cada cambio de
imagen, cuantos vblanks duro la anterior y cuando empezaron y cuanto duraron el registro y el render de la GPU.
Leer con el juego parado en un menu o al final: cada lectura corta las interrupciones del juego."""
import sys

sys.path.append('/sbin/piforce/dm_netboot')
from netdimm import NetDimm, PeekPokeTypeEnum as T  # noqa: E402

N = 16


def rel(a, b):
    """ms de b a a (tiempos de 32 bits en us)"""
    return (((a - b + (1 << 31)) & 0xffffffff) - (1 << 31)) / 1000.0
FOTO = 2 + N * 4 + N * 7


def main():
    ip, base = sys.argv[1], int(sys.argv[2], 0)
    d = NetDimm(ip)
    d.poke(0x01fffffc, T.TYPE_LONG, 0)
    pk = lambda i: d.peek((base + 4 * i) & 0x01ffffff, T.TYPE_LONG)
    if pk(0) != 0x5a415254:
        sys.exit("no es naomi_traza")
    hechas, vistas = pk(1), pk(2)
    print("fotos %d, imagenes fuera de ritmo en carrera %d" % (hechas, vistas))
    for k in range(min(hechas, int(sys.argv[3]) if len(sys.argv) > 3 else 8)):
        w = [pk(4 + k * FOTO + i) for i in range(FOTO)]
        fin = [w[2 + i * 4: 6 + i * 4] for i in range(N)]
        flip = [w[2 + N * 4 + i * 7: 9 + N * 4 + i * 7] for i in range(N)]
        vbl_t = {f[0]: f[1] for f in flip}          # vblank -> su tiempo (los que tienen cambio de imagen)
        v0 = min(f[0] for f in fin + flip if f[0])
        print("\n== foto %d (cuadros %d, cambios %d); vblanks contados desde %d" % (k, w[0], w[1], v0))
        ev = []
        for f in fin:
            if f[0]:
                ev.append((f[3], "  cuadro  mandado en v%-4d  cpu %5.1f ms  espera %5.1f ms" %
                           (f[0] - v0, (f[2] - f[1]) / 1000.0, ((f[3] - f[2]) & 0xffffffff) / 1000.0)))
        prev = None
        for f in flip:
            if f[0]:
                dur = f[0] - prev if prev is not None else 0
                prev = f[0]
                ev.append((f[1], "IMAGEN en v%-4d (la anterior duro %d)  registro %+6.1f ms (%4.1f)  render %+6.1f ms "
                           "(%4.1f) busy %d" % (f[0] - v0, dur, rel(f[2], f[1]), f[3] / 1000.0, rel(f[4], f[1]),
                                                f[5] / 1000.0, f[6])))
        t0 = min(e[0] for e in ev)
        for t, s in sorted(ev, key=lambda e: (e[0] - t0) & 0xffffffff):
            print("%8.1f ms  %s" % (((t - t0) & 0xffffffff) / 1000.0, s))


if __name__ == "__main__":
    main()
