# -*- coding: utf-8 -*-
"""第九轮：核对关卡 needle 在源码里的出现次数（跑在**去注释源码**上，与关卡同口径）。"""
import io
import os
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
P = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "worldgen", "GoldenPrisonStructure.java")


def strip_comments(s):
    out = []
    i, n = 0, len(s)
    in_block = False
    while i < n:
        if in_block:
            j = s.find("*/", i)
            if j < 0:
                return "".join(out)
            i = j + 2
            in_block = False
            continue
        if s.startswith("/*", i):
            in_block = True
            i += 2
            continue
        if s.startswith("//", i):
            j = s.find("\n", i)
            i = n if j < 0 else j
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


NEEDLES = [
    "extends Structure",
    "public void afterPlace(",
    "JigsawPlacement.addPieces(",
    "MAX_SEARCH = 24",
    "level.setBlock(",
    "allowedCells.contains(",
    "naturalBelow(level, c.pos, oldBox)",
    "usableTerrain(s)",
    "floodAir(level, window, seed, oldAir, MAX_FLOOD_CELLS)",
    "Destination dest = searchDestination(",
    "boxSum(pre, strideX, strideY, i1, j1, k1, i2, j2, k2) != vol",
    "== volShell",
    "if (write(level, c.pos, natural, rec))",
    '"minecraft:air".equals(c.cell.placedBlockId())',
    "overwroteNatural",
    '"notConnected"',
    '"noAir"',
    "protectedCells.contains(",
]

if __name__ == "__main__":
    src = strip_comments(io.open(P, encoding="utf-8").read())
    bad = 0
    for n in NEEDLES:
        c = src.count(n)
        print("%-72s %d" % (n, c))
        if c == 0:
            bad += 1
    print("missing =", bad, "| file bytes =", os.path.getsize(P))
    sys.exit(1 if bad else 0)
