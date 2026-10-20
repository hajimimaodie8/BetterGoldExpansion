# -*- coding: utf-8 -*-
"""金之牢狱 —— 件构建流水线（第 1/2/3 步）。

第 1 步：从作者存档里逐件抠出 14 个件，并派生 6 个新变体（3 尺寸 × 镜像/丰饶）=> 20 件。
第 2 步：按几何口位注入 minecraft:jigsaw（口底正中、朝外、name/target/pool）。
第 3 步：导出 .nbt 到 data/bettergold/structure/golden_prison/ + 俯视蓝图 PNG。

用法（必须用工作区自带 Python）：
    python gp_build.py --stage 1      # 只做抠件 + 变体，写 pieces_stage1.json
    python gp_build.py --stage 2      # 读 stage1，注 jigsaw，写 pieces_stage2.json
    python gp_build.py --stage 3      # 读 stage2，写 .nbt + 蓝图 + 自检
    python gp_build.py --stage all
"""
import argparse
import collections
import gzip
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt

ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
WORLD = os.path.join(ROOT, 'docs', '金之牢狱-素材清单', '金之牢狱')
EVID = os.path.join(ROOT, 'docs', '金之牢狱-实现-证据')
RES = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'structure', 'golden_prison')
BP = os.path.join(ROOT, 'docs', '金之牢狱-蓝图')
NS = 'bettergold'
POOL = 'bettergold:golden_prison/'
LOOT = 'bettergold:chests/golden_prison'
DATAVERSION = 3955

# (模板名, 源件, 世界原点 x,y,z, 尺寸 sx,sy,sz, 说明)
SRC = [
    ('treasure',       'P01', 397, -60, 491, 21, 9, 21, '宝藏房（start_pool，唯一）'),
    ('cross_a',        'P02', 421, -60, 435, 37, 8, 37, '四面道 A（中央金农田）'),
    ('cross_b',        'P03', 421, -60, 475, 37, 8, 37, '四面道 B（中央金堆+箱+蟾）'),
    ('cell_large_a',   'P04', 461, -60, 413, 15, 6, 31, '3 号牢房 #1（31 深，A）'),
    ('cell_large_b',   'P05', 461, -60, 447, 15, 6, 31, '3 号牢房 #2（31 深，A 副本）'),
    ('cell_large_c',   'P06', 461, -60, 481, 15, 6, 31, '3 号牢房 #3（31 深，无箱无笼）'),
    ('cell_medium_a',  'P07', 479, -60, 443, 15, 6, 21, '2 号牢房 #1（21 深，A）'),
    ('cell_medium_b',  'P08', 479, -60, 467, 15, 6, 21, '2 号牢房 #2（21 深，A 副本）'),
    ('cell_medium_c',  'P09', 479, -60, 491, 15, 6, 21, '2 号牢房 #3（21 深，无箱无笼）'),
    ('cell_small_a',   'P10', 497, -60, 473, 15, 6, 11, '1 号牢房 #1（11 深，A）'),
    ('cell_small_b',   'P11', 497, -60, 487, 15, 6, 11, '1 号牢房 #2（11 深，A 副本）'),
    ('cell_small_c',   'P12', 497, -60, 501, 15, 6, 11, '1 号牢房 #3（11 深，无箱无笼）'),
    ('lane',           'P13',   3, -60, 501,  5, 5,  3, '间隔过道（5×5×3）'),
    ('exit',           'P14',   3, -60, 507,  5, 8,  5, '出入口（5×8×5，南面金栅栏）'),
]

# 派生：镜像 / 丰饶。基准 = 每尺寸的 A 件。
DERIVE = [
    ('cell_small_mirror',  'cell_small_a'),
    ('cell_small_fertile', 'cell_small_a'),
    ('cell_medium_mirror', 'cell_medium_a'),
    ('cell_medium_fertile', 'cell_medium_a'),
    ('cell_large_mirror',  'cell_large_a'),
    ('cell_large_fertile', 'cell_large_a'),
]

# 口位朝向 -> (dx,dy,dz) 与 jigsaw orientation 名
DIRS = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0)}

# 每个模板的口：side -> (name, target, pool)
SOCK = {
    'treasure':    {'south': ('room', 'lane', POOL + 'lane')},
    'cross_a':     {s: ('room', 'lane', POOL + 'lane') for s in ('north', 'south', 'east', 'west')},
    'cross_b':     {s: ('room', 'lane', POOL + 'lane') for s in ('north', 'south', 'east', 'west')},
    'exit':        {'north': ('lane', 'room', POOL + 'room')},
    # 过道两个口不对称：北口把链子带回房间，南口把链子送进「小牢房三步循环」的第 1 步
    'lane':        {'north': ('lane', 'room', POOL + 'room'),
                    'south': ('lane', 'cell_small_1', POOL + 'cell_small_1')},
    # 中/大牢房：两个口同名同目标 => 无论引擎选中哪个旋转都成立
    'cell_medium_a': {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')},
    'cell_medium_mirror': {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')},
    'cell_medium_fertile': {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')},
    'cell_medium_b': {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')},
    'cell_medium_c': {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')},
    'cell_large_a': {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')},
    'cell_large_mirror': {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')},
    'cell_large_fertile': {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')},
    'cell_large_b': {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')},
    'cell_large_c': {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')},
    # 小牢房三步循环：第 1 步（A）-> 第 2 步（镜像）-> 第 3 步（丰饶）-> 回过道
    'cell_small_a':      {'north': ('cell_small_1', 'cell_small_2', POOL + 'cell_small_2'),
                          'south': ('cell_small_1', 'cell_small_2', POOL + 'cell_small_2')},
    'cell_small_b':      {'north': ('room', 'lane', POOL + 'lane'),
                          'south': ('room', 'lane', POOL + 'lane')},
    'cell_small_c':      {'north': ('room', 'lane', POOL + 'lane'),
                          'south': ('room', 'lane', POOL + 'lane')},
    'cell_small_mirror': {'north': ('cell_small_2', 'cell_small_3', POOL + 'cell_small_3'),
                          'south': ('cell_small_2', 'cell_small_3', POOL + 'cell_small_3')},
    'cell_small_fertile': {'north': ('cell_small_3', 'lane', POOL + 'lane'),
                           'south': ('cell_small_3', 'lane', POOL + 'lane')},
}

AIR = {'minecraft:air'}
NOT_WALKABLE = {'minecraft:air', 'minecraft:structure_void'}

# 俯视蓝图的配色（按方块 id）
COLORS = {
    'minecraft:air': (24, 24, 28),
    'minecraft:structure_void': (60, 60, 70),
    'bettergold:gold_bricks': (196, 154, 44),
    'bettergold:gold_pillar': (152, 112, 24),
    'bettergold:gold_bricks_stairs': (168, 130, 32),
    'bettergold:gold_bricks_wall': (140, 104, 20),
    'bettergold:gold_bricks_slab': (176, 138, 36),
    'bettergold:gold_bars': (226, 190, 90),
    'bettergold:gold_chain': (236, 206, 120),
    'bettergold:gold_trapdoor': (206, 166, 60),
    'bettergold:gold_infused_dirt': (110, 78, 34),
    'bettergold:gold_infused_farmland': (86, 58, 24),
    'bettergold:golden_wheat_crop': (214, 196, 84),
    'bettergold:golden_carrot_crop': (232, 148, 40),
    'bettergold:golden_eggplant_crop': (140, 70, 150),
    'bettergold:golden_rose_bush': (200, 92, 92),
    'bettergold:golden_toad_figurine': (246, 214, 60),
    'minecraft:gold_block': (246, 208, 52),
    'minecraft:raw_gold_block': (198, 164, 62),
    'minecraft:nether_gold_ore': (166, 66, 44),
    'minecraft:ancient_debris': (92, 66, 62),
    'minecraft:chest': (150, 106, 52),
    'minecraft:spawner': (58, 76, 96),
    'minecraft:yellow_stained_glass': (232, 232, 120),
    'minecraft:jigsaw': (240, 60, 200),
}
UNKNOWN_COLOR = (255, 0, 0)


# ---------------------------------------------------------------- 世界加载
def load_world():
    blocks = {}
    for fn in sorted(os.listdir(os.path.join(WORLD, 'region'))):
        if not fn.endswith('.mca'):
            continue
        for cx, cz, root, comp in nbt.parse_region(os.path.join(WORLD, 'region', fn)):
            for sec in (root.get('sections') or []):
                sy = sec.get('Y', 0)
                for (x, y, z), val in nbt.section_blocks(sec).items():
                    blocks[(cx * 16 + x, sy * 16 + y, cz * 16 + z)] = val
    return blocks


def k2s(pos):
    return '%d,%d,%d' % pos


def s2k(s):
    a = s.split(',')
    return (int(a[0]), int(a[1]), int(a[2]))


# ---------------------------------------------------------------- 第 1 步
def extract(blocks):
    pieces = {}
    for name, src, x0, y0, z0, sx, sy, sz, note in SRC:
        sub = {}
        for y in range(y0, y0 + sy):
            for z in range(z0, z0 + sz):
                for x in range(x0, x0 + sx):
                    v = blocks.get((x, y, z))
                    if v is None:
                        continue
                    nm, pr = v
                    if nm in AIR:
                        continue
                    sub[k2s((x - x0, y - y0, z - z0))] = [nm, dict(pr)]
        pieces[name] = {'name': name, 'src': src, 'note': note,
                        'size': [sx, sy, sz], 'blocks': sub, 'derived': 'original'}
    return pieces


def mirror_props(nm, props):
    """沿南北轴（x 轴镜像，x -> sx-1-x）镜像方块属性：东西互换、楼梯 shape 左右互换。"""
    p = dict(props)
    f = {'east': 'west', 'west': 'east'}
    if 'facing' in p and p['facing'] in f:
        p['facing'] = f[p['facing']]
    # east / west 布尔（墙、栅栏、玻璃板、锁链的连接位）
    e = p.pop('east', None)
    w = p.pop('west', None)
    if e is not None or w is not None:
        if w is not None:
            p['east'] = w
        if e is not None:
            p['west'] = e
    if 'shape' in p:
        p['shape'] = {'inner_left': 'inner_right', 'inner_right': 'inner_left',
                      'outer_left': 'outer_right', 'outer_right': 'outer_left'}.get(p['shape'], p['shape'])
    return p


def mirror_piece(piece):
    sx, sy, sz = piece['size']
    out = {}
    for key, (nm, pr) in piece['blocks'].items():
        x, y, z = s2k(key)
        out[k2s((sx - 1 - x, y, z))] = [nm, mirror_props(nm, pr)]
    return out


def solids(blocks):
    return {k: v for k, v in blocks.items() if v[0] not in NOT_WALKABLE}


def walk_level(piece, mouths):
    """可行走面 = 口洞底那一层的「地面之上的空气层」= 口底 dy。"""
    ys = {dy for (side, cx, dy, cz, d) in mouths}
    if len(ys) != 1:
        raise SystemExit('[gp-build] 一个件的多个口不在同一 dy: %s %s' % (piece['name'], sorted(ys)))
    return ys.pop()


def standable(blocks, sx, sy, sz, wy):
    out = set()
    for z in range(sz):
        for x in range(sx):
            if (x, wy, z) in blocks or (x, wy + 1, z) in blocks:
                continue
            below = blocks.get((x, wy - 1, z))
            if below is None or below[0] in NOT_WALKABLE:
                continue
            out.add((x, z))
    return out


def reachable(st, start, sx, sz):
    if start not in st:
        return set()
    seen = {start}
    q = collections.deque([start])
    while q:
        x, z = q.popleft()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n in st and n not in seen:
                seen.add(n)
                q.append(n)
    return seen


def pick_patch(st, sx, sz, wy, center_col):
    """在可达且可行走的地面里挑一块不与过道口冲突的矩形农田（最大优先）。"""
    best = None
    for w, h in ((3, 3), (3, 2), (2, 3), (2, 2)):
        for z0 in range(2, sz - 2 - h + 1):
            for x0 in range(1, sx - 1 - w + 1):
                cols = range(x0, x0 + w)
                if any(abs(c - center_col) <= 1 for c in cols):
                    continue        # 不许压在南北过道正中（3 宽）
                cells = [(x, z) for z in range(z0, z0 + h) for x in cols]
                if not all(c in st for c in cells):
                    continue
                score = (w * h, -abs(z0 + h / 2.0 - sz / 2.0) - abs(x0 + w / 2.0 - sx / 2.0))
                if best is None or score > best[0]:
                    best = (score, cells)
        if best is not None:
            return best[1]      # 只取能找到的最大面积档
    return best[1] if best else []


def fertile_piece(piece, src_blocks, mouths):
    sx, sy, sz = piece['size']
    wy = walk_level(piece, mouths)
    center_col = mouths[0][1]
    grid = {s2k(k): v for k, v in piece['blocks'].items()}
    st = standable(grid, sx, sy, sz, wy)
    # 从北口内侧一格出发做连通（口底那一层）
    starts = [(cx, 1) for cx in range(center_col - 1, center_col + 2) if (cx, 1) in st]
    reach = set()
    for s in starts:
        reach |= reachable(st, s, sx, sz)
    cells = pick_patch(reach, sx, sz, wy, center_col)
    if not cells:
        raise SystemExit('[gp-build] %s 找不到可放农田的内部空位' % piece['name'])
    # 从作者 P02 中央农田搬：farmland + 三种作物；从 P03 搬：箱子 + 金蟾
    farm = {s2k(k): v for k, v in src_blocks['cross_a']['blocks'].items()}
    ch = {s2k(k): v for k, v in src_blocks['cross_b']['blocks'].items()}
    farmland = None
    # 定位 P02 中央农田里的 farmland / 作物（相对坐标 13..23 那一带）
    fw = fc = fe = None
    for key, (nm, pr) in farm.items():
        x, y, z = key
        if not (13 <= x <= 23 and 13 <= z <= 23):
            continue
        if nm == 'bettergold:gold_infused_farmland' and farmland is None:
            farmland = [nm, dict(pr)]
        if nm == 'bettergold:golden_wheat_crop' and fw is None:
            fw = [nm, dict(pr)]
        if nm == 'bettergold:golden_carrot_crop' and fc is None:
            fc = [nm, dict(pr)]
        if nm == 'bettergold:golden_eggplant_crop' and fe is None:
            fe = [nm, dict(pr)]
    chest = None
    toad = None
    for key, (nm, pr) in ch.items():
        if nm == 'minecraft:chest' and chest is None:
            chest = ['minecraft:chest', dict(pr)]
        if nm == 'bettergold:golden_toad_figurine' and toad is None:
            toad = ['bettergold:golden_toad_figurine', dict(pr)]
    if not (farmland and fw and chest and toad):
        raise SystemExit('[gp-build] 源件里缺 farmland/crop/chest/toad：%s' %
                         (farmland, fw, fc, fe, chest, toad))
    # 最远的一个格子放箱子（不挡过道），其余按 麦/胡萝卜/茄子 三色循环
    px = sum(c[0] for c in cells) / float(len(cells))
    pz = sum(c[1] for c in cells) / float(len(cells))
    far = max(cells, key=lambda c: (c[0] - px) ** 2 + (c[1] - pz) ** 2)
    crops = [fw, fc, fe or fw]
    ci = 0
    changed = {}
    for i, (x, z) in enumerate(sorted(cells, key=lambda c: (c[1], c[0]))):
        changed[(x, wy - 1, z)] = [farmland[0], dict(farmland[1])]
        if (x, z) == far:
            changed[(x, wy, z)] = [chest[0], dict(chest[1])]
        elif i < 2:
            changed[(x, wy, z)] = [toad[0], dict(toad[1])]
        else:
            cr = crops[ci % len(crops)]
            ci += 1
            changed[(x, wy, z)] = [cr[0], dict(cr[1])]
    for k, v in changed.items():
        grid[k] = v
    out = {k2s(k): v for k, v in grid.items()}
    meta = {'patch': sorted([list(c) for c in cells]), 'chest': list(far),
            'farmland_src': 'cross_a', 'crop_src': 'cross_a', 'chest_src': 'cross_b',
            'toad_src': 'cross_b', 'walk_y': wy}
    return out, meta


def detect_mouths(blocks, sx, sy, sz):
    """在边界层找「3 宽 × 3 高、且向内一格同样为空」的洞 => 拼接口。"""
    out = []
    for side in ('north', 'south', 'west', 'east'):
        runs = []
        if side in ('north', 'south'):
            outer = 0 if side == 'north' else sz - 1
            inner = 1 if side == 'north' else sz - 2
            for dy in range(1, sy - 2):
                run = []
                for cx in range(1, sx - 1):
                    a = (cx, dy, outer) in blocks or (cx, dy + 1, outer) in blocks or (cx, dy + 2, outer) in blocks
                    b = (cx, dy, inner) in blocks or (cx, dy + 1, inner) in blocks or (cx, dy + 2, inner) in blocks
                    if not a and not b:
                        run.append(cx)
                    else:
                        if len(run) == 3:
                            runs.append((run[1], dy, outer))
                        run = []
                if len(run) == 3:
                    runs.append((run[1], dy, outer))
        else:
            outer = 0 if side == 'west' else sx - 1
            inner = 1 if side == 'west' else sx - 2
            for dy in range(1, sy - 2):
                run = []
                for cz in range(1, sz - 1):
                    a = (outer, dy, cz) in blocks or (outer, dy + 1, cz) in blocks or (outer, dy + 2, cz) in blocks
                    b = (inner, dy, cz) in blocks or (inner, dy + 1, cz) in blocks or (inner, dy + 2, cz) in blocks
                    if not a and not b:
                        run.append(cz)
                    else:
                        if len(run) == 3:
                            runs.append((outer, dy, run[1]))
                        run = []
                if len(run) == 3:
                    runs.append((outer, dy, run[1]))
        for r in sorted(set(runs)):
            cx, dy, cz = r
            if side in ('north', 'south'):
                out.append((side, cx, dy, cz, (0, 0, -1) if side == 'north' else (0, 0, 1)))
            else:
                out.append((side, cx, dy, cz, (-1, 0, 0) if side == 'west' else (1, 0, 0)))
    return sorted(out)


def stage1():
    blocks = load_world()
    pieces = extract(blocks)
    # 口位：以「逐件实测」为准，再与理论表对照
    for name, p in pieces.items():
        sx, sy, sz = p['size']
        grid = {s2k(k): v for k, v in p['blocks'].items()}
        m = detect_mouths(grid, sx, sy, sz)
        p['mouths'] = [[s, cx, dy, cz, list(d)] for (s, cx, dy, cz, d) in m]
        p['block_count'] = len(grid)
        p['walk_y'] = walk_level(p, m)
        # 口必须真的通向内部：口底那一层的「向内 3 格」要能走
        for (side, cx, dy, cz, d) in m:
            dx, dz = d[0], d[2]
            for step in (1, 2, 3):
                if side in ('north', 'south'):
                    cell = (cx, dy, cz - dz * step * -1 if False else cz + (dz * step))
                else:
                    cell = (cx + dx * step, dy, cz)
                if cell in grid:
                    raise SystemExit('[gp-build] %s 口 %s 第 %d 格被 %s 堵住' %
                                     (name, side, step, grid[cell][0]))
    # 派生
    derived_meta = {}
    for new, base in DERIVE:
        if new.endswith('_mirror'):
            pieces[new] = {'name': new, 'src': pieces[base]['src'], 'note': '%s 的南北轴镜像' % base,
                           'size': list(pieces[base]['size']), 'blocks': mirror_piece(pieces[base]),
                           'derived': 'mirror', 'base': base}
            pieces[new]['mouths'] = [list(m) for m in pieces[base]['mouths']]
            pieces[new]['block_count'] = len(pieces[new]['blocks'])
            pieces[new]['walk_y'] = pieces[base]['walk_y']
        else:
            b = {s2k(k): v for k, v in pieces[base]['blocks'].items()}
            nb, meta = fertile_piece(pieces[base], pieces, pieces[base]['mouths'])
            pieces[new] = {'name': new, 'src': pieces[base]['src'],
                           'note': '%s 的丰饶变体（农田/金蟾/箱取自 P02、P03）' % base,
                           'size': list(pieces[base]['size']), 'blocks': nb,
                           'derived': 'fertile', 'base': base}
            pieces[new]['mouths'] = [list(m) for m in pieces[base]['mouths']]
            pieces[new]['block_count'] = len(nb)
            pieces[new]['walk_y'] = pieces[base]['walk_y']
            derived_meta[new] = meta
    validate_stage1(pieces, derived_meta)
    out = {'pieces': pieces, 'derive_meta': derived_meta}
    with open(os.path.join(EVID, 'pieces_stage1.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    report_stage1(pieces, derived_meta)


def validate_stage1(pieces, derived_meta):
    problems = []
    for new, base in DERIVE:
        pb, pn = pieces[base], pieces[new]
        if new.endswith('_mirror'):
            if pb['block_count'] != pn['block_count']:
                problems.append('%s 镜像后块数变了 %d -> %d' % (new, pb['block_count'], pn['block_count']))
            if set(v[0] for v in pb['blocks'].values()) != set(v[0] for v in pn['blocks'].values()):
                problems.append('%s 镜像后调色板变了' % new)
            if mirror_piece(pn) != {k: [v[0], v[1]] for k, v in pb['blocks'].items()}:
                problems.append('%s 镜像两次 != 原始 A 件' % new)
            if [list(m) for m in pb['mouths']] != [list(m) for m in pn['mouths']]:
                problems.append('%s 镜像后口位变了' % new)
        else:
            # 只许动内部装饰 + 地面；外壳 / 口列 / 屋顶一格不许动
            sx, sy, sz = pb['size']
            wy = pb['walk_y']
            b = {s2k(k): v for k, v in pb['blocks'].items()}
            n = {s2k(k): v for k, v in pn['blocks'].items()}
            mouth_cols = {m[1] for m in pb['mouths']}
            for k in set(b) | set(n):
                if b.get(k) == n.get(k):
                    continue
                x, y, z = k
                if x == 0 or x == sx - 1 or z == 0 or z == sz - 1 or y not in (wy - 1, wy):
                    problems.append('%s 动了外壳/屋顶/非地面层 %s' % (new, k))
                elif abs(x - list(mouth_cols)[0]) <= 1 and (z <= 1 or z >= sz - 2):
                    problems.append('%s 动了过道口附近 %s' % (new, k))
    # 丰饶版必须有箱子
    for new, meta in derived_meta.items():
        if not any(v[0] == 'minecraft:chest' for v in pieces[new]['blocks'].values()):
            problems.append('%s 没有箱子' % new)
    if problems:
        for p in problems:
            print('[gp-build] NG', p)
        raise SystemExit('[gp-build] stage1 自检失败：%d 条' % len(problems))


def report_stage1(pieces, derived_meta):
    print('== stage1: 20 件 ==')
    for name in sorted(pieces):
        p = pieces[name]
        mouths = ','.join('%s(%d,%d,%d)' % (m[0], m[1], m[2], m[3]) for m in p['mouths'])
        chests = sum(1 for v in p['blocks'].values() if v[0] == 'minecraft:chest')
        print('  %-20s %-10s %2dx%d x%2d  blocks=%-5d chest=%d walk_y=%d mouths=%s' %
              (name, p['derived'], p['size'][0], p['size'][1], p['size'][2], p['block_count'],
               chests, p['walk_y'], mouths))
    for new, meta in derived_meta.items():
        print('  fertile %-18s patch=%s chest_at=%s' % (new, meta['patch'], meta['chest']))


# ---------------------------------------------------------------- 第 2 步
def jigsaw_nbt(name, target, pool):
    return {'name': name, 'target': target, 'pool': pool,
            'final_state': 'minecraft:air', 'joint': 'aligned',
            'placement_priority': 0, 'selection_priority': 0}


def stage2():
    with open(os.path.join(EVID, 'pieces_stage1.json'), encoding='utf-8') as f:
        data = json.load(f)
    pieces = data['pieces']
    for name, p in pieces.items():
        sx, sy, sz = p['size']
        grid = {s2k(k): v for k, v in p['blocks'].items()}
        spec = SOCK.get(name)
        if spec is None:
            raise SystemExit('[gp-build] %s 没有口位规格' % name)
        seen_sides = set()
        for m in p['mouths']:
            side, cx, dy, cz, d = m
            seen_sides.add(side)
            ent = spec.get(side)
            if ent is None:
                raise SystemExit('[gp-build] %s 的 %s 口没有命名规格' % (name, side))
            sn, tg, pl = ent
            k = (cx, dy, cz)
            if k in grid:
                raise SystemExit('[gp-build] %s 口位 %s 已被 %s 占用' % (name, k, grid[k][0]))
            grid[k] = ['minecraft:jigsaw', {'orientation': '%s_up' % ('north' if side == 'north' else
                                                                     'south' if side == 'south' else
                                                                     'east' if side == 'east' else 'west')},
                       jigsaw_nbt(sn, tg, pl)]
        if seen_sides != set(spec):
            raise SystemExit('[gp-build] %s 口位规格多余：%s vs %s' % (name, seen_sides, set(spec)))
        p['blocks'] = {}
        for k, v in grid.items():
            p['blocks'][k2s(k)] = [v[0], v[1]] + ([v[2]] if len(v) > 2 else [])
        p['block_count'] = len(grid)
    with open(os.path.join(EVID, 'pieces_stage2.json'), 'w', encoding='utf-8') as f:
        json.dump({'pieces': pieces, 'derive_meta': data['derive_meta']}, f,
                  ensure_ascii=False, indent=1, sort_keys=True)
    # 自检：每件的 jigsaw 恰好 = 口数
    bad = 0
    for name, p in pieces.items():
        js = [v for v in p['blocks'].values() if v[0] == 'minecraft:jigsaw']
        if len(js) != len(p['mouths']):
            print('[gp-build] NG %s jigsaw=%d mouths=%d' % (name, len(js), len(p['mouths'])))
            bad += 1
    print('== stage2: jigsaw 注入 ==')
    tot = 0
    for name in sorted(pieces):
        js = [v for v in pieces[name]['blocks'].values() if v[0] == 'minecraft:jigsaw']
        tot += len(js)
        print('  %-20s jigsaw=%d  %s' % (name, len(js),
                                         [(v[1]['orientation'], v[2]['name'], v[2]['target'])
                                          for v in js]))
    print('  total jigsaw = %d' % tot)
    if bad:
        raise SystemExit('[gp-build] stage2 自检失败')


# ---------------------------------------------------------------- NBT 写出
def nbt_string(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def nbt_tag(buf, t, name, val):
    buf += bytes([t]) + nbt_string(name)
    nbt_payload(buf, t, val)


def nbt_payload(buf, t, val):
    if t == 1:
        buf += struct.pack('>b', val)
    elif t == 2:
        buf += struct.pack('>h', val)
    elif t == 3:
        buf += struct.pack('>i', val)
    elif t == 4:
        buf += struct.pack('>q', val)
    elif t == 8:
        buf += nbt_string(val)
    elif t == 9:
        et, items = val
        buf += bytes([et]) + struct.pack('>i', len(items))
        for it in items:
            nbt_payload(buf, et, it)
    elif t == 10:
        for k, (tt, vv) in val.items():
            nbt_tag(buf, tt, k, vv)
        buf += b'\x00'
    else:
        raise ValueError('type %r' % t)


def build_nbt(piece):
    sx, sy, sz = piece['size']
    pal = []
    pal_idx = {}
    blocks_tag = []
    # 逐格写满：件自己的 bbox 内，没有显式方块的格子就是 minecraft:air。
    # 模板空气 = 放置时把地形挖成房间/门洞；只写本件 bbox，件外世界空气一律不带。
    for y in range(sy):
        for z in range(sz):
            for x in range(sx):
                key = k2s((x, y, z))
                v = piece['blocks'].get(key)
                if v is None:
                    nm, pr = 'minecraft:air', {}
                else:
                    nm, pr = v[0], v[1]
                sig = (nm, tuple(sorted(pr.items())))
                if sig not in pal_idx:
                    pal_idx[sig] = len(pal)
                    entry = {'Name': (8, nm)}
                    if pr:
                        entry['Properties'] = (10, {k: (8, str(x)) for k, x in sorted(pr.items())})
                    pal.append(entry)
                b = {'pos': (9, (3, [x, y, z])), 'state': (3, pal_idx[sig])}
                if v is not None and len(v) > 2 and v[2]:
                    be = {'id': (8, 'minecraft:jigsaw')}
                    for k, x2 in v[2].items():
                        if isinstance(x2, int):
                            be[k] = (3, x2)
                        else:
                            be[k] = (8, str(x2))
                    b['nbt'] = (10, be)
                elif nm == 'minecraft:chest':
                    # 逐箱写 LootTable（导出阶段落地，见第 5 步）
                    b['nbt'] = (10, {'id': (8, 'minecraft:chest'), 'LootTable': (8, LOOT)})
                blocks_tag.append(b)
    root = collections.OrderedDict()
    root['DataVersion'] = (3, DATAVERSION)
    root['size'] = (9, (3, [sx, sy, sz]))
    root['palette'] = (9, (10, pal))
    root['blocks'] = (9, (10, blocks_tag))
    root['entities'] = (9, (10, []))
    buf = bytearray()
    nbt_tag(buf, 10, '', root)
    return bytes(buf)


def stage3():
    with open(os.path.join(EVID, 'pieces_stage2.json'), encoding='utf-8') as f:
        pieces = json.load(f)['pieces']
    os.makedirs(RES, exist_ok=True)
    os.makedirs(BP, exist_ok=True)
    manifest = {}
    for name in sorted(pieces):
        raw = build_nbt(pieces[name])
        gz = gzip.compress(raw, 9, mtime=0)   # mtime=0 => 可复现的字节
        path = os.path.join(RES, name + '.nbt')
        with open(path, 'wb') as f:
            f.write(gz)
        # 逐格自检：① 非空气必须与 stage2 完全一致；② bbox 每格都要有（空气写满）。
        _, back = nbt.parse_auto(open(path, 'rb').read())
        got = {}
        pal = back['palette']
        for b in back['blocks']:
            x, y, z = b['pos']
            nm = pal[b['state']]['Name']
            pr = dict(pal[b['state']].get('Properties') or {})
            got[k2s((x, y, z))] = [nm, pr]
        want = {k: [v[0], v[1]] for k, v in pieces[name]['blocks'].items()}
        got_nonair = {k: v for k, v in got.items() if v[0] != 'minecraft:air'}
        if got_nonair != want:
            diff = set(got_nonair) ^ set(want)
            raise SystemExit('[gp-build] %s 逐格自检失败：差异 %d 格 %s' %
                             (name, len(diff), sorted(diff)[:5]))
        sx, sy, sz = pieces[name]['size']
        vol = sx * sy * sz
        if len(got) != vol:
            raise SystemExit('[gp-build] %s 只写了 %d/%d 格（空气没写满）' % (name, len(got), vol))
        air = sum(1 for v in got.values() if v[0] == 'minecraft:air')
        if air != vol - len(want):
            raise SystemExit('[gp-build] %s 空气 %d != 体积-非空气 %d' %
                             (name, air, vol - len(want)))
        if list(back['size']) != pieces[name]['size']:
            raise SystemExit('[gp-build] %s size 不一致' % name)
        manifest[name] = {'file': name + '.nbt', 'size': pieces[name]['size'],
                          'blocks': len(want), 'volume': vol, 'air': air,
                          'sha256': hashlib.sha256(gz).hexdigest(),
                          'loot_chests': sorted(k for k, v in pieces[name]['blocks'].items()
                                                if v[0] == 'minecraft:chest'),
                          'jigsaw': sorted(k for k, v in pieces[name]['blocks'].items()
                                           if v[0] == 'minecraft:jigsaw')}
        print('  nbt %-20s %5d solid + %5d air = %5d cells  %6d B  %s' %
              (name, len(want), air, vol, len(gz), manifest[name]['sha256'][:16]))
    with open(os.path.join(EVID, 'nbt_manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
    # 蓝图
    try:
        draw_blueprints(pieces)
    except ImportError as e:
        print('[gp-build] 蓝图跳过（缺 Pillow）：%s' % e)
    print('== stage3: 导出 %d 个 .nbt 到 %s ==' % (len(manifest), RES))


def draw_blueprints(pieces):
    from PIL import Image, ImageDraw
    S = 9      # 每格像素
    PAD_L, PAD_T, PAD_R, PAD_B = 46, 58, 56, 44
    index = []
    for name in sorted(pieces):
        p = pieces[name]
        sx, sy, sz = p['size']
        wy = p['walk_y']
        w = max(PAD_L + sx * S + PAD_R, 420)
        h = PAD_T + sz * S + PAD_B
        img = Image.new('RGB', (w, h), (18, 18, 22))
        d = ImageDraw.Draw(img)
        d.text((8, 6), '%s  %dx%dx%d' % (name.upper(), sx, sy, sz), fill=(240, 232, 200))
        d.text((8, 20), 'floor plan @ dy=%d  (N up, x right, z down)' % wy, fill=(150, 150, 160))
        d.text((8, 34), 'origin = NW corner of the structure box;  N/S/E/W = world axes',
               fill=(110, 110, 120))
        grid = {s2k(k): v for k, v in p['blocks'].items()}
        for z in range(sz):
            for x in range(sx):
                v = grid.get((x, wy, z))
                below = grid.get((x, wy - 1, z))
                if v is None:
                    # 空气：底下实心 => 可走
                    walk = below is not None and below[0] not in NOT_WALKABLE
                    col = (58, 92, 70) if walk else (28, 28, 33)
                else:
                    col = COLORS.get(v[0], UNKNOWN_COLOR)
                px, py = PAD_L + x * S, PAD_T + z * S
                d.rectangle([px, py, px + S - 1, py + S - 1], fill=col)
                if v is not None and v[0] == 'minecraft:jigsaw':
                    d.text((px + 1, py), 'J', fill=(0, 0, 0))
                elif v is not None and v[0] == 'minecraft:chest':
                    d.text((px + 1, py), 'C', fill=(255, 255, 255))
                elif v is not None and 'spawner' in v[0]:
                    d.text((px + 1, py), 'S', fill=(200, 240, 255))
        # 坐标刻度
        for x in range(0, sx, 5):
            px = PAD_L + x * S
            d.line([px, PAD_T - 4, px, PAD_T + sz * S], fill=(70, 70, 78))
            d.text((px - 2, PAD_T - 16), str(x), fill=(170, 170, 180))
        for z in range(0, sz, 5):
            py = PAD_T + z * S
            d.line([PAD_L - 4, py, PAD_L + sx * S, py], fill=(70, 70, 78))
            d.text((PAD_L - 26, py - 3), str(z), fill=(170, 170, 180))
        # N/S/E/W
        d.text((PAD_L + sx * S // 2 - 3, PAD_T + sz * S + 6), 'S', fill=(120, 200, 255))
        d.text((PAD_L + sx * S // 2 - 3, PAD_T - 14), 'N', fill=(120, 200, 255))
        d.text((PAD_L - 34, PAD_T + sz * S // 2), 'W', fill=(120, 200, 255))
        d.text((PAD_L + sx * S + 8, PAD_T + sz * S // 2), 'E', fill=(120, 200, 255))
        # legend
        d.text((8, h - 20), 'J=jigsaw  C=chest  S=spawner   green=walkable air',
               fill=(140, 140, 150))
        fn = name.upper() + '.png'
        img.save(os.path.join(BP, fn))
        index.append((name, fn, sx, sy, sz, p['block_count']))
    with open(os.path.join(BP, 'README.md'), 'w', encoding='utf-8') as f:
        f.write('# 金之牢狱 —— 20 件俯视蓝图\n\n'
                '> 由 `docs\\金之牢狱-实现-证据\\gp_build.py` 第 3 步生成，**给作者过目**。\n'
                '> 每张图是「可行走面那一层（walk_y）」的平面图：绿 = 能站的空气，金 = 作者原有金方块，\n'
                '> 洋红 `J` = `minecraft:jigsaw` 口位，`C` = 箱子，`S` = 刷怪笼。N 在上方。\n\n'
                '| 件 | 图 | 尺寸 x·y·z | 方块数 |\n|---|---|---|---|\n')
        for name, fn, sx, sy, sz, bc in index:
            f.write('| `%s` | [%s](%s) | %d×%d×%d | %d |\n' % (name, fn, fn, sx, sy, sz, bc))
    print('== 蓝图 %d 张 -> %s ==' % (len(index), BP))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='all')
    a = ap.parse_args()
    if a.stage in ('1', 'all'):
        stage1()
    if a.stage in ('2', 'all'):
        stage2()
    if a.stage in ('3', 'all'):
        stage3()
    if a.stage in ('4', 'all'):
        stage4()
    if a.stage in ('5', 'all'):
        stage5()


# ---------------------------------------------------------------- 第 4 步：worldgen
WG = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'worldgen')
# 池 -> (元素 [(模板, 权重)], fallback)
POOLS = collections.OrderedDict([
    ('start', ([(('treasure'), 1)], 'minecraft:empty')),
    ('lane', ([(('lane'), 1)], POOL + 'exit')),
    ('room', ([('cell_medium_a', 3), ('cell_medium_b', 2), ('cell_medium_c', 2), ('cell_medium_mirror', 3),
               ('cell_large_a', 3), ('cell_large_b', 2), ('cell_large_c', 2), ('cell_large_mirror', 2),
               ('cross_a', 3), ('cross_b', 3), ('cell_small_b', 2), ('cell_small_c', 2)],
              'minecraft:empty')),
    ('exit', ([('exit', 1)], 'minecraft:empty')),
    # 小牢房三步循环：1(A) -> 2(镜像) -> 3(丰饶) -> 回过道；fallback 指向自己 => 深度截断时仍补齐下一步
    ('cell_small_1', ([('cell_small_a', 1)], POOL + 'cell_small_1')),
    ('cell_small_2', ([('cell_small_mirror', 1)], POOL + 'cell_small_2')),
    ('cell_small_3', ([('cell_small_fertile', 1)], POOL + 'cell_small_3')),
    ('cell_medium_1', ([('cell_medium_a', 1)], 'minecraft:empty')),
    ('cell_medium_2', ([('cell_medium_mirror', 1)], 'minecraft:empty')),
    ('cell_medium_3', ([('cell_medium_fertile', 1)], 'minecraft:empty')),
    ('cell_large_1', ([('cell_large_a', 1)], 'minecraft:empty')),
    ('cell_large_2', ([('cell_large_mirror', 1)], 'minecraft:empty')),
    ('cell_large_3', ([('cell_large_fertile', 1)], 'minecraft:empty')),
    ('cross_a', ([('cross_a', 1)], 'minecraft:empty')),
    ('cross_b', ([('cross_b', 1)], 'minecraft:empty')),
])

STRUCTURE = {
    'type': 'minecraft:jigsaw',
    'biomes': '#minecraft:is_nether',
    'step': 'underground_structures',
    'spawn_overrides': {},
    'terrain_adaptation': 'bury',
    'start_pool': POOL + 'start',
    'size': 6,
    'start_height': {'type': 'minecraft:uniform',
                     'min_inclusive': {'absolute': 31},
                     'max_inclusive': {'absolute': 41}},
    'use_expansion_hack': False,
    'max_distance_from_center': 100,
}

STRUCTURE_SET = {
    'structures': [{'structure': 'bettergold:golden_prison', 'weight': 1}],
    'placement': {
        'type': 'minecraft:random_spread',
        # 第三轮（2026-10-20）：作者「结构生成率的话跟下界要塞相同吧」⇒ 照抄原版
        # nether_complexes 的 spacing/separation（27/4）。旧值 32/16 是第 1~2 轮的记账值（留档）。
        'spacing': 27,
        'separation': 4,
        # salt 故意保持我们自己的：同 salt + 同种子 ⇒ 候选区块与下界要塞/堡垒重合
        'salt': 19710101,
        # 原版 nether_complexes 省略该字段 ⇒ codec 默认 linear（别按印象填 triangular）
        'spread_type': 'linear',
    },
}


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    txt = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)


def stage4():
    for name, (els, fb) in POOLS.items():
        obj = {'fallback': fb, 'elements': [
            {'weight': w, 'element': {'element_type': 'minecraft:single_pool_element',
                                      'location': '%s:%s%s' % (NS, 'golden_prison/', t),
                                      'processors': 'minecraft:empty',
                                      'projection': 'rigid'}} for (t, w) in els]}
        write_json(os.path.join(WG, 'template_pool', 'golden_prison', name + '.json'), obj)
    write_json(os.path.join(WG, 'structure', 'golden_prison.json'), STRUCTURE)
    write_json(os.path.join(WG, 'structure_set', 'golden_prison.json'), STRUCTURE_SET)
    print('== stage4: worldgen JSON ==')
    print('  structure_set: spacing=27 separation=4 salt=19710101 weight=1'
          '（= 下界要塞的 spacing/separation；旧 32/16 已按作者第三轮要求改掉）')
    print('  structure    : size=%d start_height=31..41 biomes=#minecraft:is_nether step=underground_structures'
          ' terrain_adaptation=%s max_distance_from_center=%d'
          % (STRUCTURE['size'], STRUCTURE['terrain_adaptation'], STRUCTURE['max_distance_from_center']))
    for name, (els, fb) in POOLS.items():
        print('  pool %-16s elements=%s fallback=%s' %
              (name, ['%s x%d' % (t, w) for (t, w) in els], fb))


# ---------------------------------------------------------------- 第 5 步：战利品
LOOT_DIR = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'loot_table', 'chests')
LOOT_TABLE = os.path.join(LOOT_DIR, 'golden_prison.json')
TAG_DIR = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'tags')

# xlsx「战利品掉落表」的 28 个物品行（#1「无」按作者口径删掉：没有空箱率）
# 每行: (id 或 tag, 最小, 最大, 权重, 附加 functions)
LOOT_ROWS = [
    ('minecraft:gold_nugget', 6, 15, 7, []),
    ('minecraft:gold_ingot', 1, 15, 5, []),
    ('minecraft:raw_gold', 1, 15, 5, []),
    ('bettergold:golden_cowrie', 1, 3, 5, []),
    ('minecraft:enchanted_book', 1, 1, 5,
     [{'function': 'minecraft:enchant_randomly',
       'options': '#bettergold:golden_prison/any_enchantment'}]),
    ('bettergold:gift_gold_ticket', 1, 3, 4, []),
    ('bettergold:small_netherite_scrap', 1, 3, 4, []),
    ('minecraft:golden_apple', 1, 5, 3, []),
    ('minecraft:golden_carrot', 1, 3, 3, []),
    ('bettergold:golden_egg', 1, 5, 3, []),
    ('minecraft:enchanted_book', 1, 1, 3,
     [{'function': 'minecraft:enchant_randomly', 'options': 'bettergold:take_gold_food'}]),
    ('bettergold:golden_wheat_seeds', 1, 3, 3, []),
    ('bettergold:golden_wheat', 1, 4, 3, []),
    ('bettergold:chaos_coin', 1, 15, 3, []),
    ('bettergold:chaos_coin_string', 1, 3, 3, []),
    ('bettergold:golden_eggplant_seeds', 1, 5, 2, []),
    ('bettergold:golden_eggplant', 1, 3, 2, []),
    ('#bettergold:golden_prison/golden_equipment', 1, 1, 2,
     [{'function': 'minecraft:enchant_randomly'}]),
    ('bettergold:golden_cowrie_mold', 1, 1, 2, []),
    ('bettergold:chaosgold_nugget', 1, 5, 2, []),
    ('minecraft:netherite_scrap', 1, 3, 2, []),
    ('minecraft:golden_horse_armor', 1, 1, 2, []),
    ('bettergold:idol_gift_box', 1, 1, 2, []),
    ('bettergold:gourmet_box', 1, 2, 2, []),
    ('minecraft:enchanted_golden_apple', 1, 2, 1, []),
    ('minecraft:netherite_ingot', 1, 1, 1, []),
    ('bettergold:chaosgold_ingot', 1, 1, 1, []),
]

GOLDEN_EQUIPMENT = ['minecraft:golden_helmet', 'minecraft:golden_chestplate', 'minecraft:golden_leggings',
                    'minecraft:golden_boots', 'minecraft:golden_sword', 'minecraft:golden_pickaxe',
                    'minecraft:golden_axe', 'minecraft:golden_shovel', 'minecraft:golden_hoe']


def stage5():
    entries = []
    for ident, mn, mx, w, funcs in LOOT_ROWS:
        e = {'weight': w}
        if ident.startswith('#'):
            e['type'] = 'minecraft:tag'
            e['name'] = ident[1:]
            e['expand'] = False
        else:
            e['type'] = 'minecraft:item'
            e['name'] = ident
        f = list(funcs)
        if mn == mx:
            if mn != 1:
                f.append({'function': 'minecraft:set_count', 'count': mn})
        else:
            f.append({'function': 'minecraft:set_count',
                      'count': {'type': 'minecraft:uniform', 'min': mn, 'max': mx}})
        if f:
            e['functions'] = f
        entries.append(e)
    loot = {
        'type': 'minecraft:chest',
        'pools': [{
            'rolls': {'type': 'minecraft:uniform', 'min': 5, 'max': 10},
            # 幸运：LootPool#addRandomItems 的 rolls = rolls + floor(bonus_rolls * luck)
            'bonus_rolls': 1.0,
            'entries': entries,
        }],
        'random_sequence': 'bettergold:chests/golden_prison',
    }
    write_json(LOOT_TABLE, loot)
    write_json(os.path.join(TAG_DIR, 'item', 'golden_prison', 'golden_equipment.json'),
               {'replace': False, 'values': GOLDEN_EQUIPMENT})
    # 附魔 tag：全本原版附魔（非宝藏 + 宝藏 = 42 条）⇒ 自动排除 bettergold:take_gold_food
    write_json(os.path.join(TAG_DIR, 'enchantment', 'golden_prison', 'any_enchantment.json'),
               {'replace': False, 'values': ['#minecraft:non_treasure', '#minecraft:treasure']})
    tot = sum(w for (_, _, _, w, _) in LOOT_ROWS)
    print('== stage5: 战利品表 ==')
    print('  entries=%d  weight_sum=%d  rolls=uniform 5..10  bonus_rolls=1.0  no-empty-entry' %
          (len(entries), tot))
    print('  chests in templates: %d' % sum(
        1 for f in os.listdir(RES) if f.endswith('.nbt')))



if __name__ == '__main__':
    main()
