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

## Reflejo del escenario, rojo y cristales (2026-11-18, desatendido)

Lo que dijo el usuario con las fotos del mueble frente a las del PC: el coche siempre salió rosa en vez de rojo, los
cristales nunca dejaron ver la carretera a través, y quiere en la carrocería el reflejo de las palmeras, los carteles y
los edificios.

- **Cristales**: las mallas de tipo 2 en la lista transparente (COCHE00: 6 mallas, alfa del vértice 140/255, gris 0x4C
  de desplazamiento) iban con `PVR_TXRENV_MODULATE`, que en la PowerVR toma el alfa solo de la textura (el mapa del coche
  es ARGB1555: 1 dentro del círculo), así que el alfa del vértice no contaba: cristal opaco. Ahora `MODULATEALPHA` y
  `CRISTAL_ALFA` (0,6) sobre su alfa y su desplazamiento: ~21 % opacos.
- **Rosa**: el reflejo se suma a la pintura (0xE21520 en COCHE00) y con el color base blanco un gris o un azul encima
  del rojo lo vuelve rosa. En carrera la fuerza del reflejo baja a 0,08 en los costados y 0,36 arriba.
- **Panorámicas** (`homebrew/orc2cdc/reflejo.py` → `REFLEJO.DAT`, 30 zonas, 6 KB cada una, VQ 256x64): una vista de
  360 grados de cada zona desde la carretera, dibujada al convertir con la geometría y las texturas de su etapa. El juego
  las sube a la VRAM al arrancar (~190 KB) y la carrocería refleja la de su zona: girada con el rumbo de la cámara (la
  normal derecha coge lo de la derecha, la de atrás lo de detrás), a lo largo del coche (`REF_KZ`) y corriendo hacia atrás
  con la distancia (`REF_VEL`: 0,1 de la velocidad de un espejo). Sin `REFLEJO.DAT` en el disco, el cielo de la etapa como
  antes. Hay que añadir `REFLEJO.DAT` a los datos y rehacer el GDI (no se puede sustituir un fichero que no estaba).

Imágenes hechas (2026-11-18 18:20): GDI nuevo con `REFLEJO.DAT` en `datos3` (`gdi.escribe` de ORC2CDC con el
`1ST_READ_pad.BIN` de 1 MB; escrito en el disco local de la máquina virtual, 51 s, porque en la carpeta compartida va
a ~1,8 MB/s), y con `tools/withfiles.py --perfil orc3 --cab ct`: `h-orcpRC3` (piloto automático, `naomi_med` en
0x8c0bcb5c) y `h-orcRL` (la versión normal con las rayas, los cristales, el rojo y el reflejo del escenario), 504,2 MB,
en `otros/orc3/gdi5img/`. Sin probar en el mueble todavía: la Pi .60 no contesta (el mueble apagado).

### RC3 en el mueble (2026-11-18 noche, 23 min con el piloto automático, parada a petición del usuario)

Carga las 30 panorámicas (`REFLEJO: 30 panoramicas de 256x64` en el registro) y al usuario le gusta mucho cómo se ve.
Pero frente a CB0 **no sale gratis**: 29,0 fps de media (29,5), 17 % de ventanas < 28 (8 %), cpu 32,1 ms (29,8) y la
distancia de dibujo mediana baja de 3100 a 2550 m (mínimo 700). Peor en CLOU (27,8 fps), SANF (28,0) y LAKE (28,9). La
variante RC (solo el cielo, sin los cristales nuevos) medía 29,4: lo que pesa está entre RC y RC3 (panorámica, cristales
con `MODULATEALPHA`, término a lo largo del coche); sin averiguar todavía.

**Sombras sobre el coche** (pregunta del usuario): en los datos las sombras sobre la calzada son mallas planas aparte en
la lista transparente (BEAC, SEG17: textura 37, 128x128, la sombra de una palmera, 30 mallas junto a la ruta; 6, 15 y
16, bandas oscuras de carteles, puentes y vallas, unas 380 mallas). Se pueden pasar al convertir a un mapa a lo largo de
la ruta y consultarlo en unos puntos bajo el coche para oscurecer la carrocería.

## Versión definitiva `h-orc2c4` (2026-11-18 noche)

El usuario la pide como definitiva tras ver la RL. Glitches de sus fotos del vídeo largo y qué ha pasado con cada uno:
- **Cielo cortado en rectángulos, en vertical o en diagonal, y la carretera que desaparece (8'59-9'03)**: muchos
  alineados con las teselas de 32x32, sobre todo en las uniones (dos cielos). Hipótesis: OPB lleno. Se da más OPB a los
  translúcidos (`OPB_TR` 32, `OPB_EXTRA` 8). En la variante RC5 el registro `PVR_TA_OPB_POS` marca siempre 103 KB (lo que
  ocupa el primer juego: no se usan los de reserva) en CAST, CLOU y TULI, uniones incluidas, pero el del búfer de
  vértices lee 0 en la NAOMI, así que estos registros no son de fiar aquí. **Sin confirmar que lo arregle.**
- **Panel fijo en el túnel (9'38, LASV)**: candidatos, los planos aditivos gigantes de LASV (texturas 129-131, 64x16
  ARGB4444, 500-600 m de alto, alfa del vértice 0-254: los haces de los focos). **Pendiente.**
- **Nube azul quieta (7'05)**: **pendiente** (no localizada en los datos).
- **Edificios negros (9'36, 19'13)**: según docs/PARIDAD.md de ORC2CDC, el edificio negro de LASV es así en el original
  (cristal oscuro). Sin cambiar.
- **Arbusto en bloques (3'45)**: el impostor de la vegetación lejana (`LOD_LEJ_PX` 48 px, revisión 46 de ORC2CDC, una
  desviación pedida para la Dreamcast). Sin cambiar.
- Chispas al rozar y coche oscuro en zonas oscuras: normales (el usuario).
- Sombras: `SOMBRAS: 148 mallas de sombra` en LAKE (registro del juego).

### `h-orc2c4` no arranca; `h-orc2c5` (2026-11-18, 23:40)

La `h-orc2c4` (versión normal con `OPB_TR=PVR_BINSIZE_32 -DOPB_EXTRA=8`) se queda en "starting..." del cargador de
dc2naomi, sin dibujar nada, dos veces, también tras reiniciar el mueble; la imagen está entera (md5). Las de prueba con
el piloto automático y esos mismos ajustes sí arrancaban (pasan por menos menús). Sospecha: el OPB mayor (memoria de
vídeo) choca con lo que la versión normal reserva al arrancar. `h-orc2c5` = la misma sin esos dos ajustes (con las
sombras), md5 `.gz` `4af643f1a6cd1453560e1d4461cb4304`, **sin probar**; la deja el usuario en la Pi él mismo (copia en
`otros/orc3/gdi5img/`). Mientras tanto va la RL (probada). La SD de la Pi .60 dio errores de FAT ("invalid cluster
chain") y pasó `/boot` a solo lectura; tras reiniciar vuelve a escribir, pero falta un `fsck` (pendiente del usuario).

### `h-orc2c5` tampoco arranca; `h-orc2c6` (2026-11-18, 23:55)

Lo que tenían la c4 y la c5 y no la RL: `som_ofs0`, una copia de la pintura del coche (42 KB) pedida con `calloc` al
cargarlo. En la versión normal el coche se carga en el hueco de la unión prestado y luego se copia a un bloque nuevo del
montón (`compacta_modelo_de`): la memoria está repartida sin holgura. Ahora `coche_sombra` no guarda copia: rehace la
pintura con `coche_color` cuando cambia la sombra. `h-orc2c6` (RL4, sin el OPB mayor), md5 `.gz`
`1ba29f48ef6753d5440a5f5690af6478`, en `otros/orc3/gdi5img/`, **sin probar**.

### Por qué no arrancaban la c4, la c5 y la c6: la imagen cortaba el `1ST_READ.BIN` (2026-11-19, 00:15)

No era el código. El GDI de `gdi5` se hizo con `1ST_READ_pad.BIN` (1 MB, con datos solo en sus 358 primeros sectores y
ceros detrás), y la imagen de NAOMI solo guarda los sectores que tenían datos en el disco tal y como era
(`build_image.nonzero_runs`): un `1ST_READ.BIN` de 362 sectores salía cortado (la c6 coincidía con el bueno hasta el
byte 734830) y la placa se quedaba en "starting..." (también en la otra NAOMI). La RC4 (358 sectores) cabía justo; la
RL perdía lo mismo y arrancaba de suerte. Arreglo: el GDI se rehace con un relleno de 1 MB de 0xFF (`gdi.escribe` con
`~/pad_ff.bin`), y `tools/withfiles.py` ahora se niega a sustituir un fichero si el nuevo pasa del último sector con
datos del original. **`h-orc2c7_dc2naomict`** = la c6 (RL4: rayas, reflejo del escenario, sombras sin copia de la
pintura, cristales, sin el OPB mayor) en ese GDI, 504,5 MB, md5 `.gz` `8dc76a08fa4ebdffee41a27cd55aed52`, comprobado
que lleva el `1ST_READ.BIN` entero; en la Pi .60 y en el CSV (copia `romsinfo.csv.bak_orc2c7`).
La c4 (con el OPB mayor) quizá también arrancaba: no se llegó a probar bien.
La c7 arranca en el mueble (usuario, 00:24). **`h-orc2c8_dc2naomict`** = la c7 con `-DOPB_TR=PVR_BINSIZE_32
-DOPB_EXTRA=8` (más OPB para los translúcidos, por los trozos de cielo cortados), md5 `.gz`
`e800dd0a6556ecbfb182cedcab4006b2`, `1ST_READ.BIN` entero comprobado; en la Pi .60 y en el CSV (copia
`romsinfo.csv.bak_orc2c8`), copia en `otros/orc3/gdi5img/`. Si no arrancara, la c7.
