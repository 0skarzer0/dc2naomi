# HANDOFF — dc2naomi (juegos de Dreamcast en NAOMI)

Documento de traspaso entre sesiones (personas o IAs). **Actualízalo en cada sesión.**

## Recetas (para quien continúe, persona o IA): lo que funciona, paso a paso

Leer esto antes de nada. Cada receta se ha hecho de verdad (1-7 el 2026-11-10; 8-14 el 2026-11-11/12).

**0. Reglas.** Nada con copyright al repositorio (ni imágenes, ni IP.BIN, ni BIOS). La contraseña de la Raspberry
no se escribe en ningún fichero: va en la variable `PIPASS`. Un juego sólo cuenta como probado si funciona en la
placa real (Flycast no tiene caché, ni excepciones de dirección, ni comprueba SB_MDAPRO). No decir "comprobado" sin
haberlo visto. Cada prueba en placa le cuesta tiempo al usuario: antes de enviar, probar en Flycast.

**1. Reconstruir el loader tras tocar `resident/` o `loader/`:** `bash app/make_loader.sh` → `app/loader.bin`.
Direcciones de las variables del residente: `sh-elf-nm -n resident/resident.elf` (cambian en cada compilación).

**2. Probar en Flycast:** `cd tools/flycast; FCBIN=RUTA/flycast FC_SYSM_RAM=1 FC_PEDALS=1 STEP=10 DUMP=1 bash
run1.sh IMAGEN.bin 45 NOMBRE` → `NOMBRE.png` (capturas) y `/tmp/ram.bin` (los 32 MB de RAM: la dirección
`0x8dXXXXXX` está en el desplazamiento `0x01XXXXXX`). Sin `NAOMI2=1`. La imagen va descomprimida.

**3. Hablar con la placa** (scripts en `tools/board/`; la Pi del mueble Crazy Taxi es 192.168.68.60 y su NetDIMM
10.0.0.4; la del mueble estándar **192.168.68.250** (antes .59, cambiada el 2026-11-11 por un choque de IP) y 10.0.0.3):
- desde un PC de la red del usuario: `PIHOST=… PIPASS=… python3 pi.py 'ORDEN'` y `piput.py LOCAL REMOTO`
  (paramiko; sin él, `pissh.sh` y `piup.sh`: receta 11);
- en la Pi: `pk.py IP DIR[:N]` (leer memoria con el juego en marcha) y
  `nohup python3 dcl.py BASE.bin.gz LOADER.bin IP FLAGS > /tmp/dcl.log 2>&1 &` (imagen de prueba = BASE con otro
  loader y flags añadidos; mirar `/tmp/dcl.log` hasta `netdimm_send rc 0`).
- No usar `pkill -f X` en una orden cuyo propio texto contiene X (se mata a sí misma), ni `pgrep -f` sin el truco
  `[x]`.

**4. Un juego se queda en negro en la placa y en Flycast va:** caja negra. `dcl.py JUEGO LOADER IP 0x20200`
(BLACKBOX + PCSAMPLE), esperar al cuelgue, cargar OTRA imagen sin `0x20000` y con residente ≥ `d93afaf`
(p. ej. `dcl.py /boot/roms/ysgw7_dc2naomi.bin.gz LOADER_ANTIGUO IP 0`), y
`pk.py IP 0x8dda0000:8 0x8dda0020:16 0x8dda0400:32 0x8dda0800:16`. `[1]` > 0 = hubo excepción: EXPEVT, SPC, SSR,
TEA. Desensamblar el SPC (`sh-elf-objdump -d resident/resident.elf` si es `0x8dc0…`, o el 1ST_READ del juego con
`-b binary -m sh4 -EL --adjust-vma=0x8c010000`). Sin excepción: mirar los últimos PC y hasta dónde llegaron los
contadores. No apagar el mueble entre las dos cargas.

**5. Poner la VMU a un juego ya convertido:** `python3 tools/addvmu.py VIEJA.bin.gz NUEVA.bin.gz app/loader.bin`
(si dice "old header layout": antes `tools/convhdr.py VIEJA TMP "TITULO" PADMAP`). Copiar a `/boot/roms/` y dar al
usuario las dos filas de CSV (my y csv2) con el nombre nuevo.

**6. VMU en ficheros en una Raspberry nueva:** `wipi/README.md` (dos scripts a `/sbin/piforce/` y un cambio en
`wipiloader.py`, con copia `.orig`). Comprobar: `tail /var/log/dc2naomi_vmu.log` debe decir `sending … with …`,
`watching …` y, cuando el juego guarda, `saved … blocks […]`.

**6b. Partidas en la VMU (`tools/vmutool.py`, también `vmutool.exe`):** `vmutool.py import JUEGO.vmu PARTIDA.vmi`
(el `.VMS` al lado), `export`, `list`, `format`. **Regla del usuario: al crear un juego nuevo, buscar en
[bucanero/dreamcast-saves](https://github.com/bucanero/dreamcast-saves) una partida con todo desbloqueado de la misma
región y meterla en su `.vmu`.** Con el juego cargado en el mueble: `dc2naomi_vmu.py stop IP` (baja lo último), importar,
y volver a enviar con `dc2naomi_send.py`. En la Pi del Crazy Taxi la herramienta y las partidas están en `/root/vmu/`
(con las tarjetas anteriores en `*.orig` / `*.bak`).

**7. Al terminar cualquier cambio:** HANDOFF + README (agradecer todo lo usado), commit, push, y decir al usuario
con claridad qué se ha probado en placa y qué sólo en Flycast. **Regla del usuario: toda operación queda en GitHub**
(receta aquí, herramienta en `tools/`), para otras sesiones, otras IAs u otros usuarios.

Recetas añadidas el 2026-11-11/12 (todas hechas de verdad en esa sesión):

**Qué hay en cada Pi:** NAOMI de palancas (.250) en [docs/pi250-juegos.md](docs/pi250-juegos.md); mueble Crazy Taxi (.60)
en [naomi-wheel-games/docs/pi60-juegos.md](https://github.com/0skarzer0/naomi-wheel-games/blob/main/docs/pi60-juegos.md). Actualizarlos al tocar una Pi.

**8. Trabajar en el PC del usuario (shell Linux de la app de escritorio, carpeta `~/mnt/dc2naomi` =
`C:\Users\Usuario\Documents\dc2naomi`).** Cada orden dura como mucho 3 min y **lo que se deje en segundo plano
muere al acabar la orden**: convertir en primer plano, uno o dos juegos por orden (2 núcleos; 30-160 s por juego;
`GZIP_LEVEL=1` / nivel 1 si no da tiempo). En la carpeta del usuario **no se puede borrar** (`rm` da "Operation not
permitted"): mover lo sobrante a `_to_delete/` y decírselo. Clonar el repo en `~/dc2naomi-src` (fuera de `mnt`).
El usuario renombra lo entregado con el prefijo `dc-` (`dc-buzz_es_dc2naomi.bin.gz`): entregar ya así.

**8b. Regla del usuario (2026-11-12): los juegos con la música en pistas de audio de CD no le interesan por ahora**
(suenan sin música): **antes de convertir**, mirar las pistas (`disc.tracks`: varias de audio en la zona de
alta densidad de un GD, o pistas de audio en un `.cdi`); si las hay, avisarle y **no convertirlo**. El conversor
lo avisa ahora en sus notas. Reproducir CD-DA queda para el futuro (Bangai-O es el candidato: sobra sitio).

**9. Lote de juegos para un mueble:** `python3 app/dc2naomi.py --cab joy|ct --batch JUEGO.chd|.gdi|.cdi` → al lado
`JUEGO_dc2naomi.bin.gz` y `.vmu`. Nombres cortos y sin comas (una coma rompe la fila del CSV): `mv`. Partida
desbloqueada en cada `.vmu` (receta 10). Filas de CSV (receta 12).

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

**13. CD de autoarranque (`.cdi`):** entra directo en `dc2naomi.py` (`tools/cdi.py`, sección "Soporte de .cdi").
Comprobar la imagen contra el disco: `tools/cmpimage.py DISCO IMAGEN.bin.gz`.

**14. Un juego no cabe en los 512 MB** (el conversor no recorta solo: proponer opciones al usuario y que decida):
mirar qué ocupa (`walk()` agrupado por carpeta y extensión) y, de menos a más trabajo:
- relleno de un solo byte en un CDI: ya lo quita el conversor;
- música con un archivo por canal (`*L.P16` / `*R.P16`): en mono con
  `tools/withfiles.py - --alias "*R.P16=*L.P16" --cab joy --batch JUEGO.chd` (Soulcalibur 683 → 469 MB);
- vídeos Sofdec (`.SFD`): **recodificarlos (probado en placa: Rainbow Cotton)**, `tools/sfdinfo.py` para verlos,
  `tools/sfdre.py ORIG NUEVO/RUTA/X.SFD KBPS` por cada uno (0,9 Mbit/s si hace falta mucho, 2,5 si basta un poco),
  comprobar imágenes / avisos / ADX idéntico (sección de Rainbow Cotton) y
  `GZIP_LEVEL=1 tools/withfiles.py NUEVO --cab joy --batch JUEGO.cdi`;
- para ver qué ocupa y sacar los archivos: `tools/discfiles.py JUEGO.chd [ORIG .SFD .AFS]`; todos los vídeos de un
  juego de una vez, comprobados: `tools/sfdbatch.py ORIG NUEVO`;
- quitar vídeos (`--alias "X.SFD=EL_MAS_CORTO.SFD"`): sólo si el usuario lo prefiere (con Rainbow Cotton no lo quiso).
- música/voces ADX dentro de `.AFS`: `tools/afsmono.py ORIG.AFS NUEVO/X.AFS [--half-rate]` (MSR, sección de MSR);
- PCM sin comprimir de Rush 2049: `tools/rushstr.py` (mono) o compartir canciones con `--alias`;
Después, releer la imagen y comparar cada archivo (como en las secciones de Soulcalibur, Rainbow Cotton y Buzz).

**15. Un homebrew de KallistiOS compilado por nosotros (Mario Kart 64, 2026-11-13):** compilarlo con la KallistiOS
parcheada de `homebrew/mk64/kos-680d1862-naomi_host.patch` y `-DNAOMI_HOST` en vez de parchear el binario como en
`or2006`/`or37`. El parche arregla en el código fuente todo lo que en esos perfiles son parches sueltos (PCTRA, cima de
memoria, maple, bus G1) y además cinco cosas que nadie había visto (FIFO G2 ×2, DMA del AICA, SR perdido en caché,
vídeo), y mete en el programa un contestador de peeks propio con log y excepción en RAM
(`pi/live.py` de [naomi-pi-tools](https://github.com/0skarzer0/naomi-pi-tools), bloque `LIVE`). Se aplica a la 680d1862; para otra versión de KOS, los cambios son pequeños y están todos
bajo `#ifdef NAOMI_HOST`. Detalle en la sección "Mario Kart 64".

**16. Música en CD-DA (`DIMM_CDDA`, 2026-11-19):** en el perfil, `"cdda": True` (y opcionales `"cdda_channels": (62,
63)`, `"cdda_ring": 0x1F0000`). `build_image.py` mete entonces la TOC entera (CD: pistas 1..N con su número) y las
pistas de audio (2352 bytes/sector, desde la primera FAD de audio) detrás de la ranura de la VMU, y el residente toca
PLAY/PLAY2/PAUSE/RELEASE/STOP en dos canales del AICA. Antes de elegir canales y anillo, mirar qué usa el juego (sección
"RoboCop"). Para un programa de KallistiOS cerrado: `tools/kosexports.py 1ST_READ_descifrado.bin` lista su tabla de
exportaciones (nombre → dirección) y da `cdrom_cdda_play`, `g2_*`, `vid_check_cable`... sin desensamblar a ciegas.
CHD: el audio `cdfl` aún se lee como silencio (`chd.py`), así que de momento solo `.cdi` y `.gdi`.

## Objetivo

Arrancar juegos de **Dreamcast** en una **NAOMI / NAOMI 2** por netboot (NetDIMM), sustituyendo la BIOS de
Dreamcast por un programa residente. Si funciona, sirve para recopilatorios (Yu Suzuki Game Works, Namco
Museum, Midway…) y ports (Wipeout, Mario Kart 64).

## Estado (2026-11-09)

| Juego | Placa real | Mueble |
|---|---|---|
| Crazy Taxi 2 (US) | ✅ **Terminado** (`ct2h7`, salto con doble toque); `ct2h8` = `ct2h7` + VMU en fichero (Flycast OK, placa pendiente) | Crazy Taxi |
| Ikaruga (JP) | ✅ **Terminado** (`ikaruga_joy`, mandos `joy`); ✅ **con VMU desbloqueada** (`dc-ikaruga`, 2026-11-12) | estándar |
| Namco Museum (US) | ✅ **Terminado** (`nmus6` sin VMU; `nmus7` con VMU en fichero; mandos `pole`) | Crazy Taxi |
| Yu Suzuki Game Works Vol. 1 (JP) | ✅ Funciona (mandos `menu`); Power Drift: el petardeo del sonido está resuelto (2026-11-11), salir con B = negro | Crazy Taxi |
| Daytona USA 2001 (US) | ✅ Funciona (`daytona3`); ✅ **VMU en fichero (`daytona5`) confirmada**: guarda, se carga otro juego, se vuelve a cargar y recupera la partida | Crazy Taxi |
| F355, 18 Wheeler | ✅ terminados: funcionan en placa con VMU (`f355b`, `18wheeler2`) | Crazy Taxi |
| KOF99, Last Blade 2, SF3 3rd Strike, SPF2X, SSF2X, KOF 2002, MotW | sin probar en placa (título en Flycast) | estándar |
| SF3 Double Impact | ❌ el hook no llega (menú que carga dos programas) | estándar |
| Virtua Tennis (US) | llegó a "No VMU found" (2026-11-08, perfil antiguo) | — |

## El programa `dc2naomi` (2026-11-09)

`app/dc2naomi.py` convierte un `.chd`/`.gdi` en `JUEGO_dc2naomi.bin.gz` sin herramientas externas. En Windows son
dos ejecutables del mismo código (PyInstaller, `.github/workflows/windows.yml`): **`dc2naomi.exe`** (mueble
estándar, `cab=joy`) y **`dc2naomict.exe`** (Crazy Taxi, `cab=ct`); el mueble sale del nombre del ejecutable
(o `--cab`). `--batch` = sin preguntas ni pausa. **No se ha publicado ninguna release** (la crea un tag `v*`).

- **`tools/chd.py`**: lector de CHD v5 propio (mapa con Huffman, códecs `cdlz`/`cdzl`; `cdfl` = audio, se lee como
  silencio). `gdi.ChdGdi` da la misma interfaz que `Gdi`; `gdi.open_disc()` elige. Verificado: 504.150 sectores de
  SF3 Double Impact idénticos a los de `chdman extractcd`, y `1ST_READ.BIN`/`IP.BIN`/pistas iguales en 7 CHD.
- **`tools/catalog.py`**: juego conocido = SHA-1 de los programas que parchea su perfil (`SIGNATURES`, hechas con
  `tools/gensig.py`, que también lee de las imágenes ya construidas). Estado por mueble: `ok` / `experimental` /
  `broken`, mandos y nota. Daytona (`MK-51037`) está en `UNSUPPORTED`: el perfil es `rebuild` (ffmpeg + genisoimage).
- **Juego desconocido** (o versión distinta): `findpatch.analyze()` → parches de IP.BIN estándar, cable (PDTRA y
  AICA), hook de maple (primer candidato) y tiempos G1 → SCRATCH. Comprobado: da **exactamente** los parches
  hechos a mano de kof02, motw, sf3ts, spf2x, ssf2x, kof99, lb2, f355, w18, sf3di e ikaruga (Namco: falta su
  TEXPATH; Daytona: parchea el cable de otra forma equivalente). Virtua Tennis así llega a "No VMU found" en Flycast.
- **TEXPATH no se aplica automáticamente:** findpatch lista los literales `0x11000000` cargados por `mov.l`, pero en
  Virtua Tennis cambiarlo dejó la pantalla sin texturas en Flycast. Ojo: **F355 y 18 Wheeler tienen ese literal**
  (`0x8c0ffa6c`, `0x8c17bf4c`) y nunca se les puso TEXPATH: pista para cuando se retomen.
- **Imagen idéntica:** SPF2X convertido con el programa = imagen hecha a mano (archivo y disco byte a byte).
- Juegos con Windows CE (`0WINCEOS.BIN`): rechazados con mensaje. Imagen > 512 MB: se genera con aviso.
- **`app/loader.bin`**: el loader + residente compilados (título `DC2NAOMI`; el programa escribe el del juego en
  las 8 copias de la cabecera NAOMI, `0x30 + 0x20*i`, únicos bytes que cambian con `-t`). **Regenerarlo con
  `app/make_loader.sh` cada vez que se toque `resident/` o `loader/`**, o el programa llevará el residente viejo.

**Mandos nuevos (residente, 2026-11-09):**
- `DIMM_PAD_WHEEL` (4, `"wheel"`), por defecto del mueble Crazy Taxi para juegos sin ajustar: START al soltar solo
  si no se tocó nada; con START apretado palanca = arriba/abajo, freno = X, acelerador = Y (los gatillos a 0);
  sin START palanca = B/A, pedales = gatillos R/L; volante = stick X y cruceta a tope.
- `joy`: además de la cruceta, el stick analógico va al extremo (juegos 3D que solo leen el stick). Ikaruga sigue
  arrancando en Flycast; no reprobado en placa.

Resumen de lo aprendido en placa (detalles en "Ikaruga y Virtua Tennis", abajo):
- **Loader + residente + NetDIMM funcionan en placa** (lo demuestra Virtua Tennis). Las lecturas PIO de la NetDIMM
  son perfectas (prueba `READTEST`).
- **El UBC (DBR) cuelga la placa**: todos los perfiles van con `flags 0x0004` (sin UBC).
- **La DMA G2 del canal AICA (canal 0) no termina nunca en la NAOMI** cuando la lanza un juego de Dreamcast
  (`ADST` se queda a 1). Es lo que para Ikaruga y muy probablemente Namco Museum (los dos cuelgan cargando sonido).
  Virtua Tennis sube su sonido por CPU y por eso arranca. Solución en curso: `g2cpu` (copia por CPU).
- **Virtua Athlete 2000** (hecho primero para Dreamcast y portado por SEGA a NAOMI) usa la misma función de DMA G2,
  instrucción a instrucción, que su versión NAOMI, y aun así se cuelga en placa: **el bloqueo está en el entorno que
  deja el cargador (o en algo que hace la BIOS/librería NAOMI antes del juego), no en el juego**.
- Balance: 1 juego con el sonido por CPU (arranca) frente a 4 con DMA G2 (Ikaruga, Virtua Athlete, y casi seguro
  Namco Museum y YSGW: ninguno arranca).

Sesión 2026-11-04:
- Analizado YSGW entero (abajo). Es el nuevo banco de pruebas.
- **Residente v2**: el disco se sirve **por rangos de sectores con sus FAD originales** (sin reconstruir la ISO),
  TOC real sacada del GDI, **parches protegidos por grupos** y **gancho de arranque de programa** con el UBC.
- `build_image.py` con perfiles por juego (`tools/games.py`) y lectura directa del `.gdi`.
- Toolchain: en el entorno de la nube los mirrors de GNU están bloqueados, así que no se puede usar kos-chain.
  **`tools/ubuntu-toolchain.sh`** monta KallistiOS con el `gcc-sh-elf` 13 de Ubuntu (cabecera de
  compatibilidad + `libc.a` sin los objetos que ya trae KOS). El loader compila y enlaza así.
- Flycast (`7adbf3c` + `mame4all-naomi/naomi/flycast/flycast-mie-naomi.patch`) compilado, pero **falta la BIOS
  de NAOMI (`naomi.zip`)** para probar. freetype se baja del espejo de GitHub (gitlab.freedesktop bloqueado).

## Cómo funciona

1. **`loader/`** (KallistiOS, `KOS_SUBARCH=naomi`): es lo que arranca la BIOS de NAOMI. Inicializa el
   hardware (MIE + JVS), copia el residente a los 16 MB altos (`0x8dc00000`) junto con una imagen de la
   flash de Dreamcast y salta a `boot()` del residente.
2. **`resident/`** (C freestanding, sin FPU ni divisiones): hace de BIOS de Dreamcast mientras corre el juego.
   - Syscalls: GD-ROM (lecturas servidas desde la NetDIMM por el puerto de cartucho `0xa05f7000`),
     sistema, fuentes, flash, misc. Comportamiento según el HLE de Flycast (reios).
   - **Hook de maple**: responde a las peticiones de mando del juego con las entradas JVS de la NAOMI.
   - Carga `IP.BIN` y `1ST_READ.BIN` desde la NetDIMM, aplica los parches y arranca el juego.
   - **Gancho de programa (v2)**: los canales A y B del UBC paran *después* de la primera instrucción en
     `hook_pc[0..1]` (por DBR → `dbr_hook` en `head.S` → `program_start()`), vuelve a aplicar la lista de
     parches e invalida la caché de instrucciones. Así se parchean también los programas que el juego carga
     por su cuenta (en YSGW: Power Drift y el LOADER).
   - Memoria: `RES_BASE 0x8dc00000`, pila `0x8dcffff0`, flash `0x8dd00000` (128 KB),
     buffers maple `0xadd40000` (sin caché), escrituras anuladas `0xadd7f000`, log `0x8dd80000`.
3. **`tools/build_image.py GAME SOURCE WORK loader.bin OUT.bin`**: monta la imagen.
   - `layout: gdi` (YSGW): todos los sectores no vacíos de las pistas de datos de alta densidad, en hasta
     4 rangos, con su FAD original. TOC = pistas del GDI.
   - `layout: rebuild` (Daytona): ISO compacta desde LBA 45000 y música recodificada.
   - Crea la flash (región/idioma del perfil) y la tabla de parches. **Lee el valor original de cada
     parche en los ficheros del disco** y falla si no cuadra.

### Cabecera del archivo (`struct dimm_header`, versión 2, "YDCG" "IMG2")

Rangos de sectores `{fad, count, offset}`, `ip_fad`, `boot_fad/size`, TOC (`first_track`, `tracks[]`,
`leadout`), `flags` (`1` = muestreador de PC en pantalla, `2` = sin gancho), `hook_pc[2]` y 64 parches
`{addr, kind, value, expect}`:

- `CHECK` (1): abre un grupo; si `*(u32*)addr != value` se salta el grupo entero.
- `W16` (2) / `W32` (4): escribe solo si el contenido actual es `expect` (`| 0x80` = siempre).
- `value = 0xffffffff` en W32 = dirección del hook de maple del residente.
- `value = 0xfffffffe / 0xfffffffd` (`PATCH_G2CHK0/4`) = `g2chk0/4`: espera del FIFO G2 (SB_FFST bit 0 / 4)
  con tiempo límite y filas 16-19 (diagnóstico).
- `value = 0xfffffffc` (`PATCH_G2CPU`) = `g2cpu`: sustituto de la función de arranque de DMA G2 de Shinobi
  (ver "La solución g2cpu").

`flags` (`resident.h`; `build_image.py` los añade con variables de entorno): `0x0001 SAMPLER` (UBC, cuelga la
placa), `0x0002 NO_HOOK`, `0x0004 NO_UBC`, `0x0008 DIAG`, `0x0010 MASKERR`, `0x0020 CH2TEST`,
`0x0040 DMA` (lecturas NetDIMM por DMA G1: no funcionó), `0x0080 READTEST`, `0x0100 G2IDLE`,
`0x0200 PCSAMPLE` (muestreador de PC por TMU2, sí funciona en placa).

## Yu Suzuki Game Works Vol. 1 (Japón) — análisis

Disco: pistas de datos 3 (LBA 45000) y 6 (LBA 445087); en la pista 3 solo hay datos en 45000–45026
(IP.BIN, PVD, directorios); todos los ficheros están en la pista 6. 56 ficheros, 204 MB. Cabe en la
NetDIMM sin recodificar nada. Es el disco extra de Shenmue II (motor de Shenmue).

Programas y cómo se encadenan:

| Programa | Dónde corre | Qué es |
|---|---|---|
| `IP.BIN` | `0x8c008000` | Arranque Katana estándar: cable en `0x8c008382`, tabla de init con tiempos G1 |
| `1ST_READ.BIN` = monitor 64 KB + `YSC.BIN` | `0x8c010000` | El monitor copia `0x8c010100–0x8c014000` a `0x8c004000`, pone VBR `0x8c00f400`, pila `0xac00fc00` y arranca el menú (YSC) en `0x0c020000` |
| `YSC.BIN` (menú) | `0x8c020000` | Ejecuta OutRun, Hang-On, After Burner II y Space Harrier como overlays con sus propios drivers |
| `PD.BIN` (Power Drift) | `0x8c010000` | Programa aparte (compilador Hitachi). El menú carga `/loader.bin` en `0x8c800000`, copia `PD.BIN` a `0x8c010000`, pila `0x8cf00000` y salta |
| `LOADER.BIN` | `0x0c800000` | Al salir de PD (vía `mon.bin`): carga `1ST_READ.BIN` en `0x0c010000` y salta allí |

Puntos parcheados (`tools/games.py`, todos verificados contra el disco):

| Programa | Dirección | Original → nuevo | Qué |
|---|---|---|---|
| IP.BIN | `0x8c008382` | `mov.w @(4,r3),r0` → `mov #0,r0` | tipo de cable = VGA |
| IP.BIN | `0x8c00dab4`, `0x8c00dac0` | `0xa05f7490`, `0xa05f74a0` → RAM | tiempos G1 del GD-ROM (bus de la NetDIMM) |
| YSC | `0x8c1f58c6` | `mov.w @r1,r2` (PDTRA) → `mov #0,r2` | cable |
| YSC | `0x8c1f1f60` | `0x8c1f43a0` → hook | literal de la llamada "a física" antes de `SB_MDSTAR` |
| PD | `0x8c01b766` | `mov.w @r3,r4` → `mov #0,r4` | cable |
| PD | `0x8c032d44` | `0x8c034392` → hook | maple |
| LOADER | `0x8c80bca6` | `mov.w @r1,r2` → `mov #0,r2` | cable |
| LOADER | `0x8c8112dc` | `0x0c8135e0` → hook | maple |

`hook_pc = 0x8c010000, 0x0c010000`. Al arrancar PD el LOADER ya está en memoria, así que ese mismo
gancho parchea los dos. Simulado en Python: arranque → IP + YSC; entrada a PD → PD + LOADER; vuelta al
menú → YSC otra vez; ningún grupo toca un programa que no es el suyo.

Cosas a vigilar:
- El monitor tiene una rutina que escribe tiempos G1 (`0xa05f7490/94`, `0xa05f74a0`) y toca `0xa05f707c`,
  pero solo en el "modo 1" (`@0xac00f718`); el propio monitor pone el modo 2 al arrancar, que accede a
  `0xa3010000–0xa30100c0` (parece hardware de desarrollo: LEDs/DIP). En NAOMI esa zona puede responder
  distinto: **sospechoso si se cuelga justo al empezar**.
- El monitor usa `0x8c004000–0x8c010000`; no pisa los vectores de syscall (`0x8c0000b0–e0`) ni `0x8c0010f0`.
- Pistas de audio 4 y 5 (CDDA, 8 y 11 s): el residente no reproduce CDDA.
- Los overlays de cada juego (`OUTRUN.BIN`, `AB2.BIN`, `HANGON.EMU`, `HARRIER.PKS`) no tienen maple ni cable propios.

## Placa real (2026-11-05)

Con la imagen que funcionaba en Flycast: texto del loader correcto → pantalla de licencia de SEGA (la dibuja el
IP.BIN, así que residente + NetDIMM + arranque OK) → **negro justo al empezar 1ST_READ.BIN**, que es donde
saltaba el gancho UBC (DBR), lo único que Flycast no emula. Sospecha: en la placa la excepción no va a DBR
sino a VBR+0x100, que en ese momento es la zona de BIOS rellena de 0xff. **Daytona tenía puesto el muestreador,
que usa el mismo mecanismo: probablemente su pantalla negra era lo mismo.**
**Sin UBC también se queda en negro** (mismo punto). En los vídeos el monitor parece quedarse sin señal.
Imagen de diagnóstico `DIAG=1` (`flags | 0x0008`): cada 16 llamadas al residente (syscalls, hook de maple)
dibuja filas de bits en el framebuffer mostrado (0 latido, 1 llamadas GD, 2 última llamada GD, 3 sondeos maple,
4 último sector, 5 otras syscalls, 6 parches<<8|trampolines, 7 SPG_CONTROL, 8 FB_R_CTRL, 9 vueltas a VGA,
10 SPG_LOAD) y, si el juego deja los 31 kHz, vuelve a poner los tiempos VGA que tenía el loader.
**Resultado de DIAG en placa (foto 2026-11-05):** se congela con latido 79, 1044 llamadas GD, última EXEC_SERVER,
202 sondeos de maple, último sector `..4F81` (= FAD 544641, último de `SPRITE/TITLE.GZ`), 18 otras syscalls,
6 parches, **vídeo VGA intacto** (SPG_CONTROL 0x100, FB_R_CTRL 0x00800005, SPG_LOAD 0x020C0359), 0 vueltas a VGA.
En Flycast, en ese mismo punto (sector 544641, 18 otras syscalls, ~170 sondeos) el juego sigue y saca los logos
de SEGA/AM2. En placa el juego se para por completo (ni interrupciones de maple) antes del primer dibujado:
pinta a bloqueo de bus o de una DMA (TA/PVR, AICA/G2). No es el modo de vídeo ni el UBC.
Las rutinas TA-DMA del motor (p. ej. YSC `0x8c21248e`) escriben CHCR2/SB_C2D* por su cuenta.
`SAMPLER=1` (`ysgw_pc.bin`) en placa: negro justo tras la licencia, sin filas → **el UBC/DBR cuelga la placa
real** (confirmado; probablemente también la pantalla negra de Daytona). Sin UBC se llega más lejos (DIAG).
En Flycast nada cambia hacia los ~200 sondeos (TA-DMA ~1,5 por sondeo en toda la fase negra, sin registros
nuevos tras los del AICA en el sondeo 13; todas las lecturas GD a RAM; IML*EXT = 0). El juego sí habilita
**interrupciones de error del PVR en nivel 6 (IML6ERR = 0x0e)**, que Flycast no genera: sospechoso.
Imagen `DIAG=1 MASKERR=1` (`ysgw_diag2.bin`): mantiene IML2/4/6ERR a 0 en cada llamada al residente y añade
filas 11 ISTERR, 12 último ISTERR no nulo, 13 veces visto, 14 ISTNRM, 15 ISTEXT.
**Resultado DIAG2 en placa:** mismo cuelgue (1133 GD, 209 maple, sector ..4F81) con **ISTERR = 0x10 = "TA: illegal
parameter"**, pendiente desde mucho antes del cuelgue (contador de "veces visto" en centenares). En Flycast la
máquina de estados del TA no ve ninguna transición ilegal y ningún PCW lleva el bit 27 (comando ELAN de NAOMI 2).
El juego usa mucho la **ruta directa de texturas del canal 2 (`0x11xxxxxx`, LMMODE 0)**: subidas al principio y en
los sondeos 1, 51 y 61. Hipótesis: en la NAOMI 2 esa ruta no llega a la VRAM y acaba en el TA (igual que el
`pvr_txr_load_dma` colgado de Cannonball). Imagen `CH2TEST=1` (`ysgw_ch2.bin`): antes del juego hace 3 DMA de 64 bytes
(A 0x11600000 LMMODE 0, B 0x13600000, C 0x11600000 LMMODE 1) y dibuja estado / ISTERR / primera palabra leída
(filas 0-2, 4-6, 8-10) durante ~15 s. En Flycast: TE + fin de ch2, ISTERR 0, datos correctos en las tres.
CCR: el propio juego lo pone (`0x90d` en `0x8c1f7002`), así que no influye lo que deje el residente.

**Resultado CH2TEST en placa (NAOMI 2, 2026-11-06):** A `0x11600000` LMMODE0=0 → la DMA termina (TE, fin de
ch2, ISTERR 0) pero **no llega nada a la VRAM** (0/16, palabra 0). B `0x13600000` (LMMODE1=0) → 16/16 correcto.
C `0x11600000` LMMODE0=1 → 16/16 en la vista de 32 bits. **En la NAOMI 2 la ruta directa de texturas por 0x11 con
LMMODE0=0 no funciona; su réplica 0x13 sí** (y en Dreamcast es la misma ruta con LMMODE1). Probablemente es también
lo que colgaba `pvr_txr_load_dma` en Cannonball.
Arreglo (`TEXPATH`, `PATCH_R4FIX`): literales de destino `0x11000000` → `0x13000000` (YSC `0x8c2151b0`, PD
`0x8c02a404`, LOADER `0x8c822b4c`) y las 6 llamadas a la función que encola DMA del menú (`0x8c2122a0`, destino en
r4) pasan por un stub del residente (`r4fix0..3`, head.S) que cambia 0x11xxxxxx por 0x13xxxxxx. En Flycast, tras
el arreglo, todas las DMA de textura del juego van a 0x13 (las 50 a 0x11 que quedan son de la BIOS de NAOMI) y no
hay escrituras por store queue a la ruta de texturas. Pendiente: overlays (OutRun, After Burner, Hang-On, Space
Harrier) — tienen literales 0x11/0x13 propios (`OUTRUN.BIN` 0x4ddb0, `BURNER/PROG.BIN` 0x231a8, 0x24b3c, 0x31458,
`HANGON.EMU` 0xca984); falta saber dónde se cargan.
**Placa, tras el arreglo de texturas (2026-11-06):** la normal y DIAG (sin MASKERR) siguen en negro tras el logo
de SEGA; DIAG no llega a pintar filas en 10 intentos (ya antes era intermitente sin MASKERR). DIAG2 (DIAG+MASKERR,
sin arreglo) otra vez, decodificado: 0x53 latidos, 1117 llamadas GD, última 0x2c0? , 193 sondeos maple, sector
…4f81, parches 6/tramp 0, SPG_CONTROL 0x100, FB_R_CTRL 0x800004, SPG_LOAD 0x020c0378, **ISTERR 0x10** (visto 1260
veces), ISTNRM 0xc0001030, ISTEXT 0x8. Igual que la vez anterior. Hipótesis: sin MASKERR el error 0x10 (parámetro
ilegal del TA) dispara la rutina de error del juego y se para antes; el error del TA no es el de las texturas.
Siguientes imágenes: `ysgw_diag3` (DIAG+MASKERR con arreglo; fila 9 = nº de llamada GD del primer ISTERR con
MASKERR; filas cada 4 llamadas), `ysgw_diag3_tex` (igual sin R4FIX, `NOR4FIX=1`) y `ysgw_tex` (normal sin R4FIX).
`NOFIX=1` quita todo el arreglo. En Flycast las DIAG dejan la pantalla en negro (sólo filas) aunque el juego sigue.
YSGW lleva ahora `flags = 0x0004` (sin UBC): los parches van por trampolines y por la revisión en cada llamada
al GD-ROM. Pendiente de confirmar en placa. El muestreador (`SAMPLER=1`) queda en entredicho por lo mismo.

## Pruebas en Flycast (2026-11-05)

Resultado: **YSGW funciona en Flycast** en modo NAOMI 1 con la BIOS de exportación `epr-21578e`: logos de NAOMI y
SEGA → título "PRESS START BUTTON" → menú de juegos → Power Drift (programa aparte) arranca y se juega
(acelerador, volante, pausa con START largo).

La primera imagen que se probó en placa (pantalla negra) tenía dos fallos de **compilación de KallistiOS**, no
del cargador:
1. KallistiOS se había compilado para Dreamcast (`KOS_SUBARCH` sin poner): el loader quedaba enlazado en
   `0x8c010000` y pisaba el código de copia de la BIOS de NAOMI (excepción con BL=1 en `0xac0195xx`). Los
   programas de NAOMI van en **`0x8c020000`** (`LOAD_OFFSET`); `tools/ubuntu-toolchain.sh` ahora lo comprueba.
2. `aligned_alloc` de newlib 3.3 ↔ `posix_memalign` de KOS: recursión infinita (la pila se comía la RAM).

Cambios del residente en esta sesión:
- **Revisión de parches en cada syscall de GD-ROM** (`patch_poll`): Flycast **no emula el UBC** (solo guarda
  sus registros), así que el gancho de `hook_pc` nunca salta allí.
- **Trampolines** (`PATCH_TRAMP`, hasta 4): el literal del salto con el que un programa lanza al siguiente se
  cambia por un trampolín del residente, que aplica los parches y salta al destino original. Imprescindible
  para Power Drift: inicializa su driver maple antes de su primera llamada al GD-ROM, y si el hook llega tarde
  el juego ha visto el MIE en lugar de un mando y no responde. En YSGW: menú → PD (`0x8c053688`) y
  LOADER → 1ST_READ (`0x8c800480`).

Herramientas (`tools/flycast/`):
- `flycast-naomi-bios.patch` sobre Flycast `7adbf3c` (además del parche MIE de `mame4all-naomi`): activa
  `epr-21578e` en el juego de BIOS "naomi" (Flycast la tiene comentada) y, con `FC_NAOMI2=1`, arranca los
  `.bin` sueltos como NAOMI 2 (**no funciona**: la BIOS de NAOMI 2 no carga ningún `.bin`, ni el loader solo).
- `drive.py IMG NOMBRE pasos...`: Flycast sin pantalla guiado por lo que se ve (`menu` = START hasta que
  aparece el menú, `key:K:seg`, `hold:K:seg`, `wait:seg`, `dump`). Teclas por defecto: Return = START,
  flechas, J/L volante, `FC_PEDALS=1` + K = acelerador. START corto (< 20 fotogramas) = botón A.
- `run1.sh`, `pcwatch.sh` (PC con gdb), `ramlog.py RAM.bin` (log y estado del residente en un volcado).
- `FC_MIE_NODEVINFO` hace que la BIOS de NAOMI espere al MIE para siempre: no definirla (ni vacía).

## Namco Museum (USA) — juego de prueba pequeño (2026-11-06)
Perfil `nmus`: un solo programa (1ST_READ.BIN 1.7 MB en 0x8c010000, Shinobi 1.43 + KAMUI2 de 1999), imagen de
5.7 MB. Parches: IP.BIN como YSGW (cable + tabla de tiempos G1); cable `0x8c0a8782` (mov.w @r3,r4 → mov #0,r4);
maple `0x8c02e860` (literal de la función 0x8c02feb6 `and 0x0fffffff` antes de SB_MDSTAR); textura
`0x8c01a0c0` 0x11000000 → TEXPATH. El juego no escribe tiempos G1. En Flycast arranca a la primera: logos,
menú y Pac-Man; en esa prueba no hace ninguna DMA de textura propia (sólo al TA, 0x10). Imágenes
`nmus_dc2naomi` y `nmus_diag` (DIAG+MASKERR). Sirve para separar fallos del cargador de fallos de YSGW.

**Placa (2026-11-06):** `nmus` en negro tras el logo de SEGA. `nmus_diag`: congelado (mismas filas a los 9 y 12 s)
tras 80 llamadas GD, último sector 0x8566f (STREAM.MLT; antes MANATEE.DRV, el driver de sonido), última llamada
0x280 (bucle del servidor GD), 51 sondeos maple, 6 parches, primer error ASIC en la llamada 23 (valor ilegible:
las filas 12-15 salen desplazadas). En Flycast (traza `-DGDTRACE` en resident/Makefile) tras STREAM.MLT hay 35
llamadas 0x280 y luego lee DATA0.BLT; en la placa hay 47 y todo se para (ni GD ni maple): bucle con interrupciones
enmascaradas. Sospechoso: la librería G2 de Shinobi 1.43 (0x8c0a8fec lectura/escritura de 4 bytes del AICA, usada
para ARMRST 0xa0702c00 en 0x8c020f60/0x8c020fdc) enmascara interrupciones y espera en 0x8c0a9878 a que
SB_FFST (0xa05f688c) bit 5 se ponga a 0; YSGW y KOS miran los bits 0 y 4. Parche 0x8c0a9944 tst #32 → tst #0.
Imágenes `nmus2` y `nmus2_diag`. DIAG con MASKERR ahora: fila 7 = SB_FFST, fila 10 = ISTERR del primer error,
fila 11 = último ISTERR (las filas 0-11 se leen bien en el monitor).

**Crazy Taxi DC frente a NAOMI (2026-11-06)** (detalle en naomi-wheel-games `docs/crazy-taxi-dreamcast-vs-naomi.md`):
la versión NAOMI de SEGA usa el mismo Kamui con `LMMODE0 = 0` y DMA ch2 a `0x11000000` → esa ruta funciona en NAOMI,
así que el CH2TEST tenía un fallo de diseño (el caso A fue el primero, sin reinicio del TA; B y C después de uno).
`CH2TEST` ahora: filas 0-2 = A sin reinicio previo, 4-6 = A tras reinicio del TA, 8-10 = B (0x13). Imagen
`nmus_ch2`. Si A2 funciona, TEXPATH/R4FIX sobran y el problema era el estado del TA. La tabla de inicialización de
Holly (`0xa05f6800-0xa05f7c80`) es idéntica en las dos versiones. La NAOMI no lleva Shinobi/syG2; CT1 y CT2 de DC
esperan los bits 0 y 4 de SB_FFST, Namco Museum (Shinobi 1.43) el bit 5.

**Crazy Taxi 2 (USA)**, perfil `ct2` (2026-11-06): sólo parches de arranque (IP.BIN + cable `0x8c15e656`). Imagen
152,5 MB. En Flycast llega al logo de SEGA y a la pantalla de tarjetas de memoria (no responde a los mandos: el
driver maple llama a su función de dirección física `0x8c16852e` con bsr desde `0x8c167666` y `0x8c1678ae`, sin
literal; habría que parchear esos bsr). Usa los bits 0 y 4 de SB_FFST.

**Ikaruga (Japón)**, perfil `ikaruga` (2026-11-06): sólo arranque (IP.BIN + cable `0x8c04d0e4` mov.w @r3,r0 → mov #0,r0).
Imagen 36,6 MB; en Flycast llega al título (斑鳩). La versión NAOMI (GDL-0010, imagen DIMM de 32 MB, programa
principal rom 0x0-0x100000 → 0x8c020000) lleva la misma Shinobi (cvFs/gdCi 1.03, syMng 1.04) más "NAOMI LIBRARY
FOR AM" 2.22, y su espera de SB_FFST mira los bits 0 y 4 igual que la de Dreamcast: más indicios de que el bit 5
de Namco Museum es el problema. También usa DMA de texturas a 0x11000000.

**Namco Museum con el residente sin PCTRA (2026-11-09):** como YSGW ya funciona sólo con quitar la escritura de
PCTRA, el parche de SB_FFST bit 5 (`0x8c0a9944`) deja de ser parte de `nmus` y pasa a un perfil aparte, `nmus_ffst`.
Las dos llevan mandos `menu` (como YSGW). Imágenes `nmus3` (sin el parche) y `nmus3_ffst` (con él): probar primero
`nmus3`.

**Ikaruga para mueble NAOMI estándar (2026-11-09):** mandos `joy` (`pad_map` 2): palanca = cruceta, START = START,
botones 1-6 = A B X Y L R (L/R a fondo); el jugador 2 (JVS P2, `jvs.p2` = bytes 30-31 de la respuesta del MIE) en
el puerto maple B, que ahora también contesta (sólo con este reparto). Imágenes `ikaruga_joy` (perfil `ikaruga`,
sin más parches que antes) e `ikaruga_joy_g2cpu` (+ `drvpatch.py`): el cuelgue de la DMA G2 se diagnosticó con la
escritura de PCTRA aún puesta, así que probar primero la normal.

**Daytona USA 2001, `daytona3` (2026-11-09):** reconstruida con el residente actual (sin PCTRA, SB_MDAPRO abierto),
mandos `menu` y los tiempos G1 de su 1ST_READ (`0x8c1f3764/78/84`) a SCRATCH (antes iban a `0xac00fe00..`, dentro del
área de sistema de Katana). En Flycast llega a la pantalla de memory card. Pendiente de placa (antes: negro tras SEGA).
Su 1ST_READ lleva "NAOMI LIBRARY Ver 0.8 AM R&D" (NLOBJPUT/NLSPRITE) y no la librería de módem.

**Aparcados (2026-11-09, placa):** `18wheeler_novmu` (negro tras SEGA) y `f355_novmu` ("Now Loading" fijo): sin la
VMU fallan igual, así que la VMU no era la causa en estos dos (en Flycast los dos arrancan). También aparcados `kof99`
y `lb2`. Aparcado el pack ADC 1.7 (disco 1): menú + ~100 programas KallistiOS (MAME4ALL, emuladores de consolas),
cada uno con su driver maple y su detección de 32 MB: habría que parchearlos uno a uno; no lleva OpenBOR.

**Namco Museum: terminado** (2026-11-09, `nmus6` probado en el mueble: todo bien).

**Placa, 2026-11-09 (noche):** YSGW (`ysgw5`) funciona, Power Drift incluido. Pendiente para otro día: el sonido de
Power Drift petardea y al salir con B se queda en negro (no vuelve al menú). F355 con VMU se queda en "Now Loading" y
18 Wheeler con VMU en negro tras SEGA: la VMU emulada falla en placa en todos los juegos probados → `_katana_drive` ya
no la pone (imágenes `f355_novmu`, `18wheeler_novmu`). Ikaruga (`ikaruga_joy`): terminado.

**Juegos de lucha para mueble NAOMI estándar (mandos `joy`, sin VMU), 2026-11-09:** `tools/findpatch.py DIR` encuentra
los puntos (lectura de PDTRA, bits de cable que la BIOS de DC deja en el AICA `0xa0702c00` como Ikaruga, literal de
la función "a física" seguido de SB_MDST = 1, tiempos G1). Perfiles con `_katana_joy` en `games.py`. En Flycast
llegan al título / menú: `kof99` (42 pistas CDDA: sin música; DIMM_TRACKS sube a 64), `lb2` (911 MB: las 21 películas
de personaje `ZSFD/NN_*.SFD` apuntan a la más corta con la opción `alias` del builder, 418 MB; sin el parche del
cable AICA se quedaba en negro), `sf3ts` (1ST_READ de 14 MB), `spf2x`, `ssf2x`, `kof02` y `motw` (motor SNK de
LB2: mismas direcciones de cable). DIMM_RANGES sube a 32 (los ficheros omitidos parten los tramos) y el builder
tiene `blank` (ficheros fuera, leen ceros) y `alias` (registros de directorio reescritos).
**⭐ `sf3di` (SF III Double Impact): FUNCIONA EN PLACA (usuario, 2026-11-12 15:21: "funciona muy bien, la he estado
probando y no tiene fallos"; menú y los dos juegos, con VMU en fichero y la partida `v50554` desbloqueada).**
Antes se quedaba en el aviso de VMU: 1ST_READ solo es un cargador, y el menú y los juegos son programas aparte con su
propio driver de maple y su propia lectura del cable. Cómo se resolvió:
1. Sacar los programas del CHD (`gdi.open_disc(chd).read_file("GAMESEL/GAMESEL.BIN")`, etc.; en el PC del usuario).
2. **La dirección de carga de cada uno, por sus literales:** `findpatch.analyze` no encontraba gancho en GAMESEL a
   base 0x8c010000; buscando la función "a física" de 1ST_READ (`mov.l 0x0fffffff,r0; rts; and r4,r0`) por sus bytes
   aparece en GAMESEL en el desplazamiento 0x170a1e, y el código que escribe SB_MDSTAR la llama por un literal que vale
   `0x8ce70a1e` → **GAMESEL se carga en `0x8cd00000`**. SF3_1ST y SF3_2ND se cargan en `0x8c010000` (encima de
   1ST_READ: sus literales de gancho caen dentro del fichero a esa base).
3. Con `findpatch.analyze` a la base buena: cable (`mov.w @r3,r4` → `mov #0,r4`) y gancho de maple de cada programa.
4. Un grupo por programa en el perfil (`GAMES["sf3di"]["groups"] += [...]`): el residente aplica los grupos en cada
   llamada al GD-ROM, cada uno con su palabra de control, así que se parchea el programa que esté cargado.
**Microparadas (resuelto, usuario 15:51):** había una parada corta cada segundo en menús y partida, también con el
vigilante de VMU parado. Medido en placa (`gd_reads[]` del residente): el juego lee ~1 vez por segundo 32 sectores
(64 KB, ~44 KB/s) y cada `EXEC_SERVER` copiaba 32 sectores con las interrupciones cortadas. Nuevo campo de cabecera
**`dimm_header.read_chunk`** (perfil `"read_chunk"`; 0 = 32 de siempre) y variable `read_chunk` del residente
(probada en caliente con pokes: 32, 4, 16, 8): **`sf3di` usa 4 (8 KB)**. Con 4 "va mejor". (Un efecto de sonido que no
sonaba era un altavoz del mueble: no era el juego.)
Imagen en la Pi .250 (`dc-sf3di_dc2naomi.bin.gz`, md5 de la `.gz` `9657e964e17ac7f6c2ffce66a43db3be`; hecha cambiando
loader y la palabra 177 de la cabecera de la imagen probada) y su `.vmu` = la partida desbloqueada con lo guardado
en las pruebas (la anterior en `_test/sf3di_vmu_before_20261112.bak`). Copia en el PC: `otros/sf3di_files/`.
Nota: el CHD ya no está en `dreamcastisos/` del PC (el usuario lo ha movido).

**Namco Museum en placa (2026-11-09):** `nmus5_novmu` funciona bien (con el arreglo de SB_MDAPRO); con la VMU emulada
(`nmus5`) se queda en negro tras el logo de SEGA: **la VMU emulada falla en placa** (en Flycast va), sin investigar.
`nmus` queda sin VMU y con mandos `pole` (`pad_map` 3): como `menu`, pero acelerador = A, freno = B (digitales) y
palanca (cualquier sentido, sin START) = gatillo R, que en Pole Position cambia Low/High. Imagen `nmus6`.

**F355 Challenge y 18 Wheeler (USA), perfiles `f355` y `w18` (2026-11-09):** un programa cada uno (1ST_READ.BIN en
`0x8c010000`), driver maple de Shinobi con contexto en `+0x10bc`/`+0x10f4` (como Power Drift). Parches (función
`_katana_drive` en `games.py`): IP.BIN como siempre; cable `mov.w @r1,r2` de PDTRA (`0xff800030`) → `mov #0,r2`
(F355 `0x8c0de946`, 18W `0x8c15b2a6`); literal de la función "a física" antes de SB_MDSTAR → HOOK (F355
`0x8c0ec81c` → `0x8c0eeb20`, 18W `0x8c16a580` → `0x8c16c9c0`); el arranque de 1ST_READ escribe tiempos G1 en un
modo de configuración (`0x8c011046`): literales `0x8c011128/2c/30` → SCRATCH. Mandos `menu` y VMU. F355 pone
SB_MDAPRO = `0x6155404f`. En Flycast: F355 crea su fichero en la VMU y llega a PRESS START; 18 Wheeler llega al menú
de modos. **Ojo:** Flycast toma cualquier imagen llamada `f355*` o con título `F355...` por la recreativa F355 (pide
su BIOS): título `FERRARI 355 DC`, y para probar en Flycast renombrar el .bin.
`nmus_novmu` = Namco sin VMU (en placa `nmus5` con VMU queda en negro tras el logo de SEGA).

**⭐ SB_MDAPRO (2026-11-09): por qué Power Drift y Namco Museum no veían los mandos en placa.** `ysgw4_autostart`
en placa: Power Drift arranca y pausa solo (el gancho maple funciona y el juego lee nuestras respuestas), pero
volante/pedales/START reales no llegan: `jvs` no se actualiza. Power Drift, Namco Museum y F355 escriben SB_MDAPRO
(`0xa05f6c8c`) = `0x6155404f`: la DMA maple sólo puede tocar `0x0c000000-0x0cffffff`, y nuestra lista del MIE y su
búfer de respuesta están en RES_MAPLE (`0x0dd40000`): el hardware bloquea la DMA y el MIE nunca se sondea. Flycast no
comprueba MDAPRO (por eso allí funcionaba). Arreglo: `maple_hook` escribe `0x6155407f` (`0x0c000000-0x0fffffff`, el
valor de Ikaruga) en cada llamada. Imágenes `ysgw5`, `nmus5` (con VMU). Explica también que Namco se colgara en el
logo con la VMU (sus DMA maple nunca terminaban).

**Power Drift en placa no responde a START (2026-11-09):** en Flycast, con `ysgw3` (mandos `menu`), START funciona en
Power Drift (de la demo a la selección de circuito). En placa no reacciona ni a START ni a nada. `ysgw4`: el pulso de
START tras soltar pasa de 8 a 30 sondeos. `ysgw4_autostart` (`AUTOSTART=1`, flag `0x10000`): el mando pulsa START
solo 30 de cada 300 sondeos; si en placa Power Drift arranca carreras solo, el gancho maple de PD funciona y el fallo
es de tiempos; si no, PD no está usando nuestro mando en la placa. (Las filas DIAG no salen en PD ni en Flycast.)
PD guarda doble búfer de maple (`xor` en `0x10b8` del contexto) y escribe MDEN/MDST/MSYS con base `0xa05f6c00`.

**⭐ Por qué la VMU emulada colgaba la placa real (2026-11-10, resuelto).** Con `DIMM_VMU` todos los juegos se
quedaban en negro tras el logo de SEGA en placa (Namco, 18 Wheeler, Daytona) y en Flycast iban bien. Causa: con una
VMU el driver maple de Katana mete en la lista una **palabra de patrón** (bits 8-10 de la primera palabra ≠ 0:
reset/NOP), que va sola, sin dirección de respuesta ni cabecera. `maple_hook` avanzaba bien (`in += 1`) pero antes
**escribía "nada conectado" usando la palabra siguiente como dirección**: valía `0x00000001` → escritura de 32 bits en
`0xa0000001` → **excepción de dirección (EXPEVT 0x100)** dentro del residente (SPC en el bucle `r[i] = out[i]`), en
el sondeo 42, con la primera escritura del LCD. Flycast no da excepción por una escritura desalineada ni por escribir
en la ROM. Arreglo: sólo se contesta a tramas con patrón 0 y dirección alineada. `daytona4` (= `daytona3` + flag
`0x8000` + este residente): en placa, miles de sondeos, 0 excepciones, lee raíz/FAT/directorio de la VMU.
Descartado por el camino: caché (Daytona escribe la lista por P2 y pasa `0xac2e28a0`; `frame_at()` se queda por
seguridad) y el LCD (con VMU sólo-memoria moría igual).
**Confirmado en el mueble (2026-11-10):** Daytona con VMU pregunta si guarda 24 bloques, se acepta y el juego sigue
con normalidad. Primera vez que la VMU emulada funciona en placa. **Pendiente:** el programa (`app/dc2naomi.py`)
sigue forzando `vmu=False`; antes de activarla por defecto, probar en placa Namco Museum (`nmus5`), Crazy Taxi 2,
F355 y 18 Wheeler con VMU (estos dos fallaban también sin ella). La VMU está en RAM (`RES_VMU`): se pierde al apagar
o recargar.
**⭐ VMU en ficheros (2026-11-10, hecho y probado en placa con Namco Museum `nmus7`).** Ver `wipi/README.md`.
- Imagen: `dimm_header.vmu_offset` (palabra 176, antes `reserved[0]`) = hueco de 128 KB al final del archivo
  (`build_image.py` lo pone si el perfil lleva VMU; `tools/addvmu.py IN OUT [LOADER]` lo añade a una imagen hecha).
- Loader: lee el hueco; si es una tarjeta formateada (raíz `0x55`×16, FAT en 254) la copia a `RES_VMU` y deja
  "1GMI" en `RES_VMU_INFO+8`. Si no, vale la que hubiera en RAM o una nueva (`vmu_format`).
- Residente: `RES_VMU_INFO` = `0x8de20000`: `[0]` "VMUS", `[1]` nº de BLOCKWRITE desde el arranque, `[2]` 1 = tarjeta
  de la imagen; desde `+0x40`, por bloque, el valor de `[1]` en su última escritura.
- Pi (`/sbin/piforce`): `dc2naomi_send.py IP IMG` (= `netdimm_send --disable-crc` con el `.vmu` metido al vuelo con
  `FileBytes`, y deja `dc2naomi_vmu.py watch` en marcha); `dc2naomi_vmu.py` sondea cada 3 s, espera a que el
  contador se quede quieto y baja los bloques con secuencia mayor que la ya guardada (128 peeks por bloque, ~2,2 s).
  Un peek sin contestar tarda >2 s y se toma por fallo (6 seguidos = fin). `stop IP` (antes de cada envío) mata al
  vigilante y hace una última pasada. Estado en `/var/log/dc2naomi_vmu_IP.state`, log `/var/log/dc2naomi_vmu.log`.
- `wipiloader.py` de la Pi del Crazy Taxi (192.168.68.60) está modificado; el original es `wipiloader.py.orig`.
  La otra Pi (192.168.68.59, mueble estándar) tiene el mismo cambio desde el 2026-11-10 (mismos ficheros, mismo md5;
  su `wipiloader.py` original era idéntico al de la Pi del Crazy Taxi y está en `wipiloader.py.orig`).
- Probado en placa: Namco Museum crea `NAMCOMUS.SYS` al arrancar (10 bloques, idénticos a los de Flycast), "Save
  Mini-Game to VMU" (`PACIT_NM.VMU`, bloques 0-8) llega al fichero en 24 s, y al reenviar el juego arranca con la
  tarjeta del fichero (`[2]` = 1, contador 0). Era también la primera vez que Namco arranca con VMU en placa.
- **Prueba definitiva (2026-11-10, hecha por el usuario en el mueble Crazy Taxi):** `daytona5` guarda datos, se carga
  `nmus7` (Namco Museum) y después otra vez `daytona5`: arranca con los datos de la sesión anterior y los carga bien.
  Log de la Pi: `sending /boot/roms/daytona5_dc2naomi.bin.gz with /boot/roms/daytona5_dc2naomi.vmu at 0x1dd45000`.
  La VMU por fichero queda **funcionando de punta a punta** (envío con el `.vmu`, vigilante, recarga).
- **Siguiente (lo hace el usuario poco a poco):** reconvertir con VMU los juegos que se hicieron sin ella
  (`tools/addvmu.py` para una imagen ya hecha, o el programa 0.2, que la pone por defecto). Ojo: CT2, Ikaruga y
  YSGW se dieron por buenos sin VMU; si se les añade, probarlos de nuevo en placa.
- **`ct2h8` (2026-11-10):** `addvmu.py ct2h7_dc2naomi.bin.gz ct2h8_dc2naomi.bin.gz app/loader.bin` sobre la `ct2h7` de
  la Pi (md5 `2e3f5cb9…`). Sólo cambian 4 bytes de la cabecera tras el loader (flags `0x8004`, `vmu_offset`
  `0x9844000`); parches y mandos iguales. Flycast: mando en el puerto A y VMU en el Socket 1 con 200 bloques libres.
  En `/boot/roms/` de la Pi del Crazy Taxi (md5 `716ef768…`) con su fila en `/boot/config/romsinfo.csv` (copia de la de
  `ct2h7`; copia del CSV en `romsinfo.csv.bak_ct2h8`). Enviada con `dc2naomi_send.py` (49 s): el residente contesta
  (`RES_VMU_INFO` = "VMUS") y el vigilante de la VMU está en marcha. Mandos y guardado: pendiente de probar en el mueble.
- **Resuelto el mismo día:** el usuario puso una Pi 3 B+ también en el mueble Crazy Taxi; las dos van en 5 GHz a
  325 Mbit/s (~1,4 MB/s por SSH; 96 MB en 57 s). Las dos siguen marcando subtensión (`0x50005`).
- **Por qué la Pi del Crazy Taxi iba lenta (2026-11-10):** es una **Raspberry Pi 3 Model B** (sólo WiFi de 2,4 GHz: canal
  2457 MHz, 57,7 Mbit/s, ~0,5 MB/s medidos por SSH); la del mueble estándar es una **Pi 3 Model B+** en 5 GHz
  (292 Mbit/s, ~1,8 MB/s). El `eth0` de las dos está ocupado con la NetDIMM (10.0.0.1, 100 Mbit/s). La SD no es el
  cuello (16,5 MB/s de escritura). `vcgencmd get_throttled`: 0x50000 en la del CT y 0x50005 en la estándar
  (subtensión ahora mismo en la estándar). Subir 96 MB a la Pi del CT tarda ~3 min y las órdenes de la terminal de la
  app se cortan a los 180 s: subir por tramos (append) o copiar la imagen a la SD a mano.
- **`ct2h8` en placa (2026-11-10):** guarda en su `.vmu` (`C_TAXI02.SYS`, 20 bloques, bajado en ~47 s, dos veces).
- **Partidas con todo desbloqueado (2026-11-10, en la Pi del Crazy Taxi):** `ct2h8_dc2naomi.vmu` ← `v51513`
  (CT2 al 100 %; en Flycast desaparece "No Save File" y quedan 180 bloques libres) y `daytona5_dc2naomi.vmu` ←
  `v57953` ("ALL CARS", versión USA: cabecera "DAYTONA USA"; las "DAYTONA USA 2001" son japonesas; se descartó
  `v58535` porque cambia la configuración de mandos). Las tarjetas del usuario quedaron en `/root/vmu/*.orig`.
  Placa: CT2 reenviado y arranca con la tarjeta del fichero; falta que el usuario lo vea en el juego.
- Acceso a la Pi desde la sesión de Claude: la terminal de la app de escritorio solo llega a la red de casa si la
  cuenta tiene activado el acceso a **todos los dominios** (sin eso: "Network is unreachable").
- **Programa de Windows (2026-11-10, v0.2):** activa la VMU por defecto salvo `catalog.NO_VMU` (`ct2h`, `ikaruga`,
  `ysgw`: probados y buenos sin ella); `--vmu` / `--sin-vmu` fuerzan. Crea `JUEGO_dc2naomi[ct].vmu` vacío si no
  existe (`dc2naomi_vmu.blank()`) y el zip del workflow lleva `wipi/` (scripts + `LEEME_WIPI.txt`). Probado en
  Linux con Virtua Tennis (cabecera 0x8004, hueco de 128 KB, Flycast llega a la pantalla de título). Los juegos
  "experimentales" llevan la VMU sin haberse probado con ella en placa.
- Pendiente: probar apagando el mueble; Crazy Taxi 2, F355 y 18 Wheeler con VMU en placa.
- Cannonball (`outrun_1986.bin.gz`) NO sirve de banco de pruebas: es un programa NAOMI nativo, sin residente.

**Caja negra (`DIMM_BLACKBOX` 0x20000):** `0x8dda0000` por P2, por encima de lo que borra `boot()`: sobrevive al
reinicio de la placa y a cargar otra imagen. `[0]` "BOX!", `[1]` nº excepciones, `[2]/[3]` hooks maple
entrados/salidos, `[4]` tramas VMU, `[5]` listas malas, `[6]` muestras TMU2; `[8..]` 16 excepciones × 8 palabras
(EXPEVT, SPC, SSR, TEA, r15, PR, hook); `[0x100..]` primeras 32 tramas VMU × 4 (cabecera, función, recv,
hook | bloque); `[0x200..]` últimos 16 PC (con `0x0200`). Las excepciones se capturan con un desvío en `VBR+0x100`
(la entrada de Katana empieza con 5 `nop`; stub en `VBR+0x140`) a `exc_record()`. **Método:** cargar el juego con
`0x20000` (+`0x0200`), esperar al cuelgue, cargar otra imagen **sin** ese flag y con residente ≥ `d93afaf`
(`dcl.py BASE /tmp/loader.bin IP 0`) y leer `pk.py IP 0x8dda0000:8 0x8dda0020:16 0x8dda0400:32 0x8dda0800:16`.
Ojo: la `ysgw7` de `/boot/roms` de la Pi lleva un residente anterior (`2e03659`) que no lee RAM (`badadd00`); con el
juego colgado nadie contesta los peeks (ni con `0x0200` si murió por excepción) y los timeouts no rompen nada.
En esta sesión el fallo se leyó con `loader_vmu4` (la caja iba siempre activa); `0x20000` fue antes, sólo en pruebas,
"VMU sin LCD".

**VMU emulada (`DIMM_VMU` 0x8000, `"vmu": True` en el perfil; 2026-11-09):** el residente contesta como una Visual
Memory en la ranura 1 del mando del puerto A (el mando anuncia la subunidad 0x01): DEVINFO como Flycast
(`0x0e000000`, `0x403f7e7e`, `0x00100500`, `0x00410f00`), GETMEMINFO (la info del bloque raíz `+0x40`), BLOCKREAD
(130 palabras), BLOCKWRITE (fase = cuarto de 128 bytes), GETLASTERROR/SETCOND/LCD/reloj aceptados. 128 KB en RAM en
`RES_VMU` = `0x8de00000`, formateada al arrancar si no lo está (raíz 255, FAT 254, directorio 253-241, 200 bloques).
Se pierde al recargar la imagen o apagar. En Flycast, Namco Museum (`nmus4`) ya no muestra "No Memory Card found" y
va directo al menú (opciones con "Save Mini-Game to VMU"). Ikaruga en placa: **funciona, terminado**.

## Ikaruga y Virtua Tennis: la DMA G2 del AICA (2026-11-07 / 08)

### Ikaruga (Japón) — perfil `ikaruga`

Un solo programa: `1ST_READ.BIN` de 1 MB en `0x8c010000`, Shinobi (cvFs/gdCi 1.03, syMng 1.04), driver de sonido
ARM `MANATEE.DRV` y bancos `.MLT`. La versión NAOMI (GDL-0010) lleva la misma Shinobi más "NAOMI LIBRARY FOR AM"
2.22. Parches (todos en `tools/games.py`):

| Dónde | Dirección | Original → nuevo | Qué |
|---|---|---|---|
| IP.BIN | `0x8c008382`, `0x8c00dab4`, `0x8c00dac0` | como YSGW | cable VGA y tiempos G1 |
| 1ST_READ | `0x8c04d0e4` | `mov.w @r3,r0` (PDTRA) → `mov #0,r0` | cable |
| 1ST_READ | `0x8c04d05c` | `and #3,r0` → `mov #0,r0` | **el juego también lee el tipo de cable en el registro del AICA `0xa0702c00` (bits 9:8)**, que deja la BIOS de Dreamcast. En NAOMI vale 3 → modo compuesto de 15 kHz, que el monitor VGA no muestra |
| 1ST_READ | `0x8c048758` | literal `0x8c04ae50` → hook | maple (función "a física" antes de `SB_MDSTAR`) |

`tools/drvpatch.py IMAGEN [OFFSET]` cambia en `MANATEE.DRV` (dentro de la imagen ya montada, `0x96000` en Ikaruga)
las tres escrituras `mov r1,#0/#15` a `0x00802800` por `mov r1,#0x200` (bit `MEM8MB`), como hace KallistiOS en
hardware que no es una Dreamcast (`spu_ram_mode`). Imágenes `*_mem8`. No cambió nada en placa, pero se mantiene.

### El cuelgue de Ikaruga en placa

Síntoma: logo de SEGA (lo dibuja el IP.BIN) → negro. En Flycast llega al título.

Con el muestreador de PC por TMU2 (`PCSAMPLE`, filas 16-31) en placa: el juego da vueltas en
`0x8c050294` / `0x8c051376` y la DMA G2 del canal AICA está **arrancada y sin terminar**:
fila 26 = `ADST 1, ADEN 1, ADSUSP 0, ADTSEL 4 o 5`, interrupción "fin de DMA AICA" (ISTNRM bit 15) habilitada en
nivel 4 y **nunca pendiente**. `IML4NRM = 0x0007f000`. El puente de interrupciones (fila 30) nunca se activó,
porque no había ninguna interrupción pendiente que reenviar: el hardware no termina la transferencia.

Quién la lanza: la librería de sonido, en `0x8c04f8de` → **`0x8c04522c`** (arranque de DMA G2 de Shinobi,
r4 = descriptor, r5 = flag). Secuencia en Flycast (`FC_G2TRACE=1`): una DMA de prueba de la propia librería en
`0x8c045a70` (`EN=0`), luego `MANATEE.DRV` (0x9040 bytes a `0x00800000`), un comando de 0x20 bytes a
`0x00812200` y unas 15 subidas de bancos `.MLT` (`0x00818000`…), todas con `ADTSEL 5`.

Estructuras (Ikaruga, Shinobi):
- Descriptor: `[0]` canal, `[4]` dirección G2, `[8]` dirección SH4, `[12]` longitud | 0x80000000, `[16]` dirección
  (0 = SH4→G2), `[20]` TSEL, `[28]` callback, `[32]` su argumento, `[44]` ocupado, `[48]` terminado.
- Contexto: `*(0x8c0cf2f0)`; `*ctx` apunta a los registros (`0xa05f7800`, 0x20 por canal); `ctx+0xdc+canal*4`
  = transferencias empezadas, `ctx+0xec+canal*4` = terminadas.
- `0x8c04522c`: mira si el canal está ocupado (`0x8c044d48`: bit 0 de `@(24,regs)` = ADST) y si lo está devuelve
  `0x90180`; si no, purga la caché del origen (`0x8c0428ca`), escribe STAG/STAR/LEN/DIR/TSEL(|2 si r5)/EN=1,
  `desc[44]=1`, `ctx+0xdc++` y ST=1. Devuelve 0.
- Manejador de fin `0x8c044cbc(desc)` (registrado para los eventos 0xa60/0xa80/0xaa0/0xac0 en `0x8c045622`):
  EN=0, `desc[44]=0`, `desc[48]=1`, `ctx+0xec++`, borra `ISTNRM` bit `canal+15` y llama a `desc[28](desc[32])`.
- `0x8c04f8de` **apunta la transferencia en su cola después de que vuelva el arranque** (contador `+96` y anillo
  en `0x8c112df0`); el callback deshace esa anotación.
- `0x8c051370`: el cargador de `.MLT` hace `while (estado(handle) != 1)` (`0x8c050244`, lee `handle[8]`). Ese
  estado solo llega a 1 por la cadena de callbacks de fin de DMA.

### La solución g2cpu (perfil `ikaruga_g2cpu`)

Entrada de `0x8c04522c` → `mov.l @(4,pc),r0; jmp @r0; nop; nop; .long g2cpu` (`PATCH_G2CPU`). `g2cpu` (residente):
1. copia `desc[12] & 0x7fffffe0` bytes con la CPU. El origen SH4 se lee **por P1, con caché**, porque nos
   saltamos la purga de caché del juego (leyendo por P2 se copiaban datos viejos). El destino es el AICA por
   P2 (`0xa0800000+`), esperando al FIFO G2 cada 8 palabras;
2. hace la misma contabilidad que el arranque real (`desc[44]=1`, `ctx+0xdc++`) y mete el descriptor en una cola;
3. arranca TMU2 en el despachador del juego (`VBR+0x248`, prioridad 15, ~250 Hz). En cada tick se llama al
   manejador de fin del juego `0x8c044cbc(desc)` para una transferencia de la cola, como haría la interrupción.

**Por qué diferido**: llamando al manejador dentro de `g2cpu`, el callback corre antes de que `0x8c04f8de` apunte
la transferencia en su cola, y el juego se queda esperando para siempre. **En Flycast ese fallo se cuelga
exactamente en los mismos PC que la placa (`0x8c050294`/`0x8c051376`)**, lo que confirma qué espera el juego allí.
Con el fin diferido, Flycast llega al título **sin ninguna DMA G2 real** (solo la de prueba con `EN=0`).
En `_diag` las filas 20-22 son empezadas | terminadas<<16, última longitud y última dirección G2.

Probar en Flycast: `ikaruga_nosnd` (el arranque devuelve 0 sin callback) también se cuelga: el juego necesita el
fin de cada transferencia, no solo que no haya DMA.

### Pruebas en placa hechas con Ikaruga (todas con logo de SEGA → negro)

| Imagen | Qué probaba | Resultado |
|---|---|---|
| `ikaruga`, `_vga` | arranque + arreglo del cable del AICA (`0x8c04d05c`) | negro; el vídeo ya queda en VGA |
| `_maple` | hook de maple | negro (el hook funciona en Flycast) |
| `_dma` (`DMA`) | lecturas de la NetDIMM por DMA G1 | peor: el juego relee el directorio sin fin. Descartado |
| `_readtest` | toda la imagen por PIO dos veces y comparar | **lecturas perfectas** |
| `_g2` (`G2CHK0/4`) | esperas del FIFO G2 con tiempo límite | ninguna espera se atasca |
| `_g2idle` (`G2IDLE`) | PIO de la NetDIMM solo sin DMA G2 en curso | igual |
| `_nospu` (`NOSPU=1`) | el loader no inicializa el AICA ni la DMA G2 de KOS | igual |
| `_pc_diag` (`PCSAMPLE`) | muestreador de PC por TMU2 | **funciona en placa**: PC en `0x8c0502xx`/`0x8c051376` |
| `_aica_diag`, `_dmaor`, `_cpu`, `_bridge`, `_mem8` | registros AICA/DMAOR, disparo por CPU (TSEL), puente de interrupciones, modo 8 MB | DMA G2 sigue con ADST=1; DMAOR limpio; el puente nunca se activa |
| `_g2cpu` | sin DMA G2 (copia por CPU) | **pendiente** |

Descartado: el modo de vídeo, las lecturas de la NetDIMM, la DMAOR del SH4, interrupciones externas (ISTEXT),
las esperas del FIFO G2, la concurrencia PIO/DMA, la inicialización del AICA de KOS, `MEM8MB` y que la
interrupción exista pero no se entregue.

### Virtua Tennis (USA) — perfil `vt` — ✅ arranca en placa

Un programa de 2 MB en `0x8c010000`. Solo parches de arranque: IP.BIN y cable `0x8c1ea8aa` (`mov.w @r3,r4` →
`mov #0,r4`). Se eligió porque en Flycast sube el sonido al AICA **por CPU**, sin DMA G2 (la traza solo muestra la
DMA de preparación de la librería). **En placa, la normal y la diag llegan a "No VMU found in slot 1, port A"**
(2026-11-08, en las dos NAOMI del usuario). Es la prueba de que el loader, el residente, la NetDIMM y el vídeo
funcionan, y apunta a la DMA G2 del AICA como bloqueo de los demás. Falta el hook de maple para pulsar START.

### Comparación Dreamcast / NAOMI (Crazy Taxi, Virtua Tennis, Ikaruga)

Discos extraídos de las versiones NAOMI (imagen DIMM, ISO en `0x800000`, LBA base 45000). Las conversiones de SEGA
usan la misma Shinobi/Kamui; lo que cambia es lo que hace la BIOS (cable, flash, GD) y la librería "NAOMI LIBRARY
FOR AM". La tabla de inicialización de Holly es idéntica. No apareció ningún patrón de "protección" en el código del
juego: la diferencia observable es la DMA G2 del AICA.

### Herramientas añadidas

- `tools/flycast/flycast-dc2naomi-debug.patch` (Flycast `7adbf3c`, incluye `flycast-naomi-bios.patch`; el parche
  MIE de `mame4all-naomi` va aparte): `FC_G2TRACE=1` (cada arranque de DMA G2 con VBR/SR/PC/PR y registros,
  escrituras IMLxEXT, offsets PIO de la NetDIMM), `FC_EXT3=1` (ISTEXT bit 3 siempre a 1), `FC_NOIRL11=1` (sin
  interrupciones de nivel 4).
- Para probar sin pantalla: Xvfb + `flycast IMAGEN` + `import -window root` cada N s; volcado de los 32 MB de RAM
  con `gdb -p PID -batch -ex "dump binary memory ram.bin BASE BASE+0x2000000"` (BASE = `RAM(32 MB)` del log);
  las variables del residente se leen con `sh-elf-nm resident/resident.elf`.
- `tools/drvpatch.py` (arriba).
- Muestreador TMU2 (`PCSAMPLE=1`): filas 16 muestras, 17-24 últimos 8 PC, 25 SSR, 26 DMA G2 AICA, 27 ICR|IPRA,
  28 ISTNRM, 29 IML4NRM, 30 puente, 31 DMAOR. Instala su manejador en `VBR+0x248` (TMU2, INTEVT 0x440) cuando el
  VBR es el de Katana (`0x8c00f400`): el código de `VBR+0x600` del IP.BIN guarda INTEVT y salta al despachador de
  Shinobi, que llama al manejador de `VBR + 0x200 + (INTEVT-0x200)/8`.

Construir Ikaruga g2cpu:
```sh
./build.sh ikaruga_g2cpu ika/disc.gdi build/ikaruga_g2cpu.bin
DIAG=1 python3 tools/build_image.py ikaruga_g2cpu ika/disc.gdi build/ikaruga_g2cpu loader/loader.bin build/ikaruga_g2cpu_diag.bin
python3 tools/drvpatch.py build/ikaruga_g2cpu.bin && python3 tools/drvpatch.py build/ikaruga_g2cpu_diag.bin
gzip -k build/ikaruga_g2cpu.bin   # el nombre del .gz es el de romsinfo.csv (romname y audit_name)
```

### Resultados de placa del 2026-11-08 (tarde)

- **`ikaruga_g2cpu_diag`**: filas 21-22 leídas en el vídeo = `0x8001ef20` / `0x008f2e00`, la **6.ª** subida de la
  lista de Flycast. La copia por CPU funciona en placa (antes se paraba en la 1.ª), pero la fila 20 parece decir
  6 empezadas / 5 terminadas: el fin de la 6.ª no llega. La imagen `ikaruga_g2cpu_pc_diag` (muestreador + columna
  derecha con la fila 23 = etapa | en cola<<8 | ticks de TMU2<<16) está hecha pero sin probar.
- **`va_dc2naomi`**: negro tras el logo de SEGA. **`va_pc_diag`**: las filas del residente salen menos de un segundo
  sobre el logo y luego todo negro; las del muestreador no llegan a salir. El monitor (trifrecuencia) no pierde la
  señal: la imagen es negra, no un modo de vídeo distinto. O el juego apaga la salida de vídeo antes de cargar y se
  cuelga, o se cuelga antes de montar sus interrupciones. Siguiente diag útil: forzar la imagen encendida y pintar
  desde TMU2.
- Sin probar aún: `ikaruga_tsel0`, `va_tsel0` (ADTSEL = 0: arranque por CPU **sin** "suspend enable"; en placa
  ADSUSP bit 4, la petición de DMA del AICA, se leía 0, y en Flycast 1).

### Virtua Athlete 2000 (USA) — perfil `va`

Disco de 101 MB de ficheros (incluye Dream Passport). Un programa: `1ST_READ.BIN` 1,7 MB en `0x8c010000`.
Parches: IP.BIN como siempre y cable `0x8c19325a` (`mov.w @r3,r4` → `mov #0,r4`). La versión NAOMI (GDS-0019,
imagen de 112 MB; programa rom `0x0-0x1d0000` → `0x8c020000`, ISO en `0x800000`, base LBA 45000) lleva:

| | Dreamcast | NAOMI |
|---|---|---|
| Base | Shinobi 1.69 | Kunoichi Library for NAOMI 0.96 |
| syG2 | 1.02.00 | 1.02.01 |
| sd (sonido) | 2.02.07 | 2.02.11 |
| Otras | syBt, syHw, syCbl | syBtKn, syHwKn, syCblkn, syExtChkKn, "NAOMI LIBRARY FOR AM" 2.22 |

La función de arranque de DMA G2 (VA DC `0x8c1943xx`, NAOMI `0x8c1362xx`; Ikaruga DC `0x8c04522c`, NAOMI
`0x8c02af..`) es idéntica salvo literales. Literales de registros Holly que solo usa NAOMI: los del cartucho/NetDIMM
(`0x5f7000-14`, `0x5f703c`, `0x5f7068`) y tiempos G1 (`0x5f7480-b8`); los de G2 (`0x5f78xx`) son los mismos.
Ver qué hace la BIOS de NAOMI / Kunoichi con el AICA y el bus G2 antes del juego es el siguiente paso de fondo.

### Cómo predecir si un juego de Dreamcast cargará (hipótesis, 2026-11-08)

1. `FC_G2TRACE=1` en Flycast: si el juego sube su sonido por DMA G2 (líneas `G2DMA start` con `EN=1` tras la de
   prueba), hoy se cuelga en placa. Si no hay (Virtua Tennis), probablemente carga.
2. `strings 1ST_READ.BIN`: "NAOMI LIBRARY" o una librería de sonido propia (Virtua Tennis: `libsnd0.95`) son buena
   señal; `sd for DC` / `MANATEE.DRV` / audio64 suelen ir con DMA G2.

### Los juegos de coches (2026-11-08): criba y lote de 5

Dos familias de sonido, que coinciden con lo visto en placa:
- **SEGA AM**: `NAOMI LIBRARY … AM R&D` dentro del programa, driver `AICADRV.BIN` + `libsnd`, sonido subido
  **por CPU** (la traza `FC_G2TRACE` solo muestra la DMA de prueba con `EN=0`). Virtua Tennis ✅ (0.9),
  Crazy Taxi 2, Daytona USA 2001 y Yu Suzuki Game Works (0.8).
- **Kit estándar**: `MANATEE.DRV` + `sd for DC` / `.MLT`, sonido **por DMA G2**. Ikaruga ❌, Virtua Athlete ❌.
  (Crazy Taxi 2 y Daytona también llevan `MANATEE.DRV`, pero solo para el navegador Dream Passport `2_DP.BIN`.)
- Namco Museum (Shinobi 1.43): sin DMA G2 de sonido en 60 s de Flycast.

Lote para placa (normal + diag; diag = `DIAG=1 PCSAMPLE=1`, salvo YSGW = `DIAG=1 MASKERR=1` porque el muestreador
cuelga YSGW en Flycast: su monitor tiene otro despachador de interrupciones):

| Imagen | Flycast |
|---|---|
| `ct2` | pantalla de tarjetas de memoria |
| `daytona` (`layout: rebuild`, 65 músicas recodificadas a 32 kHz: 477 MB; `flags 0x0004` y tiempos G1 del IP.BIN) | logo ADX → tarjetas de memoria |
| `ysgw` | título |
| `nmus` | menú ("No Memory Card found") |

Cambios para el lote:
- **El residente pone a 0 (VGA) los bits 9:8 de `0xa0702c00`** al arrancar: la BIOS de Dreamcast deja ahí el tipo de
  cable; en NAOMI vale 3 (compuesto). Lo leen Ikaruga y Windows CE.
- `DIMM_TRACKS` 8 → 32 (Windows CE: 28 pistas) y `boot` en el perfil (`0WINCEOS.BIN`). `genisoimage` hace falta
  para `layout: rebuild` (`apt-get install genisoimage`).
- **Midway Greatest Arcade Hits Vol. 2** (perfil `mw2`, Windows CE): logo de Windows CE y Flycast cae a los ~15 s
  con "SH4 exception when blocked"; la zona de la BIOS (IP.BIN, vectores de syscall `0x8c0000b0-bc`) aparece a
  cero en un volcado justo antes. No se entregó: Windows CE necesita un estudio aparte. **Sega Rally 2 (USA)**
  también es Windows CE y cae igual (~17 s).
- **Re-Volt (USA)**, perfil `rv`: Shinobi 1.43 + Audio64 (`SFX/AUDIO64.DRV`), sin DMA G2 de sonido en Flycast, música
  en 14 pistas CDDA (no suenan). Cable `0x8c0f2082`; la misma espera de SB_FFST bit 5 que Namco Museum en
  `0x8c0f2fe4` (parcheada). En Flycast llega a la pantalla de la VMU.

### Resultado del lote en placa (2026-11-08, tarde) y dónde estamos

**No carga ninguno**: Crazy Taxi 2, Daytona 2001, YSGW, Namco Museum, Re-Volt (Midway y Sega Rally 2 ni se
enviaron). **La hipótesis del sonido no basta**: Crazy Taxi 2 es de la misma familia que Virtua Tennis (librería AM,
sonido por CPU, sin DMA G2) y se para igual.

`ct2_diag` en placa (vídeo): texto del loader → logo de SEGA con las filas del residente (llamadas GD) durante
menos de un segundo → **todo negro** (el monitor no pierde la señal) y las filas del muestreador TMU2 nunca salen.
**Igual que `va_pc_diag`.** En Flycast, tras el logo, los dos pasan a su siguiente pantalla. Ikaruga, en cambio,
se queda con el logo congelado y las filas vivas (atascado en la DMA G2).

Lo que eso dice: el juego llega a cargar datos del disco con el residente y apaga/borra la imagen para la siguiente
pantalla; después, o se para sin volver a llamar al GD-ROM, o la salida de vídeo queda desactivada y no se ve nada.
El muestreador debería armarse en la siguiente lectura (VBR `0x8c00f400` en CT2 y VA, comprobado en Flycast), así que
probablemente se para **antes** de la siguiente lectura o con las interrupciones enmascaradas.

**Pero `ct2_diag` llegó 1 vez de cada 6 a la pantalla de tarjetas de memoria** (vídeo: ~8 s en negro y luego la
pantalla amarilla con todas las filas, también las del muestreador). El fallo es **intermitente**: una carrera de
tiempos o una interrupción que salta a veces (YSGW ya fue intermitente hasta `MASKERR`). Sospechosos: el escaneo
maple del MIE (CT2 no tenía hook) y las interrupciones de error. Perfil `ct2h` = CT2 + hook de maple (literal
`0x8c166ee0` de la llamada a "a física" `0x8c16852e` antes de `SB_MDSTAR`); imágenes `ct2h`, `ct2h_maskerr` y
`ct2h_maskerr_diag` (en Flycast se ve el mando del residente en el puerto A).

`ct2h_maskerr_diag` en placa (2026-11-08, último vídeo de la sesión): logo de SEGA con filas → negro al menos 25 s,
sin filas del muestreador. Ni el hook de maple ni `MASKERR` lo arreglan en ese intento (falta saber la proporción en
varios arranques). **Proyecto en pausa en este punto.**

### CT2: análisis en Flycast tras la pausa (2026-11-08)

Dato del usuario: en la placa **nunca** sale la pantalla "Now Loading" de CT2, ni siquiera la vez que llegó a la
pantalla amarilla (pasó de negro directamente a la amarilla). En Flycast la secuencia es logo de SEGA → "Now
Loading" (~2 s) → pantalla amarilla.

Trazas nuevas en `tools/flycast/flycast-dc2naomi-debug.patch`:
- `FC_REGTRACE=1`: escrituras en registros PVR (0x000-0x1ff, sin TA/render) y SB, solo cuando cambia el valor, con
  PC/PR (con el recompilador dinámico el PC es aproximado: inicio de bloque).
- `FC_PIOCYC=N`: cada lectura PIO de 16 bits de la NetDIMM cuesta N ciclos del SH4 (imitar la placa, donde el
  residente copia por CPU y Flycast lo hace al instante).

Resultados:
- El juego configura el vídeo **una sola vez** (PC ~`0x8c154de4`): VO_CONTROL `0x00160008` (blanking), FB_R_CTRL
  `0x00800004`, VO_STARTX `0xa8`, SPG_VBLANK_INT `0x00150208`, y lo enciende (`0x00160000` / `0x00800005`) antes del
  primer frame. **No toca SPG_LOAD/HBLANK/VBLANK/WIDTH/CONTROL** (usa los que deja el IP.BIN) ni vuelve a cambiar el
  modo para la pantalla amarilla: el "Now Loading" y la amarilla salen con la misma configuración de vídeo.
- Con `FC_PIOCYC=40/120/1500` el "Now Loading" **sigue saliendo** (con 1500 dura ~25 s) y el juego llega a la
  amarilla: la lentitud de las lecturas PIO por sí sola no explica el fallo. Hipótesis descartada.

Queda abierto: qué tiene el "Now Loading" que en la placa no se ve (paleta ARGB8888, `PAL_RAM_CTRL=2`, textura
subida por DMA ch2, cambio de framebuffer en la interrupción de vblank...). Hace falta el diag del punto 1 de abajo
para ver si en ese tramo el juego está vivo.

### Alternativa encontrada: DreamShell 4.0.4 (2026-11-08)

[DreamShell](https://github.com/DC-SWAT/DreamShell) 4.0.4 (julio de 2026, de SWAT) **arranca imágenes GD-ROM de Dreamcast en
NAOMI y NAOMI 2 desde IDE o SD**, y también ROMs de cartucho NAOMI. Su ISO Loader (isoldr) hace lo mismo que nuestro
residente, pero es un proyecto maduro: emula todas las syscalls de la BIOS, lee de forma asíncrona con interrupciones,
emula CDDA en NAOMI, parchea el cable de vídeo, carga un volcado de la flash de Dreamcast y gestiona la EEPROM.
Para los mandos trae un **firmware propio de la MIE con puente JVS → mando de Dreamcast**: volante, pedales, hasta
10 botones, zona muerta, calibración de volante/acelerador/freno (aplicación "MIE JVS"). Es justo lo que buscaba
este proyecto para el mueble de Crazy Taxi.

Cómo arranca en NAOMI: con la BIOS **HollySH** (`firmware/hollysh`, imagen `.bios` que sustituye a la BIOS de la placa),
que carga DreamShell desde SD (adaptador SD por SPI en el puerto serie, conector CN1, CS por RTS) o IDE. En el código
no hay imagen de netboot para NetDIMM. Falta confirmar en el foro (http://www.dc-swat.ru/forum/thread-4297.html) qué
hardware hace falta exactamente y qué juegos de Dreamcast funcionan.

Lo que dice el hilo "DreamShell on NAOMI" del foro de dc-swat (oct. 2025 - oct. 2026, autor SWAT):
- Arranca DreamShell con una **BIOS propia grabada en la EPROM de la BIOS** (programador + borrador UV; las 27C160 viejas
  "mueren como moscas", mejor comprar otras). La BIOS de serie bloquea la interfaz ATA; la HollySH la desbloquea.
- Lee los juegos de **SD** (adaptador al conector CN1, conectores OMRON que recomienda sacar de un cartucho barato o de
  la placa óptica) o de **IDE/CF** (CF de 128 GB con LBA48). "**For DreamShell, NETDIMM is a useless thing**": no lee de
  la NetDIMM.
- Juegos de Dreamcast en NAOMI: sí, salvo probablemente Windows CE. Worms World Party "funciona a la perfección".
- Puertos maple: A y D de NAOMI se usan para otras cosas; B y C valen para periféricos de Dreamcast; el ISO Loader
  cambia C por A. Mod del puerto A: http://www.dc-swat.ru/blog/hardware/1146.html. Desde la 4.0.4, puente JVS (MIE).
- NAOMI 2: primero sin vídeo (nov. 2025); la 4.0.4 (jul. 2026) anuncia soporte completo de NAOMI y NAOMI 2.
- Soporte MIE/JVS en KallistiOS: https://github.com/KallistiOS/KallistiOS/pull/1440

Fuentes del isoldr para NAOMI: `firmware/isoldr/loader/{main.c,syscalls.c,utils.c,cdda.c,naomi.c}` (ramas
`!is_dreamcast()`); MIE: `firmware/mie`; mapeo JVS: `modules/isoldr/mie_pad.c`.

### DreamShell por netboot (perfil `ds`, 2026-11-08) — paso 1: llega al menú en Flycast

Idea: DreamShell 4.0.4 ya resuelve lo difícil (syscalls, sonido, IRQ, puente JVS). Su KallistiOS (compilado como
Dreamcast "pristine") **también monta `/cd` en NAOMI** y lee el disco con las syscalls GD de la BIOS, que nuestro
residente ya imita leyendo de la NetDIMM. Así DreamShell arranca por netboot sin BIOS HollySH ni SD/IDE.

Construcción: carpeta fuente con `IP.BIN` (uno estándar de SEGA; se usa el del disco del usuario con los parches de
Virtua Tennis), `1ST_READ.BIN` = `DS_CORE.BIN` de la release y la carpeta `DS/` de la release.
`./build.sh ds CARPETA build/ds.bin`. La ISO se hace con Rock Ridge (`"rock_ridge": True`, nombres en minúsculas).

Cambios necesarios:
- `DIMM_SYNCREAD` (0x0400, en el perfil): las lecturas DMA del GD terminan en una sola llamada a EXEC_SERVER
  (KallistiOS espera una interrupción de fin de DMA G1 si el comando sigue "procesando") y la TOC de baja densidad
  devuelve la de alta (KallistiOS busca la sesión ISO9660 en la TOC del área 0).
- `arch_stack_32m` de KallistiOS (`0x8c25d4c4` en la 4.0.4: `0x8e000000`) → `0x8dc00000`, para que no pise al residente.

En Flycast (con dos ajustes locales en `tools/flycast/flycast-dc2naomi-debug.patch`: SCI que contesta como puerto
síncrono sin nada conectado, porque el sondeo de SD por SCI espera RDRF sin límite; y `FC_SYSM_RAM=1`, modo de sistema
NAOMI `0xa1` en `0xa05f74b0` para código en RAM, como la placa real): "Root directory is /cd/DS", detecta la MIE
("JVS I/O 315-6149") y llega al menú "DreamShell 4.0.4 NAOMI".
**En placa (2026-11-08): se cuelga tras el logo de SEGA.** Sospechoso principal: el sondeo de IDE por el bus G1
(registros ATA `0xa05f7018`/`0xa05f7080-9c`), que en NAOMI es el bus de la NetDIMM; también el sondeo de SD por
SCIF/SCI. Siguiente prueba: `EMU_DS_CORE.BIN` de la release (compilado con `DS_EMU`: se salta `InitIDE()` e
`InitSDCard()`; mismo parche `0x8c25d4c4`), imágenes `dreamshell_emu` y `dreamshell_emu_diag` (`DIAG=1`). Ojo: el
constructor reutiliza `WORK/track3.iso`; con otra carpeta fuente usar otro WORK o `REBUILD=1`.
`dreamshell_emu_diag` en placa: filas vivas (las llamadas GD siguen) pero negro, sin menú; con lecturas PIO lentas en
Flycast llega igual al menú, así que no es lentitud. Hipótesis: `cdrom_init` del KallistiOS de DreamShell repite el
desbloqueo de la protección del bus G1 (escribe `0x1fffff` en `0xa05f74e4` y lee los 2 MB de BIOS) si `0xa05f74ec`
no vale 3; en NAOMI esas direcciones G1 son el puerto del cartucho (la NetDIMM) y, con un multibios, la verificación
puede fallar y bloquear el bus: el residente leería basura y DreamShell no encontraría su carpeta. Perfil `ds_emu`:
`cmp/eq #3,r0` en `0x8c15ba1e` (EMU_DS_CORE) → `sett`, se salta el desbloqueo. Imágenes `dreamshell_emu2(_diag)`.
**`dreamshell_emu2_diag` en placa (2026-11-08): igual**, filas vivas durante minutos y negro. La protección del bus G1
no era (o no era lo único). Sin forma de ver en placa qué devuelve cada lectura, el camino por netboot queda
**aparcado**. Para seguirlo haría falta un diag legible (por ejemplo dígitos hexadecimales en vez de bits: contador de
llamadas GD, último comando, último FAD y los primeros bytes del último sector leído) o preguntar a SWAT. La ruta
probada por SWAT sigue siendo BIOS HollySH + SD en CN1 (MISO B45, MOSI A46, CLK A47, CS B50, 3,3 V) o CF/IDE.
Siguiente: lanzar un juego de Dreamcast desde el ISO Loader leyendo de la NetDIMM (paso 2) y el puente JVS (paso 3).


**`dstest` en placa (2026-11-08, foto):** SYSMODE `0xa0`, protección G1 **ya superada** (`0x5f74ec = 3`; el multibios
arranca con `0xe6ff`, el bootstrap "mágico"), TOC correcta, PIO y DMA de sectores bien (`CD001`), iso9660 lista
`/cd/DS`, `startup.lua` se lee y `curl.klf` (946 KB) a **2,4 MB/s**. Forzar a mano el desbloqueo G1 pone el estado en 2
y la NetDIMM devuelve solo `ff`: el desbloqueo sí rompe el bus, pero DreamShell no lo hace porque el estado ya es 3.
Conclusión: el camino de lectura de DreamShell funciona en placa; se para en algo posterior.

**Consola en pantalla (`DIMM_CONSOLE` 0x0800, `CONSOLE=1`):** el residente se hace pasar por dcload (`0xdeadbeef`
en `0x8c004004`, función en `0x8c004008`) y dibuja en el frame buffer todo el dbglog/printf de KallistiOS (fuente
8x16 de `tools/dstest/font.h`). Imagen `dreamshell_con` (EMU core). En Flycast se ve el registro hasta
"Initializing DreamShell Core...".
**`dreamshell_con` en placa: se queda en "Initializing DreamShell Core..."** (último mensaje del core normal antes del
menú). Después vienen, sin mensajes: SDL (vídeo + joystick: MIE/JVS), TTF, GUI, consola, módulos, apps y Lua.
Siguiente: `dreamshell_dbg` = `DEBUG_DS_CORE.BIN` (perfil `ds_dbg`, parche `0x8c25d504`) + consola: en Flycast muestra
"Loading module vkb", "Installing apps", "DS_OK: ..." y "Initializing time".
**`dreamshell_dbg` en placa (foto): DreamShell arranca entero.** "DreamShell 4.0.4 NAOMI 2", "Base path: /cd/DS",
módulo vkb, todas las apps `DS_OK`, "App Launch App opened", "Startup time: 6833 ms". Pero la pantalla sigue mostrando
el texto de la consola: lo que DreamShell dibuja con el PVR (3D) no llega a la pantalla. La placa es una **NAOMI 2**
(SWAT: "en NAOMI 2 aún no hay vídeo, la salida hay que configurarla aparte"; su BIOS HollySH inicializa ELAN). Flycast
no puede emular NAOMI 2 sin su BIOS. Siguiente: `tools/pvrtest` (imagen `pvrtest`): los pasos de vídeo de DreamShell
(`pvr_init_defaults`, `pvr_dma_init`, textura por SQ y por DMA ch2, fotogramas con límite de tiempo) con texto.
**`pvrtest` en placa (vídeo):** pvr_init_defaults, pvr_dma_init, textura por SQ y por DMA ch2: todo bien. El fotograma
0 se envía pero **el 1 nunca está listo** ("NOT READY after 3 s" sin fin). `ISTNRM = 0x40000030` en cada lectura:
vblank in/out pendientes sin atender y una interrupción externa pendiente (bit 30); nunca los bits de render terminado.
Parece que las interrupciones de Holly no llegan a KallistiOS (o algo externo de la NAOMI 2 las bloquea).
`pvrtest2`: contador de IRQ de vblank, bits de ISTNRM tras el fotograma 0, IML*, ISTEXT, SR, ICR, registros de ELAN
(`0xa8800000`: ID `0xe1ad0000`, IFCTL `+0x10`, IRQSTAT `+0x74`, IRQMASK `+0x78`) y dos experimentos (máscara de ELAN a
0; máscaras externas a 0).
**`pvrtest2` en placa:** SR=`0x40000001` (IRQ activas), ICR=`0x8000`, `ISTEXT=0x8` (el bit 3 externo de siempre).
El vblank (bit 3 de ISTNRM) aparece y se borra: **las interrupciones sí llegan** (los bits 4-5 pendientes son eventos
que KallistiOS no usa; lectura anterior corregida). Tras el fotograma 0 nunca aparecen el bit 7 (lista opaca
terminada) ni los 0-2 (render terminado): **el TA no recibe los polígonos**. KallistiOS los manda por store queues
directos a `0x10000000`; Katana suele mandarlos por DMA ch2. `pvrtest3`: modo directo (SQ) 5 s con TA_OPB_POS /
TA_VERTBUF_POS, QACR0/1, MMUCR, CCR, LMMODE0/1; si falla, `pvr_init` con `dma_enabled` (fondo verde).
**`pvrtest3` en placa: fallan los dos modos** (directo y DMA de vértices). QACR0/1=`0x10`, MMUCR=0, CCR=`0x105`,
LMMODE0/1=0/1: iguales que en Flycast. Pero el TA escribe cerca de 0: directo `TA_OPB_POS=0x00022580` (Flycast
`0x00489600`); DMA `TA_OPB_POS=0x00012580`, `TA_VERTBUF_POS=0x00000084` (Flycast `0x00400000`). Como si los registros
de base del TA no tuvieran lo que KallistiOS escribe. `pvrtest4`: volcado de registros PVR/TA tras `pvr_init_defaults`
y tras la lista opaca, y escritura/relectura de los registros del TA.
**`pvrtest4` en placa:** ELAN presente (`0xa8800000` = `0xe1ad0000`). Todos los registros PVR/TA iguales que en
Flycast y todos se pueden escribir y releer, **salvo que `TA_OPB_POS` sigue en `0x00022580`** (debería volver a
`TA_OPBINIT` = `0x00089600` en cada `TA_LIST_INIT`): el TA no responde a la orden de iniciar lista ni procesa datos.
La tabla de inicialización del IP.BIN no toca el PVR/TA. KallistiOS normal (Cannonball, NAOMI) hace el mismo
`PVR_RESET_ALL` y funciona arrancando desde la BIOS. Experimento: la misma prueba con KallistiOS de NAOMI
(`tools/pvrnaomi`): `pvrtest_nb` (imagen NAOMI directa, como Cannonball) y `pvrtest_np` (por loader + residente +
IP.BIN, con un salto de 64 KB delante porque KallistiOS NAOMI enlaza en `0x8c020000`).
**Resultado en placa: `pvrtest_nb` dibuja (cuadrado rojo), `pvrtest_np` no (texto).** El TA se queda sin
responder por algo de **nuestro camino de arranque**, no por KallistiOS ni DreamShell. Sospechosos y flags nuevos del
residente: `DIMM_NOIPBOOT` 0x1000 (saltar a 1ST_READ sin el bootstrap del IP.BIN), `DIMM_NOPCTRA` 0x2000 (no escribir
PCTRA `0x000a03f0`), `DIMM_NOBIOSHW` 0x4000 (no escribir AICA SCI*, DMAOR ni PCTRA). Imágenes
`pvrtest_np_noipboot`, `pvrtest_np_nopctra`, `pvrtest_np_nobioshw`.

## ⭐ CAUSA ENCONTRADA (2026-11-08): `PCTRA = 0x000a03f0` mata el TA de la NAOMI 2

En placa: `pvrtest_np_nopctra` y `pvrtest_np_nobioshw` dibujan (cuadrado rojo); `pvrtest_np_noipboot` no. El residente
escribía en `boot()` el valor que deja la BIOS de Dreamcast en el control del puerto A del SH4 (`PCTRA`,
`0xff80002c`). En la NAOMI 2 esos pines se usan para otra cosa y con ese valor **el TA deja de responder**
(`TA_LIST_INIT` ignorado, `TA_OPB_POS` congelado, nunca "lista terminada" ni "render terminado"): el 3D no dibuja
nada. Era la causa de que DreamShell arrancara entero sin verse, y probablemente de la pantalla negra tras el logo de
SEGA en casi todos los juegos de Katana (Virtua Tennis sería la excepción por cómo inicializa el TA o porque reescribe
PCTRA). **Arreglo:** el residente ya no escribe `PCTRA` (el flag `0x2000` ahora sirve para volver a escribirlo en
pruebas). Imágenes con el arreglo: `dreamshell2`, `ct2h2`, `daytona2`.

**Resultados en placa con el arreglo (2026-11-08):** DreamShell muestra su menú y se maneja con los mandos del mueble.
**Crazy Taxi 2 funciona**: "Now Loading", pantalla de VMU y, en el mueble de Crazy Taxi, volante y pedales responden
bien con el hook de mandos. Daytona USA 2001 sigue en negro tras el logo de SEGA.

**Idioma japonés: CRC de la flash mal.** `crc_block` de `build_image.py` no invertía el resultado (la BIOS y
KallistiOS devuelven `~n & 0xffff`), así que el bloque de configuración (bloque lógico 5, partición 2) era inválido y
los juegos de Katana usaban japonés. Corregido; `ct2h3` sale en inglés.

**Mapeo del mueble para CT2 (`ct2h4`, en `pad_state` del residente):** volante → stick X; acelerador → R; freno → L;
START → Y al instante (Crazy Hop), mantenido 1 s (60 sondeos) → START (título, pausa); palanca adelante → B (marcha D /
volver), atrás → A (marcha R / aceptar); volante en el último ~6 % del recorrido → cruceta izquierda+arriba /
derecha+abajo (cursor de menús); botón JVS 0x0200 → X. (Es global en el residente: si otro juego necesita otro reparto,
hacer el mapeo por perfil.)

**Mandos por juego (`pad_map` en la cabecera, `"pads"` en `tools/games.py`):** el residente lee `pad_map` (antes
`reserved[0]`) y elige el reparto. `ct` (0, por defecto) = el de CT2, ya dado por bueno en el mueble. `menu` (1) =
Yu Suzuki Game Works: START normal pero se manda **al soltarlo** (8 sondeos) y solo si no se tocó la palanca mientras
estaba pulsado; START + palanca adelante = arriba, START + palanca atrás = abajo (el menú necesita arriba/abajo limpios;
con izquierda+arriba a la vez no se llegaba a OutRun ni a Space Harrier); palanca sola = B/A; volante a tope =
izquierda/derecha. Motivo: en Power Drift el START mantenido del reparto CT (Y y luego START) no se reconocía.
CT2: probado en el mueble y **terminado** (2026-11-08). Yu Suzuki: ya arranca y juega con el residente sin PCTRA.

### SB_G2APRO (protección de direcciones de la DMA G2, `0xa05f78bc`) — revisado 2026-11-08

El driver G2 DMA de Linux (`arch/sh/drivers/dma/dma-g2.c`) escribe `SB_G2DSTO` (`0xa05f7890`) = 27 y `SB_G2APRO` =
`0x4659404f`; KallistiOS escribe `0x4659007F` ("0x0C000000-0x0CFFFFFF", es decir solo 16 MB: en NAOMI, con 32 MB, una
DMA G2 desde `0x0Dxxxxxx` daría error de overrun; a tener en cuenta para DreamShell en modo 32 MB con streaming).
Los juegos Katana calculan y escriben su propio G2APRO con **la misma función de Shinobi en la versión Dreamcast y en
la NAOMI** (Ikaruga, Virtua Athlete: idéntica, literales `0x07f00000`, `0x46590000`, `0xa05f78bc`), así que G2APRO
no explica por qué la DMA G2 de Ikaruga no termina en placa con nuestro loader.

Virtua Tennis sigue siendo la única excepción fija y no sabemos por qué. Ideas sin probar, en orden:
1. Diag que **fuerce la imagen** (FB_R_CTRL/VO_CONTROL) y pinte desde TMU2 armado ya en `boot()` (no esperar a una
   lectura GD), con el VBR que haya: saber si el juego sigue vivo y dónde.
2. Comparar el estado de Holly/AICA/SH4 que deja la BIOS de NAOMI al lanzar un juego NAOMI con el que deja nuestro
   loader KOS (registros G1/G2, `SB_*`, IML*, DMAC, CCR/MMU, AICA 0x2800/0x2c00, RTC). La versión NAOMI de Virtua
   Athlete corre el mismo código que la de Dreamcast y en la placa sí funciona.
3. Mirar qué hace Virtua Tennis distinto justo tras el logo (en Flycast, trazando accesos a registros de CT2 y VT).

## Cómo encontrar los parches en otro juego Katana

Herramientas en `tools/` (necesitan `sh-elf-objdump`):
`gdx.py JUEGO.gdi DIR` (extraer), `lits.py FICH VAL,...` (literales), `refs.py FICH BASE LIT...`
(quién carga un literal), `dis.sh FICH BASE INICIO FIN` (desensamblar).

1. **Cable**: literal `0xff800030` (PDTRA) → la instrucción `mov.w @Rn,Rm` que lo lee → `mov #0,Rm`.
   En IP.BIN suele ser `mov.w @(4,r3),r0` con `r3 = 0xff80002c`.
2. **Maple**: la función "a física" (`and 0x0fffffff`/`0x1fffffff` de r4). De sus llamadas, la buena es la
   que va seguida de `mov.l r0,@(4,base)` (`SB_MDSTAR`) y de escribir 1 en `@(24,base)` (`SB_MDST`), con
   `base = 0xa05f6c00` guardado en `struct+0x10f4`. Se parchea **el literal** que contiene la función.
3. **G1**: entradas `0xa05f7484/90/94/a0/b4` en tablas de init → a `RES_SCRATCH`.
4. Si el juego carga otros programas, añade sus direcciones de entrada a `hook_pc` y un grupo por programa.

## Compilar

```sh
source /opt/toolchains/dc/kos/environ.sh        # KallistiOS con KOS_SUBARCH=naomi
chdman extractcd -i ysgw.chd -o ysgw/disc.gdi   # tu propio volcado
./build.sh ysgw ysgw/disc.gdi                    # -> build/ysgw.bin (201 MB)
SAMPLER=1 ./build.sh ysgw ysgw/disc.gdi          # diagnóstico: bits en pantalla, sin gancho
./build.sh daytona ../files                      # Daytona (ficheros extraídos)
```

Para WiPi Netbooter: `gzip build/ysgw.bin` y una línea en `romsinfo.csv`.

## Notas de hardware (aprendidas en otros ports)

- La VRAM real de NAOMI **no admite escrituras de byte** (Flycast sí): usar escrituras de 16/32 bits.
- La DMA del PVR se cuelga en NAOMI.
- **La DMA G2 del canal AICA que lanza un juego de Dreamcast no termina nunca en la NAOMI** (ADST se queda a 1,
  no hay interrupción de fin). Copiar por CPU y simular el fin (`g2cpu`).
- **El UBC (excepción DBR) cuelga la placa**; TMU2 por el despachador del juego sí funciona.
- Algunos juegos leen el tipo de cable del registro del AICA `0xa0702c00` (bits 9:8), no solo de PDTRA.
- En Flycast sin BIOS el driver MIE de KOS no se activa (ver parche en `mame4all-naomi/naomi/flycast`).

## Siguientes pasos

1. **Probar en placa `ikaruga_g2cpu` / `ikaruga_g2cpu_diag`.** Si pasa del logo de SEGA, la DMA G2 del AICA queda
   confirmada como el bloqueo y `g2cpu` es la receta. En la diag: fila 20 = empezadas | terminadas<<16,
   21 = última longitud, 22 = última dirección G2. Si empezadas > terminadas, no llega la interrupción de TMU2.
2. Si funciona, llevar `g2cpu` a **Namco Museum** (Shinobi 1.43; buscar la misma función: escribe
   `0xa05f7800+canal*0x20` en el orden STAG/STAR/LEN/DIR/TSEL/EN/ST, y su manejador de fin, que escribe
   `ISTNRM = 1 << (canal+15)` y llama a `desc[28](desc[32])`) y a YSGW (motor de Shenmue, librería propia).
   Las direcciones de `ctx` (`0x8c0cf2f0`) y del manejador (`0x8c044cbc`) están fijas en `g2cpu` para Ikaruga:
   para otro juego hay que pasarlas por el perfil.
3. Un **hook de maple para Virtua Tennis** (pide START en "No VMU found"): mismo método que Ikaruga (literal de la
   función "a física" antes de `SB_MDSTAR`).
4. Entender **por qué** la DMA G2 no termina en la NAOMI (¿el AICA de NAOMI necesita algo que hace su BIOS o la
   librería NAOMI, o es el modo de disparo de `ADTSEL`?). La versión NAOMI de Ikaruga sí usa DMA G2: comparar su
   secuencia de inicio del AICA con la de Dreamcast.
5. YSGW: además del sonido, queda el error del TA (ISTERR 0x10) y la ruta de texturas 0x11 (ver arriba).

## Agradecimientos (regla)

Citar en el README (sección "Agradecimientos") todo lo que se use de otros, y también lo que haya servido de inspiración o ayuda directa o indirecta. Añadirlo en el mismo commit en que se empiece a usar.

**Crazy Taxi 2, `ct2h5` (2026-11-09):** a petición del usuario (el salto en START no le gustaba), `DIMM_PAD_CT` pasa a ser
el mapa por defecto del mueble (`DIMM_PAD_WHEEL`: START al soltar, con START apretado palanca = arriba/abajo, freno = X,
acelerador = Y) más la marcha: la palanca del mueble vuelve al centro, así que el residente recuerda la marcha
(empieza en D). Palanca adelante en R = D (B); adelante ya en D = salto (Y, Crazy Hop); atrás = R (A). Si la marcha
del juego y la del residente se desincronizan, basta un toque atrás y otro adelante. Imagen hecha cambiando solo el
loader de `ct2h4` (el disco de CT2 ya no está aquí; la cabecera conserva `pad_map` 0). En Flycast llega a la pantalla
de memory card. `app/loader.bin` regenerado.

**Crazy Taxi 2, `ct2h6` (2026-11-09):** sustituye a `ct2h5` (que recordaba la marcha). Ahora el salto es un **doble toque
adelante**: el primer toque = D (B) y "carga" el salto durante `HOP_WINDOW` = 60 sondeos (~1 s, uno por fotograma);
un segundo toque adelante dentro de esa ventana = Crazy Hop (Y). Palanca atrás (R, A) o START apretado descargan.
Las técnicas Crazy pasan por R, así que no deberían disparar el salto (pendiente de confirmar en placa: Crazy Dash y
Crazy Drift). Ventana elegida con el usuario: 1 s (2 s era la alternativa). Misma forma de construir que `ct2h5`.

**⚠️ Formato de la cabecera (2026-11-09):** las imágenes hechas antes de subir `DIMM_RANGES`/`DIMM_TRACKS` a 32/64
(`ct2h4`, `ysgw5`, `nmus6`, `ikaruga_joy` y anteriores) usan 4/8. **No se les puede cambiar solo el loader**: el
residente nuevo leería la tabla de parches en otro sitio y no aplicaría ninguno. Así salieron `ct2h5` y la primera
`ct2h6` (malas en placa; en Flycast arrancan igual porque Flycast no necesita los parches para llegar al menú).
`tools/convhdr.py VIEJA.bin.gz NUEVA.bin.gz TITULO [PADMAP]` reescribe la cabecera al formato actual con el
`app/loader.bin` de ahora; la `ct2h6` buena está hecha así (comprobado: parches en su sitio, `pad_map` 0).

**Yu Suzuki, `ysgw6` (2026-11-09):** mandos `ysgw` (`DIMM_PAD_YSGW` = 5): los del mueble por defecto y, a petición del
usuario, un modo avión manual: **START + volante a tope a la derecha** = avión (palanca adelante = arriba, atrás =
abajo, en cruceta y stick; acelerador = A disparo, freno = B misil; volante = stick X y cruceta desde media vuelta),
**START + volante a tope a la izquierda** = coche. Con START apretado el volante no manda cruceta. Pendiente de
confirmar en placa qué botón es disparo y cuál misil en After Burner II, y el sentido de la palanca. Hecha con el
programa desde el CHD (disco idéntico a `ysgw5`). En Flycast llega a PRESS START.

## Lista de juegos del mueble estándar (`docs/pi250-juegos.md`): hecha (2026-11-13)

La tabla de juegos de Dreamcast la escribió una sesión a mano; se le añadió un apéndice con todo lo demás que hay en la
Pi .250 (originales de NAOMI, NAOMI 2 y Atomiswave, y filas o ficheros sueltos), generado con
`tools/board/picatalog.py` (lee el CSV y `/boot/roms/` por SSH; estados de `docs/pi250-estado.csv`). Para rehacerlo:
`PIHOST=192.168.68.250 PIPASS=... python3 tools/board/picatalog.py docs/pi250-estado.csv` (vale también para la .60).

## OutRun DC demo v37 (ArkRetro, 2026-11-12) — perfil `or37`, mueble Crazy Taxi

Nueva versión de la demo de abajo (autor: **ArkRetro**, https://github.com/ArkRetro; el usuario la dejó como
`outrun_dc_demo37_gdi.zip` en su carpeta `dc2naomi`). Mismo tratamiento que `or2006`; las direcciones de esta compilación
se encontraron por los mismos patrones en `1ST_READ.BIN` (desensamblado con `sh-elf-objdump`):
- `_arch_mem_top`: el único literal `0x8e000000` (`0x8c0a36b0`).
- `maple_dma_addr()`: el único uso del literal `0xa05f6c04` (`0x8c06bd70`: `mov.l 0x1fffffff,r1; and r1,r4; mov.l
  SB_MDSTAR,r1; mov.l r4,@r1; rts`): literal `0x8c06bd7c` → `HOOKST`, `0x8c06bd72` → `jmp @r1`, `0x8c06bd74` → `nop`.
- `cdrom_init`: el `cmp/eq #3,r0` tras leer `0xa05f74ec`, antes del desbloqueo con `0xa05f74e4` (`0x8c06740a`) → `sett`.
- `vid_check_cable` y sus dos copias: el `tst r0,r0` tras `jsr 0x8c07f9fc` delante de cada lectura de PDTRA
  (`0xff80002c`): `0x8c074414`, `0x8c074732`, `0x8c074af2` → `clrt`.
Tamaño: 984 MB en disco, 846 MB sin el relleno `0.0` (137 MB de ceros). 28 canciones largas `MUS0`–`MUS27` (402 MB) y
35 cortas (63 MB). **El usuario eligió quedarse con las 4 primeras**; las otras 24 están en `alias` repartidas
(4, 8, 12… → `MUS0`; 5, 9… → `MUS1`…), así que todas las carreras tienen música. Imagen: 527.071.232 bytes (502,7 MiB).
VMU activada (el juego guarda licencias). Mandos `wheel`.
- Flycast (`FC_PEDALS=1`): pantalla del loader, logo de OutRun 2006 y la demo de atracción en marcha. **En placa: sin
  probar.**
- En la Pi .60: `h-or37_dc2naomict.bin.gz` (md5 de la `.gz` `a6535dc17f3fe180adc3c839e4170ad0`) + `.vmu` vacío, fila en
  el CSV (`audit_name` `or37_dc2naomict.bin.gz`, copia `romsinfo.csv.bak_or37`, reimportado). Copia en el PC:
  `otros/or37/dc-or37_dc2naomict.bin.gz` (generada en la VM del PC, que tiene el disco y el repo).
- 2026-11-13 04:00: cargada en el mueble (`dc2naomi_send.py` a 10.0.0.4; residente vivo, IP.BIN en RAM). **Ojo:** tras el
  envío no quedaron corriendo ni el vigilante de VMU (`dc2naomi_vmu.py watch`) ni `timehack.py` (no había
  `/var/log/dc2naomi_vmu.log`; la Pi .60 parecía recién reiniciada). Se arrancaron a mano:
  `nohup python3 /sbin/piforce/timehack.py 10.0.0.4 &` y `nohup python3 /sbin/piforce/dc2naomi_vmu.py watch 10.0.0.4
  /boot/roms/h-or37_dc2naomict.vmu &`. Si se repite al cargar desde el menú del WiPi, revisar `wipiloader.py` de la .60.
  En el CSV de la .60 queda una fila huérfana, `h-daytona3_dc2naomi.bin.gz` (sin fichero), pendiente de que el usuario
  decida.

## OutRun 2006 Coast 2 Coast, demo para Dreamcast v24 (homebrew KallistiOS, 2026-11-09) — perfil `or2006`

Demo hecha por fans (textos en español, "OUTRUN DC DEMO", IP.BIN casero con fecha 2026-11-09), GDI con `track03.iso`
de 2048 bytes/sector. **No es Katana sino KallistiOS 2.x**, así que se trata como DreamShell:
- flags `0x1404`: `DIMM_SYNCREAD` (KOS espera la IRQ de fin de DMA G1 si la lectura sigue "procesando"),
  `DIMM_NOIPBOOT` (su IP.BIN no es el de SEGA: la tabla G1 no está en `0x5ab4`) y sin user break.
- `arch_stack_32m` (`0x8c0862f4`, `0x8e000000`) → `0x8dc00000`: es `_arch_mem_top`, techo de pila y montículo.
- `cdrom_init`: `cmp/eq #3,r0` (`0x8c04b6ba`) → `sett`, sin desbloqueo del bus G1 (en placa ya vale 3).
- `vid_check_cable` y sus dos copias en línea: `tst r0,r0` → `clrt` (`0x8c0581f4`, `0x8c058512`, `0x8c0588d2`):
  siempre VGA y nunca la escritura de PCTRA que mata el TA de la NAOMI 2 (en placa ya lo evitaría SYSMODE `0xa0`).
- **Mandos, nuevo:** `maple_dma_addr()` de KOS (`0x8c04fbc0`: `and 0x1fffffff,r4; mov.l r4,@SB_MDSTAR; rts`) pasa a
  saltar a `maple_hook_mdstar` del residente (valor de parche `HOOKST` = `0xfffffffb`, `PATCH_HOOKST`): llama al gancho
  maple y escribe en SB_MDSTAR lo que devuelve. Sirve para cualquier programa KOS con ese driver.
- Tamaño: 598 MB de datos (el archivo `0.0` de 405 MB es relleno a cero y no cuenta). `alias` acepta ahora una lista:
  `MVATTR.VQV` → `MVTS.VQV` y `MUS4/5/16/17/18.ADP` → `MUS3.ADP` (las canciones más largas). Queda en 493,6 MB.
- En Flycast (`FC_SYSM_RAM=1`): vídeo de intro, título "INICIO", START entra en "Elegir carnet", A (palanca atrás)
  crea licencia y escribe el nombre. Con `AUTOSTART=1` también pasa del título. Carrera sin comprobar.
  Mandos `wheel` (los del mueble por defecto). Sin probar en placa.

**⚠️ Corrección (2026-11-09 noche): la `ct2h6` entregada no aplicaba ningún parche** (el usuario: "no ve el mando en el
puerto A"). `convhdr.py` suponía el formato viejo con `DIMM_TRACKS` 8, pero `ct2h4` se hizo con 4 rangos y **32**
pistas (el historial de `resident.h`: 8 pistas hasta el 08-11 13:10, 32 hasta el 09-11 02:12, luego 32/64). La tabla
de parches quedó con 6 entradas vacías delante y el residente se para en la primera. Mi comprobación filtraba las
vacías y no lo vio. `convhdr.py` ahora deduce el formato (la tabla debe empezar por una comprobación de grupo) y lo
comprueba. Imagen buena: **`ct2h7`** (= la v6 bien hecha). Comprobado en Flycast en la RAM: literal del gancho
`0x8c166ee0` = `0x8dc01884`, cable parcheado, mando en el puerto A, START pasa de la pantalla de VMU.
**Ojo al probar mandos en Flycast:** sin `FC_PEDALS=1` el acelerador y el freno están a media carrera (`0x8000`), así
que con los mapas `wheel`/`ct` START cuenta como "usado" (pedal > 64) y no se envía. Usar `FC_PEDALS=1`.

## Depuración en la placa real por la red (2026-11-09 noche)

El usuario enlazó su PC y dio acceso a las dos Raspberry del WiPi (SSH; credenciales solo en el chat, no aquí):
`192.168.68.59` ("virtua"; desde el 2026-11-11 **`192.168.68.250`**) → NetDIMM `10.0.0.3` (NAOMI 2, mueble estándar) y `192.168.68.60` ("Netbooter") → NetDIMM
`10.0.0.4` (NAOMI 2, mueble Crazy Taxi). Firmware 3.17, 512 MB. El WiPi lleva las herramientas de DragonMinded en
`/sbin/piforce/dm_netboot` (`netdimm.NetDimm(ip).info()/peek()/poke()`), que se usan desde la Raspberry.
- `peek` con un juego de NAOMI normal: contesta al momento. **Con nuestro residente: 17-30 s y basura** (nadie
  atendía la petición; era la "interrupción externa bit 3 siempre pendiente" de las pruebas de DreamShell).
- **`dimm_service()` en el residente** (protocolo de `dimmcomms.c` de libnaomi): contesta peek/poke 8/16/32 y la
  dirección base, solo sobre memoria segura (RAM, Holly, AICA, VRAM, registros del SH4). Se sondea desde el gancho
  maple, cada syscall GD y el tick de TMU2 (con `DIMM_PCSAMPLE` 0x0200, que además deja los últimos PC en `pcs_ring`).
  Primera imagen con ello: `ysgw7` (sin probar en placa). Guardar el `nm` del residente de cada imagen de prueba
  para saber las direcciones (`_hook_calls`, `_jvs`, `_dbg_val`, `_pcs_ring`...).

## 18 Wheeler en placa con lectura en directo (2026-11-10)
- `ct2h8` + partida al 100 %: confirmado por el usuario en el mueble (todo desbloqueado).
- `18wheeler_novmu` con el loader actual y `0x20200` (caja negra + muestreador): **no se cuelga**. 0 excepciones,
  llamadas GD y maple subiendo, vídeo VGA encendido (`FB_R_CTRL 0x800005`, `SOF1 0x582800`). PCs en el bucle
  `0x8c069ce0`: espera a que la ranura 0 de la tabla `0x8c3a12d8` (pasos de 0x80; +4 = ocupada, +8 = orden) quede
  libre; la orden la pone `0x8c04ecc0(0)` → `0x8c160b00(0, 0x8c240848, 0xf420)` + `0x8c15fa60` (orden 1). Librerías:
  NAOMI LIBRARY 0.9 AM R&D, libsnd 1.05a, ADX 5.x, bu 2.13. Último sector `0x7ac6d`, última llamada GD `0x04ec`.
- **En Flycast (misma imagen y residente) a los 25 s el estado es el mismo** (ranura 0 = 1, mismo sector) y la pantalla
  muestra un texto de memory card ("There are not enough free memory blocks... Press START"): ese bucle es normal.
- Con VMU (`18wheeler_dc2naomi` + loader actual, `0x28204`): en placa **0 llamadas al hook maple** (en Flycast 0x1ea, con
  0xe8 tramas de VMU) y muchas más llamadas GD. Pendiente: saber qué se ve en la pantalla del mueble.
- **Lo que se veía en el mueble (el usuario):** no era negro sino el aviso de memory card (texto blanco pequeño sobre
  negro). Con `18wheeler_dc2naomi` (la de VMU) además salía "the controller has been removed": **esa imagen tiene la
  cabecera antigua** (lista de parches en otro sitio, todo ceros en la palabra 183+) y el residente actual no aplica
  ningún parche, ni el del mando. `dcl.py` no lo comprueba: usar sólo imágenes con la cabecera actual (o `convhdr.py`).
- **`18wheeler2_dc2naomi` (2026-11-10):** `addvmu.py 18wheeler_novmu… 18wheeler2… app/loader.bin` (md5 `c5c185b9…`).
- **Mandos de 18 Wheeler (2026-11-10, placa):** con `pad_map` 1 (`menu`) todo funciona pero no hay X/Y: no se puede cambiar la vista (Y) ni tocar la bocina (X), y con START pulsado los pedales siguen acelerando. Cambiado a `pad_map` 4 (`wheel`): START mantenido + acelerador = Y (vista), START + freno = X (bocina), START + palanca = arriba/abajo, START al soltar. Solo cambian 4 bytes de la cabecera (`pad_map` es la palabra 175 de la cabecera, en `0x40000 + 175*4` de la imagen; `vmu_offset` la 176). Imagen nueva: md5 `1d8c9cea030f37a2c503561d8688e4f2`, mismo nombre `18wheeler2_dc2naomi.bin.gz`. `tools/games.py` (`w18`) ya usa `wheel`.
  Flycast: aviso normal de VMU → ADX → título → MODE SELECT → camión. VMU con `18LUN` de dreamcast-saves ("Perfect
  Save! All Secret Unlocked!", `18WHDATA.SYS`, 5 bloques): en Flycast se salta el aviso y entra en Arcade. En la Pi del
  Crazy Taxi con su `.vmu`, fila en el CSV (importada) y enviada; placa: pendiente de que el usuario la pruebe.
- **`dcl.py` mataba `timehack.py` y no lo volvía a arrancar:** a los pocos minutos la placa se reinicia con "error 33
  gateway is not found". Arreglado (lo relanza tras el envío). Ojo con `pkill -f` y `pgrep -f`: el patrón también casa
  con la propia orden `bash -c` que lo contiene (hay que usar un fichero `.sh` aparte o `[t]` y que no aparezca el resto).


## F355 Challenge en placa (2026-11-10)
- `f355_dc2naomi` (la de VMU) tenía **la cabecera antigua** (como 18 Wheeler) y `f355_novmu` un loader anterior.
- **`f355b_dc2naomi`**: `tools/addvmu_stream.py /boot/roms/f355_novmu_dc2naomi.bin.gz OUT /root/loader_cur.bin 4`
  hecho **en la propia Raspberry** (es `addvmu.py` sin cargar la imagen en RAM, y además pone `pad_map`; la Pi 3B+
  tarda ~4 min). md5 `e8f500b2ee030154db8c3b1d01f4787f`. Mandos `wheel` (4). `.vmu` con la «Perfect Save!» de
  dreamcast-saves (`f355_2` = `F355DATA.SYS` 14 bloques + `f355_1` = `F355DATA.PLY` 8 bloques). Fila en el CSV e importada.
- **Usuario, en el mueble: todo funciona** (juego, volante, pedales, cambio de marcha, música). **Terminado.**
  La música no sonaba porque la «Perfect Save!» de dreamcast-saves trae en `F355DATA.SYS` (opciones) el volumen de la
  música a 0; el usuario lo subió en Options y lo guardó en su `.vmu`. (El disco no tiene CDDA: TOC solo pista 3.)
  **Ojo con las partidas descargadas:** traen también las opciones de quien las grabó (volumen, controles...).
- `18wheeler2` con mandos `wheel`: **usuario: perfecto, no tocar**.
- Ojo: `/boot/config/romsinfo.csv` no acababa en salto de línea; al añadir con `>>` la fila se pegaba a la anterior.

## Yu Suzuki Game Works separado: una imagen por juego (2026-11-11) — perfiles `outrun`, `hangon`, `powerdrift`, `afterburner2`, `spaceharrier`

Hecho a petición del usuario, para el mueble Crazy Taxi. `python3 tools/mkgz.py PERFIL DISCO.chd SALIDA.bin.gz`
(el programa de Windows sigue sacando la imagen única `ysgw`). Imágenes en la Pi .60 como `/boot/roms/dc-*_dc2naomict.bin.gz` (md5 comprobado; prefijo `dc-` como las demás del
usuario: `romname` con `dc-`, `audit_name` sin él), filas añadidas a `/boot/config/romsinfo.csv` (copia en
`romsinfo.csv.bak_ysgw_split`) e importadas a `/var/www/html/csv/romsinfo.csv` con `importcsv.py`. **Sin probar en placa.** Sin VMU (el juego no la usa). Mismo disco entero (184 MB comprimida): quitar
los ficheros de los otros juegos ahorraría poco (~30 MB de 213) y el menú carga sprites de todos.

Cómo funciona el menú (YSC, dentro de `1ST_READ.BIN`):
- "Escenas" en una tabla en `0x8c2505c4` (12 bytes cada una: función, 0, pila), arrancadas por
  `0x8c0dc7e0(escena, arg)`. 1 = arranque, 4 = logos + título + menú, 8 = OutRun, 9 = After Burner II,
  10 = Hang-On, 11 = Space Harrier. Power Drift es otro programa: `0x8c05e000(0)` carga `LOADER.BIN` y `PD.BIN`.
- La tarea de arranque `0x8c0ca060` hace `start_scene(1, 0)` (`mov #1,r4` en `0x8c0ca068`, literal en `0x8c0ca080`).
- Título: `0x8c17bd20` espera START (`bt.s` en `0x8c17bd32`). Menú: estados en `0x8c25cc20` (rejilla `0x8c17cca0`,
  ficha del juego `0x8c17d400`); juego elegido en `0x8c25cc10` (0 Hang-On, 1 Space Harrier, 2 OutRun, 3 After
  Burner II, 4 Power Drift; `0x8c17cbe0` lo pone a 4 con `mov #4,r1` en `0x8c17cbe8`). La rejilla pasa a la ficha con
  START/A (`bt.s` en `0x8c17cd74`) y la ficha lanza con START (`bf.s` en `0x8c17d42a`) mediante
  `0x8c17b720(escena, 1)`.

Parches de cada perfil (`_ysgw_one` en `tools/games.py`, sobre los del perfil `ysgw`): título, rejilla y ficha sin
esperar a START, y el juego elegido; así, al salir de un juego o acabar la partida se vuelve a entrar en él.
OutRun, Hang-On y Power Drift además arrancan directos (la tarea de arranque lanza su escena, o el cargador de Power
Drift): sin logos. After Burner II y Space Harrier pasan por logos, título y menú solos (~45 s): lanzados como
escena desde el arranque, en Flycast se quedaban en gris/negro; pero en Flycast **tampoco funcionan desde el menú
original** (After Burner II en negro, Space Harrier con basura en rojo), así que no se sabe si en placa arrancarían
directos. After Burner II sí funciona en placa desde el menú (usuario, 2026-11-09).

Flycast: OutRun, Hang-On y Power Drift llegan a la partida; After Burner II y Space Harrier llegan a sus escenas
(9 y 11, leído en RAM) sin imagen, como con la imagen original.

Mandos: OutRun, Hang-On y Power Drift `wheel` (el mueble por defecto). After Burner II y Space Harrier `plane`
(`DIMM_PAD_PLANE` = 6, nuevo): el modo avión de `ysgw` siempre (volante = izquierda/derecha y stick X, cruceta desde
media vuelta; palanca adelante = arriba, atrás = abajo; acelerador = A disparo, freno = B misil), START como `wheel`.
**After Burner II: mandos confirmados en placa (usuario, 2026-11-11, "así está perfecto")**, mapa propio `ab2`
(`DIMM_PAD_AB2` = 7). Probado en directo, cambiando `plane_cfg[]` del residente con pokes por la NetDIMM (script
`pc.py`: `plane_cfg` = {acelerador, freno, START+palanca adelante, START+palanca atrás, gatillo L en reposo}; bits bajos =
botones de Dreamcast, 0x10000 = gatillo R a tope, 0x20000 = L a tope, 0x40000 = L suelto). En este juego: **R = vulcan,
A = misil, el gatillo L es la palanca de gases analógica del arcade** (suelto = lo más lento, a tope = postcombustión;
la velocidad de crucero de MAME, "casi 2", sale con L a media, 0x80); B, X, Y, C y Z no hacen nada. Antes (mapa
`plane`: acelerador A, freno B, L suelto) volaba siempre "frenado" y el acelerador lanzaba misiles.
**Mandos definitivos (elegidos por el usuario, 23:20: "así funciona estupendamente, lo dejamos así"):** volante =
izquierda/derecha, palanca = arriba/abajo, **vulcan automático** (R siempre a tope), **acelerador = gases todo o nada**
(suelto = crucero, L 0x80; pisado más de un cuarto = L 255 de golpe), **freno = misil**, **START + acelerador = frenar**
(L suelto), **START + freno = quitar/poner el disparo automático**, START solo = START. `plane_cfg` tiene ya 8 valores
([5] lo que se envía siempre, [6] 1 = gases proporcionales al pedal / 2 = todo o nada, [7] recorrido de R).
Lo aprendido: (1) con R siempre pulsado **la cuenta atrás de "continue" se salta sola** al morir (sale "insert coin"):
por eso START + freno lo quita; (2) con los gases proporcionales al pedal (L subiendo 0x80 → 0xff en una décima) la
postcombustión (velocidad > 3) solo entraba a veces, aunque al juego le llegaba L = 255 fijo (leído en `0x8c2e6f44`,
byte alto = L, siguiente = R); con el salto directo a 255 entra siempre. No se sabe por qué.

**Luces del arcade en el botón START (After Burner II, probado en placa, usuario 23:35: "la luz ya está perfecta").**
- *Encender luces desde el residente:* la petición JVS que el residente hace a la MIE en cada sondeo lleva, si
  `jvs_lamp[0]` no es 0, la orden de salidas generales `0x32 0x01 valor` detrás de las entradas (el byte de respuesta va
  al final: nada se mueve en la contestación). **`0x80` = la luz del botón START del mueble Crazy Taxi** (la salida 0 de
  KallistiOS, la que usa Cannonball). `jvs_lamp[]` = {activo, valor, dirección, máscara}: con dirección, el valor sigue a
  la memoria del juego (0x80 mientras `byte & máscara` no sea 0). Vale para cualquier juego; se puede probar en caliente
  con pokes (`lamp.py`: `scan N` enciende las 8 salidas una a una).
- *Dónde están las luces del juego:* `BURNER/AB2.BIN` (en `0x8cb80000`) es un **emulador de 68000** que ejecuta el
  programa del arcade (`PROG.BIN`, en `0x8ca80000`). Su mapa de memoria está en una tabla en `0x8cb80b10` (pares
  página·0x10000|0x0300, puntero; los 12 bits bajos del puntero son indicadores): la página 0x14 (el chip de E/S del
  arcade, `0x140000`) es memoria normal en **`0x8ca40000`**, y la 0x15 en `0x8ca50000`. El puerto D de salida
  (`0x140007`) es el byte **`0x8ca40006`**: bit 7 siempre a 1 en partida, y los bits 4-6 son las luces (se vio el bit 5
  encenderse un segundo). Con máscara `0x70` la luz de START: apagada al empezar, encendida con el "Fire" (enemigo a
  tiro), parpadea cuando te dan o te estrellas. No se ha separado qué bit es cada luz (no hizo falta).
- Lo fija el mapa de mandos `ab2` (junto a `plane_cfg`).
Dónde lee el mando: el menú copia el periférico Katana (`0x8c1f5060`) en `0x8c2e6f3c` (16 bytes por puerto, +2 botones
con los bytes cambiados) con `0x8c0fec80`; After Burner II es `BURNER/AB2.BIN` (código SH4, cargado en `0x8cb80000`,
más `PROG.BIN` 68000 del arcade) y recibe las funciones del menú por una tabla copiada en `0x8c400000`. (`0x8c2e71ac`,
la otra tabla de mandos, es la de OutRun/el menú.)
**Space Harrier: probado en placa (usuario, 2026-11-12: "funciona todo genial", "así está perfecto").** Mapa `plane`:
volante = izquierda/derecha, palanca = arriba/abajo, acelerador y freno disparan (A y B). El autodisparo del juego
(botón mantenido) es lento: **el acelerador lleva disparo rápido** (`plane_cfg[8]` = 3: A pulsado 3 sondeos y suelto 3,
10 disparos por segundo; probados en directo 15 y 30, el usuario eligió 10). El freno, botón mantenido como siempre.

**Resultado en placa (usuario, 2026-11-11 03:59):** OutRun y Hang-On perfectos. Power Drift: **el sonido petardea y no va
del todo fluido, solo con música** (la demo sin música va bien); en su Dreamcast va perfecto. After Burner II y Space
Harrier: sin resultado todavía.

**⭐ Power Drift: el petardeo de la música, RESUELTO EN PLACA (usuario, 2026-11-11 06:28: "ya no petardea").**

*Cómo suena Power Drift (PD.BIN en `0x8c010000` + módulo `PD.SHX` cargado en `0x8ca9c1e0`; el offset X del fichero
está en `0x8ca9c1e0 + X`, y sus literales se recolocan con base `0x0ca9c220`):*
- TMU2 a 125 Hz (TCOR 100000, P/4, prioridad 8). Manejador `0x8c010540` (se registra desde el literal de `0x8c010598`):
  pone TCR2 = 0, llama al mezclador del módulo (`0x0ca9c7b4` → `0x0ca9c890`) y deja TCR2 = 0x20.
- El mezclador escribe PCM de 16 bits, 44,1 kHz, en dos anillos de 0x4000 bytes en la RAM del AICA (`0xa09e7f80` y
  `0xa09ebfc0`, canales 0 y 1 en bucle). Su estado está en `0x8cd45c20`: {destino izq., destino der., offset de escritura}.
- En cada tic pide la posición de reproducción (función del juego `0x8c013f3c(0)`, que lee el buzón del driver ARM,
  `0xa0800114`; el juego se la pasa al módulo por la tabla de `0x8ca9c320`: +0x10c posición, +0x120 proveedor de PCM
  `0x8c011f14`) y calcula `objetivo = (posición*2 + 0x2c4) & 0x3ffe`, `adelanto = (escritura - objetivo)` (si sale negativo
  le suma 0x4000) y escribe `0x38c - adelanto` bytes si es positivo. Máximo 0x38c bytes por tic (sus búferes no dan más).
- **La música viene del disco**: ficheros PCM de 44,1 kHz estéreo (176 KB/s) leídos en trozos de 32 KB (16 sectores)
  a 8 búferes encadenados (`0x8c089610`, 36 bytes cada uno: estado, ..., sector, nº sectores, búfer, puntero, quedan,
  pista, siguiente). Pista actual en `0x8c0895fc`, posición de lectura en `0x8c089600`, tabla de pistas `0x8c089730`
  (24 bytes: ..., tamaño, ..., bucle). (Lo de "ninguna lectura de disco durante la partida" de antes era falso.)

*La causa:* si un tic llega más de ~2,3 ms tarde (101 muestras), el objetivo ya ha pasado al offset de escritura, el
"adelanto" sale negativo, el mezclador lo toma por "una vuelta entera por delante" y **no escribe NADA hasta que la
posición da la vuelta al anillo: 170 ms de sonido viejo**. En la NAOMI cada lectura de un trozo de música (varias por
segundo; `cart_read` corta las interrupciones mientras copia de la NetDIMM, y el juego llama con ellas ya cortadas)
retrasa un tic así. Medido en placa con `pd_mon`: 124 tics/s, **45,7 % de los tics sin escribir nada**, música consumida
~90 KB/s en vez de 176. Por eso a mitad de tono (pitch `0x7800` a mano) sonaba limpio pero lento, y sin música iba bien.

*El arreglo (perfil `ysgw`, lo heredan los cinco juegos sueltos; solo Power Drift lo usa):*
1. `(0x8C011CA4, 4, PDPOS)`: el literal con el que el juego da al módulo su función de posición apunta a `pd_pos` del
   residente. Llama a la original y, si el offset de escritura está por detrás del objetivo, devuelve la posición que
   hace objetivo = escritura: el mezclador escribe su máximo (0x38c) y recupera 202 bytes por tic, sin parón.
2. `disc_patches`: `PD.SHX+0x7a4` `c4 02` → `c4 0a` (la constante 0x2c4 → 0xac4: escribe 23 ms más adelantado, para que
   un tic tardío no se oiga antes de recuperar). **Sola no arregla nada** (el parón no depende de esa constante): probado.
Medido en placa con el arreglo: 0 % de tics sin escribir, ~7,8 recuperaciones por segundo, música a 174 KB/s. El usuario:
"ya no petardea; no sé si es perfecto, pero es más que suficiente". (La imagen que oyó llevaba además el medidor
`PDMON`; la que queda en la Pi y sale del repo no lo lleva: pendiente de que el usuario la confirme.)

*Herramienta de medida:* `(0x8C010598, 4, PDMON)` en el grupo de PD.BIN pone `pd_mon` (resident.c) delante del tic:
`pdmon[]` (dirección con `sh-elf-nm resident/resident.elf`) = tics, tics sin escritura, peor retraso, peor duración,
histogramas de avance de posición, retraso y bytes escritos. Se lee con dos tandas de peeks separadas unos segundos.

*Descartado por el camino (todo probado en placa, sin efecto; quitado del código):* modo de memoria MEM8MB del AICA (solo
el registro `0x8C01306E` → `0x9332`; persistente con el driver ARM `AICADRV.BIN+0x3394` `7f0000e2` → `020080e3`; la
función entera en modo 8 MB cuelga la placa al arrancar, y cambiar el bit en caliente congela el juego); leer la posición
del registro `0x2814` en vez del buzón; escribir en el AICA a través de una copia en RAM con esperas de la FIFO de G2;
releer del AICA lo escrito (ni un dato erróneo en 7 millones, pero **las lecturas de la RAM del AICA por G2 son lentas**:
354 por tic bastaban para alargar el tic más de 8 ms). `DIMM_PCSAMPLE` (0x0200) **cuelga Power Drift** (usa TMU2).
Datos de la NAOMI leídos entonces: BCR1 `0xa3020008`, WCR1 `0x01110111`, WCR2 `0x018060d8`, WCR3 `0x07777777`, MCR
`0x80121214`, CCR `0x105`, IPRA `0x0080` con PD en marcha; P = 50 MHz.

*Lección:* un contador "muestras/s entregadas al chip" medido una sola vez dio 44.097 (parecía sano) y desvió horas; lo
que lo aclaró fue medir **por tic** (escribe / no escribe) y comparar los bytes de música consumidos con los 176 KB/s
debidos. *Mejora posible:* que las lecturas de la NetDIMM no retrasen los tics (trozos más pequeños por llamada, o DMA G1).

## Sega Rally 2 (USA) — Windows CE. ✅ FUNCIONA EN PLACA (2026-11-11 00:31, mueble Crazy Taxi)
Perfil `sr2` (como `mw2`). Probado solo en Flycast (NAOMI, `FC_SYSM_RAM=1`); en placa no se ha enviado.
Disco: pista 3 + 17 pistas CDDA (4-20, la música: no sonaría) + pista 21. Programa: `RALLY2.EXE`.

**Lo que ya está resuelto (en el loader y el builder):**
1. **`0WINCEOS.BIN` es un contenedor:** cabecera de 0x800 bytes (`D61A`, 1 sección: carga `0x0c010000`, desplazamiento
   `0x800`, tamaño, entrada). La BIOS carga la sección, no el fichero. `GdiDisc.boot()` lo detecta y apunta `boot_fad`
   al 2.º sector; además pone el flag nuevo `DIMM_WINCE` (0x40000) y el residente copia la cabecera en `0x8ce01000`,
   como hace el HLE de Flycast (`core/reios/reios.cpp`). Antes: excepción de instrucción ilegal en `0xac010010`.
2. **CE llama a las syscalls del GD-ROM con la MMU encendida y direcciones virtuales** (pila del hilo en P0, p. ej.
   `0x0205fb5c`). `in_ram()` las rechazaba y el driver nunca veía resultados. Ahora, solo dentro de `gd_syscall` y con
   `MMUCR.AT`, acepta P0/P3 **salvo por debajo de 64 KB**: `REQ_CMD INIT` llega con `r5 = 0` y leer la dirección 0
   mataba el hilo del driver (ese fue el falso "depende de la compilación": la traza `GDTRACE` también leía `*r5`).
3. **El driver de CE (`WSEGACD.DLL`, dentro de la imagen ROM; WDM) usa lecturas en flujo** (`MULTI_PIOREAD` 0x27,
   `MULTI_DMAREAD` 0x26) con `SET_PIO_CALLBACK` / `REQ_PIO_TRANS` y un hilo de interrupción (SYSINTR 21 = ISTNRM bit 14,
   fin de DMA G1) que pide cada trozo de DMA. Con MMU encendida: `REQ_PIO_TRANS` copia en el momento y el callback se
   llama al salir de la syscall (en bucle, sin anidar); tras `REQ_DMA_TRANS` el residente hace una DMA G1 real de 32 bytes
   (NetDIMM → `RES_SCRATCH+0x800`) para que salte la interrupción de fin de DMA, **fuera** de la syscall (si salta dentro,
   el hilo de CE entra anidado y se ignora).
   Mapa de interrupciones del núcleo de CE (`0x8c02e020`...): ISTNRM bit 14 → SYSINTR 21; ISTEXT bit 0 (unidad GD-ROM) → 20.
4. **`REQ_PIO_TRANS` y el callback PIO, como el HLE de Flycast** (`core/reios/gdrom_hle.cpp`): `REQ_PIO_TRANS` solo
   anota la petición; la copia la hace el siguiente `EXEC_SERVER`, y **al terminar esa llamada** el residente llama al
   callback (`SET_PIO_CALLBACK`), que pide el trozo siguiente. Mientras hay un `REQ_PIO_TRANS` pendiente,
   `GET_CMD_STAT` devuelve BUSY (solo con MMU encendida). **Error que costó horas:** hacer la copia y llamar al
   callback dentro del propio `REQ_PIO_TRANS`: el driver avanza su lista de búferes *después* de que la llamada
   vuelve, así que el callback anidado pedía otra vez el mismo trozo y los ficheros salían revueltos. Síntoma:
   CE se quedaba en el logo; el hilo que cargaba `CEMM.DLL` moría en `DoImports` del núcleo (`0x8c02094c`) leyendo un
   puntero basura (tabla de imports con datos de otra parte del fichero) y el despachador de excepciones del núcleo
   se quedaba dando vueltas (`NKLookupFunctionEntry` `0x8c0268f4` con el mismo PC) acaparando la CPU.
5. **No hizo falta parchear `WSEGACD.DLL`** (la espera de la interrupción de la unidad, ISTEXT bit 0): con lo de
   arriba el driver funciona sondeando, igual que en el HLE de Flycast, que tampoco levanta esa interrupción.
6. **Mandos (maple) en Windows CE:** `MAPLE.DLL` (en la ROM, `0x8c098000` = fichero `0x10001000`) escribe SB_MDSTAR
   una sola vez (su lista, un búfer común) y deja que el hardware lance la DMA en cada vblank (SB_MDTSEL = 1,
   MSYS `0xc3501000`, rearme con SB_MSHTCL). Corre en modo usuario con MMU: no puede llamar al residente. El gancho va
   en **el manejador de interrupciones del núcleo**: la rama de ISTNRM bits 12/13 (SYSINTR 18) en `0x8c02e114`
   salta a `ce_maple_isr` (head.S; parche `CEMAPLE` = `PATCH_CEMAPLE` sobre el literal `0x8c02e194` + `jmp @r3`),
   que llama a `ce_maple_poll()`: contesta la lista de CE con `maple_hook()` y apunta SB_MDSTAR a nuestro sondeo del
   MIE para el vblank siguiente. CE ve un mando en el puerto A (GETCOND) y nada en B-D.
   Tabla de interrupciones del núcleo: `0x8c02e020` (ISTERR, nivel 2), `0x8c02e0ac` (ISTNRM & IML4NRM: bits 0-11 →
   SYSINTR 16, 12-13 → 18 maple, 14 → 21 fin DMA G1, 15 → 24), `0x8c02e13c` (ISTEXT & IML6EXT: bit 0 → 20, bit 1 → 23).
7. **Resultado en Flycast (NAOMI): arranca.** Logo de CE → título "PRESS START BUTTON" → demo con coches → ranking.
   Probado después en Flycast con mandos: START, MODE SELECT, SELECT CAR, NAME ENTRY y carrera (el coche apenas
   corría en la prueba: revisar pedales en placa). Con `vmu=True` el juego carga de la tarjeta ("Load complete").
8. **Imagen para la placa (2026-11-10, 23:15):** `sega_rally2_dc2naomi.bin.gz` (md5 `9c44f9b76b720d5747fc7cd6580bedee`,
   268 MB; sin comprimir 414 MB, md5 `361b65e50e40473acfa41ffcb18d84bb`; flags `0x48004` = NO_UBC + VMU + WINCE,
   `pad_map` 4 `wheel`) y `sega_rally2_dc2naomi.vmu` con la partida «US - ALL UNLOCKED» de dreamcast-saves
   (`r/segarally/SGRALLY2.VMI`, fichero `SGRALLY2I0VD`, 61 bloques; **sin probar si el juego la acepta**). Subidas a
   `/boot/roms` de la Pi del Crazy Taxi (192.168.68.60), fila añadida a `/boot/config/romsinfo.csv` e importada, y
   enviada a la NetDIMM 10.0.0.4 con `/root/sendsr2.sh`. **Pendiente: resultado en la placa real** (lo dirá el
   usuario). Copia también en el PC: `C:\Users\Usuario\Documents\dc2naomi\`.

9. **PLACA REAL (2026-11-10, 23:16-23:50): se queda colgado en la pantalla "SEGA / Powered by Windows CE"**
   (dos intentos del usuario, mueble Crazy Taxi). En Flycast esa misma imagen llega al título y a la carrera.
   - El peek por la NetDIMM (`/root/pk.py`) **no responde** (antes de mandar el juego sí): nadie llama a
     `dimm_service()`, o sea, ni syscalls GD ni el gancho de maple se están ejecutando.
   - Añadido **`ce_tick_isr`/`ce_tick()`** (`PATCH_CETICK` = `CETICK` en games.py): el manejador del tick de CE
     (`0x8c02e228`, TMU0 cada 25 ms) pasa por el residente y atiende la NetDIMM, para poder leer la placa con CE en
     marcha. Parche: literal `0x8c02e24c` (`0xffd80000`) → `ce_tick_isr`, y `0x8c02e22c` → `jmp @r1`. Funciona en
     Flycast (1538 ticks en 60 s). **En la placa el peek sigue sin responder → el tick de CE tampoco corre: el
     cuelgue es muy temprano** (arranque del núcleo, o antes), no en la carga del juego.
   - Descartado mirando el código: el núcleo no escribe registros BSC ni SCIF; el RTC (`0xa0710000`) lo lee una vez.
   - **En curso:** imagen `sr2diag_dc2naomi.bin.gz` (perfil `sr2_diag` = `sr2` + `DIMM_DIAG` 0x8; md5 del .gz
     `6c4100761e976d45b5b492bcfb5e76af`) enviada al mueble: dibuja filas de bits arriba a la izquierda desde las
     syscalls, el gancho de maple y el tick (fila 0 llamadas a diag/4, 1 nº de llamadas GD, 2 última llamada
     `r7<<8|r4`, 3 sondeos maple, 4 último FAD, 5 otras syscalls, 16 ticks de CE, 17 llamadas al gancho, 18 MMUCR).
     Pedida foto al usuario. La secuencia de llamadas GD es determinista: con el nº de la fila 1 y la traza de
     Flycast (`EXTRA=-DGDTRACE`) se sabe en qué paso se paró.
   - **Foto 1 del usuario (23:48), filas leídas (bit más alto a la izquierda):** fila 1 (llamadas GD) = 0, fila 2
     (última llamada) = `0x0200`, fila 3 (maple) = 0, fila 4 (FAD) ≈ `0xA800`, fila 5 = 0, fila 6 = 0, fila 8 (FB_R_CTRL)
     = `0xD`, fila 14 (ISTNRM) = `0x38`, fila 15 (ISTEXT) = 0, **fila 16 (ticks de CE) = 3**, fila 17 (gancho maple) = 0,
     fila 18 (MMUCR) con el bit 0 a 1. **Conclusión: CE arranca en la placa (MMU encendida, 3 ticks de 25 ms) y se
     congela del todo (ni ticks) justo donde en Flycast llega la primera syscall GD de CE** (en Flycast las llamadas
     nº 7 a 26 — `INIT` r7=3, `REQ_CMD 0x18`, `EXEC_SERVER`, `GET_CMD_STAT`, TOC `0x13`, primeras lecturas — caen todas en
     el tick 3; traza: `EXTRA=-DGDTRACE` con `ce_ticks` como último dato del `dlog`). Los contadores a 0 con "última
     llamada 0x200" indican además que **las variables del residente vuelven a valores viejos**: CE reinicia la caché
     (CCR) y se pierde lo que el residente tenía solo en caché desde el `ocbwb` de `boot()`.
   - **Diagnóstico 2 (en curso, md5 del .gz `9a2a584c1a3c624808cbf076bdb49cb4`):** `stage(n, v)` dibuja al momento la
     fila 19 = paso y la 20 = dato: en `gd_syscall` 1 = entrada (v = `r7<<8|r4`), 2 = tras `dimm_service` (v = r5),
     3 = tras `dbg_draw` (v = nº de llamada), 4 = tras `patch_poll` (v = r6), 5 = tras el cuerpo (v = r0), 6 = salida;
     `0x10` = `sys_syscall`, `0x20` = `flash_syscall`, `0x30` = `misc_syscall` (v = `r7<<8|r4`). Filas 21/22 = SPC y SSR
     del último tick. Con MMU encendida `diag_draw` dibuja en todas las llamadas (antes 1 de cada 4).
   - **Fotos 2-5 (00:00, diagnóstico 2):** fila 1 (llamadas GD) = `0x13` (19), fila 2 (última) = `0x0105`
     (`GET_CMD_STAT` de la petición 5), fila 4 (FAD) = `0xB075`, fila 16 (ticks) = 3, fila 17 (gancho maple) = 0,
     **fila 19 (paso) = 6 y fila 20 = `0x13`: la llamada 19 terminó y volvió a CE**; fila 21 (SPC del último tick) ≈
     `0x000115xx` (código de usuario), fila 22 (SSR) = `0x00008001`. Es decir: en la placa CE hace `INIT`, las dos TOC
     y **la primera lectura de datos (`DMAREAD` FAD `0xb06e`, 8 sectores) completa y correcta**, y se congela antes
     del 4.º tick (en Flycast la llamada 20 llega ya en el tick 4). No hay reinicio (la BIOS recargaría el juego).
   - **Hipótesis actual (arreglo en el diagnóstico 3, md5 del .gz `1f569f2d97d5b599a69dfc29c9d2114e`, enviado a las
     00:20): los ganchos de interrupción usaban la pila del hilo interrumpido.** Los manejadores del núcleo de CE son
     rutinas hoja que solo usan r0-r3; `ce_tick_isr`/`ce_maple_isr` apilaban en r15 y llamaban a C. Si r15 es la
     pila de usuario del hilo interrumpido y su página no está en la TLB, con SR.BL = 1 un fallo de TLB **cuelga la
     CPU real** (64 entradas de TLB; Flycast casi nunca falla). Los ticks 1-3 caen con el núcleo ocupado; el 4.º es
     el primero con el sistema en reposo. Ahora los dos ganchos pasan a **pila propia** (`0x8dcf8000` maple,
     `0x8dcf4000` tick) y restauran r15 al salir. Si era esto, el cuelgue de la primera imagen (sin gancho de tick)
     sería el mismo fallo en el gancho de maple.
     Regla para ganchos en ISR de CE: solo direcciones P1/P2, pila propia, nada de coma flotante.
   - **✅ CONFIRMADO (usuario, 00:31): con la pila propia en los ganchos "funciona perfectamente"** en la placa
     (diagnóstico 3). Era eso: fallo de TLB con SR.BL = 1 al apilar en la pila del hilo interrumpido.
     Falta la música de las carreras (pistas CDDA 4-20, no se reproducen).
   - **Imagen limpia (variable, sin el parche de 30 FPS; sustituida el 2026-11-11, ver más abajo):** `sega_rally2_dc2naomi.bin.gz` md5 `b61bf3b07d478e1f1ea7f2acfe77f37e` (sin comprimir
     `8aed51a83f3f21dc7335a20164160f99`), perfil `sr2` (flags `0x48004`, mandos `wheel`), en `/boot/roms` de la Pi .60
     y en el PC. Lleva también el gancho del tick (peek por red con CE en marcha). `.vmu` con «US - ALL UNLOCKED».
   - El vigilante viejo de CT2 no tocó su tarjeta (el usuario tiene los ficheros renombrados con prefijo `dc-`:
     `dc-ct2h8_dc2naomi.vmu`..., fecha sin cambios).
   - **Ideas pendientes del usuario:** (1) CDDA a baja calidad (quedan ~98 MB libres de 512: ADPCM 4 bits de la AICA
     a 32 kHz estéreo ≈ 91 MB, o 22 kHz ≈ 62 MB; habría que robar 2 canales de la AICA al driver de sonido de CE y
     alimentarlos desde el gancho del tick; órdenes CD_PLAY/STOP/REQ_STAT/subcódigo en `gd_command`); (2) el juego
     tiene trucos en la pantalla de título: 30 FPS = Arriba, A, Abajo, Abajo, Izq, Der, B, B, Arriba; 60 FPS (con menos
     detalle) = lo mismo acabando en Abajo. Quiere los 30 FPS por defecto: buscar la tabla de la secuencia en
     `RALLY2.EXE` y dejar el modo activado de serie, o que el residente teclee la secuencia solo.
   - **✅ 30 FPS de serie (2026-11-11), probado en placa: el usuario confirma el 2026-11-13 que funciona perfecto.** La tabla no está en `RALLY2.EXE` sino en
     **`TITLE.DLL`** (pantalla de título). Cómo se encontró: el `.gdi` original en Flycast modo Dreamcast, el truco
     tecleado con `xdotool` (`scr/run_seq.sh`: A = tecla `x`, B = `c`, cruceta = flechas, 0,15 s por tecla, a los
     24 s) y volcados de RAM comparados (30 FPS / 60 FPS / secuencia mala, 2 pasadas de cada). Sale la tabla en
     `.data` de TITLE.DLL (ImageBase 0x10000000): botones del juego Arriba 0x200, Abajo 0x400, Izq 0x800, Der
     0x1000, A 1, B 2; cuatro códigos, cada uno 9 (o 14) palabras + contador de progreso: 0x1000e0e8 (14 botones,
     contador 0x1000e120), 0x1000e124, 0x1000e14c, 0x1000e174 (60 FPS) y **0x1000e19c (30 FPS)**. La función que
     los comprueba cada fotograma está en 0x10001094. Al completar: 60 FPS → `**(*0x1000ebf0) |= 1`; **30 FPS →
     `**(*0x1000ebf0) |= 0x80000000`** (palabra de opciones del juego; en modo DC queda en la RAM física 0xd8ace0)
     y suena el aviso (método 8 del objeto de `*0x1000e4bc`, r5 = 3, r6 = 2).
     **Parche:** en TITLE.DLL offset de fichero 0x63C (VA 0x1000123c, 18 bytes), la comprobación del cuarto código
     se cambia por `mov.l lit,r1; mov.l @r1,r1; mov.l lit(0x80000000),r3; mov.l @r1,r5; mov.l @r5,r2; or r3,r2;
     mov.l r2,@r5; bra 0x10001280; nop` (usa los literales que ya había: sin tocar relocalizaciones): el bit se pone
     en cada fotograma del título, sin sonido. Los otros trucos siguen funcionando (el de 60 FPS también).
     Como CE carga la DLL más tarde en memoria virtual, los parches de RAM del residente no llegan: opción nueva del
     builder **`disc_patches = [(fichero, offset, bytes viejos, bytes nuevos)]`** (`build_image.py`, cambia los
     sectores del disco dentro de la imagen; comprueba los bytes viejos). Perfil `sr2` (y `sr2_diag`).
     Comprobado en Flycast: modo DC con el disco parcheado → palabra = 0x80000000 sin tocar nada; imagen NAOMI →
     arranca, título y demo normales.
     **Imagen nueva (mismo nombre):** `sega_rally2_dc2naomi.bin.gz` md5 `2e2b65554234b059ddb50d8e61f736e9` (sin
     comprimir `135fbf4cc009f343ad8ec418b44b9792`; solo cambian esos bytes, en el offset 432170556 de la imagen).
     Hecha en el PC con **`tools/patch_gz.py IN OUT OFFSET VIEJOS NUEVOS`** (parchea un `.bin.gz` sin cargarlo en
     RAM, vale en la Pi) a partir de la limpia. Está en la carpeta del PC `dc2naomi/sr2_30fps/` junto con el `.vmu`.
     **Subida a la Pi .60** (`/boot/roms`, md5 comprobado allí; sustituye a la anterior, el `.vmu` no se ha tocado y
     el CSV no cambia). Probada en placa el 2026-11-13: perfecta.
   - Descartado: no hay instrucción `sleep` en el núcleo (no es STBCR/standby); las esperas del FIFO G2 no se
     atascan en placa (tabla de variantes).
   - Sospechas por orden: (a) algo del arranque del núcleo de CE que la NAOMI real no tolera; (b) la DMA G1 real del
     "kick" (`cart_dma` 32 bytes; las lecturas por DMA G1 de la NetDIMM nunca funcionaron en placa, ver tabla de
     flags) — alternativa ya pensada: que `ce_maple_isr` devuelva SYSINTR 21 en vez de 18 cuando haya un kick
     pendiente, sin enmascarar los bits 12/13 (la interrupción de maple vuelve a saltar enseguida); (c) la primera
     DMA de maple con la lista de CE va al MIE real antes de que el gancho la cambie.
   - Ojo en la Pi: quedó un vigilante viejo `dc2naomi_vmu.py watch ... ct2h8_dc2naomi.vmu` corriendo a la vez que el
     de SR2 (pid 8363); comprobar que el `.vmu` de CT2 no se haya sobrescrito (copia buena: `/root/vmu/*.orig`/`.bak`).

**Cómo se encontró (herramientas de depuración añadidas al Flycast local, no al repo):** variables de entorno
`FC_INTPC=N` (PC, registros Holly y TMU en 1 de cada N interrupciones), `FC_GDLOG=1|2` (peticiones y todas las
syscalls GD del HLE en modo Dreamcast: **correr el .gdi original en Flycast modo Dreamcast da la secuencia de
referencia para comparar**), `FC_APILOG` (llamadas a la API de CE: son excepciones de dirección en `0xffffxxxx`;
comparar por hilo, el hilo se distingue por los bits altos de r15), `FC_TLBLOG`, `FC_EXCLOG`, `FC_REGS` (registros y
direcciones de retorno de la pila en un rango de PC), `FC_G1LOG`, `FC_TMULOG`, `FC_PCTRACE`. Ojo: leer TCNT0 desde el
emulador tiene efectos (recarga el contador). Símbolos del núcleo: los `.map` de wince-dc son de otra compilación
(desplazados ~0x10020-0x10f3c según la zona); sirven de orientación.
Módulos de la ROM de SR2: nk, coredll, device, gwes, filesys, sysstart, platutil, wdevice, maple, wdmlib, wdmoem,
wsegacd (`0x8c093000`, virtual `0x01df1000`), ddraw, d3dim, ddhal, sndcore, dinputx, ole32, cemm...
**Regresión:** CT2 (`ct2h8`) con el loader nuevo llega igual a la pantalla de la VMU en Flycast (los cambios de CE
solo actúan con la MMU encendida).

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

## Ikaruga con VMU desbloqueada para el mueble estándar (2026-11-12) — `dc-ikaruga_dc2naomi.bin.gz`

Pedido por el usuario. No había disco de Ikaruga en el PC: se partió de la imagen buena de la Pi .250
(`ikaruga_joy_dc2naomi.bin.gz`, cabecera antigua, probada en placa el 2026-11-09).
- `tools/convhdr.py ikaruga_joy_dc2naomi.bin.gz conv.bin.gz "IKARUGA DC"` (cabecera nueva y `app/loader.bin` actual;
  mismos 8 parches, mandos `joy` = 2) y `tools/addvmu_stream.py conv.bin.gz dc-ikaruga_dc2naomi.bin.gz app/loader.bin 2`
  (flags `0x8004`). md5 `87f68248de681d7cde707b90737c66a4`.
- VMU `dc-ikaruga_dc2naomi.vmu` (md5 `6038d6ff…`): `IKARUGA_DATA` de bucanero/dreamcast-saves (`r/ikaruga`,
  "Credit MAX, All Mode Unlocked!", 34 bloques).
- En la Pi .250: `/boot/roms/dc-ikaruga_dc2naomi.{bin.gz,vmu}` (md5 comprobado), fila nueva en
  `/boot/config/romsinfo.csv` (copia `romsinfo.csv.bak_ikaruga_vmu`) importada con `importcsv.py`. **Se dejan las
  entradas viejas** (`ikaruga_joy`, `ikaruga_joy_g2cpu`) por si la nueva falla. Copia en el PC: `dc2naomi/ikaruga/`.
  Ojo: `/boot` de esa Pi está al 100 % (≈190 MB libres tras esto).
- **✅ Probado en placa (usuario, 2026-11-12 11:12: "funciona estupendamente").** Ikaruga va con el residente actual y
  con la VMU en fichero. (En Flycast se queda en el logo 斑鳩, también la imagen vieja: Flycast no sirve para Ikaruga.)
  Quitado `ikaruga` de `catalog.NO_VMU`: el programa ya le pone VMU.

## Super Street Fighter II X, traducción al inglés de ComradeSnarky (2026-11-12) — `dc-ssf2x_en_dc2naomi.bin.gz`

Pedido por el usuario (CHD `Super Street Fighter II X for Matching Service (Japan) [T-En by ComradeSnarky]`).
`app/dc2naomi.py --cab joy --batch` (11 s): 159,5 MB, 124,5 MB comprimida; juego desconocido para el catálogo
(parches de `findpatch`), mandos `joy`. md5 `f908f639dd77766bf580b0df00f33035`.
- VMU: `SSF2X.VMI` de bucanero/dreamcast-saves (`r/ssf2x`, "Everything unlocked, including DIP Switch Menu!"). Ojo:
  las cuatro partidas de esa carpeta se llaman igual (`SSF2X___.SYS`) y `vmutool import` sustituye: importar solo esa.
- Pi .250: `/boot/roms/dc-ssf2x_en_dc2naomi.{bin.gz,vmu}` (md5 comprobado), fila en `/boot/config/romsinfo.csv`
  (copia `romsinfo.csv.bak_ssf2x_en`) importada con `importcsv.py`. Copia en el PC: `dc2naomi/ssf2x_en/`.
  `/boot` de esa Pi: 2,5 GB libres (el usuario liberó espacio).
- **2026-11-12: en la placa, negro tras el logo de SEGA (en Flycast va: llega a "Save file loaded", CAPCOM y el
  título). RESUELTO, usuario 12:37: "ya funciona estupendamente".** Cómo se encontró (receta 4, con el VMU puesto):
  `dclb.py` (= `dcl.py` sin enviar) + `dc2naomi_send.py` de la imagen con flags `0x20200`; tras el cuelgue (el vigilante
  de VMU dice "no answer"; los peeks ya no contestan porque el gancho de maple no corre), cargar Ikaruga (14 MB) y leer
  la caja negra: 1 excepción, **EXPEVT `0xe0`** (error de dirección en lectura), **SPC `0x8c197bd2`** (`mov.w @r3,r1`),
  **TEA `0x8c0224b3`**. El código (`0x8c197b92`): `índice = *(u16 *)(*0x8c2d55b4 + 0x380)`, si 0 → byte `+0x462`, si no
  → 12; luego lee la tabla `0x8c0268f8 + índice`. TEA − tabla = −0x4445 → la palabra era **`0xbbbb`**: `*0x8c2d55b4` =
  `0x8c600000`, memoria de trabajo del juego que **lee antes de escribirla**. En Flycast la RAM empieza a cero (0 →
  índice válido); en la placa tiene lo que dejaron el loader y los juegos anteriores.
  **Arreglo general (residente, `boot()`):** pone a cero la RAM del juego (`0x8c008000` → `RES_BASE`) antes de leer
  IP.BIN, línea a línea por la caché y con `ocbp` en cada línea (para que ninguna línea sucia del loader se escriba
  encima después). Lo llevan todas las imágenes nuevas; las viejas siguen igual (cambiar su loader con `dcl.py`/
  `withfiles.py` si fallan así). En Flycast la imagen con el arreglo sigue llegando al título.
  Imagen nueva (solo cambia el loader): md5 de la `.gz` `b76d824ebd649d4072042434d215b55b`, en la Pi .250 y en el PC
  (`dc2naomi/ssf2x_en/`); su `.vmu` en la Pi es el de la partida de prueba (el anterior: `_test/en_vmu_before.bak`).
  Las versiones japonesa (`dc-ssf2x`) y española (`dc-ssf2x_es`) de la Pi llevan el loader viejo: **sin probar**; si se
  quedan en negro igual, cambiarles el loader.
- **Por qué `ssf2x_es` ocupa el doble que `ssf2x_en` (300 frente a 131 MB comprimidas; 332 frente a 160 MB):** los
  dos discos tienen los mismos 567 archivos, pero en el CDI español las músicas de escenario (`S_*.ADX`, 15 archivos)
  son **piezas largas** de 3,5-4,5 minutos (por ejemplo `S_RYU_02.ADX`: 11,5 MB, 242 s) en vez de los bucles de
  ~1 minuto del original (2,6 MB, 56 s). Mismo formato (ADX tipo 3, estéreo, 44,1 kHz): el ADX apenas se comprime, así
  que se nota entero en la imagen. Medido con `gdi.open_disc(...).walk()` y la cabecera ADX de cada archivo.
  **El usuario la descarta (2026-11-12: "no merece la pena la española"):** borrados de la Pi .250
  `dc-ssf2x_es_dc2naomi.{bin.gz,vmu}` y su fila (copia `romsinfo.csv.bak_ssf2x_es`; reimportado con `importcsv.py`).
  La copia del PC (`isosdream/`) se queda.
  Después también la japonesa (usuario: "la japonesa la quitamos también, dejamos la inglesa"): borrados
  `dc-ssf2x_dc2naomi.{bin.gz,vmu}` de la .250 y su fila (copia `romsinfo.csv.bak_ssf2x_jp`). En la .250 solo queda
  `dc-ssf2x_en`. La copia del PC (`dreamcastisos/ssf2x_dc2naomi.*`) se queda.
- **Limpieza de la Pi .250 (usuario, 2026-11-12: "quita las líneas huérfanas y las versiones de Dreamcast que ya
  estén en arcade"):** fuera del CSV (copia `romsinfo.csv.bak_dc_dupes`, reimportado) las filas huérfanas
  `ikaruga_joy_dc2naomi` e `ikaruga_joy_g2cpu_dc2naomi` (sus ficheros ya no estaban) y `dc-ikaruga` y `dc-cspike_es`
  (el usuario tiene los originales de NAOMI, `n1-ikaruga_v3` y `n1-cannon_spike`); borrados sus `.bin.gz` y `.vmu`.
  Las copias del PC se quedan. **Para la receta 4 (leer la caja negra cargando otra imagen) ya no está Ikaruga en esa
  Pi:** usar la más pequeña que quede (`dc-spf2x`, 110 MB) o subir una.
  **Corrección (13:40): Ikaruga de Dreamcast vuelve a la .250.** El original de NAOMI (`n1-ikaruga_v3`, y también
  `n1-shikigami_no_shiro_2`) es **vertical** (monitor girado); la versión de Dreamcast se juega en un monitor
  horizontal, así que **no es un duplicado**: no quitar versiones de Dreamcast de juegos verticales aunque esté el arcade.
  Subidos desde el PC `dc-ikaruga_dc2naomi.{bin.gz,vmu}` (md5 de la `.gz` `87f68248de681d7cde707b90737c66a4`; el `.vmu`
  es el desbloqueado del PC: lo guardado en la placa desde el día 11 se perdió al borrarlo) y su fila de nuevo en el CSV
  (copia `romsinfo.csv.bak_ikaruga_back`). Vuelve a servir para la receta 4 (14 MB).
- **Ojo con la Pi .250:** se reinició dos veces mientras comprimía una imagen con `pigz` (`vcgencmd get_throttled` =
  `0x50005`: **falta de tensión**). En esa Pi no comprimir imágenes grandes: hacerlo en el contenedor o en el PC y
  subir el `.gz` ya hecho (`piput.py` / `tools/board/piup.sh`).

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

## Bangai-O (USA) para el mueble estándar (2026-11-12) — `dreamcastisos/dc-bangaio_dc2naomi.bin.gz`

Juego nuevo para el catálogo (Treasure, `T40217N`): `dc2naomi.py --cab joy` en 19 s, parches localizados por
`findpatch`, imagen **98 MB** (66 MB comprimida); `cmpimage.py`: 663 archivos iguales, IP.BIN y 1ST_READ iguales.
VMU `bangaio/v95185` ("all stages completed"; la otra publicada solo llega a la fase 24). Fila en
`dreamcastisos/filas_romsinfo.csv`; no subido a la Pi (lo hace el usuario). Sin probar en placa.
**Sin música:** el disco lleva 34 pistas de audio de CD (≈ 680 MB, toda la banda sonora); efectos y voces van en
archivos y sí suenan. Es el mejor candidato para la idea pendiente de reproducir CD-DA (recodificada para caber: con
98 MB de imagen quedan ~400 MB libres en la NetDIMM).

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

## Mario Kart 64 (homebrew KallistiOS, mk64-dc) — perfil `mk64`, mueble Crazy Taxi. ✅ FUNCIONA EN PLACA (2026-11-13)

**Qué es.** El port de Dreamcast de la decompilación de Mario Kart 64, de **jnmartin84**
([mk64-dc](https://github.com/jnmartin84/mk64-dc), commit `1cbad2ef`, 2026-08-23: audio mezclado por el AICA, backend
Fast3D directo al PowerVR, 30 fps a 4 jugadores). No es un juego de Dreamcast comercial: **lo compilamos nosotros**
desde su código con la ROM del usuario (`Mario Kart 64 (U) [!].z64`, MD5 `3a67d9986f54eb282924fca4cd5f6dff`), y
dc2naomi lo empaqueta con el layout `rebuild` (directorio con los archivos del disco). Todo en un comando:

```sh
KOS_NAOMI_ENV=/opt/toolchains/dc/kos-naomi/environ.sh homebrew/mk64/build_mk64.sh baserom.us.z64
# -> build/mk64_dc2naomict.bin(.gz) (17,5 MB / 11,6 MB). PROFILE=mk64_dbg para la de diagnóstico.
```

El script clona KallistiOS `680d1862` (la que pide mk64-dc) en un árbol propio y le aplica el parche, clona kos-ports
para `sh4zam`, compila Torch (HarbourMasters) y las herramientas de la decompilación, extrae los assets de la ROM, compila
el juego (`mk64.bin` 8,45 MB + `dc_data/` 8,3 MB + `loader.bin` como `1ST_READ.BIN` sin cifrar + `IP.BIN` de
`makeip`) y llama a `./build.sh mk64`. Nada con copyright en el repositorio: ni la ROM, ni código de mk64-dc (que no
tiene licencia publicada; se descarga de su autor), ni nada derivado de la ROM. Comprobado de cero el 2026-11-13.

**En placa (2026-11-13, usuario):** "todo perfecto", con "alguna caída de frames, lo normal" (es el port; en NAOMI no
se ha tocado el rendimiento). Música, vídeo a 640×480 VGA, mandos.

**Mandos (`pads: "mk64"`, `DIMM_PAD_MK64 = 8`, elegidos por el usuario):** acelerador = A (acelerar), freno = B
(frenar), **palanca adelante = R (salto y derrape), palanca atrás = Z (usar objeto)**, START al soltarlo; con START
apretado la palanca es arriba/abajo (menús); volante a tope = izquierda/derecha. El volante va **2,5 veces más rápido**
alrededor del centro (la dirección a tope al 40 % del recorrido; lo pidió el usuario: "tener que girarlo mucho
menos"). El port traduce el mando de Dreamcast así (`src/main.c`, `update_controller`): A = N64 A, X = N64 B, gatillo
L = Z en carrera / L en menús, gatillo R = R, Y = C-arriba; por eso el residente manda acelerador → A, freno → X,
palanca adelante → gatillo R y atrás → gatillo L.

**Pendiente:** VMU (ahora `flags` sin `0x8000`: no guarda récords ni opciones; el juego guarda en la VMU con su propio
formato, así que no hay partida que buscar en bucanero/dreamcast-saves: nunca hubo un Mario Kart 64 comercial de
Dreamcast); versión en **español** con el parche de **blade133bo** (v1.1, `Mario Kart 64 (ES).xdelta`, se aplica a la
misma ROM: comprobado que da 12.582.912 bytes, mismo tamaño, 1,4 % de bytes cambiados en 82 zonas, nada movido de
sitio; habría que saltarse la comprobación de MD5 de la compilación y ver si Torch extrae bien los assets cambiados).

### Lo que hubo que arreglar en KallistiOS (todo en `kos-680d1862-naomi_host.patch`, bajo `#ifdef NAOMI_HOST`)

mk64-dc se compila para Dreamcast (`KOS_SUBARCH=pristine`), así que KallistiOS hace lo que haría en una Dreamcast. En
la NAOMI 2, por orden de aparición en placa:

| # | Dónde | Qué pasaba | Arreglo |
|---|---|---|---|
| 1 | `hardware/video.c` `vid_check_cable()` | escribe PCTRA para leer el cable: **mata el TA** (sección "CAUSA ENCONTRADA") → pantalla negra con ruido | devuelve VGA sin escribir nada (el residente ya pone VGA en el AICA `0x2c00`) |
| 2 | `kernel/stack.c` | la NAOMI 2 no hace espejo de `0xadffffff` → KOS cree 32 MB y pone la cima en `0x8e000000`, **encima del residente** | `arch_stack_32m` = `0x8dc00000` (lo mismo que DreamShell y or2006) |
| 3 | `maple/maple_utils.c` `maple_dma_addr()` | sin el gancho de maple no hay mandos (ni VMU) | lee el gancho de la **tabla del residente** (`0x8dc00000`: `"DCLR"`, +8 `maple_hook`) y escribe su resultado en `SB_MDSTAR`; sin tabla (Dreamcast real) hace lo normal. **Mejor que el parche `HOOKST`:** no depende de direcciones y sobrevive a recompilar el residente |
| 4 | `hardware/cdrom.c` `cdrom_init()` | desbloqueo del bus G1 leyendo la BIOS entera (con multibios puede bloquearlo) | no lo intenta |
| 5 | `hardware/g2bus.c` `g2_fifo_wait()` | espera sin límite a que bajen los bits 0/4 de `SB_FFST` (`0xa05f688c`): los mismos que `G2CHK0`/`G2CHK4` | 3.000.000 vueltas como el residente, luego sigue; tras el primer fallo solo 1024 (`g2_fifo_stuck` lo cuenta) |
| 6 | `include/dc/g2bus.h` `g2_lock()` | igual, **con las interrupciones apagadas**: congela la placa entera | igual que 5 |
| 7 | `hardware/spu.c` `spu_memload()` | sube el audio por DMA G2 del AICA, que en esta placa no termina (`ADST` se queda a 1, como en `G2CPU`): bucle infinito cediendo el turno → pantalla quieta/temblando tras el logo de Nintendo | siempre por las store queues (CPU) |
| 8 | `kernel/startup.S` + `kernel/exec.c` | **el fallo de fondo, descubierto leyendo la RAM:** la primera instrucción guarda el SR de quien lo lanza en `_arch_old_sr` y tres instrucciones después reescribe el CCR con OCI (invalida la caché de datos **sin escribirla**). El loader de dc2naomi (KallistiOS) deja la caché en copy-back y el residente no la toca: el SR se queda en una línea sucia que se tira, en RAM queda 0. Al saltar del cargador de Mario Kart al juego (`arch_exec`), `ldc r0,sr` con SR = 0 = **modo usuario**: error de dirección en la siguiente instrucción (`EXPEVT 0x0e0`), excepción contra la tabla del residente rellena de `0xff`, reinicio, y la NetDIMM vuelve a cargar: **logo de Nintendo en bucle, sonido y tembleque** | guardar el SR por P2 (sin caché); y `arch_exec` nunca carga un SR sin el bit MD (usa `0x400000f0`, el del residente) |

Los puntos 5, 6 y 7 eran cosas que ya habíamos medido en placa con juegos comerciales (`G2CHK0/4`, `G2CPU`): KallistiOS
tropieza igual. DreamShell no lo había destapado porque dibuja en 2D y casi no usa el AICA. El 8 afecta a cualquier
programa de KallistiOS que encadene otro (`arch_exec`) lanzado por el loader de dc2naomi; también a or2006/or37 si
alguna vez lo hacen.

**Descartado:** el camino de DMA de texturas a `0x11000000` que no escribe en la NAOMI 2 (`TEXPATH`) no afecta: el
port sube las texturas con `pvr_txr_load()` (store queues a VRAM), no por DMA.

### Depuración en placa de un homebrew de KallistiOS (con NAOMI_HOST)

Los peeks del residente (`tools/board/pk.py`) **no sirven** con un programa de KallistiOS: el residente solo atiende la
NetDIMM dentro de sus llamadas de GD-ROM y del gancho de maple, y KallistiOS lee el disco con sus propias rutinas. Lo que
devuelven es basura (el valor de la ventana, `a0000000`) o se agota el tiempo. Por eso el parche añade al programa:

- **Un contestador de peeks propio** (`naomi_peek_poll`, `maple_utils.c`), mismo protocolo que el residente y que
  `dimmcomms.c` de libnaomi (DragonMinded), llamado desde un hilo cada 2 ms (como `naomi_dimmcomms.c` del Daytona nativo)
  y en cada vblank. Ventana en `0x01fffffc` igual que el residente: `pk.py` funciona también.
- **`naomi_live`** (dirección con `sh-elf-nm`; la imprime `build_mk64.sh`): vblanks, peeks atendidos, PC/PR que
  interrumpió el último vblank y los 16 últimos (un perfilador por muestreo), contexto del hilo principal, y **las
  últimas 8 KB de todo lo que imprime KallistiOS** (dbgio y la consola de dcload, aunque estén desactivadas).
- **Parar en vez de reiniciar:** `arch_abort/exit/reboot` se quedan en un bucle atendiendo peeks; la excepción no
  atendida (`irq.c`) deja código, evento, PC, PR, SR, R0–R15, EXPEVT, INTEVT y TEA en `naomi_live`.
- Lector: `live.py IP ADDR` de [naomi-pi-tools](https://github.com/0skarzer0/naomi-pi-tools) desde la Raspberry (reconoce el bloque `LIVE`; sondea hasta que el programa se detiene y vuelca el
  log). **Sin `timehack.py` corriendo** mientras se lee (`wipiloader.py … hackoff`, o matarlo): con los dos hablando
  a la NetDIMM los peeks devolvieron valores viejos.

Así salió el punto 8: log con `kernel panic: unhandled IRQ/Exception` justo tras "Please wait..." del cargador,
`EXPEVT 0x0e0`, `SR = 0`, PC en `arch_exec_at` tras `ldc r0,sr`. Y con el juego ya corriendo, el anillo de PCs lo
mostró dibujando (`gfx_sp_tri1_impl`), subiendo texturas y con la música en marcha (`note_set_vel_pan_reverb`).

Otras herramientas que ayudaron: el perfil `mk64_dbg` (`CONSOLE | DIAG`: el `printf` del juego en pantalla y los
tiempos de 31 kHz del cargador restaurados) y Flycast con la BIOS de NAOMI 2 del usuario (`epr-23608b.ic27`, CRC32
`a554b1e3`, en un `naomi2.zip`): arranca el loader y reconoce el juego, pero se queda en negro tras "Starting..."
(no se siguió: la placa con el lector `live.py` resultó más directa).

### Notas de la compilación

- **Torch:** `make` dentro de `tools/torch` no hace falta; `cmake -B cmake-build-release -GNinja` y `cmake --build`.
- **Assets `.mio0`:** los `.mk` de `assets/include/` cuelgan las texturas de objetos que no son los que las incluyen
  (`data/textures_0a.s` incluye `assets/character_select/mario/mario_face_00.mio0`, pero el `.mk` la pone como requisito
  de `data/course_player_selection.o`). Con `make -j` se ensambla antes de que exista. `build_mk64.sh` compila primero
  los 52 objetos que nombran esos `.mk` y luego todo.
- **No usar el `.cdi`/`.iso` que circulan** (el usuario trajo tres): el de diciembre de 2025 lleva 640 MB de relleno
  delante de los datos y no cabe en la NetDIMM; el `.iso` es para DreamShell; el CDI de BootDreams es de agosto de 2025.
  Además ninguno lleva los arreglos de arriba.
- **gitlab.com no es accesible** desde el entorno de la IA: `mkdcdisc` no hace falta (dc2naomi hace el ISO con
  genisoimage).

**Pi .60:** `dc-mk64_dc2naomict.bin.gz` (nombre y fila del CSV de siempre: `audit_name` `mk64_dc2naomict.bin.gz`) y
`dc-mk64dbg_dc2naomict.bin.gz` (fila "Mario Kart 64 (DC diagnostico)"; borrable). Copia de la versión con mandos
`pole` en `/boot/roms/_test/dc-mk64_dc2naomict.bin.gz.pole-2026-11-13`. **La última imagen (palanca adelante = salto,
y free play / attract mudo puestos con `naomi-ct-patches/tools/sysdef_all.py` como piden las imágenes nuevas) quedó en la
carpeta `dc2naomi` del PC sin subir: la .60 estaba apagada** (2026-11-13 17:50). Al subirla, el nombre y la fila no
cambian.

## Descartados por los mandos (2026-11-13)

Repasando los 11 que no caben sin recortes, el usuario descarta por jugarse mal con palanca digital **Jet Grind Radio,
Fur Fighters y Evil Dead**: sus CHD borrados de `dreamcastisos/` (con su permiso de borrado), y el `.part` que quedó de
Evil Dead en `_to_delete/`. Quedan por recortar, por orden de interés para la palanca: Vampire Chronicle, VF3tb, Tech
Romancer, Psychic Force 2012, Pro Pinball Trilogy. Después borrados también Sonic Adventure 1 y 2 y Rayman 2 (usuario,
mismo día): de los recortes solo quedan esos cinco.

## OutRun 2006 C2C "Turbo v3" de ArkRetro compilado para NAOMI (2026-11-17) — `h-orc2c3_dc2naomict`, sin probar en placa

El usuario dejó la v3 (`outrun coast2coast_outrunners_TAXI_V3.rar`, GDI de 984 MB, IP.BIN `ORC2CDC` de 2026-11-14) y
luego las fuentes (https://github.com/ArkRetro/ORC2CDC, `3539fa6`). Sin las fuentes no cabía (el juego sin música ya
son 458 MB; la música, 492 MB en ADPCM de Yamaha estéreo a 44,1 kHz). Con ellas: **compilado desde el código con
KallistiOS `NAOMI_HOST`, datos grandes comprimidos (ZCK1, zlib en trozos de 64 KB) y 25 de las 29 canciones largas a
22 kHz** (reparto del usuario: a 44 kHz `MUS0`–`MUS3` de OutRun 2 y las 35 pistas cortas; si no cupiera, bajar otra
larga, nunca las cortas). Rechazó LZMA (más compresión) por riesgo. Todo en **`homebrew/orc2cdc/`** (README con los
pasos, parches de KallistiOS `d81aa3f` y de ORC2CDC, `zck.py`, `adp22.c`).
- Imagen **500,6 MB** (453 MB la `.gz` a nivel 1), perfil nuevo **`orc3`** (`tools/games.py`; sin parches) y opción
  nueva **`--perfil NOMBRE`** de `app/dc2naomi.py` para forzar un perfil (un homebrew recompilado cambia de suma cada
  vez). Mandos `wheel`, VMU vacía (no hay partida publicada).
- Pi .60: `/boot/roms/h-orc2c3_dc2naomict.{bin.gz,vmu}` (md5 de la `.gz` `561212d584c49ddd3a277ac0150be393`), fila
  añadida (copia `romsinfo.csv.bak_orc2c3`, reimportado; `audit_name` `orc2c3_dc2naomict.bin.gz`, como `h-or37`).
- Trabajo en el PC del usuario: `otros/orc3/` (`datos/` = los ficheros ya comprimidos y recodificados, `gdi/` = el
  disco y la imagen, `1ST_READ.BIN`, `IP.BIN`); scripts sueltos `~/orc3data.py` (el paso 3 del README) en la VM.
- **Sin probar en Flycast ni en placa.** Qué mirar en placa: que arranque (si no, leer el bloque `LIVE` con
  `naomi-pi-tools`), que la música suene (las de 22 kHz a su tono) y cuánto tarda en cargar una etapa conduciendo.
- Toolchain en el contenedor de la nube: apt solo va por HTTPS a través del proxy (cambiar `http://` por `https://` en
  `/etc/apt/sources.list.d/ubuntu.sources` y `-o Acquire::https::Proxy=$HTTPS_PROXY`); kos-ports no puede bajar de
  zlib.net (zlib clonado de GitHub); el gcc de Ubuntu no trae C++ (SH4ZAM a mano).
- **2026-11-18 00:00, en placa (Pi .60, `dc2naomi_send.py`, 3 min):** arranca. `live.py 10.0.0.4 0x8c0c54a0` (dirección
  de `_naomi_live` de esta compilación) desde `/root` de la Pi: KallistiOS ve mando y VMU en A, `MVTS.VQV` entero (7722 KB
  en 61 lecturas, sin errores: la lectura ZCK1 va), `MVATTR.VQV` saltado, música del menú, licencia `OR2C2C` guardada y
  releída bien, menú principal y selección de coches. **Pendiente:** el juego solo ve 16 MB (`RAM: al arrancar en uso
  12941K, libre 309K` y un `Out of memory` de 212 KB): el `gcc-sh-elf` de Ubuntu no define `__KOS_GCC_32MB__`, así que
  `arch.h` fija `_arch_mem_top` en `0x8d000000` aunque `startup.S` ya mide `0x8dc00000`. Arreglo: `-D__KOS_GCC_32MB__` en
  `KOS_CFLAGS`, recompilar KallistiOS y el juego (unos 12 MB más). Las cachés de ZCK1 (~330 KB de bss) restan de esos 16 MB.
- Los árboles de trabajo del contenedor (`/home/claude/orc-build/kos`, `.../orc`) son clones de terceros: sus cambios
  solo se guardan como los dos parches de `homebrew/orc2cdc/` (regenerados con `git diff`).
- **2026-11-18 00:40, segunda versión** (pedida por el usuario: sin sonidos en carrera; quitar OutRunners, el taxi y el
  turbo taxi, los vídeos, dejar una sola canción larga, aprovechar la NAOMI 2): 32 MB (`-D__KOS_GCC_32MB__`), sin
  vídeos / OutRunners / `COCHE07.DAT` (taxi), menú con `-DSIN_OR_TAXI`, largas = copias de `MUS0`, nada comprimido:
  **491,6 MB**, mismo nombre `h-orc2c3_dc2naomict` (md5 `.gz` `86c214c54795d0cb9185292225441bb0`). En placa (live.py
  `0x8c0bf488`): `VOZ: VOCES.DAT, 34 muestras, 207 KB en el AICA` (antes no cabía), sin "Out of memory". Detalle en
  `homebrew/orc2cdc/README.md`. No se creó fork de ORC2CDC (el usuario no contestó): sigue como parche.
- **2026-11-18 01:30-03:30, trabajo desatendido (el usuario: medir en la demo, "estable a 30 mejor que subidas y
  bajadas", toda la música a 22 kHz y 8 largas: MUS0-7):** medidas con `homebrew/orc2cdc/med.py` desde la Pi .60
  (`/root/med.py`, `corre.sh` / `lanza.sh`: envía una imagen, espera al arranque y mide; `resumen.py` resume un CSV).
  Resultados en **`homebrew/orc2cdc/MEDIDAS.md`**: la CPU no llega a 45 fps (~30 ms por cuadro); tope a 30 fps,
  lecturas en trozos de 4 sectores (`GD_TROZO`) y por DMA del G1 (`DIMM_DMA`, ahora en el perfil `orc3`). Imagen nueva
  con el mismo nombre (`h-orc2c3`, md5 `.gz` `654c485f8b03d8ded6534ba244ecdc7c`), base ORC2CDC `a689a9a`.
  Imágenes de prueba `h-orcp{B,D,E,F,G,H,P}` subidas a la Pi .60 para medir (sin fila en el CSV).
- **2026-11-18 08:15:** vuelve el taxi (`COCHE07.DAT` en `datos3`, `comun/menu.c` ya no lo bloquea); OutRunners sigue fuera (14 MB: no cabe sin quitar una canción) y la tarjeta de All I Want también. `h-orc2c3`, md5 `.gz` `a17a7cab16f8c08c5e8d4a7c691d82fd`.
- **2026-11-18 09:30:** el usuario no podía cambiar de marcha: en ORC2CDC el cambio manual va en la cruceta arriba/abajo y A / B eran acelerador / freno a fondo, así que la palanca del mueble (B adelante, A atrás) frenaba y aceleraba. `-DNAOMI_PALANCA`: B sube, A baja, gas y freno solo de los pedales. md5 `.gz` `a0034116d6077beb42b8ebd780a24e78`.

## OutRun C2C para NAOMI: `h-orc2c4_dc2naomict` definitiva (2026-11-18 noche)

Sustituye a `h-orc2c3` en la Pi .60 (fila 53 de `romsinfo.csv`, copia `romsinfo.csv.bak_orc2c4`, reimportado; VMU
copiada de la `h-orc2c3`). Rayas más lejos, reflejo del escenario (panorámicas `REFLEJO.DAT` de `homebrew/orc2cdc/reflejo.py`),
sombras de la calzada sobre el coche, cristales transparentes, rojo menos rosa y más OPB. Detalle, medidas y glitches
pendientes (panel del túnel de LASV, nube azul): `homebrew/orc2cdc/README.md` y `MEDIDAS.md`. En la Pi: `/root/manda.sh
IMAGEN` (para med.py y los `vmu.py watch` que se queden y manda la imagen); había vigilantes de VMU de envíos viejos
guardando en la VMU de otra imagen. Imágenes de prueba en `/boot/roms/h-orcp*` (se pueden borrar).

## The Last Blade 2 Final Edition (Japón, parche VGA) — perfil `lb2fe`, Pi .250 (2026-11-18) — sin probar en placa

**Problema:** `dc-lastblade2_dc2naomi` (USA) en la .250 se queda en negro tras el logo de SEGA y el monitor dice
"OUT OF RANGE … 15.2KHZ 29HZ". La versión USA no tiene modo VGA: el campo de periféricos del IP.BIN es `07BBA00` (bit
VGA 0x10 a cero) y el juego fija NTSC 480i (15 kHz) diga lo que diga el cable. No se arregla con un parche de cable.

**Solución elegida por el usuario:** convertir su `THE LAST BLADE 2 FINAL EDITITION (JAPONES)-(VGA).7z` (T3107M
V1.003, IP.BIN `07BBA10`, parche VGA de la comunidad; 774 MB en `.gdi`):
1. `discfiles.py DISCO ORIG .SFD` + `sfdbatch.py`: los 29 `ZSFD/*.SFD` de 477 MB a 106 MB.
2. `withfiles.py NUEVOS --cab joy --batch disc.gdi` → 404 MB (323 MB en .gz). Hizo falta arreglar `withfiles.py`
   (f08f75d): con un `.gdi` de origen los sectores puestos a cero no se quitaban y salían 775 MB.
3. **Perfil `lb2fe`** (catálogo por SHA1 del 1ST_READ `6d0dd952…`). `findpatch.py` adivinó mal los puntos del cable
   (0x8c13a47e y 0x8c15d38a no son lecturas de PDTRA: corrompían código y se colgaba tras SEGA). Los buenos:
   - 0x8C132B7E `mov.w @r3,r4` (PDTRA, 0xFF800030) → `mov #0,r4`;
   - 0x8C15588A `mov.w @r0,r0` → `mov #0,r0`: es la comprobación del propio parche VGA (si cable = VGA llama a
     0x8c11f534(0), que pone los bits de salida de audio del AICA 0xa0702c00);
   - HOOK en el literal 0x8C14ADD8 (función "a física" 0x8c14c426).
4. Con eso salían los logos (SEGA, Sofdec, SNK) y luego **negro con el juego vivo** (la música y la demo seguían: la
   caja negra mostraba lecturas de `MUSIC.AFS`, `VOICE.AFS`, `TIT.GKC`, `GE*.GKC`). Con `FC_REGTRACE=1` en Flycast:
   al pasar a 320×240 se escribe **VO_STARTY = 0x0027fff8** → campo 1 = línea 1016, fuera de la pantalla. Causa: un
   fallo del parche VGA. Su código (0x8c1557c6) guarda el VO_STARTY de su tabla (0x00280028) en las variables del
   juego al revés: `extu.w` → 0x8cef9f70 (campo 2) y `shll16` → 0x8cef9f6c (campo 1 = 0x00280000). El juego suma cada
   cuadro su desplazamiento vertical (0x8cef9f64 = -8 en ese modo) y escribe `[9f6c]+d | ([9f70]+d)<<16`
   (0x8c13c766). **Parche:** 0x8C1557D2 `shll16 r0` (0x4028) → `extu.w r1,r0` (0x601D). En Flycast llega a la intro
   ("1864年", SNK Presents…), al título y al menú (STORY / VS / TIME ATTACK / …).
5. Subida a la .250 como `dc-lastblade2fe_dc2naomi.bin.gz` + `.vmu` vacía (md5 del .gz `cefbbd0f…`), comprimida en la VM
   del PC (no comprimir en la Pi .250: se reinicia por baja tensión). En `romsinfo.csv` la fila de
   `dc-lastblade2_dc2naomi.bin.gz` (USA) se cambió por la de la Final Edition (copia: `romsinfo.csv.bak_lb2fe`) y se
   reimportó. El `.bin.gz` USA y su `.vmu` siguen en `/boot/roms/` sin fila (no salen en el menú).
6. Cargada con `dc2naomi_send.py 10.0.0.3` dentro de `nohup sh -c "…; timehack; vmu watch"`. **Ojo:** `pkill -f
   timehack.py` lanzado por SSH se mata a sí mismo (el patrón está en su propia línea de órdenes): usar
   `pkill -f "[t]imehack.py"`. Y el envío de 340 MB (unos 2 min) tarda más que el tiempo de espera de `pi.py`: lanzarlo
   con nohup. `dc2naomi_send.py` de la .250 ya arranca él solo el vigilante de la VMU al acabar: no lanzar otro (quedaron
   dos y se mató uno); `timehack.py` sí hay que arrancarlo a mano. Cargada 2026-11-18 21:10 (hora de la Pi, que va
   atrasada), sin probar aún en placa.

**Para otros juegos con parche VGA:** si tras los logos queda negro con el juego vivo, mirar VO_STARTY/VO_STARTX con
`FC_REGTRACE=1` (`tools/flycast/run1.sh`): los parches VGA reescriben los modos de vídeo y pueden dejar mal las
variables que el juego reutiliza cada cuadro.


## OutRun C2C NAOMI: versión final `h-orc2c8_dc2naomict` (2026-11-19 00:40)

El usuario la da por buena. Detalle en `homebrew/orc2cdc/README.md` (cabecera) y `MEDIDAS.md`. Lecciones:
- **La imagen cortaba el `1ST_READ.BIN`**: `build_image.nonzero_runs` mira qué sectores tenían datos en el disco tal y
  como era; un `1ST_READ` más grande que lo que había con datos en el hueco (relleno de ceros) sale cortado y la placa
  se queda en "starting..." del cargador. Rellenar el hueco con 0xFF; `tools/withfiles.py` ya lo detecta y se para.
- **No leer de la NetDIMM (peek/poke, live.py, med.py) mientras la placa arranca**, y no dejar varios
  `dc2naomi_vmu.py watch` a la vez: la NetDIMM atiende una conexión y los vigilantes viejos escribían la VMU de otra
  imagen. `/root/manda.sh IMAGEN` en la Pi para los que haya y manda.
- **La SD de la Pi .60 dio errores de FAT** ("invalid cluster chain") y pasó `/boot` a solo lectura; tras reiniciar
  escribe, pero **falta un `fsck.vfat`** (pendiente del usuario). Imágenes de prueba en `/boot/roms/h-orcp*`,
  `h-orcRL*`, `h-orc2c4..7*` (se pueden borrar).

## Fallos del 2026-11-19 (TD6, Airline Pilots, Wacky Races, SPF2X, Rush 2049, MSR)

El usuario probó en placa y avisó: TD6 se queda con la música sonando tras START; Airline Pilots (NAOMI original, pasado
de la .250 a la .60) dice "CAUTION 51 game assignments are incorrect"; Wacky Races pide un mando en el puerto A; SPF2X
se cuelga tras los logos de CAPCOM y ADX; Rush 2049 (las dos) deja de responder y va lento tras START; MSR, pantalla
negra tras el vídeo.

**Programas cargados encima de 1ST_READ (Wacky Races, Test Drive Le Mans, MSR).** En esos discos `1ST_READ.BIN` es un
cargador y el juego otro programa en 0x8c010000 (Wacky Races: `WACKY.BIN` + `MOVIE.BIN`; Le Mans: `FMV.BIN` +
`LEMANS24.BIN`; MSR: `MSR.BIN`). El perfil automático solo parcheaba `1ST_READ.BIN`: el programa siguiente usaba su
propio driver de maple contra el MIE (caja negra: 0 llamadas al gancho). Cómo verlo: `hdr.py` del perfil + volcado de
RAM en Flycast (`DUMP=1`): las palabras de comprobación ya no están y `findpatch` sobre la RAM da otro gancho.
- `app/dc2naomi.py other_programs()`: el perfil automático añade un grupo por cada `.BIN/.EXE/...` de 64 KB-8 MB con
  muchos literales 0x8cXXXXXX ≥ 0x8c010000 en el que findpatch encuentra gancho de maple (cable y gancho, como 1ST_READ).
- `tools/addprograms.py IMAGEN.bin.gz DISCO [SALIDA]`: añade esos grupos a una imagen ya hecha (no toca los ficheros
  sustituidos: vídeos recodificados, audio mono). Hechas en `otros/fix/` del PC: msr, rush2049, rush2049_9, tdlemans.
- Ojo: `2_DP.BIN` (Rush 2049, MSR, SW Racer, TXR2, Net de Tennis, Vampire Chronicle) y `DP_BEXP3.BIN` (TNN) son el
  navegador DreamPassport, no el juego: parchearlo no cambia nada.
- Wacky Races reconvertido con el perfil nuevo (`dreamcastisos/Wacky Races (USA)_dc2naomict.bin.gz`): en Flycast ve el
  mando y la VMU y llega a los menús y a elegir piloto.
- Escaneo de todos los CHD de `dreamcastisos` (`~/scanall.py` en la VM): solo los citados tienen otro programa del juego.

**MSR: lectura en streaming del vídeo (`DIMM_DMAIRQ`, 0x80000).** Con `MSR.BIN` ya enganchado seguía negro: pedía
`DMA_READ_REQ` (0x1c) de 0x2e sectores de `MOVIES/MSR.SFD`, recibía un `REQ_DMA_TRANS` de un sector y volvía a empezar.
Espera la interrupción de fin de DMA del GD (ISTNRM bit 14), que nuestra copia no daba. Como el HLE de Flycast
(`core/reios/gdrom_hle.cpp`: `asic_RaiseInterrupt(holly_GDROM_DMA)` en REQ_DMA_TRANS, `asic_CancelInterrupt` en
G1_DMA_END): con la bandera, cada REQ_DMA_TRANS hace una DMA G1 de 32 bytes real al salir de la llamada (lo que ya se
hacía con Windows CE), G1_DMA_END borra el bit 14 y su callback se llama al salir de la llamada (llamado dentro, o desde
la interrupción anidada, sus GET_CMD_STAT recibían "ocupado" para siempre: tormenta de interrupciones). Sin la bandera
no cambia nada para los demás juegos. En Flycast MSR llega al reloj, la zona horaria y "PRESS START BUTTON".
`tools/newloader.py` con `FLAGS=0x80000` → `otros/fix/dc-msr_dc2naomict_v2.bin.gz` (falta subirla a la .60).

**SPF2X: residente viejo.** La imagen de la .250 (2026-11-09) era anterior a la limpieza de RAM (6c95d60) que arregló el
mismo síntoma en SSF2X. `tools/newloader.py VIEJA NUEVA` pone el cargador y residente actuales conservando título,
cabecera y datos (no hace falta el disco). En Flycast: menú principal. **Subida a la .250** (md5 `0725d92c…`; la vieja en
`/boot/spf2x_old.bin.gz.bak`). En la .250 hay más imágenes con cargadores anteriores (md5 de la zona del cargador):
dcop_es, kof02, motw, rcotton_en, sf3ts, soulcal, ysgw (grupo más viejo); buzz_es, ikaruga; ssf2x_en, toystory2_es.
Si alguna se cuelga igual, `newloader.py`.

**Airline Pilots (NAOMI original):** la cabecera del juego (0x429 = 0x01) solo admite mueble de 1 jugador; la BIOS da
CAUTION 51 si SYSTEM ASSIGNMENTS → CABINET TYPE no coincide. Arreglo: ponerlo a 1 PLAYER(S) en el test de la .60. Los
controles para volante y pedales: pendiente.

**TD6 — resuelto en placa (2026-11-19 13:39, el usuario: "llega al menú!").** Con la caja negra en la placa (Pi .251,
`tools/board/pk.py`): tras START el juego lee `FRONTEND/FRONTEND.TEX` entero (DMAREAD de 0x635 sectores, 3,2 MB, hasta
0x8d000000); la lectura acaba bien (estado del residente: COMPLETE consumido, 0x31a800 bytes) pero el juego no pide nada
más: la música del título sigue y el icono de carga queda quieto; sus hilos (tareas por cuadro a 0x8c0ce5a8, que miden
tiempo con el TMU2) siguen vivos. En Flycast la misma imagen sigue (la siguiente lectura es el sector 0x4951e).
Con `read_chunk` = 4 (cada EXEC_SERVER copia 8 KB con las interrupciones cortadas, no 64 KB) puesto en vivo con
`tools/board/pp.py 10.0.0.4 0x8dc05174=4` (dirección de `_read_chunk` en `resident.elf` del mismo cargador), llega al
menú. Igual que SF3 Double Impact. Imagen definitiva: `tools/newloader.py` con `READ_CHUNK=4 PAD=9` (md5
`0adb2a72…`), subida a la .251 con la VMU de la sesión de pruebas (copia de la anterior en
`/boot/td6_vmu_backup_20261119.vmu`).
**Mandos de TD6 (elección del usuario):** palanca = arriba/abajo (cambio de marcha), START + palanca = B/A: nuevo
`DIMM_PAD_WHEELUD` (9; `"pads": "wheelud"` en un perfil, `PAD=9` en newloader). El resto como `DIMM_PAD_WHEEL`.
Ojo al muestrear el PC (`DIMM_PCSAMPLE`): TD6 usa el TMU2 como contador libre (TCOR2 = -1), las muestras no valen.
Ojo con `piapp.py`: sale con 0 aunque acabe en PAUSE (subida a medias); comprobar "done" antes de renombrar.
Para cargar desde la Pi por SSH sin que el envío muera al cerrar la sesión: `/root/load.sh IP IMAGEN` lanzado con
`setsid nohup ... &` (mata timehack, envía, arranca timehack; el vigilante de la VMU lo arranca el propio envío).
`pkill -f timehack.py` dentro de un `sh -c` que también contiene "timehack.py" mata ese mismo shell.

**TD6 (lo anterior):** con mando estándar llega en Flycast al menú principal con los créditos de la VMU: el cuelgue es solo de la
placa. Pendiente: cargarlo con la caja negra (flags 0x20000) y que el usuario pulse START. En Flycast el modo de mandos
del mueble no sirve para probar START: sin pedales los ejes de Flycast quedan a media escala y START + freno cuenta
como X (`tools/flycast` sin mapa de pedales; `tools/flycast/img_setpad.py IMAGEN 2` lo pasa a mando estándar para probar).

**Rush 2049:** el menú tras START (en 1ST_READ, no en 2_DP) responde poco y va a ~5 llamadas de maple por segundo en
Flycast (la demo, ~48): el juego dibuja (muestras de PC en su código de texto y del TA), sin llamadas al GD. Sin
resolver; mirar en placa.

**Vigilante de la VMU:** en la .60 seguía uno de TD6 corriendo bajo Rush (el `stop` solo mata el PID del fichero de
estado). Ahora cada vigilante sale si el fichero de estado ya no lleva su PID. Instalado en la .250 (copia
`dc2naomi_vmu.py.bak_20261119`); falta la .60.

Herramientas de prueba en `tools/flycast/`: `img_mkbin.py` (descomprime e inyecta la .vmu como el netbooter),
`img_setpad.py`, `img_setflag.py`, `img_hdr.py` (tabla de parches), `img_box.py` (caja negra de un volcado de Flycast).


## ⭐ CD-DA en NAOMI + RoboCop (DreamNeo CD 4.0), 2026-11-19 — perfil `robocop_dncd`, Pi .250 — **sin probar (ni Flycast ni placa)**

**Cómo toca la música DreamNeo CD** (CDI `[DNCD - 4.0 ROBOCOP][RELEASE]`, 21-10-2026, de IMR Technology / Ian Michael;
juego de Teo Tormo). Sesión 1: 16 pistas de audio (1 y 2 son relleno de 7 s; música 3-16, 194 MB). Sesión 2: pista de
datos de 7,7 MB con `1ST_READ.BIN` (cifrado MIL-CD; KallistiOS git del 28-07-2026, compilado para 16 MB: no pisa el
residente) y los ficheros del juego (`RC.PRG/.SPR/.PCM/.Z80/.FIX`). El código de la 1.0 (público) lo cuenta y la 4.0 hace
lo mismo: el 68000 pide a la BIOS de Neo Geo CD "pista N" (BCD), el emulador lo intercepta y desde un hilo (`cdda_thread`,
cola de 16 órdenes en `0x8c50f548`) llama a `cdrom_cdda_play(N, N+1, 0, CDDA_TRACKS)` = orden **PLAY** del GD-ROM: el
**lector** lee la pista y la manda en digital a la entrada de CD del AICA (volumen con `spu_cdda_volume` = EFSDL de las
salidas 16/17). Para repetir, cuenta la duración que saca de la TOC (`0x8c025922`: (entrada N+1 − N) × 60 / 75
fotogramas, 3600 si no sale) y vuelve a pedirla. **En NAOMI no hay lector ni nada en esa entrada**: por eso dc2naomi
nunca tuvo música CD-DA.

**Lo nuevo (genérico, `DIMM_CDDA` 0x100000):**
- `resident.c`, sección "CD audio": PLAY (pistas, fin inclusivo), PLAY2 (FAD), PAUSE, RELEASE, STOP/SEEK, INIT para la
  música; REQ_STAT, GET_DRV_STAT (3 = sonando) y GETSCD (subcódigo Q) la cuentan, como el HLE de Flycast. Repetición 0 =
  una vez, 15 = siempre. Sonido: dos canales del AICA (por defecto 62/63, PCM 16 bits, 44,1 kHz) con un anillo de
  16384 muestras (32 KB) cada uno en `0x1f0000`/`0x1f8000`, rellenado desde el gancho maple (cada fotograma) y cada
  llamada GD; posición por MSLC/CA (`0x280c`/`0x2814`) devolviendo MSLC a lo que tenía. Si el programa apaga los canales
  (reset del AICA), se vuelven a armar. Volumen y panorama de cada canal = EFSDL/EFPAN que el juego pone al CD
  (`0xa0702040/44`). `cd.stats[6]` = órdenes de play, bombeos, sectores leídos, rearmes, desbordes, finales (para peeks).
  Disco de tipo CD-ROM XA (`0x20`) en GET_DRV_STAT si es un CD con CDDA.
- Cabecera: los 5 `reserved` pasan a ser `cdda_offset, cdda_fad, cdda_count, cdda_cfg, cdda_ring` (mismo tamaño: las
  imágenes viejas leen 0 = sin CDDA).
- `build_image.py`, `gdi.py`, `cdi.py`: `cd_tracks()` y `audio_sector()`; las pistas van detrás de la VMU.

**Lo que usa DNCD del AICA** (desensamblado): su sonido va en los canales **0 y 1** (anillos de 16 KB en `0x11000` y
`0x16000`, `0x8c027f5c`), escritos por sus propias rutinas (`0x8c02760c` arranca un canal, `0x8c02786c` lee CA por
MSLC). El menú usa `snd_sfx_play` de KallistiOS (`0x8c01e520`): puede pasar por cualquier canal; si los 62/63 se
oyeran raros solo en el menú, sería eso.

**Parches** (`tools/games.py`, direcciones de la tabla de exportaciones de KOS): `maple_dma_addr` (`0x8c09c678`) →
`HOOKST`; `cdrom_init` sin desbloqueo del bus G1 (`0x8c094832` nop, `0x8c094834` `bra`); `vid_check_cable`
(`0x8c0a6c50`) = `rts; mov #0,r0` (VGA, sin PCTRA); las 34 esperas de `g2_lock` a SB_FFST bit 5 (`and #32` → `and #0`) y
la del emulador en `0x8c02766a`. No hace falta techo de RAM (16 MB). Flags `0x1404` + VMU + CDDA, mandos `joy`.

**Imagen:** `dc-robocop_dncd_dc2naomi.bin.gz` (197 MB sin comprimir, 120 MB en gz): `./build.sh robocop_dncd
DNCD4.0[ROBOCOP].cdi OUT.bin`. Comprobado aquí solo: la cabecera (flags `0x109404`, audio en `+0x62f000`, FAD 150 +
85001 sectores) y que los sectores de audio de la imagen son idénticos a los del CDI. **Sin Flycast ni BIOS de NAOMI
en esta sesión**: falta probarla en Flycast antes que en placa (receta 2). Si no suena: peek de `cd` (`sh-elf-nm` del
residente) para ver si llegan órdenes PLAY (`stats[0]`) y si el anillo avanza (`played`).

**IP nueva de la Raspberry del mueble Crazy Taxi: 192.168.68.251** (antes .60; cambiada por el usuario el 2026-11-19).
Subidas a la .251 ese día: Wacky Races reconvertido (md5 `7898e31f…`), MSR v2 (otros programas + `DIMM_DMAIRQ`,
`85d9581c…`), Test Drive Le Mans (otros programas, `312db8a9…`), TD6 (arriba), y el vigilante de la VMU nuevo
(copia `dc2naomi_vmu.py.bak_20261119`).
**Primera prueba en placa (Pi .250, 2026-11-19):** cuadraditos (las filas de diagnóstico del residente) y nada más; con
`CONSOLE=1` solo `flashrom_get_region: unknown code '00100'`. Diagnóstico con peeks (`pk.py`), sin Flycast:
- la región de la flash emulada era `00100`, que no es de ninguna consola: ahora `make_flash` escribe los códigos reales
  (`00000` Japón, `00110` EE. UU., `00211` Europa). (Aviso inocuo, pero era real.)
- **cómo ver qué hace un programa de KallistiOS cerrado en la placa:** la variable `irq_srt_addr` (literal de la rutina
  de guardado de registros, aquí `0x8c095d20`) apunta al contexto del hilo interrumpido (r0-r15, spc `+0x40`, pr `+0x44`
  en esta versión de KOS); la lista de hilos sale de `thd_init` (cabeza `0x8c5bb03c`, siguiente `+0`, tid `+0x18`,
  estado `+0x24`, mensaje de espera `+0x2c`, nombre `+0x3c`, contexto `+0x23c`). El residente guarda también en
  `gd_caller` la dirección de retorno y el r15 de la última llamada GD. Así salió: hilo `[kernel]` en `thd_sleep`, desde
  `0x8c0173c0` = el **menú de modo de vídeo** de DreamNeo CD 4.0 (tabla `0x8c0bf1e0`: nombre, modo de KOS, ...), que
  espera al botón A (= botón 1 del mueble) y que no se veía porque dibuja con **bfont** y el residente daba una fuente
  vacía. Pulsando el botón 1 arranca.
- **`DIMM_BFONT` (0x200000):** `FONTROM_ADDRESS` da una fuente con el formato de la BIOS (12x24, 1 bpp, 2 filas cada 3
  bytes; índice 1-94 = ASCII 33-126, 288 = espacio) hecha de `font8x16.h` escalada 1,5 (`resident/biosfont12x24.h`).
  Solo con el flag, porque los caracteres japoneses (más allá) no están.
- Con el cable VGA que damos, el menú ofrece **VGA 640x480 (31 kHz)**, NTSC 640x480, NTSC 640x480 IL, PAL 640x480 y PAL
  640x480 IL (15 kHz). KallistiOS programa el vídeo él mismo y no mira el interruptor de la NAOMI: se elige la frecuencia
  en el menú (monitor trifrecuencia de la .250).
- Menú en placa (foto del usuario): detecta "VGA (RGB HiRes)" y lista VGA, NTSC y PAL. Pero "NTSC 640x480" y "PAL
  640x480" son el modo 3 de KOS = 640x480 VGA otra vez (31 kHz): esas dos entradas de la tabla pasan a ser
  **NTSC 320x240** (modo 2, 240p a 15 kHz, la resolución nativa de la Neo Geo) y **PAL 320x240** (modo 11). Quedan:
  VGA 640x480 (31 kHz), NTSC 320x240 y NTSC 640x480 IL (15 kHz, 60 Hz), PAL 320x240 y PAL 640x480 IL (15 kHz, 50 Hz).
- **Corrección (mismo día): no salía a 15 kHz.** KallistiOS fuerza la sincronía VGA (31 kHz) siempre que
  `vid_check_cable()` diga VGA, pida el modo que pida (y no lee el interruptor de la NAOMI). Se quitan los cambios de la
  tabla del menú y del escalado, y quedan **dos perfiles**: `robocop_dncd` (cable VGA, 31 kHz) y `robocop_dncd15`
  (`vid_check_cable` = `mov #2,r0`, cable RGB: KOS y el menú del emulador, "RGB 640x480 IL / RGB 640x480", a 15 kHz
  como una Dreamcast con euroconector). Imágenes `dc-robocop_dncd_dc2naomi.bin.gz` (md5 `302fcdc1…`) y
  `dc-robocop_dncd15_dc2naomi.bin.gz` (`c6686a59…`). La música CD-DA **suena en la placa** (confirmado por el usuario).
  Receta general: en un programa de KallistiOS, la frecuencia de la NAOMI la decide el cable que devuelva el parche de
  `vid_check_cable` (0 VGA = 31 kHz, 2 RGB = 15 kHz).
- **15 kHz sin entrelazar:** la versión RGB salía a 480i (leído en placa: SPG_CONTROL `0x150`, SPG_LOAD `0x020c0359`
  = 525 líneas), porque las dos entradas RGB del menú usan el modo 4 de KOS (640x480 NTSC IL). En `robocop_dncd15` la
  entrada "RGB 640x480" pasa a ser **"RGB 320x240"** (modo 2, 320x240 NTSC progresivo, 240p). Imagen md5 `68c34a1d…`.
  En la .250 quedan solo "RoboCop 31kHz" y "RoboCop 15kHz" (la DIAG borrada; copia del CSV `romsinfo.csv.bak_robodiag`).
