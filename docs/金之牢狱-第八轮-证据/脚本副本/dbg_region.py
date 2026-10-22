# -*- coding: utf-8 -*-
"""只读调试：验证 validate_golden_prison 里的 region 读取 + 结构空位集合。"""
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'tools\asset-generator')
import validate_golden_prison as V

cells = V.load_world_cells((421, -60, 435, 457, -53, 471))
print('cross_a box cells =', len(cells))
for p in [(421, -54, 435), (421, -53, 435), (421, -60, 435)]:
    print(p, '->', cells.get(p))

for name in ('cross_a', 'cross_b', 'exit', 'treasure', 'cell_small_a', 'cell_small_mirror'):
    print('%-20s void=%d' % (name, len(V.source_void_cells(name))))
