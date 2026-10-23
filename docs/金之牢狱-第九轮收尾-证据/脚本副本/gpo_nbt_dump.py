# -*- coding: utf-8 -*-
"""读 exit.nbt（只读，不改）：打印 z=0 层逐格状态、被省略（structure_void）的格、air 分布。"""
import gzip
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
b = gzip.open(r"src\main\resources\data\bettergold\structure\golden_prison\exit.nbt", "rb").read()
i = 0


def rd(fmt):
    global i
    v = struct.unpack_from(fmt, b, i)[0]
    i += struct.calcsize(fmt)
    return v


def rstr():
    global i
    n = struct.unpack_from(">H", b, i)[0]
    i += 2
    s = b[i:i + n].decode("utf-8")
    i += n
    return s


def payload(t):
    global i
    if t == 1:
        return rd(">b")
    if t == 2:
        return rd(">h")
    if t == 3:
        return rd(">i")
    if t == 4:
        return rd(">q")
    if t == 5:
        return rd(">f")
    if t == 6:
        return rd(">d")
    if t == 7:
        n = rd(">i")
        v = b[i:i + n]
        i += n
        return v
    if t == 8:
        return rstr()
    if t == 9:
        et = rd(">b")
        n = rd(">i")
        return [payload(et) for _ in range(n)]
    if t == 10:
        d = {}
        while True:
            tt = rd(">b")
            if tt == 0:
                break
            d[rstr()] = payload(tt)
        return d
    if t == 11:
        n = rd(">i")
        return [rd(">i") for _ in range(n)]
    if t == 12:
        n = rd(">i")
        return [rd(">q") for _ in range(n)]
    raise ValueError(t)


t = rd(">b")
rstr()
root = payload(t)
pal = root["palette"]
blocks = root["blocks"]
grid = {}
for bl in blocks:
    grid[tuple(bl["pos"])] = (pal[bl["state"]]["Name"], bl.get("nbt"))
print("blocks", len(blocks), "size", root["size"])
print("z=0 layer (y=1..3):")
for y in range(1, 4):
    print("  y=%d:" % y, [grid.get((x, y, 0), ("OMITTED",))[0] for x in range(5)])
om = [(x, y, z) for x in range(5) for y in range(8) for z in range(5) if (x, y, z) not in grid]
print("omitted", len(om))
lay = {}
for p in om:
    lay[p[1]] = lay.get(p[1], 0) + 1
print("omitted by y", lay)
air = [p for p, v in grid.items() if v[0] in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air")]
print("air", len(air), "by layer", {y: sum(1 for p in air if p[1] == y) for y in range(8)})
print("jigsaw", [(p, v) for p, v in grid.items() if v[0] == "minecraft:jigsaw"])
