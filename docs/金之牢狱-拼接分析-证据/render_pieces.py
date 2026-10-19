# -*- coding: utf-8 -*-
"""把每个件渲染成字符平面图（俯视/剖面），用于人眼判断房间与开口。"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt
import analyze_grid

BASE = r'E:\mc\mcmod\bettergold-template-1.21.1\docs\金之牢狱-素材清单\金之牢狱'
OUT = os.path.dirname(os.path.abspath(__file__))

CHAR = {
    'minecraft:air': '.',
    'minecraft:structure_void': 'v',
    'bettergold:gold_bricks': '#',
    'bettergold:gold_bricks_slab': '_',
    'bettergold:gold_bricks_stairs': '/',
    'bettergold:gold_bricks_wall': '=',
    'bettergold:gold_pillar': '|',
    'bettergold:gold_chain': 'c',
    'bettergold:gold_bars': 'b',
    'bettergold:gold_trapdoor': 't',
    'minecraft:chest': 'C',
    'minecraft:barrel': 'B',
    'minecraft:spawner': 'S',
    'bettergold:golden_toad_figurine': 'F',
    'minecraft:nether_gold_ore': 'o',
    'minecraft:raw_gold_block': 'r',
    'minecraft:gold_block': 'G',
    'minecraft:ancient_debris': 'A',
    'minecraft:yellow_stained_glass': 'y',
    'bettergold:gold_infused_dirt': 'd',
    'bettergold:gold_infused_farmland': 'f',
    'bettergold:golden_wheat_crop': 'w',
    'bettergold:golden_carrot_crop': 'k',
    'bettergold:golden_eggplant_crop': 'e',
    'bettergold:golden_rose_bush': 'R',
    'minecraft:bamboo_sign': 'N',
}


def ch(v):
    return CHAR.get(v[0], '?')


def main():
    blocks, bes = analyze_grid.load_all()
    lines = []
    for label, x0, y0, z0, sx, sy, sz, sb in analyze_grid.PIECES:
        lines.append('\n' + '=' * 90)
        lines.append('%s  origin=%s size=%s' % (label, (x0, y0, z0), (sx, sy, sz)))
        for dy in range(sy):
            y = y0 + dy
            lines.append('\n-- %s  y=%d (dy=%d) --' % (label, y, dy))
            for dz in range(sz):
                row = []
                for dx in range(sx):
                    v = blocks.get((x0 + dx, y, z0 + dz))
                    row.append(ch(v) if v else '.')
                lines.append('%3d %s' % (dz, ''.join(row)))
    with open(os.path.join(OUT, 'pieces_maps.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('wrote', len(lines), 'lines')


if __name__ == '__main__':
    main()
