#!/usr/bin/env python3
"""withfiles.py FOLDER [dc2naomi.py arguments] : converts a game with some of its disc files replaced by smaller
ones, e.g. movies re-encoded by tools/sfdre.py so that the image fits in the NetDIMM.

FOLDER holds the new files at their disc paths (FOLDER/MOVIES/INTRO.SFD replaces MOVIES/INTRO.SFD). Each new file
is written at the first sector of the one it replaces (it must not be bigger), its directory record gets the new
size, and the rest of the old file's sectors read as zeros, which the image leaves out. Nothing else on the disc
changes. Used for Rainbow Cotton (16 movies, 873 -> 500 MB, works on the board) and Buzz Lightyear of Star Command.

    python3 tools/withfiles.py ~/rc/new --cab joy --batch "Rainbow Cotton.chd"
    (GZIP_LEVEL=1 in the environment: faster, slightly bigger .gz)
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_image  # noqa: E402
import gdi  # noqa: E402

_open_disc = gdi.open_disc


def replaced_disc(folder):
    news = {}
    for root, _, names in os.walk(folder):
        for n in names:
            full = os.path.join(root, n)
            news[os.path.relpath(full, folder).replace(os.sep, "/").upper()] = full

    def opener(path):
        d = _open_disc(path)
        raw = d.sector
        files = {p.upper(): (lba, size) for p, lba, size in d.walk()}
        repl, zero, dirpatch, sizes = {}, set(), {}, {}
        for name, full in news.items():
            if name not in files:
                raise SystemExit(f"{name}: no está en el disco")
            lba, size = files[name]
            data = open(full, "rb").read()
            if len(data) > size:
                raise SystemExit(f"{name}: el nuevo ({len(data)} bytes) es mayor que el original ({size})")
            sizes[name] = len(data)
            data += bytes(-len(data) % 2048)
            for k in range(len(data) // 2048):
                repl[lba + k] = data[k * 2048:(k + 1) * 2048]
            for k in range(len(data) // 2048, (size + 2047) // 2048):
                zero.add(lba + k)
        pvd = raw(d.base + 16)
        root = pvd[156:190]
        todo = [("", struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0])]
        while todo:
            pre, dlba, dsize = todo.pop()
            for k in range((dsize + 2047) // 2048):
                sl = dlba + k
                sec = bytearray(dirpatch.get(sl, raw(sl)))
                i = 0
                while i < 2048 and sec[i]:
                    n = sec[i]
                    nm = bytes(sec[i + 33:i + 33 + sec[i + 32]])
                    if nm not in (b"\0", b"\1"):
                        full = pre + nm.decode(errors="replace").split(";")[0]
                        if sec[i + 25] & 2:
                            todo.append((full + "/", struct.unpack_from("<I", sec, i + 2)[0],
                                         struct.unpack_from("<I", sec, i + 10)[0]))
                        elif full.upper() in sizes:
                            struct.pack_into("<I", sec, i + 10, sizes[full.upper()])
                            struct.pack_into(">I", sec, i + 14, sizes[full.upper()])
                            dirpatch[sl] = bytes(sec)
                    i += n
        zeros = bytes(2048)

        def sector(lba):
            if lba in repl:
                return repl[lba]
            if lba in zero:
                return zeros
            if lba in dirpatch:
                return dirpatch[lba]
            return raw(lba)
        d.sector = sector
        print(f"  {len(news)} archivos sustituidos ({sum(sizes.values()) / 1048576:.1f} MB), "
              f"{len(zero)} sectores sobrantes a cero")
        return d
    return opener


def main():
    level = os.environ.get("GZIP_LEVEL")                  # e.g. 1, when time is short (3 min per command)
    if level:
        import gzip
        orig = gzip.GzipFile.__init__

        def init(self, *a, **k):
            k["compresslevel"] = int(level)
            orig(self, *a, **k)
        gzip.GzipFile.__init__ = init
    folder = sys.argv[1]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    opener = replaced_disc(folder)
    gdi.open_disc = build_image.open_disc = opener
    sys.path.insert(0, os.path.join(HERE, "..", "app"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("dc2naomi_app", os.path.join(HERE, "..", "app", "dc2naomi.py"))
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app.open_disc = opener
    auto = app.auto_profile

    def auto_profile(*a):
        game, notes = auto(*a)
        notes.append(f"Archivos del disco sustituidos por los de {folder} (vídeos recodificados con sfdre.py).")
        return game, notes
    app.auto_profile = auto_profile
    sys.exit(app.main("ct" if "--cab" in sys.argv and sys.argv[sys.argv.index("--cab") + 1] == "ct" else "joy"))


if __name__ == "__main__":
    main()
