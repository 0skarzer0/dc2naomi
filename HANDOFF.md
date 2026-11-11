# HANDOFF — dc2naomi (juegos de Dreamcast en NAOMI)

Documento de traspaso entre sesiones (personas o IAs). **Actualízalo en cada sesión.**

## Recetas (para quien continúe, persona o IA): lo que funciona, paso a paso

Leer esto antes de nada. Cada receta se ha hecho de verdad en la sesión del 2026-11-10.

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
- desde un PC de la red del usuario: `PIHOST=… PIPASS=… python3 pi.py 'ORDEN'` y `piput.py LOCAL REMOTO`;
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
con claridad qué se ha probado en placa y qué sólo en Flycast.

## Objetivo

Arrancar juegos de **Dreamcast** en una **NAOMI / NAOMI 2** por netboot (NetDIMM), sustituyendo la BIOS de
Dreamcast por un programa residente. Si funciona, sirve para recopilatorios (Yu Suzuki Game Works, Namco
Museum, Midway…) y ports (Wipeout, Mario Kart 64).

## Estado (2026-11-09)

| Juego | Placa real | Mueble |
|---|---|---|
| Crazy Taxi 2 (US) | ✅ **Terminado** (`ct2h7`, salto con doble toque); `ct2h8` = `ct2h7` + VMU en fichero (Flycast OK, placa pendiente) | Crazy Taxi |
| Ikaruga (JP) | ✅ **Terminado** (`ikaruga_joy`, mandos `joy`) | estándar |
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
**`sf3di` (SF III Double Impact) no funciona:** 1ST_READ es un cargador; el menú es `GAMESEL/GAMESEL.BIN` y los juegos
`SFNG/SF3_1ST.BIN` y `SFNG2/SF3_2ND.BIN` (programas aparte, como Power Drift): el gancho de 1ST_READ nunca se llama
(se queda en el aviso de VMU sin responder). Hace falta encontrar dónde se carga cada uno y parchearlos con
trampolines como YSGW.

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
la velocidad de crucero de MAME, "casi 2", sale con L a media, 0x80); B, X, Y, C y Z no hacen nada. Queda: volante =
izquierda/derecha, palanca = arriba/abajo, acelerador = vulcan, freno = misil, START + palanca adelante = acelerar, START
+ palanca atrás = frenar, START solo = START. Antes (mapa `plane`: acelerador A, freno B, L suelto) volaba siempre
"frenado" y el acelerador lanzaba misiles.
Dónde lee el mando: el menú copia el periférico Katana (`0x8c1f5060`) en `0x8c2e6f3c` (16 bytes por puerto, +2 botones
con los bytes cambiados) con `0x8c0fec80`; After Burner II es `BURNER/AB2.BIN` (código SH4, cargado en `0x8cb80000`,
más `PROG.BIN` 68000 del arcade) y recibe las funciones del menú por una tabla copiada en `0x8c400000`. (`0x8c2e71ac`,
la otra tabla de mandos, es la de OutRun/el menú.)
Space Harrier sigue con `plane` (acelerador A, freno B): **sin probar en placa**.

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
   - **✅ 30 FPS de serie (2026-11-11), hecho; falta probarlo en placa.** La tabla no está en `RALLY2.EXE` sino en
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
     el CSV no cambia). Pendiente: que el usuario la pruebe en placa.
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
