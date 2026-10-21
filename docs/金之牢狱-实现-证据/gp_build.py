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
import copy
import gzip
import hashlib
import json
import os
import struct
import sys

try:                     # 兜底：Windows 控制台默认 GBK，遇到 ⇒ / 中文标点会 UnicodeEncodeError
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

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
    # ★ 第五轮：出入口的口 target 从 room 改成 empty（任务书第 3 步）——
    #   它只在"深度到顶"时被放（JigsawPlacement:474 不再入队），但万一被放在更浅的深度，
    #   target=room 会让它继续长；改成 minecraft:empty = 引擎的"空池"，既不再展开也不会报
    #   "Empty or non-existent pool"（Pools.EMPTY 是白名单）。
    'exit':        {'north': ('lane', 'empty', 'minecraft:empty')},
    # ★ 第五轮：过道两口改成**对称**（都 name=lane / target=room）——
    #   旧的"南口进小牢房链"是序列固定的根因之一（见 §11）；现在两口等价，引擎挑哪个旋转都成立。
    'lane':        {'north': ('lane', 'room', POOL + 'room'),
                    'south': ('lane', 'room', POOL + 'room')},
    # 中/大/小牢房：两个口同名同目标 => 无论引擎选中哪个旋转都成立
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
    # ★ 第五轮：小牢房也进同一个 room 池、按权重随机（不再有 cell_small_1→2→3 硬循环）
    'cell_small_a':      {'north': ('room', 'lane', POOL + 'lane'),
                          'south': ('room', 'lane', POOL + 'lane')},
    'cell_small_b':      {'north': ('room', 'lane', POOL + 'lane'),
                          'south': ('room', 'lane', POOL + 'lane')},
    'cell_small_c':      {'north': ('room', 'lane', POOL + 'lane'),
                          'south': ('room', 'lane', POOL + 'lane')},
    'cell_small_mirror': {'north': ('room', 'lane', POOL + 'lane'),
                          'south': ('room', 'lane', POOL + 'lane')},
    'cell_small_fertile': {'north': ('room', 'lane', POOL + 'lane'),
                           'south': ('room', 'lane', POOL + 'lane')},
}

AIR = {'minecraft:air'}
NOT_WALKABLE = {'minecraft:air', 'minecraft:structure_void'}

# ---------------------------------------------------------------- 第五轮：实体 / 方块实体源
# ★ 为什么不能从 +512 展示区读：作者当年是「把方块搬过去、BE 与实体留给原地」
#   （拼接分析 §2.4）。+512 的 14 个件是**纯方块副本**（BE = 0、entities = 0，本轮实测）。
#   实体（6 个 glow_item_frame）与 53 个件的 BE（39 spawner + 14 chest）**全部还在原件区**。
#   所以 BE / 实体的坐标一律「原件区坐标 − 原件区原点」，不是 +512 那边。
#   12 个大件的原件区 = 展示区 − (512, 0, 512)；lane / exit 只平移了 z（x 仍是 3）。
SRC_NEG = {
    'treasure': (-115, -60, -21), 'cross_a': (-91, -60, -77), 'cross_b': (-91, -60, -37),
    'cell_large_a': (-51, -60, -99), 'cell_large_b': (-51, -60, -65), 'cell_large_c': (-51, -60, -31),
    'cell_medium_a': (-33, -60, -69), 'cell_medium_b': (-33, -60, -45), 'cell_medium_c': (-33, -60, -21),
    'cell_small_a': (-15, -60, -39), 'cell_small_b': (-15, -60, -25), 'cell_small_c': (-15, -60, -11),
    'lane': (3, -60, -11), 'exit': (3, -60, -5),
}

# 实体 Facing(0..5=down/up/north/south/west/east) -> 它「贴着的支撑方块」的偏移（= facing 的反方向）
FACE_OPP = {0: (0, 1, 0), 1: (0, -1, 0), 2: (0, 0, 1), 3: (0, 0, -1), 4: (1, 0, 0), 5: (-1, 0, 0)}

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


def load_entities():
    """实体区（entities/*.mca）的原始 NBT —— 逐字段照抄，不做任何"重新生成"。"""
    out = []
    ed = os.path.join(WORLD, 'entities')
    for fn in sorted(os.listdir(ed)):
        if not fn.endswith('.mca'):
            continue
        for cx, cz, root, comp in nbt.parse_region(os.path.join(ed, fn)):
            for e in (root.get('Entities') or []):
                out.append(e)
    return out


def load_block_entities():
    """region 里**全部**方块实体的完整 NBT，键 = 绝对坐标。"""
    out = {}
    rd = os.path.join(WORLD, 'region')
    for fn in sorted(os.listdir(rd)):
        if not fn.endswith('.mca'):
            continue
        for cx, cz, root, comp in nbt.parse_region(os.path.join(rd, fn)):
            for b in (root.get('block_entities') or []):
                out[(b['x'], b['y'], b['z'])] = b
    return out


def k2s(pos):
    return '%d,%d,%d' % pos


def s2k(s):
    a = s.split(',')
    return (int(a[0]), int(a[1]), int(a[2]))


# ---------------------------------------------------------------- 第 1 步
def piece_entities(ents, origin, size):
    """件内实体：Pos -> 件内相对坐标、TileX/Y/Z -> 件内相对格；其余字段逐字照抄。

    ⚠ 判定用**实体自己占的格子**（HangingEntity 的 Tile = 它自己的格子，
    支撑方块 = Tile + facing 的反方向，见 ItemFrame#setDirection / BlockAttachedEntity#setPos）。
    """
    ox, oy, oz = origin
    sx, sy, sz = size
    out = []
    for e in ents:
        tx, ty, tz = e['TileX'], e['TileY'], e['TileZ']
        if not (ox <= tx < ox + sx and oy <= ty < oy + sy and oz <= tz < oz + sz):
            continue
        ent = copy.deepcopy(e)
        pos = list(ent['Pos'])
        rel_pos = [pos[0] - ox, pos[1] - oy, pos[2] - oz]
        rel_tile = [tx - ox, ty - oy, tz - oz]
        # 模板格式：pos = 实体坐标（相对）、blockPos = Tile（相对）、nbt = 实体存档（Pos/Tile 也写相对）
        ent['Pos'] = rel_pos
        ent['TileX'], ent['TileY'], ent['TileZ'] = rel_tile
        out.append({'pos': rel_pos, 'blockPos': rel_tile, 'nbt': ent})
    return out


def piece_bes(bes, origin, size):
    """件内方块实体：完整 NBT 照抄，只把 x/y/z 改写成件内相对坐标。"""
    ox, oy, oz = origin
    sx, sy, sz = size
    out = {}
    for (bx, by, bz), b in bes.items():
        if not (ox <= bx < ox + sx and oy <= by < oy + sy and oz <= bz < oz + sz):
            continue
        d = copy.deepcopy(b)
        d['x'], d['y'], d['z'] = bx - ox, by - oy, bz - oz
        out[k2s((bx - ox, by - oy, bz - oz))] = d
    return out


def extract(blocks, ents, bes):
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
                        'size': [sx, sy, sz], 'blocks': sub, 'derived': 'original',
                        'entities': piece_entities(ents, SRC_NEG[name], (sx, sy, sz)),
                        'block_entities': piece_bes(bes, SRC_NEG[name], (sx, sy, sz))}
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


def mirror_entities(ents, sx):
    """南北轴镜像：Pos 的 x -> sx - x，Tile 的 x -> sx-1-x，facing east<->west，yaw 取反。"""
    out = []
    for e in ents:
        d = copy.deepcopy(e)
        d['pos'][0] = sx - d['pos'][0]
        d['blockPos'][0] = sx - 1 - d['blockPos'][0]
        n = d['nbt']
        n['Pos'][0] = d['pos'][0]
        n['TileX'] = d['blockPos'][0]
        if 'Facing' in n:
            n['Facing'] = {4: 5, 5: 4}.get(n['Facing'], n['Facing'])
        if 'Rotation' in n:
            n['Rotation'] = [-n['Rotation'][0], n['Rotation'][1]]
        out.append(d)
    return out


def mirror_bes(bes, sx):
    out = {}
    for key, b in bes.items():
        x, y, z = s2k(key)
        d = copy.deepcopy(b)
        d['x'] = sx - 1 - x
        out[k2s((sx - 1 - x, y, z))] = d
    return out


def chest_be(x, y, z):
    """派生件（丰饶版）新放的箱子：与源件同款 BE（Items 空）+ 本仓 LootTable。"""
    return {'id': 'minecraft:chest', 'keepPacked': 0, 'Items': [], 'LootTable': LOOT,
            'x': x, 'y': y, 'z': z}


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


# ---------------------------------------------------------------- 第五轮：出入口「上升段」
# ★ 为什么只能做进 exit.nbt：JigsawPlacement.java:474 `if (depth + 1 <= this.maxDepth)` ——
#   件只有在这个条件下才会被重新入队展开。exit 是 lane 池的 **fallback**，正常情况下
#   在 depth == maxDepth 那一层被放（且 fallback 件本身不再入队）⇒ **挂在 exit 顶上的
#   up_jigsaw 永远不会被展开**。所以"从链尾向上接"只能做成同一个模板里的上升段。
# 造型只用作者已有的方块（gold_bricks / gold_pillar），不引入新方块；井口朝天。
EXIT_SHAFT_H = 36          # 上升段层数（门楼仍是原样的 8 层，井筒在它上面）
EXIT_ROOF_OPEN = (1, 3, 1, 3)   # 打通屋顶的 x/z 范围（x1..3, z1..3）；y=6 全开、y=7 只开 z1..2


def extend_exit(piece):
    """给 exit 加「上升段」：屋顶开井 + 5×5 井筒（内 3×3、井口朝天）。门楼 8 层一格不动。

    ⚠ 必须从 y=4 开始打通：门楼的可走空间只有 y=1..3，y=4..7 是作者的屋顶/装饰层
    （y=4 是一整层实心 + 柱子、y=5..7 是楼梯/台阶/结构空）。只在 y=6..7 开洞的话，
    井筒和门楼之间还隔着一层实心屋顶 —— 洪泛到不了（本轮实测：从口洪泛只到 9.14%）。
    打通的只有 x1..3 / z1..2 这 3×2 列，**z=3 那一列（展示框的支撑方块）保留**。
    """
    sx, sy, sz = piece['size']
    grid = {s2k(k): v for k, v in piece['blocks'].items()}
    opened = []
    for y in range(4, 8):
        for x in range(1, sx - 1):
            for z in (1, 2):
                if grid.pop((x, y, z), None) is not None:
                    opened.append([x, y, z])
    for y in range(sy, sy + EXIT_SHAFT_H):
        for x in range(sx):
            for z in range(sz):
                if x in (0, sx - 1) or z in (0, sz - 1):
                    corner = (x in (0, sx - 1)) and (z in (0, sz - 1))
                    if corner:
                        grid[(x, y, z)] = ['bettergold:gold_pillar', {'axis': 'y'}]
                    else:
                        grid[(x, y, z)] = ['bettergold:gold_bricks', {}]
    piece['size'] = [sx, sy + EXIT_SHAFT_H, sz]
    piece['blocks'] = {k2s(k): v for k, v in grid.items()}
    piece['block_count'] = len(grid)
    piece['shaft'] = {'h': EXIT_SHAFT_H, 'shaft_from_y': sy, 'top_y': sy + EXIT_SHAFT_H - 1,
                      'opened_cells': len(opened),
                      'rim': 'gold_bricks + gold_pillar(axis=y) corners，井口 3×3 朝天'}
    print('  [exit] 上升段 +%d 层 ⇒ size=%s top_y=%d 开顶 %d 格'
          % (EXIT_SHAFT_H, piece['size'], sy + EXIT_SHAFT_H - 1, len(opened)))
    return piece


def stage1():
    blocks = load_world()
    ents = load_entities()
    bes = load_block_entities()
    pieces = extract(blocks, ents, bes)
    print('== stage1 实体 / 方块实体（源存档原件区）==')
    print('  源实体 %d 个；源方块实体 %d 个（件内 %d）' %
          (len(ents), len(bes), sum(len(p['block_entities']) for p in pieces.values())))
    for name in sorted(pieces):
        p = pieces[name]
        print('  %-18s entities=%d bes=%d %s' %
              (name, len(p['entities']), len(p['block_entities']),
               [(e['nbt']['id'], e['blockPos']) for e in p['entities']]))
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
        # 实体检查：展示框的支撑方块必须在件内是「实心非空气」（否则放置后存活不了）
        for e in p['entities']:
            n = e['nbt']
            bx, by, bz = e['blockPos']
            fx = FACE_OPP[n['Facing']]
            sup = (bx + fx[0], by + fx[1], bz + fx[2])
            sv = grid.get(sup)
            if sv is None or sv[0] in NOT_WALKABLE:
                raise SystemExit('[gp-build] %s 的实体 %s 支撑方块 %s 不是实心（%s）' %
                                 (name, n['id'], sup, sv and sv[0]))
            e['support'] = list(sup)
            e['support_block'] = sv[0]
    # 派生
    derived_meta = {}
    for new, base in DERIVE:
        if new.endswith('_mirror'):
            sx = pieces[base]['size'][0]
            pieces[new] = {'name': new, 'src': pieces[base]['src'], 'note': '%s 的南北轴镜像' % base,
                           'size': list(pieces[base]['size']), 'blocks': mirror_piece(pieces[base]),
                           'derived': 'mirror', 'base': base,
                           'entities': mirror_entities(pieces[base]['entities'], sx),
                           'block_entities': mirror_bes(pieces[base]['block_entities'], sx)}
            pieces[new]['mouths'] = [list(m) for m in pieces[base]['mouths']]
            pieces[new]['block_count'] = len(pieces[new]['blocks'])
            pieces[new]['walk_y'] = pieces[base]['walk_y']
        else:
            b = {s2k(k): v for k, v in pieces[base]['blocks'].items()}
            nb, meta = fertile_piece(pieces[base], pieces, pieces[base]['mouths'])
            pieces[new] = {'name': new, 'src': pieces[base]['src'],
                           'note': '%s 的丰饶变体（农田/金蟾/箱取自 P02、P03）' % base,
                           'size': list(pieces[base]['size']), 'blocks': nb,
                           'derived': 'fertile', 'base': base,
                           'entities': copy.deepcopy(pieces[base]['entities']),
                           'block_entities': copy.deepcopy(pieces[base]['block_entities'])}
            pieces[new]['mouths'] = [list(m) for m in pieces[base]['mouths']]
            pieces[new]['block_count'] = len(nb)
            pieces[new]['walk_y'] = pieces[base]['walk_y']
            # 丰饶版新放的箱子需要有 BE（否则放置后是无战利品的空箱）
            cx, cy, cz = meta['chest'][0], meta['walk_y'], meta['chest'][1]
            ck = k2s((cx, cy, cz))
            if ck not in pieces[new]['block_entities']:
                pieces[new]['block_entities'][ck] = chest_be(cx, cy, cz)
            derived_meta[new] = meta
    extend_exit(pieces['exit'])
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
    elif t == 5:
        buf += struct.pack('>f', val)
    elif t == 6:
        buf += struct.pack('>d', val)
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
    elif t == 11:              # TAG_Int_Array（实体 UUID 必须保留这个类型，否则 Entity#load 读不到）
        buf += struct.pack('>i', len(val))
        for v in val:
            buf += struct.pack('>i', v)
    else:
        raise ValueError('type %r' % t)


# 解析器不保留类型，写回实体/BE NBT 时按「已知键」还原类型（错了实体/方块实体会读不到字段）
LIST_TYPES = {'Pos': 6, 'Motion': 6, 'Rotation': 5}


def nbt_obj(obj, key=''):
    """把解析出来的 python 值写回带类型的 NBT 值。"""
    if isinstance(obj, bool):
        return (1, 1 if obj else 0)
    if isinstance(obj, int):
        return (3, obj)
    if isinstance(obj, float):
        return (6, obj)
    if isinstance(obj, str):
        return (8, obj)
    if isinstance(obj, list):
        if key in LIST_TYPES:
            et = LIST_TYPES[key]
            return (9, (et, [float(x) for x in obj]))
        if key == 'UUID' and len(obj) == 4:
            return (11, [int(x) for x in obj])
        return (9, (10, [nbt_obj(x)[1] for x in obj]))
    if isinstance(obj, dict):
        return (10, collections.OrderedDict((k, nbt_obj(v, k)) for k, v in obj.items()))
    raise ValueError('nbt_obj: unsupported %r' % (obj,))


def be_tag(be):
    t = nbt_obj(be)
    if t[0] != 10:
        raise SystemExit('[gp-build] BE 不是 compound: %r' % (be,))
    return t


def build_nbt(piece):
    sx, sy, sz = piece['size']
    pal = []
    pal_idx = {}
    blocks_tag = []
    bes = piece.get('block_entities') or {}
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
                    jb = {'id': (8, 'minecraft:jigsaw')}
                    for k, x2 in v[2].items():
                        if isinstance(x2, int):
                            jb[k] = (3, x2)
                        else:
                            jb[k] = (8, str(x2))
                    b['nbt'] = (10, jb)
                elif key in bes:
                    # ★ 源存档里的完整 BE（spawner 的 SpawnData/SpawnPotentials/Delay、
                    #   chest 的 Items…），坐标已是件内相对坐标；箱子再补我们的 LootTable。
                    be = copy.deepcopy(bes[key])
                    if nm == 'minecraft:chest':
                        be['LootTable'] = LOOT
                    b['nbt'] = be_tag(be)
                elif nm == 'minecraft:chest':
                    b['nbt'] = be_tag(chest_be(x, y, z))
                blocks_tag.append(b)
    ents_tag = []
    for e in (piece.get('entities') or []):
        ents_tag.append(collections.OrderedDict([
            ('pos', (9, (6, [float(x) for x in e['pos']]))),
            ('blockPos', (9, (3, [int(x) for x in e['blockPos']]))),
            ('nbt', nbt_obj(e['nbt'])),
        ]))
    root = collections.OrderedDict()
    root['DataVersion'] = (3, DATAVERSION)
    root['size'] = (9, (3, [sx, sy, sz]))
    root['palette'] = (9, (10, pal))
    root['blocks'] = (9, (10, blocks_tag))
    root['entities'] = (9, (10, ents_tag))
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
        # ③ 实体段逐条回读：数量、id、Item、blockPos 必须与源存档逐条相等
        src_ents = pieces[name].get('entities') or []
        got_ents = back.get('entities') or []
        if len(got_ents) != len(src_ents):
            raise SystemExit('[gp-build] %s 实体数 %d != 源 %d' %
                             (name, len(got_ents), len(src_ents)))
        for ge in got_ents:
            sn = ge['nbt']
            match = [se for se in src_ents
                     if se['nbt']['id'] == sn['id'] and se['blockPos'] == list(ge['blockPos'])]
            if not match:
                raise SystemExit('[gp-build] %s 实体回读对不上：%s %s' %
                                 (name, sn['id'], ge['blockPos']))
            if 'Item' in match[0]['nbt'] and sn.get('Item') != match[0]['nbt']['Item']:
                raise SystemExit('[gp-build] %s 实体 Item 丢了：%s' % (name, sn.get('Item')))
        # ④ 方块实体段逐条回读：数量相等 + spawner 的 SpawnData / chest 的 LootTable 都在
        src_bes = pieces[name].get('block_entities') or {}
        got_bes = {}
        for b in back['blocks']:
            if 'nbt' in b and pal[b['state']]['Name'] != 'minecraft:jigsaw':
                got_bes[k2s(tuple(b['pos']))] = b['nbt']
        if len(got_bes) != len(src_bes):
            raise SystemExit('[gp-build] %s 方块实体 %d != 源 %d' %
                             (name, len(got_bes), len(src_bes)))
        for k, sb in src_bes.items():
            gb = got_bes.get(k)
            if gb is None:
                raise SystemExit('[gp-build] %s 缺方块实体 %s' % (name, k))
            if sb['id'] == 'minecraft:mob_spawner':
                if (gb.get('SpawnData') or {}).get('entity', {}).get('id') != \
                        (sb.get('SpawnData') or {}).get('entity', {}).get('id'):
                    raise SystemExit('[gp-build] %s 刷怪笼 SpawnData 丢了 %s' % (name, k))
            if sb['id'] == 'minecraft:chest' and gb.get('LootTable') != LOOT:
                raise SystemExit('[gp-build] %s 箱子缺 LootTable %s' % (name, k))
        manifest[name] = {'file': name + '.nbt', 'size': pieces[name]['size'],
                          'blocks': len(want), 'volume': vol, 'air': air,
                          'sha256': hashlib.sha256(gz).hexdigest(),
                          'entities': len(got_ents),
                          'entity_ids': sorted(set(e['nbt']['id'] for e in got_ents)),
                          'block_entities': len(got_bes),
                          'be_ids': sorted(set(v['id'] for v in got_bes.values())),
                          'loot_chests': sorted(k for k, v in pieces[name]['blocks'].items()
                                                if v[0] == 'minecraft:chest'),
                          'jigsaw': sorted(k for k, v in pieces[name]['blocks'].items()
                                           if v[0] == 'minecraft:jigsaw')}
        print('  nbt %-20s %5d solid + %5d air = %5d cells  ent=%d be=%d  %6d B  %s' %
              (name, len(want), air, vol, len(got_ents), len(got_bes), len(gz),
               manifest[name]['sha256'][:16]))
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

# ★ 第五轮（2026-10-21）：池子从「按序号链」改成「按权重随机」。
#   旧口径（1~4 轮，原文留档）：room 12 条 + cell_small_1..3 三段硬循环 ⇒ 序列固定。
#   新口径：**所有池的 fallback 都是 exit**（唯一的例外是 start 与 exit 自己），
#   于是「深度到顶 / 普通元素放不下」时一定收敛到出入口 ⇒ 落单口 = 0 的机制保证。
#   权重记账（第五轮）：每个尺寸 5 个变体（a=2 b=2 c=2 mirror=2 fertile=6）=> 14/尺寸、三种尺寸 42；
#   再加 cross_a=5 / cross_b=5 = **总权重 52**。
#   ⇒ P(一次 room 抽到丰饶) = 18/52 = 34.6%
#   ⇒ P(连续 3 个 room 至少一个丰饶) = 1-(34/52)^3 = 72.0%（旧口径是"必含"，见 §11 记账）
#   ⚠ max_distance_from_center 100 → **128**：JigsawStructure.verifyRange 在 terrain_adaptation=NONE
#     时 padding=0 ⇒ 上限就是 128；100 会把"离中心 ~100 格之外"的口裁掉（A 级实测 2/10 个种子
#     各留 1 个落单口，全部落在距中心 99~103 格内那一圈）⇒ 改到 128 后落单口 = 0。
#
# ★ 第六轮（本文件所在轮，2026-10-21）：丰饶权重 6 → **10**（作者放行"按推荐方案落地"）。
#   旧口径原文留档在上面（fertile=6 / 总权重 52 / P(3 连)=72.0%），不删。
#   新记账（**按文件里实际的三条 fertile 元素各 10 算**）：
#     每个尺寸 4 个普通变体 2×4=8 + fertile 10 = 18/尺寸、三种尺寸 54；+ cross_a 5 + cross_b 5
#     ⇒ **总权重 = 64**；非丰饶 = 24 + 10 = **34**。
#     一次 room 抽到丰饶 = 30/64 = 46.875%
#     P(连续 3 个 room 至少一个丰饶) = 1-(34/64)^3 = **0.8501 = 85.0%**（旧 72.0%）。
#   ⚠ 任务书里写的「新总权重 = 56 ⇒ 1-(46/56)^3 ≈ 82.x%」是按**一条** fertile 元素记的账
#     （52-6=46 非丰饶、52+4=56 总权重），而 room 池里 fertile 有**三条**（小/中/大各一条）
#     ⇒ 实际是 64 与 34。按 1-(46/56)^3 算出来是 44.6%（比旧值更低），与"要更高"的意图相反；
#     本轮按**文件实际**记账（总 64 / 非丰饶 34 / P=85.0%），差异见 docs\金之牢狱-实现记录.md §12。
#     参考：想精确落在 82% 需要 fertile ≈ 8.74，即权重 9（1-(34/61)^3 = 82.7%）。
POOL_CELL_W = {'a': 2, 'b': 2, 'c': 2, 'mirror': 2, 'fertile': 10}
ROOM_WEIGHTS = []
for _size in ('cell_small', 'cell_medium', 'cell_large'):
    for _v in ('a', 'b', 'c', 'mirror', 'fertile'):
        ROOM_WEIGHTS.append(('%s_%s' % (_size, _v), POOL_CELL_W[_v]))
ROOM_WEIGHTS += [('cross_a', 5), ('cross_b', 5)]

POOLS = collections.OrderedDict([
    ('start', ([(('treasure'), 1)], 'minecraft:empty')),
    ('lane', ([(('lane'), 1)], POOL + 'exit')),
    ('room', (ROOM_WEIGHTS, POOL + 'exit')),
    ('exit', ([('exit', 1)], 'minecraft:empty')),
])

# ★ 第六轮（本文件所在轮）：**按群系分支**（纯数据，不写 Java）。
#   旧口径（第五轮，原文留档、不删）：
#     `biomes = #minecraft:is_nether` + `terrain_adaptation = none` 的**一套**结构 ——
#     在玄武岩三角洲最好（件内异类方块 110），但在绯红森林比 bury 差（6 → 187，全是疣块/菌柄/藤）。
#   ⇒ 拆两套（宝藏房唯一性靠两套的 start_pool **指向同一个 start 池**）：
#     ① `structure/golden_prison.json`（**保留原名**）：biomes = #bettergold:golden_prison/no_basalt
#        + terrain_adaptation = **bury**（对非玄武岩群系更好：把结构周围的植被压掉）；
#     ② `structure/golden_prison_basalt.json`（新）：biomes = minecraft:basalt_deltas
#        + terrain_adaptation = **none**（玄武岩的 delta / *_basalt_columns 是 feature，晚于结构放置，
#        胡子挡不住；none + underground_decoration 的读数才是 110）。
#   两套其余字段**逐字相同**（step / size / start_height / max_distance_from_center / start_pool）。
#   ⚠ **max_distance_from_center 的 116**：JigsawStructure.verifyRange（源码逐行见关卡注释）
#       `int i = terrainAdaptation()==NONE ? 0 : 12;  maxDistanceFromCenter + i > 128 ⇒ DataResult.error`
#     ⇒ bury 档**最大只能 116**（116+12 = 128）。写 128 会让结构**静默加载失败**（整个结构没有），
#       所以主结构用 116；玄武岩档是 none，照旧 128。
#       （第五轮 100→128 是为了消掉"距中心 99~103 格那一圈被裁掉的口"；116 仍大于那一圈，实测见 §12。）
BIOMES_ALL_NETHER = '#minecraft:is_nether'      # 旧口径（一套结构时用的，留档）
BIOMES_MAIN = '#bettergold:golden_prison/no_basalt'
BIOMES_BASALT = 'minecraft:basalt_deltas'


def _structure(biomes, terrain_adaptation, max_distance_from_center):
    """两套 structure JSON 的唯一构造入口 —— 除这三个字段外**逐字相同**。"""
    return {
        'type': 'minecraft:jigsaw',
        'biomes': biomes,
        # ★ 第五轮：地下结构 → 地下装饰。依据 = 原版 fortress.json 也是 underground_decoration；
        #   玄武岩三角洲的 delta / small_basalt_columns / large_basalt_columns 在 surface_structures 步，
        #   晚于 underground_structures ⇒ 柱子会长进结构里（"贯穿"）。改到更晚的步就能被模板空气清掉。
        'step': 'underground_decoration',
        'spawn_overrides': {},
        # ★ 第五轮：bury → none（全局一套时）。第六轮按群系分支：
        #   非玄武岩 = bury（恢复）、玄武岩 = none。两档的读数见 §11 / §12。
        'terrain_adaptation': terrain_adaptation,
        'start_pool': POOL + 'start',
        'size': 6,
        'start_height': {'type': 'minecraft:uniform',
                         'min_inclusive': {'absolute': 31},
                         'max_inclusive': {'absolute': 41}},
        'use_expansion_hack': False,
        'max_distance_from_center': max_distance_from_center,
    }


STRUCTURE = _structure(BIOMES_MAIN, 'bury', 116)
STRUCTURE_BASALT = _structure(BIOMES_BASALT, 'none', 128)

# 群系标签：原版 #minecraft:is_nether 的成员逐条（真源 = build 里原版 resources jar 的
# data/minecraft/tags/worldgen/biome/is_nether.json，5 条、无嵌套标签），**去掉 basalt_deltas**。
# ⚠ `replace` 必须是 **false**（缺省也是 false，但显式写出来）：写成 true 会把原版标签静默清空。
NETHER_BIOMES = ['minecraft:nether_wastes', 'minecraft:soul_sand_valley', 'minecraft:crimson_forest',
                 'minecraft:warped_forest', 'minecraft:basalt_deltas']
BIOME_TAG = {'replace': False,
             'values': [b for b in NETHER_BIOMES if b != BIOMES_BASALT]}

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

# ★ 第六轮：玄武岩三角洲那一套 —— spacing/separation/spread_type **完全相同**（否则两套密度会叠加），
#   **salt 只差 1**（19710102）：RandomSpreadStructurePlacement#getPotentialStructureChunk 用
#   `setLargeFeatureWithSalt(seed, regionX, regionZ, salt)` 抽候选区块 ⇒ 两套若同 salt，候选区块逐个重合，
#   同一格会既排普通版又排玄武岩版（本设计里两套群系互斥，实际不会双生成，但**不靠巧合**）；
#   salt 只改分布偏移、不改密度。
OUR_SALT_BASALT = 19710102
STRUCTURE_SET_BASALT = {
    'structures': [{'structure': 'bettergold:golden_prison_basalt', 'weight': 1}],
    'placement': {
        'type': 'minecraft:random_spread',
        'spacing': 27,
        'separation': 4,
        'salt': OUR_SALT_BASALT,
        'spread_type': 'linear',
    },
}


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    txt = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)


def stage4():
    pdir = os.path.join(WG, 'template_pool', 'golden_prison')
    for name, (els, fb) in POOLS.items():
        obj = {'fallback': fb, 'elements': [
            {'weight': w, 'element': {'element_type': 'minecraft:single_pool_element',
                                      'location': '%s:%s%s' % (NS, 'golden_prison/', t),
                                      'processors': 'minecraft:empty',
                                      'projection': 'rigid'}} for (t, w) in els]}
        write_json(os.path.join(pdir, name + '.json'), obj)
    # 第五轮：池从 15 个收成 4 个，旧池文件必须删掉（否则引擎里还留着"死池"，关卡也会数错）
    stale = []
    for fn in sorted(os.listdir(pdir)):
        if fn.endswith('.json') and fn[:-5] not in POOLS:
            os.remove(os.path.join(pdir, fn))
            stale.append(fn)
    if stale:
        print('  [pools] 删除旧池 %d 个：%s' % (len(stale), stale))
    write_json(os.path.join(WG, 'structure', 'golden_prison.json'), STRUCTURE)
    write_json(os.path.join(WG, 'structure', 'golden_prison_basalt.json'), STRUCTURE_BASALT)
    write_json(os.path.join(WG, 'structure_set', 'golden_prison.json'), STRUCTURE_SET)
    write_json(os.path.join(WG, 'structure_set', 'golden_prison_basalt.json'), STRUCTURE_SET_BASALT)
    # 第六轮：群系标签（列表 = 原版 #minecraft:is_nether 减 basalt_deltas；replace 显式 false）
    write_json(os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'tags',
                            'worldgen', 'biome', 'golden_prison', 'no_basalt.json'), BIOME_TAG)
    print('== stage4: worldgen JSON ==')
    print('  structure_set: spacing=27 separation=4 spread_type=linear'
          '（= 下界要塞的 spacing/separation；旧 32/16 已按作者第三轮要求改掉）')
    for label, st, pl in (('golden_prison（主，非玄武岩）', STRUCTURE, STRUCTURE_SET['placement']),
                          ('golden_prison_basalt（玄武岩）', STRUCTURE_BASALT,
                           STRUCTURE_SET_BASALT['placement'])):
        print('  %-32s biomes=%-38s terrain_adaptation=%-4s max_distance=%-3d salt=%d'
              % (label, st['biomes'], st['terrain_adaptation'], st['max_distance_from_center'],
                 pl['salt']))
    print('  biome tag no_basalt: replace=%r values=%s'
          % (BIOME_TAG['replace'], BIOME_TAG['values']))
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
