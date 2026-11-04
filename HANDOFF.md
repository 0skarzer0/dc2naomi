# HANDOFF — dc2naomi (juegos de Dreamcast en NAOMI)

Documento de traspaso entre sesiones (personas o IAs). **Actualízalo en cada sesión.**

## Objetivo

Arrancar juegos de **Dreamcast** en una **NAOMI / NAOMI 2** por netboot (NetDIMM), sustituyendo la BIOS de
Dreamcast por un programa residente. Si funciona, sirve para recopilatorios (Yu Suzuki Game Works, Namco
Museum, Midway…) y ports (Wipeout, Mario Kart 64).

## Estado (2026-11-04)

| Juego | Estado |
|---|---|
| Daytona USA 2001 (US) | ❌ Pantalla negra en placa real (sesión anterior). Parado. |
| **Yu Suzuki Game Works Vol. 1 (Japón)** | 🧪 Imagen completa (`build/ysgw.bin`, 201 MB) con el loader compilado; **sin probar** (ni Flycast ni placa) |

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

## Pruebas en Flycast (2026-11-05)

- **Placa real: pantalla negra** con `ysgw_dc2naomi.bin.gz`.
- En Flycast **modo Dreamcast** (BIOS HLE `UseReios`) el CHD de YSGW arranca y llega al título: el disco y el
  flujo menú/monitor funcionan con una BIOS que hace lo mismo que el residente.
- Flycast `7adbf3c` + `tools/flycast/flycast-naomi2-bin.patch` (`FC_NAOMI2=1`: los `.bin` sueltos como NAOMI 2
  con `naomi2.zip`, BIOS `epr-23608b`). **No sirve todavía**: la BIOS de NAOMI 2 corre (sus tareas cambian) pero
  en 3 minutos no dibuja nada ni carga el programa, **ni siquiera el loader solo**. Es un problema de esa
  combinación en Flycast, no del cargador. Hace falta la BIOS de NAOMI 1 (`naomi.zip`), como en las pruebas de
  MAME4ALL.
- Ojo: `FC_MIE_NODEVINFO` (parche de `mame4all-naomi`) hace que la BIOS de NAOMI se quede esperando al MIE
  (bucle en `0x0c033904`); no definir la variable (ni vacía) salvo para probar el driver MIE de KOS sin BIOS.
- `tools/flycast/run1.sh IMG SEG NOMBRE` (capturas cada `STEP` s en una cuadrícula) y `pcwatch.sh IMG SEG PASO`
  (PC/PR con gdb sobre una compilación RelWithDebInfo y volcado de RAM con `DUMP=1`; el log del residente está en
  `0x0dd80000`, magic del residente en `0x0dc00000`).

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
- En Flycast sin BIOS el driver MIE de KOS no se activa (ver parche en `mame4all-naomi/naomi/flycast`).

## Siguientes pasos

1. Probar `build/ysgw.bin` en placa (WiPi Netbooter).
2. Probar en Flycast (necesita `naomi.zip` en `home/.local/share/flycast/` del entorno de prueba) (NAOMI, con el parche MIE) antes que en placa: ¿llega al menú? Mirar el log del
   residente en `0x8dd80000` (entradas "PROG"/"PATC" del gancho, "RQ" de GD-ROM).
3. Si hay pantalla negra: `SAMPLER=1` y foto de la pantalla (filas de bits: llamadas GD, última llamada,
   sondeos de maple, último sector, otras syscalls y los últimos PC).
4. Controles en el menú de YSGW: confirmar que START corto = A y que el volante mueve el cursor.
5. Si YSGW funciona, volver a Daytona 2001 con la imagen por rangos (`layout: gdi`) y el gancho.
