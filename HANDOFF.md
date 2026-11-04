# HANDOFF — dc2naomi (juegos de Dreamcast en NAOMI)

Documento de traspaso entre sesiones (personas o IAs). **Actualízalo en cada sesión.**

## Objetivo

Arrancar juegos de **Dreamcast** en una **NAOMI / NAOMI 2** por netboot (NetDIMM), sustituyendo la BIOS de
Dreamcast por un programa residente. Primer intento: **Daytona USA 2001** (versión US).
Si funciona, el mismo cargador serviría para recopilatorios (Yu Suzuki Game Works, Namco Museum, Midway…)
y ports (Wipeout, Mario Kart 64).

## Estado (2026-11-04)

- **Experimental. Daytona 2001 se queda en pantalla negra** en la placa real. Parado de momento.
- Pendiente: averiguar dónde se queda (log del residente en `RES_LOG`, `dbg_draw`), o probar con un
  juego más sencillo como banco de pruebas.

## Cómo funciona

1. **`loader/`** (KallistiOS, `KOS_SUBARCH=naomi`): es lo que arranca la BIOS de NAOMI. Inicializa el
   hardware (MIE + JVS), copia el residente a los 16 MB altos (`0x8dc00000`) junto con una imagen de la
   flash de Dreamcast, para KOS y salta a `boot()` del residente.
2. **`resident/`** (C freestanding, sin FPU ni divisiones): hace de BIOS de Dreamcast mientras corre el juego.
   - Syscalls: GD-ROM (lecturas servidas desde la NetDIMM por el puerto de cartucho `0xa05f7000`),
     sistema, fuentes, flash, misc. Comportamiento según el HLE de Flycast (reios).
   - **Hook de maple**: responde a las peticiones de mando del juego con las entradas JVS de la NAOMI
     (volante, pedales…).
   - Carga `IP.BIN` y `1ST_READ.BIN` desde la NetDIMM y arranca el juego.
   - Memoria: `RES_BASE 0x8dc00000`, pila `0x8dcffff0`, flash `0x8dd00000` (128 KB),
     buffers maple `0xadd40000` (sin caché), log `0x8dd80000`.
3. **`tools/build_image.py FILES BUILD loader.bin OUT.bin`**: reconstruye la ISO a partir de los ficheros
   del disco (LBA 45000 = FAD 45150), crea una flash de Dreamcast (región US, inglés), añade el archivo
   `YDCG IMG1` (cabecera `dimm_header` en `resident.h`) detrás del loader y la tabla de parches.

## Parches específicos de Daytona 2001 (`tools/build_image.py`)

| Dirección | Qué hace |
|---|---|
| `0x8c008382` | IP.BIN: tipo de cable 0 (VGA) |
| `0x8c1d21ee`, `0x8c1f6866` | `syCblCheck` (2 copias) → `rts` devolviendo VGA |
| `0x8c1e966c` | llamada "dirección a física" del driver maple → hook del residente |
| `0x8c1f3764/78/84` | registros G1 (`0xa05f7484`, `0xa05f74a0`, `0xa05f74b4`) redirigidos a RAM `0xac00fe..` |

Para otro juego habrá que localizar sus equivalentes (cable VGA, driver maple, registros G1/GD-ROM).

## Compilar

```sh
source /opt/toolchains/dc/kos/environ.sh
./build.sh      # residente + loader + imagen (rutas del build.sh a ajustar)
```

Necesita los ficheros extraídos del disco del juego en `../files` (**nunca se suben al repositorio**).

## Notas de hardware (aprendidas en otros ports)

- La VRAM real de NAOMI **no admite escrituras de byte** (Flycast sí): usar escrituras de 16/32 bits.
- La DMA del PVR se cuelga en NAOMI.
- En Flycast sin BIOS el driver MIE de KOS no se activa (ver parche en `mame4all-naomi/naomi/flycast`).

## Siguientes pasos

1. Volcar por pantalla el log del residente (`RES_LOG`) para ver la última syscall antes del cuelgue.
2. Comprobar en Flycast con BIOS NAOMI real (no HLE) si se reproduce.
3. Probar con un juego más simple (Yu Suzuki Game Works sería el objetivo ideal).
