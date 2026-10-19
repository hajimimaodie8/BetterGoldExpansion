# -*- coding: utf-8 -*-
"""同尺寸件之间的结构差异（忽略装饰性随机块），判断"三种"是真三种还是复制件。"""
import json
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_grid

OUT = os.path.dirname(os.path.abspath(__file__))
DECO = {'minecraft:nether_gold_ore', 'bettergold:gold_chain', 'minecraft:gold_block',
        'bettergold:golden_rose_bush', 'bettergold:golden_toad_figurine',
        'bettergold:golden_wheat_crop', 'bettergold:golden_carrot_crop',
        'bettergold:golden_eggplant_crop', 'minecraft:chest', 'minecraft:spawner',
        'minecraft:raw_gold_block', 'bettergold:gold_infused_dirt', 'bettergold:gold_infused_farmland',
        'minecraft:yellow_stained_glass', 'minecraft:ancient_debris'}


def grid(blocks, box, drop_deco=True):
    x0, y0, z0, sx, sy, sz = box
    g = {}
    for dx in range(sx):
        for dy in range(sy):
            for dz in range(sz):
                v = blocks.get((x0 + dx, y0 + dy, z0 + dz))
                if not v or v[0] == 'minecraft:air':
                    continue
                if drop_deco and v[0] in DECO:
                    continue
                g[(dx, dy, dz)] = v[0] + '|' + ','.join('%s=%s' % kv for kv in sorted(v[1].items()))
    return g


def diff(a, b):
    keys = set(a) | set(b)
    d = [k for k in keys if a.get(k) != b.get(k)]
    return d


def main():
    blocks, bes = analyze_grid.load_all()
    boxes = {p[0]: (p[1], p[2], p[3], p[4], p[5], p[6]) for p in analyze_grid.PIECES}
    groups = [['P04', 'P05', 'P06'], ['P07', 'P08', 'P09'], ['P10', 'P11', 'P12'], ['P02', 'P03']]
    for g in groups:
        print('\n### group', g)
        gs = {k: grid(blocks, boxes[k]) for k in g}
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                d = diff(gs[g[i]], gs[g[j]])
                print('  %s vs %s : %d/%d cells differ (非装饰)' % (g[i], g[j], len(d), len(set(gs[g[i]]) | set(gs[g[j]]))))
                if d and len(d) <= 40:
                    for k in sorted(d)[:40]:
                        print('     ', k, gs[g[i]].get(k), '->', gs[g[j]].get(k))
    # 全件两两：结构骨架相同？
    print('\n### 全部同尺寸骨架指纹')
    fp = collections.defaultdict(list)
    for p in analyze_grid.PIECES:
        k = (p[4], p[5], p[6])
        g = grid(blocks, (p[1], p[2], p[3], p[4], p[5], p[6]))
        h = hash(tuple(sorted(g.items())))
        fp[k].append((p[0], len(g), h))
    print(json.dumps({str(k): v for k, v in fp.items()}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
