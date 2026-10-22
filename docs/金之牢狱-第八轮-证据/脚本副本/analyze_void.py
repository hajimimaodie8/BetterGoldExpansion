# -*- coding: utf-8 -*-
"""只读分析：源存档里 14 个件的 structure_void 分布（逐层平面 + 边界统计）。"""
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'docs\金之牢狱-实现-证据')
import nbt  # noqa: E402
import gp_build as G  # noqa: E402

blocks = G.load_world()
print('world blocks =', len(blocks))

for name, src, x0, y0, z0, sx, sy, sz, note in G.SRC:
    void = []
    solid = []
    air = 0
    for y in range(y0, y0 + sy):
        for z in range(z0, z0 + sz):
            for x in range(x0, x0 + sx):
                v = blocks.get((x, y, z))
                if v is None or v[0] == 'minecraft:air':
                    air += 1
                elif v[0] == 'minecraft:structure_void':
                    void.append((x - x0, y - y0, z - z0))
                else:
                    solid.append((x - x0, y - y0, z - z0))
    print('\n== %s  size=%dx%dx%d  solid=%d air=%d void=%d' % (name, sx, sy, sz, len(solid), air, len(void)))
    if not void:
        continue
    by_y = Counter(v[1] for v in void)
    print('   void per y:', dict(sorted(by_y.items())))
    edge = sum(1 for (x, y, z) in void
               if x in (0, sx - 1) or z in (0, sz - 1) or y in (0, sy - 1))
    print('   void on bbox edge: %d / %d' % (edge, len(void)))
    # 顶层视图（取 void 最多的那一层）
    ysel = by_y.most_common(1)[0][0]
    print('   layer y=%d  (s=void  .=air  #=solid)' % ysel)
    for z in range(sz):
        row = ''
        for x in range(sx):
            if (x, ysel, z) in set(void):
                row += 's'
            elif (x, ysel, z) in set(solid):
                row += '#'
            else:
                row += '.'
        print('     %s' % row)
