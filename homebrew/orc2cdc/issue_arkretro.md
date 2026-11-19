Hola: he compilado ORC2CDC (a689a9a, "FINAL7") desde sus fuentes para la NAOMI 2 de un mueble de Crazy Taxi (misma SH-4 a 200 MHz y misma PowerVR CLX2 que la Dreamcast, pero 32 MB de RAM y 16 MB de VRAM), y al medirla en la placa han salido cosas que creo que te sirven para la Dreamcast. Todo está en un parche aparte (tu repositorio no lleva licencia, así que no hay nada de tu código ni de tus datos fuera de ti): https://github.com/0skarzer0/dc2naomi/tree/main/homebrew/orc2cdc (`orc2cdc-a689a9a-naomi.patch`, medidas en `MEDIDAS.md`). Cada cambio va detrás de un `-D`, apagado por defecto. ¡Gracias por el port y por publicar las fuentes!

## Sin coste de CPU, deberían valer tal cual en Dreamcast

**1. Las rayas de la carretera "se pintan delante del coche"** en las calzadas con textura cuadrada con mipmaps (BEAC: la 11 de SEG17, 256x256, las rayas van dentro del asfalto). Vista de canto, la PowerVR baja varios niveles de mip y las rayas se funden con el gris a 30-60 m (las calzadas con texturas rectangulares, sin mipmaps, sí las ven lejos). En `compila_cab`, solo para las texturas con `0x200`:
- `-DSUELO_SS=1`: bit 12 de la palabra TSP (`m2.supersampling`, "Super-Sample Texture").
- `-DSUELO_MIPBIAS=PVR_MIPBIAS_0_25` (`cx.txr.mipmap_bias`).

Con las dos, las rayas se ven mucho más lejos y sin centelleo apreciable; la PowerVR no se nota (29,3 frente a 29,5 fps de media a 30 fps).

**2. Los cristales del coche salen opacos.** Las mallas de tipo 2 del CEX2 con su textura en la lista transparente (COCHE00: alfa del vértice 140/255, gris 0x4C de desplazamiento) usan `PVR_TXRENV_MODULATE`, y con MODULATE la PowerVR toma el alfa **solo de la textura** (el mapa del coche es ARGB1555: 1 dentro del círculo), así que el alfa del vértice no cuenta. Con `PVR_TXRENV_MODULATEALPHA` para el coche con `especular == 1` y lista 2 se ve la carretera a través (yo además bajo su alfa y su desplazamiento a 0,6: `CRISTAL_ALFA`).

## Medidas en la placa (misma CPU que la Dreamcast)

**3. La CPU no llega a 45 fps:** unos 30 ms de CPU por cuadro de media en carrera (dibujo + lógica, la medida con la que el juego recorta la distancia). Con el tope en 45 el juego va a unos 32 fps, sube y baja, y **acorta la distancia de dibujo hasta el mínimo, 600 m: el popping**. Con `FPS_OBJETIVO=30` y el recorte a 29/25 ms (`CPU_MS_CORTA` / `CPU_MS_ALARGA`), la distancia se queda en una mediana de unos 2750 m y la imagen va estable. Lo más probable es que en Dreamcast pase lo mismo.

**4. Dónde se va el tiempo** (con un `PRF` por partes de `demo/main.c`, 415 ventanas de carrera): el **coche del jugador**, 4 ms fijos por cuadro (10 440 vértices, sin LOD), y los **dos personajes**, 3,7 ms (2 900 vértices con huesos en la CPU): casi una cuarta parte del cuadro pase lo que pase en la carretera. La etapa, 6-8 ms.

**5. Compilador** (gcc 13 de Ubuntu, `gcc-sh-elf`): `-ffast-math -ffp-contract=fast` triplica la CPU por cuadro, y con `-O3` no arranca (menos `main.c` y `camara.c`, que no compilan con `-O3`). Puede que con tu compilador sea distinto.

## Opcional: lo que añadimos y quizá te interese

**6. Reflejo del escenario en la carrocería** (`-DREFLEJO_CIELO=1`, `coche_reflejo`). El mapa de entorno del coche es una vista fija y oscura (media 35/255) indexada por la normal vista desde la cámara: con la cámara detrás, el capó coge casi siempre la misma zona y nunca refleja la etapa (además, sumado al rojo, lo vuelve rosa). Ahora una panorámica de 360 grados por zona (cielo, palmeras, edificios, carteles), dibujada al convertir por software a partir de los datos de la etapa (`reflejo.py`, que usa tus `pvs.py`, `pak_union.py` y `vq.py`: `REFLEJO.DAT`, VQ 256x64, 6 KB por zona, 185 KB las 30). Gira con el rumbo y corre hacia atrás con la distancia. Sin el fichero, refleja el cielo de la etapa. Ojo: en la placa costó ~2 ms de CPU por cuadro y aún no sé de qué parte.

**7. Sombras de la calzada sobre el coche** (`-DSOMBRA_COCHE=1`, `coche_sombra`). Las sombras de palmeras, carteles y puentes son mallas planas de la lista 2 con textura oscura con alfa (BEAC: la 37, 128x128, la sombra de una palmera). Se miran 6 puntos a lo largo del coche contra esas mallas (texel del blob con `texel_de`) y se oscurece la pintura con un degradado. Solo gasta al entrar o salir de una sombra y no pide RAM (una copia de 42 KB pedida al cargar el coche rompía el reparto).

## Glitches vistos en la placa (no sé si salen también en Dreamcast)

- **Cielo cortado en rectángulos, en vertical o en diagonal**, casi siempre en las uniones (dos cielos fundiéndose), con bordes alineados con las teselas de 32x32; y en la ciudad de noche (LASV, ~9'00) **falta la carretera** y se ve el agua debajo. Sospecho de un OPB lleno; en NAOMI subí los translúcidos a `PVR_BINSIZE_32` con 8 juegos de reserva (`OPB_TR`, `OPB_EXTRA`), sin confirmar que lo arregle (en Dreamcast hay la mitad de VRAM).
- **Panel liso fijo con degradado rosa-blanco** delante, dentro de un túnel de LASV (~9'38). Candidatos: los planos aditivos gigantes de los focos (texturas 129-131 de SEG22, 64x16 ARGB4444, 500-600 m de alto).
- **Una forma azul lisa y quieta en el cielo** al atardecer (~7'05).

Si quieres fotos, medidas o algo más concreto, lo preparo.
