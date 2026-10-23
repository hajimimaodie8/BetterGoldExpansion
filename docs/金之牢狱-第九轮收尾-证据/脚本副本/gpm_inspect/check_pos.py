# -*- coding: utf-8 -*-
"""gpm：确认 PoolElementStructurePiece 的 position 与 bbox.min 关系 / calculateRelativePosition 口径。"""
import sys
import zipfile

sys.stdout.reconfigure(errors="replace")
z = zipfile.ZipFile(r"E:\mc\mcmod\bettergold-template-1.21.1\build\moddev\artifacts\neoforge-21.1.228-sources.jar")
for n, keys in [
    ("net/minecraft/world/level/levelgen/structure/PoolElementStructurePiece.java",
     ["PoolElementStructurePiece(", "getPosition()", "makeBoundingBox", "public void move"]),
    ("net/minecraft/world/level/levelgen/structure/templatesystem/StructureTemplate.java",
     ["calculateRelativePosition", "static BlockPos transform"]),
]:
    t = z.read(n).decode("utf-8", "replace")
    lines = t.splitlines()
    print("=====", n)
    for i, line in enumerate(lines):
        if any(k in line for k in keys):
            print("----", i + 1)
            for j in range(max(0, i - 3), min(len(lines), i + 12)):
                print("%5d %s" % (j + 1, lines[j]))
