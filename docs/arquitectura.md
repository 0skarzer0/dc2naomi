# Arquitectura de dc2naomi (referencia)

> Referencia técnica sacada del antiguo `HANDOFF.md` (2026-11-25). Partes escritas el 2026-11-09 y no puestas al día: el gancho por UBC ya no se usa en placa (todos los perfiles van con `NO_UBC` 0x0004 y trampolines); la lista de `flags` está incompleta (la completa, en `resident/resident.h`); la DMA G2 del AICA no era la causa general de los cuelgues (era `PCTRA`: ver [historial/placa-inicial.md](historial/placa-inicial.md)); `app/dc2naomi.py` también lee `.cdi`.

> **Ojo con las IP:** en este diario la Pi del mueble Crazy Taxi aparece como **.60** (y la del mueble estándar a veces como **.59**). Desde el 2026-11-19 son **192.168.68.251** (Crazy Taxi) y **192.168.68.250** (estándar). El texto se deja como se escribió.

## Objetivo

Arrancar juegos de **Dreamcast** en una **NAOMI / NAOMI 2** por netboot (NetDIMM), sustituyendo la BIOS de
Dreamcast por un programa residente. Si funciona, sirve para recopilatorios (Yu Suzuki Game Works, Namco
Museum, Midway…) y ports (Wipeout, Mario Kart 64).

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

## Notas de hardware (aprendidas en otros ports)

- La VRAM real de NAOMI **no admite escrituras de byte** (Flycast sí): usar escrituras de 16/32 bits.
- La DMA del PVR se cuelga en NAOMI.
- **La DMA G2 del canal AICA que lanza un juego de Dreamcast no termina nunca en la NAOMI** (ADST se queda a 1,
  no hay interrupción de fin). Copiar por CPU y simular el fin (`g2cpu`).
- **El UBC (excepción DBR) cuelga la placa**; TMU2 por el despachador del juego sí funciona.
- Algunos juegos leen el tipo de cable del registro del AICA `0xa0702c00` (bits 9:8), no solo de PDTRA.
- En Flycast sin BIOS el driver MIE de KOS no se activa (ver parche en `mame4all-naomi/naomi/flycast`).

**⚠️ Formato de la cabecera (2026-11-09):** las imágenes hechas antes de subir `DIMM_RANGES`/`DIMM_TRACKS` a 32/64
(`ct2h4`, `ysgw5`, `nmus6`, `ikaruga_joy` y anteriores) usan 4/8. **No se les puede cambiar solo el loader**: el
residente nuevo leería la tabla de parches en otro sitio y no aplicaría ninguno. Así salieron `ct2h5` y la primera
`ct2h6` (malas en placa; en Flycast arrancan igual porque Flycast no necesita los parches para llegar al menú).
`tools/convhdr.py VIEJA.bin.gz NUEVA.bin.gz TITULO [PADMAP]` reescribe la cabecera al formato actual con el
`app/loader.bin` de ahora; la `ct2h6` buena está hecha así (comprobado: parches en su sitio, `pad_map` 0).
