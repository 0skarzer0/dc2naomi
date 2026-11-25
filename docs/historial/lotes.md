# Historial: lotes de juegos y cambios en las Pi (2026-11-11 a 11-13)

> Historial: diario de sesiones copiado tal cual del antiguo `HANDOFF.md` (2026-11-25). Puede estar superado por lo escrito después; lo vigente está en [HANDOFF.md](../../HANDOFF.md).

> **Ojo con las IP:** en este diario la Pi del mueble Crazy Taxi aparece como **.60** (y la del mueble estándar a veces como **.59**). Desde el 2026-11-19 son **192.168.68.251** (Crazy Taxi) y **192.168.68.250** (estándar). El texto se deja como se escribió.

## Lista de juegos del mueble estándar (`docs/pi250-juegos.md`): hecha (2026-11-13)

La tabla de juegos de Dreamcast la escribió una sesión a mano; se le añadió un apéndice con todo lo demás que hay en la
Pi .250 (originales de NAOMI, NAOMI 2 y Atomiswave, y filas o ficheros sueltos), generado con
`tools/board/picatalog.py` (lee el CSV y `/boot/roms/` por SSH; estados de `docs/pi250-estado.csv`). Para rehacerlo:
`PIHOST=192.168.68.250 PIPASS=... python3 tools/board/picatalog.py docs/pi250-estado.csv` (vale también para la .60).

## Lote de lucha + YSGW con VMU para el mueble estándar (2026-11-11, madrugada)

Pedido por el usuario: convertir los 7 CHD de su carpeta `dreamcastisos` con mandos normales (`joy`) y VMU con todo
desbloqueado, subirlos a la Pi del mueble estándar y actualizar el CSV.
- **Red:** la Pi `virtua` tenía la `192.168.68.59` estática y otro aparato (MAC `80:c5:f2:1c:4c:3d`, TTL 255) tenía la
  misma IP: el móvil llegaba a la Pi y el PC al otro aparato ("Connection refused"). El usuario la pasó a la
  **`192.168.68.250`** (fuera del DHCP). NetDIMM sigue en `10.0.0.3`.
- **Conversión** en el PC del usuario (terminal de la app de escritorio): `app/dc2naomi.py --cab joy --batch CHD`,
  29-94 s por juego. Ojo: un proceso lanzado en segundo plano muere al acabar la orden (límite de 3 min por orden):
  hay que convertir en primer plano, uno o dos por orden.
- **VMU** (`tools/vmutool.py import`, partidas de bucanero/dreamcast-saves): Garou `garou1` (galería al 100 %), KOF
  2002 `KOF_2002` (todo), SSF2X `SSF2X` (todo y menú DIP; versión japonesa), 3rd Strike `v37955` (todos los
  secretos, partida USA), Double Impact `v50554` (todo). Super Puzzle Fighter II X: no hay partida publicada, tarjeta
  vacía. YSGW: sin VMU (`catalog.NO_VMU`).
- **Pi** (`/boot/roms/`, md5 comprobado de los 13 ficheros): `kof02`, `motw`, `sf3ts`, `spf2x`, `ssf2x` sustituidos
  (eran las imágenes del 2026-11-09 sin hueco de VMU; mismos nombres, así que sus filas siguen valiendo) y nuevos
  `sf3di`, `ysgw` (`*_dc2naomi.bin.gz`) con fila en `/boot/config/romsinfo.csv` (copia en
  `romsinfo.csv.bak_dc2naomi_vmu`) importada a `/var/www/html/csv/romsinfo.csv` con `importcsv.py`. Cada juego con
  VMU tiene su `*_dc2naomi.vmu` al lado; `wipiloader.py` de esa Pi ya envía con `dc2naomi_send.py`.
- Subida reanudable desde el PC (`tail -c +N | ssh "cat >> X.part"`, md5 y `mv`): el Wi-Fi del portátil iba de 3 MB/s a
  0,15 MB/s (ping al router 70-250 ms). La Pi no tiene `rsync`; su `/boot` queda al 93 % (2,0 GB libres).
- **Estado:** nada de este lote probado en placa ni en Flycast con VMU. `sf3di` sigue roto según el catálogo (dos
  programas lanzados por un menú; los mandos no llegan); se subió porque el usuario lo pidió.

## Segundo lote para el mueble estándar: `isosdream` (2026-11-11, 06:00) — sin subir a la Pi (lo hace el usuario)

`app/dc2naomi.py --cab joy --batch` en el PC del usuario; nombres cortos; filas en `isosdream/filas_romsinfo.csv`.
- `dcop_es` (Dynamite Cop PAL, traducción al español de pitito, Detonator Pack integrado): 198 MB. VMU `v18467`
  (`D_COP_PL.REC`, la única partida PAL publicada: misiones 4-6 abiertas, no todo). El IP.BIN no es el estándar.
- `shutokou2_en` (Shutokou Battle 2 JP, traducción de SGGG): 365 MB. VMU `shoudu2` ("Jap Perfect Save! All Open!").
- `soulcal` (Soulcalibur USA): **683 MB, no cabe** en la NetDIMM de 512 MB. VMU `00000031` (todo abierto, USA).
- `rcotton_en` (Rainbow Cotton JP, traducción de Derek Pascarella): **873 MB, no cabe**; comprimido con nivel 1 para
  caber en los 3 min de una orden (154 s). VMU `RAINCOT` (selección de voces).
- Los cuatro son juegos desconocidos para el catálogo (parches de `findpatch`). Nada probado en Flycast ni en placa.
- **CDI (6, sin convertir):** el programa solo lee `.chd`/`.gdi`. Buzz Lightyear of Star Command, Cannon Spike,
  Millennium Y2K Fighters, SSF2X, Toy Story 2 y Unreal Tournament, todos traducciones al español en CDI
  (autoarranque en CD: segunda sesión, `1ST_READ.BIN` posiblemente cifrado para MIL-CD). Haría falta un lector de CDI,
  descifrar el `1ST_READ` y una TOC de CD en el residente. Aqua GT desapareció de la carpeta antes de convertirlo.
- Ojo: un argumento con corchetes funciona (`[pitito]`); `dc2naomi.py` no expande comodines.

## Bangai-O (USA) para el mueble estándar (2026-11-12) — `dreamcastisos/dc-bangaio_dc2naomi.bin.gz`

Juego nuevo para el catálogo (Treasure, `T40217N`): `dc2naomi.py --cab joy` en 19 s, parches localizados por
`findpatch`, imagen **98 MB** (66 MB comprimida); `cmpimage.py`: 663 archivos iguales, IP.BIN y 1ST_READ iguales.
VMU `bangaio/v95185` ("all stages completed"; la otra publicada solo llega a la fase 24). Fila en
`dreamcastisos/filas_romsinfo.csv`; no subido a la Pi (lo hace el usuario). Sin probar en placa.
**Sin música:** el disco lleva 34 pistas de audio de CD (≈ 680 MB, toda la banda sonora); efectos y voces van en
archivos y sí suenan. Es el mejor candidato para la idea pendiente de reproducir CD-DA (recodificada para caber: con
98 MB de imagen quedan ~400 MB libres en la NetDIMM).

## Criba de 78 CHD por música en CD-DA (2026-11-12) — `tools/cddascan.py`

El usuario dejó 78 imágenes en `dreamcastisos` y pidió, sin convertir, cuáles descartar (regla 8b). `cddascan.py`
(solo lee la tabla de pistas: 32 s). **39 descartadas** (4 a 49 pistas de audio): Mortal Kombat Gold, Bangai-O, Hydro
Thunder, Mr. Driller, Stunt GP, F1 World Grand Prix II (Europe), F1 World Grand Prix (USA), Monaco Grand Prix, Super
Runabout, Racing Simulation 2, Tokyo Xtreme Racer, Vigilante 8 2nd Offense, ChuChu Rocket!, Ms. Pac-Man Maze Madness,
Walt Disney World Quest, 4 Wheel Thunder, Re-Volt, Looney Tunes Space Race, SnoCross, Vanishing Point, Ducati World,
Sega GT, Soul Fighter, Suzuki Alstare, Toy Racer, The Flintstones Viva Rock Vegas (proto), South Park Rally, Speed
Devils Online, F1 Racing Championship, GigaWing, Roadsters, Taxi 2, 4x4 Evo, Aqua GT, Exhibition of Speed, POD
Speedzone, Speed Devils, Test Drive V-Rally, Spirit of Speed 1937. **39 sin música en CD** (0 pistas, o una sola de
1 MB, el aviso de "esto es un GD-ROM"; Last Blade 2 una de 18 MB con la música en `.AFS`). Ojo: varias de las válidas
pasan de 512 MB (Sonic Adventure 1 y 2, Vampire Chronicle, Tech Romancer, SF Rush 2049, Evil Dead…): se verá al
convertir (receta 14).
**Borradas por petición del usuario** las 39 descartadas (`dreamcastisos`, con su permiso de borrado): quedan 39 CHD,
ninguno con CD-DA. Los `dc-bangaio_dc2naomi.*` convertidos antes siguen ahí.

## Lote de 17 juegos sin coches ni ripeos, subido a la Pi .250 (2026-11-12)

Pedido del usuario: "convierte todos los que no sean de coches y no necesites ripear nada, súbelos a la Pi .250 y
actualiza el CSV". De los 39 CHD que quedaban (sin CD-DA, ver arriba):
- **Convertidos** (`--cab joy`, 5-104 s cada uno, en el PC del usuario con `~/conv.sh` = bucle sobre la lista que
  salta lo ya hecho y para a los ~100 s para caber en los 3 min): Gunbird 2, Jeremy McGrath Supercross 2000 (moto, no
  coche), JoJo, Karous, The Last Blade 2 (417 MB: el conversor ya quita el relleno de los `ZSFD`; sin vídeos reales),
  Neo Golden Logres, Net de Tennis, Psyvariar 2, Radirgy, Shikigami no Shiro II, Sonic Shuffle, Star Wars Racer
  (pods, no coches), Triggerheart Exelica, Trizeal, Twinkle Star Sprites, Under Defeat, WWF Royal Rumble.
  Nombres `dc-<corto>_dc2naomi.{bin.gz,vmu}` en `dreamcastisos/`.
- **VMU con partida desbloqueada** (bucanero, receta 10; región USA donde la hay): Gunbird 2 `v33167`, JM Supercross
  `v85569` (opciones, todo abierto) + `v52330`, JoJo `v11766` ("Everything unlocked"), Last Blade 2 `v35892` (versión
  USA), Sonic Shuffle `v20598`, SW Racer `v25373` ("Everything open"), WWF Royal Rumble `v39825` (todos los
  secretos). Sin partida publicada (tarjeta vacía): Karous, Neo Golden Logres, Net de Tennis, Psyvariar 2, Radirgy,
  Shikigami II, Triggerheart, Trizeal, Twinkle Star Sprites, Under Defeat.
- **Coches, no convertidos por la petición:** Demolition Racer, MSR, SF Rush 2049, Test Drive 6, Test Drive Le Mans,
  TNN Hardcore Heat, Tokyo Xtreme Racer 2, Wacky Races (siguen como CHD en la carpeta).
- **Pasan de 512 MB (necesitarían ripeo/recorte), sin convertir:** Evil Dead (977 MB), Fur Fighters (828), Jet Grind
  Radio (899), Rayman 2 (921), Sonic Adventure (973) y 2 (968), Tech Romancer (966), Vampire Chronicle (953), Pro
  Pinball Trilogy (664), Psychic Force 2012 (749). Virtua Fighter 3tb (643 MB) se convirtió y no cabe: sus ficheros
  están en `_to_delete/`. (Tamaño = suma de archivos del disco: `~/sz.py` con `gdi.open_disc(...).walk()`.)
- **No soportados** (arrancan con un `.BIN` de Windows CE: "0.BIN", `00MMXDC.BIN`, `1WWFTUDE.BIN`): Mars Matrix,
  Marvel vs. Capcom (Clash of Super Heroes) y WWF Attitude. Quedan como CHD.
- **Pi .250:** los 34 ficheros (17 `.bin.gz` + 17 `.vmu`) en `/boot/roms/`, md5 comprobado con `piup.sh` (5 tandas), 17
  filas añadidas a `/boot/config/romsinfo.csv` (copia `romsinfo.csv.bak_dc_lote3`, importado con `importcsv.py`; copia
  de las filas en `dreamcastisos/filas_romsinfo_lote3.csv`). **`/boot` queda al 99 % (474 MB libres):** para más
  juegos hay que borrar alguno de la Pi. Nada de este lote probado en placa.

## Juegos de coches para el mueble Crazy Taxi (Pi .60), 2026-11-12

Pedido del usuario: convertir los de coches con `--cab ct`, subirlos a la Pi .60 y actualizar su CSV; **no** convertir los
que tengan música en CD, arranquen con Windows CE o superen los 512 MB. Mandos `ct` (los de siempre): volante = stick
analógico, acelerador = R, freno = L, **START apretado + acelerador = Y, START + freno = X**, START actúa al soltarlo
(README, "Mueble Crazy Taxi"); el conversor `--cab ct` los pone solo.
- **Convertidos** (`~/convct.sh`, como `conv.sh` pero `--cab ct`; 51-96 s): Test Drive 6 (493,7 MB), Test Drive Le Mans
  (246,2 MB), Wacky Races (475,4 MB). Ficheros `dc-td6|tdlemans|wackyraces_dc2naomict.{bin.gz,vmu}`.
- **VMU con todo desbloqueado** (bucanero): TD6 `v26596` (`TESTDRIV6_00`, todos los torneos); Le Mans `v6000`
  (`TDLEMANS.OPT`, todo abierto) + `v40738` (`TDLEMANS.001`, todos los modos y coches; nombres de la versión USA);
  Wacky Races `v7471` (`WACKYRUS.001`, todas las estrellas y pistas) + `v41658` (`WACKYRUS.SYS`, niveles y habilidades).
- **No convertidos (superan 512 MB, suma de archivos):** Demolition Racer 530, MSR 758, SF Rush 2049 958, TNN Hardcore
  Heat 733, Tokyo Xtreme Racer 2 669. Ninguno tiene CD-DA (criba anterior) ni arranca con Windows CE.
- **Pi .60:** los 6 ficheros en `/boot/roms/` (md5 comprobado con `piup.sh`, `/boot` con 21 GB libres), 3 filas al final de
  `/boot/config/romsinfo.csv` (copia `romsinfo.csv.bak_dc_ct_cars`; imagen `crzytaxi.png`, "Analog (Driving)",
  `crazy-taxi` / `generic-driving-no-ffb-support`, como las demás `*_dc2naomict`; importado con `importcsv.py`); copia de
  las filas en `dreamcastisos/filas_romsinfo_ct.csv`. Sin probar en placa.
- Error mío a evitar: al derivar `convct.sh` de `conv.sh` con `sed` quedaron en la lista los juegos del lote anterior y se
  convirtieron 4 con `ct` por error (movidos a `_to_delete/`); revisar siempre la lista antes de lanzar el script.

## Descartados por los mandos (2026-11-13)

Repasando los 11 que no caben sin recortes, el usuario descarta por jugarse mal con palanca digital **Jet Grind Radio,
Fur Fighters y Evil Dead**: sus CHD borrados de `dreamcastisos/` (con su permiso de borrado), y el `.part` que quedó de
Evil Dead en `_to_delete/`. Quedan por recortar, por orden de interés para la palanca: Vampire Chronicle, VF3tb, Tech
Romancer, Psychic Force 2012, Pro Pinball Trilogy. Después borrados también Sonic Adventure 1 y 2 y Rayman 2 (usuario,
mismo día): de los recortes solo quedan esos cinco.
