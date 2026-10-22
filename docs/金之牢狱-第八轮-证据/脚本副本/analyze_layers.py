# -*- coding: utf-8 -*-
"""只读分析 2：每件的真实（solid 最小包围盒）尺寸 vs SRC 包围盒；逐层 solid/air/void 计数。"""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'docs\金之牢狱-实现-证据')
import gp_build as G  # noqa: E402

blocks = G.load_world()

for name, src, x0, y0, z0, sx, sy, sz, note in G.SRC:
    cells = {}
    for y in range(y0, y0 + sy):
        for z in range(z0, z0 + sz):
            for x in range(x0, x0 + sx):
                v = blocks.get((x, y, z))
                nm = 'minecraft:air' if v is None else v[0]
                cells[(x - x0, y - y0, z - z0)] = nm
    solid = [(x, y, z) for (x, y, z), nm in cells.items()
             if nm not in ('minecraft:air', 'minecraft:structure_void')]
    if solid:
        mnx, mny, mnz = min(s[0] for s in solid), min(s[1] for s in solid), min(s[2] for s in solid)
        mxx, mxy, mxz = max(s[0] for s in solid), max(s[1] for s in solid), max(s[2] for s in solid)
    else:
        mnx = mny = mnz = mxx = mxy = mxz = -1
    print('\n== %-20s SRC bbox %dx%dx%d  solid-bbox x%d..%d y%d..%d z%d..%d  (%dx%dx%d)' % (
        name, sx, sy, sz, mnx, mxx, mny, mxy, mnz, mxz,
        mxx - mnx + 1, mxy - mny + 1, mxz - mnz + 1))
    for y in range(sy):
        c = Counter(cells[(x, y, z)] for x in range(sx) for z in range(sz))
        s = sum(v for k, v in c.items() if k not in ('minecraft:air', 'minecraft:structure_void'))
        a = c.get('minecraft:air', 0)
        vd = c.get('minecraft:structure_void', 0)
        print('   y=%d  solid=%4d air=%4d void=%4d' % (y, s, a, vd))
