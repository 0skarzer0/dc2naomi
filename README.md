# dc2naomi — juegos de Dreamcast en Sega NAOMI

Convierte un juego de **Dreamcast** (tu propio volcado en `.chd` o `.gdi`) en una imagen para arrancarlo en una
placa **Sega NAOMI / NAOMI 2** por **netboot (NetDIMM)**, sin modificar el hardware.

La NAOMI es casi una Dreamcast (mismo SH-4, PowerVR2 y AICA, pero con más memoria). Lo que le falta para ejecutar
un juego de Dreamcast es la **BIOS de Dreamcast** y el **lector GD-ROM**. Este proyecto los sustituye por software
y traduce los controles de la recreativa (JVS) a un mando de Dreamcast.

## El programa (Windows)

Hay dos ejecutables, uno por tipo de mueble. Los dos aceptan cualquier juego:

| Programa | Mueble |
|---|---|
| **`dc2naomi.exe`** | NAOMI estándar: 2 palancas, 6 botones por jugador y 2 START |
| **`dc2naomict.exe`** | NAOMI Crazy Taxi: volante, acelerador, freno, palanca de 2 posiciones y START |

**Uso:** arrastra el `.chd` del juego **encima del icono** del programa (o abre el programa y arrastra el archivo a
su ventana, y pulsa Enter). Al terminar tendrás `JUEGO_dc2naomi.bin.gz` (o `JUEGO_dc2naomict.bin.gz`) junto al
`.chd`, listo para tu netbooter.

El programa te dice:

- **qué juego es** y su estado: **PROBADO** en placa real con ese mueble (con la configuración de botones que se
  ajustó para él), **EXPERIMENTAL** (no probado: se aplica la configuración por defecto y los parches se localizan
  automáticamente) o **NO FUNCIONA todavía** (te pregunta si quieres convertirlo igualmente);
- **cómo quedan los mandos**;
- si la imagen **no cabe** en la NetDIMM de 512 MB. Se genera igualmente: recorta tú el juego (vídeos, datos que
  no uses) y vuelve a convertirlo. Las pistas de audio de CD se descartan siempre (ver limitaciones).

Formatos de entrada: `.chd` (versión 5, la de cualquier `chdman` reciente) y `.gdi`. No hace falta `chdman`.

**La memoria (VMU).** Salvo en los juegos que ya iban bien sin ella (Crazy Taxi 2, Ikaruga, Yu Suzuki GW), el
programa activa la VMU emulada y deja junto al `.bin.gz` un `JUEGO_dc2naomi.vmu` vacío (128 KB). Para que las partidas
no se pierdan al apagar la placa hacen falta los scripts de la carpeta [`wipi/`](wipi/README.md) en tu WiPi Netbooter
(vienen también dentro del zip de Windows, con sus instrucciones en `LEEME_WIPI.txt`): copiar los dos `.py` a
`/sbin/piforce/`, cambiar dos líneas de `/sbin/piforce/wipiloader.py` y dejar el `.bin.gz` y el `.vmu` juntos en
`/boot/roms/`. Opciones para forzarlo: `--vmu` / `--sin-vmu`.

Algunos antivirus desconfían de los ejecutables hechos con PyInstaller. El código está en este repositorio y los
ejecutables se compilan en GitHub Actions (`.github/workflows/windows.yml`).

### Mandos por defecto

**Mueble estándar:** palanca = cruceta (y stick analógico al máximo), botones 1-6 = A, B, X, Y, L, R; cada jugador
con su START.

**Mueble Crazy Taxi:**

- Volante = stick analógico; al llegar al tope, también izquierda/derecha de la cruceta (menús).
- Acelerador = gatillo R, freno = gatillo L.
- Palanca adelante = B, atrás = A.
- START actúa **al soltarlo**, y solo si mientras estaba apretado no se tocó nada más.
- **Con START apretado:** palanca = arriba/abajo, freno = X, acelerador = Y.

Los juegos probados pueden tener su propia configuración (por ejemplo, en Crazy Taxi 2 START es el salto).

### Partidas guardadas (`vmutool.exe`)

`vmutool.exe` (en el mismo zip) mete y saca partidas del `.vmu` de un juego, en el formato `.VMI` + `.VMS` de las
descargas de partidas de Dreamcast (por ejemplo [bucanero/dreamcast-saves](https://github.com/bucanero/dreamcast-saves),
con partidas con todo desbloqueado de cientos de juegos):

- **Importar:** arrastra a la vez el `.vmu` del juego y el `.VMI` de la partida (con su `.VMS` en la misma carpeta)
  sobre `vmutool.exe`. Si la VMU ya tiene un fichero con ese nombre, lo sustituye y guarda la VMU anterior en `.bak`.
- **Exportar:** arrastra solo el `.vmu`: lista lo que hay y lo saca a la carpeta `JUEGO_partidas/` como `.VMI` + `.VMS`.
- En línea de comandos: `vmutool list|export|import|format ...` (`vmutool.exe` sin argumentos muestra la ayuda).
- Ojo: la partida tiene que ser de la misma región que el juego (en Daytona USA 2001, las americanas dicen
  "DAYTONA USA" en la cabecera y las japonesas "DAYTONA USA 2001"), y **no toques el `.vmu` de un juego mientras está
  cargado en el mueble** (la Raspberry lo sobrescribiría al guardar): carga otro juego, cambia el `.vmu` y vuelve a cargarlo.

### Juegos

| Juego | Mueble estándar | Mueble Crazy Taxi |
|---|---|---|
| Crazy Taxi 2 (USA) | experimental | ✅ probado (también con VMU en fichero) |
| Ikaruga (Japón) | ✅ probado | experimental |
| Namco Museum (USA) | experimental | ✅ probado (Pole Position: acelerador = A, freno = B, palanca = cambio) |
| Yu Suzuki Game Works Vol. 1 (Japón) | experimental | ✅ probado (Power Drift: el sonido petardea; salir con B deja negro) |
| Yu Suzuki GW, un juego por imagen (OutRun, Hang-On, Power Drift, After Burner II, Space Harrier) | — | sin probar en placa; se crean con `tools/mkgz.py` |
| KOF Dream Match 1999, Last Blade 2, SF III 3rd Strike, Super Puzzle Fighter II X, Super Street Fighter II X, KOF 2002, Mark of the Wolves | experimental (llegan al título en emulador) | experimental |
| F355 Challenge (USA) | experimental | ✅ probado con VMU en fichero y partida desbloqueada (esa partida trae la música a volumen 0: súbela en Options) |
| 18 Wheeler: American Pro Trucker (USA) | experimental | ✅ probado con VMU en fichero y partida desbloqueada (START + acelerador = vista, START + freno = bocina) |
| Sega Rally 2 (USA; arranca con Windows CE) | experimental | ✅ probado con VMU en fichero (sin la música de las carreras: son pistas de audio CD; la imagen activa de serie el modo oculto de 30 FPS del juego, pendiente de probar en placa) |
| SF III Double Impact | ❌ no funciona todavía | ❌ |
| Daytona USA 2001 | aún no soportado por el programa (necesita recodificar la música) | funciona en placa con una imagen hecha a mano, también con VMU en fichero |
| Cualquier otro juego de Dreamcast | experimental | experimental |

### Limitaciones

- **No hay audio de CD** (pistas CDDA): los juegos que ponen su música así quedan sin ella.
- **Memorias (VMU):** emulada, y probada en placa real solo con Namco Museum y Daytona USA 2001 (con los scripts de
  `wipi/` las partidas se conservan entre cargas de otros juegos: comprobado en placa con Daytona y Namco). Vive en la memoria
  de la placa y se pierde al apagarla, salvo que uses los scripts de [`wipi/`](wipi/README.md) (WiPi Netbooter), que
  guardan la tarjeta de cada juego en un fichero `.vmu` junto a su imagen. El resto de juegos (menos los tres que ya
  iban bien sin ella) la llevan activada sin haberse probado con ella en placa.
- **No están soportados los juegos especiales:** los que arrancan con Windows CE solo están resueltos para Sega Rally 2
  (cada juego trae su propio núcleo y hay que localizar sus manejadores de interrupción: ver HANDOFF); los
  Midway's Greatest Arcade Hits siguen sin funcionar y los que son un menú que carga varios programas (como SF III Double Impact).
- **Probado con NAOMI 2 y NetDIMM de 512 MB.** No se ha probado con NAOMI 1, aunque debería funcionar.

### Ideas para el futuro

- Audio de CD (recodificado para caber en la NetDIMM).
- Un aviso visible de "guardado en el fichero" (hoy solo está en el registro de la Raspberry).
- Llevar la vibración (Puru Puru Pack) al force feedback de los muebles NAOMI que lo tengan.

## Cómo funciona

- **`loader/`**: programa para NAOMI (KallistiOS) que arranca desde la NetDIMM, prepara el hardware y coloca el
  residente en la memoria alta.
- **`resident/`**: hace de BIOS de Dreamcast mientras corre el juego. Atiende sus llamadas al GD-ROM leyendo el
  disco desde la NetDIMM y traduce los mandos.
- **`tools/build_image.py`**: monta la imagen con el loader, los sectores originales del disco, una flash de
  Dreamcast y los parches de cada juego (`tools/games.py`), comprobados contra el disco al construir.
- **`tools/catalog.py`**: qué juegos están probados y con qué mueble; un juego se reconoce por la huella (SHA-1)
  de su programa. **`tools/findpatch.py`** localiza los parches de un juego desconocido.
- **`wipi/`**: scripts para WiPi Netbooter que guardan la VMU de cada juego en un fichero.
- **`tools/chd.py`**: lector de CHD propio. **`app/dc2naomi.py`**: el programa.

Los detalles técnicos, las direcciones y lo aprendido en la placa están en [HANDOFF.md](HANDOFF.md).

## Compilar

El programa es Python 3 sin dependencias: `python3 app/dc2naomi.py [--cab joy|ct] JUEGO.chd`. El loader viene
compilado en `app/loader.bin`; para regenerarlo tras tocar `resident/` o `loader/` hace falta
[KallistiOS](https://github.com/KallistiOS/KallistiOS) con `KOS_SUBARCH=naomi` y `app/make_loader.sh`.

Para desarrollo, `./build.sh PERFIL disco.gdi` construye un perfil concreto de `tools/games.py`.

## Contribuir

El código es abierto y **aceptamos pull requests verificados**: un juego nuevo, un ajuste de mandos o un arreglo.

**Verificado quiere decir probado en hardware real** (indica placa, NAOMI 1 o 2, NetDIMM y mueble). Probarlo solo en
Flycast no basta: el emulador es mucho más permisivo que la placa. Por ejemplo, Power Drift y Namco Museum leían los
mandos en Flycast y en la placa no (SB_MDAPRO). Flycast sirve para un primer
paso, pero el juego solo cuenta como probado cuando funciona en la placa.

## Agradecimientos

Este proyecto se apoya en el trabajo de mucha gente. Gracias a:

- **[KallistiOS](https://github.com/KallistiOS/KallistiOS)** (licencia BSD) y sus desarrolladores: el loader está
  hecho con KallistiOS para NAOMI (`KOS_SUBARCH=naomi`) y se empaqueta con su `naomibintool`. El soporte MIE/JVS de
  KallistiOS ([PR #1440](https://github.com/KallistiOS/KallistiOS/pull/1440)) sirvió de referencia para los mandos.
- **[Flycast](https://github.com/flyinghead/flycast)** (flyinghead y colaboradores): el emulador con el que se ha
  probado todo antes de llevarlo a la placa, y su HLE de la BIOS de Dreamcast (reios) fue la referencia para las
  llamadas al sistema que imita el residente.
- **[MAME](https://github.com/mamedev/mame)** y su equipo: el formato CHD y `chdman`. El lector de CHD de este
  proyecto (`tools/chd.py`) está escrito siguiendo su código (`chd.cpp`, `chdcodec.cpp`, `cdrom.cpp`, BSD-3-Clause).
- **[DreamShell](https://github.com/DC-SWAT/DreamShell)** y **SWAT** ([DC-SWAT](http://www.dc-swat.ru)): DreamShell
  se estudió y probó por netboot, y sus notas sobre NAOMI y JVS fueron de mucha ayuda.
- **[DragonMinded](https://github.com/DragonMinded)**: su [libnaomi](https://github.com/DragonMinded/libnaomi)
  documenta el protocolo de peticiones de la NetDIMM (`dimmcomms.c`), que el residente sigue para contestar las
  lecturas de memoria por red, y sus [herramientas de netboot](https://github.com/DragonMinded/netboot) son las que
  usamos para depurar en la placa real.
- **[dreamcast-saves](https://github.com/bucanero/dreamcast-saves)** (bucanero, Damian Parrino): la colección de
  partidas `.VMI`/`.VMS` de la que salen las partidas con todo desbloqueado que ponemos en los `.vmu`, y la referencia
  del formato `.VMI` para `tools/vmutool.py`.
- **[WiPi Netbooter](https://github.com/chunksin/WiPiNetbooter)** (chunksin y colaboradores): el netbooter con el
  que se carga y prueba todo en las placas, y en el que se apoyan los scripts de la VMU (`wipi/`), hechos a imagen
  de su `timehack.py`.
- **VMU:** el formato de la tarjeta y las respuestas maple siguen las de Flycast; para entenderla sirvieron también
  [MaplePad](https://github.com/mackieks/MaplePad) (mackieks), [libevmu](https://github.com/gyrovorbis/libevmu)
  (Falco Girgis), [dcvmu-tool](https://github.com/bucanero/dcvmu-tool) (bucanero),
  [waterbear](https://github.com/wtetzner/waterbear) (wtetzner) y [chao](https://github.com/lordbananza/chao)
  (lordbananza), que nos pasó el usuario como referencia.
- **[wince-dc](https://github.com/maximqaxd/wince-dc)** (maximqaxd), que nos pasó el usuario: su SDK de Windows CE
  2.12 para Dreamcast, los mapas de símbolos del núcleo y su `wrap-image.ps1` sirven de referencia para el estudio de
  los juegos con Windows CE (formato de `0WINCEOS.BIN`).
- La comunidad de **Dreamcast y NAOMI** que ha documentado durante años el hardware (Katana, Holly, AICA, maple, JVS,
  NetDIMM) y los desarrolladores de los **netbooters** para NAOMI.
- **[DejaVu Fonts](https://dejavu-fonts.github.io)**: la letra de los mensajes en pantalla sale de DejaVu Sans Mono.
- **[PyInstaller](https://pyinstaller.org)** y **GitHub Actions**, con los que se compilan los ejecutables de Windows.
- Herramientas usadas durante el desarrollo: GCC para SH-4, Python, ffmpeg y genisoimage.
- Proyectos hermanos de los que viene buena parte de lo aprendido:
  [naomi-wheel-games](https://github.com/0skarzer0/naomi-wheel-games) y
  [mame4all-naomi](https://github.com/0skarzer0/mame4all-naomi) (incluido su parche MIE para Flycast).

Si hemos usado algo tuyo y no apareces aquí, abre una incidencia y lo añadimos.

## Aviso legal

Este repositorio **no contiene** juegos, imágenes de disco, BIOS ni desensamblados: solo código propio y, de los
juegos, direcciones de memoria y huellas SHA-1. Necesitas **tu propio volcado** de cada juego. Dreamcast, NAOMI y
los juegos citados son marcas de sus propietarios.

Parte del proyecto [naomi-wheel-games](https://github.com/0skarzer0/naomi-wheel-games).
