# -*- coding: utf-8 -*-
"""只读：JigsawStructure / Structure 里 maxDistanceFromCenter 的用法。"""
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
JAR = r'build\moddev\artifacts\neoforge-21.1.228-sources.jar'
z = zipfile.ZipFile(JAR)
for name in ('net/minecraft/world/level/levelgen/structure/structures/JigsawStructure.java',
             'net/minecraft/world/level/levelgen/structure/Structure.java'):
    txt = z.read(name).decode('utf-8', 'replace')
    print('#### %s' % name.rsplit('/', 1)[-1])
    for i, line in enumerate(txt.split('\n'), 1):
        if 'maxDistance' in line or 'verifyRange' in line or 'BoundingBox' in line and 'new' in line:
            print('%5d: %s' % (i, line.rstrip()))
    print()
