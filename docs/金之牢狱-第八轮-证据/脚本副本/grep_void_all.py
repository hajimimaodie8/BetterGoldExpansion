# -*- coding: utf-8 -*-
"""只读：全 sources jar 搜 STRUCTURE_VOID / structure_void 的所有引用；并打印 StructureVoidBlock。"""
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
JAR = r'build\moddev\artifacts\neoforge-21.1.228-sources.jar'
z = zipfile.ZipFile(JAR)
hits = []
for info in z.infolist():
    if not info.filename.endswith(('.java', '.json')):
        continue
    try:
        txt = z.read(info).decode('utf-8', 'replace')
    except Exception:
        continue
    if 'STRUCTURE_VOID' in txt or 'structure_void' in txt:
        for i, line in enumerate(txt.split('\n'), 1):
            if 'STRUCTURE_VOID' in line or 'structure_void' in line:
                hits.append((info.filename, i, line.strip()))
print('total hits =', len(hits))
for fn, i, line in hits:
    print('%-95s %5d: %s' % (fn.replace('net/minecraft/', ''), i, line))

print('\n#### StructureVoidBlock')
for info in z.infolist():
    if info.filename.endswith('StructureVoidBlock.java'):
        print(z.read(info).decode('utf-8', 'replace'))
