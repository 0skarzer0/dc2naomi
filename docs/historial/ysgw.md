# Historial: Yu Suzuki Game Works separado (2026-11-09 a 11-11)

> Historial: diario de sesiones copiado tal cual del antiguo `HANDOFF.md` (2026-11-25). Puede estar superado por lo escrito después; lo vigente está en [HANDOFF.md](../../HANDOFF.md).

> **Ojo con las IP:** en este diario la Pi del mueble Crazy Taxi aparece como **.60** (y la del mueble estándar a veces como **.59**). Desde el 2026-11-19 son **192.168.68.251** (Crazy Taxi) y **192.168.68.250** (estándar). El texto se deja como se escribió.


**Yu Suzuki, `ysgw6` (2026-11-09):** mandos `ysgw` (`DIMM_PAD_YSGW` = 5): los del mueble por defecto y, a petición del
usuario, un modo avión manual: **START + volante a tope a la derecha** = avión (palanca adelante = arriba, atrás =
abajo, en cruceta y stick; acelerador = A disparo, freno = B misil; volante = stick X y cruceta desde media vuelta),
**START + volante a tope a la izquierda** = coche. Con START apretado el volante no manda cruceta. Pendiente de
confirmar en placa qué botón es disparo y cuál misil en After Burner II, y el sentido de la palanca. Hecha con el
programa desde el CHD (disco idéntico a `ysgw5`). En Flycast llega a PRESS START.

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
