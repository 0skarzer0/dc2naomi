#!/usr/bin/env python3
"""drive.py IMAGE NAME STEPS... : Flycast (NAOMI 1, headless) driven by what is on screen.

Steps (in order):
  menu            hold START until the screen turns dark (the game menu)
  key:K[:HOLD]    press key K (xdotool name) for HOLD seconds
  hold:K:SECS     keep K pressed in the background for SECS seconds
  wait:SECS       wait
  shot            add a screenshot to the grid
  dump            dump the 32 MB of RAM to /tmp/ram.bin
Screenshots also every 4 s while waiting. Grid -> NAME.png, log -> NAME.log.
"""
import os
import subprocess
import sys
import time

from PIL import Image, ImageStat

FC = os.environ.get("FCBIN", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../flycast/build/flycast"))
HERE = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, DISPLAY=":99", SDL_AUDIODRIVER="dummy", LIBGL_ALWAYS_SOFTWARE="1",
           HOME=os.path.join(HERE, "home"))
env.pop("FC_NAOMI2", None)
env.pop("FC_MIE_NODEVINFO", None)

img, name, steps = sys.argv[1], sys.argv[2], sys.argv[3:]
if subprocess.run(["pgrep", "-x", "Xvfb"], capture_output=True).returncode:
    subprocess.Popen(["Xvfb", ":99", "-screen", "0", "800x600x24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
for f in os.listdir(os.path.join(HERE, "home/.local/share/flycast")):
    if f.endswith(".nvmem"):
        os.remove(os.path.join(HERE, "home/.local/share/flycast", f))
log = open(os.path.join(HERE, name + ".log"), "w")
fp = subprocess.Popen([FC, "-config", "log:LogToConsole=yes", img], env=env, stdout=log, stderr=subprocess.STDOUT)
t0 = time.time()
shots = []


def grab(keep=True):
    p = f"/tmp/{name}_{len(shots):03d}.png"
    subprocess.run(["import", "-window", "root", "-resize", "320x240", p], env=env, capture_output=True)
    if keep:
        shots.append(p)
    return p


def bright(p):
    im = Image.open(p).convert("L").crop((40, 30, 280, 210))
    return ImageStat.Stat(im).mean[0]


def key(k, hold=0.2):
    subprocess.run(["xdotool", "keydown", k], env=env)
    time.sleep(hold)
    subprocess.run(["xdotool", "keyup", k], env=env)


def wait(secs):
    end = time.time() + secs
    nxt = time.time()
    while time.time() < end:
        if time.time() >= nxt:
            grab()
            nxt += 4
        time.sleep(0.2)


for st in steps:
    p = st.split(":")
    if p[0] == "menu":
        ok = False
        for _ in range(60):
            time.sleep(2)
            b = bright(grab(False))
            if b < 90 and time.time() - t0 > 20:  # menu: dark; logos and title: white
                ok = True
                break
            if time.time() - t0 > 25:
                key("Return", 1.0)
        grab()
        print(f"menu {'reached' if ok else 'NOT reached'} at {time.time() - t0:.0f}s")
    elif p[0] == "key":
        key(p[1], float(p[2]) if len(p) > 2 else 0.2)
    elif p[0] == "hold":
        subprocess.Popen(f"xdotool keydown {p[1]}; sleep {p[2]}; xdotool keyup {p[1]}", shell=True, env=env)
    elif p[0] == "wait":
        wait(float(p[1]))
    elif p[0] == "shot":
        grab()
    elif p[0] == "dump":
        os.environ["DN"] = p[1] if len(p) > 1 else ""
        ram = [l for l in open(os.path.join(HERE, name + ".log")) if "RAM(32 MB)" in l][0].split("RAM(32 MB) ")[1].split()[0]
        subprocess.run(["gdb", "-p", str(fp.pid), "-batch", "-ex",
                        f"dump binary memory /tmp/ram{os.environ.get("DN","")}.bin {ram} {ram}+0x2000000"], capture_output=True)
fp.kill()
subprocess.run(["montage"] + shots + ["-tile", "4x", "-geometry", "+2+2", os.path.join(HERE, name + ".png")])
print(f"{len(shots)} shots, {time.time() - t0:.0f}s")
