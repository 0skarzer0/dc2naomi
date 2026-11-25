#!/usr/bin/env python3
"""med_mk64.py NETDIMM_IP ADDR [SEGUNDOS] [SALIDA.csv] [PAUSA] : las medidas de Mario Kart 64 compilado para NAOMI (el bloque
naomi_med que mk64-dc-naomi.patch mete en src/gfx/gfx_dc.c; el juego lo rellena cada 30 cuadros), leidas desde la
Raspberry por la NetDIMM mientras se juega. ADDR: la de _naomi_med (la imprime build_mk64.sh). Corre EN la Raspberry,
con el netdimm.py de DragonMinded en /sbin/piforce/dm_netboot. Sin timehack.py hablando a la vez con la NetDIMM.
Cada lectura la contesta el juego con las interrupciones cortadas: con PAUSA (s) solo lee una ventana cada PAUSA
segundos, y esa ventana se ha jugado sin lecturas.

Una linea por ventana de 30 cuadros: fps, cuadros tarde (de mas de 2 vblanks; acumulado), el peor cuadro (vblanks y
us de CPU), ms por cuadro de logica / recorrido de la lista de dibujo (incluye la espera a la GPU) / fin del cuadro,
espera a la GPU, KB de texturas subidas, histograma de vblanks por cuadro (1/2/3/4/5+), estado y circuito; retraso
al despertar tras el vblank del ritmo, ms del hilo de audio por llamada, el desglose del peor cuadro y, lo que
cuenta para el jugador, lo que se ve en pantalla: vblanks entre cambios de imagen (1/2/3/4/5+) y ms de render de la GPU.
"""
import struct
import sys
import time

sys.path.append('/sbin/piforce/dm_netboot')
from netdimm import NetDimm, PeekPokeTypeEnum as T  # noqa: E402

CAMPOS = ("marca n estado curso jug cuadros vbl tarde peor_vbl peor_us us_logica us_dibujo us_fin up_kb "
          "h1 h2 h3 h4 h5 f30 us_gpu us_lat lat_max us_aud aud_max aud_n w_cpu w_lat w_hueco w_logica w_dibujo "
          "hueco_max p1 p2 p3 p4 p5 us_render render_max cambios").split()
ESTADOS = {0: "inicio", 1: "menu", 2: "pilotos", 3: "circuitos", 4: "carrera", 5: "final", 7: "datos",
           9: "creditos"}   # include/defines.h (gGamestate)
CIRCUITOS = ("mario_raceway choco_mountain bowsers_castle banshee_boardwalk yoshi_valley frappe_snowland "
             "koopa_beach royal_raceway luigi_raceway moo_moo_farm toads_turnpike kalimari_desert sherbet_land "
             "rainbow_road wario_stadium block_fort skyscraper double_deck dk_jungle big_donut").split()


def main():
    ip, base = sys.argv[1], int(sys.argv[2], 0)
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else 60
    out = open(sys.argv[4], "a") if len(sys.argv) > 4 else None
    pausa = float(sys.argv[5]) if len(sys.argv) > 5 else 0   # >0: leer solo cada PAUSA s (ventanas sin lecturas)
    d = NetDimm(ip)
    d.poke(0x01fffffc, T.TYPE_LONG, 0)          # ventana = RAM
    pk = lambda i: d.peek((base + 4 * i) & 0x01ffffff, T.TYPE_LONG)
    t0 = time.time(); ult = None
    if out and out.tell() == 0:
        out.write("t," + ",".join(CAMPOS[1:]) + "\n")
    while time.time() - t0 < dur:
        try:
            if pausa:
                time.sleep(pausa)
            n = pk(1)
            if n == ult:
                time.sleep(0.3)
                continue
            v = [pk(i) for i in range(len(CAMPOS))]
        except Exception as e:  # noqa: BLE001
            print("sin respuesta (%s)" % type(e).__name__, flush=True); time.sleep(2); continue
        if v[0] != 0x34364b4d:
            print("no es el bloque de medidas (%08x)" % v[0], flush=True); time.sleep(2); continue
        ult = v[1]
        r = dict(zip(CAMPOS, v))
        cur = struct.unpack("<h", struct.pack("<H", r["curso"] & 0xffff))[0]
        fps = 60.0 * r["cuadros"] / r["vbl"] if r["vbl"] else 0
        print("t+%5.0f n=%d %s %s %dj fps=%.1f tarde=%d peor=%dv/%.1fms | logica %.1f dibujo %.1f (gpu %.1f) fin %.1f ms"
              " | tex %d KB | v/cuadro %d/%d/%d/%d/%d | despertar %.1f (max %.1f) audio %.1f (max %.1f, %d)"
              " | peor: cpu %.1f desp %.1f hueco %.1f logica %.1f dibujo %.1f"
              " || PANTALLA v/imagen %d/%d/%d/%d/%d render %.1f (max %.1f)" %
              (time.time() - t0, r["n"], ESTADOS.get(r["estado"], r["estado"]),
               CIRCUITOS[cur] if 0 <= cur < len(CIRCUITOS) else cur, r["jug"], fps, r["tarde"], r["peor_vbl"],
               r["peor_us"] / 1000, r["us_logica"] / 1000, r["us_dibujo"] / 1000, r["us_gpu"] / 1000,
               r["us_fin"] / 1000, r["up_kb"], r["h1"], r["h2"], r["h3"], r["h4"], r["h5"],
               r["us_lat"] / 1000, r["lat_max"] / 1000, r["us_aud"] / 1000, r["aud_max"] / 1000, r["aud_n"],
               r["w_cpu"] / 1000, r["w_lat"] / 1000, r["w_hueco"] / 1000, r["w_logica"] / 1000,
               r["w_dibujo"] / 1000, r["p1"], r["p2"], r["p3"], r["p4"], r["p5"], r["us_render"] / 1000,
               r["render_max"] / 1000), flush=True)
        if out:
            out.write("%.0f," % (time.time() - t0) + ",".join(str(r[k]) for k in CAMPOS[1:]) + "\n"); out.flush()


if __name__ == "__main__":
    main()
