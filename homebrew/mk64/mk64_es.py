#!/usr/bin/env python3
"""mk64_es.py US.z64 ES.z64 MK64DC_DIR

Spanish Mario Kart 64 for mk64-dc, from the user's own ROMs: US.z64 is Mario Kart 64 (U) [!] and ES.z64 is the
same ROM with blade133bo's Spanish patch (v1.1, xdelta) applied. Nothing translated is stored here: this script
only knows where the text is.

What the patch changes, and how each part reaches the port:
  * textures (menus, titles, onomatopoeia palette...): Torch extracts them from the ROM, so building from ES.z64
    is enough. Torch knows the ROM by its SHA1 (config.yml): the US block is duplicated under the ES SHA1.
  * text: in the N64 code's data, which the decompilation rebuilds from C (src/menu_items.c, src/ending/credits.c)
    and the course yamls (yamls/courses/*_metadata.yml: name, debug_name). The strings of the two ROMs pair one to
    one; the C literals are matched to the US strings in order (difflib), so an English string used twice with two
    translations gets each one where it belongs.
  * the port's own strings (the VMU messages that replace the Controller Pak ones) are not in any ROM: they get
    our own translation, PORT_ES below.

The files it touches are restored with git first, so it can run again.
"""
import difflib, glob, hashlib, os, re, subprocess, sys

US_MD5 = "3a67d9986f54eb282924fca4cd5f6dff"
US_SHA1 = "579c48e211ae952530ffc8738709f078d5dd215e"
# null-terminated strings of the main code's data: menus and course names, then the credits
TEXT_BLOCKS = [(0xF0300, 0xF1900), (0x12A100, 0x12A700)]
C_FILES = ["src/menu_items.c", "src/ending/credits.c", "src/racing/memory.c"]

# the port's VMU messages (src/menu_items.c), translated by us: array -> {English: Spanish}. They win over the
# ROM's text inside that array (its lines no longer pair with the Controller Pak message they replaced).
PORT_ES = {
    "D_800E7940": {
        "NO DREAMCAST VMU DETECTED": "NO SE DETECTA LA VMU",
        "TO SAVE GHOST DATA, ": "PARA GUARDAR EL FANTASMA,",
        "INSERT DREAMCAST VMU ": "COLOCA UNA VMU DE DREAMCAST",
        "UNABLE TO READ ": "IMPOSIBLE LEER LOS DATOS",
        "DREAMCAST VMU DATA": "DE LA VMU DE DREAMCAST",
        "INSUFFICIENT FREE PAGES AVAILABLE ": "NO HAY BLOQUES LIBRES",
        "ON DREAMCAST VMU TO CREATE ": "EN LA VMU PARA CREAR LOS",
        "GAME DATA, PLEASE FREE 67 BLOCKS": "DATOS. LIBERA 67 BLOQUES PARA",
        "TO SAVE TIME TRIAL GHOSTS.": "GUARDAR LOS FANTASMAS.",
    },
    "D_800E7980": {"INSERT DREAMCAST VMU ": "COLOCA UNA VMU DE DREAMCAST"},
}


def strings(rom, lo, hi):
    return [m.group() for m in re.finditer(rb"[\x20-\x7e]{2,}", rom[lo:hi]) if rom[lo + m.end()] == 0]


def c_escape(b):
    return b.decode("ascii").replace("\\", "\\\\").replace('"', '\\"')


def main():
    us_path, es_path, src = sys.argv[1:4]
    us = open(us_path, "rb").read()
    es = open(es_path, "rb").read()
    if hashlib.md5(us).hexdigest() != US_MD5:
        sys.exit(f"{us_path} is not Mario Kart 64 (U) [!].z64")
    if len(es) != len(us):
        sys.exit(f"{es_path}: not the size of the US ROM (is it the Spanish patch?)")
    es_sha1 = hashlib.sha1(es).hexdigest()

    pairs = []
    for lo, hi in TEXT_BLOCKS:
        a, b = strings(us, lo, hi), strings(es, lo, hi)
        if len(a) != len(b):
            sys.exit(f"text block 0x{lo:X}: {len(a)} English strings, {len(b)} Spanish ones")
        pairs += list(zip(a, b))

    files = C_FILES + sorted(os.path.relpath(f, src) for f in glob.glob(f"{src}/yamls/courses/*_metadata.yml"))
    subprocess.run(["git", "-C", src, "checkout", "--", "config.yml", "mk64.us.sha1"] + files, check=True)

    # 1. extract_assets.py checks baserom.us.z64 against mk64.us.sha1; Torch, against config.yml:
    #    the Spanish ROM's SHA1 in the first, the US description under that SHA1 in the second
    open(f"{src}/mk64.us.sha1", "w").write(f"{es_sha1}  build/us/mk64.us.z64\n")
    cfg_path = f"{src}/config.yml"
    cfg = open(cfg_path).read()
    m = re.search(rf"^{US_SHA1}:\n(?:[ \t].*\n|\n)*", cfg, re.M)
    if not m:
        sys.exit("config.yml: no block for the US ROM")
    open(cfg_path, "w").write(cfg + "\n" + m.group().replace(US_SHA1, es_sha1, 1).replace("[US]", "[US, ES]", 1))

    # 2. course names: one translation each (the ROM repeats the list three times, always the same)
    names = {}
    for a, b in pairs:
        names.setdefault(a, b)
    ny = 0
    yaml_done = set()
    for f in files[len(C_FILES):]:
        p = f"{src}/{f}"
        t = open(p).read()
        def yrep(mm):
            nonlocal ny
            v = mm.group(2).encode()
            if v in names and names[v] != v:
                ny += 1
                yaml_done.add(v)
                return f"{mm.group(1)}{names[v].decode().rstrip()}"
            return mm.group(0)
        t = re.sub(r"^(  (?:name|debug_name): )(.*)$", yrep, t, flags=re.M)
        open(p, "w").write(t)

    # 3. C literals, aligned with the ROM's English strings in order
    lit = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
    found = []  # (file, start, end, value)
    texts = {}
    for f in C_FILES:
        t = open(f"{src}/{f}", encoding="latin-1").read()
        texts[f] = t
        for mm in lit.finditer(t):
            line = t[t.rfind("\n", 0, mm.start()) + 1:mm.start()]
            if "//" in line or line.lstrip().startswith("#"):
                continue
            v = mm.group(1).encode("latin-1").decode("unicode_escape").encode("latin-1")
            found.append((f, mm.start(), mm.end(), v))
    sm = difflib.SequenceMatcher(None, [p[0] for p in pairs], [x[3] for x in found], autojunk=False)
    edits = {f: [] for f in C_FILES}
    nc = 0
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            a, b = pairs[blk.a + k]
            f, s, e, _ = found[blk.b + k]
            if a != b:
                edits[f].append((s, e, b))
                nc += 1
    np_ = 0
    t = texts["src/menu_items.c"]
    for arr, table in PORT_ES.items():
        m = re.search(rf"\b{arr}\[\][^{{]*{{", t)
        if not m:
            sys.exit(f"src/menu_items.c: no {arr}")
        lo, hi = m.end(), t.index("};", m.end())
        for f, s, e, v in found:
            tr = table.get(v.decode("latin-1"))
            if f == "src/menu_items.c" and lo <= s < hi and tr:
                edits[f] = [x for x in edits[f] if x[0] != s] + [(s, e, tr.encode())]
                np_ += 1
    for f, ed in edits.items():
        t = texts[f]
        for s, e, b in sorted(ed, reverse=True):
            t = t[:s] + '"' + c_escape(b) + '"' + t[e:]
        open(f"{src}/{f}", "w", encoding="latin-1").write(t)

    used = names_used(pairs, sm)
    left = [a.decode() for a, b in pairs if a != b and a not in used and a not in yaml_done]
    print(f"Spanish: {len(pairs)} ROM strings, {nc} C literals and {ny} course names translated, "
          f"{np_} port strings (VMU); Torch knows SHA1 {es_sha1}")
    if left:
        print("not found in the source (yaml or unused):", ", ".join(sorted(set(left))))


def names_used(pairs, sm):
    used = set()
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            used.add(pairs[blk.a + k][0])
    return used


if __name__ == "__main__":
    main()
