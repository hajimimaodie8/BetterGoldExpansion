# -*- coding: utf-8 -*-
"""只读：打印 StructureTemplate.fillFromWorld / placeInWorld 全文（带行号）。"""
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
JAR = r'build\moddev\artifacts\neoforge-21.1.228-sources.jar'
NAME = 'net/minecraft/world/level/levelgen/structure/templatesystem/StructureTemplate.java'
LO, HI = 75, 145
LO2, HI2 = 220, 330
lines = zipfile.ZipFile(JAR).read(NAME).decode('utf-8', 'replace').split('\n')
for lo, hi, label in ((LO, HI, 'fillFromWorld'), (LO2, HI2, 'placeInWorld')):
    print('#### %s  lines %d..%d' % (label, lo, hi))
    for i in range(lo - 1, min(hi, len(lines))):
        print('%5d: %s' % (i + 1, lines[i].rstrip()))
    print()
