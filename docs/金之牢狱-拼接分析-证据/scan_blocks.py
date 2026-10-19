# -*- coding: utf-8 -*-
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt

BASE = r'E:\mc\mcmod\bettergold-template-1.21.1\docs\金之牢狱-素材清单\金之牢狱'
OUT = os.path.dirname(os.path.abspath(__file__))


def main():
    level = nbt.parse_auto(open(os.path.join(BASE, 'level.dat'), 'rb').read())[1]
    d = level.get('Data', {})
    print('LevelName      :', d.get('LevelName'))
    print('DataVersion    :', d.get('DataVersion'))
    print('Version        :', d.get('Version'))
    print('Spawn          :', d.get('SpawnX'), d.get('SpawnY'), d.get('SpawnZ'))
    print('LastPlayed     :', d.get('LastPlayed'))
    wg = d.get('WorldGenSettings') or {}
    print('WGS seed/type  :', wg.get('seed'), wg.get('generate_features'), wg.get('bonus_chest'))
    dims = wg.get('dimensions') or {}
    print('WGS dimensions :', {k: (v.get('type') if isinstance(v, dict) else v) for k, v in dims.items()})
    print('GameRules      :', d.get('GameRules'))

    hist = collections.Counter()
    interesting = collections.defaultdict(list)
    chunk_bounds = []
    total_nonair = 0
    chunks = 0
    for fn in sorted(os.listdir(os.path.join(BASE, 'region'))):
        if not fn.endswith('.mca'):
            continue
        p = os.path.join(BASE, 'region', fn)
        for cx, cz, root, comp in nbt.parse_region(p):
            chunks += 1
            minp = [10 ** 9] * 3
            maxp = [-10 ** 9] * 3
            cnt = 0
            for sec in (root.get('sections') or []):
                sy = sec.get('Y', 0)
                blocks = nbt.section_blocks(sec)
                for (x, y, z), (nm, pr) in blocks.items():
                    wx, wy, wz = cx * 16 + x, sy * 16 + y, cz * 16 + z
                    cnt += 1
                    hist[nm] += 1
                    for i, v in enumerate((wx, wy, wz)):
                        minp[i] = min(minp[i], v)
                        maxp[i] = max(maxp[i], v)
                    if nm in ('minecraft:jigsaw', 'minecraft:structure_block', 'minecraft:chest',
                              'minecraft:barrel', 'minecraft:trapped_chest', 'minecraft:frogspawn',
                              'minecraft:frog') or 'gold' in nm or 'shulker' in nm or 'spawner' in nm:
                        interesting[nm].append((wx, wy, wz, dict(pr)))
            total_nonair += cnt
            chunk_bounds.append((fn, cx, cz, cnt, minp, maxp,
                                 len(root.get('block_entities') or []), len(root.get('Entities') or [])))
    print('\nchunks', chunks, 'nonair', total_nonair)
    print('\n== block histogram ==')
    for nm, c in hist.most_common():
        print('%7d  %s' % (c, nm))
    print('\n== interesting blocks ==')
    for nm, lst in sorted(interesting.items()):
        print(nm, len(lst))
        for e in lst[:200]:
            print('   ', e)
    with open(os.path.join(OUT, 'blocks_scan.json'), 'w', encoding='utf-8') as f:
        json.dump({'hist': dict(hist), 'interesting': {k: v for k, v in interesting.items()},
                   'chunks': chunk_bounds}, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
