# -*- coding: utf-8 -*-
"""gpm：打印 BlockBehaviour 里 isSolid / blocksMotion 的实现上下文。"""
import sys
import zipfile

sys.stdout.reconfigure(errors="replace")
z = zipfile.ZipFile(r"E:\mc\mcmod\bettergold-template-1.21.1\build\moddev\artifacts\neoforge-21.1.228-sources.jar")
t = z.read("net/minecraft/world/level/block/state/BlockBehaviour.java").decode("utf-8", "replace")
lines = t.splitlines()
for i, line in enumerate(lines):
    if "public boolean isSolid()" in line or "public boolean blocksMotion()" in line or "public boolean isAir()" in line:
        print("---- line", i + 1)
        for j in range(max(0, i - 6), min(len(lines), i + 8)):
            print("%5d %s" % (j + 1, lines[j]))
