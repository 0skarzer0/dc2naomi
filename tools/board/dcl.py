#!/usr/bin/env python3
"""dcl.py BASE.bin.gz LOADER.bin IP [FLAGS_OR]: test image = BASE with its loader replaced and extra header flags,
sent to the NetDIMM. Runs ON the Raspberry; working copy in /boot/roms/_test (not listed by WiPi).
Start it with nohup and watch /tmp/dcl.log: "built ..." then "netdimm_send rc 0" (4-5 minutes for 500 MB)."""
import gzip, os, struct, subprocess, sys
base, loader, ip = sys.argv[1:4]
flags_or = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0
os.makedirs("/boot/roms/_test", exist_ok=True)
out = "/boot/roms/_test/test.bin.gz"
new = bytearray(open(loader, "rb").read())
pz = subprocess.Popen(["pigz", "-1", "-c"], stdin=subprocess.PIPE, stdout=open(out, "wb"))
with gzip.open(base, "rb") as f:
    o = pz.stdin
    head = f.read(0x41000)
    so, _, sl = struct.unpack_from("<III", head, 0x360)
    b = (so + sl + 0xffff) & ~0xffff
    so2, _, sl2 = struct.unpack_from("<III", new, 0x360)
    assert ((so2 + sl2 + 0xffff) & ~0xffff) == b == 0x40000, "archive base changed"
    new[0x30:0x130] = head[0x30:0x130]            # the game title
    hdr = bytearray(head[b:b + 0x1000])
    assert struct.unpack_from("<I", hdr, 0)[0] == 0x47434459
    fl = struct.unpack_from("<I", hdr, 16)[0] | flags_or
    struct.pack_into("<I", hdr, 16, fl)
    o.write(bytes(new) + bytes(b - len(new)) + bytes(hdr))
    while True:
        d = f.read(1 << 20)
        if not d: break
        o.write(d)
pz.stdin.close(); pz.wait()
print("built", out, os.path.getsize(out), "flags", hex(fl), flush=True)
os.system("pkill -f timehack.py")
r = subprocess.call(["python3", "/sbin/piforce/dm_netboot/netdimm_send", ip, out, "--disable-crc"])
print("netdimm_send rc", r, flush=True)
# The WiPi keeps the NetDIMM alive with timehack.py (without it the board resets with "error 33 gateway is not found").
subprocess.Popen("nohup python3 /sbin/piforce/timehack.py %s > /dev/null 2>&1 &" % ip, shell=True)
print("timehack.py restarted", flush=True)
