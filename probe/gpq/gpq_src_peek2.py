# -*- coding: utf-8 -*-
"""看 LootItem / LootPoolEntryContainer / LootPool 的字段与采样入口（决定探针的读法）。"""
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
JAR = r"build\moddev\artifacts\neoforge-21.1.228-sources.jar"
z = zipfile.ZipFile(JAR)
for name, lo, hi in (
        ("net/minecraft/world/level/storage/loot/entries/LootItem.java", 1, 90),
        ("net/minecraft/world/level/storage/loot/entries/LootPoolEntryContainer.java", 1, 60),
        ("net/minecraft/world/level/storage/loot/LootTable.java", 55, 120),
):
    t = z.read(name).decode("utf-8", "replace").splitlines()
    print("=" * 30, name, len(t), "lines")
    for i in range(lo, min(hi, len(t)) + 1):
        print("%4d %s" % (i, t[i - 1]))
