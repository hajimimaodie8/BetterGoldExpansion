# -*- coding: utf-8 -*-
"""只读分析 3：cross_a 逐层 ASCII（#=solid .=air v=void）+ 与当前 nbt 逐格 diff。"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'docs\金之牢狱-实现-证据')
import nbt  # noqa: E402
import gp_build as G  # noqa: E402

blocks = G.load_world()


def cell(x, y, z):
    v = blocks.get((x, y, z))
    return 'minecraft:air' if v is None else v[0]


def ch(nm):
    if nm == 'minecraft:air':
        return '.'
    if nm == 'minecraft:structure_void':
        return 'v'
    if nm == 'minecraft:jigsaw':
        return 'J'
    return '#'


for name in ('cross_a', 'exit'):
    _, src, x0, y0, z0, sx, sy, sz, note = [s for s in G.SRC if s[0] == name][0]
    print('\n######## %s  %dx%dx%d  origin=(%d,%d,%d)' % (name, sx, sy, sz, x0, y0, z0))
    for y in range(sy):
        print('  --- y=%d%s' % (y, ' (walk)' if y == 1 else ''))
        for z in range(sz):
            print('   ' + ''.join(ch(cell(x0 + x, y0 + y, z0 + z)) for x in range(sx)))

# 当前 nbt 与源存档逐格 diff（cross_a）
RES = r'src\main\resources\data\bettergold\structure\golden_prison'
for name in ('cross_a', 'cross_b'):
    _, src, x0, y0, z0, sx, sy, sz, note = [s for s in G.SRC if s[0] == name][0]
    _, back = nbt.parse_auto(open(os.path.join(RES, name + '.nbt'), 'rb').read())
    pal = back['palette']
    got = {}
    for b in back['blocks']:
        got[tuple(b['pos'])] = pal[b['state']]['Name']
    src_cells = {}
    for y in range(sy):
        for z in range(sz):
            for x in range(sx):
                src_cells[(x, y, z)] = cell(x0 + x, y0 + y, z0 + z)
    diff = [k for k in src_cells if src_cells[k] != got.get(k)]
    print('\n== %s: nbt vs 源存档 逐格 diff = %d 格' % (name, len(diff)))
    kinds = {}
    for k in diff:
        kinds[(src_cells[k], got.get(k))] = kinds.get((src_cells[k], got.get(k)), 0) + 1
    for k, n in sorted(kinds.items()):
        print('   %-28s -> %-28s x%d' % (k[0], k[1], n))
