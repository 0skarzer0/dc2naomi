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

**Ya no están en esta Pi:** `shutokou2_en` (carreras: al mueble Crazy Taxi va Tokyo Xtreme Racer 2); `ssf2x` (japonés) y `ssf2x_es` (el usuario se quedó con la inglesa); `cspike_es` (está el
original de NAOMI); Jeremy McGrath Supercross 2000 y Star Wars Racer (pasaron al mueble Crazy Taxi).
**Convertidos y sin subir** (en el PC, `isosdream/` y `dreamcastisos/`): Buzz Lightyear, Toy Story 2, Unreal Tournament
y Millennium Racer (sin música), Bangai-O (música en CD-DA, no suena).
**No convertidos** de lo que había en `dreamcastisos/`: pasan de 512 MB (Rayman 2, Sonic Adventure 1 y 2, Tech Romancer, Vampire Chronicle, Pro Pinball Trilogy, Psychic Force 2012, Virtua
Fighter 3tb); arrancan con Windows CE (Mars Matrix, Marvel vs. Capcom, WWF Attitude). **Descartados y borrados** (2026-11-13, se
juegan mal con palanca digital): Jet Grind Radio, Fur Fighters y Evil Dead.

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

## Apéndice: todo lo que hay en esta Pi (generado el 2026-11-13)

Además de los juegos de Dreamcast de arriba, la Pi tiene la colección de originales del usuario. Lista sacada de la
propia Pi con `tools/board/picatalog.py` (lee el CSV y `/boot/roms/`; estados de `docs/pi250-estado.csv`). En estos no
se ha documentado ninguna prueba, por eso salen con "?". Para regenerarla:
`PIHOST=192.168.68.250 PIPASS=... python3 tools/board/picatalog.py docs/pi250-estado.csv`.

**CSV limpiado el 2026-11-13 (a petición del usuario; copia `romsinfo.csv.bak_limpieza_20261113`, reimportado):**
quitadas 35 filas cuyo fichero no estaba en la tarjeta (Chihiro, Triforce, Initial D, Club Kart, King of Route 66,
Wild Riders, Crazy Taxi, Maximum Speed…: juegos del mueble Crazy Taxi o que no hay); la fila de Mushiking 2004 apuntaba
a `[840-0150]` y el fichero es `[840-0152]` (corregida); añadidas las de los cuatro ficheros que no salían en el menú:
las dos Capcom vs. SNK 2 "Unlocked-debug" (copiadas de las "unlocked", título con "(debug)") y Dragon Treasure 2 y 3
(filas nuevas sin imagen ni vídeo; son juegos de cartas). Ahora cada fila tiene su fichero y cada fichero su fila
(196 juegos).

**Después (mismo día, a petición del usuario: "Dragon Treasure quítalo; si hay algún juego de carreras quítalo, está
en la otra NAOMI"):** fuera de la tarjeta y del CSV (copia `romsinfo.csv.bak_quita_carreras`) Dragon Treasure 2 y 3,
18 Wheeler Deluxe y Standard, Faster Than Speed, Wave Runner GP, Tokyo Bus Guide, Jambo! Safari y Shutokou Battle 2 de
Dreamcast (`dc-shutokou2_en`, con su `.vmu`): los de conducción van al mueble Crazy Taxi (Pi .60). Quedan 187
juegos; `/boot` con 5,8 GB libres.

### Originales de NAOMI

| Fichero | Juego | Mandos | VMU | Estado |
|---|---|---|---|---|
| `n1-airline_pilots-[840-0005]` | Airline Pilots | Analog (Stick) |  | ? |
| `n1-akatsuki_bk_ausf_achse-[841-0058]` | Akatsuki Bk Ausf Achse | Digital (Stick) |  | ? |
| `n1-alien_front-[840-0048]` | Alien Front | Digital (Stick) |  | ? |
| `n1-azumanga_daioh_puzzle_bobble-[GDL-0018]` | Azumanga Daioh Puzzle Bobble | Digital (Stick) |  | ? |
| `n1-border_down-[GDL-0023]` | Border Down | Digital (Stick) |  | ? |
| `n1-burning_casino_{moeru_casino}-[GDL-0013]` | Burning Casino | Other |  | ? |
| `n1-cannon_spike-[841-0012]` | Cannon Spike / Gun Spike | Digital (Stick) |  | ? |
| `n1-capcom_vs_snk_2_mark_of_the_millenium-[GDL-0008]` | Capcom Vs. SNK 2 Mark of the Millenium 2001 | Digital (Stick) |  | ? |
| `n1-capcom_vs_snk_2_mark_of_the_millenium-unlocked-[GDL-0008]` | Capcom Vs. SNK 2 Mark of the Millenium 2001 UNLOCKED | Digital (Stick) |  | ? |
| `n1-capcom_vs_snk_2_mark_of_the_millenium-Unlocked-debug-[GDL-0008]` | Capcom Vs. SNK 2 Mark of the Millenium 2001 UNLOCKED (debug) | Digital (Stick) |  | ? |
| `n1-capcom_vs_snk_2_millionaire_fighting_2001-[GDL-0007]` | Capcom Vs. SNK 2 Millionaire Fighting 2001 | Digital (Stick) |  | ? |
| `n1-capcom_vs_snk_2_millionaire_fighting_2001-unlocked-[GDL-0007]` | Capcom Vs. SNK 2 Millionaire Fighting 2001 UNLOCKED | Digital (Stick) |  | ? |
| `n1-capcom_vs_snk_2_millionaire_fighting_2001-Unlocked-debug-[GDL-0007]` | Capcom Vs. SNK 2 Millionaire Fighting 2001 UNLOCKED (debug) | Digital (Stick) |  | ? |
| `n1-capcom_vs_snk_millenium_fight_2000_pro-[GDL-0004]` | Capcom Vs. SNK Millenium Fight 2000 Pro | Digital (Stick) |  | ? |
| `n1-capcom_vs_snk_millenium_fight_2000_pro-unlocked-[GDL-0004]` | Capcom Vs. SNK Millenium Fight 2000 Pro UNLOCKED | Digital (Stick) |  | ? |
| `n1-capcom_vs_snk_millenium_fight_2000-[841-0011]` | Capcom Vs. SNK Millennium Fight 2000 | Digital (Stick) |  | ? |
| `n1-capcom_vs_snk_millenium_fight_2000-unlocked-[841-0011]` | Capcom Vs. SNK Millennium Fight 2000 UNLOCKED | Digital (Stick) |  | ? |
| `n1-chaos_field-[GDL-0025]` | Chaos Field | Digital (Stick) |  | ? |
| `n1-cleopatra_fortune_plus-[GDL-0012]` | Cleopatra Fortune Plus | Digital (Stick) |  | ? |
| `n1-confidential_mission-[GDS-0001]` | Confidential Mission | Lightgun |  | ? |
| `n1-cosmic_smash-[840-0044]` | Cosmic Smash | Digital (Stick) |  | ? |
| `n1-crackin_dj-[840-0043]` | Crackin' DJ | Other |  | ? |
| `n1-crackin_dj_part_2-[840-0068]` | Crackin' DJ Part 2 | Other |  | ? |
| `n1-dead_or_alive_2-[841-0003]` | Dead or Alive 2 | Digital (Stick) |  | ? |
| `n1-dead_or_alive_2_millenium-[841-0003]` | Dead or Alive 2 Millennium | Digital (Stick) |  | ? |
| `n1-death_crimson_ox-[841-0016]` | Death Crimson OX | Digital (Stick) |  | ? |
| `n1-derby_owners_club-[840-0016]` | Derby Owners Club | Other |  | ? |
| `n1-derby_owners_club_2-[840-0083]` | Derby Owners Club II | Other |  | ? |
| `n1-derby_owners_club_world_rev.d-[840-0088]` | Derby Owners Club World Edition | Other |  | ? |
| `n1-doki_doki_idol_star_seeker-[GDL-0005]` | Doki Doki Idol Star Seeker | Digital (Stick) |  | ? |
| `n1-virtua_golf_{dynamic_golf}-[GDS-0009]` | Dynamic Golf / Virtua Golf | Analog (Trackball) |  | ? |
| `n1-dynamite_baseball-[840-0001]` | Dynamite Baseball NAOMI | Digital (Stick) |  | ? |
| `n1-dynamite_deka_ex-[840-0175]` | Dynamite Deka Ex - Asian Dynamite | Digital (Stick) |  | ? |
| `n1-giant_gram_2_all_japan_pro_wrestling-[840-0007]` | Giant Gram | Digital (Stick) |  | ? |
| `n1-giant_gram_3_giant_gram_2000-[840-0039]` | Giant Gram 2000 | Digital (Stick) |  | ? |
| `n1-giant_gram_4_{shin_nihon_pro_wrestling_toukon_retsuden_4_arcade_edition}-[25349801_TRF1_Ver.A]` | Giant Gram Toukon 4 | Digital (Stick) |  | ? |
| `n1-gigawing_2-[841-0014]` | Giga Wing 2 | Digital (Stick) |  | ? |
| `n1-guilty_gear_x-[841-0013]` | Guilty Gear X | Digital (Stick) |  | ? |
| `n1-guilty_gear_xx_midnight_carnival-[GDL-0011]` | Guilty Gear XX | Digital (Stick) |  | ? |
| `n1-guilty_gear_xx_accent_core-[GDL-0041]` | Guilty Gear XX Accent Core | Digital (Stick) |  | ? |
| `n1-guilty_gear_xx_reload-[GDL-0019]` | Guilty Gear XX Reload | Digital (Stick) |  | ? |
| `n1-guilty_gear_xx_slash-[GDL-0033]` | Guilty Gear XX Slash | Digital (Stick) |  | ? |
| `n1-biohazard_code_veronica-[25709801]` | Gun Survivor 2 Bio Hazard Code Veronica Comms Board | Lightgun |  | ? |
| `n1-biohazard_code_veronica_no_comm_board-[25709801]` | Gun Survivor 2 Bio Hazard Code Veronica NO Comms Board | Lightgun |  | ? |
| `n1-heavy_metal_geomatrix-[HMG016007]` | Heavy Metal Geomatrix | Digital (Stick) |  | ? |
| `n1-the_house_of_the_dead_2-[834-13636]` | House of the Dead 2 | Lightgun |  | ? |
| `n1-ikaruga_v3-[GDL-0010]` | Ikaruga | Digital (Stick) |  | ? |
| `n1-illmatic_envelope-[841-0059]` | Illvelo | Digital (Stick) |  | ? |
| `n1-jingi_storm_the_arcade-[GDL-0037]` | Jingy Storm - The Arcade | Digital (Stick) |  | ? |
| `n1-karous_v3-[GDL-0040]` | Karous | Digital (Stick) |  | ? |
| `n1-kuru_kuru_chameleon-[GDL-0034]` | Kurukuru Chameleon | Digital (Stick) |  | ? |
| `n1-la_keyboard_xyu-[GDS-0017]` | La Keyboardxyu | Digital (Keyboard) |  | ? |
| `n1-lupin_the_3rd_the_shooting-[GDS-0018]` | Lupin The Third - The Shooting | Lightgun |  | ? |
| `n1-lupin_the_3rd_the_typing-[GDS-0021]` | Lupin The Third - The Typing | Digital (Keyboard) |  | ? |
| `n1-mamoru-kun-wa-norowarete-shimatta!-[841-0060]` | Mamonoro | Digital (Stick) |  | ? |
| `n1-kasei_channel_mars_tv-[840-0025]` | Mars TV | Digital (Stick) |  | ? |
| `n1-marvel_vs_capcom_2-[841-0007]` | Marvel vs. Capcom 2 | Digital (Stick) |  | ? |
| `n1-marvel_vs_capcom_2_all_unlocked-[841-0007]` | Marvel vs. Capcom 2 UNLOCKED | Digital (Stick) |  | ? |
| `n1-the_maze_of_the_kings-[GDS-0022]` | Maze of the Kings, The | Lightgun |  | ? |
| `n1-melty_blood_act_cadenza_rev_a-[GDL-0028C]` | Melty Blood Act Cadenza | Digital (Stick) |  | ? |
| `n1-melty_blood_act_cadenza_rev.b-[GDL-0039]` | Melty Blood Act Cadenza Rev B | Digital (Stick) |  | ? |
| `n1-melty_blood_act_cadenza_rev.b2-[GDL-0039A]` | Melty Blood Act Cadenza Rev B2 | Digital (Stick) |  | ? |
| `n1-melty_blood_actress_again-[841-0061]` | Melty Blood Actress Again | Digital (Stick) |  | ? |
| `n1-melty_blood_actress_again_unlocked-[841-0061]` | Melty Blood Actress Again UNLOCKED | Digital (Stick) |  | ? |
| `n1-mobile_suit_gundam_federation_vs_zeon-[GDL-0001]` | Mobile Suit Gundam Federation vs. Zeon | Other |  | ? |
| `n1-mobile_suit_gundam_federation_vs_zeon_dx-[GDL-0006]` | Mobile Suit Gundam Federation Vs. Zeon DX | Other |  | ? |
| `n1-monkey_ball-[GDS-0008]` | Monkey Ball | Analog (Stick) |  | ? |
| `n1-musapeys_choco_marker-[GDL-0014]` | Musapeys Choco Marker | Digital (Stick) |  | ? |
| `n1-mushi_king_of_beetles_2004-[840-0152]` | Mushiking The King Of Beetles 2k4 | Other |  | ? |
| `n1-mushi_king_of_beetles_2005-[840-0158]` | Mushiking The King Of Beetles 2k5 2nd | Other |  | ? |
| `n1-ninja_assault-[25469801_NJA3_Ver.A]` | Ninja Assault | Lightgun |  | ? |
| `n1-noukone_puzzle_takoron-[GDL-0042]` | Noukone Puzzle Takoron | Digital (Stick) |  | ? |
| `n1-outtrigger-[840-0017]` | OutTrigger | Other |  | ? |
| `n1-power_stone-[841-0001]` | Power Stone | Digital (Stick) |  | ? |
| `n1-power_stone_2-[841-0008]` | Power Stone 2 | Digital (Stick) |  | ? |
| `n1-power_stone_2-unlocked-[841-0008]` | Power Stone 2 UNLOCKED | Digital (Stick) |  | ? |
| `n1-rival_schools_2_{project_justice}-[841-0015]` | Project Justice | Digital (Stick) |  | ? |
| `n1-rival_schools_2_{project_justice}_unlocked-[841-0015]` | Project Justice UNLOCKED | Digital (Stick) |  | ? |
| `n1-psyvariar2-[GDL-0024]` | Psyvariar 2 - The Will To Fabricate | Digital (Stick) |  | ? |
| `n1-puyo_pop_fever-[GDS-0034]` | Puyo Pop Fever | Digital (Stick) |  | ? |
| `n1-puyo_puyo_da-[841-0006]` | Puyo Puyo Da! | Digital (Stick) |  | ? |
| `n1-puyo_puyo_fever-[GDS-0031]` | Puyo Puyo Fever | Digital (Stick) |  | ? |
| `n1-quiz_ah_megamisama!-[840-0030]` | Quiz Ah Megamisama | Other |  | ? |
| `n1-quiz_keitai_q_mode-[GDL-0017]` | Quiz Keitai Q mode | Other |  | ? |
| `n1-radirgy-[GDL-0032]` | Radirgy | Digital (Stick) |  | ? |
| `n1-radirgy_noa-[841-0062]` | Radirgy Noir | Digital (Stick) |  | ? |
| `n1-rythm_tengoku-[840-0177]` | Rhythm Tengoku | Digital (Stick) |  | ? |
| `n1-samba_de_amigo-[840-0020]` | Samba De Amigo | Other |  | ? |
| `n1-sega_marine_fishing-[840-0027]` | Sega Marine Fishing | Other |  | ? |
| `n1-sega_strike_fighter-[840-0035]` | Sega Strike Fighter | Analog (Stick) |  | ? |
| `n1-sega_tetris-[840-0018]` | Sega Tetris | Digital (Stick) |  | ? |
| `n1-senko_no_ronde-[GDL-0030]` | Senko No Ronde | Digital (Stick) |  | ? |
| `n1-senko_no_ronde_sp-[GDL-0038]` | Senko No Ronde Special | Digital (Stick) |  | ? |
| `n1-shakatto_tambourine_motto_norinori_shinkyoku_tsuika_2001-[GDS-0013}` | Shakatto Tambourine 2001 | Other |  | ? |
| `n1-shakatto_tambourine_cho_powerup_chu_2001-[GDS-0016]` | Shakatto Tambourine 2001 Power Up | Other |  | ? |
| `n1-shakatto_tambourine_rev.b-[GDS-0002]` | Shakatto Tambourine Rev B | Other |  | ? |
| `n1-shikigami_no_shiro_2-[GDL-0021]` | Shikigami No Shiro II / The Castle of Shikigami II | Digital (Stick) |  | ? |
| `n1-exzeal_shooting_love_2007-[841-0057]` | Shooting Love 2007 | Digital (Stick) |  | ? |
| `n1-shootout_pool-[840-0095]` | Shootout Pool | Other |  | ? |
| `n1-slashout-[GDS-0004]` | Slashout | Digital (Stick) |  | ? |
| `n1-spawn_in_the_demons_hand-[841-0005]` | Spawn - In the Demons Hand | Digital (Stick) |  | ? |
| `n1-spikers_battle-[GDS-0005]` | Spikers Battle | Digital (Stick) |  | ? |
| `n1-sports_jam-[GDS-0003]` | Sports Jam | Digital (Stick) |  | ? |
| `n1-street_fighter_zero_3_upper-[GDL-0002]` | Street Fighter Zero 3 Upper | Digital (Stick) |  | ? |
| `n1-super_shanghai_2005_ver_a-[GDL-0031]` | Super Shanghai 2005 | Digital (Stick) |  | ? |
| `n1-tetris_kiwamemichi-[GDL-0020]` | Tetris Kiwamemichi | Digital (Stick) |  | ? |
| `n1-toy_fighter_{waffupu}-[840-0011]` | Toy Fighter | Digital (Stick) |  | ? |
| `n1-trigger-heart_exelica-[GDL-0036]` | Trigger Heart Exelica | Digital (Stick) |  | ? |
| `n1-trizeal-[GDL-0026]` | Trizeal | Digital (Stick) |  | ? |
| `n1-the_typing_of_the_dead-[840-0026]` | Typing of the Dead, The | Digital (Keyboard) |  | ? |
| `n1-under_defeat-[GDL-0035]` | Under Defeat | Digital (Stick) |  | ? |
| `n1-usagui_yamashiro_mahjong_hen-[GDL-0022]` | Usagi - Yamashiro Mahjong Hen | Other |  | ? |
| `n1-virtua_athletics_{virtua_athlete}-GDS-0019` | Virtua Athletics / Virtua Athlete | Digital (Stick) |  | ? |
| `n1-virtua_nba-[0840-0021C-01]` | Virtua NBA | Digital (Stick) |  | ? |
| `n1-virtua_striker_2_ver.2000-[840-0010]` | Virtua Striker 2 Ver. 2000 | Digital (Stick) |  | ? |
| `n1-virtua_tennis_{power_smash}-[GDS-0011]` | Virtua Tennis / Power Smash | Digital (Stick) |  | ? |
| `n1-virtua_tennis_2_{power_smash_2}-[GDS-0015]` | Virtua Tennis 2 / Power Smash 2 | Digital (Stick) |  | ? |
| `n1-virtual_on_oratorio_tangramvonot-[840-0028]` | Virtual On Oratorio Tangram M.S.B.S. ver5.66 2000 Edition | Other |  | ? |
| `n1-world_series_baseball-[GDS-0010]` | World Series Baseball / Super Major League | Digital (Stick) |  | ? |
| `n1-wwf_royal_rumble-[840-0040]` | WWF Royal Rumble | Digital (Stick) |  | ? |
| `n1-zero_gunner_2-[841-0020]` | Zero Gunner 2 | Digital (Stick) |  | ? |
| `n1-zombie_revenge-[840-0003]` | Zombie Revenge | Analog (Stick) |  | ? |

### Originales de NAOMI 2

| Fichero | Juego | Mandos | VMU | Estado |
|---|---|---|---|---|
| `n2-beach_spikers-[GDS-0014]` | Beach Spikers | Digital (Stick) |  | ? |
| `n2-virtua_fighter_4-[GDS-0012]` | Virtua Fighter 4 | Digital (Stick) |  | ? |
| `n2-virtua_fighter_4_evolution-[GDS-0024B]` | Virtua Fighter 4 Evolution | Digital (Stick) |  | ? |
| `n2-virtua_fighter_4_evolution_ver.b-[GDS-0024B]` | Virtua Fighter 4 Evolution Ver B | Digital (Stick) |  | ? |
| `n2-virtua_fighter_4_final_tuned-[GDS-0036A]` | Virtua Fighter 4 Final Tuned | Digital (Stick) |  | ? |
| `n2-virtua_fighter_4_final_tuned_ver.a-[GDS-0036D]` | Virtua Fighter 4 Final Tuned Ver A | Digital (Stick) |  | ? |
| `n2-virtua_fighter_4_final_tuned_ver.b-[GDS-0036F]` | Virtua Fighter 4 Final Tuned Ver B | Digital (Stick) |  | ? |
| `n2-virtua_fighter_4_ver.a-[GDS-0012B]` | Virtua Fighter 4 Ver A | Digital (Stick) |  | ? |
| `n2-virtua_fighter_4_ver.b-[GDS-0012C]` | Virtua Fighter 4 Ver B | Digital (Stick) |  | ? |
| `n2-virtua_striker_3-[GDS-0006]` | Virtua Striker 3 | Analog (Stick) |  | ? |

### Atomiswave convertidos

| Fichero | Juego | Mandos | VMU | Estado |
|---|---|---|---|---|
| `aw-baskets_AW16` | Animal Basket | Digital (Stick) |  | ? |
| `aw-demolish_fist_AW14` | Demolish Fist | Digital (Stick) |  | ? |
| `aw-dirty_pigskin_football_AW13` | Dirty Pigskin Football | Digital (Stick) |  | ? |
| `aw-dolphin_blue_AW00` | Dolphin Blue | Digital (Stick) |  | ? |
| `aw-hokuto_no_ken_AW15` | Fist of the North Star (Hokuto No Ken) | Digital (Stick) |  | ? |
| `aw-force_five_AW18` | Force Five | Digital (Stick) |  | ? |
| `aw-guilty_gear_isuka_AW01` | Guilty Gear Isuka | Digital (Stick) |  | ? |
| `aw-guilty_gear_x_ver15_AW20` | Guilty Gear X Ver. 1.5 | Digital (Stick) |  | ? |
| `aw-kenju_AW23` | Kenju | Digital (Stick) |  | ? |
| `aw-the_king_of_fighters_neo_wave_AW05` | King of Fighters NeoWave, The | Digital (Stick) |  | ? |
| `aw-the_king_of_fighters_neo_wave_characters_unlocked_AW05` | King of Fighters NeoWave, The UNLOCKED | Digital (Stick) |  | ? |
| `aw-the_king_of_fighters_xi_AW02` | King of Fighters XI, The | Digital (Stick) |  | ? |
| `aw-the_king_of_fighters_xi_unlocked_AW02` | King of Fighters XI, The UNLOCKED | Digital (Stick) |  | ? |
| `aw-knights_of_valour_the_7_spirits_AW03` | Knights Of Valour The Seven Spirits | Digital (Stick) |  | ? |
| `aw-knights_of_valour_the_7_spirits_dubhe_unlocked_AW03` | Knights Of Valour The Seven Spirits UNLOCKED | Digital (Stick) |  | ? |
| `aw-metal_slug_6_AW08` | Metal Slug 6 | Digital (Stick) |  | ? |
| `aw-violent_metal_slug_6_AW08` | Metal Slug 6 (Violent) | Digital (Stick) |  | ? |
| `aw-neogeobattlecoliseum_AW04` | Neo-Geo Battle Coliseum | Digital (Stick) |  | ? |
| `aw-neogeobattlecoliseum_unlocked_AW04` | Neo-Geo Battle Coliseum UNLOCKED | Digital (Stick) |  | ? |
| `aw-the_rumble_fish_2_AW19` | Rumble Fish 2, The | Digital (Stick) |  | ? |
| `aw-the_rumble_fish_2_unlocked_AW19` | Rumble Fish 2, The UNLOCKED | Digital (Stick) |  | ? |
| `aw-the_rumble_fish_AW17` | Rumble Fish, The | Digital (Stick) |  | ? |
| `aw-the_rumble_fish_unlocked_AW17` | Rumble Fish, The UNLOCKED | Digital (Stick) |  | ? |
| `aw-salaryman_kintaro_netselect_AW07` | Salary Man Kintaro | Other |  | ? |
| `aw-samurai_spirits_6_AW06` | Samurai Shodown VI | Digital (Stick) |  | ? |
| `aw-bass_fishing_simulator_AW22` | Sega Bass Fishing Challenge | Other |  | ? |
| `aw-sega_clay_challenge_AW21` | Sega Clay Challenge | Lightgun |  | ? |
| `aw-sports_shooting_AW11` | Sports Shooting USA | Lightgun |  | ? |
| `aw-tore_tore_sushi_AW12` | Sushi Bar | Digital (Stick) |  | ? |
