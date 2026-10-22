# -*- coding: utf-8 -*-
"""只读：从 NeoForge sources jar 里抽取与 structure_void / jigsaw 相关的源码行。"""
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
JAR = r'build\moddev\artifacts\neoforge-21.1.228-sources.jar'
TARGETS = {
    'net/minecraft/world/level/levelgen/structure/templatesystem/StructureTemplate.java':
        ('structure_void', 'STRUCTURE_VOID', 'placeInWorld', 'fillFromWorld'),
    'net/minecraft/world/level/levelgen/structure/templatesystem/StructurePlaceSettings.java':
        ('void', 'ignoreEntities'),
    'net/minecraft/world/level/levelgen/structure/pools/JigsawPlacement.java':
        ('maxDepth', 'canAttach'),
}
z = zipfile.ZipFile(JAR)
for name, needles in TARGETS.items():
    txt = z.read(name).decode('utf-8', 'replace')
    lines = txt.split('\n')
    print('#### %s  (%d lines)' % (name.rsplit('/', 1)[-1], len(lines)))
    for i, line in enumerate(lines, 1):
        low = line.lower()
        if any(n.lower() in low for n in needles):
            print('%5d: %s' % (i, line.rstrip()))
    print()
