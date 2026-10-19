# -*- coding: utf-8 -*-
"""修正版开口统计：structure_void 视为"不可通行"，并打印每个开口中心列的竖向剖面。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_grid

OUT = os.path.dirname(os.path.abspath(__file__))
AIR = {'minecraft:air', 'minecraft:water', 'minecraft:lava'}
VOID = 'minecraft:structure_void'


def main():
    blocks, bes = analyze_grid.load_all()
    out = {}
    for label, x0, y0, z0, sx, sy, sz, sb in analyze_grid.PIECES:
        x1, y1, z1 = x0 + sx - 1, y0 + sy - 1, z0 + sz - 1
        w = sx if sx < sz else sz
        c = (w - 1) // 2
        info = {'size': [sx, sy, sz], 'center': c, 'faces': {}}
        for side in ('north', 'south', 'west', 'east'):
            if side == 'north':
                fx, fz, ixx, izz = c, 0, 0, 1
            elif side == 'south':
                fx, fz, ixx, izz = c, sz - 1, 0, -1
            elif side == 'west':
                fx, fz, ixx, izz = 0, c, 1, 0
            else:
                fx, fz, ixx, izz = sx - 1, c, -1, 0
            prof = []
            for dy in range(sy):
                b = blocks.get((x0 + fx, y0 + dy, z0 + fz))
                bi = blocks.get((x0 + fx + ixx, y0 + dy, z0 + fz + izz))
                prof.append((dy,
                             b[0].replace('minecraft:', '').replace('bettergold:', '') if b else 'air',
                             'air' if (bi is None or bi[0] in AIR) else ('void' if bi[0] == VOID else 'solid')))
            passable = [p[0] for p in prof if p[1] == 'air' and p[2] == 'air']
            info['faces'][side] = {'profile': prof, 'passable_dy': passable}
        out[label] = info
        print('\n%s %s center=%d' % (label, (sx, sy, sz), c))
        for side, d in info['faces'].items():
            print('  %-5s passable_dy=%s  profile=%s' % (side, d['passable_dy'],
                  ' '.join('%d:%s/%s' % p for p in d['profile'])))
    with open(os.path.join(OUT, 'faces2.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
