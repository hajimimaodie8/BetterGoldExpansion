# -*- coding: utf-8 -*-
"""gpm：查源码 jar 里 BlockState 的"固体/碰撞体"API。"""
import sys
import zipfile

sys.stdout.reconfigure(errors="replace")
z = zipfile.ZipFile(r"E:\mc\mcmod\bettergold-template-1.21.1\build\moddev\artifacts\neoforge-21.1.228-sources.jar")
for n in ["net/minecraft/world/level/block/state/BlockBehaviour.java",
          "net/minecraft/world/level/block/state/BlockState.java"]:
    if n not in z.namelist():
        print("missing", n)
        continue
    t = z.read(n).decode("utf-8", "replace")
    print("==", n, len(t))
    for line in t.splitlines():
        s = line.strip()
        if "isSolid" in s or "blocksMotion" in s or "public boolean isAir" in s:
            print("   ", s[:180])
