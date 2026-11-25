# Historial: soporte .cdi y juegos que no caben en 512 MB (2026-11-11 a 11-12)

> Historial: diario de sesiones copiado tal cual del antiguo `HANDOFF.md` (2026-11-25). Puede estar superado por lo escrito después; lo vigente está en [HANDOFF.md](../../HANDOFF.md).

> **Ojo con las IP:** en este diario la Pi del mueble Crazy Taxi aparece como **.60** (y la del mueble estándar a veces como **.59**). Desde el 2026-11-19 son **192.168.68.251** (Crazy Taxi) y **192.168.68.250** (estándar). El texto se deja como se escribió.

## ⭐ Soporte de `.cdi` (CD de autoarranque, 2026-11-11, mañana) — `tools/cdi.py`

Pedido por el usuario para los 6 CDI de `isosdream` (traducciones al español). Sin cambios en el residente ni en el
loader: solo Python.
- **`tools/cdi.py`**: lee DiscJuggler 2.0/3.0/3.5 (descriptor al final del archivo, como lo describe cdirip de DeXT;
  sectores de 2048/2336/2352 bytes, modo 1 y 2) con la interfaz de `gdi.Gdi`. `base` = LBA del IP.BIN (la última
  pista de datos). **El LBA del descriptor ya es el de la pista (índice 1)**; el pregap va guardado delante.
- **`Gdi.base`** (45000 por defecto) sustituye las LBA fijas 45000/45016 en `gdi.py`, `build_image.py` (IP.BIN,
  PVD, `ip_fad` de la cabecera), `dc2naomi.py` y `gensig.py` (`ImageDisc.base` era el desplazamiento del archivo:
  ahora `arc`, y `base` sale del `ip_fad` de la cabecera).
- **TOC:** el residente contesta como lector GD-ROM, así que el área de alta densidad del CDI es solo la pista del
  IP.BIN, numerada 3 (`Cdi.hd_tracks`). Los sectores de las demás pistas de datos se sirven igual (Toy Story 2 tiene
  los archivos en la sesión 1 y el IP.BIN en una sesión 2 de 302 sectores).
- **Cifrado MIL-CD:** `cdi.descramble` (algoritmo de `scramble` de Marcus Comstedt, KallistiOS utils) y
  `Cdi.boot_is_scrambled`: texto de 48+ bytes seguidos solo sobrevive sin cifrar (las cadenas cortas sobreviven al
  barajado de bloques de 32 bytes y engañaban a la primera versión); un 1ST_READ que empieza por `nop` es plano.
  Los 6 discos lo llevan **sin cifrar** (binhack). El descifrado está probado solo con datos propios (ida y vuelta).
- **Relleno:** `Gdi.filler_files()` (archivos ≥ 4 MB de un solo byte repetido); `dc2naomi.py` los mete en `blank`
  solo para `.cdi`. Cannon Spike: `0A.DAT`, 448 MB de `0x37` → imagen de 614 a 166 MB.
- **`tools/cmpimage.py DISCO IMAGEN`**: relee la imagen como el residente (cabecera, TOC, rangos) y compara IP.BIN,
  volumen ISO, programa de arranque y todos los archivos. Pasa en los 6 CDI. Regresión: SPF2X (CHD) convertido con el
  código nuevo da la misma imagen descomprimida (md5 `8f22c293…`) que con el anterior.
- **Conversión** (mandos `joy`, VMU de bucanero/dreamcast-saves, nombres cortos, filas en
  `isosdream/filas_romsinfo.csv`; gzip nivel 1 para caber en los 3 min por orden del PC):
  `cspike_es` 166 MB (VMU `v62540`, todo), `ut_es` 200 MB (`UNREALT`, arenas USA; sin música: 18 pistas CDDA),
  `ssf2x_es` 332 MB (`SSF2X`), `millennium_es` 83 MB (sin partida publicada; sin música: 8 pistas CDDA; el resto del
  CD era relleno a cero), `buzz_es` **559 MB, no cabe** (`v18060`), `toystory2_es` **674 MB, no cabe** (`v38204`).
  Los 6 con arranque estándar, cable y gancho de mandos encontrados por `findpatch`. **Nada probado en Flycast ni en
  placa** (no había Flycast ni BIOS de NAOMI en esta sesión).
- **Riesgos a mirar si no arrancan:** (1) el residente dice "GD-ROM" (`GET_DRV_STAT` = `0x80`) y un juego parcheado
  para CD-R puede esperar CD (`0x20`) o pedir la TOC del área 0 (hoy fija, de GD); (2) el IP.BIN de estos discos
  puede llevar un cargador propio (binhack) que el residente ejecuta como bootstrap; probar con `DIMM_NOIPBOOT`.

## Soulcalibur (USA) con música en mono (2026-11-12) — `isosdream/soulcal_dc2naomi.bin.gz`

683 MB → **469 MB** (cabe). Elegido por el usuario entre las opciones: la música son 34 temas en PCM de 16 bits sin
cabecera, cada canal en su archivo (`*L.P16` / `*R.P16`, mismo tamaño, 442 MB); los 34 `*R.P16` apuntan con `alias`
a su `*L.P16` (221 MB fuera). Finales, galería y todo lo demás intactos. Hecho con un envoltorio de una vez que añade
`game["alias"] = [([R], L), …]` al perfil automático (y gzip nivel 1); el conversor no recorta por su cuenta.
Comprobado releyendo la imagen: 88 archivos correctos (los 34 derechos = su izquierdo), IP.BIN y 1ST_READ iguales.
VMU `00000031` (todo abierto, USA); fila añadida a `filas_romsinfo.csv`. Sin probar en placa. La versión de 683 MB
quedó en `isosdream/_to_delete/`.

## Rainbow Cotton (traducción de Derek Pascarella) con los vídeos recodificados (2026-11-12) — `tools/sfdre.py`

873 MB → **500,2 MB** (cabe; 424 MB comprimido). Elegido por el usuario (opción A: todo a 640×480… en realidad, cada
vídeo con **su** tamaño y frecuencia, ~0,9 Mbit/s); no quiso respaldo con vídeos quitados.
- **Los SFD** (Sofdec): packs de 2048 bytes, un paquete de 2030 por pack; 3 packs de cabecera (2 de sistema +
  relleno, 1 privado `SofdecStream`); sonido ADX en `C0` con PTS; vídeo MPEG-1 en `E0` con cabecera fija de 12 bytes
  (STD `602e` + PTS/DTS o `0f`) y 2018 de datos; pack final `000001b9` + `FF`. GOP de 15 con 2 B. **END y STF son
  640×240, STF a 29,97 fps**: no suponer 640×480/24.
- **`tools/sfdre.py ORIG OUT KBPS`**: ffmpeg recodifica solo el vídeo (mismo tamaño y frecuencia, `-g 15 -bf 2`,
  máx. 3,6 Mbit/s, búfer 40 KB; `setpts=N/(FR·TB)` para no añadir ni quitar imágenes: las marcas del original no son
  monótonas); el empaquetador copia tal cual los packs de cabecera y de sonido (con su SCR) y mete el vídeo nuevo en
  los huecos del original al mismo ritmo de imágenes; marcas estándar (DTS = orden de decodificación, PTS = orden de
  presentación + 1 imagen: el vídeo va 42 ms detrás del sonido). Comprobado en los 16: mismas imágenes, 0 avisos al
  decodificar con ffmpeg, sonido ADX idéntico (md5). Muestra a 60 s de OP: algo más blando, subtítulos legibles.
- **Imagen:** envoltorio de una vez sobre `open_disc`: cada SFD nuevo en el primer sector del original, tamaño nuevo
  en su registro de directorio, el resto de su extensión a cero (lo omite `nonzero_runs`). Comprobado releyendo la
  imagen: 328 archivos (16 vídeos = los recodificados, el resto = el disco), IP.BIN y 1ST_READ iguales.
- VMU `RAINCOT` (voces desbloqueadas); fila en `isosdream/filas_romsinfo.csv`. **Sin probar en placa ni en Flycast:**
  si se cuelga al llegar a un vídeo, el sospechoso es el empaquetado (Sofdec de la consola, no ffmpeg); la versión de
  873 MB quedó en `isosdream/_to_delete/`.

## ⭐ Rainbow Cotton **funciona perfecto en la placa** (2026-11-12, el usuario) → vídeos recodificados validados; Buzz Lightyear igual

- El reempaquetado Sofdec de `tools/sfdre.py` es bueno en hardware real: el usuario prefiere ya recodificar vídeos a
  quitarlos para que un juego quepa.
- **`sfdre.py`** ahora copia del original la longitud de GOP y si usa imágenes B (Rainbow Cotton: 15 con B; Buzz:
  12 y la intro sin B; algunos 4, 8 o 30) y toma como techo de bitrate el mayor entre el del original y 3,6 Mbit/s.
  Comprobado: los SFD de Rainbow Cotton salen **byte a byte iguales** a los que funcionan (STV5, STF, END).
- **`tools/withfiles.py CARPETA [argumentos de dc2naomi.py]`** (generaliza el envoltorio de una vez): sustituye los
  archivos del disco por los de la carpeta (misma ruta), cada uno en el primer sector del original, con su tamaño
  nuevo en el directorio y el resto a cero. `GZIP_LEVEL=1` para ir rápido. Reconstruido Rainbow Cotton con ella: la
  **parte del disco es idéntica** a la imagen que funciona; solo cambia el cargador (`loader.bin` posterior: luces del
  mueble por JVS, `c6a0300`).
- **Buzz Lightyear of Star Command** (traducción al español de pitito, CDI): 43 vídeos `MOVIES/*.SFD` de 320×480 a
  30 fps recodificados a 2,5 Mbit/s (351 → 211,5 MB; los 43 con las mismas imágenes, 0 avisos, ADX idéntico; fotograma
  de la intro indistinguible) → imagen **437 MB** (antes 559). Comprobada: 194 archivos (43 vídeos = recodificados, el
  resto = el CDI), IP.BIN y 1ST_READ iguales. Entregada como **`isosdream/dc-buzz_es_dc2naomi.bin.gz`** (el usuario
  ya usa el prefijo `dc-` en los nombres) con su VMU `v18060` (completo) y su fila en `filas_romsinfo.csv`. Sin
  probar en placa.

## Toy Story 2 (traducción al español de pitito, CDI) con los vídeos recodificados (2026-11-12) — 674 → 477 MB

Opción elegida por el usuario de las que se le dieron (receta 14): recodificar a 1,2 Mbit/s (la otra, 1,0).
- Disco: 402 MB de vídeo (23 `GEM_MOVIES/*.SFD`, casi todos 320×416 a 29,97 fps, ~2,6 Mbit/s; I y P en GOP de 12,
  algunos con B), 170 MB de música ADX (`GEM_MUSIC`, sin tocar), 67 MB de gráficos (`GEM_WADS`).
- **`sfdre.py` ya no toma como techo el bitrate de la cabecera si es la marca de "variable" (104,86 Mbit/s,
  `0x3FFFF` × 400)**; comprobado que Rainbow Cotton (STF, STV5) y Buzz (INTRO, TTALES) salen idénticos.
- Recodificados a 1200 kbit/s: 401,9 → 204,5 MB en 22 s; los 23 con las mismas imágenes, 0 avisos y ADX idéntico;
  fotograma de L003 a 40 s comparado: casi igual. `GZIP_LEVEL=1 tools/withfiles.py ~/ts/new --cab joy --batch
  Toy_Story_2…cdi` → **476,9 MB** (378 MB comprimido). Comprobada: 389 archivos (23 vídeos = recodificados, el resto =
  el CDI; los datos están en la sesión 1 y el IP.BIN en la LBA 359984), IP.BIN y 1ST_READ iguales.
- Entregada como **`isosdream/dc-toystory2_es_dc2naomi.bin.gz`** con su VMU `v38204` ("100% complete") y su fila en
  `filas_romsinfo.csv` (género `Platform`). Sin probar en placa.

## The Last Blade 2: el CHD del usuario es un ripeo sin vídeos (2026-11-12)

Revisado a petición del usuario ("¿qué le pasaba?"): no fallaba; está aparcado sin probar en placa (en Flycast llega
al título). **Los 29 `ZSFD/*.SFD` (630 MB) del CHD del usuario (`otros/Last Blade 2 … (USA).chd`, 240 MB) son
relleno**: la secuencia 00 01 02 … FF repetida, ningún MPEG ni `SofdecStream` (`sfdinfo.py` y ffprobe no ven nada).
El `alias` del perfil `lb2` (vídeos de personaje → el más corto) no quitaba nada real; sin vídeos el juego son unos
280 MB. Una pista de audio de CD (17,7 MB); la música va en `.AFS`: la regla de "sin música" no le afecta.
Opciones dadas al usuario: probarlo tal cual (sin intro ni escenas), o un volcado completo y recodificar sus vídeos
(~1,2 Mbit/s → unos 500 MB). KOF Dream Match 1999 (42 pistas de CD-DA) queda fuera por la regla 8b.
**Para cualquier juego:** si un archivo de vídeo es esa secuencia, el volcado es un ripeo (comprobar antes de
proponer recortes).

## Coches con vídeos recodificados + motos y Star Wars Racer al mueble Crazy Taxi (2026-11-12, tarde)

El usuario eligió para los 5 que no cabían: recodificar (Demolition Racer, TNN, TXR2), audio a mono (MSR) e investigar
Rush 2049; todos con mandos `ct`, VMU desbloqueada y CSV. Además, Jeremy McGrath Supercross 2000 y Star Wars Racer
pasan al mueble Crazy Taxi y salen del de palancas.
- **Herramientas** (ahora en el repo: `tools/discfiles.py` = `extract.py` + `sz.py`/`anal.py`, `tools/sfdbatch.py` =
  `reall.py` + `chk.py`; los nombres de abajo son los de los scripts sueltos que se usaron en el PC): `~/extract.py CHD DIR
  "*SFD"` (saca archivos del disco), `~/reall.py ORIG NUEVO FRAC MIN MAX` (sfdre.py a cada SFD, kbps = FRAC × bitrate de
  la cabecera entre MIN y MAX), `~/chk.py ORIG NUEVO` (mismas imágenes y mismos paquetes C0 de audio con sfdinfo, y
  ffmpeg sin errores de vídeo).
- **Ojo:** el tamaño final depende poco del kbps pedido: estos vídeos eran sobre todo relleno de bitrate (TNN 583 → 157
  MB pidiendo 0,9 × su bitrate). Se usó FRAC 0,9 (2500-5500 kbps), la mejor calidad que cabe.
- **Demolition Racer:** `MISC/CREDITS.SFD` 38,1 → 18,2 MB y `MISC/INTRO.SFD` 27,1 → 13,0 MB (1600 kbps, 640x240): imagen
  **497,3 MB**. VMU `demolitionrace/v21403` ("100 % all complete"). `dc-demolition_dc2naomict`.
- **TNN Hardcore Heat:** 26 de 28 SFD recodificados; `EU_ROLL.SFD` (640x448, sin paquete BF, audio MPEG en C0) y
  `USA/ASC_240.SFD` se dejan como estaban por ser de otro tipo: imagen **310,2 MB**. VMU `hardcore/v49295`
  (`HARDCORE.SYS`, "opening all secrets"). `dc-tnnhh_dc2naomict`.
- **Tokyo Xtreme Racer 2:** los 6 SFD 312,7 → 137,2 MB: imagen **493,8 MB**. VMU `tokyo2/v15947` (`TXRACER02GF0`,
  versión USA, "everything done"). `dc-txr2_dc2naomict`.
- **Jeremy McGrath (`dc-jmsx2000_dc2naomict`) y SW Racer (`dc-swracer_dc2naomict`)** con `--cab ct` y las mismas partidas
  que en la .250. Quitados de la .250 (ficheros y filas; copia `romsinfo.csv.bak_quita_motos_swracer`, reimportado; las
  versiones `joy` del PC a `_to_delete/`).
- Pi .60: los 10 ficheros con md5 comprobado, 5 filas nuevas (copias `romsinfo.csv.bak_dc_ct_motos`,
  `.bak_dc_ct_videos`), todas en `dreamcastisos/filas_romsinfo_ct.csv`. Nada probado en placa.

## MSR y SF Rush 2049 adelgazados para el mueble Crazy Taxi (2026-11-12, tarde) — sin probar en placa

**Metropolis Street Racer (USA Rev A), 758 → 487,4 MB, `dc-msr_dc2naomict`:**
- Lo que ocupa: `SOUND/{VOICE,TOKYO,LONDON,SANFRAN}.AFS` (430 MB): AFS sin tabla de nombres, primera entrada en 524288
  (tabla de 512 KB), entradas alineadas a 2048; dentro, 248 ADX tipo 3, cabecera v3, 44,1 kHz estéreo (uno con bucle,
  cabecera de 2048 bytes). `MOVIES/MSR.SFD` 60 MB (320x480, 25 fps).
- **Nuevo `tools/adxmono.c`** (decodifica ADX como vgmstream, mezcla los dos canales y vuelve a codificar mono probando
  7 escalas por bloque con la historia del decodificador; reescribe canales y, si hay bucle, los bytes del bucle) y
  **`tools/afsmono.py`** (reempaqueta el AFS con las mismas entradas desde el mismo primer desplazamiento).
  Comprobado: SNR 32 dB frente a la mezcla mono del original decodificada por ffmpeg, igual que el codificador ADX de
  ffmpeg (31,7 dB): es lo que da ADX de 4 bits; el bucle (`TOKYO` entrada 10) queda en 0x800 / 0x38e4f0, bien calculado.
- Solo mono daba 511 MB (sin margen): **las voces (`VOICE.AFS`) además a 22050 Hz** (`--half-rate`; el navegador del
  propio juego ya trae voces a 22050). Música 112,8+108,9+87,5 → 56,7+54,7+44,0; voces 117,6 → 30,0. Vídeo 59,9 →
  28,8 MB (`reall.py` 0,9). Comprobados los 4 AFS: mismo número de entradas, cada ADX mono, alineado, con las muestras
  esperadas; una voz decodificada por ffmpeg sin errores.
- VMU `metropolisracer/v81430` (`MSRSINGL.SAV`, "Domestic save … EVERYTHING", 68 bloques).
- **Riesgo:** que el motor de sonido espere estéreo en la música (no debería: ADXT lee los canales de la cabecera).

**San Francisco Rush 2049 (USA), 958 MB → dos versiones:**
- Los 18 `.STR` (905 MB) son **la banda sonora en PCM de 16 bits sin comprimir**: cabecera de 2048 bytes (palabras LE:
  versión 1, 44100, 16 bits, 16384 bytes por bloque de canal, nº de bloques, bytes de datos, 2 canales, nº de bloques)
  y bloques de 16384 bytes alternando canal izquierdo y derecho (`tools/rushstr.py` lo documenta). No es ADX ni vídeo.
- **`dc-rush2049_dc2naomict` (504,7 MB): las 18 canciones en mono** (`tools/rushstr.py`: cada par de bloques
  promediado, cabecera con 1 canal y la mitad de bytes). **No se sabe si el juego lee los canales de la cabecera**
  (los 18 archivos traen los mismos valores): si la música suena rara (doble velocidad, cortes), usar la otra.
- **`dc-rush2049_9_dc2naomict` (463,8 MB, reserva segura): formato intacto, 9 canciones**: `withfiles.py -` con
  `--alias` BASSY=HIGH, STARSKY=STUNTED, WARRIOR=SUNSET, MORNING=NIGHT, NOON=FLIER, SPEED=TRANCEY, GARAGE=THEROCK,
  WINGEY=ROBO, HIDDEN=VICE (se quedan las 9 más cortas; diez ya no caben).
- VMU `rush2049/v82401` ("Everything unlocked", `RUSH2049.P00`) en las dos.
- En el PC queda `rush_bassy_prueba.wav` (37 s de BASSY.STR leído como bloques L/R): sirve para confirmar de oído que
  la disposición de bloques es la correcta.

**Pi .60:** `dc-msr`, `dc-rush2049`, `dc-rush2049_9` (`.bin.gz` + `.vmu`, md5 comprobado), filas añadidas (copia
`romsinfo.csv.bak_dc_ct_msr_rush`, reimportado); 18 filas `_dc2naomict` en total, todas con su archivo. `/boot` al 37 %.
