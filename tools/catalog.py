"""The games dc2naomi knows, per cabinet.

A disc is "known" when the SHA-1 of every program file its games.py profile patches matches SIGNATURES
(made with tools/gensig.py; hashes only, nothing from the discs). Any other disc, or a known one with a
different or modified program, is converted in experimental mode (patch points found by findpatch.py).

Status per cabinet:
  ok           tested on a real NAOMI with this cabinet: the controls given are the tuned ones
  experimental not tested on a real board with this cabinet (default controls)
  broken       known not to work yet (the user is asked before converting)
Cabinets: "joy" = standard NAOMI cabinet (2 sticks, 6 buttons per player, 2 STARTs; dc2naomi.exe),
          "ct"  = Crazy Taxi cabinet (wheel, gas, brake, 2-position lever, START; dc2naomict.exe).
"""

SIGNATURES = {
    "ct2h": [("1ST_READ.BIN", "bcff06e9defcd454d99ada84b9d26757e8ab4221")],
    "ikaruga": [("1ST_READ.BIN", "f2524eb571da1b0fb4a9b2cdab448ce24764c6f9")],
    "nmus": [("1ST_READ.BIN", "cd332c1b75c2fa2e7bed3fba92d894b87a50f1bf")],
    "kof99": [("1ST_READ.BIN", "c0fe5e55fd89cf9f0d28d080770979f433a29296")],
    "lb2": [("1ST_READ.BIN", "238e30382a4dfb44d48225015516a8a81d09b5a7")],
    "ssf2x": [("1ST_READ.BIN", "5a4ee7a2c7447fd2267524d951059d01364a1000")],
    "f355": [("1ST_READ.BIN", "78b6c980a0f4d383d4c206c0decc322076414ed7")],
    "kof02": [("1ST_READ.BIN", "aed05deb3421cff08303534197999248bce884f8")],
    "sf3ts": [("1ST_READ.BIN", "f2ee7ce2b687ad5c0816a5eac630bb299bdc5572")],
    "motw": [("1ST_READ.BIN", "ec6bcbe8e9a88b4d5ac0d8d6aecd3ef0716ebfbb")],
    "spf2x": [("1ST_READ.BIN", "98a030e0106d537bfdd8b4bf458264ba6b684193")],
    "w18": [("1ST_READ.BIN", "9b93efd881dca11c4b40beff3f62408cf67a6dac")],
    "ysgw": [("1ST_READ.BIN", "4245af01235c1ab6ee70ae62c28e2a21aecf8402"),
             ("PD.BIN", "30ca1175ce8d13e9e78395eae4c01c1bb30f7b81"),
             ("LOADER.BIN", "23f409186873b525259478ae17f5ad5959327fdd")],
    "sf3di": [("1ST_READ.BIN", "d0cae155657304bc8ea227b21586835380721b91")],
}

# Control descriptions shown to the user (Spanish: the project's language).
PADS_TEXT = {
    "joy": ["Palanca = cruceta y stick analógico", "Botones 1-6 = A, B, X, Y, L, R",
            "START = START (cada jugador el suyo)"],
    "wheel": ["Volante = stick analógico (a tope: izquierda/derecha)",
              "Acelerador = gatillo R, freno = gatillo L", "Palanca adelante = B, atrás = A",
              "START = START al soltarlo (si no se tocó nada más)",
              "Con START apretado: palanca = arriba/abajo, freno = X, acelerador = Y"],
    "menu": ["Volante a tope = izquierda/derecha (y stick analógico)", "Palanca adelante = B, atrás = A",
             "START = START al soltarlo; START + palanca = arriba/abajo"],
    "pole": ["Menús: como Yu Suzuki (START al soltar, START + palanca = arriba/abajo)",
             "Pole Position: acelerador = A, freno = B, palanca = cambio Low/High"],
    "ysgw": ["Como el mueble por defecto (START al soltar; con START: palanca = arriba/abajo, freno = X, acelerador = Y)",
             "START + volante a tope a la derecha = modo avión (After Burner II, Space Harrier):",
             "  palanca adelante = arriba, atrás = abajo; acelerador = disparo (A), freno = misil (B)",
             "START + volante a tope a la izquierda = vuelta al modo coche (OutRun, Hang-On, Power Drift)"],
    "ct": ["Como el mueble por defecto, y además:",
           "Palanca adelante = marcha D (B) y prepara el salto; otro toque adelante antes de 1 s = salto",
           "Palanca atrás = marcha R (A)",
           "START = START al soltarlo; con START apretado: palanca = arriba/abajo, freno = X, acelerador = Y"],
}

GAMES = {
    # profile: name, {cabinet: (status, pads, note)}; a missing cabinet = experimental with the default pads
    "ct2h": ("Crazy Taxi 2 (USA)", {"ct": ("ok", "ct", "")}),
    "ikaruga": ("Ikaruga (Japón)", {"joy": ("ok", "joy", "")}),
    "nmus": ("Namco Museum (USA)", {"ct": ("ok", "pole", "Sin memory card: confirmar con A (palanca atrás)")}),
    "ysgw": ("Yu Suzuki Game Works Vol. 1 (Japón)", {"ct": ("ok", "ysgw",
             "Power Drift: el sonido petardea y al salir con B se queda en negro")}),
    "kof99": ("The King of Fighters: Dream Match 1999 (USA)", {"joy": ("experimental", "joy", "Sin música (pistas de audio)")}),
    "lb2": ("The Last Blade 2 (USA)", {"joy": ("experimental", "joy", "Las películas de historia apuntan a una sola, para caber")}),
    "sf3ts": ("Street Fighter III: 3rd Strike (USA)", {"joy": ("experimental", "joy", "")}),
    "spf2x": ("Super Puzzle Fighter II X (Japón)", {"joy": ("experimental", "joy", "")}),
    "ssf2x": ("Super Street Fighter II X (Japón)", {"joy": ("experimental", "joy", "")}),
    "kof02": ("The King of Fighters 2002 (Japón)", {"joy": ("experimental", "joy", "")}),
    "motw": ("Garou: Mark of the Wolves (USA)", {"joy": ("experimental", "joy", "")}),
    "f355": ("F355 Challenge (USA)", {"ct": ("broken", "menu", "Se queda en \"Now Loading\""),
                                      "joy": ("broken", "joy", "Se queda en \"Now Loading\"")}),
    "w18": ("18 Wheeler: American Pro Trucker (USA)", {"ct": ("broken", "menu", "Pantalla negra tras el logo de SEGA"),
                                                       "joy": ("broken", "joy", "Pantalla negra tras el logo de SEGA")}),
    "sf3di": ("Street Fighter III: Double Impact (USA)", {
        "ct": ("broken", "wheel", "Son dos programas cargados por un menú: los mandos no llegan"),
        "joy": ("broken", "joy", "Son dos programas cargados por un menú: los mandos no llegan")}),
}

# Discs recognised by their IP.BIN product number but not convertible by this program yet.
UNSUPPORTED = {
    "MK-51037": "Daytona USA 2001: necesita recodificar su música para caber en 512 MB; aún no está en este programa.",
}

DEFAULT_PADS = {"joy": "joy", "ct": "wheel"}

# Games tested on the real board WITHOUT the emulated Visual Memory and left that way (the tuned, working build
# stays as it was tested). Every other game gets the VMU (Namco Museum and Daytona USA 2001 tested with it).
NO_VMU = {"ct2h", "ikaruga", "ysgw"}


def status(profile, cab):
    """(name, status, pads, note) of a known profile on a cabinet."""
    name, per = GAMES[profile]
    st, pads, note = per.get(cab, ("experimental", DEFAULT_PADS[cab], ""))
    return name, st, pads, note
