# dc2naomi — juegos de Dreamcast en Sega NAOMI

Cargador **experimental** para arrancar juegos de **Dreamcast** en una placa **Sega NAOMI / NAOMI 2**
por **netboot (NetDIMM)**, sin modificar el hardware.

La NAOMI es casi una Dreamcast (mismo SH-4, PowerVR2 y AICA, pero con más memoria). Lo que le falta
para ejecutar un juego de Dreamcast es la **BIOS de Dreamcast** y el **lector GD-ROM**. Este proyecto
los sustituye por software:

- **`loader/`**: programa para NAOMI (KallistiOS) que arranca desde la NetDIMM, prepara el hardware y
  coloca el residente en la memoria alta.
- **`resident/`**: hace de BIOS de Dreamcast mientras corre el juego. Atiende sus llamadas al GD-ROM
  leyendo el disco desde la NetDIMM y traduce los mandos de Dreamcast a los controles JVS de la recreativa.
- **`tools/build_image.py`**: monta la imagen `.bin` para netboot con el loader, el disco del juego
  (directamente desde un `.gdi`, con sus sectores originales), una flash de Dreamcast y los parches propios
  de cada juego (`tools/games.py`), verificados contra el disco al construir.

## Estado

| Juego | Resultado |
|---|---|
| Daytona USA 2001 (US) | ❌ Pantalla negra en placa real |
| Yu Suzuki Game Works Vol. 1 (JP) | 🧪 Imagen preparada (201 MB, disco con sus LBA originales); pendiente de probar |

**Es un trabajo en curso.** Los detalles técnicos, las direcciones y los siguientes pasos están en
[HANDOFF.md](HANDOFF.md).

Si funciona, abriría la puerta a recopilatorios como **Yu Suzuki Game Works Vol. 1** (Hang-On, OutRun,
Power Drift), **Namco Museum** (Pole Position) o los **Midway Greatest Arcade Hits**, y a ports
de Dreamcast como Wipeout o Mario Kart 64.

## Compilar

Requiere [KallistiOS](https://github.com/KallistiOS/KallistiOS) con `KOS_SUBARCH=naomi`.

```sh
source /opt/toolchains/dc/kos/environ.sh
chdman extractcd -i juego.chd -o juego/disc.gdi
./build.sh ysgw juego/disc.gdi      # -> build/ysgw.bin
```

Necesitas **tu propio volcado** del juego.

## Aviso legal

Este repositorio **no contiene** juegos, imágenes de disco, BIOS ni desensamblados. Solo código propio.
Dreamcast, NAOMI y los juegos citados son marcas de sus propietarios.

Parte del proyecto [naomi-wheel-games](https://github.com/0skarzer0/naomi-wheel-games).
