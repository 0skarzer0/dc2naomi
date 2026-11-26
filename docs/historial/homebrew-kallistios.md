# Historial: homebrew de KallistiOS (OutRun demos, OutRun C2C, Mario Kart 64, NesterDC)

> Historial: diario de sesiones copiado tal cual del antiguo `HANDOFF.md` (2026-11-25). Puede estar superado por lo escrito después; lo vigente está en [HANDOFF.md](../../HANDOFF.md).

> **Ojo con las IP:** en este diario la Pi del mueble Crazy Taxi aparece como **.60** (y la del mueble estándar a veces como **.59**). Desde el 2026-11-19 son **192.168.68.251** (Crazy Taxi) y **192.168.68.250** (estándar). El texto se deja como se escribió.

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
Dreamcast).

### Versión en español (`mk64es`, 2026-11-25)

Con el parche de **blade133bo** (v1.1, `Mario Kart 64 (ES).xdelta`, sobre la misma ROM US; MD5 de la ROM parcheada
`79743743904eea727cb82725be765ec6`, SHA1 `93c63590…`). Un comando:

```sh
ESPATCH="Mario Kart 64 (ES).xdelta" WORK=/root/mk64-es KOS_NAOMI_ENV=/opt/toolchains/dc/kos-naomi/environ.sh \
  homebrew/mk64/build_mk64.sh baserom.us.z64      # -> build/mk64es_dc2naomict.bin(.gz)
```

Lo que cambia el parche y cómo llega a la decompilación:
- **Gráficos** (texturas de menús y títulos, la paleta de las onomatopeyas `gTLUTOnomatopoeia`; ROM `0x132B50`–`0x145470`,
  `0x642xxx`–`0x6A04E3`, `0x7DBxxx`–`0x809449`): los extrae **Torch** de la ROM, así que basta con darle la española. Torch
  reconoce la ROM por su SHA1 en `config.yml`: `mk64_es.py` duplica el bloque US con la clave de la española.
- **Textos**: están en los datos del código del N64, que la decompilación **recompila desde C**, no los saca de la ROM.
  En la ROM, cadenas terminadas en 0 en `0xF0300`–`0xF1900` (308: copas, circuitos, menús, Controller Pak, resultados)
  y `0x12A100`–`0x12A700` (62: créditos); las de las dos ROMs emparejan una a una. En el fuente están en
  `src/menu_items.c`, `src/ending/credits.c` y, los nombres de circuito, en `yamls/courses/*_metadata.yml`
  (`name`, `debug_name`). `mk64_es.py` alinea los literales del C con las cadenas US en orden (difflib), así que una
  frase inglesa repetida con dos traducciones ("N64 CONTROLLER PAK", "    th" → ro/do/to/mo/vo) recibe cada una la
  suya. Resultado: 189 literales y 40 nombres de circuito.
- **Textos del port** (los mensajes de la VMU que sustituyen a los del Controller Pak, `D_800E7940`, `D_800E7980`): no
  están en ninguna ROM; traducción nuestra en `PORT_ES` (`mk64_es.py`).
- Los trucos de fuente del traductor ("yu2uru", "kei2o", "disezo" = diseño) se copian tal cual: la fuente también sale
  de su ROM. Errata suya que se queda: "A SIDO GUARDADO".

- `extract_assets.py` (los gráficos que no pasan por Torch) también comprueba el SHA1 de `baserom.us.z64`, contra
  `mk64.us.sha1`: `mk64_es.py` escribe ahí el de la española.

El script no guarda ningún texto traducido: lee las dos ROMs del usuario. Restaura con git los archivos que toca, así
que se puede repetir.

**Estado (2026-11-26):** compilada desde main `851fb98`, con el ritmo de imagen final y los mandos nuevos de `mk64`. En
Flycast (`naomi.zip`): menús, copas, circuitos y marcador de carrera ("VUELTA", "TIEMPO", "8vo") en español; acelerador
= A, freno = B, START + freno = L (leído en `gControllers`, que en esta compilación está en `0x8c95880c`). Subida a la
.251 como ROM aparte (`dc-mk64es_dc2naomict.bin.gz`, fila "Mario Kart 64 (Dreamcast, espanol)") y cargada en el mueble:
**funciona en placa** (el usuario, 2026-11-26: "funciona perfecto"). Si `cmake` de Torch falla al bajar sus
dependencias (DNS de WSL), basta con repetir: copiar `cmake-build-release` de otro WORK no sirve (su caché guarda la
ruta). Lo aprendido para el siguiente port: [../guia-ports-kallistios.md](../guia-ports-kallistios.md).

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

## NesterDC (emulador de NES, `homebrew/nesterdc/`) — perfil `nesterdc`. ⚠️ SIN PROBAR EN PLACA (2026-11-20)

**Qué es.** [NesterDC](https://github.com/pqrs-org/NesterDC) (pqrs-org / tekezo; núcleo Nester GPL2, código de
Dreamcast BSD) es un emulador de NES para Dreamcast hecho con KallistiOS 1.1.8 y gcc 3.2. Lo hemos llevado a la
KallistiOS actual (`680d1862` + el parche `NAOMI_HOST` de `homebrew/mk64/`) **solo el núcleo** (CPU, PPU, APU, mappers:
136 ficheros compilan con sh-elf-gcc 15). El frontend original (menús, AICA con firmware propio ARM, VMU, mandos de
KOS 1.1.8) **no se usa**: `ndc_main.cpp` es uno nuevo y mínimo (vídeo PVR 640x480 estirado, audio `snd_stream`
mono 44,1 kHz con el mismo protocolo de dos mitades del núcleo, mandos maple).

```sh
homebrew/nesterdc/build_nesterdc.sh CARPETA_O_JUEGO.nes   # -> build/nesterdc_dc2naomict.bin(.gz)
```

Las ROMs van en el disco (`/cd/ROMS/`), con un menú al arrancar (palanca = cursor, acelerador o START = jugar); en juego, **START + volante a la derecha (medio segundo) vuelve al menú**. Perfil de mandos nuevo `nes` (`DIMM_PAD_NES` = 10 en `resident/resident.c`, esquema del usuario, 2026-11-20): START = START mientras se mantiene (no si se usa de cambio), volante a tope = izquierda/derecha (y stick analógico), acelerador = A, freno = B, palanca = arriba/abajo; con START apretado: acelerador = X, freno = Y, palanca adelante = L, atrás = R. En NES: A, B, START, SELECT = X o Y, cruceta = volante y palanca.
No hay nada con copyright en el repositorio. `nester-kos-modern.patch` es el cambio a los fuentes de NesterDC
(tipos `uint8…` sin `kos.h`, `htonl` propio, `*((T*)p)++` ilegal en gcc moderno, un `class NES_mapper;`).

**Estado (2026-11-20):** primera imagen de prueba (ROM mínima) **arrancó en la placa: pantalla roja** (el usuario lo confirmó). La imagen con menú y varias ROMs de prueba se acaba de generar y no se ha probado aún. Antes de eso: no hay BIOS de
NAOMI 2 en la sesión de la IA para Flycast y la Raspberry/.251 no es alcanzable desde la nube (IP privada). Probado solo
con una ROM de prueba mínima hecha a mano (fondo de un color, no es un juego).

**Imagen completa (2026-11-20):** 142 ROMs del usuario en una imagen de 23,9 MB (11 MB comprimida). **Lección:** la primera versión enlazaba las ROMs dentro de `1ST_READ.BIN` (23,8 MB): en la placa se quedó en «starting...» (el residente lee `1ST_READ.BIN` entero por PIO antes de arrancar, y además dejaba solo ~4,9 MB de montículo). Ahora las ROMs van **como ficheros del disco** (`/cd/ROMS/NNN.NES`, nombres en `/cd/ROMS.TXT`) y el programa mide 636 KB; la ROM se lee al elegirla (`/cd/ROMS/NNN.NES` se pasa directamente a `NES::initialize`). Nombres del menú sin paréntesis ni corchetes; volante izquierda/derecha = página de 8. **Pendiente / dudas:** que arranque; el audio (la posición de reproducción se saca de lo consumido por el callback, que
va adelantado respecto a lo que suena); mandos (volante = joyx ±48, A→A, X/B→B, Y/Z→SELECT, START); VMU y partidas
guardadas (no están); menú de selección de ROM (no hay); FDS (necesita `disksys.rom`). No sirve para el volante: la NES
tiene pocos juegos de conducción.

### NesterDC — correcciones tras la primera prueba en placa (2026-11-20)
Probado en la placa: arranca, menú responde. Arreglado en la iteración siguiente (pendiente de probar):
- **Menú ilegible**: `bfont` no sirve sobre la textura RGB565 de 512x256; ahora se dibuja con `font8x16.h` (copia de `resident/font8x16.h`, DejaVu Sans Mono), 64 columnas x 16 filas.
- **Sin sonido**: el callback de `snd_stream` recibe y devuelve **bytes** (se estaban duplicando); ahora un FIFO alimentado con las mitades de 4 KB del APU.
- **Volver al menú**: el resident (`DIMM_PAD_NES`) enviaba `0x0800` con START + volante derecha; ahora envía START+RIGHT mantenidos y el programa los detecta 300 ms (`timer_ms_gettime64`). START solo se envía al soltarlo si no se usó ningún otro control.
- **Carpetas**: `build_nesterdc.sh` genera `ROMS.TXT` con líneas `d|f<TAB>id<TAB>padre<TAB>nombre` y los ROMs como `/cd/ROMS/<id>.NES`; el menú navega carpetas (`[carpeta]`, `..`).
- Zona muerta del volante en el perfil `nes` reducida al mínimo: izquierda x<116, derecha x>140 (centro 128; antes 16/239, luego 124/132 que el rebote del volante activaba solo).

### NesterDC SE recompilado (2026-11-26) — `homebrew/nesterse/`, perfil `nesterse`
La imagen de abajo (binario original) daba **pantalla negra en la placa** (el usuario). Ahora se compila desde los
fuentes de SE 1.0 (2005-12-24, en el fork [0skarzer0/NesterDC](https://github.com/0skarzer0/NesterDC), `NesterDCSE/`)
contra KallistiOS 680d1862 + `NAOMI_HOST`: `build_nesterse.sh CARPETA_v1.1 CARPETA_ROMS [SALIDA.bin]`. El disco lleva
los menús .js, fuentes y gráficos de la v1.1 (Christuserloeser: su `1ST_READ.BIN` es del 2005-12-09, igual que la
1.0; solo cambian los .js) con nuestro `1ST_READ.BIN` sin cifrar, y las ROMs en `NES/` (carpetas conservadas,
nombres sin paréntesis, ≤46 + `.nes`). Perfil `nesterse` con VMU emulada (`0x9404`; `nesterse_dbg` = `0x9C0C`).
Qué hubo que cambiar (`nesterse-kos-modern.patch`, `nse_compat.h`, `nse_timer.c`):
- kjs (motor JS de los menús) con g++ 15: `port_kjs.h` redefinía `uint32_t`, `dtoa.cpp` (`strtod`), `ustring.cpp`
  (`KJS::operator` dentro del namespace); `vmu_pkg_t.data` ahora es `const` y `vmu_pkg_parse` pide el tamaño.
- 6502 en C (`nes6502.c`): casts como lvalue (`((uint8)REG_S)--`), que gcc ya no admite.
- **TMU2**: SE lo usaba como reloj de 50/60 Hz y en la KOS actual es el reloj de `timer_ms_*` (TMU1 es de
  `timer_spin_sleep`): ahora va con `vblank_handler_add` (`nse_timer.c`; 60 Hz en la NAOMI, 50 salta uno de cada 6).
- `spu_dma_init/shutdown` ya no existen (no hacen falta); `ptr_t` → `void *`; `pvr_internal.h` por su ruta en KOS.
- **Cuelgue en el splash**: libjpeg 9 (kos-ports) tiene `scale_num` = 8 por defecto (1 en la 6b): con solo
  `scale_denom = 1` cada JPEG salía a 1280×960, 300 trozos para `Image.polys[256]` (en la pila) y se colgaba.
- **Pánico en el primer PNG**: libimageload de kos-ports llama a `readpng_*` de libpng con su firma antigua
  (`png_error` salta a basura). Los PNG se leen en `image.c` con el `readpng_*` actual (nombres por `__asm__`) y
  se pasan a RGB565/ARGB1555/ARGB4444; color clave a 5 bits por canal (el arte trae 252,2,252) o tRNS.
- kos-ports: zlib.net ya no sirve 1.3.2; el script la baja de las releases de madler/zlib (mismo SHA-256).
- El firmware del AICA es el `sound/aica_fw.h` precompilado de SE: no hace falta toolchain ARM. Arranca (el
  handshake con el ARM pasa) pero **el sonido no se ha oído**: Flycast va sin audio en esta máquina.
Depuración: con `nesterse_dbg` se ve el log de KOS; con el programa colgado, `naomi_live` (volcado de RAM de
Flycast + `nm` del ELF) dio el PC del hilo principal y el log aunque no se viera.
En Flycast (BIOS NAOMI): título con la rueda, menú principal, explorador de `/NES`, juego (Bomb Sweeper) jugable.
En placa (2026-11-26, .251): arranca y suena bien. No se podía volver al explorador: SE sale del juego con START +
stick a la izquierda (`poll_input` en `main.cpp`; con la cruceta en modo analógico, START + cruceta izquierda; no
hay menú emergente), pero el perfil `nes` del residente sólo manda START mantenido junto con el volante a tope a la
derecha (el combo de nuestro NesterDC 7.1); START + izquierda no se cambió en el residente porque en 7.1 llegaría al
juego como START de NES. El parche añade START + cruceta derecha a las dos condiciones de SE: **START + volante a la
derecha vuelve al explorador**, como en 7.1 (aquí al instante, sin los 300 ms).

### NesterDC SE v1.1 (2026-11-20) — perfil `nesterse` (binario original, NO arranca en placa)
El usuario aportó NesterDC SE v1.1 (Christuserloeser, 2008-12-09; build modificada de NesterDC SE, binario + scripts .js; **no está en el repo**). Imagen sin recompilar: `1ST_READ.BIN` + `IP.BIN` del paquete tal cual, carpeta `NES/` con las ROMs del usuario (nombres ≤46+3 caracteres, sin paréntesis; estructura de carpetas conservada) y `REBUILD=1 ./build.sh nesterse DISCO SALIDA.bin`. Mismo perfil de mandos `nes` (START+acelerador = X = subir de carpeta; B = volver al menú principal). `1ST_READ.BIN` viene **scrambled**: se desbloquea con `scramble -d` (KOS utils) antes de meterlo en el disco. Imagen generada 2026-11-20 (143 ROMs, 28,4 MB; `h-nesterse_naomi.bin.gz`). ⚠️ Sin probar en placa: es un binario KOS 1.1.8 sin parche NAOMI_HOST, puede no arrancar.

**Confirmado por el usuario (2026-11-25):** la última imagen de Mario Kart 64 (palanca adelante = salto, free play / attract mudo) sí llegó a subirse a la Pi del Crazy Taxi.
