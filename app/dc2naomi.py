"""dc2naomi: converts a Dreamcast GD-ROM (.chd or .gdi) or self-booting CD (.cdi) into a NetDIMM image (.bin.gz) for a NAOMI / NAOMI 2.

    dc2naomi.exe   JUEGO.chd     standard NAOMI cabinet (2 sticks, 6 buttons per player, 2 STARTs)
    dc2naomict.exe JUEGO.chd     Crazy Taxi cabinet (wheel, pedals, 2-position lever, START)

Drag the .chd onto the program's icon (or run it and drag the file into its window). The image is written
next to the .chd. The cabinet comes from the program's name (or --cab joy|ct).
"""
import contextlib
import gzip
import hashlib
import io
import os
import sys
import time

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = getattr(sys, "_MEIPASS", None)  # PyInstaller one-file bundle
sys.path.insert(0, os.path.join(ROOT, "tools") if ROOT else os.path.join(HERE, "..", "tools"))
sys.path.insert(0, ROOT if ROOT else os.path.join(HERE, "..", "wipi"))

import build_image  # noqa: E402
import dc2naomi_vmu  # noqa: E402
import catalog  # noqa: E402
import findpatch  # noqa: E402
import games  # noqa: E402
from gdi import open_disc  # noqa: E402

VERSION = "0.2"
NETDIMM = 512 * 1024 * 1024
CABS = {"joy": "mueble NAOMI estándar (2 palancas, 6 botones, 2 START)",
        "ct": "mueble NAOMI Crazy Taxi (volante, pedales, palanca, START)"}
STATUS = {"ok": "PROBADO en placa real", "experimental": "EXPERIMENTAL (no probado en placa con este mueble)",
          "broken": "NO FUNCIONA todavía"}


def loader_path():
    return os.path.join(ROOT, "loader.bin") if ROOT else os.path.join(HERE, "loader.bin")


def say(*a):
    print(*a, flush=True)


def pause(interactive):
    if interactive:
        try:
            input("\nPulsa Enter para salir...")
        except EOFError:
            pass


def ask_yes(q, interactive):
    if not interactive:
        return True
    try:
        return input(q + " (s/N): ").strip().lower() in ("s", "si", "sí", "y", "yes")
    except EOFError:
        return False


def ip_info(ip):
    t = lambda a, b: ip[a:b].decode("latin-1").strip()  # noqa: E731
    return {"product": t(0x40, 0x4A), "version": t(0x4A, 0x50), "area": t(0x30, 0x38),
            "boot": t(0x60, 0x70), "title": t(0x80, 0x100), "hw": t(0, 0x10)}


def set_title(image, title):
    """The NAOMI header keeps the game name 8 times (one per region), 32 bytes each, padded with spaces."""
    name = "".join(c if 32 <= ord(c) < 127 else " " for c in title.upper())[:32].ljust(32).encode("ascii")
    image = bytearray(image)
    for i in range(8):
        image[0x30 + 0x20 * i:0x50 + 0x20 * i] = name
    return bytes(image)


def identify(disc):
    """The known games.py profile whose program files all match SIGNATURES, or None."""
    cache = {}
    for prof, files in catalog.SIGNATURES.items():
        ok = True
        for fn, sha in files:
            if fn not in cache:
                try:
                    cache[fn] = hashlib.sha1(disc.read_file(fn)).hexdigest()
                except KeyError:
                    cache[fn] = None
            if cache[fn] != sha:
                ok = False
                break
        if ok:
            return prof
    return None


def auto_profile(ip, first_read, info, pads):
    """Experimental profile for a game nobody has tuned: patch points found by findpatch.py."""
    r = findpatch.analyze(ip, first_read)
    notes = []
    groups = []
    if r["ip_std"]:
        groups.append({"file": "IP.BIN", "base": 0x8C008000, "patches": [
            (0x8C008382, 2, games.mov_imm0(0)), (0x8C00DAB4, 4, games.SCRATCH + 0x00),
            (0x8C00DAC0, 4, games.SCRATCH + 0x10)]})
    else:
        notes.append("El arranque (IP.BIN) no es el estándar de SEGA: puede no arrancar.")
    p = []
    for addr, reg in r["cable"]:
        p.append((addr, 2, games.mov_imm0(reg)))
    for addr in r["aica"]:
        p.append((addr, 2, games.mov_imm0(0)))
    if r["hook"]:
        p.append((r["hook"][0], 4, games.HOOK))
    else:
        notes.append("No se ha encontrado el controlador de mandos: puede arrancar pero sin responder a los mandos.")
    if not r["cable"] and not r["aica"]:
        notes.append("No se ha encontrado la detección del cable de vídeo: puede salir en un modo que el monitor no muestre.")
    # (r["texdma"] is not applied: on Virtua Tennis that literal is not the texture DMA, and aiming it at
    #  0x13000000 left the screen without textures in Flycast; it is only found and printed for hand tuning)
    for i, addr in enumerate(r["g1"][:16]):
        p.append((addr, 4, games.SCRATCH + 0x20 + 0x10 * i))
    if p:
        groups.append({"file": "1ST_READ.BIN", "base": 0x8C010000, "patches": p})
    area = info["area"]
    region = 1 if "U" in area else 2 if "E" in area else 0
    game = {"title": info["title"][:32] or "DREAMCAST", "pads": pads, "region": region, "language": 1,
            "layout": "gdi", "flags": 0x0004, "hook_pc": [], "groups": groups}
    return game, notes


class Progress(io.RawIOBase):
    """The gzip output, with a percentage on screen."""

    def __init__(self, f):
        self.f, self.total, self.done, self.last = f, 0, 0, -1

    def set_total(self, total):
        self.total = total

    def write(self, b):
        self.f.write(b)
        self.done += len(b)
        pct = min(100, self.done * 100 // max(1, self.total))
        if pct != self.last and self.total:
            self.last = pct
            sys.__stdout__.write(f"\r  Escribiendo... {pct:3d}%")
            sys.__stdout__.flush()
        return len(b)

    def writable(self):
        return True


def convert(path, cab, interactive, vmu=None):
    say(f"dc2naomi {VERSION} - {CABS[cab]}")
    say("=" * 72)
    if not os.path.isfile(path):
        say(f"No encuentro el archivo: {path}")
        return 1
    say(f"Disco: {os.path.basename(path)}")
    try:
        disc = open_disc(path)
        ip = disc.sectors(disc.base, 16)
    except Exception as e:  # noqa: BLE001
        say(f"No se puede leer el disco: {e}")
        return 1
    info = ip_info(ip)
    if not info["hw"].startswith("SEGA SEGAKATANA"):
        say("No parece un disco de Dreamcast (falta la cabecera SEGA SEGAKATANA).")
        return 1
    say(f"Juego:  {info['title']}  [{info['product']} {info['version']}]")
    if info["product"] in catalog.UNSUPPORTED:
        say("\n" + catalog.UNSUPPORTED[info["product"]])
        return 1
    if info["boot"].upper() != "1ST_READ.BIN":
        say(f"\nEste juego arranca con {info['boot']} (Windows CE u otro sistema): de momento no está soportado.")
        return 1

    prof = identify(disc)
    notes = []
    if prof:
        name, st, pads, note = catalog.status(prof, cab)
        game = dict(games.GAMES[prof], pads=pads)
        say(f"        {name}")
        if note:
            notes.append(note)
    else:
        st, pads = "experimental", catalog.DEFAULT_PADS[cab]
        try:
            first = disc.read_file("1ST_READ.BIN")
        except KeyError:
            say("\nNo encuentro 1ST_READ.BIN en el disco.")
            return 1
        game, notes = auto_profile(ip, first, info, pads)
        notes.insert(0, "Juego no probado (o versión distinta de la probada): parches localizados automáticamente.")
    if path.lower().endswith(".cdi"):
        notes.append("CD de autoarranque (.cdi): datos en la LBA %d%s." % (
            disc.base, "; 1ST_READ.BIN descifrado como hace la BIOS" if getattr(disc, "scrambled", False) else ""))
        filler = disc.filler_files()
        if filler:   # padding that places the data on the disc's edge: left out, it reads as zeros
            game["blank"] = list(game.get("blank", ())) + filler
            notes.append("Relleno del CD que no se copia: " + ", ".join(filler) + ".")
        if sum(1 for t in disc.tracks if t[2] != 4) > 1:
            notes.append("La música en pistas de audio de CD no suena (el residente no reproduce CD-DA).")
    else:
        # a GD-ROM's music as CD audio tracks in the high-density area (Bangai-O: 33 tracks): it will be silent
        cdda = [t for t in disc.tracks if t[1] >= 45000 and t[2] != 4]
        if len(cdda) >= 2:
            notes.append("AVISO: la música va en %d pistas de audio de CD (%d MB) y NO SONARÁ (el residente no "
                         "reproduce CD-DA); efectos y voces sí." % (len(cdda), sum(t[5] for t in cdda) * 2352 >> 20))
    if vmu is None:  # the default: every game but the ones tested (and left) without it
        vmu = prof not in catalog.NO_VMU
    game["vmu"] = vmu
    game["flags"] = (game["flags"] | 0x8000) if vmu else (game["flags"] & ~0x8000)
    say(f"Estado: {STATUS[st]}")
    if st == "broken":
        for n in notes:
            say(f"  - {n}")
        if not ask_yes("\nSabemos que este juego aún no funciona. ¿Convertirlo igualmente?", interactive):
            return 1
        notes = []

    base = os.path.splitext(path)[0]
    out = base + ("_dc2naomict" if cab == "ct" else "_dc2naomi") + ".bin.gz"
    tmp = out + ".part"
    image = set_title(open(loader_path(), "rb").read(), game["title"])
    say("\nAnalizando el disco (puede tardar un par de minutos)...")
    log = io.StringIO()
    t0 = time.time()
    try:
        with open(tmp, "wb") as raw, gzip.GzipFile(filename=os.path.basename(out)[:-3], mode="wb",
                                                     fileobj=raw, compresslevel=6, mtime=0) as gz:
            sink = Progress(gz)
            with contextlib.redirect_stdout(log):
                size = build_image.build(prof or "auto", game, path, None, image, sink)
        sys.stdout.write("\n")
        os.replace(tmp, out)
    except Exception as e:  # noqa: BLE001
        sys.stdout.write("\n")
        say(f"Error al convertir: {e}")
        say(log.getvalue()[-2000:])
        with contextlib.suppress(OSError):
            os.remove(tmp)
        return 1
    vmu_file = out[:-len(".bin.gz")] + ".vmu"
    if vmu and not os.path.exists(vmu_file):
        dc2naomi_vmu.save(vmu_file, dc2naomi_vmu.blank())
    gzsize = os.path.getsize(out)
    say(f"\nListo en {time.time() - t0:.0f} s: {out}")
    say(f"  Imagen: {size / 1048576:.1f} MB (comprimida {gzsize / 1048576:.1f} MB)")
    if size > NETDIMM:
        say(f"\n  AVISO: la imagen ocupa {size / 1048576:.0f} MB y NO CABE en la NetDIMM (512 MB).")
        say("  Reduce el juego (vídeos, datos que no uses) y vuelve a convertirlo.")
    if vmu:
        say(f"\nMemoria (VMU) emulada: {os.path.basename(vmu_file)} (tarjeta vacía de 128 KB; déjala junto al .bin.gz).")
        say("  Con los scripts de la carpeta wipi (ver LEEME_WIPI.txt) el netbooter guarda ahí las partidas;")
        say("  sin ellos el juego ve la tarjeta pero se pierde al apagar la placa.")
    else:
        say("\nSin memoria (VMU): este juego se probó sin ella y se deja como se probó.")
    say("\nMandos:")
    for line in catalog.PADS_TEXT[pads]:
        say(f"  - {line}")
    if notes:
        say("\nNotas:")
        for n in notes:
            say(f"  - {n}")
    return 0


def main(default_cab):
    args = [a for a in sys.argv[1:]]
    cab = default_cab
    if "--cab" in args:
        i = args.index("--cab")
        cab = args[i + 1]
        del args[i:i + 2]
    interactive = "--batch" not in args
    vmu = True if "--vmu" in args else False if "--sin-vmu" in args else None
    args = [a for a in args if a not in ("--batch", "--vmu", "--sin-vmu")]
    if not args:
        say(f"dc2naomi {VERSION} - {CABS[cab]}\n")
        say("Arrastra aquí el archivo .chd, .gdi o .cdi del juego y pulsa Enter:")
        try:
            args = [input("> ").strip().strip('"').strip("'")]
        except EOFError:
            return 1
    rc = 1
    for a in args:
        try:
            rc = convert(a, cab, interactive, vmu)
        except KeyboardInterrupt:
            say("\nCancelado.")
            rc = 1
        say("")
    pause(interactive)
    return rc


if __name__ == "__main__":
    name = os.path.basename(sys.argv[0]).lower()
    sys.exit(main("ct" if "dc2naomict" in name else "joy"))
