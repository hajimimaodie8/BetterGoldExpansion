# -*- coding: utf-8 -*-
"""gpm：确认 WorldGenRegion.getChunk(x,z,status,require) 的返回语义。"""
import sys
import zipfile

sys.stdout.reconfigure(errors="replace")
z = zipfile.ZipFile(r"E:\mc\mcmod\bettergold-template-1.21.1\build\moddev\artifacts\neoforge-21.1.228-sources.jar")
t = z.read("net/minecraft/server/level/WorldGenRegion.java").decode("utf-8", "replace")
lines = t.splitlines()
for i, line in enumerate(lines):
    if "getChunk(int" in line and "ChunkStatus" in line:
        print("----", i + 1)
        for j in range(max(0, i - 3), min(len(lines), i + 18)):
            print("%5d %s" % (j + 1, lines[j]))
