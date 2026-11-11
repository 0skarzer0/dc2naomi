#!/usr/bin/env python3
"""mkgz.py PROFILE DISC.chd|.gdi OUT.bin.gz: builds a profile of tools/games.py straight to a .bin.gz with
app/loader.bin (the title of the profile written in the NAOMI header), as the Windows program does."""
import gzip, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import build_image  # noqa: E402
import games  # noqa: E402
from dc2naomi import set_title  # noqa: E402

name, src, out = sys.argv[1:4]
game = games.GAMES[name]
image = set_title(open(os.path.join(HERE, "..", "app", "loader.bin"), "rb").read(), game["title"])
with open(out + ".part", "wb") as raw, gzip.GzipFile(filename=os.path.basename(out)[:-3], mode="wb", fileobj=raw,
                                                      compresslevel=6, mtime=0) as gz:
    size = build_image.build(name, game, src, None, image, gz)
os.replace(out + ".part", out)
print(out, size, os.path.getsize(out))
