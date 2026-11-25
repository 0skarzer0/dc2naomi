# Mario Kart 64 en la NAOMI: fluidez (fps)

El port de [mk64-dc](https://github.com/jnmartin84/mk64-dc) va siempre a 30 fps (`force_30fps = 1`): cada imagen
debería verse 2 vblanks (2 × 16,7 ms). Aquí está cómo se mide en la placa, qué causa los tirones y qué se ha cambiado.
Los cambios están en `homebrew/mk64/mk64-dc-naomi.patch` (todo bajo `NAOMI_HOST`) y `build_mk64.sh` lo aplica.

## Cómo se mide

- El juego rellena un bloque `naomi_med` (40 números) cada 30 cuadros. `build_mk64.sh` imprime su dirección
  (`0x8c101258` en las imágenes de noviembre de 2026).
- Desde la Raspberry, por la NetDIMM, sin `timehack.py` a la vez:

  ```
  pkill -f "[t]imehack.py"
  python3 med_mk64.py 10.0.0.4 0x8c101258 480 /root/medida.csv        # una línea por ventana de 30 cuadros
  python3 resumen_mk64.py /root/medida.csv                             # por tramo (estado, circuito, jugadores)
  ```

  Con un 5.º argumento (`10`) solo lee una ventana cada 10 s, y esa ventana se ha jugado sin lecturas. El juego
  contesta cada lectura con las interrupciones cortadas. Comprobado que las lecturas seguidas no son lo que causa
  los tirones (2,8 % con lecturas seguidas, 2,2 % sin ellas).
- Se mide la **demo automática** (la que sale sola tras el título). Siempre es la misma secuencia: Mario Raceway 1P,
  Choco Mountain 2P, Kalimari Desert 1P, Wario Stadium 3P, Bowser's Castle 1P, Sherbet Land 4P... Así las medidas se
  pueden comparar. Una vuelta entera son unos 8 minutos.
- Lo que cuenta para el jugador es **«pantalla»**: cuántos vblanks dura cada imagen en la tele. Se cuenta en el
  vblank con el contador de cambios de imagen de la PVR. 2 = bien. 1 o 3 = tirón (una imagen se queda un vblank de
  más y la siguiente uno de menos). También se miden: lógica y dibujo (CPU), render de la GPU, el retraso con que
  despierta el juego tras el vblank y el hilo de audio.

## Medida de partida (sin cambios, demo, placa)

| Tramo | imágenes fuera de ritmo |
|---|---|
| Título y menús de la demo | 1,5 – 2,4 % |
| Mario Raceway 1P | 2,7 % |
| Choco Mountain 2P | 2,8 % |
| Kalimari Desert 1P | 2,6 % |
| Wario Stadium 3P | 7,9 % |
| **Todas las carreras** | **3,8 %** |

- El juego en sí va a 30,0 fps: no le falta CPU. Lógica + dibujo suman 10-21 ms de los 33 disponibles.
- La GPU tarda 8-12 ms de media en pintar cada imagen (picos de 15-19 ms).
- El juego despierta tras el vblank 1,4 ms tarde de media (máximo 2,9 ms).
- El audio gasta menos de 1 ms por vblank: no es el problema.

## Causas (en sencillo)

1. **El ritmo se marcaba en el sitio equivocado.** El juego esperaba al vblank par *después* de mandar el cuadro a la
   GPU, y KallistiOS cambia la imagen en el primer vblank tras acabar el render. Por eso la imagen salía cuando le
   tocaba según lo que tardasen CPU + GPU. Si un cuadro acababa antes de 16,7 ms y el siguiente después, uno se veía 1
   vblank y otro 3, aunque el juego fuese a 30 fps justos.
2. **El juego despertaba tarde.** KallistiOS no cambia de hilo cuando llega el vblank: el juego esperaba al siguiente
   punto de cambio, que era el hilo que contesta a la NetDIMM (cada 2 ms) o el tic del reloj (cada 10 ms).

## Cambios

Cada uno se probó primero en Flycast (la demo con la BIOS NAOMI 1, `naomi.zip` en `~/.local/share/flycast/`) y luego
en la placa del mueble Crazy Taxi con la misma demo.

**1. El ritmo, antes de mandar el cuadro a la GPU** (`gfx_end_frame` en `src/gfx/gfx_retro_dc.c`). El juego espera
al vblank par y entonces llama a `pvr_scene_finish`. La GPU arranca siempre en el vblank del ritmo y la imagen sale
en el siguiente, siempre que el render quepa en 16,7 ms. Además, la CPU del cuadro siguiente trabaja mientras la GPU
pinta. Flycast: de 3/24/3 a 0/30/0 (imágenes de 1/2/3 vblanks en 30). Placa: título y menús al 0-0,4 %.

**2. Cambiar de hilo en el vblank** (`vblfunc` en `src/main.c`: `thd_schedule(1, 0)` tras despertar a quien espera,
igual que hace KallistiOS en `pvr_irq.c` al acabar la GPU). Retraso al despertar: de 1,4 ms (máx. 2,9) a 0,0.

**Con los dos (placa, una vuelta entera de la demo):**

| Tramo | antes | después |
|---|---|---|
| Título y menús de la demo | 1,5 – 2,4 % | 0 – 0,6 % |
| Mario Raceway 1P | 2,7 % | 1,2 – 2,2 % |
| Kalimari Desert 1P | 2,6 % | 1,6 – 1,8 % |
| Wario Stadium 3P | 7,9 % | 4,8 % |
| Choco Mountain 2P | 2,8 % | 3,4 – 4,8 % |
| Sherbet Land 4P | – | 2,5 % |
| **Todas las carreras** | **3,8 %** | **2,8 %** |

## Lo que queda

En las carreras sigue habiendo un 2-3 % de imágenes fuera de ritmo en ventanas donde ni la CPU (menos de 33 ms), ni
el render (menos de 14 ms) ni el despertar (0 ms) lo explican. Choco Mountain 2P es el peor. Lo siguiente sería
apuntar, imagen por imagen, cuándo se manda el cuadro, cuándo acaba la GPU y en qué vblank cambia la imagen, para ver
cuál de los tres se sale de su sitio. Las imágenes con render de más de 16,7 ms (picos de hasta 20-30 ms en Mario
Raceway y Bowser's Castle) también saltan un vblank: sería cosa de aligerar lo que pinta la GPU (las listas
translúcidas se ordenan por píxel, `autosort`).
