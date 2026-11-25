# Mario Kart 64 en la NAOMI: fluidez (fps)

El port de [mk64-dc](https://github.com/jnmartin84/mk64-dc) va siempre a 30 fps (`force_30fps = 1`): cada imagen
debería verse 2 vblanks (2 × 16,7 ms). Aquí está cómo se mide en la placa, qué causa los tirones y qué se ha cambiado.
Los cambios están en `homebrew/mk64/mk64-dc-naomi.patch` (el juego) y en `kos-680d1862-naomi_host.patch` (KallistiOS),
todo bajo `NAOMI_HOST`. `build_mk64.sh` los aplica y, si encuentra un árbol con una versión anterior, lo pone al día.

**Resultado (placa, demo entera): imágenes fuera de ritmo en carrera del 3,8 % al 0,0 %.**

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

- **Traza de los tirones** (`traza_mk64.py`, dirección `_naomi_traza`, `0x8c10f9f4`): en carrera, cuando una imagen no
  dura 2 vblanks, el juego guarda los últimos 16 cuadros (cuándo empezaron, cuándo acabó la CPU, cuándo se mandaron a
  la GPU) y los últimos 16 cambios de imagen (cuándo empezaron y cuánto duraron el registro y el render). Hasta 8
  fotos. Se leen al final, de una vez: `python3 traza_mk64.py 10.0.0.4 0x8c10f9f4`.

## Causas (en sencillo)

1. **El ritmo se marcaba en el sitio equivocado.** El juego esperaba al vblank par *después* de mandar el cuadro a la
   GPU, y KallistiOS cambia la imagen en el primer vblank tras acabar el render. Por eso la imagen salía cuando le
   tocaba según lo que tardasen CPU + GPU. Si un cuadro acababa antes de 16,7 ms y el siguiente después, uno se veía 1
   vblank y otro 3, aunque el juego fuese a 30 fps justos.
2. **La imagen salía 1 o 2 vblanks después de mandarla, según el cuadro** (la que más pesaba; la encontró la traza).
   Entre mandar el cuadro y la imagen nueva hay dos pasos: el registro (la geometría entra en la GPU, 7-15 ms) y el
   render (7-18 ms). Juntos rondan los 16,7 ms: un cuadro de 10,1 + 7,6 ms salía a los 2 vblanks y el siguiente, de
   8,8 + 7,2, a 1. KallistiOS cambia la imagen en el primer vblank tras acabar.
3. **El juego despertaba tarde.** KallistiOS no cambia de hilo cuando llega el vblank: el juego esperaba al siguiente
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

**3. La imagen sale siempre 2 vblanks después de mandarla** (parche de KallistiOS: `pvr_naomi_hold_flip(n)` y la
condición en `pvr_vblank_handler`; el juego lo llama antes de `pvr_scene_finish`). KallistiOS ya no cambia de imagen
antes de tiempo aunque el registro y el render acaben pronto. Todas duran 2 vblanks mientras registro + render quepan
en 33 ms, y en la traza siempre caben. El precio es que las imágenes que antes salían un vblank antes ahora esperan:
unos 16 ms más de retraso entre el mando y la pantalla en esas escenas.

**Con los cambios 1 y 2 (placa, una vuelta entera de la demo):**

| Tramo | antes | después |
|---|---|---|
| Título y menús de la demo | 1,5 – 2,4 % | 0 – 0,6 % |
| Mario Raceway 1P | 2,7 % | 1,2 – 2,2 % |
| Kalimari Desert 1P | 2,6 % | 1,6 – 1,8 % |
| Wario Stadium 3P | 7,9 % | 4,8 % |
| Choco Mountain 2P | 2,8 % | 3,4 – 4,8 % |
| Sherbet Land 4P | – | 2,5 % |
| **Todas las carreras** | **3,8 %** | **2,8 %** |

**Con los tres (placa, una vuelta entera de la demo, 8.670 imágenes en carrera):**

| Tramo | sin cambios | 1 + 2 | 1 + 2 + 3 |
|---|---|---|---|
| Título y menús de la demo | 1,5 – 2,4 % | 0 – 0,6 % | 0 % |
| Mario Raceway 1P | 2,7 % | 1,2 – 2,2 % | 0 % |
| Choco Mountain 2P | 2,8 % | 3,4 – 4,8 % | 0 % |
| Kalimari Desert 1P | 2,6 % | 1,6 – 1,8 % | 0 % |
| Wario Stadium 3P | 7,9 % | 4,8 % | 0 % |
| Bowser's Castle 1P | 0,9 % | 3,1 % | 0 % |
| Sherbet Land 4P | – | 2,5 % | 0 % |
| **Todas las carreras** | **3,8 %** | **2,8 %** | **0,0 %** |

## Lo que queda

- Medido con la demo, sin nadie jugando. Falta una partida de verdad (con objetos, 4 jugadores) y la opinión del
  jugador sobre el retraso del mando (cambio 3).
- Un cuadro cuyo registro + render pase de 33 ms, o cuya CPU pase de 33 ms, sigue saltando un vblank. En la demo
  no pasa (el render llega como mucho a 28 ms y la CPU, en carrera, a 30 ms: cerca del límite); en una partida con más objetos, quizá.
- `timehack.py` corre en el uso normal y habla con la NetDIMM; en las medidas estaba parado. Las lecturas no afectan
  (comprobado arriba), así que no debería notarse.

## Mandos (2026-11-26)

Esquema del usuario, en el residente (`DIMM_PAD_MK64`) y en el parche del juego:

| En el mueble | Botón del N64 |
|---|---|
| Acelerador | A |
| Freno | **B** (antes era C-derecha, ver abajo) |
| START + freno | **L** |
| Acelerador + START | **stick abajo + Z** (lanzar el objeto hacia atrás) |
| Palanca adelante / atrás | R (salto y derrape) / Z (usar objeto) |
| START solo | START (al soltarlo; con la palanca, arriba/abajo en los menús) |

- mk64-dc se compila con `BUTTON_SWAP_X=1`: la X de la Dreamcast es C-derecha y la B es B. El residente mandaba el
  freno como X, así que el freno nunca fue el B del N64. Ahora manda B.
- En el port, el gatillo L de la Dreamcast es Z en carrera y L en los menús: no había botón para L en carrera. El
  parche del juego hace que la C de la Dreamcast (que no usa nadie) sea L, y el residente la manda con START + freno.
- Con cualquiera de las dos combinaciones, START no se manda al soltarlo.
- Probado en Flycast leyendo `gControllers[0]` del juego: freno → B; START + freno → L; acelerador + START → A, stick
  abajo y gatillo L (en la demo, que cuenta como menú, sale como L; en carrera el port lo convierte en Z); START solo
  → del título a la selección de juego. En el mueble, pendiente.
- El perfil `dkr` (Diddy Kong Racing, otra sesión) usa los mismos mandos y hereda el cambio.
