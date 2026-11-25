# Historial: CD-DA en NAOMI y RoboCop (2026-11-19)

> Historial: diario de sesiones copiado tal cual del antiguo `HANDOFF.md` (2026-11-25). Puede estar superado por lo escrito después; lo vigente está en [HANDOFF.md](../../HANDOFF.md).

> **Ojo con las IP:** en este diario la Pi del mueble Crazy Taxi aparece como **.60** (y la del mueble estándar a veces como **.59**). Desde el 2026-11-19 son **192.168.68.251** (Crazy Taxi) y **192.168.68.250** (estándar). El texto se deja como se escribió.

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
