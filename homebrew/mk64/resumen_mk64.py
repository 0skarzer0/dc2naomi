#!/usr/bin/env python3
"""resumen_mk64.py MEDIDA.csv [...] : resume lo que med_mk64.py guardo, por tramo (estado, circuito, jugadores) en el
orden en que salieron. Por tramo: ventanas, fps del juego, cuadros de mas de 2 vblanks; lo que se ve en pantalla
(imagenes de 1 / 2 / 3+ vblanks: con el juego a 30 fps, lo bueno es que todas duren 2) y medias de logica, dibujo,
render de la GPU y retraso al despertar. Las ventanas con un cuadro de mas de 10 vblanks (cargas) se cuentan aparte."""
import csv
import sys

ESTADOS = {"0": "inicio", "1": "menu", "2": "pilotos", "3": "circuitos", "4": "carrera", "5": "final",
           "7": "datos", "9": "creditos"}
CIRCUITOS = ("mario_raceway choco_mountain bowsers_castle banshee_boardwalk yoshi_valley frappe_snowland "
             "koopa_beach royal_raceway luigi_raceway moo_moo_farm toads_turnpike kalimari_desert sherbet_land "
             "rainbow_road wario_stadium block_fort skyscraper double_deck dk_jungle big_donut").split()


def main():
    for path in sys.argv[1:]:
        rows = list(csv.DictReader(open(path)))
        print("== %s: %d ventanas de 30 cuadros" % (path, len(rows)))
        tramos = []
        for r in rows:
            c = int(r["curso"]) & 0xffff
            k = (ESTADOS.get(r["estado"], r["estado"]), CIRCUITOS[c] if c < len(CIRCUITOS) else str(c), r["jug"])
            if not tramos or tramos[-1][0] != k:
                tramos.append((k, []))
            tramos[-1][1].append(r)
        tot = {}
        for k, rs in tramos:
            cargas = [r for r in rs if int(r["peor_vbl"]) > 10]
            rs = [r for r in rs if 0 < int(r["peor_vbl"]) <= 10]
            if not rs:
                continue
            S = lambda f: sum(int(r.get(f) or 0) for r in rs)
            n = len(rs)
            p = [S("p1"), S("p2"), S("p3") + S("p4") + S("p5")]
            pt = sum(p) or 1
            print("%-8s %-17s %sj %3d v  fps %5.2f  tarde %3d | pantalla 1v %3d  2v %4d  3v+ %3d (%4.1f %% mal) |"
                  " logica %4.1f dibujo %4.1f render %4.1f (max %4.1f) despertar %3.1f ms%s" %
                  (k[0], k[1], k[2], n, 60.0 * S("cuadros") / S("vbl"), S("h3") + S("h4") + S("h5"), p[0], p[1],
                   p[2], 100.0 * (p[0] + p[2]) / pt, S("us_logica") / n / 1000, S("us_dibujo") / n / 1000,
                   S("us_render") / n / 1000, max(int(r.get("render_max") or 0) for r in rs) / 1000,
                   S("us_lat") / n / 1000, "  (+%d con carga)" % len(cargas) if cargas else ""))
            if k[0] == "carrera":
                for i, f in enumerate(p):
                    tot[i] = tot.get(i, 0) + f
        if tot:
            t = sum(tot.values()) or 1
            print("carreras: pantalla 1v %d  2v %d  3v+ %d -> %.1f %% de imagenes fuera de ritmo" %
                  (tot[0], tot[1], tot[2], 100.0 * (tot[0] + tot[2]) / t))


if __name__ == "__main__":
    main()
