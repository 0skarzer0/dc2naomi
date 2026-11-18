# Medidas en la placa (NAOMI 2 del mueble Crazy Taxi), OutRun C2C compilado para NAOMI

Con `med.py` desde la Raspberry .60 mientras corre la **demo automática** (estado 2 = carrera), una ventana por cada 30
cuadros. "cpu" = ms de CPU por cuadro (dibujo + lógica, la misma medida con la que el juego acorta la distancia de
dibujo); "lejos" = distancia de dibujo en m (la del original llega a 4000; el juego la baja 50 m por segundo si la CPU
pasa del tope y la sube si baja del otro); "peor" = el cuadro más largo de la ventana.

Todas con la compilación de ArkRetro `a689a9a` + parche NAOMI (32 MB, sin vídeos / OutRunners / taxi, 8 canciones
largas a 22 kHz), mismos datos (`datos3`).

| Variante | Qué cambia | fps medio (mín) | ventanas < 28 fps | cpu medio (máx) | lejos mediana (mín) | peor cuadro |
|---|---|---|---|---|---|---|
| base | como ArkRetro: tope 45 fps, recorte de distancia a 21 / 17 ms | 32,4 (17,1) | 13 % | 30,5 (58,6) | 2084 (600) | 99 ms |
| B | **tope 30 fps** (`FPS_OBJETIVO=30`), recorte a 29 / 25 ms | 29,0 (17,5) | 14 % | 30,9 (57,0) | 2749 (1350) | 124 ms |
| E | D + `-ffast-math -ffp-contract=fast` | 17,1 (6,3) | 60 % | 86,9 (159) | — | 103 ms |
| D | B + **lecturas del disco en trozos de 4 sectores** (`GD_TROZO=4`, `comun/gd.c`) | 29,2 (20,6) | 14 % | 30,8 (48,5) | 2728 (1200) | 57 ms |
| F | D + **lectura de la NetDIMM por DMA del G1** (perfil `orc3dma`, `DIMM_DMA` en el residente) | 29,6 (20,1) | 7 % | 29,6 (49,8) | 2827 (1600) | 47 ms |
| G | F con el recorte a 27 / 23 ms | 29,6 (20,7) | 5 % | 29,4 (48,2) | 2563 (900) | 44 ms |
| **R** | **= F, la que queda en la Pi** (`h-orc2c3`, 172 ventanas) | **29,7 (23,7)** | **5 %** | 29,2 (42,1) | **2839 (1650)** | **45 ms** |
| H | F + `-O3` (menos `main.c` y `camara.c`, que el gcc 13 no compila con `-O3`) | no arranca (no contesta a los peeks) | | | | |

Lo que dicen:
- **Elegida F (= R):** G apenas gana estabilidad y deja la distancia en 900 m en algún momento (más popping).
- **`-ffast-math` es mucho peor** (la CPU por cuadro se triplica con el gcc 13 de Ubuntu): descartado.
- **La CPU no llega a 45 fps en la NAOMI** (~30 ms por cuadro de media en carrera): con el tope de 45 el juego va a
  32 fps de media, sube y baja, y para intentarlo **acorta la distancia de dibujo hasta el mínimo (600 m)**: eso es el
  popping (lo de lejos aparece de golpe al acercarse).
- **Con el tope en 30** la distancia se queda mucho más lejos (mediana 2750 m, nunca por debajo de 1200-1350).
- **Los tirones** (cuadros de 60-124 ms) venían de leer el disco: el residente de dc2naomi sirve cada lectura de una
  vez, copiando de la NetDIMM a ~1,3 MB/s con las interrupciones cortadas (perfil `orc3`: `DIMM_SYNCREAD`), así que
  una lectura de 64 sectores (la etapa siguiente, mientras se conduce) o el trozo de 32 KB de la música paraban el
  juego 25-90 ms. Leyendo de 4 en 4 sectores y cediendo la CPU entre trozos, el peor cuadro baja a 40-57 ms.

## Dónde se va el tiempo (variante P = D + `-DNAOMI_PRF`, 415 ventanas de carrera)

ms por cuadro de cada parte del dibujo (las de `PRF()` de `demo/main.c`; "ini" incluye la lógica y las esperas):

| ini | vis | cielo | etapa | bo | coche | robot | traf | l2 | lógica |
|---|---|---|---|---|---|---|---|---|---|
| 14,8 | 1,9 | 0,8 | 6,9 | 0,4 | **4,0** | **3,7** | 1,0 | 0,6 | 7,0 |

- El **coche del jugador** (10 440 vértices, el original no tiene LOD para él) se lleva 4 ms fijos en cada cuadro y
  los **dos personajes** (piloto y acompañante, 2 900 vértices con huesos calculados en la CPU) otros 3,7: entre los
  dos, casi una cuarta parte del cuadro, pase lo que pase en la carretera. Es lo primero a mirar para ganar margen.
- La etapa (6-8 ms) es lo que regula el juego con la distancia de dibujo.

Cargas con F (registro del juego): etapas `SEGnn.DAT` en 3,8-5,4 s y uniones `BKnn.DAT` en 1,7-2,5 s mientras se
conduce (hay ~12 s de margen).

## Todas las etapas (2026-11-18, piloto automático, rama izquierda)

La demo normal solo pasa por unas pocas etapas. Con los modos de prueba de ORC2CDC (`-DPRUEBA_AUTO -DPRUEBA_ORDEN
-DPRUEBA_SIN_TIEMPO -DPRUEBA_RAMA=0 -DPRUEBA_RAMA_FIJA=0`: el piloto corre seguidas las carreras de la lista `PO`,
OutRun 2 y SP en sus cuatro árboles, contrarreloj, misiones, siempre por la izquierda) sobre la versión R3 (la de la
Pi), 55 min, 3101 ventanas de carrera en **33 zonas**: 29,3 fps de media, 10 % de ventanas por debajo de 28.

Las que van peor (ciudades y bosque denso): **METR** 25,7 fps (64 % de ventanas < 28, distancia hasta 800 m),
**LASV** 27,0 (45 %), **GHOS** 27,5 (45 %), **FLOR** 27,6 (37 %, hasta 600 m); NEWY y SANF 29,0 (19 %); CLOU 29,2 (13 %).
Las demás, 29,3-29,9 con 0-10 %. El peor cuadro por zona, 31-63 ms (sin los cambios de pantalla). CSV completo en la
Pi .60: `/root/med_CB0.csv`.

## Más detalle a lo lejos: CL0 frente a CB0 (2026-11-18, rama izquierda, 55 min cada una)

CL0 = CB0 + `-DREPARTO_LOD_MAS=1 -DTA_VB_BYTES=(3072*1024)`: los objetos pequeños (líneas y marcas de la carretera,
señales, piedras...) que el original quita por LOD siguen dibujándose hasta el doble de su distancia (la idea de
DisableStageCulling de OutRun2006Tweaks; ya estaba en ORC2CDC, apagada), en la cola del reparto: solo si sobra TA
después de lo que dibuja el original. El búfer de parámetros del TA sube de 1,9 a 3 MB (la NAOMI 2 tiene 16 MB de VRAM).

| | fps medio | ventanas < 28 fps | cpu medio | lejos mediana | peor cuadro |
|---|---|---|---|---|---|
| CB0 (= R3) | 29,3 | 11 % | 30,1 ms | 3150 m | 63 ms |
| CL0 | 29,1 | 13 % | 30,6 ms | 3100 m | 71 ms |

Por zona (fps CB0 → CL0, ventanas < 28): las abiertas casi igual (CAPE, SEQU, YOSE, DESE, GRAN, NIAG: ±0,1 fps); las
que ya iban justas empeoran: **CLOU** 29,2 → 28,7 (14 → 28 %), **LAKE** 29,5 → 29,0 (9 → 20 %), **SANF** 29,0 → 28,5
(19 → 26 %), **LASV** 27,0 → 26,5 (46 → 57 %), **METR** 25,7 → 24,7 (65 → 69 %), GHOS 27,5 → 27,1. La CPU sube
0,5 ms de media (1-2 ms en las ciudades): el coste es de CPU (recorrer y mandar más nodos), no del TA, así que el
búfer mayor no lo arregla. Lo que se gana a la vista (líneas pintadas más lejos) hay que mirarlo en el mueble: las
medidas no lo ven.

Conclusión: no entra en la versión de la Pi sin que lo pruebe el usuario; si se quiere, lo razonable sería encenderlo
solo en las zonas abiertas (por zona, con la lista de arriba).

## Vídeo del mueble (2026-11-18): rayas de la calzada y reflejos

El usuario grabó 23 min del recorrido automático (CB0) en el mueble (`PXL_20261118_113920908.mp4`, 1080p a 60 fps)
con `med.py` a la vez (`/root/med_VID.csv` en la Pi; el vídeo empieza 6,6 s antes que la medida).

- **Rayas que "se pintan delante del coche"**: no son nodos que quite el LOD ni el reparto del TA; van pintadas en la
  textura del asfalto (BEAC: la 11 de SEG17, 256x256 con mipmaps). Vista de canto, la PowerVR elige el nivel de mip
  por la mayor derivada y las rayas finas se funden con el gris a 30-60 m. Donde se ven lejos, la calzada usa texturas
  rectangulares (sin mipmaps en la PowerVR: llegan lejos, centelleando). Arreglo sin CPU (`demo/main.c compila_cab`,
  solo en las texturas con mipmaps): `-DSUELO_SS=1` supermuestreo de la textura (bit 12 de la palabra TSP) o
  `-DSUELO_MIPBIAS=PVR_MIPBIAS_0_50` (ajuste D: un nivel más nítido). Variantes `h-orcpSS` y `h-orcpMB` (piloto
  automático) en la Pi .60, para que el usuario las compare en el mueble.
- **Reflejos de la carrocería**: el mapa de entorno del coche (`COCHEnn.DAT`, texturas de 256x256 del bloque del coche)
  es una vista fija oscura (media 35/255; el centro, nubes vistas desde abajo; los bordes, edificios), indexada por la
  normal en el espacio de la cámara: con la cámara detrás, el capó coge casi siempre la misma zona negra y nunca refleja
  la etapa. El PC dibuja un cubo dinámico con `cs_ENV_<zona>` (race_env_model_44cd30); propuesta barata pendiente de
  decidir: reflejar el cielo de la etapa girado por el rumbo del coche.

### Probado en el mueble (2026-11-18 tarde)

- **Rayas**: `SUELO_SS=1` solo apenas se nota; `SUELO_SS=1` + `SUELO_MIPBIAS=PVR_MIPBIAS_0_25` (variante S25, el ajuste
  más nítido que admite la PowerVR) sí: las rayas se ven bastante más lejos y el usuario no nota centelleo. 29,3 fps de
  media frente a 29,5 (13 min). Quitar los mipmaps del suelo (copia sin niveles de las texturas VQ al subirlas) queda
  para una futura versión mejorada (decisión del usuario: toca el reparto de la VRAM entre etapa y unión).
- **Reflejo del cielo** (`-DREFLEJO_CIELO=1`, `demo/main.c coche_reflejo`): la carrocería refleja el cielo de la etapa,
  girado con el rumbo de la cámara; fuerza 0,15 en los costados a 0,45 arriba. Variante RC: 29,4 fps frente a 29,5
  (21 min). Al usuario le gusta; los cristales salían opacos (las mallas de tipo 2 en la lista transparente sacan su
  transparencia del alfa del mapa del coche, ARGB1555, y el cielo es RGB565): RC2 deja esas mallas con el mapa de antes.
