# -*- coding: utf-8 -*-
"""只读：JigsawReplacementProcessor 全文 + 全 jar 里引用它的位置 + processBlockInfos / Palette 里有没有过滤。"""
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
JAR = r'build\moddev\artifacts\neoforge-21.1.228-sources.jar'
TARGET = 'net/minecraft/world/level/levelgen/structure/templatesystem/JigsawReplacementProcessor.java'
z = zipfile.ZipFile(JAR)
print('#### %s' % TARGET.rsplit('/', 1)[-1])
print(z.read(TARGET).decode('utf-8', 'replace'))

print('\n#### 谁引用 JigsawReplacementProcessor')
for info in z.infolist():
    if not info.filename.endswith('.java'):
        continue
    txt = z.read(info).decode('utf-8', 'replace')
    if 'JigsawReplacementProcessor' in txt and not info.filename.endswith('JigsawReplacementProcessor.java'):
        for i, line in enumerate(txt.split('\n'), 1):
            if 'JigsawReplacementProcessor' in line:
                print('%-80s %5d: %s' % (info.filename.replace('net/minecraft/', ''), i, line.strip()))
