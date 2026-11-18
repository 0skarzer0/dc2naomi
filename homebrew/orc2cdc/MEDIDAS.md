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
