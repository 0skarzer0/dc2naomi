# Historial: juegos Katana en placa (Namco, CT2, VMU, F355, 18 Wheeler, SSF2X, LB2FE, fallos del 11-19)

> Historial: diario de sesiones copiado tal cual del antiguo `HANDOFF.md` (2026-11-25). Puede estar superado por lo escrito después; lo vigente está en [HANDOFF.md](../../HANDOFF.md).

> **Ojo con las IP:** en este diario la Pi del mueble Crazy Taxi aparece como **.60** (y la del mueble estándar a veces como **.59**). Desde el 2026-11-19 son **192.168.68.251** (Crazy Taxi) y **192.168.68.250** (estándar). El texto se deja como se escribió.

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
**⭐ `sf3di` (SF III Double Impact): FUNCIONA EN PLACA (usuario, 2026-11-12 15:21: "funciona muy bien, la he estado
probando y no tiene fallos"; menú y los dos juegos, con VMU en fichero y la partida `v50554` desbloqueada).**
Antes se quedaba en el aviso de VMU: 1ST_READ solo es un cargador, y el menú y los juegos son programas aparte con su
propio driver de maple y su propia lectura del cable. Cómo se resolvió:
1. Sacar los programas del CHD (`gdi.open_disc(chd).read_file("GAMESEL/GAMESEL.BIN")`, etc.; en el PC del usuario).
2. **La dirección de carga de cada uno, por sus literales:** `findpatch.analyze` no encontraba gancho en GAMESEL a
   base 0x8c010000; buscando la función "a física" de 1ST_READ (`mov.l 0x0fffffff,r0; rts; and r4,r0`) por sus bytes
   aparece en GAMESEL en el desplazamiento 0x170a1e, y el código que escribe SB_MDSTAR la llama por un literal que vale
   `0x8ce70a1e` → **GAMESEL se carga en `0x8cd00000`**. SF3_1ST y SF3_2ND se cargan en `0x8c010000` (encima de
   1ST_READ: sus literales de gancho caen dentro del fichero a esa base).
3. Con `findpatch.analyze` a la base buena: cable (`mov.w @r3,r4` → `mov #0,r4`) y gancho de maple de cada programa.
4. Un grupo por programa en el perfil (`GAMES["sf3di"]["groups"] += [...]`): el residente aplica los grupos en cada
   llamada al GD-ROM, cada uno con su palabra de control, así que se parchea el programa que esté cargado.
**Microparadas (resuelto, usuario 15:51):** había una parada corta cada segundo en menús y partida, también con el
vigilante de VMU parado. Medido en placa (`gd_reads[]` del residente): el juego lee ~1 vez por segundo 32 sectores
(64 KB, ~44 KB/s) y cada `EXEC_SERVER` copiaba 32 sectores con las interrupciones cortadas. Nuevo campo de cabecera
**`dimm_header.read_chunk`** (perfil `"read_chunk"`; 0 = 32 de siempre) y variable `read_chunk` del residente
(probada en caliente con pokes: 32, 4, 16, 8): **`sf3di` usa 4 (8 KB)**. Con 4 "va mejor". (Un efecto de sonido que no
sonaba era un altavoz del mueble: no era el juego.)
Imagen en la Pi .250 (`dc-sf3di_dc2naomi.bin.gz`, md5 de la `.gz` `9657e964e17ac7f6c2ffce66a43db3be`; hecha cambiando
loader y la palabra 177 de la cabecera de la imagen probada) y su `.vmu` = la partida desbloqueada con lo guardado
en las pruebas (la anterior en `_test/sf3di_vmu_before_20261112.bak`). Copia en el PC: `otros/sf3di_files/`.
Nota: el CHD ya no está en `dreamcastisos/` del PC (el usuario lo ha movido).

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


**⚠️ Corrección (2026-11-09 noche): la `ct2h6` entregada no aplicaba ningún parche** (el usuario: "no ve el mando en el
puerto A"). `convhdr.py` suponía el formato viejo con `DIMM_TRACKS` 8, pero `ct2h4` se hizo con 4 rangos y **32**
pistas (el historial de `resident.h`: 8 pistas hasta el 08-11 13:10, 32 hasta el 09-11 02:12, luego 32/64). La tabla
de parches quedó con 6 entradas vacías delante y el residente se para en la primera. Mi comprobación filtraba las
vacías y no lo vio. `convhdr.py` ahora deduce el formato (la tabla debe empezar por una comprobación de grupo) y lo
comprueba. Imagen buena: **`ct2h7`** (= la v6 bien hecha). Comprobado en Flycast en la RAM: literal del gancho
`0x8c166ee0` = `0x8dc01884`, cable parcheado, mando en el puerto A, START pasa de la pantalla de VMU.
**Ojo al probar mandos en Flycast:** sin `FC_PEDALS=1` el acelerador y el freno están a media carrera (`0x8000`), así
que con los mapas `wheel`/`ct` START cuenta como "usado" (pedal > 64) y no se envía. Usar `FC_PEDALS=1`.

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

## Ikaruga con VMU desbloqueada para el mueble estándar (2026-11-12) — `dc-ikaruga_dc2naomi.bin.gz`

Pedido por el usuario. No había disco de Ikaruga en el PC: se partió de la imagen buena de la Pi .250
(`ikaruga_joy_dc2naomi.bin.gz`, cabecera antigua, probada en placa el 2026-11-09).
- `tools/convhdr.py ikaruga_joy_dc2naomi.bin.gz conv.bin.gz "IKARUGA DC"` (cabecera nueva y `app/loader.bin` actual;
  mismos 8 parches, mandos `joy` = 2) y `tools/addvmu_stream.py conv.bin.gz dc-ikaruga_dc2naomi.bin.gz app/loader.bin 2`
  (flags `0x8004`). md5 `87f68248de681d7cde707b90737c66a4`.
- VMU `dc-ikaruga_dc2naomi.vmu` (md5 `6038d6ff…`): `IKARUGA_DATA` de bucanero/dreamcast-saves (`r/ikaruga`,
  "Credit MAX, All Mode Unlocked!", 34 bloques).
- En la Pi .250: `/boot/roms/dc-ikaruga_dc2naomi.{bin.gz,vmu}` (md5 comprobado), fila nueva en
  `/boot/config/romsinfo.csv` (copia `romsinfo.csv.bak_ikaruga_vmu`) importada con `importcsv.py`. **Se dejan las
  entradas viejas** (`ikaruga_joy`, `ikaruga_joy_g2cpu`) por si la nueva falla. Copia en el PC: `dc2naomi/ikaruga/`.
  Ojo: `/boot` de esa Pi está al 100 % (≈190 MB libres tras esto).
- **✅ Probado en placa (usuario, 2026-11-12 11:12: "funciona estupendamente").** Ikaruga va con el residente actual y
  con la VMU en fichero. (En Flycast se queda en el logo 斑鳩, también la imagen vieja: Flycast no sirve para Ikaruga.)
  Quitado `ikaruga` de `catalog.NO_VMU`: el programa ya le pone VMU.

## Super Street Fighter II X, traducción al inglés de ComradeSnarky (2026-11-12) — `dc-ssf2x_en_dc2naomi.bin.gz`

Pedido por el usuario (CHD `Super Street Fighter II X for Matching Service (Japan) [T-En by ComradeSnarky]`).
`app/dc2naomi.py --cab joy --batch` (11 s): 159,5 MB, 124,5 MB comprimida; juego desconocido para el catálogo
(parches de `findpatch`), mandos `joy`. md5 `f908f639dd77766bf580b0df00f33035`.
- VMU: `SSF2X.VMI` de bucanero/dreamcast-saves (`r/ssf2x`, "Everything unlocked, including DIP Switch Menu!"). Ojo:
  las cuatro partidas de esa carpeta se llaman igual (`SSF2X___.SYS`) y `vmutool import` sustituye: importar solo esa.
- Pi .250: `/boot/roms/dc-ssf2x_en_dc2naomi.{bin.gz,vmu}` (md5 comprobado), fila en `/boot/config/romsinfo.csv`
  (copia `romsinfo.csv.bak_ssf2x_en`) importada con `importcsv.py`. Copia en el PC: `dc2naomi/ssf2x_en/`.
  `/boot` de esa Pi: 2,5 GB libres (el usuario liberó espacio).
- **2026-11-12: en la placa, negro tras el logo de SEGA (en Flycast va: llega a "Save file loaded", CAPCOM y el
  título). RESUELTO, usuario 12:37: "ya funciona estupendamente".** Cómo se encontró (receta 4, con el VMU puesto):
  `dclb.py` (= `dcl.py` sin enviar) + `dc2naomi_send.py` de la imagen con flags `0x20200`; tras el cuelgue (el vigilante
  de VMU dice "no answer"; los peeks ya no contestan porque el gancho de maple no corre), cargar Ikaruga (14 MB) y leer
  la caja negra: 1 excepción, **EXPEVT `0xe0`** (error de dirección en lectura), **SPC `0x8c197bd2`** (`mov.w @r3,r1`),
  **TEA `0x8c0224b3`**. El código (`0x8c197b92`): `índice = *(u16 *)(*0x8c2d55b4 + 0x380)`, si 0 → byte `+0x462`, si no
  → 12; luego lee la tabla `0x8c0268f8 + índice`. TEA − tabla = −0x4445 → la palabra era **`0xbbbb`**: `*0x8c2d55b4` =
  `0x8c600000`, memoria de trabajo del juego que **lee antes de escribirla**. En Flycast la RAM empieza a cero (0 →
  índice válido); en la placa tiene lo que dejaron el loader y los juegos anteriores.
  **Arreglo general (residente, `boot()`):** pone a cero la RAM del juego (`0x8c008000` → `RES_BASE`) antes de leer
  IP.BIN, línea a línea por la caché y con `ocbp` en cada línea (para que ninguna línea sucia del loader se escriba
  encima después). Lo llevan todas las imágenes nuevas; las viejas siguen igual (cambiar su loader con `dcl.py`/
  `withfiles.py` si fallan así). En Flycast la imagen con el arreglo sigue llegando al título.
  Imagen nueva (solo cambia el loader): md5 de la `.gz` `b76d824ebd649d4072042434d215b55b`, en la Pi .250 y en el PC
  (`dc2naomi/ssf2x_en/`); su `.vmu` en la Pi es el de la partida de prueba (el anterior: `_test/en_vmu_before.bak`).
  Las versiones japonesa (`dc-ssf2x`) y española (`dc-ssf2x_es`) de la Pi llevan el loader viejo: **sin probar**; si se
  quedan en negro igual, cambiarles el loader.
- **Por qué `ssf2x_es` ocupa el doble que `ssf2x_en` (300 frente a 131 MB comprimidas; 332 frente a 160 MB):** los
  dos discos tienen los mismos 567 archivos, pero en el CDI español las músicas de escenario (`S_*.ADX`, 15 archivos)
  son **piezas largas** de 3,5-4,5 minutos (por ejemplo `S_RYU_02.ADX`: 11,5 MB, 242 s) en vez de los bucles de
  ~1 minuto del original (2,6 MB, 56 s). Mismo formato (ADX tipo 3, estéreo, 44,1 kHz): el ADX apenas se comprime, así
  que se nota entero en la imagen. Medido con `gdi.open_disc(...).walk()` y la cabecera ADX de cada archivo.
  **El usuario la descarta (2026-11-12: "no merece la pena la española"):** borrados de la Pi .250
  `dc-ssf2x_es_dc2naomi.{bin.gz,vmu}` y su fila (copia `romsinfo.csv.bak_ssf2x_es`; reimportado con `importcsv.py`).
  La copia del PC (`isosdream/`) se queda.
  Después también la japonesa (usuario: "la japonesa la quitamos también, dejamos la inglesa"): borrados
  `dc-ssf2x_dc2naomi.{bin.gz,vmu}` de la .250 y su fila (copia `romsinfo.csv.bak_ssf2x_jp`). En la .250 solo queda
  `dc-ssf2x_en`. La copia del PC (`dreamcastisos/ssf2x_dc2naomi.*`) se queda.
- **Limpieza de la Pi .250 (usuario, 2026-11-12: "quita las líneas huérfanas y las versiones de Dreamcast que ya
  estén en arcade"):** fuera del CSV (copia `romsinfo.csv.bak_dc_dupes`, reimportado) las filas huérfanas
  `ikaruga_joy_dc2naomi` e `ikaruga_joy_g2cpu_dc2naomi` (sus ficheros ya no estaban) y `dc-ikaruga` y `dc-cspike_es`
  (el usuario tiene los originales de NAOMI, `n1-ikaruga_v3` y `n1-cannon_spike`); borrados sus `.bin.gz` y `.vmu`.
  Las copias del PC se quedan. **Para la receta 4 (leer la caja negra cargando otra imagen) ya no está Ikaruga en esa
  Pi:** usar la más pequeña que quede (`dc-spf2x`, 110 MB) o subir una.
  **Corrección (13:40): Ikaruga de Dreamcast vuelve a la .250.** El original de NAOMI (`n1-ikaruga_v3`, y también
  `n1-shikigami_no_shiro_2`) es **vertical** (monitor girado); la versión de Dreamcast se juega en un monitor
  horizontal, así que **no es un duplicado**: no quitar versiones de Dreamcast de juegos verticales aunque esté el arcade.
  Subidos desde el PC `dc-ikaruga_dc2naomi.{bin.gz,vmu}` (md5 de la `.gz` `87f68248de681d7cde707b90737c66a4`; el `.vmu`
  es el desbloqueado del PC: lo guardado en la placa desde el día 11 se perdió al borrarlo) y su fila de nuevo en el CSV
  (copia `romsinfo.csv.bak_ikaruga_back`). Vuelve a servir para la receta 4 (14 MB).
- **Ojo con la Pi .250:** se reinició dos veces mientras comprimía una imagen con `pigz` (`vcgencmd get_throttled` =
  `0x50005`: **falta de tensión**). En esa Pi no comprimir imágenes grandes: hacerlo en el contenedor o en el PC y
  subir el `.gz` ya hecho (`piput.py` / `tools/board/piup.sh`).

## The Last Blade 2 Final Edition (Japón, parche VGA) — perfil `lb2fe`, Pi .250 (2026-11-18) — sin probar en placa

**Problema:** `dc-lastblade2_dc2naomi` (USA) en la .250 se queda en negro tras el logo de SEGA y el monitor dice
"OUT OF RANGE … 15.2KHZ 29HZ". La versión USA no tiene modo VGA: el campo de periféricos del IP.BIN es `07BBA00` (bit
VGA 0x10 a cero) y el juego fija NTSC 480i (15 kHz) diga lo que diga el cable. No se arregla con un parche de cable.

**Solución elegida por el usuario:** convertir su `THE LAST BLADE 2 FINAL EDITITION (JAPONES)-(VGA).7z` (T3107M
V1.003, IP.BIN `07BBA10`, parche VGA de la comunidad; 774 MB en `.gdi`):
1. `discfiles.py DISCO ORIG .SFD` + `sfdbatch.py`: los 29 `ZSFD/*.SFD` de 477 MB a 106 MB.
2. `withfiles.py NUEVOS --cab joy --batch disc.gdi` → 404 MB (323 MB en .gz). Hizo falta arreglar `withfiles.py`
   (f08f75d): con un `.gdi` de origen los sectores puestos a cero no se quitaban y salían 775 MB.
3. **Perfil `lb2fe`** (catálogo por SHA1 del 1ST_READ `6d0dd952…`). `findpatch.py` adivinó mal los puntos del cable
   (0x8c13a47e y 0x8c15d38a no son lecturas de PDTRA: corrompían código y se colgaba tras SEGA). Los buenos:
   - 0x8C132B7E `mov.w @r3,r4` (PDTRA, 0xFF800030) → `mov #0,r4`;
   - 0x8C15588A `mov.w @r0,r0` → `mov #0,r0`: es la comprobación del propio parche VGA (si cable = VGA llama a
     0x8c11f534(0), que pone los bits de salida de audio del AICA 0xa0702c00);
   - HOOK en el literal 0x8C14ADD8 (función "a física" 0x8c14c426).
4. Con eso salían los logos (SEGA, Sofdec, SNK) y luego **negro con el juego vivo** (la música y la demo seguían: la
   caja negra mostraba lecturas de `MUSIC.AFS`, `VOICE.AFS`, `TIT.GKC`, `GE*.GKC`). Con `FC_REGTRACE=1` en Flycast:
   al pasar a 320×240 se escribe **VO_STARTY = 0x0027fff8** → campo 1 = línea 1016, fuera de la pantalla. Causa: un
   fallo del parche VGA. Su código (0x8c1557c6) guarda el VO_STARTY de su tabla (0x00280028) en las variables del
   juego al revés: `extu.w` → 0x8cef9f70 (campo 2) y `shll16` → 0x8cef9f6c (campo 1 = 0x00280000). El juego suma cada
   cuadro su desplazamiento vertical (0x8cef9f64 = -8 en ese modo) y escribe `[9f6c]+d | ([9f70]+d)<<16`
   (0x8c13c766). **Parche:** 0x8C1557D2 `shll16 r0` (0x4028) → `extu.w r1,r0` (0x601D). En Flycast llega a la intro
   ("1864年", SNK Presents…), al título y al menú (STORY / VS / TIME ATTACK / …).
5. Subida a la .250 como `dc-lastblade2fe_dc2naomi.bin.gz` + `.vmu` vacía (md5 del .gz `cefbbd0f…`), comprimida en la VM
   del PC (no comprimir en la Pi .250: se reinicia por baja tensión). En `romsinfo.csv` la fila de
   `dc-lastblade2_dc2naomi.bin.gz` (USA) se cambió por la de la Final Edition (copia: `romsinfo.csv.bak_lb2fe`) y se
   reimportó. El `.bin.gz` USA y su `.vmu` siguen en `/boot/roms/` sin fila (no salen en el menú).
6. Cargada con `dc2naomi_send.py 10.0.0.3` dentro de `nohup sh -c "…; timehack; vmu watch"`. **Ojo:** `pkill -f
   timehack.py` lanzado por SSH se mata a sí mismo (el patrón está en su propia línea de órdenes): usar
   `pkill -f "[t]imehack.py"`. Y el envío de 340 MB (unos 2 min) tarda más que el tiempo de espera de `pi.py`: lanzarlo
   con nohup. `dc2naomi_send.py` de la .250 ya arranca él solo el vigilante de la VMU al acabar: no lanzar otro (quedaron
   dos y se mató uno); `timehack.py` sí hay que arrancarlo a mano. Cargada 2026-11-18 21:10 (hora de la Pi, que va
   atrasada), sin probar aún en placa.

**Para otros juegos con parche VGA:** si tras los logos queda negro con el juego vivo, mirar VO_STARTY/VO_STARTX con
`FC_REGTRACE=1` (`tools/flycast/run1.sh`): los parches VGA reescriben los modos de vídeo y pueden dejar mal las
variables que el juego reutiliza cada cuadro.

## Fallos del 2026-11-19 (TD6, Airline Pilots, Wacky Races, SPF2X, Rush 2049, MSR)

El usuario probó en placa y avisó: TD6 se queda con la música sonando tras START; Airline Pilots (NAOMI original, pasado
de la .250 a la .60) dice "CAUTION 51 game assignments are incorrect"; Wacky Races pide un mando en el puerto A; SPF2X
se cuelga tras los logos de CAPCOM y ADX; Rush 2049 (las dos) deja de responder y va lento tras START; MSR, pantalla
negra tras el vídeo.

**Programas cargados encima de 1ST_READ (Wacky Races, Test Drive Le Mans, MSR).** En esos discos `1ST_READ.BIN` es un
cargador y el juego otro programa en 0x8c010000 (Wacky Races: `WACKY.BIN` + `MOVIE.BIN`; Le Mans: `FMV.BIN` +
`LEMANS24.BIN`; MSR: `MSR.BIN`). El perfil automático solo parcheaba `1ST_READ.BIN`: el programa siguiente usaba su
propio driver de maple contra el MIE (caja negra: 0 llamadas al gancho). Cómo verlo: `hdr.py` del perfil + volcado de
RAM en Flycast (`DUMP=1`): las palabras de comprobación ya no están y `findpatch` sobre la RAM da otro gancho.
- `app/dc2naomi.py other_programs()`: el perfil automático añade un grupo por cada `.BIN/.EXE/...` de 64 KB-8 MB con
  muchos literales 0x8cXXXXXX ≥ 0x8c010000 en el que findpatch encuentra gancho de maple (cable y gancho, como 1ST_READ).
- `tools/addprograms.py IMAGEN.bin.gz DISCO [SALIDA]`: añade esos grupos a una imagen ya hecha (no toca los ficheros
  sustituidos: vídeos recodificados, audio mono). Hechas en `otros/fix/` del PC: msr, rush2049, rush2049_9, tdlemans.
- Ojo: `2_DP.BIN` (Rush 2049, MSR, SW Racer, TXR2, Net de Tennis, Vampire Chronicle) y `DP_BEXP3.BIN` (TNN) son el
  navegador DreamPassport, no el juego: parchearlo no cambia nada.
- Wacky Races reconvertido con el perfil nuevo (`dreamcastisos/Wacky Races (USA)_dc2naomict.bin.gz`): en Flycast ve el
  mando y la VMU y llega a los menús y a elegir piloto.
- Escaneo de todos los CHD de `dreamcastisos` (`~/scanall.py` en la VM): solo los citados tienen otro programa del juego.

**MSR: lectura en streaming del vídeo (`DIMM_DMAIRQ`, 0x80000).** Con `MSR.BIN` ya enganchado seguía negro: pedía
`DMA_READ_REQ` (0x1c) de 0x2e sectores de `MOVIES/MSR.SFD`, recibía un `REQ_DMA_TRANS` de un sector y volvía a empezar.
Espera la interrupción de fin de DMA del GD (ISTNRM bit 14), que nuestra copia no daba. Como el HLE de Flycast
(`core/reios/gdrom_hle.cpp`: `asic_RaiseInterrupt(holly_GDROM_DMA)` en REQ_DMA_TRANS, `asic_CancelInterrupt` en
G1_DMA_END): con la bandera, cada REQ_DMA_TRANS hace una DMA G1 de 32 bytes real al salir de la llamada (lo que ya se
hacía con Windows CE), G1_DMA_END borra el bit 14 y su callback se llama al salir de la llamada (llamado dentro, o desde
la interrupción anidada, sus GET_CMD_STAT recibían "ocupado" para siempre: tormenta de interrupciones). Sin la bandera
no cambia nada para los demás juegos. En Flycast MSR llega al reloj, la zona horaria y "PRESS START BUTTON".
`tools/newloader.py` con `FLAGS=0x80000` → `otros/fix/dc-msr_dc2naomict_v2.bin.gz` (falta subirla a la .60).

**SPF2X: residente viejo.** La imagen de la .250 (2026-11-09) era anterior a la limpieza de RAM (6c95d60) que arregló el
mismo síntoma en SSF2X. `tools/newloader.py VIEJA NUEVA` pone el cargador y residente actuales conservando título,
cabecera y datos (no hace falta el disco). En Flycast: menú principal. **Subida a la .250** (md5 `0725d92c…`; la vieja en
`/boot/spf2x_old.bin.gz.bak`). En la .250 hay más imágenes con cargadores anteriores (md5 de la zona del cargador):
dcop_es, kof02, motw, rcotton_en, sf3ts, soulcal, ysgw (grupo más viejo); buzz_es, ikaruga; ssf2x_en, toystory2_es.
Si alguna se cuelga igual, `newloader.py`.

**Airline Pilots (NAOMI original):** la cabecera del juego (0x429 = 0x01) solo admite mueble de 1 jugador; la BIOS da
CAUTION 51 si SYSTEM ASSIGNMENTS → CABINET TYPE no coincide. Arreglo: ponerlo a 1 PLAYER(S) en el test de la .60. Los
controles para volante y pedales: pendiente.

**TD6 — resuelto en placa (2026-11-19 13:39, el usuario: "llega al menú!").** Con la caja negra en la placa (Pi .251,
`tools/board/pk.py`): tras START el juego lee `FRONTEND/FRONTEND.TEX` entero (DMAREAD de 0x635 sectores, 3,2 MB, hasta
0x8d000000); la lectura acaba bien (estado del residente: COMPLETE consumido, 0x31a800 bytes) pero el juego no pide nada
más: la música del título sigue y el icono de carga queda quieto; sus hilos (tareas por cuadro a 0x8c0ce5a8, que miden
tiempo con el TMU2) siguen vivos. En Flycast la misma imagen sigue (la siguiente lectura es el sector 0x4951e).
Con `read_chunk` = 4 (cada EXEC_SERVER copia 8 KB con las interrupciones cortadas, no 64 KB) puesto en vivo con
`tools/board/pp.py 10.0.0.4 0x8dc05174=4` (dirección de `_read_chunk` en `resident.elf` del mismo cargador), llega al
menú. Igual que SF3 Double Impact. Imagen definitiva: `tools/newloader.py` con `READ_CHUNK=4 PAD=9` (md5
`0adb2a72…`), subida a la .251 con la VMU de la sesión de pruebas (copia de la anterior en
`/boot/td6_vmu_backup_20261119.vmu`).
**Mandos de TD6 (elección del usuario):** palanca = arriba/abajo (cambio de marcha), START + palanca = B/A: nuevo
`DIMM_PAD_WHEELUD` (9; `"pads": "wheelud"` en un perfil, `PAD=9` en newloader). El resto como `DIMM_PAD_WHEEL`.
Ojo al muestrear el PC (`DIMM_PCSAMPLE`): TD6 usa el TMU2 como contador libre (TCOR2 = -1), las muestras no valen.
Ojo con `piapp.py`: sale con 0 aunque acabe en PAUSE (subida a medias); comprobar "done" antes de renombrar.
Para cargar desde la Pi por SSH sin que el envío muera al cerrar la sesión: `/root/load.sh IP IMAGEN` lanzado con
`setsid nohup ... &` (mata timehack, envía, arranca timehack; el vigilante de la VMU lo arranca el propio envío).
`pkill -f timehack.py` dentro de un `sh -c` que también contiene "timehack.py" mata ese mismo shell.

**TD6 (lo anterior):** con mando estándar llega en Flycast al menú principal con los créditos de la VMU: el cuelgue es solo de la
placa. Pendiente: cargarlo con la caja negra (flags 0x20000) y que el usuario pulse START. En Flycast el modo de mandos
del mueble no sirve para probar START: sin pedales los ejes de Flycast quedan a media escala y START + freno cuenta
como X (`tools/flycast` sin mapa de pedales; `tools/flycast/img_setpad.py IMAGEN 2` lo pasa a mando estándar para probar).

**Rush 2049:** el menú tras START (en 1ST_READ, no en 2_DP) responde poco y va a ~5 llamadas de maple por segundo en
Flycast (la demo, ~48): el juego dibuja (muestras de PC en su código de texto y del TA), sin llamadas al GD. Sin
resolver; mirar en placa.

**Vigilante de la VMU:** en la .60 seguía uno de TD6 corriendo bajo Rush (el `stop` solo mata el PID del fichero de
estado). Ahora cada vigilante sale si el fichero de estado ya no lleva su PID. Instalado en la .250 (copia
`dc2naomi_vmu.py.bak_20261119`); falta la .60.

Herramientas de prueba en `tools/flycast/`: `img_mkbin.py` (descomprime e inyecta la .vmu como el netbooter),
`img_setpad.py`, `img_setflag.py`, `img_hdr.py` (tabla de parches), `img_box.py` (caja negra de un volcado de Flycast).

**Confirmado por el usuario (2026-11-25):** MSR v2, Test Drive Le Mans y Wacky Races (los de "otros programas") funcionan en la placa del mueble Crazy Taxi.
