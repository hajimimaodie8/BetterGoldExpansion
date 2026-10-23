# -*- coding: utf-8 -*-
"""读 sources jar 里 LootTable / LootPool 的字段与可见性（决定探针怎么读条目）。"""
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
JAR = r"build\moddev\artifacts\neoforge-21.1.228-sources.jar"
z = zipfile.ZipFile(JAR)
for name in ("net/minecraft/world/level/storage/loot/LootTable.java",
             "net/minecraft/world/level/storage/loot/LootPool.java",
             "net/minecraft/world/level/storage/loot/entries/LootPoolEntryContainer.java",
             "net/minecraft/world/level/storage/loot/entries/LootItem.java"):
    try:
        t = z.read(name).decode("utf-8", "replace")
    except KeyError:
        print("!! not in jar:", name)
        continue
    print("=" * 30, name)
    for i, line in enumerate(t.splitlines(), 1):
        if re.search(r"^\s*(public|private|protected)?\s*(final\s+)?(List<.*>|ResourceKey|lootTableId|int|float)\s+\w+;", line) \
                or "public List<LootPool>" in line or "class LootTable" in line or "class LootPool" in line \
                or "public LootTable" in line or "LootPoolEntryContainer" in line:
            print(i, line.strip()[:150])
