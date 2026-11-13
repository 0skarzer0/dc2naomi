# NAOMI de palancas (Pi .250): juegos de Dreamcast cargados

Mueble estándar de dos jugadores: 2 palancas, 6 botones y START por jugador. Raspberry WiPi `virtua` en
**192.168.68.250**, NetDIMM en 10.0.0.3. Todas las imágenes se hacen con `app/dc2naomi.py --cab joy` (palanca =
cruceta y stick, botones 1-6 = A B X Y L R) y llevan su `.vmu` al lado, con una partida con todo desbloqueado de
[bucanero/dreamcast-saves](https://github.com/bucanero/dreamcast-saves) cuando hay una de la misma región. Los juegos
de volante van al mueble Crazy Taxi (Pi .60): índice en
[naomi-wheel-games/docs/pi60-juegos.md](https://github.com/0skarzer0/naomi-wheel-games/blob/main/docs/pi60-juegos.md).

✅ funciona en placa · 🧪 subido, sin probar · ❌ con fallos. Ficheros `/boot/roms/dc-<nombre>_dc2naomi.{bin.gz,vmu}`;
la fila de cada uno en `/boot/config/romsinfo.csv` usa el nombre exacto del `.gz`. Cómo y cuándo se hizo cada uno:
la sección del [HANDOFF](../HANDOFF.md) que se indica.

| Fichero (`dc-…`) | Juego | Estado | VMU | HANDOFF |
|---|---|---|---|---|
| `ikaruga` | Ikaruga (JP) | ✅ | todo desbloqueado | Ikaruga con VMU desbloqueada |
| `sf3di` | Street Fighter III Double Impact | ✅ | `v50554` | sf3di funciona en placa |
| `ssf2x_en` | Super Street Fighter II X (traducción al inglés de ComradeSnarky) | ✅ | todo y menú DIP | Super Street Fighter II X |
| `rcotton_en` | Rainbow Cotton (traducción de Derek Pascarella), vídeos recodificados | ✅ | `RAINCOT` | Rainbow Cotton funciona |
| `kof02` | The King of Fighters 2002 | 🧪 | `KOF_2002` | Lote de lucha + YSGW |
| `motw` | Garou: Mark of the Wolves | 🧪 | `garou1` | Lote de lucha + YSGW |
| `sf3ts` | Street Fighter III 3rd Strike | 🧪 | `v37955` | Lote de lucha + YSGW |
| `spf2x` | Super Puzzle Fighter II X | 🧪 | vacía (no hay partida) | Lote de lucha + YSGW |
| `ysgw` | Yu Suzuki Game Works | 🧪 | sin VMU | Lote de lucha + YSGW |
| `dcop_es` | Dynamite Cop (PAL, traducción de pitito) | 🧪 | `v18467` (misiones 4-6) | Segundo lote: isosdream |
| `shutokou2_en` | Shutokou Battle 2 (traducción de SGGG) | 🧪 | `shoudu2` | Segundo lote: isosdream |
| `soulcal` | Soulcalibur (USA), música en mono | 🧪 | `00000031` | Soulcalibur |
| `gunbird2` | Gunbird 2 | 🧪 | `v33167` | Lote de 17 juegos |
| `jojo` | JoJo's Bizarre Adventure | 🧪 | `v11766` | Lote de 17 juegos |
| `karous` | Karous | 🧪 | vacía | Lote de 17 juegos |
| `lastblade2` | The Last Blade 2 (ripeo: sin vídeos) | 🧪 | `v35892` | Lote de 17 juegos; Last Blade 2 |
| `neogoldenlogres` | Neo Golden Logres | 🧪 | vacía | Lote de 17 juegos |
| `netdetennis` | Net de Tennis | 🧪 | vacía | Lote de 17 juegos |
| `psyvariar2` | Psyvariar 2 | 🧪 | vacía | Lote de 17 juegos |
| `radirgy` | Radirgy | 🧪 | vacía | Lote de 17 juegos |
| `shikigami2` | Shikigami no Shiro II | 🧪 | vacía | Lote de 17 juegos |
| `sonicshuffle` | Sonic Shuffle | 🧪 | `v20598` | Lote de 17 juegos |
| `triggerheart` | Triggerheart Exelica | 🧪 | vacía | Lote de 17 juegos |
| `trizeal` | Trizeal | 🧪 | vacía | Lote de 17 juegos |
| `twinklestar` | Twinkle Star Sprites | 🧪 | vacía | Lote de 17 juegos |
| `underdefeat` | Under Defeat | 🧪 | vacía | Lote de 17 juegos |
| `wwfrumble` | WWF Royal Rumble | 🧪 | `v39825` | Lote de 17 juegos |

**Ya no están en esta Pi:** `ssf2x` (japonés) y `ssf2x_es` (el usuario se quedó con la inglesa); `cspike_es` (está el
original de NAOMI); Jeremy McGrath Supercross 2000 y Star Wars Racer (pasaron al mueble Crazy Taxi).
**Convertidos y sin subir** (en el PC, `isosdream/` y `dreamcastisos/`): Buzz Lightyear, Toy Story 2, Unreal Tournament
y Millennium Racer (sin música), Bangai-O (música en CD-DA, no suena).
**No convertidos** de lo que había en `dreamcastisos/`: pasan de 512 MB (Evil Dead, Fur Fighters, Jet Grind Radio,
Rayman 2, Sonic Adventure 1 y 2, Tech Romancer, Vampire Chronicle, Pro Pinball Trilogy, Psychic Force 2012, Virtua
Fighter 3tb); arrancan con Windows CE (Mars Matrix, Marvel vs. Capcom, WWF Attitude).

## Reglas del usuario para esta Pi

- Nada con la música en pistas de audio de CD (no suena): avisar y no convertir.
- No versiones de Dreamcast de juegos que ya tiene en su original de NAOMI, **salvo los verticales** (el arcade va con
  el monitor girado; el de Dreamcast se juega en horizontal): Ikaruga, Shikigami II, Karous, Radirgy, Trizeal,
  Triggerheart, Under Defeat y Psyvariar 2 se quedan.
- Espacio en `/boot`: 4,6 GB libres el 2026-11-13 (84 %).
- No comprimir imágenes grandes en la propia Pi (se reinicia por falta de tensión): subir el `.gz` hecho.

*Al cambiar algo en la Pi .250, actualizar esta tabla.* **Comprobada contra la Pi el 2026-11-13 (21:30):** los 27
`dc-*_dc2naomi.bin.gz` de la tabla y ninguno más, cada uno con una sola fila en el CSV y con su `.vmu` (menos `ysgw`,
que no lleva); ninguna fila sin fichero. Sobra un `kof02_dc2naomi.vmu` sin prefijo (de antes del cambio de nombre,
distinto del `dc-kof02` actual y sin fila que lo use): se deja hasta que el usuario diga si lo quiere.
