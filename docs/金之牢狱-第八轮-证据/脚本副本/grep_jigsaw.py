# -*- coding: utf-8 -*-
"""只读：JigsawPlacement 的距离/边界判定（用于写准确的关卡断言）。"""
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
JAR = r'build\moddev\artifacts\neoforge-21.1.228-sources.jar'
NAME = 'net/minecraft/world/level/levelgen/structure/pools/JigsawPlacement.java'
lines = zipfile.ZipFile(JAR).read(NAME).decode('utf-8', 'replace').split('\n')
for i in range(330, 500):
    if i - 1 < len(lines):
        print('%5d: %s' % (i, lines[i - 1].rstrip()))
