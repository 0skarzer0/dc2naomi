# OutRun 2006 Coast 2 Coast (demo de ArkRetro) compilado para NAOMI

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
