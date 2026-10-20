# -*- coding: utf-8 -*-
"""阶段 B-1：静态核 20 个 NBT（不跑游戏）。

对每件：
  1) size / 满体积 / 方块条目数（应 == 满体积）/ palette 含 minecraft:air / air 条目数与占比
  2) 逐口：口平面 3x3x1 是否全空 + 口内一格那层 3x3x1 是否全空（9 格逐格列出）
  3) 行走层（洞底那一层 = jigsaw 的 y）：整层空气占比 + 去掉一圈外壳的内圈占比
  4) 与 `git show HEAD:<path>` 的旧版逐格 diff：旧版几格、新版非空气几格，
     必须「只多出空气条目」——坐标 / 方块 id / 属性 / jigsaw 块实体 / 箱子 LootTable 一格不许变。

用法：
  py -3 docs\\金之牢狱-生成预览-证据\\gp_air_static.py            # 打印表 + 写 json
  py -3 docs\\金之牢狱-生成预览-证据\\gp_air_static.py --quiet    # 只写 json
输出：
  docs\\金之牢狱-生成预览-证据\\gp_air_static.json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / 'docs' / '金之牢狱-实现-证据'
sys.path.insert(0, str(EVID))
import nbt  # noqa: E402

STRUCT = ROOT / 'src' / 'main' / 'resources' / 'data' / 'bettergold' / 'structure' / 'golden_prison'
REL = 'src/main/resources/data/bettergold/structure/golden_prison/'
AIR = 'minecraft:air'
VOID = 'minecraft:structure_void'
JIG = 'minecraft:jigsaw'
DIRV = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0)}


def parse(raw):
    """-> (size, {(x,y,z): (name, props)}, {pos: be}, {pos: props})"""
    if raw[:2] == b'\x1f\x8b':
        import gzip
        raw = gzip.decompress(raw)
    _, root = nbt.parse(raw)
    size = tuple(root['size'])
    pal = root['palette']
    blocks, jig = {}, {}
    for b in root['blocks']:
        p = tuple(b['pos'])
        e = pal[b['state']]
        nm = e['Name']
        pr = dict(e.get('Properties') or {})
        blocks[p] = (nm, pr)
        if nm == JIG:
            jig[p] = dict(b.get('nbt') or {})
    return size, blocks, jig


def outward(p, size):
    x, y, z = p
    sx, sy, sz = size
    c = []
    if z == 0:
        c.append('north')
    if z == sz - 1:
        c.append('south')
    if x == 0:
        c.append('west')
    if x == sx - 1:
        c.append('east')
    return c


def mouth_cells(pos, side):
    """口平面（件边界那一层）的 3 宽 x 3 高，共 9 格；再返回朝件内一格的 9 格。"""
    x, y, z = pos
    dx, dy, dz = DIRV[side]
    plane, inner = [], []
    for d in (-1, 0, 1):
        for h in (0, 1, 2):
            if side in ('north', 'south'):
                plane.append((x + d, y + h, z))
                inner.append((x + d, y + h, z - dz))
            else:
                plane.append((x, y + h, z + d))
                inner.append((x - dx, y + h, z + d))
    return plane, inner


def main(quiet=False):
    rows = []
    for f in sorted(STRUCT.glob('*.nbt')):
        name = f.stem
        new_raw = f.read_bytes()
        size, blocks, jig = parse(new_raw)
        sx, sy, sz = size
        vol = sx * sy * sz
        air = sum(1 for v in blocks.values() if v[0] == AIR)
        names = set(v[0] for v in blocks.values())
        # 行走层 = 洞底那一层（jigsaw 的 y）
        wy = None
        for pos in jig:
            wy = pos[1] if wy is None else min(wy, pos[1])
        walk = [(x, wy, z) for x in range(sx) for z in range(sz)]
        wair = sum(1 for c in walk if blocks.get(c, (None,))[0] == AIR)
        inner_walk = [(x, wy, z) for x in range(1, sx - 1) for z in range(1, sz - 1)]
        iwair = sum(1 for c in inner_walk if blocks.get(c, (None,))[0] == AIR)
        # 口
        mouths = []
        for pos, be in sorted(jig.items()):
            out = outward(pos, size)
            side = out[0] if len(out) == 1 else '?'
            plane, inner = mouth_cells(pos, side) if side != '?' else ([], [])
            pv = [blocks.get(c, (None,))[0] for c in plane]
            iv = [blocks.get(c, (None,))[0] for c in inner]
            mouths.append({
                'side': side, 'pos': list(pos),
                'name': be.get('name'), 'target': be.get('target'),
                'plane': pv, 'plane_air': sum(1 for v in pv if v in (AIR, JIG)),
                'inner': iv, 'inner_air': sum(1 for v in iv if v in (AIR, JIG)),
                'plane_cells': [list(c) for c in plane],
                'inner_cells': [list(c) for c in inner],
                'plane_ok': all(v in (AIR, JIG) for v in pv),
                'inner_ok': all(v in (AIR, JIG) for v in iv),
            })
        # 与 HEAD 旧版 diff
        rel = REL + f.name
        old_raw = subprocess.check_output(['git', 'show', 'HEAD:' + rel], cwd=str(ROOT))
        osize, oblocks, ojig = parse(old_raw)
        same_size = tuple(osize) == tuple(size)
        old_air = sum(1 for v in oblocks.values() if v[0] == AIR)
        removed = sorted(set(oblocks) - set(blocks))
        added = sorted(set(blocks) - set(oblocks))
        changed = sorted(k for k in set(oblocks) & set(blocks) if oblocks[k] != blocks[k])
        jig_same = ojig == jig
        added_nonair = [k for k in added if blocks[k][0] != AIR]
        rows.append({
            'file': f.name, 'size': list(size), 'volume': vol,
            'entries': len(blocks), 'palette_has_air': AIR in names,
            'air': air, 'air_pct': round(100.0 * air / vol, 2),
            'solid': vol - air,
            'walk_y': wy, 'walk_cells': len(walk), 'walk_air': wair,
            'walk_air_pct': round(100.0 * wair / len(walk), 2),
            'walk_inner_cells': len(inner_walk), 'walk_inner_air': iwair,
            'walk_inner_pct': round(100.0 * iwair / len(inner_walk), 2),
            'mouths': mouths,
            'old_size': list(osize), 'old_entries': len(oblocks), 'old_solid': len(oblocks),
            'old_air': old_air,
            'diff': {
                'same_size': same_size,
                'removed': [list(k) for k in removed],
                'changed': [[list(k), oblocks[k], blocks[k]] for k in changed],
                'added_count': len(added),
                'added_sample': [list(k) for k in added[:12]],
                'added_nonair': [list(k) for k in added_nonair],
                'jigsaw_same': jig_same,
                'only_air_added': (same_size and not removed and not changed
                                   and not added_nonair and jig_same and old_air == 0),
                'added_air': len(added) - len(added_nonair),
            },
        })

    out = {
        'note': '阶段 B-1 静态核：20 个 NBT 的 air / 逐口 3x3 / 行走层 / 与 HEAD 旧版逐格 diff',
        'templates': len(rows),
        'rows': rows,
    }
    p = Path(__file__).with_name('gp_air_static.json')
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')

    if quiet:
        print('[gp-air-static] wrote', p)
        return 0
    print('%-20s %-12s %6s %6s %6s %7s %7s %7s %s' %
          ('template', 'size', 'vol', 'entr', 'air', 'air%', 'walk%', 'inwalk%', 'diff'))
    for r in rows:
        d = r['diff']
        print('%-20s %-12s %6d %6d %6d %6.2f%% %6.2f%% %6.2f%%  %s' %
              (r['file'][:-4], 'x'.join(str(v) for v in r['size']), r['volume'],
               r['entries'], r['air'], r['air_pct'], r['walk_air_pct'],
               r['walk_inner_pct'],
               'only-air(+%d)' % d['added_air'] if d['only_air_added'] else 'DIFF!'))
    print()
    for r in rows:
        print('# %s  (%d 口)' % (r['file'][:-4], len(r['mouths'])))
        for m in r['mouths']:
            print('   %-5s %-14s plane3x3=%d/9 %s inner3x3=%d/9 %s' %
                  (m['side'], '(%d,%d,%d)' % tuple(m['pos']), m['plane_air'],
                   'OK' if m['plane_ok'] else 'BAD', m['inner_air'],
                   'OK' if m['inner_ok'] else 'BAD'))
    tot = sum(r['volume'] for r in rows)
    tot_air = sum(r['air'] for r in rows)
    tot_ew = sum(r['walk_inner_cells'] for r in rows)
    tot_ewa = sum(r['walk_inner_air'] for r in rows)
    print()
    print('TOTAL 20 件：体积 %d / 空气 %d = %.2f%% ；行走层内圈 %d/%d = %.2f%%'
          % (tot, tot_air, 100.0 * tot_air / tot, tot_ewa, tot_ew, 100.0 * tot_ewa / tot_ew))
    bad = [r['file'] for r in rows if not r['diff']['only_air_added']]
    print('diff 自证：%d/20 件「只多了空气」%s' %
          (20 - len(bad), '' if not bad else '  ⚠ ' + ', '.join(bad)))
    print('最低 air%% = %.2f%% ; 最低行走层内圈 = %.2f%% ; 所有口 3x3x1 全空 = %s'
          % (min(r['air_pct'] for r in rows), min(r['walk_inner_pct'] for r in rows),
             all(m['plane_ok'] and m['inner_ok'] for r in rows for m in r['mouths'])))
    print('wrote', p)
    return 0


if __name__ == '__main__':
    sys.exit(main('--quiet' in sys.argv))
