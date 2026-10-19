# -*- coding: utf-8 -*-
"""按世界内实际摆放的 14 个件做逐件解析（坐标由结构方块尺寸 + 空档聚类得出）。"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt

BASE = r'E:\mc\mcmod\bettergold-template-1.21.1\docs\金之牢狱-素材清单\金之牢狱'
OUT = os.path.dirname(os.path.abspath(__file__))

# (label, x0, y0, z0, sx, sy, sz, structure_block_position)
PIECES = [
    ('P01', 397, -60, 491, 21, 9, 21, (-116, -61, -22)),
    ('P02', 421, -60, 435, 37, 8, 37, (-92, -61, -78)),
    ('P03', 421, -60, 475, 37, 8, 37, (-92, -61, -38)),
    ('P04', 461, -60, 413, 15, 6, 31, (-52, -61, -100)),
    ('P05', 461, -60, 447, 15, 6, 31, (-52, -61, -66)),
    ('P06', 461, -60, 481, 15, 6, 31, (-52, -61, -32)),
    ('P07', 479, -60, 443, 15, 6, 21, (-34, -61, -70)),
    ('P08', 479, -60, 467, 15, 6, 21, (-34, -61, -46)),
    ('P09', 479, -60, 491, 15, 6, 21, (-34, -61, -22)),
    ('P10', 497, -60, 473, 15, 6, 11, (-16, -61, -40)),
    ('P11', 497, -60, 487, 15, 6, 11, (-16, -61, -26)),
    ('P12', 497, -60, 501, 15, 6, 11, (-16, -61, -12)),
    # 注意：结构与实测位置按"尺寸"配对——5×5×3 在 z501..503，5×8×5 在 z507..511
    ('P13', 3, -60, 501, 5, 5, 3, (2, -61, 500)),   # 间隔过道
    ('P14', 3, -60, 507, 5, 8, 5, (2, -61, 506)),   # 出入口
]

SOLID_IGNORE = {'minecraft:air', 'minecraft:structure_void', 'minecraft:water', 'minecraft:lava'}


def load_all():
    blocks = {}
    bes = []
    for fn in sorted(os.listdir(os.path.join(BASE, 'region'))):
        if not fn.endswith('.mca'):
            continue
        for cx, cz, root, comp in nbt.parse_region(os.path.join(BASE, 'region', fn)):
            for sec in (root.get('sections') or []):
                sy = sec.get('Y', 0)
                for (x, y, z), val in nbt.section_blocks(sec).items():
                    blocks[(cx * 16 + x, sy * 16 + y, cz * 16 + z)] = val
            for be in (root.get('block_entities') or []):
                bes.append(be)
    return blocks, bes


def main():
    blocks, bes = load_all()
    out = []
    for label, x0, y0, z0, sx, sy, sz, sb in PIECES:
        x1, y1, z1 = x0 + sx - 1, y0 + sy - 1, z0 + sz - 1
        sub = {k: v for k, v in blocks.items()
               if x0 <= k[0] <= x1 and y0 <= k[1] <= y1 and z0 <= k[2] <= z1 and v[0] != 'minecraft:air'}
        hist = collections.Counter(v[0] for v in sub.values())
        # 每层方块数
        yh = collections.Counter(k[1] for k in sub)
        # 四面开口（2 格高，相对坐标）
        ops = {}
        for side, zf in (('north', z0), ('south', z1)):
            runs, cur = [], None
            for x in range(x0, x1 + 1):
                ok = all((x, y0 + dy, zf) in sub and sub[(x, y0 + dy, zf)][0] not in SOLID_IGNORE
                         for dy in (1, 2))
                if ok:
                    cur = [x, x] if cur is None else [cur[0], x]
                elif cur:
                    runs.append(cur); cur = None
            if cur:
                runs.append(cur)
            ops[side] = [[a - x0, b - x0] for a, b in runs]
        for side, xf in (('west', x0), ('east', x1)):
            runs, cur = [], None
            for z in range(z0, z1 + 1):
                ok = all((xf, y0 + dy, z) in sub and sub[(xf, y0 + dy, z)][0] not in SOLID_IGNORE
                         for dy in (1, 2))
                if ok:
                    cur = [z, z] if cur is None else [cur[0], z]
                elif cur:
                    runs.append(cur); cur = None
            if cur:
                runs.append(cur)
            ops[side] = [[a - z0, b - z0] for a, b in runs]
        chests = [[k[0] - x0, k[1] - y0, k[2] - z0] for k, v in sub.items() if v[0] in ('minecraft:chest', 'minecraft:barrel')]
        spawners = [[k[0] - x0, k[1] - y0, k[2] - z0] for k, v in sub.items() if v[0] == 'minecraft:mob_spawner']
        fig = [[k[0] - x0, k[1] - y0, k[2] - z0] for k, v in sub.items() if v[0] == 'bettergold:golden_toad_figurine']
        voids = [[k[0] - x0, k[1] - y0, k[2] - z0] for k, v in sub.items() if v[0] == 'minecraft:structure_void']
        doors = [[k[0] - x0, k[1] - y0, k[2] - z0, v[0]] for k, v in sub.items() if 'door' in v[0] or 'gate' in v[0]]
        # 顶层俯视：非空列 + 最高块
        top = {}
        for (x, y, z), v in sub.items():
            top[(x - x0, z - z0)] = max(top.get((x - x0, z - z0), -99), y - y0)
        p = {'label': label, 'origin': [x0, y0, z0], 'size': [sx, sy, sz], 'sb': sb,
             'hist': dict(hist), 'ycount': {str(k - y0): v for k, v in sorted(yh.items())},
             'openings': ops, 'chests': chests, 'spawners': spawners, 'figurines': fig,
             'voids': voids, 'doors': doors, 'block_count': len(sub),
             'top': {'%d,%d' % k: v for k, v in top.items()}}
        out.append(p)
        print('\n==== %s origin=%s size=%s blocks=%d ====' % (label, [x0, y0, z0], [sx, sy, sz], len(sub)))
        print(' hist:', json.dumps(dict(hist), ensure_ascii=False, sort_keys=True))
        print(' ycount:', p['ycount'])
        print(' openings(n/s/w/e):', ops)
        print(' chests:', chests, 'figurines:', fig, 'spawners n=', len(spawners), spawners)
        print(' doors n=', len(doors), ' voids n=', len(voids))
    with open(os.path.join(OUT, 'pieces_grid.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
