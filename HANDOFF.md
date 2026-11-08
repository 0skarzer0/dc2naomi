# HANDOFF — dc2naomi (juegos de Dreamcast en NAOMI)

Documento de traspaso entre sesiones (personas o IAs). **Actualízalo en cada sesión.**

## Objetivo

Arrancar juegos de **Dreamcast** en una **NAOMI / NAOMI 2** por netboot (NetDIMM), sustituyendo la BIOS de
Dreamcast por un programa residente. Si funciona, sirve para recopilatorios (Yu Suzuki Game Works, Namco
Museum, Midway…) y ports (Wipeout, Mario Kart 64).

## Estado (2026-11-08)

| Juego | Flycast | Placa real |
|---|---|---|
| Daytona USA 2001 (US) | — | ❌ Negro (probablemente el UBC, ver abajo). Parado |
| Yu Suzuki Game Works Vol. 1 (JP) | ✅ Menú y Power Drift jugable | ❌ Negro tras la licencia de SEGA |
| Namco Museum (US) | ✅ Menú y Pac-Man | ❌ Congelado tras STREAM.MLT (sonido) |
| Crazy Taxi 2 (US) | ✅ Hasta tarjetas de memoria | sin probar |
| Crazy Taxi 2 (US), Daytona 2001, Re-Volt | ✅ hasta tarjetas de memoria / VMU | ❌ logo de SEGA → negro (lote del 2026-11-08) |
| **Virtua Tennis (US)** | ✅ | ✅ **Primer juego de Dreamcast que arranca en la placa real** (2026-11-08): llega a "No VMU found in slot 1, port A" |
| Ikaruga (JP) | ✅ Título | ❌ Logo de SEGA → negro: atascado en la DMA G2 del AICA. Con `g2cpu` avanza 5 subidas más y se para en la 6.ª |
| Virtua Athlete 2000 (US) | ✅ Título y demo | ❌ Logo de SEGA → negro (monitor trifrecuencia: no pierde señal). **Mismo código de DMA G2 que su versión NAOMI, que sí funciona** |

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
