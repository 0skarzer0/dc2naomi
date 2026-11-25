# Historial: Sega Rally 2 y Windows CE (2026-11-11)

> Historial: diario de sesiones copiado tal cual del antiguo `HANDOFF.md` (2026-11-25). Puede estar superado por lo escrito después; lo vigente está en [HANDOFF.md](../../HANDOFF.md).

> **Ojo con las IP:** en este diario la Pi del mueble Crazy Taxi aparece como **.60** (y la del mueble estándar a veces como **.59**). Desde el 2026-11-19 son **192.168.68.251** (Crazy Taxi) y **192.168.68.250** (estándar). El texto se deja como se escribió.

## Sega Rally 2 (USA) — Windows CE. ✅ FUNCIONA EN PLACA (2026-11-11 00:31, mueble Crazy Taxi)
Perfil `sr2` (como `mw2`). Probado solo en Flycast (NAOMI, `FC_SYSM_RAM=1`); en placa no se ha enviado.
Disco: pista 3 + 17 pistas CDDA (4-20, la música: no sonaría) + pista 21. Programa: `RALLY2.EXE`.

**Lo que ya está resuelto (en el loader y el builder):**
1. **`0WINCEOS.BIN` es un contenedor:** cabecera de 0x800 bytes (`D61A`, 1 sección: carga `0x0c010000`, desplazamiento
   `0x800`, tamaño, entrada). La BIOS carga la sección, no el fichero. `GdiDisc.boot()` lo detecta y apunta `boot_fad`
   al 2.º sector; además pone el flag nuevo `DIMM_WINCE` (0x40000) y el residente copia la cabecera en `0x8ce01000`,
   como hace el HLE de Flycast (`core/reios/reios.cpp`). Antes: excepción de instrucción ilegal en `0xac010010`.
2. **CE llama a las syscalls del GD-ROM con la MMU encendida y direcciones virtuales** (pila del hilo en P0, p. ej.
   `0x0205fb5c`). `in_ram()` las rechazaba y el driver nunca veía resultados. Ahora, solo dentro de `gd_syscall` y con
   `MMUCR.AT`, acepta P0/P3 **salvo por debajo de 64 KB**: `REQ_CMD INIT` llega con `r5 = 0` y leer la dirección 0
   mataba el hilo del driver (ese fue el falso "depende de la compilación": la traza `GDTRACE` también leía `*r5`).
3. **El driver de CE (`WSEGACD.DLL`, dentro de la imagen ROM; WDM) usa lecturas en flujo** (`MULTI_PIOREAD` 0x27,
   `MULTI_DMAREAD` 0x26) con `SET_PIO_CALLBACK` / `REQ_PIO_TRANS` y un hilo de interrupción (SYSINTR 21 = ISTNRM bit 14,
   fin de DMA G1) que pide cada trozo de DMA. Con MMU encendida: `REQ_PIO_TRANS` copia en el momento y el callback se
   llama al salir de la syscall (en bucle, sin anidar); tras `REQ_DMA_TRANS` el residente hace una DMA G1 real de 32 bytes
   (NetDIMM → `RES_SCRATCH+0x800`) para que salte la interrupción de fin de DMA, **fuera** de la syscall (si salta dentro,
   el hilo de CE entra anidado y se ignora).
   Mapa de interrupciones del núcleo de CE (`0x8c02e020`...): ISTNRM bit 14 → SYSINTR 21; ISTEXT bit 0 (unidad GD-ROM) → 20.
4. **`REQ_PIO_TRANS` y el callback PIO, como el HLE de Flycast** (`core/reios/gdrom_hle.cpp`): `REQ_PIO_TRANS` solo
   anota la petición; la copia la hace el siguiente `EXEC_SERVER`, y **al terminar esa llamada** el residente llama al
   callback (`SET_PIO_CALLBACK`), que pide el trozo siguiente. Mientras hay un `REQ_PIO_TRANS` pendiente,
   `GET_CMD_STAT` devuelve BUSY (solo con MMU encendida). **Error que costó horas:** hacer la copia y llamar al
   callback dentro del propio `REQ_PIO_TRANS`: el driver avanza su lista de búferes *después* de que la llamada
   vuelve, así que el callback anidado pedía otra vez el mismo trozo y los ficheros salían revueltos. Síntoma:
   CE se quedaba en el logo; el hilo que cargaba `CEMM.DLL` moría en `DoImports` del núcleo (`0x8c02094c`) leyendo un
   puntero basura (tabla de imports con datos de otra parte del fichero) y el despachador de excepciones del núcleo
   se quedaba dando vueltas (`NKLookupFunctionEntry` `0x8c0268f4` con el mismo PC) acaparando la CPU.
5. **No hizo falta parchear `WSEGACD.DLL`** (la espera de la interrupción de la unidad, ISTEXT bit 0): con lo de
   arriba el driver funciona sondeando, igual que en el HLE de Flycast, que tampoco levanta esa interrupción.
6. **Mandos (maple) en Windows CE:** `MAPLE.DLL` (en la ROM, `0x8c098000` = fichero `0x10001000`) escribe SB_MDSTAR
   una sola vez (su lista, un búfer común) y deja que el hardware lance la DMA en cada vblank (SB_MDTSEL = 1,
   MSYS `0xc3501000`, rearme con SB_MSHTCL). Corre en modo usuario con MMU: no puede llamar al residente. El gancho va
   en **el manejador de interrupciones del núcleo**: la rama de ISTNRM bits 12/13 (SYSINTR 18) en `0x8c02e114`
   salta a `ce_maple_isr` (head.S; parche `CEMAPLE` = `PATCH_CEMAPLE` sobre el literal `0x8c02e194` + `jmp @r3`),
   que llama a `ce_maple_poll()`: contesta la lista de CE con `maple_hook()` y apunta SB_MDSTAR a nuestro sondeo del
   MIE para el vblank siguiente. CE ve un mando en el puerto A (GETCOND) y nada en B-D.
   Tabla de interrupciones del núcleo: `0x8c02e020` (ISTERR, nivel 2), `0x8c02e0ac` (ISTNRM & IML4NRM: bits 0-11 →
   SYSINTR 16, 12-13 → 18 maple, 14 → 21 fin DMA G1, 15 → 24), `0x8c02e13c` (ISTEXT & IML6EXT: bit 0 → 20, bit 1 → 23).
7. **Resultado en Flycast (NAOMI): arranca.** Logo de CE → título "PRESS START BUTTON" → demo con coches → ranking.
   Probado después en Flycast con mandos: START, MODE SELECT, SELECT CAR, NAME ENTRY y carrera (el coche apenas
   corría en la prueba: revisar pedales en placa). Con `vmu=True` el juego carga de la tarjeta ("Load complete").
8. **Imagen para la placa (2026-11-10, 23:15):** `sega_rally2_dc2naomi.bin.gz` (md5 `9c44f9b76b720d5747fc7cd6580bedee`,
   268 MB; sin comprimir 414 MB, md5 `361b65e50e40473acfa41ffcb18d84bb`; flags `0x48004` = NO_UBC + VMU + WINCE,
   `pad_map` 4 `wheel`) y `sega_rally2_dc2naomi.vmu` con la partida «US - ALL UNLOCKED» de dreamcast-saves
   (`r/segarally/SGRALLY2.VMI`, fichero `SGRALLY2I0VD`, 61 bloques; **sin probar si el juego la acepta**). Subidas a
   `/boot/roms` de la Pi del Crazy Taxi (192.168.68.60), fila añadida a `/boot/config/romsinfo.csv` e importada, y
   enviada a la NetDIMM 10.0.0.4 con `/root/sendsr2.sh`. **Pendiente: resultado en la placa real** (lo dirá el
   usuario). Copia también en el PC: `C:\Users\Usuario\Documents\dc2naomi\`.

9. **PLACA REAL (2026-11-10, 23:16-23:50): se queda colgado en la pantalla "SEGA / Powered by Windows CE"**
   (dos intentos del usuario, mueble Crazy Taxi). En Flycast esa misma imagen llega al título y a la carrera.
   - El peek por la NetDIMM (`/root/pk.py`) **no responde** (antes de mandar el juego sí): nadie llama a
     `dimm_service()`, o sea, ni syscalls GD ni el gancho de maple se están ejecutando.
   - Añadido **`ce_tick_isr`/`ce_tick()`** (`PATCH_CETICK` = `CETICK` en games.py): el manejador del tick de CE
     (`0x8c02e228`, TMU0 cada 25 ms) pasa por el residente y atiende la NetDIMM, para poder leer la placa con CE en
     marcha. Parche: literal `0x8c02e24c` (`0xffd80000`) → `ce_tick_isr`, y `0x8c02e22c` → `jmp @r1`. Funciona en
     Flycast (1538 ticks en 60 s). **En la placa el peek sigue sin responder → el tick de CE tampoco corre: el
     cuelgue es muy temprano** (arranque del núcleo, o antes), no en la carga del juego.
   - Descartado mirando el código: el núcleo no escribe registros BSC ni SCIF; el RTC (`0xa0710000`) lo lee una vez.
   - **En curso:** imagen `sr2diag_dc2naomi.bin.gz` (perfil `sr2_diag` = `sr2` + `DIMM_DIAG` 0x8; md5 del .gz
     `6c4100761e976d45b5b492bcfb5e76af`) enviada al mueble: dibuja filas de bits arriba a la izquierda desde las
     syscalls, el gancho de maple y el tick (fila 0 llamadas a diag/4, 1 nº de llamadas GD, 2 última llamada
     `r7<<8|r4`, 3 sondeos maple, 4 último FAD, 5 otras syscalls, 16 ticks de CE, 17 llamadas al gancho, 18 MMUCR).
     Pedida foto al usuario. La secuencia de llamadas GD es determinista: con el nº de la fila 1 y la traza de
     Flycast (`EXTRA=-DGDTRACE`) se sabe en qué paso se paró.
   - **Foto 1 del usuario (23:48), filas leídas (bit más alto a la izquierda):** fila 1 (llamadas GD) = 0, fila 2
     (última llamada) = `0x0200`, fila 3 (maple) = 0, fila 4 (FAD) ≈ `0xA800`, fila 5 = 0, fila 6 = 0, fila 8 (FB_R_CTRL)
     = `0xD`, fila 14 (ISTNRM) = `0x38`, fila 15 (ISTEXT) = 0, **fila 16 (ticks de CE) = 3**, fila 17 (gancho maple) = 0,
     fila 18 (MMUCR) con el bit 0 a 1. **Conclusión: CE arranca en la placa (MMU encendida, 3 ticks de 25 ms) y se
     congela del todo (ni ticks) justo donde en Flycast llega la primera syscall GD de CE** (en Flycast las llamadas
     nº 7 a 26 — `INIT` r7=3, `REQ_CMD 0x18`, `EXEC_SERVER`, `GET_CMD_STAT`, TOC `0x13`, primeras lecturas — caen todas en
     el tick 3; traza: `EXTRA=-DGDTRACE` con `ce_ticks` como último dato del `dlog`). Los contadores a 0 con "última
     llamada 0x200" indican además que **las variables del residente vuelven a valores viejos**: CE reinicia la caché
     (CCR) y se pierde lo que el residente tenía solo en caché desde el `ocbwb` de `boot()`.
   - **Diagnóstico 2 (en curso, md5 del .gz `9a2a584c1a3c624808cbf076bdb49cb4`):** `stage(n, v)` dibuja al momento la
     fila 19 = paso y la 20 = dato: en `gd_syscall` 1 = entrada (v = `r7<<8|r4`), 2 = tras `dimm_service` (v = r5),
     3 = tras `dbg_draw` (v = nº de llamada), 4 = tras `patch_poll` (v = r6), 5 = tras el cuerpo (v = r0), 6 = salida;
     `0x10` = `sys_syscall`, `0x20` = `flash_syscall`, `0x30` = `misc_syscall` (v = `r7<<8|r4`). Filas 21/22 = SPC y SSR
     del último tick. Con MMU encendida `diag_draw` dibuja en todas las llamadas (antes 1 de cada 4).
   - **Fotos 2-5 (00:00, diagnóstico 2):** fila 1 (llamadas GD) = `0x13` (19), fila 2 (última) = `0x0105`
     (`GET_CMD_STAT` de la petición 5), fila 4 (FAD) = `0xB075`, fila 16 (ticks) = 3, fila 17 (gancho maple) = 0,
     **fila 19 (paso) = 6 y fila 20 = `0x13`: la llamada 19 terminó y volvió a CE**; fila 21 (SPC del último tick) ≈
     `0x000115xx` (código de usuario), fila 22 (SSR) = `0x00008001`. Es decir: en la placa CE hace `INIT`, las dos TOC
     y **la primera lectura de datos (`DMAREAD` FAD `0xb06e`, 8 sectores) completa y correcta**, y se congela antes
     del 4.º tick (en Flycast la llamada 20 llega ya en el tick 4). No hay reinicio (la BIOS recargaría el juego).
   - **Hipótesis actual (arreglo en el diagnóstico 3, md5 del .gz `1f569f2d97d5b599a69dfc29c9d2114e`, enviado a las
     00:20): los ganchos de interrupción usaban la pila del hilo interrumpido.** Los manejadores del núcleo de CE son
     rutinas hoja que solo usan r0-r3; `ce_tick_isr`/`ce_maple_isr` apilaban en r15 y llamaban a C. Si r15 es la
     pila de usuario del hilo interrumpido y su página no está en la TLB, con SR.BL = 1 un fallo de TLB **cuelga la
     CPU real** (64 entradas de TLB; Flycast casi nunca falla). Los ticks 1-3 caen con el núcleo ocupado; el 4.º es
     el primero con el sistema en reposo. Ahora los dos ganchos pasan a **pila propia** (`0x8dcf8000` maple,
     `0x8dcf4000` tick) y restauran r15 al salir. Si era esto, el cuelgue de la primera imagen (sin gancho de tick)
     sería el mismo fallo en el gancho de maple.
     Regla para ganchos en ISR de CE: solo direcciones P1/P2, pila propia, nada de coma flotante.
   - **✅ CONFIRMADO (usuario, 00:31): con la pila propia en los ganchos "funciona perfectamente"** en la placa
     (diagnóstico 3). Era eso: fallo de TLB con SR.BL = 1 al apilar en la pila del hilo interrumpido.
     Falta la música de las carreras (pistas CDDA 4-20, no se reproducen).
   - **Imagen limpia (variable, sin el parche de 30 FPS; sustituida el 2026-11-11, ver más abajo):** `sega_rally2_dc2naomi.bin.gz` md5 `b61bf3b07d478e1f1ea7f2acfe77f37e` (sin comprimir
     `8aed51a83f3f21dc7335a20164160f99`), perfil `sr2` (flags `0x48004`, mandos `wheel`), en `/boot/roms` de la Pi .60
     y en el PC. Lleva también el gancho del tick (peek por red con CE en marcha). `.vmu` con «US - ALL UNLOCKED».
   - El vigilante viejo de CT2 no tocó su tarjeta (el usuario tiene los ficheros renombrados con prefijo `dc-`:
     `dc-ct2h8_dc2naomi.vmu`..., fecha sin cambios).
   - **Ideas pendientes del usuario:** (1) CDDA a baja calidad (quedan ~98 MB libres de 512: ADPCM 4 bits de la AICA
     a 32 kHz estéreo ≈ 91 MB, o 22 kHz ≈ 62 MB; habría que robar 2 canales de la AICA al driver de sonido de CE y
     alimentarlos desde el gancho del tick; órdenes CD_PLAY/STOP/REQ_STAT/subcódigo en `gd_command`); (2) el juego
     tiene trucos en la pantalla de título: 30 FPS = Arriba, A, Abajo, Abajo, Izq, Der, B, B, Arriba; 60 FPS (con menos
     detalle) = lo mismo acabando en Abajo. Quiere los 30 FPS por defecto: buscar la tabla de la secuencia en
     `RALLY2.EXE` y dejar el modo activado de serie, o que el residente teclee la secuencia solo.
   - **✅ 30 FPS de serie (2026-11-11), probado en placa: el usuario confirma el 2026-11-13 que funciona perfecto.** La tabla no está en `RALLY2.EXE` sino en
     **`TITLE.DLL`** (pantalla de título). Cómo se encontró: el `.gdi` original en Flycast modo Dreamcast, el truco
     tecleado con `xdotool` (`scr/run_seq.sh`: A = tecla `x`, B = `c`, cruceta = flechas, 0,15 s por tecla, a los
     24 s) y volcados de RAM comparados (30 FPS / 60 FPS / secuencia mala, 2 pasadas de cada). Sale la tabla en
     `.data` de TITLE.DLL (ImageBase 0x10000000): botones del juego Arriba 0x200, Abajo 0x400, Izq 0x800, Der
     0x1000, A 1, B 2; cuatro códigos, cada uno 9 (o 14) palabras + contador de progreso: 0x1000e0e8 (14 botones,
     contador 0x1000e120), 0x1000e124, 0x1000e14c, 0x1000e174 (60 FPS) y **0x1000e19c (30 FPS)**. La función que
     los comprueba cada fotograma está en 0x10001094. Al completar: 60 FPS → `**(*0x1000ebf0) |= 1`; **30 FPS →
     `**(*0x1000ebf0) |= 0x80000000`** (palabra de opciones del juego; en modo DC queda en la RAM física 0xd8ace0)
     y suena el aviso (método 8 del objeto de `*0x1000e4bc`, r5 = 3, r6 = 2).
     **Parche:** en TITLE.DLL offset de fichero 0x63C (VA 0x1000123c, 18 bytes), la comprobación del cuarto código
     se cambia por `mov.l lit,r1; mov.l @r1,r1; mov.l lit(0x80000000),r3; mov.l @r1,r5; mov.l @r5,r2; or r3,r2;
     mov.l r2,@r5; bra 0x10001280; nop` (usa los literales que ya había: sin tocar relocalizaciones): el bit se pone
     en cada fotograma del título, sin sonido. Los otros trucos siguen funcionando (el de 60 FPS también).
     Como CE carga la DLL más tarde en memoria virtual, los parches de RAM del residente no llegan: opción nueva del
     builder **`disc_patches = [(fichero, offset, bytes viejos, bytes nuevos)]`** (`build_image.py`, cambia los
     sectores del disco dentro de la imagen; comprueba los bytes viejos). Perfil `sr2` (y `sr2_diag`).
     Comprobado en Flycast: modo DC con el disco parcheado → palabra = 0x80000000 sin tocar nada; imagen NAOMI →
     arranca, título y demo normales.
     **Imagen nueva (mismo nombre):** `sega_rally2_dc2naomi.bin.gz` md5 `2e2b65554234b059ddb50d8e61f736e9` (sin
     comprimir `135fbf4cc009f343ad8ec418b44b9792`; solo cambian esos bytes, en el offset 432170556 de la imagen).
     Hecha en el PC con **`tools/patch_gz.py IN OUT OFFSET VIEJOS NUEVOS`** (parchea un `.bin.gz` sin cargarlo en
     RAM, vale en la Pi) a partir de la limpia. Está en la carpeta del PC `dc2naomi/sr2_30fps/` junto con el `.vmu`.
     **Subida a la Pi .60** (`/boot/roms`, md5 comprobado allí; sustituye a la anterior, el `.vmu` no se ha tocado y
     el CSV no cambia). Probada en placa el 2026-11-13: perfecta.
   - Descartado: no hay instrucción `sleep` en el núcleo (no es STBCR/standby); las esperas del FIFO G2 no se
     atascan en placa (tabla de variantes).
   - Sospechas por orden: (a) algo del arranque del núcleo de CE que la NAOMI real no tolera; (b) la DMA G1 real del
     "kick" (`cart_dma` 32 bytes; las lecturas por DMA G1 de la NetDIMM nunca funcionaron en placa, ver tabla de
     flags) — alternativa ya pensada: que `ce_maple_isr` devuelva SYSINTR 21 en vez de 18 cuando haya un kick
     pendiente, sin enmascarar los bits 12/13 (la interrupción de maple vuelve a saltar enseguida); (c) la primera
     DMA de maple con la lista de CE va al MIE real antes de que el gancho la cambie.
   - Ojo en la Pi: quedó un vigilante viejo `dc2naomi_vmu.py watch ... ct2h8_dc2naomi.vmu` corriendo a la vez que el
     de SR2 (pid 8363); comprobar que el `.vmu` de CT2 no se haya sobrescrito (copia buena: `/root/vmu/*.orig`/`.bak`).

**Cómo se encontró (herramientas de depuración añadidas al Flycast local, no al repo):** variables de entorno
`FC_INTPC=N` (PC, registros Holly y TMU en 1 de cada N interrupciones), `FC_GDLOG=1|2` (peticiones y todas las
syscalls GD del HLE en modo Dreamcast: **correr el .gdi original en Flycast modo Dreamcast da la secuencia de
referencia para comparar**), `FC_APILOG` (llamadas a la API de CE: son excepciones de dirección en `0xffffxxxx`;
comparar por hilo, el hilo se distingue por los bits altos de r15), `FC_TLBLOG`, `FC_EXCLOG`, `FC_REGS` (registros y
direcciones de retorno de la pila en un rango de PC), `FC_G1LOG`, `FC_TMULOG`, `FC_PCTRACE`. Ojo: leer TCNT0 desde el
emulador tiene efectos (recarga el contador). Símbolos del núcleo: los `.map` de wince-dc son de otra compilación
(desplazados ~0x10020-0x10f3c según la zona); sirven de orientación.
Módulos de la ROM de SR2: nk, coredll, device, gwes, filesys, sysstart, platutil, wdevice, maple, wdmlib, wdmoem,
wsegacd (`0x8c093000`, virtual `0x01df1000`), ddraw, d3dim, ddhal, sndcore, dinputx, ole32, cemm...
**Regresión:** CT2 (`ct2h8`) con el loader nuevo llega igual a la pantalla de la VMU en Flycast (los cambios de CE
solo actúan con la MMU encendida).
