# -*- coding: utf-8 -*-
"""阶段 B-4：从探针 dump 算 A 级读数（不跑游戏，纯离线复算）。

输入：`docs\\金之牢狱-生成预览\\_raw\\{meta.json, blocks.tsv}`（GpPreviewProbe 在 runServer 里 dump）
输出：`docs\\金之牢狱-生成预览-证据\\gp_world_check.json` + 终端表

读的东西（全部都能在 dump 里逐格复算）：
  1) 件数 / 模板 / 宝藏房唯一性 / 出入口数 / 起点 Y / 行走面 / 包围盒重叠 / BFS 深度
  2) 每个口的**门洞 3x3x1**：口平面那 9 格 + 口内一层 9 格，逐格列（不是只验 jigsaw 那 1 格）
  3) ★ **真实可站格洪泛**：从宝藏房出发（站得住 = 该格空气 + 正上方空气 + 脚下一格实心），
     6 邻接，必须到**每个出入口**；逐箱检查「箱子旁边有可站格」。
  4) 件内空气占比 / 行走层空气占比（对照上一轮 4.10% / 5.73%）
"""
import argparse
import json
import sys
from collections import deque
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
AIRNAMES = ('minecraft:air', 'minecraft:cave_air', 'minecraft:void_air')
VOIDNAME = 'minecraft:structure_void'


def load(inp):
    """严格口径：dump 里有行的格子 = 有方块（structure_void 也算「有方块」，
    与修前文档的 4.10% 同一口径）；只有 blocks.tsv 里完全没有的格子才算空。

    另返回 voids 集合：structure_void 没有碰撞、玩家能穿过，所以洪泛里当「可通行」但不算空。
    """
    meta = json.loads((inp / 'meta.json').read_text(encoding='utf-8'))
    blocks, voids = set(), set()
    for line in (inp / 'blocks.tsv').read_text(encoding='utf-8').splitlines():
        x, y, z, bid = line.split(',', 3)
        if bid in AIRNAMES:
            continue
        c = (int(x), int(y), int(z))
        if bid == VOIDNAME:
            voids.add(c)
        else:
            blocks.add(c)
    return meta, blocks, voids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', default=str(ROOT / 'docs' / '金之牢狱-生成预览' / '_raw'))
    ap.add_argument('--tag', default='后（新模板）')
    ap.add_argument('--json', default='gp_world_check.json')
    a = ap.parse_args()
    inp = Path(a.inp) if Path(a.inp).is_absolute() else ROOT / a.inp
    meta, blocks, voids = load(inp)
    pieces = meta['pieces']
    dump = meta['dumpBBox']  # [minX,minY,minZ,maxX,maxY,maxZ]
    dmin = (dump[0], dump[1], dump[2])
    dmax = (dump[3], dump[4], dump[5])

    def solid(c):
        return c in blocks

    def air(c):
        return c not in blocks and c not in voids

    def passable(c):
        return c not in blocks

    def inside(c):
        return all(dmin[i] <= c[i] <= dmax[i] for i in range(3))

    def standable(c):
        """站得住：脚那格可通行（空气 / structure_void）+ 头顶可通行 + 脚下一格实心。"""
        return (passable(c) and passable((c[0], c[1] + 1, c[2]))
                and solid((c[0], c[1] - 1, c[2])))

    # ---- 1) 结构层面的读数
    n_pieces = len(pieces)
    templates = sorted({p['template'] for p in pieces})
    treasure = [p for p in pieces if p['template'] == 'treasure']
    exits = [p for p in pieces if p['template'] == 'exit']
    start_y = treasure[0]['origin'][1] if treasure else None
    walk_y = max(p['bbox'][1] for p in pieces) + 1
    depths = sorted({p['depth'] for p in pieces})
    overlaps = 0
    for i in range(n_pieces):
        for j in range(i + 1, n_pieces):
            A, B = pieces[i]['bbox'], pieces[j]['bbox']
            if not (A[3] < B[0] or B[3] < A[0] or A[4] < B[1] or B[4] < A[1]
                    or A[5] < B[2] or B[5] < A[2]):
                overlaps += 1
    ports = [(p['index'], q) for p in pieces for q in p['ports']]
    paired = meta['portStats']['paired']

    # ---- 2) 逐口 3x3x1（口平面 + **口内一层**；口内 = 朝件里，即 pos - dir）
    DIRV = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0)}
    mouth_rows = []
    for idx, q in ports:
        x, y, z = q['pos']
        dx, dy, dz = DIRV[q['dir']]
        plane, inner = [], []
        for d in (-1, 0, 1):
            for h in (0, 1, 2):
                if q['dir'] in ('north', 'south'):
                    plane.append((x + d, y + h, z))
                    inner.append((x + d, y + h, z - dz))
                else:
                    plane.append((x, y + h, z + d))
                    inner.append((x - dx, y + h, z + d))
        pbad = [c for c in plane if not air(c)]
        ibad = [c for c in inner if not air(c)]
        mouth_rows.append({'piece': idx, 'dir': q['dir'], 'pos': [x, y, z],
                           'plane_air': 9 - len(pbad), 'inner_air': 9 - len(ibad),
                           'plane_bad': [list(c) for c in pbad],
                           'inner_bad': [list(c) for c in ibad]})

    # ---- 3) 从宝藏房洪泛（真实可站格）
    tb = treasure[0]['bbox']
    seeds = [(x, y, z) for x in range(tb[0], tb[3] + 1)
             for y in range(tb[1], tb[4] + 1) for z in range(tb[2], tb[5] + 1)
             if standable((x, y, z))]
    seen = set(seeds)
    dq = deque(seeds)
    while dq:
        c = dq.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
            if n in seen or not inside(n) or not standable(n):
                continue
            seen.add(n)
            dq.append(n)

    # 另一套口径：只按「可通行格」（空气 / structure_void，不要求站得住）洪泛
    # —— 用来判「箱子的相邻格能不能到」（箱子可能塞在 1 格高的壁龛里，站不进去但能挖开）
    pseed = [(x, y, z) for x in range(tb[0], tb[3] + 1)
             for y in range(tb[1], tb[4] + 1) for z in range(tb[2], tb[5] + 1)
             if passable((x, y, z))]
    pseen = set(pseed)
    dq2 = deque(pseed)
    while dq2:
        c = dq2.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
            if n in pseen or not inside(n) or not passable(n):
                continue
            pseen.add(n)
            dq2.append(n)

    def mouth_reach(q):
        """口的内侧可站格（朝**件内** = pos - dir，找 6 格内最近的可站格）。"""
        x, y, z = q['pos']
        dx, dy, dz = DIRV[q['dir']]
        for k in range(1, 8):
            c = (x - dx * k, y, z - dz * k)
            for dy2 in (0, 1):
                cc = (c[0], c[1] + dy2, c[2])
                if cc in seen:
                    return cc
        return None

    exit_reach = []
    for p in exits:
        hits = [(idx, q, mouth_reach(q)) for idx, q in ports if idx == p['index']]
        ok = [h for h in hits if h[2]]
        exit_reach.append({'piece': p['index'], 'ports': len(hits), 'reached': len(ok),
                           'cells': [list(h[2]) for h in ok]})

    # ---- 4) 箱子可达（箱子旁边有可站格）
    chest_rows = []
    for p in pieces:
        for cp in p.get('chestPos') or []:
            c = tuple(cp)
            nb = [(c[0] + 1, c[1], c[2]), (c[0] - 1, c[1], c[2]),
                  (c[0], c[1], c[2] + 1), (c[0], c[1], c[2] - 1),
                  (c[0], c[1] + 1, c[2]), (c[0], c[1] - 1, c[2])]
            hit = [n for n in nb if n in seen]
            adj = [n for n in nb if n in pseen]
            chest_rows.append({'piece': p['index'], 'pos': cp,
                               'reached': bool(hit), 'reachableAdj': bool(adj),
                               'stand': [list(n) for n in hit[:1]],
                               'adj': [list(n) for n in adj[:1]]})

    # ---- 5) 件内空气 / 行走层（与上一轮同口径）
    tot_cells = tot_air = tot_pass = 0
    walk_cells = walk_air = 0
    piece_air = []
    for p in pieces:
        b = p['bbox']
        cells = [(x, y, z) for x in range(b[0], b[3] + 1) for y in range(b[1], b[4] + 1)
                 for z in range(b[2], b[5] + 1)]
        ar = sum(1 for c in cells if air(c))
        ps = sum(1 for c in cells if passable(c))
        wc = [c for c in cells if c[1] == walk_y]
        wa = sum(1 for c in wc if air(c))
        tot_cells += len(cells)
        tot_air += ar
        tot_pass += ps
        walk_cells += len(wc)
        walk_air += wa
        piece_air.append({'index': p['index'], 'template': p['template'],
                          'cells': len(cells), 'air': ar,
                          'airPct': round(100.0 * ar / len(cells), 2),
                          'passable': ps, 'passablePct': round(100.0 * ps / len(cells), 2),
                          'walkAir': wa, 'walkCells': len(wc)})

    out = {
        'tag': a.tag, 'world': meta.get('worldName'), 'seed': meta.get('seed'),
        'structurePos': meta.get('locate', {}).get('result'),
        'pieces': n_pieces, 'templates': templates, 'templateCount': len(templates),
        'treasureCount': len(treasure), 'exitCount': len(exits),
        'startY': start_y, 'walkY': walk_y, 'depths': depths,
        'bboxOverlaps': overlaps, 'ports': len(ports), 'portsPaired': paired,
        'pieceUnionBBox': meta.get('pieceUnionBBox'),
        'chests': len(chest_rows), 'spawners': sum(p.get('spawners', 0) for p in pieces),
        'toads': sum(p.get('toads', 0) for p in pieces),
        'mouths': mouth_rows,
        'mouthsAll9': sum(1 for m in mouth_rows if m['plane_air'] == 9 and m['inner_air'] == 9),
        'flood': {'standSeeds': len(seeds), 'reached': len(seen),
                  'passSeeds': len(pseed), 'passReached': len(pseen)},
        'exitsReached': exit_reach,
        'chestReached': sum(1 for c in chest_rows if c['reached']),
        'chestAdjReached': sum(1 for c in chest_rows if c['reachableAdj']),
        'chestRows': chest_rows,
        'airInside': {'cells': tot_cells, 'air': tot_air,
                      'airPct': round(100.0 * tot_air / tot_cells, 2),
                      'passable': tot_pass,
                      'passablePct': round(100.0 * tot_pass / tot_cells, 2),
                      'walkCells': walk_cells, 'walkAir': walk_air,
                      'walkAirPct': round(100.0 * walk_air / walk_cells, 2)},
        'pieceAir': piece_air,
        'probeAirStats': meta.get('airStats'),
    }
    p = Path(__file__).with_name(a.json)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')

    print('== %s ==' % a.tag)
    print('世界 %s / 种子 %s / 结构 %s' % (out['world'], out['seed'], out['structurePos']))
    print('件 %d / 模板 %d / 宝藏房 %d / 出入口 %d / startY=%s / walkY=%d / 深度 %s'
          % (n_pieces, out['templateCount'], out['treasureCount'], len(exits), start_y,
             walk_y, depths))
    print('包围盒重叠 %d 对 / 口 %d（成对 %d）/ 箱 %d / 笼 %d / 蟾 %d'
          % (overlaps, len(ports), paired, len(chest_rows), out['spawners'], out['toads']))
    print('门洞 3x3x1（口平面 + 口内一层）：%d/%d 口 18 格全空'
          % (out['mouthsAll9'], len(mouth_rows)))
    bad = [m for m in mouth_rows if m['plane_air'] != 9 or m['inner_air'] != 9]
    for m in bad[:10]:
        print('   BAD 件#%d %-5s %s  平面 %d/9 内层 %d/9' %
              (m['piece'], m['dir'], m['pos'], m['plane_air'], m['inner_air']))
    print('洪泛：宝藏房可站种子 %d -> 连通 %d 格 ；可通行洪泛 %d -> %d 格'
          % (len(seeds), len(seen), len(pseed), len(pseen)))
    print('出入口可达：%s' % [(e['piece'], e['reached'], e['ports']) for e in exit_reach])
    print('箱子：可站邻格 %d/%d ; 相邻格可达（含 1 格高壁龛）%d/%d'
          % (out['chestReached'], len(chest_rows), out['chestAdjReached'], len(chest_rows)))
    for c in chest_rows:
        if not c['reached']:
            print('   箱子站不到（件#%d %s）' % (c['piece'], c['pos']))
    ai = out['airInside']
    print('件内空气（严格）%d/%d = %.2f%%  可通行（含 structure_void）%d/%d = %.2f%%'
          % (ai['air'], ai['cells'], ai['airPct'], ai['passable'], ai['cells'], ai['passablePct']))
    print('行走层空气 %d/%d = %.2f%%'
          % (ai['walkAir'], ai['walkCells'], ai['walkAirPct']))
    print('wrote', p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
