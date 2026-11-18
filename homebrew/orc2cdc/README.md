# OutRun 2006 Coast 2 Coast (demo de ArkRetro) compilado para NAOMI

> **2026-11-18 09:30: cambio de marchas en la palanca del mueble** (`-DNAOMI_PALANCA`, `demo/main.c`): con los mandos
> `wheel` la palanca adelante llega como B y atrás como A, que en ORC2CDC eran freno y acelerador a fondo (A = gas, B / X =
> freno); ahora suben y bajan de marcha en el cambio manual, y gas y freno salen solo de los pedales. md5 `.gz`
> `a0034116d6077beb42b8ebd780a24e78`.
>
> **2026-11-18 08:15: vuelve el taxi de Crazy Taxi** (`COCHE07.DAT`, 0,2 MB, y su compra en el Salón; el usuario lo
> quiso; OutRunners no cabe con las 8 canciones: 14 MB, y la tarjeta de All I Want sigue fuera). Imagen 504,0 MB, md5
> `.gz` `a17a7cab16f8c08c5e8d4a7c691d82fd`.
>
> **Versión de la madrugada del 2026-11-18 (`h-orc2c3_dc2naomict`, 504 MB):** ORC2CDC **`a689a9a`** ("FINAL7") con
> `orc2cdc-a689a9a-naomi.patch` y compilada con `KOS_CFLAGS="$KOS_CFLAGS -DFPS_OBJETIVO=30 -DCPU_MS_CORTA=29.0f
> -DCPU_MS_ALARGA=25.0f -DGD_TROZO=4 -DNAOMI_PALANCA"`; perfil `orc3` con `DIMM_DMA`. Por qué, con las medidas en la placa:
> [MEDIDAS.md](MEDIDAS.md). En resumen: **30 fps fijos** (la CPU de la NAOMI no llega a los 45 del port y el juego
> acortaba la distancia de dibujo hasta 600 m: el popping), **lecturas del disco troceadas y por DMA** (los tirones
> de 60-120 ms venían de leer la etapa siguiente y la música con el residente parado copiando), y la **música a
> 22 kHz** entera (`MUSn.A22`, `comun/musica.c`): 8 canciones largas propias (MUS0-MUS7: Splash Wave, Magical Sound
> Shower, Passing Breeze, Risky Ride, Shiny World, Night Flight, Life Was a Bore, Radiation) y las otras 21 suenan como
> una de esas 8 (`~/orc3data3.py`: copias que `tools/gdi.py` guarda una vez); las 35 cortas también a 22 kHz.
> El parche añade además `naomi_med` (medidas cada 30 cuadros) para `med.py`, y con `-DNAOMI_PRF` el tiempo de cada
> parte del cuadro. `-ffast-math` y `-O3` probados y descartados.

> **Versión actual (2026-11-18, `h-orc2c3_dc2naomict`, 491,6 MB, sin comprimir nada):** elección del usuario tras la
> primera prueba en placa (faltaban los sonidos de carrera: `VOCES.DAT` no cabía en los 16 MB, "Out of memory" de
> 212 KB). KallistiOS con `-D__KOS_GCC_32MB__` (el gcc de Ubuntu no lo define y `arch.h` fijaba la RAM en 16 MB):
> ahora usa la RAM hasta el residente (`0x8dc00000`) y carga `VOCES.DAT`. Fuera del disco: los vídeos (`MVATTR.VQV`,
> `MVTS.VQV`), OutRunners (`OUTRUNNERS.BIN`, `CORE.ASSETS`, `TILES4.Z`, `SPRITES.Z`, `PCM.BIN`, `AICA_*.BIN`) y el taxi
> de Crazy Taxi (`COCHE07.DAT`); el menú los deja bloqueados y sin venta en el Salón (`-DSIN_OR_TAXI` en
> `comun/menu.c`, y sin la tarjeta de All I Want). Música: **una sola canción larga**, `MUS0` (Splash Wave): las demás
> largas son copias suyas (`tools/gdi.py` de ORC2CDC guarda una vez los ficheros repetidos); las 35 cortas intactas.
> Ya no hay ZCK1 ni `MUSn.A22`: el parche de ORC2CDC actual solo toca `comun/menu.c` y `demo/Makefile` (`zck.py` y
> `adp22.c` quedan para la versión anterior, descrita abajo). Pasos: los mismos, con `~/orc3data2.py` en vez del 3.
> En placa: arranca, carga las voces, guarda la licencia; carrera sin probar todavía.

La demo [ORC2CDC](https://github.com/ArkRetro/ORC2CDC) de **ArkRetro** (KallistiOS, para Dreamcast) compilada desde sus
fuentes para la NAOMI 2 del mueble Crazy Taxi, y su disco adelgazado para que quepa en la NetDIMM de 512 MB (el de
Dreamcast, "Turbo v3", ocupa 984 MB). Probado: compila y la imagen sale en **500,6 MB**; **en placa, sin probar**.
Aquí no hay nada del juego: los datos salen de tu disco (`tools/regenera_datos.sh` del proyecto original los hace
desde tu ISO del juego).

| Fichero | Qué es |
|---|---|
| `kos-d81aa3f-naomi_host.patch` | KallistiOS `d81aa3f` (la que usa ORC2CDC) con `NAOMI_HOST`: el parche de `homebrew/mk64` llevado a esta versión (cima de RAM bajo el residente, maple por el residente, bus G1, vídeo, FIFO G2, DMA del AICA, bloque `LIVE`) |
| `orc2cdc-3539fa6-naomi.patch` | ORC2CDC `3539fa6`: `comun/gd.c` lee ficheros ZCK1 (con `-DGD_ZCK`), `comun/musica.c` toca `MUSn.A22` a 22050 Hz, `demo/Makefile` enlaza el inflate de zlib |
| `zck.py` | un fichero del disco a ZCK1: trozos de 64 KB comprimidos cada uno con zlib (nivel 9), para leer cualquier sector sin descomprimir el fichero entero |
| `adp22.c` | una pista `MUSn.ADP` (ADPCM de Yamaha estéreo, 44,1 kHz) a `MUSn.A22` (la mitad de muestras, se toca a 22050 Hz con el mismo tono) |

## Cómo se hizo (2026-11-17)

1. Compilador: `gcc-sh-elf` 13 de Ubuntu (`tools/ubuntu-toolchain.sh` de dc2naomi: la libc sin los objetos que
   chocan con KallistiOS en `/opt/toolchains/dc/compat/lib`). KallistiOS `d81aa3f` + `kos-d81aa3f-naomi_host.patch`,
   `environ.sh` con `-DNAOMI_HOST -include /opt/toolchains/dc/compat/kos_gcc13.h`. SH4ZAM (`7e57d5c`) a mano (el gcc de
   Ubuntu no trae C++ para su CMake): los 6 `.c` de `source/` con `kos-cc` en `libsh4zam.a`.
2. ORC2CDC `3539fa6` + `orc2cdc-3539fa6-naomi.patch`, zlib 1.3.1 (`madler/zlib`) en `../../zlib-src` respecto a
   `demo/`; `make` en `demo/`; `sh-elf-objcopy -R .stack -O binary demo.elf 1ST_READ.BIN`.
3. Datos (de tu disco de Dreamcast de la demo, todos sus ficheros salvo `1ST_READ.BIN` y el relleno `0.0`):
   - Música (reparto del usuario): `MUS0`–`MUS3` (Splash Wave, Magical Sound Shower, Passing Breeze, Risky Ride de
     OutRun 2) y las 35 pistas cortas (menú, avances, meta, récord) siguen a 44,1 kHz; `MUS4`–`MUS27` y `MUS67` (All
     I Want) a 22 kHz con `adp22` (`MUSn.A22`, sin el `.ADP`). Comprobado: SNR 22 dB frente al original filtrado y
     diezmado, mismo nivel (lo que da volver a codificar ADPCM de 4 bits).
   - Todo lo demás de 64 KB o más (salvo `CORE.ASSETS`, que se abre con `fopen` de KallistiOS) a ZCK1 con `zck.py`
     si gana un 10 % o más: 231 ficheros (`SEGS.PAK` 255 MB, `UNIONES*.PAK`, etapas, menús, vídeos `.VQV`...).
   - 498,5 MB de datos en total.
4. GDI con `tools/gdi.py` de ORC2CDC (`gdi.escribe(salida, 1ST_READ.BIN, IP.BIN, datos)`, el IP.BIN del disco
   original), y la imagen de NAOMI con dc2naomi: `tools/withfiles.py - --perfil orc3 --cab ct --batch disc.gdi`
   (perfil `orc3` de `tools/games.py`: sin parches, porque `NAOMI_HOST` ya los hace en el código).

## Lo que cambia en el juego

- **Lectura** (`comun/gd.c`): `gd_busca` mira la primera vez el primer sector de cada fichero; si es `ZCK1` devuelve
  un LBA virtual (bit 30, índice del fichero en los bits 18-29) y el tamaño original, y `lee()` descomprime los sectores
  pedidos con una caché de 4 trozos de 64 KB. Nadie más lo nota: tampoco los paquetes de etapas y uniones, que leen
  ventanas de `SEGS.PAK` / `UNIONES.PAK`. Coste: un `uncompress` de zlib por cada 64 KB nuevos (y se leen del disco
  unas 2,5 veces menos sectores). **Hay que medir en la placa que la carga de cada etapa (que se lee conduciendo, con
  ~12 s de margen) no se alarga demasiado.**
- **Música** (`comun/musica.c`): busca `MUSn.A22` (22050 Hz) antes que `MUSn.ADP` (44100 Hz).
- **Memoria:** con `NAOMI_HOST` KallistiOS ve la RAM hasta `0x8dc00000` (28 MB) en vez de 16 MB; el juego no la
  aprovecha todavía (sus huecos siguen siendo los de la Dreamcast).

## Agradecimientos

**ArkRetro** por la demo y por publicar sus fuentes (su repositorio no lleva licencia: aquí solo hay un parche contra
él, nada de su código ni de sus datos); **KallistiOS** y sus autores; **SH4ZAM** (Falco Girgis, MIT); **zlib**
(Jean-loup Gailly y Mark Adler); el codificador ADPCM de Yamaha de `adp22.c` es el de `tools/c/musica.c` de ORC2CDC
(a su vez como `wav2adpcm` de KallistiOS).
