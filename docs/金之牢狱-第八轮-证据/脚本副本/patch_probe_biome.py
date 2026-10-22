# -*- coding: utf-8 -*-
"""补回 biomeAt（上一版替换时被一起切掉了）。"""
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'src\main\java\com\hjmmd_8\bettergold\probe\GpjProbe.java'
txt = open(P, 'rb').read().decode('utf-8')
if 'private static String biomeAt(' in txt:
    print('already there')
    sys.exit(0)
anchor = '    private static StructureStart findStartLoose(BlockPos mid, Structure structure) {'
add = '''    private static String biomeAt(BlockPos p) {
        return lvl.getBiome(p).unwrapKey().map(k -> k.location().toString()).orElse("");
    }

'''
txt = txt.replace(anchor, add + anchor, 1)
open(P, 'wb').write(txt.encode('utf-8'))
print('added biomeAt')
