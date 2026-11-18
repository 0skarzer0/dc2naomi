#!/usr/bin/env python3
"""reflejo.py DATOS/ SALIDA.DAT [--zonas=BEAC,LASV] [--png=CARPETA] : las panoramicas del reflejo de la carroceria de
OutRun C2C para NAOMI (REFLEJO.DAT; demo/main.c coche_reflejo con -DREFLEJO_CIELO=1).

El PC refleja en el coche un cubo que dibuja cada cuadro con modelos del escenario (cs_ENV_<zona>,
race_env_model_44cd30); la CPU de la NAOMI no da para eso. Aqui, sin coste en la placa: una vista de 360 grados de cada
zona (cielo, palmeras, edificios, carteles...) desde la carretera, dibujada al convertir con la geometria y las texturas
ya convertidas de su etapa (SEGnn.DAT, sueltas o en SEGS.PAK, y CURSO.DAT / CURSOTA.DAT para saber la etapa de cada
zona). La demo la pone en la carroceria girada con el rumbo de la camara y corriendo con la distancia recorrida.

Panoramica: W x H texeles (256 x 64), u = acimut (atan2(x, z), una vuelta), v = elevacion de -20 (v = 0, primera fila)
a +70 grados (v = 1). Ojo a 1 m sobre la ruta, en el primero de PUNTOS (fracciones de su longitud: 0,3, 0,55, 0,8, 0,15) con el cielo libre por
encima de +10 grados entre el 45 y el 75 % (o el mas cercano al 60 %: ni dentro de un tunel ni en medio de la nada); se dibuja lo que esta entre 3 y 700 m
(el suelo bajo el coche no). Rasterizado por software con supermuestreo 4x4: textura x color del vertice (la luz ya va
cocida en los vertices de la etapa), alfa recortado en la lista perforada y mezclado en la transparente (de lejos a
cerca), el cielo de la lista 3 detras de todo (en su direccion, sin distancia). Sin niebla.

REFLEJO.DAT: 'REF1', n, W, H; n entradas {zona (4 bytes), desplazamiento, tamano, formato}; los datos alineados a 32:
VQ de la PowerVR (libro de 256 entradas RGB565 y los indices, twiddled; tools/vq.py de ORC2CDC), formato 0x101.

Necesita las herramientas de ORC2CDC (tools/ de su repositorio: pvs.py, pak_union.py, vq.py, modelo.py) en
ORC2CDC_TOOLS o en ../orc2/tools. Sale de tus datos: no se distribuye."""
import os, struct, sys, math
import numpy as np

T = os.environ.get('ORC2CDC_TOOLS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../orc-build/orc2/tools'))
sys.path.insert(0, T)
import pvs, pak_union, vq  # noqa: E402

W, H, SS = 256, 64, 4
EL0, EL1 = -20.0, 70.0
PUNTO = float(os.environ.get('PUNTO', '0.3'))
PUNTOS = (PUNTO, 0.55, 0.8, 0.15)
CERCA, LEJOS = 3.0, 700.0
TEX = np.dtype([('w', '<u4'), ('h', '<u4'), ('fmt', '<u4'), ('lista', '<u4'), ('off', '<u4'), ('tam', '<u4')])


def bloque_texeles(b):
    h = struct.unpack_from('<13I', b, 4)
    nmallas, nvert, nruta, paso, ntex = h[:5]; nnodos, ncart, nsec = h[10], h[11], h[12] & 0x7FFFFFFF
    p = 56 + 24 * ntex + 32 * nmallas + 24 * nvert + nruta * paso * 4 + 32 * nnodos + 64 * ncart
    if nsec:
        ini = struct.unpack_from('<%dI' % (nsec + 1), b, p); p += (nsec + 1) * 4
        if h[12] >> 31: p += ini[nsec]; p = (p + 1) & ~1
        else: p += ini[nsec] * 2
        p += nruta * 2
    p = (p + 3) & ~3
    return (p + 31) & ~31


def textura(b, p0, t):
    """RGBA (alto x ancho x 4) del nivel base de la textura t"""
    w, h, fmt, lista, off, tam = (int(x) for x in t)
    d = b[p0 + off:p0 + off + tam]; fb = fmt & 0xff
    if fb > 2: return None
    mip = (fmt & 0x200) and w == h
    if fmt & 0x100:
        n = ((fmt >> 16) & 0xff) + 1; libro = d[:8 * n]; idx = d[8 * n:]
        if mip:                                        # niveles de 1x1 a la base: 1, 1, 4, 16... bytes de indices
            o, s = 0, 1
            while s < w: o += max(1, (s // 2) ** 2); s *= 2
            idx = idx[o:]
        return vq.decodifica(libro + idx, w, h, fb, n)
    if mip:
        o, s = 6, 1
        while s < w: o += s * s * 2; s *= 2
        d = d[o:]
    return vq.decodifica16(d, w, h, fb)


def mallas_tri(d):
    """(lista, textura, 3 indices de vertice) de cada triangulo de las tiras"""
    M = d['M']; h = d['h']; ini = list(h[5:10]) + [len(M)]
    out = []
    for k in range(len(M)):
        m = M[k]; n = int(m['n']); v0 = int(m['v0'])
        if n < 3: continue
        l = next(i for i in range(4, -1, -1) if k >= ini[i]) if ini[4] else next(i for i in range(3, -1, -1) if k >= ini[i])
        i = np.arange(n - 2) + v0
        out.append((l, int(m['t']), np.stack([i, i + 1, i + 2], 1)))
    return out


class Lienzo:
    def __init__(s):
        s.w, s.h = W * SS, H * SS
        s.rgb = np.zeros((s.h, s.w, 3), np.float32); s.z = np.full((s.h, s.w), np.inf, np.float32)

    def tri(s, P, UV, C, tex, modo, d):
        """P: 3 x (x, y) en pixeles del lienzo, UV 3 x 2, C 3 x 4 (0..1), d 3 distancias; modo 0 opaco, 1 recorte,
        2 mezcla, 3 cielo (sin z)"""
        x0 = int(max(0, math.floor(P[:, 0].min()))); x1 = int(min(s.w - 1, math.ceil(P[:, 0].max())))
        y0 = int(max(0, math.floor(P[:, 1].min()))); y1 = int(min(s.h - 1, math.ceil(P[:, 1].max())))
        if x0 > x1 or y0 > y1: return
        (ax, ay), (bx, by), (cx, cy) = P
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9: return
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        l0 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den
        l1 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den
        l2 = 1 - l0 - l1
        m = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
        if not m.any(): return
        z = l0 * d[0] + l1 * d[1] + l2 * d[2]
        zs = s.z[y0:y1 + 1, x0:x1 + 1]
        if modo != 3: m &= z < zs
        if not m.any(): return
        col = l0[..., None] * C[0] + l1[..., None] * C[1] + l2[..., None] * C[2]
        if tex is not None:
            th, tw = tex.shape[:2]
            u = l0 * UV[0, 0] + l1 * UV[1, 0] + l2 * UV[2, 0]; v = l0 * UV[0, 1] + l1 * UV[1, 1] + l2 * UV[2, 1]
            tu = (np.floor(u * tw).astype(np.int64) % tw); tv = (np.floor(v * th).astype(np.int64) % th)
            tx = tex[tv, tu] / 255.0
            col = col * tx
        a = col[..., 3]
        if modo == 1: m &= a >= 0.5
        if not m.any(): return
        dst = s.rgb[y0:y1 + 1, x0:x1 + 1]
        if modo == 2:
            dst[m] = dst[m] * (1 - a[m, None]) + col[m, :3] * a[m, None]
        else:
            dst[m] = col[m, :3]
        if modo in (0, 1): zs[m] = z[m]

    def imagen(s):
        a = s.rgb.reshape(H, SS, W, SS, 3).mean((1, 3))
        return np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)


def proyecta(D):
    """direcciones (n x 3) -> pixeles del lienzo (n x 2) y distancias"""
    d = np.linalg.norm(D, axis=1)
    az = np.arctan2(D[:, 0], D[:, 2]); el = np.degrees(np.arcsin(np.clip(D[:, 1] / np.maximum(d, 1e-6), -1, 1)))
    x = (az / (2 * np.pi) % 1.0) * W * SS; y = (el - EL0) / (EL1 - EL0) * H * SS
    return np.stack([x, y], 1), d


def dibuja(lz, D, UV, C, tex, modo, prof=0):
    """un triangulo (direcciones desde el ojo D 3x3): se parte si abarca mucho angulo (la proyeccion no es lineal)"""
    P, d = proyecta(D)
    if modo != 3 and (d.min() < CERCA or d.min() > LEJOS): return
    ang = max(np.degrees(np.arccos(np.clip(np.dot(D[i] / d[i], D[j] / d[j]), -1, 1))) for i, j in ((0, 1), (1, 2), (0, 2)))
    if ang > 4.0 and prof < 6:
        m = [(0, 1), (1, 2), (2, 0)]
        Dm = np.array([(D[i] + D[j]) / 2 for i, j in m]); UVm = np.array([(UV[i] + UV[j]) / 2 for i, j in m]); Cm = np.array([(C[i] + C[j]) / 2 for i, j in m])
        for t in ((0, 3, 5), (3, 1, 4), (5, 4, 2), (3, 4, 5)):
            DD = np.concatenate([D, Dm])[list(t)]; UU = np.concatenate([UV, UVm])[list(t)]; CC = np.concatenate([C, Cm])[list(t)]
            dibuja(lz, DD, UU, CC, tex, modo, prof + 1)
        return
    if P[:, 0].max() - P[:, 0].min() > W * SS / 2:      # cruza la costura del acimut: por los dos lados
        Q = P.copy(); Q[Q[:, 0] < W * SS / 2, 0] += W * SS
        lz.tri(Q, UV, C, tex, modo, d); Q[:, 0] -= W * SS; lz.tri(Q, UV, C, tex, modo, d)
    else:
        lz.tri(P, UV, C, tex, modo, d)


def panoramica(b, punto=PUNTO):
    d = pvs.lee_bytes(b) if hasattr(pvs, 'lee_bytes') else None
    if d is None:
        tmp = '/dev/shm/refl_%d.ord' % os.getpid(); open(tmp, 'wb').write(b)
        try: d = pvs.lee(tmp)
        finally: os.remove(tmp)
    V = d['V']; R = d['R']
    Tt = np.frombuffer(d['texs'], TEX); p0 = bloque_texeles(b)
    texs = {}
    k = int(len(R) * punto); ojo = R[k, :3].astype(np.float64) + np.array([0, 1.0, 0])
    pos = np.stack([V['x'], V['y'], V['z']], 1).astype(np.float64)
    uv = np.stack([V['u'], V['v']], 1).astype(np.float64)
    c = V['c'].astype(np.uint64)
    col = np.stack([(c >> 16) & 255, (c >> 8) & 255, c & 255, c >> 24], 1).astype(np.float64) / 255.0
    lz = Lienzo()
    tris = mallas_tri(d)
    # el cielo (lista 3) primero, en su direccion
    for l, t, I in tris:
        if l != 3: continue
        tx = None
        if t >= 0:
            if t not in texs: texs[t] = textura(b, p0, Tt[t])
            tx = texs[t]
        for tri in I:
            D = pos[tri]
            if np.linalg.norm(D, axis=1).min() < 1: continue
            dibuja(lz, D, uv[tri], col[tri], tx, 3)
    # opaco y recortado; luego lo transparente de lejos a cerca
    trans = []
    for l, t, I in tris:
        if l == 3: continue
        D0 = pos[I] - ojo; dist = np.linalg.norm(D0, axis=2).min(1)
        sel = (dist >= CERCA) & (dist <= LEJOS)
        if not sel.any(): continue
        tx = None
        if t >= 0:
            if t not in texs: texs[t] = textura(b, p0, Tt[t])
            tx = texs[t]
        for q in np.nonzero(sel)[0]:
            if l == 2: trans.append((dist[q], D0[q], uv[I[q]], col[I[q]], tx)); continue
            dibuja(lz, D0[q], uv[I[q]], col[I[q]], tx, 1 if l == 1 else 0)
    for _, D, U, C, tx in sorted(trans, key=lambda x: -x[0]):
        dibuja(lz, D, U, C, tx, 2)
    alto = int((10.0 - EL0) / (EL1 - EL0) * lz.h)              # cielo libre por encima de +10 grados
    return lz.imagen(), float(np.isinf(lz.z[alto:]).mean())


def zonas_seg(datos):
    import re
    b = b''
    for f in ('CURSO.DAT', 'CURSOTA.DAT'):
        if os.path.exists(os.path.join(datos, f)): b += open(os.path.join(datos, f), 'rb').read()
    z = {}
    for x in re.finditer(rb'[A-Z]{4}', b):
        s = b[x.end()]
        if s < 64 and b[x.end() + 1] < 5: z.setdefault(x.group().decode(), set()).add(s)
    return {k: sorted(v) for k, v in z.items()}


def etapa(datos, n, pak):
    f = os.path.join(datos, 'SEG%02d.DAT' % n)
    if not os.path.exists(f): return None
    b = open(f, 'rb').read()
    if b[:4] != b'ORD7':
        if pak is None: return None
        b = pak_union.recompone(b, pak)
    return b


def main():
    datos, sal = sys.argv[1], sys.argv[2]
    opt = dict(a[2:].split('=', 1) for a in sys.argv[3:] if a.startswith('--') and '=' in a)
    pakf = os.path.join(datos, 'SEGS.PAK'); pak = open(pakf, 'rb').read() if os.path.exists(pakf) else None
    Z = zonas_seg(datos)
    quiero = opt['zonas'].split(',') if 'zonas' in opt else sorted(Z)
    ent = []
    for z in quiero:
        b = None
        for n in Z.get(z, []):
            b = etapa(datos, n, pak)
            if b: break
        if not b: print('%s: sin etapa' % z); continue
        mejor = None
        for pt in PUNTOS:                                   # el punto con mas mezcla de cielo y escenario
            img_, cielo = panoramica(b, pt)
            if mejor is None or abs(cielo - 0.6) < abs(mejor[1] - 0.6): mejor = (img_, cielo, pt)
            if abs(cielo - 0.6) < 0.15: break
        img = mejor[0]; print('%s: punto %.2f, cielo libre %.0f %%' % (z, mejor[2], 100 * mejor[1]), flush=True)
        if 'png' in opt:
            from PIL import Image
            os.makedirs(opt['png'], exist_ok=True); Image.fromarray(img[::-1]).save(os.path.join(opt['png'], z + '.png'))
        dat, err = vq.codifica(np.concatenate([img, np.full(img.shape[:2] + (1,), 255, np.uint8)], 2), 1)
        print('%s: SEG%02d, %d bytes, error VQ %.1f' % (z, n, len(dat), err), flush=True)
        ent.append((z, dat))
    cab = b'REF1' + struct.pack('<3I', len(ent), W, H); o = len(cab) + 16 * len(ent); o += -o % 32
    cuerpo = b''; tabla = b''
    for z, dat in ent:
        tabla += z.encode() + struct.pack('<3I', o + len(cuerpo), len(dat), 0x101)
        cuerpo += dat + b'\0' * (-len(dat) % 32)
    pre = cab + tabla; pre += b'\0' * (-len(pre) % 32)
    open(sal, 'wb').write(pre + cuerpo)
    print('%s: %d zonas, %d bytes' % (sal, len(ent), len(pre) + len(cuerpo)))


if __name__ == '__main__':
    main()
