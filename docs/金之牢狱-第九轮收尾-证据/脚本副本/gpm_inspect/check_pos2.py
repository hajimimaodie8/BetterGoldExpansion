# -*- coding: utf-8 -*-
"""gpm：打印 transform / getBoundingBox 的口径。"""
import sys
import zipfile

sys.stdout.reconfigure(errors="replace")
z = zipfile.ZipFile(r"E:\mc\mcmod\bettergold-template-1.21.1\build\moddev\artifacts\neoforge-21.1.228-sources.jar")
for n in ["net/minecraft/world/level/levelgen/structure/templatesystem/StructureTemplate.java",
          "net/minecraft/world/level/levelgen/structure/pools/StructurePoolElement.java",
          "net/minecraft/world/level/levelgen/structure/templatesystem/StructurePlaceSettings.java"]:
    t = z.read(n).decode("utf-8", "replace")
    lines = t.splitlines()
    print("=====", n)
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("private static BlockPos transform") or s.startswith("public BoundingBox getBoundingBox") \
                or s.startswith("public BlockPos getRotationPivot") or s.startswith("public StructurePlaceSettings setRotationPivot") \
                or "rotationPivot" in s and "=" in s and "private" in s:
            print("----", i + 1)
            for j in range(max(0, i - 2), min(len(lines), i + 28)):
                print("%5d %s" % (j + 1, lines[j]))
