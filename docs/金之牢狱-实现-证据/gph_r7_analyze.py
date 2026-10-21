# -*- coding: utf-8 -*-
"""第七轮 A 级读数（离线复算）：空腔露头 / 落单口诊断 / 箱子↔BE 双向。

用法：
  python gph_r7_analyze.py --dir docs\\金之牢狱-实现-证据\\gph_r7a --tag r7a [--json out.json]
"""
import argparse
import collections
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
STRUCT = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'structure', 'golden_prison')

# 子件「最小盒子」的两档：lane（5 宽 x 5 高 x 3 深）/ exit（第七轮 11 宽 x 62 高 x 5 深）
CHILD = {'lane': (2, 3, 1), 'exit': (5, 5, 1)}   # (半宽, 深, 口底相对 y)


def bbox_center(b):
    return ((b[0] + b[3]) // 2, (b[2] + b[5]) // 2)


def touch(A, B):
    """两个 bbox 是否「贴合」（某一轴间距 <=1，另两轴有交集）—— 用来还原连接图。"""
    ox = min(A[3], B[3]) - max(A[0], B[0])
    oy = min(A[4], B[4]) - max(A[1], B[1])
    oz = min(A[5], B[5]) - max(A[2], B[2])
    gx = max(A[0] - B[3], B[0] - A[3])
    gy = max(A[1] - B[4], B[1] - A[4])
    gz = max(A[2] - B[5], B[2] - A[5])
    if ox > 0 and oy > 0 and oz > 0:
        return min(gx, gy, gz) <= 1
    return (gx <= 1 and oy > 0 and oz > 0) or (gy <= 1 and ox > 0 and oz > 0) \
        or (gz <= 1 and ox > 0 and oy > 0)


def depths_of(pieces):
    """从件 0 做 BFS（meta 里没有 depths 时兜底；有就用 dump 的）。"""
    n = len(pieces)
    d = [-1] * n
    d[0] = 0
    q = [0]
    while q:
        a = q.pop(0)
        for b in range(n):
            if d[b] < 0 and touch(pieces[a]['bbox'], pieces[b]['bbox']):
                d[b] = d[a] + 1
                q.append(b)
    return d


def out_box(pos, d, half, depth):
    """子件盒（只算 x/z；y 无所谓，盒子的 y 永远够大）。pos = 父口 jigsaw 的外侧面格。"""
    dx, dz = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}[d]
    x0, z0 = pos[0], pos[2]
    if dx:
        xs = sorted([x0 + dx, x0 + dx * depth])
        return [xs[0] - half, xs[1] + half]
    zs = sorted([z0 + dz, z0 + dz * depth])
    return [zs[0] - half, zs[1] + half]


def shortfall(box, lo, hi):
    """子件盒超出「可用空间」盒 [lo, hi] 多少格（0 = 放得下）。"""
    return max(0, lo - box[0], box[1] - hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--tag', default='')
    ap.add_argument('--json', default='')
    a = ap.parse_args()
    d = a.dir
    tag = a.tag or os.path.basename(d.rstrip('\\/'))
    res = {'tag': tag, 'dir': d, 'real': [], 'seedRuns': []}
    print('== [%s] %s ==' % (tag, d))

    mp = os.path.join(d, 'meta.json')
    metas = json.load(open(mp, encoding='utf-8')) if os.path.exists(mp) else []
    print('-- 真生成 %d 座 --' % len(metas))
    for i, m in enumerate(metas):
        pieces = m['pieces']
        start = pieces[0]
        cx, cz = bbox_center(start['bbox'])
        maxd = 128 if m.get('structure') == 'golden_prison_basalt' else 116
        lo_x, hi_x = cx - maxd, cx + maxd + 1
        lo_z, hi_z = cz - maxd, cz + maxd + 1
        depths = m.get('depths') or depths_of(pieces)
        # 箱子：只算**件 bbox 内**的（union 里可能有别的结构/遗迹的箱子）
        def in_piece(p):
            for q in pieces:
                b = q['bbox']
                if b[0] <= p[0] <= b[3] and b[1] <= p[1] <= b[4] and b[2] <= p[2] <= b[5]:
                    return q['i']
            return None
        bes = m.get('blockEntities') or []
        chests = [b for b in bes if b['id'] == 'minecraft:chest']
        ours = [(b, in_piece(b['pos'])) for b in chests]
        ours = [(b, k) for (b, k) in ours if k is not None]
        loaded = [(b, k) for (b, k) in ours if b.get('lootTable') == 'bettergold:chests/golden_prison']
        foreign = [(b, in_piece(b['pos'])) for b in chests if in_piece(b['pos']) is None]
        spawners = [b for b in bes if b['id'] == 'minecraft:mob_spawner']
        ents = m.get('entities') or []
        frames = [e for e in ents if e['id'] == 'minecraft:glow_item_frame']
        exits = []
        for e in (m.get('exits') or []):
            top = e['topY']
            af = e.get('airFromY')
            exits.append({'idx': e['pieceIndex'], 'topY': top, 'airFromY': af,
                          'pass': (af is not None and af <= top),
                          'delta': (af - top) if af is not None else None,
                          'clear8': e.get('columnsClearAboveRim8'),
                          'cols': e.get('columns')})
        orph = []
        for o in (m.get('orphans') or []):
            pi = o['piece']
            # 口 pos 是 jigsaw 那一格（父件的外侧面）
            lb = out_box(o['pos'], o['dir'], CHILD['lane'][0], CHILD['lane'][1])
            eb = out_box(o['pos'], o['dir'], CHILD['exit'][0], CHILD['exit'][1])
            if o['dir'] in ('north', 'south'):
                sf_lane = shortfall(lb, lo_z, hi_z)
                sf_exit = shortfall(eb, lo_z, hi_z)
                dist = max(abs(o['pos'][0] - cx), abs(o['pos'][2] - cz))
                axis = 'z'
                avail = (lo_z, hi_z)
            else:
                sf_lane = shortfall(lb, lo_x, hi_x)
                sf_exit = shortfall(eb, lo_x, hi_x)
                dist = max(abs(o['pos'][0] - cx), abs(o['pos'][2] - cz))
                axis = 'x'
                avail = (lo_x, hi_x)
            orph.append({'piece': pi, 'tpl': o['tpl'], 'depth': depths[pi] if pi < len(depths) else None,
                         'pos': o['pos'], 'dir': o['dir'], 'target': o.get('target'),
                         'distBox': dist, 'axis': axis, 'avail': avail,
                         'laneBox': lb, 'laneShort': sf_lane,
                         'exitBox': eb, 'exitShort': sf_exit})
        print('   #%d %-18s %-22s 件=%2d 宝藏房=%s 口 %s / 配对 %s / 落单 %d'
              % (i, m['biome'], m.get('structure'), len(pieces), m.get('treasurePieces'),
                 m.get('ports'), m.get('paired'), len(orph)))
        print('      箱子（件内）：%d 块 / %d 带战利品表；件外箱子 %d 条%s'
              % (len(ours), len(loaded), len(foreign),
                 ('（%s）' % ', '.join('%s@%s' % (b.get('lootTable'), b['pos']) for b, _ in foreign))
                 if foreign else ''))
        print('      刷怪笼 %d / 展示框 %d' % (len(spawners), len(frames)))
        for e in exits:
            print('      exit#%d topY=%s airFromY=%s 达标=%s（Δ=%s）环顶上方 8 格全空 %s/9'
                  % (e['idx'], e['topY'], e['airFromY'], e['pass'], e['delta'], e['clear8']))
        for o in orph:
            print('      落单口：件 #%d %s 深度=%s 口=%s %s target=%s 距起点中心 %d 格（%s 轴，可用 %s）'
                  % (o['piece'], o['tpl'], o['depth'], o['pos'], o['dir'], o['target'],
                     o['distBox'], o['axis'], o['avail']))
            print('        子件盒：lane %s（超出 %d 格） / exit %s（超出 %d 格）'
                  % (o['laneBox'], o['laneShort'], o['exitBox'], o['exitShort']))
        res['real'].append({'biome': m['biome'], 'structure': m.get('structure'),
                            'pieces': len(pieces), 'treasure': m.get('treasurePieces'),
                            'ports': m.get('ports'), 'paired': m.get('paired'),
                            'orphans': orph, 'chestOurs': len(ours), 'chestLoot': len(loaded),
                            'chestForeign': [(b.get('lootTable'), b['pos']) for b, _ in foreign],
                            'spawners': len(spawners), 'frames': len(frames),
                            'exits': exits})
    n_all = sum(len(r['exits']) for r in res['real'])
    n_pass = sum(1 for r in res['real'] for e in r['exits'] if e['pass'])
    n_orph = sum(len(r['orphans']) for r in res['real'])
    print('-- 汇总：出入口 %d 个，达标（airFromY <= topY）%d 个；落单口 %d 个；'
          '箱子（件内）%d / 带战利品表 %d'
          % (n_all, n_pass, n_orph,
             sum(r['chestOurs'] for r in res['real']), sum(r['chestLoot'] for r in res['real'])))
    res['summary'] = {'exits': n_all, 'exitsPass': n_pass, 'orphans': n_orph,
                      'chestOurs': sum(r['chestOurs'] for r in res['real']),
                      'chestLoot': sum(r['chestLoot'] for r in res['real'])}

    sp = os.path.join(d, 'seeds.json')
    if os.path.exists(sp):
        sd = json.load(open(sp, encoding='utf-8'))
        for key in [k for k in sd if k.startswith('runs')]:
            runs = [r for r in sd[key] if r.get('fingerprint')]
            print('-- 10 种子 [%s]：%d 个有效 run' % (key, len(runs)))
            orph = 0
            rows = []
            for r in runs:
                k = len(r.get('orphans') or [])
                orph += k
                rows.append({'seed': r['seed'], 'pieces': len(r['pieces']),
                             'treasure': r.get('treasurePieces'), 'orphans': k,
                             'fertile': sum(1 for t in r['fingerprint'] if t.endswith('_fertile')),
                             'exits': sum(1 for t in r['fingerprint'] if t == 'exit')})
                print('   seed %-9d 件=%2d 宝藏房=%s 落单=%d 出入口=%d fertile=%d'
                      % (r['seed'], len(r['pieces']), r.get('treasurePieces'), k,
                         rows[-1]['exits'], rows[-1]['fertile']))
            print('   落单口合计 = %d；件数范围 %d..%d；出入口合计 %d'
                  % (orph, min(x['pieces'] for x in rows), max(x['pieces'] for x in rows),
                     sum(x['exits'] for x in rows)))
            res['seedRuns'].append({'key': key, 'runs': len(runs), 'orphans': orph,
                                    'rows': rows})
    if a.json:
        open(a.json, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
        print('   -> %s' % a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
