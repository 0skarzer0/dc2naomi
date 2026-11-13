# dc2naomi — juegos de Dreamcast en Sega NAOMI

Convierte un juego de **Dreamcast** (tu propio volcado en `.chd` o `.gdi`, o un CD de autoarranque en `.cdi`) en una imagen para arrancarlo en una
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

**Uso:** arrastra el `.chd` (o `.gdi`, o `.cdi`) del juego **encima del icono** del programa (o abre el programa y arrastra el archivo a
su ventana, y pulsa Enter). Al terminar tendrás `JUEGO_dc2naomi.bin.gz` (o `JUEGO_dc2naomict.bin.gz`) junto al
`.chd`, listo para tu netbooter.

El programa te dice:

- **qué juego es** y su estado: **PROBADO** en placa real con ese mueble (con la configuración de botones que se
  ajustó para él), **EXPERIMENTAL** (no probado: se aplica la configuración por defecto y los parches se localizan
  automáticamente) o **NO FUNCIONA todavía** (te pregunta si quieres convertirlo igualmente);
- **cómo quedan los mandos**;
- si la imagen **no cabe** en la NetDIMM de 512 MB. Se genera igualmente: recorta tú el juego (vídeos, datos que
  no uses) y vuelve a convertirlo. Las pistas de audio de CD se descartan siempre (ver limitaciones).

**Si no cabe por los vídeos** (películas Sofdec, `.SFD`), se pueden recodificar a menos calidad sin quitar nada
(hace falta Python 3 y ffmpeg; no está en los ejecutables):

```
python3 tools/sfdre.py ORIGINAL.SFD NUEVO/MOVIES/INTRO.SFD 2500      # kbit/s del vídeo; el sonido no se toca
python3 tools/withfiles.py NUEVO --cab joy --batch JUEGO.chd          # convierte con esos archivos sustituidos
```

Para ver cómo es un vídeo: `tools/sfdinfo.py X.SFD`. Para música con un archivo por canal (`*L` / `*R`):
`tools/withfiles.py - --alias "*R.P16=*L.P16" --cab joy --batch JUEGO.chd` la deja en mono (Soulcalibur, 683 → 469 MB).
Para buscar una partida con todo desbloqueado de la misma región: `tools/findsave.py` (instrucciones dentro).
Música y voces en archivos ADX empaquetados en `.AFS` (Metropolis Street Racer, 758 → 487 MB):
`tools/afsmono.py ORIG.AFS NUEVO/SOUND/X.AFS [--half-rate]` pasa cada ADX estéreo a mono (y, con `--half-rate`, a la
mitad de frecuencia, para voces) con `tools/adxmono.c` (lo compila con gcc). Música en PCM sin comprimir de San
Francisco Rush 2049 (`.STR`): `tools/rushstr.py` (mono, **sin probar en placa**); si suena mal, que varios circuitos
compartan canción con `--alias "BASSY.STR=HIGH.STR"`.

`sfdre.py` mantiene el tamaño, la frecuencia, las imágenes y el patrón (GOP) de cada vídeo y el sonido ADX byte a
byte; `withfiles.py` escribe cada archivo nuevo donde estaba el original. **Probado en placa con Rainbow Cotton**
(16 vídeos a 0,9 Mbit/s: 873 → 500 MB); Buzz Lightyear de la misma forma (43 vídeos a 2,5 Mbit/s: 559 → 437 MB).

Formatos de entrada: `.chd` (versión 5, la de cualquier `chdman` reciente), `.gdi` y `.cdi` (DiscJuggler 2, 3 y
3.5: los CD de autoarranque, la forma habitual de las traducciones). No hace falta `chdman`.

**CD de autoarranque (`.cdi`).** El juego está en la última sesión del CD, en su propia dirección (11700, 45000…),
y así se sirve; el `1ST_READ.BIN` se descifra como hace la BIOS si viene cifrado (MIL-CD), y el relleno que llevan
muchos de estos discos para colocar los datos al borde del CD (un archivo de un solo byte repetido, p. ej. 448 MB
en Cannon Spike) no se copia a la imagen. La música en pistas de audio de CD no suena (ver limitaciones).
Comprobado contra el disco original archivo por archivo (`tools/cmpimage.py`); **ninguno probado aún en placa**.

**La memoria (VMU).** Salvo en los juegos que ya iban bien sin ella (Crazy Taxi 2, Yu Suzuki GW), el
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
| Ikaruga (Japón) | ✅ probado (también con VMU en fichero y partida desbloqueada) | experimental |
| Super Street Fighter II X, traducción al inglés de ComradeSnarky | ✅ probado (con VMU y partida desbloqueada de bucanero/dreamcast-saves) | experimental |
| Namco Museum (USA) | experimental | ✅ probado (Pole Position: acelerador = A, freno = B, palanca = cambio) |
| Yu Suzuki Game Works Vol. 1 (Japón) | experimental | ✅ probado (Power Drift: salir con B deja negro) |
| Yu Suzuki GW, un juego por imagen (OutRun, Hang-On, Power Drift, After Burner II, Space Harrier) | — | ✅ probados OutRun, Hang-On, Power Drift (su música petardeaba en la NAOMI: resuelto) y After Burner II (disparo automático, acelerador = gases, freno = misil, START + acelerador = frenar, START + freno = quitar/poner el disparo automático; las luces del arcade, en el botón START); Space Harrier (acelerador = disparo rápido); se crean con `tools/mkgz.py` |
| KOF Dream Match 1999, Last Blade 2, SF III 3rd Strike, Super Puzzle Fighter II X, Super Street Fighter II X, KOF 2002, Mark of the Wolves | experimental (llegan al título en emulador) | experimental |
| F355 Challenge (USA) | experimental | ✅ probado con VMU en fichero y partida desbloqueada (esa partida trae la música a volumen 0: súbela en Options) |
| 18 Wheeler: American Pro Trucker (USA) | experimental | ✅ probado con VMU en fichero y partida desbloqueada (START + acelerador = vista, START + freno = bocina) |
| Sega Rally 2 (USA; arranca con Windows CE) | experimental | ✅ probado con VMU en fichero (sin la música de las carreras: son pistas de audio CD; la imagen activa de serie el modo oculto de 30 FPS del juego, pendiente de probar en placa) |
| SF III Double Impact (USA) | ✅ probado (los dos juegos y el menú; con VMU en fichero y partida desbloqueada) | experimental |
| Daytona USA 2001 | aún no soportado por el programa (necesita recodificar la música) | funciona en placa con una imagen hecha a mano, también con VMU en fichero |
| OutRun 2006 Coast 2 Coast, demo para Dreamcast de ArkRetro (homebrew KallistiOS; v37, perfil `or37`) | — | llega al título y a la demo en emulador; 24 de sus 28 canciones largas suenan como una de las 4 primeras (no cabe en 512 MB) |
| Cualquier otro juego de Dreamcast | experimental | experimental |

### Limitaciones

- **No hay audio de CD** (pistas CDDA): los juegos que ponen su música así quedan sin ella (también los `.cdi` con
  pistas de audio, como Unreal Tournament o Millennium Racer).
- **Memorias (VMU):** emulada, y probada en placa real solo con Namco Museum y Daytona USA 2001 (con los scripts de
  `wipi/` las partidas se conservan entre cargas de otros juegos: comprobado en placa con Daytona y Namco). Vive en la memoria
  de la placa y se pierde al apagarla, salvo que uses los scripts de [`wipi/`](wipi/README.md) (WiPi Netbooter), que
  guardan la tarjeta de cada juego en un fichero `.vmu` junto a su imagen. El resto de juegos (menos los tres que ya
  iban bien sin ella) la llevan activada sin haberse probado con ella en placa.
- **No están soportados los juegos especiales:** los que arrancan con Windows CE solo están resueltos para Sega Rally 2
  (cada juego trae su propio núcleo y hay que localizar sus manejadores de interrupción: ver HANDOFF); los
  Midway's Greatest Arcade Hits siguen sin funcionar. Los que son un menú que carga varios programas necesitan los
  parches de cada programa en su perfil (resuelto para SF III Double Impact y Yu Suzuki Game Works).
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

## Juegos convertidos

Lo que hay cargado en la NAOMI de palancas y su estado: [docs/pi250-juegos.md](docs/pi250-juegos.md). Los del mueble
Crazy Taxi: [naomi-wheel-games/docs/pi60-juegos.md](https://github.com/0skarzer0/naomi-wheel-games/blob/main/docs/pi60-juegos.md).

## Agradecimientos

Este proyecto se apoya en el trabajo de mucha gente. Gracias a:

- **[KallistiOS](https://github.com/KallistiOS/KallistiOS)** (licencia BSD) y sus desarrolladores: el loader está
  hecho con KallistiOS para NAOMI (`KOS_SUBARCH=naomi`) y se empaqueta con su `naomibintool`. El soporte MIE/JVS de
  KallistiOS ([PR #1440](https://github.com/KallistiOS/KallistiOS/pull/1440)) sirvió de referencia para los mandos.
- **[Flycast](https://github.com/flyinghead/flycast)** (flyinghead y colaboradores): el emulador con el que se ha
  probado todo antes de llevarlo a la placa, y su HLE de la BIOS de Dreamcast (reios) fue la referencia para las
  llamadas al sistema que imita el residente.
- **cdirip** (DeXT) y los emuladores que leen imágenes de DiscJuggler (Flycast, Redream, Demul): el formato `.cdi`
  (de DiscJuggler, de Padus) que lee `tools/cdi.py` sigue la descripción de cdirip; no se ha copiado código.
- **Marcus Comstedt** y su `scramble` (en los `utils` de KallistiOS): el algoritmo del cifrado MIL-CD del
  `1ST_READ.BIN` de los CD, que `tools/cdi.py` deshace como la BIOS de Dreamcast.
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
- **[ArkRetro](https://github.com/ArkRetro)**: su demo de OutRun 2006 Coast 2 Coast para Dreamcast (homebrew con
  KallistiOS), que el usuario convierte para su mueble de Crazy Taxi (la demo no se incluye).
- **ComradeSnarky**: su traducción al inglés de Super Street Fighter II X for Matching Service, que el usuario
  convierte y juega en la placa (el parche no se incluye: hay que conseguirlo de su autor).
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
- Herramientas usadas durante el desarrollo: GCC para SH-4, Python, ffmpeg y genisoimage. **ffmpeg** recodifica
  además el vídeo MPEG-1 de las películas Sofdec (de CRI Middleware) que `tools/sfdre.py` vuelve a empaquetar
  con la misma estructura que las originales (Rainbow Cotton).
- **[vgmstream](https://github.com/vgmstream/vgmstream)**: la descripción del ADX de CRI (cabecera, coeficientes de
  predicción a partir del filtro, fórmula de decodificación) que siguen `tools/adxmono.c` y `afsmono.py` sale de su
  código y documentación; no se ha copiado código. El resultado se comprobó decodificándolo con **ffmpeg**
  (`adpcm_adx`), cuyo propio codificador ADX sirvió de referencia de calidad.
- Proyectos hermanos de los que viene buena parte de lo aprendido:
  [naomi-wheel-games](https://github.com/0skarzer0/naomi-wheel-games) y
  [mame4all-naomi](https://github.com/0skarzer0/mame4all-naomi) (incluido su parche MIE para Flycast).

Si hemos usado algo tuyo y no apareces aquí, abre una incidencia y lo añadimos.

## Aviso legal

Este repositorio **no contiene** juegos, imágenes de disco, BIOS ni desensamblados: solo código propio y, de los
juegos, direcciones de memoria y huellas SHA-1. Necesitas **tu propio volcado** de cada juego. Dreamcast, NAOMI y
los juegos citados son marcas de sus propietarios.

Parte del proyecto [naomi-wheel-games](https://github.com/0skarzer0/naomi-wheel-games).
