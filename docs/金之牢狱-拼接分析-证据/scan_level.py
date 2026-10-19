# -*- coding: utf-8 -*-
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt

BASE = r'E:\mc\mcmod\bettergold-template-1.21.1\docs\金之牢狱-素材清单\金之牢狱'


def main():
    level = nbt.parse_auto(open(os.path.join(BASE, 'level.dat'), 'rb').read())[1]
    data = level.get('Data', {})
    print('== level.dat ==')
    for k in ('LevelName', 'DataVersion', 'Version', 'WorldGenSettings', 'SpawnX', 'SpawnY', 'SpawnZ',
              'LastPlayed', 'Time', 'DayTime', 'raining', 'difficulty'):
        v = data.get(k)
        if k == 'WorldGenSettings':
            print(k, ':', {kk: vv for kk, vv in v.items() if kk in ('seed', 'generate_features', 'bonus_chest')} if isinstance(v, dict) else v)
        else:
            print(k, ':', v)

    print('\n== region files ==')
    for fn in sorted(os.listdir(os.path.join(BASE, 'region'))):
        if not fn.endswith('.mca'):
            continue
        p = os.path.join(BASE, 'region', fn)
        n = 0
        for cx, cz, root, comp in nbt.parse_region(p):
            n += 1
            print(fn, 'chunk', cx, cz, 'dataver', root.get('DataVersion'), 'status', root.get('Status'),
                  'sections', len(root.get('sections') or []), 'bes', len(root.get('block_entities') or []),
                  'entities', len(root.get('Entities') or []), 'structures', bool(root.get('structures')),
                  'comp', comp)
        print(fn, 'chunks', n)


if __name__ == '__main__':
    main()
