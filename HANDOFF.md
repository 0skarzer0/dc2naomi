# HANDOFF — dc2naomi (juegos de Dreamcast en NAOMI)

Documento de traspaso entre sesiones (personas o IAs): **lo vigente**. Arrancar juegos de Dreamcast en una NAOMI /
NAOMI 2 por netboot (NetDIMM), sustituyendo la BIOS de Dreamcast por un programa residente.

- El diario de sesiones (investigaciones, pruebas, lotes) está en [`docs/historial/`](#historial-dónde-está-cada-cosa): solo se
  lee cuando hace falta el detalle de un juego o de un problema. Cómo está hecho por dentro: [docs/arquitectura.md](docs/arquitectura.md).
- **Actualízalo en cada sesión:** lo que cambia el estado o las recetas, aquí; el relato de la sesión, en el archivo de
  `docs/historial/` que toque (o uno nuevo, enlazado en el índice del final).

## Recetas: lo que funciona, paso a paso

Cada receta se ha hecho de verdad (1-7 el 2026-11-10; 8-14 el 2026-11-11/12; 15-16 el 2026-11-13/19).

**0. Reglas.** Nada con copyright al repositorio (ni imágenes, ni IP.BIN, ni BIOS). **Los juegos del usuario y su
`info.txt` están en `C:\Users\Usuario\Documents\dc2naomi` y no se suben nunca** (ni se copian al repo). La contraseña
de la Raspberry no se escribe en ningún fichero del repo: va en la variable `PIPASS`. Un juego sólo cuenta como probado
si funciona en la placa real (Flycast no tiene caché, ni excepciones de dirección, ni comprueba SB_MDAPRO). No decir
"comprobado" sin haberlo visto. Cada prueba en placa le cuesta tiempo al usuario: antes de enviar, probar en Flycast.

**1. Reconstruir el loader tras tocar `resident/` o `loader/`:** `bash app/make_loader.sh` → `app/loader.bin` (si no,
el programa llevará el residente viejo). Direcciones de las variables del residente: `sh-elf-nm -n resident/resident.elf`
(cambian en cada compilación). Construir un perfil concreto de `tools/games.py`: `./build.sh PERFIL DISCO [SALIDA.bin]`.

**2. Probar en Flycast:** `cd tools/flycast; FCBIN=RUTA/flycast FC_SYSM_RAM=1 FC_PEDALS=1 STEP=10 DUMP=1 bash
run1.sh IMAGEN.bin 45 NOMBRE` → `NOMBRE.png` (capturas) y `/tmp/ram.bin` (los 32 MB de RAM: la dirección
`0x8dXXXXXX` está en el desplazamiento `0x01XXXXXX`). Sin `NAOMI2=1`. La imagen va descomprimida (`img_mkbin.py` la
descomprime e inyecta la `.vmu` como el netbooter). Sin `FC_PEDALS=1`, con los mapas `wheel`/`ct` START cuenta como
"usado" y no se envía. Otras: `img_setpad.py IMAGEN 2` (mando estándar para probar), `img_setflag.py`, `img_hdr.py`
(tabla de parches), `img_box.py` (caja negra de un volcado).

**3. Hablar con la placa** (scripts en `tools/board/`):

| Mueble | Raspberry (WiPi) | NetDIMM |
|---|---|---|
| Crazy Taxi | **192.168.68.251** (antes .60, cambiada el 2026-11-19) | 10.0.0.4 |
| Estándar (palancas) | **192.168.68.250** (antes .59, cambiada el 2026-11-11) | 10.0.0.3 |

- desde un PC de la red del usuario: `PIHOST=… PIPASS=… python3 pi.py 'ORDEN'` y `piput.py LOCAL REMOTO`
  (paramiko; sin él, `pissh.sh` y `piup.sh`: receta 11);
- en la Pi: `pk.py IP DIR[:N]` (leer memoria con el juego en marcha), `pp.py IP DIR=VALOR` (escribir) y
  `nohup python3 dcl.py BASE.bin.gz LOADER.bin IP FLAGS > /tmp/dcl.log 2>&1 &` (imagen de prueba = BASE con otro
  loader y flags añadidos; mirar `/tmp/dcl.log` hasta `netdimm_send rc 0`). Para cargar por SSH sin que muera al cerrar
  la sesión: `setsid nohup … &`.
- No usar `pkill -f X` en una orden cuyo propio texto contiene X (se mata a sí misma), ni `pgrep -f` sin el truco
  `[x]` (`pkill -f "[t]imehack.py"`).
- Lectura en directo de un homebrew de KallistiOS con `NAOMI_HOST`: `pi/live.py` de
  [naomi-pi-tools](https://github.com/0skarzer0/naomi-pi-tools). No leer durante el arranque ni con `timehack.py` a la vez.

**4. Un juego se queda en negro en la placa y en Flycast va:** caja negra. `dcl.py JUEGO LOADER IP 0x20200`
(BLACKBOX + PCSAMPLE), esperar al cuelgue, cargar OTRA imagen sin `0x20000` y con residente ≥ `d93afaf`
(p. ej. `dc-ikaruga` o `dc-spf2x`), y `pk.py IP 0x8dda0000:8 0x8dda0020:16 0x8dda0400:32 0x8dda0800:16`.
`[1]` > 0 = hubo excepción: EXPEVT, SPC, SSR, TEA. Desensamblar el SPC (`sh-elf-objdump -d resident/resident.elf` si es
`0x8dc0…`, o el 1ST_READ del juego con `-b binary -m sh4 -EL --adjust-vma=0x8c010000`). Sin excepción: mirar los últimos
PC y hasta dónde llegaron los contadores. No apagar el mueble entre las dos cargas. Ojo: si el juego usa el TMU2 como
contador libre (TD6), las muestras de PC no valen. Causas ya vistas: un segundo programa del juego sin parchear
(receta 9b), lecturas grandes con interrupciones cortadas (`read_chunk` 4, como SF3 Double Impact y TD6), un vídeo en
streaming que espera la interrupción de fin de DMA (`DIMM_DMAIRQ` 0x80000, MSR), o un residente viejo (`newloader.py`).

**5. Poner la VMU a un juego ya convertido:** `python3 tools/addvmu.py VIEJA.bin.gz NUEVA.bin.gz app/loader.bin`
(si dice "old header layout": antes `tools/convhdr.py VIEJA TMP "TITULO" PADMAP`). Copiar a `/boot/roms/` y dar al
usuario las dos filas de CSV (my y csv2) con el nombre nuevo. **Cambiar solo el cargador y residente** de una imagen
ya hecha, sin el disco: `tools/newloader.py VIEJA NUEVA` (variables `FLAGS=`, `READ_CHUNK=`, `PAD=`). Añadir el
parche de un segundo programa del juego: `tools/addprograms.py IMAGEN.bin.gz DISCO [SALIDA]`.

**6. VMU en ficheros en una Raspberry nueva:** `wipi/README.md` (dos scripts a `/sbin/piforce/` y un cambio en
`wipiloader.py`, con copia `.orig`). Comprobar: `tail /var/log/dc2naomi_vmu.log` debe decir `sending … with …`,
`watching …` y, cuando el juego guarda, `saved … blocks […]`. El vigilante nuevo (sale si el fichero de estado ya no
lleva su PID) está instalado en las dos Pi (2026-11-19).

**6b. Partidas en la VMU (`tools/vmutool.py`, también `vmutool.exe`):** `vmutool.py import JUEGO.vmu PARTIDA.vmi`
(el `.VMS` al lado), `export`, `list`, `format`. **Regla del usuario: al crear un juego nuevo, buscar en
[bucanero/dreamcast-saves](https://github.com/bucanero/dreamcast-saves) una partida con todo desbloqueado de la misma
región y meterla en su `.vmu`.** Con el juego cargado en el mueble: `dc2naomi_vmu.py stop IP` (baja lo último), importar,
y volver a enviar con `dc2naomi_send.py`. En la Pi del Crazy Taxi la herramienta y las partidas están en `/root/vmu/`
(con las tarjetas anteriores en `*.orig` / `*.bak`). Ojo: algunas partidas traen opciones raras (la de F355 trae la
música a volumen 0).

**7. Al terminar cualquier cambio:** HANDOFF (+ historial) + README (agradecer todo lo usado, en el mismo commit en que se
empiece a usar, también lo que sirvió de inspiración), commit, push, y decir al usuario con claridad qué se ha probado
en placa y qué sólo en Flycast. **Regla del usuario: toda operación queda en GitHub** (receta aquí, herramienta en
`tools/`), para otras sesiones, otras IAs u otros usuarios.

**Qué hay en cada Pi:** NAOMI de palancas (.250) en [docs/pi250-juegos.md](docs/pi250-juegos.md); mueble Crazy Taxi (.251)
en [naomi-wheel-games/docs/pi60-juegos.md](https://github.com/0skarzer0/naomi-wheel-games/blob/main/docs/pi60-juegos.md)
(el archivo conserva el nombre de la IP antigua). Actualizarlos al tocar una Pi. Rehacer la lista con
`PIHOST=192.168.68.250 PIPASS=... python3 tools/board/picatalog.py docs/pi250-estado.csv` (vale también para la .251).

**8. Trabajar en el PC del usuario (shell Linux de la app de escritorio, carpeta `~/mnt/dc2naomi` =
`C:\Users\Usuario\Documents\dc2naomi`).** Cada orden dura como mucho 3 min y **lo que se deje en segundo plano
muere al acabar la orden**: convertir en primer plano, uno o dos juegos por orden (2 núcleos; 30-160 s por juego;
`GZIP_LEVEL=1` / nivel 1 si no da tiempo). En la carpeta del usuario **no se puede borrar** (`rm` da "Operation not
permitted"): mover lo sobrante a `_to_delete/` y decírselo. Clonar el repo en `~/dc2naomi-src` (fuera de `mnt`).
El usuario renombra lo entregado con el prefijo `dc-` (`dc-buzz_es_dc2naomi.bin.gz`): entregar ya así. No comprimir
`.gz` grandes en la Pi .250 (subtensión).

**8b. Regla del usuario (2026-11-12): los juegos con la música en pistas de audio de CD no le interesan por ahora**
(suenan sin música): **antes de convertir**, mirar las pistas (`disc.tracks`: varias de audio en la zona de
alta densidad de un GD, o pistas de audio en un `.cdi`; criba en lote: `tools/cddascan.py`); si las hay, avisarle y
**no convertirlo**. El conversor lo avisa en sus notas. Desde el 2026-11-19 el residente sí sabe tocar CD-DA (receta 16,
probado en placa con RoboCop), pero el conversor automático no la activa: preguntar al usuario antes de hacer un perfil
con CD-DA para un juego comercial.

**9. Lote de juegos para un mueble:** `python3 app/dc2naomi.py --cab joy|ct --batch JUEGO.chd|.gdi|.cdi` → al lado
`JUEGO_dc2naomi.bin.gz` y `.vmu`. Nombres cortos y sin comas (una coma rompe la fila del CSV): `mv`. Partida
desbloqueada en cada `.vmu` (receta 10). Filas de CSV (receta 12).

**9b. Juegos con varios programas** (Wacky Races, Test Drive Le Mans, MSR: `1ST_READ.BIN` es un cargador y el juego otro
programa en 0x8c010000): `other_programs()` de `app/dc2naomi.py` ya añade sus parches en el perfil automático; para una
imagen vieja, `tools/addprograms.py`. `2_DP.BIN` y `DP_BEXP3.BIN` son el navegador DreamPassport, no el juego.

**10. Partida con todo desbloqueado:** clon parcial de bucanero/dreamcast-saves y `tools/findsave.py SAVES palabra`
(lista cada `.VMI` con el **nombre del archivo que escribe el juego, que dice la región**: Soulcalibur `_MBU` USA /
`_MBE` Europa, Dynamite Cop `D_COP_US` / `D_COP_PL`, títulos en japonés = Japón); luego
`tools/vmutool.py import JUEGO.vmu PARTIDA.vmi --batch` y `list` para comprobarlo. Sin partida publicada (Super
Puzzle Fighter II X, Millennium Racer) la tarjeta se queda vacía: decírselo al usuario.

**11. Subir a una Raspberry sin paramiko** (p. ej. desde el PC del usuario): `PIHOST=… PIPASS=…
tools/board/pissh.sh 'ORDEN'` y `tools/board/piup.sh ARCHIVO...` (a `/boot/roms/`, reanudable: repetir hasta
`TODO_SUBIDO`; comprueba md5). La Pi no tiene `rsync`. Si ya había una versión, sustituirla con el mismo nombre deja
válida su fila del CSV.

**12. CSV del WiPi** (`/boot/config/romsinfo.csv`, 18 columnas): copia `romsinfo.csv.bak_*` antes de tocarlo,
**el archivo no acaba en salto de línea** (añadir uno antes de la fila), sólo ASCII, y luego
`python3 /sbin/piforce/importcsv.py /boot/config/romsinfo.csv /var/www/html/csv/romsinfo.csv`. Fila tipo:
`"Sega Naomi",NOMBRE.bin.gz,,,"Título (Dreamcast)","Corto\n(Dreamcast)",Homebrew,AÑO,Fighter,"AAMA - Green (Suitable
For All Ages)",Horizontal,"Digital (Stick)",Yes,No,generic,none,,NOMBRE.bin.gz` (géneros que usa: Fighter, Driving,
Shooter, Puzzle, Action, Miscellaneous, `Beat-'Em-Up`…). Si el usuario lo sube él, dejarle `filas_romsinfo.csv`.

**13. CD de autoarranque (`.cdi`):** entra directo en `dc2naomi.py` (`tools/cdi.py`; detalle en
[historial/cdi-y-recortes.md](docs/historial/cdi-y-recortes.md)). Comprobar la imagen contra el disco:
`tools/cmpimage.py DISCO IMAGEN.bin.gz`.

**14. Un juego no cabe en los 512 MB** (el conversor no recorta solo: proponer opciones al usuario y que decida):
mirar qué ocupa (`walk()` agrupado por carpeta y extensión; o `tools/discfiles.py JUEGO.chd [ORIG .SFD .AFS]`, que
además saca los archivos) y, de menos a más trabajo:
- relleno de un solo byte en un CDI: ya lo quita el conversor; un ripeo con relleno `00 01 02… FF` no tiene vídeos;
- música con un archivo por canal (`*L.P16` / `*R.P16`): en mono con
  `tools/withfiles.py - --alias "*R.P16=*L.P16" --cab joy --batch JUEGO.chd` (Soulcalibur 683 → 469 MB);
- vídeos Sofdec (`.SFD`): **recodificarlos (probado en placa: Rainbow Cotton)**, `tools/sfdinfo.py` para verlos,
  `tools/sfdre.py ORIG NUEVO/RUTA/X.SFD KBPS` por cada uno (0,9 Mbit/s si hace falta mucho, 2,5 si basta un poco), o
  todos de una vez, comprobados: `tools/sfdbatch.py ORIG NUEVO`; luego
  `GZIP_LEVEL=1 tools/withfiles.py NUEVO --cab joy --batch JUEGO.cdi`;
- quitar vídeos (`--alias "X.SFD=EL_MAS_CORTO.SFD"`): sólo si el usuario lo prefiere (con Rainbow Cotton no lo quiso);
- música/voces ADX dentro de `.AFS`: `tools/afsmono.py ORIG.AFS NUEVO/X.AFS [--half-rate]` (MSR);
- PCM sin comprimir de Rush 2049: `tools/rushstr.py` (mono) o compartir canciones con `--alias`.
Después, releer la imagen y comparar cada archivo (`tools/cmpimage.py`).

**15. Un homebrew de KallistiOS compilado por nosotros (Mario Kart 64, OutRun C2C, NesterDC):** compilarlo con la
KallistiOS parcheada de `homebrew/mk64/kos-680d1862-naomi_host.patch` y `-DNAOMI_HOST` en vez de parchear el binario
como en `or2006`/`or37`. El parche arregla en el código fuente PCTRA, cima de memoria, maple, bus G1, FIFO G2 ×2, DMA
del AICA, SR perdido en caché y vídeo, y mete un contestador de peeks propio con log y excepción en RAM (bloque `LIVE`
de `pi/live.py`). Para usar los 28 MB: `-D__KOS_GCC_32MB__`. Para otra versión de KOS, los cambios están todos bajo
`#ifdef NAOMI_HOST`. Scripts: `homebrew/mk64/build_mk64.sh`, `homebrew/nesterdc/build_nesterdc.sh`,
`homebrew/orc2cdc/README.md`. Detalle en [historial/homebrew-kallistios.md](docs/historial/homebrew-kallistios.md).
**Un programa de KallistiOS cerrado:** `tools/kosexports.py 1ST_READ_descifrado.bin` lista su tabla de exportaciones
(nombre → dirección: `maple_dma_addr` → `HOOKST`, `cdrom_init`, `g2_lock`, `vid_check_cable`) sin desensamblar a ciegas.
La frecuencia de vídeo la decide el cable que devuelva el parche de `vid_check_cable` (0 VGA = 31 kHz, 2 RGB = 15 kHz).
Un `1ST_READ.BIN` cifrado (MIL-CD) se descifra con `scramble -d` (utils de KOS) antes de meterlo en el disco.

**16. Música en CD-DA (`DIMM_CDDA`, 2026-11-19):** en el perfil, `"cdda": True` (y opcionales `"cdda_channels": (62,
63)`, `"cdda_ring": 0x1F0000`). `build_image.py` mete entonces la TOC entera y las pistas de audio (2352 bytes/sector)
detrás de la ranura de la VMU, y el residente toca PLAY/PLAY2/PAUSE/RELEASE/STOP en dos canales del AICA. Antes de
elegir canales y anillo, mirar qué usa el juego ([historial/cdda-robocop.md](docs/historial/cdda-robocop.md)). CHD: el
audio `cdfl` aún se lee como silencio (`chd.py`), así que de momento solo `.cdi` y `.gdi`. Un programa que dibuja con
bfont necesita además `DIMM_BFONT` (0x200000).

**17. Un juego Katana desconocido:** `findpatch.analyze()` (lo usa el programa) da parches de IP.BIN, cable (PDTRA y
AICA), gancho de maple y tiempos G1; coincide con todos los perfiles hechos a mano. Método manual y detalles en
[docs/arquitectura.md](docs/arquitectura.md) ("Cómo encontrar los parches"). Juegos con Windows CE (`0WINCEOS.BIN`):
solo Sega Rally 2 ([historial/sega-rally-2-wince.md](docs/historial/sega-rally-2-wince.md)); el programa los rechaza.
Un parche VGA de la comunidad puede traer fallos propios (`lb2fe`: posición vertical del modo 320×240).

## Mandos y flags (chuleta)

`pad_map` (`resident/resident.h`, `"pads"` en el perfil): 0 `ct` (Crazy Taxi 2, doble toque = salto), 1 `menu`,
2 `joy` (mueble estándar), 3 `pole` (Namco Museum), 4 `wheel` (**por defecto del mueble Crazy Taxi**), 5 `ysgw`,
6 `plane` (Space Harrier), 7 `ab2` (After Burner II), 8 `mk64`, 9 `wheelud` (TD6: palanca = arriba/abajo), 10 `nes`.

Flags más usados: `0x0004 NO_UBC` (**todos los perfiles**: el UBC cuelga la placa), `0x0008 DIAG`, `0x0200 PCSAMPLE`,
`0x0400 SYNCREAD` y `0x1000 NOIPBOOT` (KallistiOS), `0x0040 DMA` (lecturas por DMA G1: sirve en KallistiOS),
`0x8000 VMU`, `0x20000 BLACKBOX`, `0x40000 WINCE`, `0x80000 DMAIRQ`, `0x100000 CDDA`, `0x200000 BFONT`. Lista
completa y comentada: `resident/resident.h`. **No escribir nunca `PCTRA = 0x000a03f0`** (mata el TA de la NAOMI 2: era
la causa de los primeros cuelgues; [historial/placa-inicial.md](docs/historial/placa-inicial.md)).

## Estado de los juegos (2026-11-25)

✅ = funciona en la placa real. Lo que hay cargado en cada Pi, con más detalle: ver "Qué hay en cada Pi".

| Juego (perfil / imagen) | Estado | Mueble |
|---|---|---|
| Crazy Taxi 2 (US) `ct2h8` | ✅ terminado, con VMU en fichero | Crazy Taxi |
| Namco Museum (US) `nmus7` | ✅ terminado, con VMU (mandos `pole`) | Crazy Taxi |
| Yu Suzuki GW Vol. 1 `ysgw` y un juego por imagen (`outrun`, `hangon`, `powerdrift`, `afterburner2`, `spaceharrier`) | ✅ los cinco sueltos probados (Power Drift sin petardeo; After Burner II con mapa `ab2`) | Crazy Taxi |
| Daytona USA 2001 `daytona5` | ✅ con VMU (imagen hecha a mano; el programa aún no lo soporta) | Crazy Taxi |
| F355 `f355b`, 18 Wheeler `18wheeler2` | ✅ terminados, con VMU | Crazy Taxi |
| Sega Rally 2 (Windows CE) `sr2` | ✅ con VMU y modo de 30 FPS (sin música de carreras: CD-DA) | Crazy Taxi |
| Test Drive 6 | ✅ llega al menú (`read_chunk` 4, mandos `wheelud`) | Crazy Taxi |
| MSR v2, Test Drive Le Mans, Wacky Races (otros programas) | ✅ funcionan (confirmado por el usuario el 2026-11-25) | Crazy Taxi |
| SF Rush 2049 | ❌ menú lento tras START, sin resolver | Crazy Taxi |
| Airline Pilots (NAOMI original) | CAUTION 51: ponerlo a 1 PLAYER(S) en el test; mandos pendientes | Crazy Taxi |
| Mario Kart 64 (homebrew) `mk64` | ✅ funciona; la última imagen (palanca = salto) está subida | Crazy Taxi |
| OutRun C2C (homebrew de ArkRetro) `h-orc2c8_dc2naomict` | ✅ versión final aprobada en el mueble | Crazy Taxi |
| NesterDC `nesterdc` | arranca y el menú responde; las correcciones (letra, sonido, carpetas) sin probar | Crazy Taxi |
| NesterDC SE v1.1 `nesterse` | sin probar (binario KOS 1.1.8 sin `NAOMI_HOST`) | Crazy Taxi |
| Ikaruga (JP) `dc-ikaruga` | ✅ con VMU desbloqueada (mandos `joy`) | estándar |
| SF3 Double Impact `dc-sf3di` | ✅ menú y los dos juegos, con VMU | estándar |
| SSF2X (inglés, ComradeSnarky) `dc-ssf2x_en` | ✅ con VMU | estándar |
| Rainbow Cotton (inglés), Buzz Lightyear (es) | ✅ con los vídeos recodificados | estándar |
| RoboCop (DreamNeo CD 4.0) `robocop_dncd` / `robocop_dncd15` | ✅ con música CD-DA (31 y 15 kHz) | estándar |
| Super Puzzle Fighter II X `dc-spf2x` | se colgaba tras los logos; rehecha con `newloader.py`, sin reprobar | estándar |
| Last Blade 2 Final Edition (parche VGA) `lb2fe` | experimental (intro, título y menú en Flycast) | estándar |
| Resto de la .250 (lotes del 2026-11-11/12) | ver [docs/pi250-juegos.md](docs/pi250-juegos.md) | estándar |
| Virtua Tennis | sin terminar: llegó a "No VMU found" (2026-11-08, perfil antiguo) | — |
| Midway's Greatest Arcade Hits | no funciona | — |

## Pendiente

- Confirmar en placa: SPF2X rehecha, NesterDC corregido, NesterDC SE.
- Rush 2049 (menú lento), mandos de Airline Pilots.
- Si otra imagen vieja de la .250 se cuelga como SPF2X: `newloader.py` (dcop_es, kof02, motw, rcotton_en, sf3ts,
  soulcal, ysgw, buzz_es, ikaruga, ssf2x_en, toystory2_es llevan cargadores anteriores).
- Restos en las Pi sin decidir: fila huérfana `h-daytona3_dc2naomi.bin.gz` en el CSV de la .251; `kof02_dc2naomi.vmu`
  y `dc-lastblade2_dc2naomi.bin.gz` (sin fila) en la .250.
- OutRun C2C, Rev 2.9-b de ArkRetro (GDI en la carpeta del usuario, `outrun2/`): sin fuentes publicadas y con datos
  que ya no casan con `a689a9a`; aprovechable el coche ligero `COCHEnnL.DAT` (mismo `ORD7`, 25 % menos vértices) y
  los commits `25f60d0`/`7dfe8a9` (nuestro parche entra salvo el trozo de `arranque_hold`). Pedidas las fuentes
  (`homebrew/orc2cdc/issue_arkretro_fuentes29b.md`, comentario en ArkRetro/ORC2CDC#2 publicado por el usuario):
  esperar respuesta antes de rebasar.
- Ideas del usuario: un aviso visible de "guardado"; vibración → force feedback; versión en castellano de Mario Kart 64.

## Historial: dónde está cada cosa

El antiguo HANDOFF (2285 líneas) se repartió el 2026-11-25 sin quitar nada. Si un comentario del código o un documento
cita "HANDOFF, sección X", está en:

| Sección antigua | Archivo |
|---|---|
| Objetivo, El programa `dc2naomi`, Cómo funciona, Cabecera, Caja negra y `DIMM_VMU`, Cómo encontrar los parches, Notas de hardware, Formato de la cabecera (`convhdr.py`) | [docs/arquitectura.md](docs/arquitectura.md) |
| Estado (2026-11-09), Sesión 2026-11-04, Yu Suzuki GW (análisis), Placa real, Pruebas en Flycast, Crazy Taxi DC frente a NAOMI, Ikaruga y Virtua Tennis (DMA G2, g2cpu, DreamShell), CAUSA ENCONTRADA (PCTRA), SB_G2APRO, Compilar (antiguo), Siguientes pasos (2026-11-08), Depuración por la red | [docs/historial/placa-inicial.md](docs/historial/placa-inicial.md) |
| Namco Museum, Crazy Taxi 2 (`ct2`…`ct2h8`), Daytona, lote de lucha, SF3 Double Impact, SB_MDAPRO, VMU en ficheros, 18 Wheeler, F355, Ikaruga con VMU, SSF2X, Last Blade 2 FE, Fallos del 2026-11-19 (TD6, MSR, SPF2X, Airline Pilots, Rush 2049) | [docs/historial/juegos-katana.md](docs/historial/juegos-katana.md) |
| Yu Suzuki `ysgw6` y Yu Suzuki GW separado (Power Drift, After Burner II, luces) | [docs/historial/ysgw.md](docs/historial/ysgw.md) |
| Sega Rally 2 (Windows CE) | [docs/historial/sega-rally-2-wince.md](docs/historial/sega-rally-2-wince.md) |
| Lista de juegos del mueble estándar, lotes para la .250, `isosdream`, Bangai-O, criba de CD-DA, coches para el Crazy Taxi, Descartados por los mandos | [docs/historial/lotes.md](docs/historial/lotes.md) |
| Soporte de `.cdi`, Soulcalibur, Rainbow Cotton, Toy Story 2, Last Blade 2 (ripeo), coches con vídeos recodificados, MSR y Rush 2049 adelgazados | [docs/historial/cdi-y-recortes.md](docs/historial/cdi-y-recortes.md) |
| OutRun demo v37 y v24 (`or37`, `or2006`), Mario Kart 64, OutRun C2C (`orc2c3`…`orc2c8`), NesterDC y NesterDC SE | [docs/historial/homebrew-kallistios.md](docs/historial/homebrew-kallistios.md) |
| CD-DA en NAOMI y RoboCop (DreamNeo CD 4.0) | [docs/historial/cdda-robocop.md](docs/historial/cdda-robocop.md) |

En el historial la Pi del Crazy Taxi aparece como .60 (hoy .251) y la estándar a veces como .59 (hoy .250).
