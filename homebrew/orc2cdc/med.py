#!/usr/bin/env python3
"""med.py NETDIMM_IP ADDR [SEGUNDOS] [SALIDA.csv] : las medidas de OutRun C2C compilado para NAOMI (el bloque naomi_med
de demo/main.c, que el juego rellena cada 30 cuadros), leidas desde la Raspberry por la NetDIMM mientras se juega o
mientras corre la demo. ADDR: la de _naomi_med (sh-elf-nm demo.elf). Corre EN la Raspberry (WiPi), con el netdimm.py
de DragonMinded en /sbin/piforce/dm_netboot. Una linea por cada ventana nueva de 30 cuadros:

  fps, ms de CPU (dibujo / logica), distancia de dibujo, vertices, TA usado, cuadros tarde (acumulado), el peor
  cuadro de la ventana (campos de vblank entre presentaciones y us de CPU), estado (0 titulo/demo, 2 carrera...)
  y la zona.
"""
import struct
import sys
import time

sys.path.append('/sbin/piforce/dm_netboot')
from netdimm import NetDimm, PeekPokeTypeEnum as T  # noqa: E402

PARTES = "ini vis cielo etapa bo coche robot traf l2 fin".split()   # con -DNAOMI_PRF (si no, ceros)
CAMPOS = ("marca n estado nodo fps ms ms_log lejos vtx tri ta_real ta_opb tarde peor_campos peor_us gd_us vbl zona".split()
          + ["us_" + p for p in PARTES] + ["v_" + p for p in PARTES])
FLOAT = {"fps", "ms", "ms_log", "lejos"}


def main():
    ip, base = sys.argv[1], int(sys.argv[2], 0)
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else 60
    out = open(sys.argv[4], "a") if len(sys.argv) > 4 else None
    d = NetDimm(ip)
    d.poke(0x01fffffc, T.TYPE_LONG, 0)          # ventana = RAM
    pk = lambda i: d.peek((base + 4 * i) & 0x01ffffff, T.TYPE_LONG)
    t0 = time.time(); ult = None
    if out and out.tell() == 0:
        out.write("t," + ",".join(CAMPOS[1:]) + "\n")
    while time.time() - t0 < dur:
        try:
            n = pk(1)
            if n == ult:
                time.sleep(0.3)
                continue
            v = [pk(i) for i in range(len(CAMPOS))]
        except Exception as e:  # noqa: BLE001
            print("sin respuesta (%s)" % type(e).__name__, flush=True); time.sleep(2); continue
        if v[0] != 0x4944454d:
            print("no es el bloque de medidas (%08x)" % v[0], flush=True); time.sleep(2); continue
        ult = v[1]
        r = {}
        for k, x in zip(CAMPOS, v):
            r[k] = struct.unpack("<f", struct.pack("<I", x))[0] if k in FLOAT else x
        r["zona"] = struct.pack("<I", r["zona"]).decode("ascii", "replace").strip("\0")
        lin = ("t+%5.0f n=%d est=%d %s fps=%.1f cpu=%.1f+%.1f ms lejos=%.0f vtx=%d ta=%dK tarde=%d peor=%dc/%dus" %
               (time.time() - t0, r["n"], r["estado"], r["zona"], r["fps"], r["ms"], r["ms_log"], r["lejos"], r["vtx"],
                r["ta_real"] >> 10, r["tarde"], r["peor_campos"], r["peor_us"]))
        if any(r["us_" + p] for p in PARTES):
            lin += " | " + " ".join("%s %d/%d" % (p, r["us_" + p], r["v_" + p]) for p in PARTES)
        print(lin, flush=True)
        if out:
            out.write("%.0f," % (time.time() - t0) + ",".join(str(r[k]) for k in CAMPOS[1:]) + "\n"); out.flush()
        # el peor de la ventana se pone a cero aqui (el juego solo lo sube)
        d.poke((base + 4 * CAMPOS.index("peor_campos")) & 0x01ffffff, T.TYPE_LONG, 0)
        d.poke((base + 4 * CAMPOS.index("peor_us")) & 0x01ffffff, T.TYPE_LONG, 0)


if __name__ == "__main__":
    main()
