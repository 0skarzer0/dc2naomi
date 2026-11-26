# Guía: portar a la NAOMI un homebrew de KallistiOS (ports de decompilaciones de N64)

Lo aprendido con **Mario Kart 64** (mk64-dc de jnmartin84; `mk64` y su versión en español `mk64es`, las dos
funcionando en el mueble Crazy Taxi), para el siguiente juego del mismo tipo (Diddy Kong Racing, otro port de
decompilación de N64, otro homebrew de KallistiOS). Es una lista de pasos y trampas; el detalle está en:

- [historial/homebrew-kallistios.md](historial/homebrew-kallistios.md): Mario Kart 64 (compilación, los 8 arreglos de
  KallistiOS, depuración en placa, versión en español).
- [juegos/mario-kart-64.md](juegos/mario-kart-64.md): fluidez (cómo medir, causas y cambios) y mandos.
- `homebrew/mk64/build_mk64.sh`: el script que hace todo de un comando, la plantilla para el siguiente.

## 1. Antes de empezar

- **Compilar nosotros, no parchear binarios.** Los `.cdi`/`.iso` que circulan no sirven: relleno que no cabe en la
  NetDIMM, hechos para DreamShell y, sobre todo, sin los arreglos de KallistiOS para la NAOMI.
- **Nada con copyright en el repo:** ni la ROM, ni el código del port si no tiene licencia publicada (el script lo
  clona del autor en un commit fijo), ni nada sacado de la ROM, ni textos de traducciones ajenas. Todo eso vive en
  `$WORK` o en la carpeta del usuario. Comprobar la ROM por su MD5 al principio del script.
- **Dos árboles de KallistiOS distintos:**
  - el del juego: la versión que pida el port (mk64-dc: `680d1862`), en `$WORK`, con
    `homebrew/mk64/kos-680d1862-naomi_host.patch` y `-DNAOMI_HOST` en `KOS_CFLAGS`. Para otra versión de KOS, todos
    los cambios están bajo `#ifdef NAOMI_HOST` y se pueden pasar a mano;
  - el del loader de dc2naomi: `KOS_SUBARCH=naomi` (`KOS_NAOMI_ENV`). Hoy es KOS master `9926b70a`: `680d1862` no
    tiene `dcache_wback_range` ni `icache_sync_range`.
- **Toolchain:** sh-elf-gcc 15 en `/opt/toolchains/dc/sh-elf`, compilando en WSL (Ubuntu 22.04). Con dc-chain:
  `toolchain_profile=15.1.1-dev` en `Makefile.cfg`, y primero `make -j1 fetch-sh-gcc fetch-newlib` (con `-j16` la
  descarga de gcc por git choca consigo misma, `tmp_pack`).
- **WSL, trampas que costaron tiempo:**
  - `wsl.exe` expande `$var` por su cuenta: lo que lleve variables va en un `.sh` (pasado por `tr -d '\r'`);
  - desde el Bash de Git, `MSYS_NO_PATHCONV=1 wsl.exe ...`, o reescribe las rutas `/root/...`;
  - la copia de Windows tiene saltos CRLF (`core.autocrlf`): compilar desde un clon en Linux;
  - `pkill -f X` / `pgrep -f X` se encuentran a sí mismos si su orden contiene X (truco `[x]`);
  - los trabajos largos van en una tarea de fondo que mantenga `wsl.exe` vivo (con `setsid nohup` sueltos, a veces
    murieron al cerrarse WSL);
  - el DNS de WSL falla a ratos: si `cmake` no puede bajar una dependencia, repetir. Copiar el `cmake-build-release`
    de otro `$WORK` no sirve (su caché guarda la ruta).

## 2. Compilar y empaquetar

- El script hace, en orden:
  1. el KOS del juego con el parche;
  2. los kos-ports que necesite el juego (mk64: solo `sh4zam`);
  3. las herramientas de la decompilación (Torch, de HarbourMasters, compilado con `cmake -GNinja`);
  4. los assets desde la ROM y luego el juego;
  5. los archivos del disco en una carpeta;
  6. `./build.sh PERFIL CARPETA SALIDA` con `REBUILD=1`, y el `.bin.gz`.
- **Layout `rebuild`:**
  - `IP.BIN` de `makeip`;
  - `1ST_READ.BIN` = el binario del juego **sin cifrar** (la ruta GD-ROM no cifra);
  - el resto de archivos tal cual. Nombres en minúsculas → `rock_ridge: True` en el perfil.
- **Perfil en `tools/games.py`:**
  - `flags 0x1404`: sin user break, lecturas GD por DMA de una vez (`DIMM_SYNCREAD`), sin el arranque del IP.BIN de SEGA;
  - `+0x8000` si se quiere la VMU emulada;
  - `hook_pc: []`, `groups: []`: no hay nada que parchear en el binario.
  - Hacer además un perfil `_dbg` con `CONSOLE | DIAG`, que saca el `printf` del juego en pantalla.
- **`make -j` y assets:** los `.mk` de la decompilación pueden colgar texturas de objetos que no son los que las
  incluyen. Compilar primero los objetos que nombran esos `.mk` y luego todo (`build_mk64.sh`, paso 4).
- Imprimir al final las direcciones de `naomi_live` (y de `naomi_med` si hay medidas), sacadas con `sh-elf-nm`.
- **Si el script aplica parches al juego o a KOS, debe saber poner al día un `$WORK` viejo**: comprobar con
  `git apply -R --check` y, si no está, restaurar y volver a aplicar.

## 3. Lo que KallistiOS hace mal en la NAOMI 2 (ya resuelto en el parche)

El port se compila como para Dreamcast, así que KOS hace lo que haría en una Dreamcast. Los 8 arreglos, con su
síntoma en placa (tabla completa en el historial):

| Síntoma | Causa | Arreglo |
|---|---|---|
| Pantalla negra con ruido | `vid_check_cable()` escribe PCTRA: mata el TA | devolver VGA sin escribir nada |
| La pila y el montículo pisan el residente | la NAOMI 2 no hace espejo de `0xadffffff`: KOS cree 32 MB y pone la cima en `0x8e000000` | `arch_stack_32m` = `0x8dc00000` |
| Sin mandos ni VMU | `maple_dma_addr()` no pasa por el gancho maple del residente | leer el gancho de la tabla `DCLR` en `0x8dc00000` |
| Bloqueo del bus G1 con multibios | `cdrom_init()` lee la BIOS entera para desbloquear G1 | no hacerlo |
| Placa congelada | `g2_fifo_wait()` y `g2_lock()` esperan sin límite al FIFO G2 | límite de vueltas como el residente |
| Imagen quieta tras el logo | `spu_memload()` sube el audio por DMA G2, que aquí no acaba | subirlo por store queues |
| Logo en bucle, reinicios | SR guardado en una línea de caché que se tira; `arch_exec` salta en modo usuario | guardar SR por P2; `arch_exec` siempre con MD |

Lección general: lo que ya se había medido en placa con juegos comerciales (G2, DMA del AICA) le pasa igual a KOS.
Un homebrew que dibuje en 3D y use el AICA lo destapa; DreamShell no.

## 4. Depurar en placa

- **Los peeks del residente no sirven** con KallistiOS (el residente solo atiende la NetDIMM dentro de sus llamadas).
  El parche mete en el juego un contestador propio (`naomi_peek_poll`, mismo protocolo y ventana). Así funciona
  `tools/board/pk.py`.
- **`naomi_live`:** vblanks, PCs muestreados (un perfilador), las últimas 8 KB de lo que imprime KOS y, ante una
  excepción, todos los registros. Lector: `pi/live.py IP ADDR` de naomi-pi-tools, sin `timehack.py` corriendo a la vez.
- `arch_abort/exit/reboot` se quedan atendiendo peeks en vez de reiniciar: el fallo se puede leer.

## 5. Fluidez (fps)

Medir antes de cambiar, en placa, siempre con la **demo automática**, que repite la misma secuencia y permite comparar.
El juego rellena un bloque `naomi_med` y `med_mk64.py`/`resumen_mk64.py` lo leen desde la Pi. La cifra que importa
es cuántos vblanks dura cada imagen en pantalla. Las tres causas de Mario Kart 64 (3,8 % → 0 %) las tendrá
probablemente cualquier port de KOS a 30 fps:

1. marcar el ritmo (esperar al vblank) **antes** de `pvr_scene_finish`, no después;
2. `thd_schedule(1, 0)` en el vblank, para que el juego despierte a tiempo;
3. `pvr_naomi_hold_flip(n)` (parche de KOS) para que la imagen salga siempre n vblanks después de mandarla.

Por qué: KallistiOS cambia la imagen **en el primer vblank después de que la GPU acaba**. Entre `pvr_scene_finish` y
la imagen nueva van el registro (la geometría entra en la GPU, 7-15 ms) y el render (7-18 ms); juntos rondaban los
16,7 ms y la imagen salía a 1 o 2 vblanks según el cuadro, aunque el juego hiciera 30 fps justos. Y KallistiOS no
cambia de hilo cuando una interrupción despierta a alguien: el juego esperaba al siguiente tic (0-3 ms).
`pvr_naomi_hold_flip` cuesta hasta un vblank más de retraso del mando en escenas ligeras (en Mario Kart no se nota)
y vale mientras registro + render quepan en n vblanks.

Cómo se encontró, por si el siguiente juego tiene otra causa:
- **Las medias no bastan.** Con CPU, render y despertar todos dentro de presupuesto seguía habiendo un 2-3 % de
  tirones. Lo resolvió una **traza**: al ver en carrera una imagen fuera de ritmo, el juego guarda los 16 últimos
  cuadros (inicio, fin de CPU, envío a la GPU) y los 16 últimos cambios de imagen con los tiempos de registro y render
  (`naomi_traza`, lector `homebrew/mk64/traza_mk64.py`). Esos tiempos están en `pvr_state`: desde el juego,
  `#include <../hardware/pvr/pvr_internal.h>`.
- Los cambios de imagen se cuentan en un manejador de vblank con `pvr_get_stats()` (`frame_count`).
- **Las lecturas de la Pi cortan las interrupciones del juego** (el contestador de peeks). Comprobar que no falsean
  la medida: `med_mk64.py ... SEGUNDOS SALIDA.csv 10` lee solo una ventana cada 10 s (lo medimos: no eran la causa).
- Lo que **no** era: el audio (menos de 1 ms por vblank), las subidas de texturas, la CPU (sobraba la mitad).
- Flycast sirve para ver que un cambio no rompe nada y efectos grandes (el histograma pasó de 3/24/3 a 0/30/0), no
  para medir.

Los cambios del juego van en un parche aparte (`mk64-dc-naomi.patch`), todo bajo `NAOMI_HOST`.

## 6. Mandos

- Leer cómo traduce el port el mando de Dreamcast (mk64: `update_controller` en `src/main.c`) **y sus opciones de
  compilación**: con `BUTTON_SWAP_X=1` la X de Dreamcast era C-derecha, y el freno mandado como X nunca fue el B del N64.
- El mapa del mueble va en el residente (`DIMM_PAD_MK64`, `pads: "mk64"`). Si falta un botón del N64, el parche del
  juego puede reasignar uno de Dreamcast que nadie use (mk64: C → L) y el residente lo manda con una combinación.
- Comprobar en Flycast leyendo el estado del mando del juego en RAM (`gControllers`, dirección con `sh-elf-nm`: cambia
  con cada compilación) con `FC_PEDALS=1` (`FC_PEDALS_BRK=1` = la tecla k frena) y `DUMP=1` de `run1.sh`. Todo junto:
  `tools/flycast/fcpad.sh IMAGEN DIR_gControllers NOMBRE KEYS` (p. ej. `'30:k:45,60:Return:12'` = acelerador desde el
  segundo 30 y START desde el 60, aún pulsados al volcar la RAM) imprime el stick y los botones de N64 que recibe el
  juego. Los dos parches locales de Flycast están en `tools/flycast/flycast-dc2naomi-debug.patch`.
- Combinaciones con START: el residente manda START **al soltarlo** y solo si no se usó para otra cosa
  (`start_used = 1` en cada combinación). El stick va en `joyy`: 255 = abajo.
- Varios perfiles pueden compartir `pads` (Diddy Kong Racing usa `mk64`): cambiar uno cambia los demás.

## 7. Traducciones (parche xdelta sobre la ROM)

Receta de `mk64es` (`ESPATCH=… build_mk64.sh` + `homebrew/mk64/mk64_es.py`), válida para cualquier decompilación:

- **Gráficos:** salen de la ROM con las herramientas de assets, así que basta con darles la ROM traducida. Pero **todo
  lo que comprueba el hash de la ROM** debe aceptar el de la traducida. En mk64 son dos sitios: `config.yml` de Torch
  (bloque duplicado bajo el SHA1 nuevo) y `mk64.us.sha1` de `extract_assets.py`.
- **Textos:** una decompilación los **recompila desde C**; no los saca de la ROM. Hay que:
  1. buscar en las dos ROMs los bloques de cadenas terminadas en 0 que cambian, y emparejarlos uno a uno (mismo número);
  2. alinear los literales del C con las cadenas originales **en orden** (difflib), para que una frase repetida con
     dos traducciones reciba la suya;
  3. reemplazarlos con escapes de C. También van los nombres en yamls u otros datos de la decompilación.
- **Textos que añade el port** (mk64: los mensajes de la VMU en lugar del Controller Pak): no están en ninguna ROM;
  traducción nuestra, por array, en el script.
- **El script no guarda texto traducido** (lee las dos ROMs del usuario) y restaura con git lo que toca, así que se
  puede repetir. Comprobar que no restaura archivos que toca otro parche del build.
- La fuente del juego también sale de la ROM traducida: los trucos del traductor ("disezo" = diseño) se copian tal cual.
- Perfil propio (`mk64es`) y ROM aparte en la Pi, sin tocar la principal.

## 8. Probar y subir

1. **Flycast:**
   - BIOS NAOMI 1 (`naomi.zip` en `$FCTEST/home/.local/share/flycast/`: `run1.sh` pone `HOME=$FCTEST/home`; la de
     NAOMI 2 no arranca imágenes de netboot);
   - `run1.sh IMAGEN SEGUNDOS NOMBRE` con `FC_SYSM_RAM=1 FC_PEDALS=1`;
   - `KEYS` para pasar menús (Return = START, k = acelerar, j/l = volante); las capturas salen en una rejilla.
2. **Pi:**
   - `tools/board/piput.py` (desde Git Bash, `MSYS_NO_PATHCONV=1`, o convierte la ruta remota en una de Windows);
   - comprobar el MD5;
   - fila en `romsinfo.csv` (receta 12 del HANDOFF; copia `.bak` antes);
   - cargar con `setsid nohup python3 /sbin/piforce/dc2naomi_send.py 10.0.0.4 /boot/roms/… &`, o como la web:
     `load.php?rom=…&name=…&dimm=10.0.0.4&mapping=…&ffb=…` con `User-Agent: Chrome` (`loadcheck.php` solo redirige:
     `curl` sin `-L` no carga nada); progreso en `/var/log/progress_10.0.0.4` hasta `COMPLETE`;
   - la carga arranca `timehack.py`: pararlo antes de leer memoria (`pkill -f "[t]imehack.py"`); vuelve con la
     siguiente carga;
   - las pruebas, con otro nombre de ROM (`dc-JUEGOmed…`) para no pisar la del usuario; al cambiar la principal,
     copia de la anterior en `/boot/roms/_test/`; y borrar las de prueba al acabar.
3. **"Probado" = el usuario lo confirma en el mueble.** Hasta entonces, en HANDOFF y en el historial, "sin probar en
   placa".

## 9. Varias sesiones en la misma copia

- Subir solo lo propio. Con cambios ajenos sin subir en el mismo archivo, no usar `git add`: preparar el índice con
  el archivo de `HEAD` más los cambios propios (`git hash-object -w --stdin` + `git update-index --cacheinfo`).
  `git apply --cached --unidiff-zero` coloca mal los trozos cuando el archivo tiene líneas ajenas.
- Mirar `git log` antes de crear un documento: otra sesión puede estar escribiendo el mismo (esta guía la empezaron
  dos a la vez).
- Avisar a las otras sesiones cuando un cambio les afecta (un parche compartido, un perfil de mandos compartido).
