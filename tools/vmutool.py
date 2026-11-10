#!/usr/bin/env python3
"""vmutool: partidas de Visual Memory (VMU) para los .vmu de dc2naomi (volcado de 128 KB de una VMU).

Uso (también arrastrando ficheros sobre vmutool.exe):
  vmutool JUEGO.vmu                      lista las partidas y las exporta a la carpeta JUEGO_partidas/ (.VMI + .VMS)
  vmutool JUEGO.vmu PARTIDA.vmi          importa la partida (el .VMS va al lado, con el nombre que dice el .VMI);
                                         si en la VMU ya hay un fichero con ese nombre, lo sustituye
  vmutool list JUEGO.vmu
  vmutool export JUEGO.vmu [NOMBRE] [CARPETA]
  vmutool import JUEGO.vmu PARTIDA.vmi [PARTIDA.vms]
  vmutool format JUEGO.vmu               crea una VMU vacía (o borra la que haya)
Opción --batch: no espera a que pulses Enter al terminar.

Formatos: .VMI/.VMS es el de las descargas de partidas (p. ej. github.com/bucanero/dreamcast-saves) y del
navegador web de Dreamcast; el .vmu es la tarjeta entera, como la guardan los emuladores y los scripts de wipi/.
No toques el .vmu de un juego mientras ese juego esté cargado en el mueble: la Raspberry lo sobrescribiría."""
import datetime
import os
import struct
import sys

BLOCK = 512
NBLOCKS = 256
ROOT, FAT, DIR, DIR_N, USER = 255, 254, 253, 13, 200
FREE, END = 0xFFFC, 0xFFFA


def bcd(v):
    return ((v // 10) << 4) | (v % 10)


def unbcd(v):
    return (v >> 4) * 10 + (v & 15)


class Vmu:
    def __init__(self, data=None):
        self.b = bytearray(data) if data else self.blank()
        if len(self.b) != NBLOCKS * BLOCK:
            raise SystemExit("el .vmu tiene que ocupar 131072 bytes (tiene %d)" % len(self.b))
        if self.b[ROOT * BLOCK:ROOT * BLOCK + 16] != b"\x55" * 16:
            raise SystemExit("ese .vmu no está formateado (usa: vmutool format)")

    @staticmethod
    def blank():
        b = bytearray(NBLOCKS * BLOCK)
        r = ROOT * BLOCK
        b[r:r + 16] = b"\x55" * 16
        b[r + 0x10] = 1                                  # custom colour off
        now = datetime.datetime.now()
        b[r + 0x30:r + 0x38] = bytes([bcd(now.year // 100), bcd(now.year % 100), bcd(now.month), bcd(now.day),
                                      bcd(now.hour), bcd(now.minute), bcd(now.second), now.weekday()])
        struct.pack_into("<12H", b, r + 0x40, ROOT, 0, ROOT, FAT, 1, DIR, DIR_N, 0, USER, 31, 0, 0)
        fat = [FREE] * NBLOCKS
        fat[ROOT] = fat[FAT] = END
        for blk in range(DIR, DIR - DIR_N, -1):
            fat[blk] = blk - 1
        fat[DIR - DIR_N + 1] = END
        struct.pack_into("<256H", b, FAT * BLOCK, *fat)
        return b

    def fat(self):
        return list(struct.unpack_from("<256H", self.b, FAT * BLOCK))

    def set_fat(self, fat):
        struct.pack_into("<256H", self.b, FAT * BLOCK, *fat)

    def dir_slots(self):
        """(offset in self.b) of the 32-byte entries, in directory order (block 253 first)."""
        for blk in range(DIR, DIR - DIR_N, -1):
            for i in range(16):
                yield blk * BLOCK + i * 32

    def entries(self):
        out = []
        for off in self.dir_slots():
            e = self.b[off:off + 32]
            if e[0] in (0x33, 0xCC):
                out.append((off, e))
        return out

    def chain(self, first):
        fat, c = self.fat(), [first]
        while fat[c[-1]] not in (END, FREE) and len(c) < NBLOCKS:
            c.append(fat[c[-1]])
        return c

    def find(self, name):
        name = name.upper().encode("ascii", "replace")[:12].ljust(12, b"\0")
        for off, e in self.entries():
            if bytes(e[4:16]).rstrip(b" \0").upper() == name.rstrip(b" \0"):
                return off, e
        return None

    def read(self, e):
        first, size = struct.unpack_from("<H", e, 2)[0], struct.unpack_from("<H", e, 24)[0]
        return b"".join(bytes(self.b[blk * BLOCK:(blk + 1) * BLOCK]) for blk in self.chain(first)[:size])

    def delete(self, off):
        e = self.b[off:off + 32]
        fat = self.fat()
        for blk in self.chain(struct.unpack_from("<H", e, 2)[0]):
            fat[blk] = FREE
        self.set_fat(fat)
        self.b[off:off + 32] = bytes(32)

    def add(self, name, data, game, protect, stamp):
        nblk = (len(data) + BLOCK - 1) // BLOCK
        fat = self.fat()
        free = [blk for blk in range(USER) if fat[blk] == FREE]
        if game:                                          # games: blocks 0.. in a row
            blocks = list(range(nblk))
            if any(fat[blk] != FREE for blk in blocks):
                raise SystemExit("no hay sitio para un minijuego: los bloques del principio están ocupados")
        else:                                             # data: from block 199 down
            if len(free) < nblk:
                raise SystemExit("no cabe: hacen falta %d bloques y quedan %d libres" % (nblk, len(free)))
            blocks = sorted(free, reverse=True)[:nblk]
        for a, b2 in zip(blocks, blocks[1:]):
            fat[a] = b2
        fat[blocks[-1]] = END
        data = data + bytes(nblk * BLOCK - len(data))
        for i, blk in enumerate(blocks):
            self.b[blk * BLOCK:(blk + 1) * BLOCK] = data[i * BLOCK:(i + 1) * BLOCK]
        slot = next((o for o in self.dir_slots() if self.b[o] == 0), None)
        if slot is None:
            raise SystemExit("el directorio de la VMU está lleno")
        e = bytearray(32)
        e[0] = 0xCC if game else 0x33
        e[1] = 0xFF if protect else 0x00
        struct.pack_into("<H", e, 2, blocks[0])
        e[4:16] = name.encode("ascii", "replace")[:12].ljust(12, b"\0")
        e[16:24] = stamp
        struct.pack_into("<HH", e, 24, nblk, 1 if game else 0)
        self.b[slot:slot + 32] = e
        self.set_fat(fat)

    def free_blocks(self):
        fat = self.fat()
        return sum(1 for blk in range(USER) if fat[blk] == FREE)


def stamp_of(e):
    s = e[16:24]
    try:
        return "%02d%02d-%02d-%02d %02d:%02d" % tuple(unbcd(x) for x in s[:6])
    except Exception:
        return "?"


def cmd_list(path):
    v = Vmu(open(path, "rb").read())
    print("%s: %d bloques libres de %d" % (os.path.basename(path), v.free_blocks(), USER))
    for _, e in v.entries():
        print("  %-12s %3d bloques  %s  %s" % (bytes(e[4:16]).rstrip(b"\0").decode("ascii", "replace"),
                                                struct.unpack_from("<H", e, 24)[0],
                                                "minijuego" if e[0] == 0xCC else "datos", stamp_of(e)))
    return v


def cmd_export(path, name=None, folder=None):
    v = Vmu(open(path, "rb").read())
    folder = folder or os.path.splitext(path)[0] + "_partidas"
    os.makedirs(folder, exist_ok=True)
    done = 0
    for _, e in v.entries():
        fname = bytes(e[4:16]).rstrip(b"\0").decode("ascii", "replace")
        if name and fname.upper() != name.upper():
            continue
        data = v.read(e)
        res = "".join(c for c in fname if c.isalnum())[:8] or "partida"
        vmi = bytearray(108)
        vmi[0:4] = bytes(a ^ b for a, b in zip(res.encode("ascii")[:4].ljust(4, b"\0"), b"SEGA"))
        desc = data[0x10:0x30] if e[0] == 0x33 else data[BLOCK + 0x10:BLOCK + 0x30]
        vmi[4:36] = desc.split(b"\0")[0][:32].ljust(32, b"\0")
        vmi[36:68] = b"dc2naomi vmutool".ljust(32, b"\0")
        s = e[16:24]
        struct.pack_into("<H", vmi, 68, unbcd(s[0]) * 100 + unbcd(s[1]))
        vmi[70:76] = bytes([unbcd(s[2]), unbcd(s[3]), unbcd(s[4]), unbcd(s[5]), unbcd(s[6]), s[7]])
        struct.pack_into("<HH", vmi, 76, 0, 1)
        vmi[80:88] = res.encode("ascii").ljust(8, b"\0")
        vmi[88:100] = e[4:16]
        struct.pack_into("<HH", vmi, 100, (2 if e[0] == 0xCC else 0) | (1 if e[1] == 0xFF else 0), 0)
        struct.pack_into("<I", vmi, 104, len(data))
        open(os.path.join(folder, res + ".VMI"), "wb").write(vmi)
        open(os.path.join(folder, res + ".VMS"), "wb").write(data)
        print("  exportado %s -> %s.VMI + %s.VMS" % (fname, res, res))
        done += 1
    if not done:
        print("  no hay partidas que exportar")
    else:
        print("en %s" % folder)


def cmd_import(path, vmi_path, vms_path=None):
    vmi = open(vmi_path, "rb").read()
    if len(vmi) < 108:
        raise SystemExit("%s no parece un .VMI (tiene que ocupar 108 bytes)" % vmi_path)
    res = vmi[80:88].split(b"\0")[0].decode("ascii", "replace")
    name = vmi[88:100].split(b"\0")[0].decode("ascii", "replace")
    mode, size = struct.unpack_from("<H", vmi, 100)[0], struct.unpack_from("<I", vmi, 104)[0]
    if not vms_path:
        folder = os.path.dirname(os.path.abspath(vmi_path))
        cands = [f for f in os.listdir(folder) if f.upper() == (res + ".VMS").upper()]
        if not cands:
            raise SystemExit("no encuentro %s.VMS junto al .VMI" % res)
        vms_path = os.path.join(folder, cands[0])
    data = open(vms_path, "rb").read()
    if size and len(data) != size:
        print("aviso: el .VMI dice %d bytes y el .VMS tiene %d" % (size, len(data)))
    y = struct.unpack_from("<H", vmi, 68)[0]
    mo, d, h, mi, s, wd = vmi[70:76]
    stamp = bytes([bcd(y // 100), bcd(y % 100), bcd(mo), bcd(d), bcd(h), bcd(mi), bcd(s), wd])
    if os.path.exists(path):
        v = Vmu(open(path, "rb").read())
    else:
        v = Vmu()
    old = v.find(name)
    if old:
        bak = path + ".bak"
        open(bak, "wb").write(bytes(v.b))
        v.delete(old[0])
        print("sustituyo %s (copia de la VMU anterior en %s)" % (name, os.path.basename(bak)))
    v.add(name, data, bool(mode & 2), bool(mode & 1), stamp)
    open(path, "wb").write(bytes(v.b))
    print("importado %s (%d bloques) en %s" % (name, (len(data) + BLOCK - 1) // BLOCK, os.path.basename(path)))
    cmd_list(path)


def cmd_format(path):
    open(path, "wb").write(bytes(Vmu().b))
    print("VMU vacía en %s (%d bloques libres)" % (path, USER))


def main(argv):
    batch = "--batch" in argv
    args = [a for a in argv if a != "--batch"]
    try:
        if not args:
            print(__doc__)
        elif args[0] == "list":
            cmd_list(args[1])
        elif args[0] == "export":
            cmd_export(args[1], *(args[2:4]))
        elif args[0] == "import":
            cmd_import(args[1], args[2], args[3] if len(args) > 3 else None)
        elif args[0] == "format":
            cmd_format(args[1])
        else:                                             # drag and drop
            vmus = [a for a in args if a.lower().endswith((".vmu", ".bin"))]
            vmis = [a for a in args if a.lower().endswith(".vmi")]
            if len(vmus) != 1:
                raise SystemExit("arrastra un .vmu (y, para importar, también el .VMI de la partida)")
            if vmis:
                for f in vmis:
                    cmd_import(vmus[0], f)
            else:
                cmd_list(vmus[0])
                cmd_export(vmus[0])
    except SystemExit as e:
        if e.code not in (None, 0):
            print("ERROR: %s" % e.code)
    if not batch and getattr(sys, "frozen", False):
        input("\nPulsa Enter para cerrar...")


if __name__ == "__main__":
    main(sys.argv[1:])
