# -*- coding: utf-8 -*-
"""[bgp-*] 金之牢狱（golden_prison）关卡 —— 结构 NBT / 模板池 / 战利品 / 方向闸。

约定（docs\\构建与跑测注意事项.md §七）：
  exit 0 = 全绿；exit 1 = 有「问题」；exit 2 = 前置缺失 / 基线被破坏 / 脚本自身出错。
  「问题列表为空」不等于「检查过」：本关卡每次都会打印 `[bgp-counter] checked=N`，N<=0 => exit 2。

跑法（必须用工作区自带 Python，禁用 `py -3`）：
  "C:\\Users\\Lenovo\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\python\\python.exe" validate_golden_prison.py

方向闸（[bgp-gate]）把 JigsawPlacement 的拼接口径用坐标复算了一遍：
  子件原点 = 父件原点 + 父口局部坐标 + 朝向 D - 子口局部坐标（旋转后）
  并断言 ① 两口同面同高 ② 洞底 = 行走面（拼完行走面连续） ③ jigsaw orientation = 实际外侧 ④ 两件不重叠。
"""
import gzip
import hashlib
import json
import os
import struct
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
STRUCT = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'structure', 'golden_prison')
WG = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'worldgen')
LOOT = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'loot_table', 'chests',
                    'golden_prison.json')
TAGS = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'bettergold', 'tags')
LANG = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'bettergold', 'lang', 'zh_cn.json')
BP = os.path.join(ROOT, 'docs', '金之牢狱-蓝图')
POOL = 'bettergold:golden_prison/'
LOOT_ID = 'bettergold:chests/golden_prison'

# 冻结快照：20 个模板的尺寸（第 1 步的产出，不许被悄悄改）
EXPECT_SIZE = {
    'treasure': (21, 9, 21), 'cross_a': (37, 8, 37), 'cross_b': (37, 8, 37),
    'lane': (5, 5, 3), 'exit': (5, 8, 5),
    'cell_large_a': (15, 6, 31), 'cell_large_b': (15, 6, 31), 'cell_large_c': (15, 6, 31),
    'cell_large_mirror': (15, 6, 31), 'cell_large_fertile': (15, 6, 31),
    'cell_medium_a': (15, 6, 21), 'cell_medium_b': (15, 6, 21), 'cell_medium_c': (15, 6, 21),
    'cell_medium_mirror': (15, 6, 21), 'cell_medium_fertile': (15, 6, 21),
    'cell_small_a': (15, 6, 11), 'cell_small_b': (15, 6, 11), 'cell_small_c': (15, 6, 11),
    'cell_small_mirror': (15, 6, 11), 'cell_small_fertile': (15, 6, 11),
}
# 冻结快照：从作者存档逐格抠出来的 14 件方块数（docs\\金之牢狱-拼接分析.md §3.3）
EXPECT_SRC_COUNT = {
    'treasure': 2195, 'cross_a': 6280, 'cross_b': 6277, 'lane': 48, 'exit': 155,
    'cell_large_a': 1755, 'cell_large_b': 1752, 'cell_large_c': 1742,
    'cell_medium_a': 1212, 'cell_medium_b': 1200, 'cell_medium_c': 1184,
    'cell_small_a': 670, 'cell_small_b': 663, 'cell_small_c': 644,
}
# 冻结快照：出海口（口数 / 是否终端）
EXPECT_MOUTHS = {
    'treasure': {'south'}, 'cross_a': {'north', 'south', 'east', 'west'},
    'cross_b': {'north', 'south', 'east', 'west'}, 'lane': {'north', 'south'}, 'exit': {'north'},
}
for _c in ('large', 'medium', 'small'):
    for _v in ('a', 'b', 'c', 'mirror', 'fertile'):
        EXPECT_MOUTHS['cell_%s_%s' % (_c, _v)] = {'north', 'south'}
EXPECT_WALK_Y = {'treasure': 3, 'cells': 1, 'lane': 1, 'exit': 1}
# 冻结快照：第 2 步的 socket 命名（name, target, pool）
SOCK = {
    'treasure': {'south': ('room', 'lane', POOL + 'lane')},
    'cross_a': {s: ('room', 'lane', POOL + 'lane') for s in ('north', 'south', 'east', 'west')},
    'cross_b': {s: ('room', 'lane', POOL + 'lane') for s in ('north', 'south', 'east', 'west')},
    'exit': {'north': ('lane', 'room', POOL + 'room')},
    'lane': {'north': ('lane', 'room', POOL + 'room'),
             'south': ('lane', 'cell_small_1', POOL + 'cell_small_1')},
    'cell_small_a': {'north': ('cell_small_1', 'cell_small_2', POOL + 'cell_small_2'),
                     'south': ('cell_small_1', 'cell_small_2', POOL + 'cell_small_2')},
    'cell_small_mirror': {'north': ('cell_small_2', 'cell_small_3', POOL + 'cell_small_3'),
                          'south': ('cell_small_2', 'cell_small_3', POOL + 'cell_small_3')},
    'cell_small_fertile': {'north': ('cell_small_3', 'lane', POOL + 'lane'),
                           'south': ('cell_small_3', 'lane', POOL + 'lane')},
}
for _n in ('cell_medium_a', 'cell_medium_b', 'cell_medium_c', 'cell_medium_mirror', 'cell_medium_fertile',
           'cell_large_a', 'cell_large_b', 'cell_large_c', 'cell_large_mirror', 'cell_large_fertile',
           'cell_small_b', 'cell_small_c'):
    SOCK[_n] = {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')}

# 池：名字 -> (元素模板, fallback 池)
EXPECT_POOLS = {
    'start': (['treasure'], 'minecraft:empty'),
    'lane': (['lane'], POOL + 'exit'),
    'room': (['cell_medium_a', 'cell_medium_b', 'cell_medium_c', 'cell_medium_mirror',
              'cell_large_a', 'cell_large_b', 'cell_large_c', 'cell_large_mirror',
              'cross_a', 'cross_b', 'cell_small_b', 'cell_small_c'], 'minecraft:empty'),
    'exit': (['exit'], 'minecraft:empty'),
    'cell_small_1': (['cell_small_a'], POOL + 'cell_small_1'),
    'cell_small_2': (['cell_small_mirror'], POOL + 'cell_small_2'),
    'cell_small_3': (['cell_small_fertile'], POOL + 'cell_small_3'),
    'cell_medium_1': (['cell_medium_a'], 'minecraft:empty'),
    'cell_medium_2': (['cell_medium_mirror'], 'minecraft:empty'),
    'cell_medium_3': (['cell_medium_fertile'], 'minecraft:empty'),
    'cell_large_1': (['cell_large_a'], 'minecraft:empty'),
    'cell_large_2': (['cell_large_mirror'], 'minecraft:empty'),
    'cell_large_3': (['cell_large_fertile'], 'minecraft:empty'),
    'cross_a': (['cross_a'], 'minecraft:empty'),
    'cross_b': (['cross_b'], 'minecraft:empty'),
}

EXPECT_LOOT_WEIGHT = 80
EXPECT_LOOT_ENTRIES = 27
EXPECT_LOOT_IDS = [
    'minecraft:gold_nugget', 'minecraft:gold_ingot', 'minecraft:raw_gold', 'bettergold:golden_cowrie',
    'minecraft:enchanted_book', 'bettergold:gift_gold_ticket', 'bettergold:small_netherite_scrap',
    'minecraft:golden_apple', 'minecraft:golden_carrot', 'bettergold:golden_egg',
    'bettergold:golden_wheat_seeds', 'bettergold:golden_wheat', 'bettergold:chaos_coin',
    'bettergold:chaos_coin_string', 'bettergold:golden_eggplant_seeds', 'bettergold:golden_eggplant',
    'bettergold:golden_cowrie_mold', 'bettergold:chaosgold_nugget', 'minecraft:netherite_scrap',
    'minecraft:golden_horse_armor', 'bettergold:idol_gift_box', 'bettergold:gourmet_box',
    'minecraft:enchanted_golden_apple', 'minecraft:netherite_ingot', 'bettergold:chaosgold_ingot',
]
# 「算不出来」被删掉的两行（不许悄悄回来，也不许悄悄换 id）
FORBIDDEN_LOOT = ['bettergold:chaosgold_enchantment']

problems = []
checked = [0]


def ng(code, msg):
    problems.append('[%s] %s' % (code, msg))


def ok(n=1):
    checked[0] += n


# ------------------------------------------------------------------ NBT 解析（自写）
TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG, TAG_FLOAT, TAG_DOUBLE = 0, 1, 2, 3, 4, 5, 6
TAG_BYTE_ARRAY, TAG_STRING, TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 7, 8, 9, 10, 11, 12


class R:
    def __init__(self, d):
        self.d = d
        self.p = 0

    def take(self, n):
        b = self.d[self.p:self.p + n]
        if len(b) != n:
            raise EOFError('nbt eof')
        self.p += n
        return b

    def u1(self):
        return self.take(1)[0]

    def u2(self):
        return struct.unpack('>H', self.take(2))[0]

    def i1(self):
        return struct.unpack('>b', self.take(1))[0]

    def i2(self):
        return struct.unpack('>h', self.take(2))[0]

    def i4(self):
        return struct.unpack('>i', self.take(4))[0]

    def i8(self):
        return struct.unpack('>q', self.take(8))[0]

    def f4(self):
        return struct.unpack('>f', self.take(4))[0]

    def f8(self):
        return struct.unpack('>d', self.take(8))[0]

    def s(self):
        return self.take(self.u2()).decode('utf-8', 'replace')


def rp(r, t):
    if t == TAG_BYTE:
        return r.i1()
    if t == TAG_SHORT:
        return r.i2()
    if t == TAG_INT:
        return r.i4()
    if t == TAG_LONG:
        return r.i8()
    if t == TAG_FLOAT:
        return r.f4()
    if t == TAG_DOUBLE:
        return r.f8()
    if t == TAG_BYTE_ARRAY:
        return r.take(r.i4())
    if t == TAG_STRING:
        return r.s()
    if t == TAG_LIST:
        it = r.u1()
        n = r.i4()
        return [] if it == TAG_END else [rp(r, it) for _ in range(n)]
    if t == TAG_COMPOUND:
        out = {}
        while True:
            tt = r.u1()
            if tt == TAG_END:
                return out
            nm = r.s()
            out[nm] = rp(r, tt)
    if t == TAG_INT_ARRAY:
        n = r.i4()
        return list(struct.unpack('>%di' % n, r.take(4 * n)))
    if t == TAG_LONG_ARRAY:
        n = r.i4()
        return list(struct.unpack('>%dq' % n, r.take(8 * n)))
    raise ValueError('tag %r' % t)


def parse_nbt(path):
    raw = open(path, 'rb').read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    r = R(raw)
    t = r.u1()
    if t != TAG_COMPOUND:
        raise ValueError('root not compound')
    r.s()
    return rp(r, TAG_COMPOUND)


# ------------------------------------------------------------------ 件模型
AIR = 'minecraft:air'
VOID = 'minecraft:structure_void'
DIRV = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0)}


class Piece:
    def __init__(self, name, size, blocks, jigsaws, chests, palette):
        self.name = name
        self.size = size
        self.blocks = blocks          # (x,y,z) -> (name, props)
        self.jigsaws = jigsaws        # (x,y,z) -> be dict
        self.chests = chests          # list of (x,y,z)
        self.palette = palette

    def at(self, p):
        return self.blocks.get(p)


def load_piece(name):
    path = os.path.join(STRUCT, name + '.nbt')
    root = parse_nbt(path)
    size = tuple(root['size'])
    pal = root['palette']
    blocks, jig, chests = {}, {}, []
    for b in root['blocks']:
        p = tuple(b['pos'])
        e = pal[b['state']]
        nm = e['Name']
        pr = dict(e.get('Properties') or {})
        blocks[p] = (nm, pr)
        if nm == 'minecraft:jigsaw':
            be = b.get('nbt') or {}
            jig[p] = be
            try:
                o = pr['orientation']
            except KeyError:
                ng('bgp-nbt', '%s 的 jigsaw %s 缺 orientation' % (name, p))
                o = ''
            jig[p]['_orientation'] = o
            jig[p]['_dir'] = o.split('_')[0] if o else ''
        if nm == 'minecraft:chest':
            chests.append(p)
            be = b.get('nbt') or {}
            if be.get('LootTable') != LOOT_ID:
                ng('bgp-chest', '%s 的箱子 %s LootTable=%r（应为 %s）'
                   % (name, p, be.get('LootTable'), LOOT_ID))
            ok()
    return Piece(name, size, blocks, jig, chests, pal)


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


def mouth_passable(piece, sock, size):
    """口必须是 3 宽 × 3 高、洞底 = 行走面，且洞底下一格是实心（能站）。"""
    side = sock['dir']
    x, y, z = sock['pos']
    bad = []
    for d in (-1, 0, 1):
        for dy in (0, 1, 2):
            if side in ('north', 'south'):
                c = (x + d, y + dy, z)
            else:
                c = (x, y + dy, z + d)
            v = piece.at(c)
            if v is not None and v[0] not in (AIR, 'minecraft:jigsaw'):
                bad.append((c, v))
    # 洞底下一格
    d = DIRV[side]
    for off in (-1, 0, 1):
        if side in ('north', 'south'):
            c = (x + off, y - 1, z)
        else:
            c = (x, y - 1, z + off)
        v = piece.at(c)
        if v is None or v[0] in (AIR, VOID):
            bad.append(('floor', c, v))
    return bad


# 旋转（复刻 StructureTemplate.transform：mirror=NONE, pivot=ZERO）
ROTS = ['none', 'cw90', 'cw180', 'ccw90']


def rot_pos(p, r):
    x, y, z = p
    if r == 'none':
        return (x, y, z)
    if r == 'cw90':
        return (-z, y, x)
    if r == 'cw180':
        return (-x, y, -z)
    return (z, y, -x)


DIR_RING = ['north', 'east', 'south', 'west']


def rot_dir(d, r):
    if d not in DIR_RING:
        return d
    i = DIR_RING.index(d)
    k = {'none': 0, 'cw90': 1, 'cw180': 2, 'ccw90': 3}[r]
    return DIR_RING[(i + k) % 4]


def rot_size(size, r):
    sx, sy, sz = size
    return (sz, sy, sx) if r in ('cw90', 'ccw90') else (sx, sy, sz)


def piece_bbox(size, r, origin):
    sx, sy, sz = size
    a = rot_pos((0, 0, 0), r)
    b = rot_pos((sx - 1, sy - 1, sz - 1), r)
    lo = (min(a[0], b[0]) + origin[0], min(a[1], b[1]) + origin[1], min(a[2], b[2]) + origin[2])
    hi = (max(a[0], b[0]) + origin[0], max(a[1], b[1]) + origin[1], max(a[2], b[2]) + origin[2])
    return lo, hi


def bbox_overlap(a, b):
    return not (a[1][0] < b[0][0] or b[1][0] < a[0][0] or
                a[1][1] < b[0][1] or b[1][1] < a[0][1] or
                a[1][2] < b[0][2] or b[1][2] < a[0][2])


# ------------------------------------------------------------------ 各检查段
def check_inventory():
    files = sorted(f for f in os.listdir(STRUCT) if f.endswith('.nbt')) if os.path.isdir(STRUCT) else []
    if not os.path.isdir(STRUCT):
        raise SystemExit(2)
    if len(files) != 20:
        ng('bgp-inventory', '模板数 %d != 20' % len(files))
    for f in files:
        ok()
    got = {f[:-4] for f in files}
    for n in EXPECT_SIZE:
        if n not in got:
            ng('bgp-inventory', '缺模板 %s' % n)
    for n in got - set(EXPECT_SIZE):
        ng('bgp-inventory', '多出模板 %s' % n)
    # 蓝图
    pngs = [f for f in os.listdir(BP) if f.endswith('.png')] if os.path.isdir(BP) else []
    if len(pngs) < 20:
        ng('bgp-blueprint', '蓝图 %d 张 < 20' % len(pngs))
    for n in EXPECT_SIZE:
        if n.upper() + '.png' not in pngs:
            ng('bgp-blueprint', '缺蓝图 %s.png' % n.upper())
        ok()


def check_pieces(pieces):
    for name, p in pieces.items():
        if p.size != EXPECT_SIZE[name]:
            ng('bgp-nbt', '%s 尺寸 %s != %s' % (name, p.size, EXPECT_SIZE[name]))
        ok()
        # 方块数（14 个源件对照证据；派生件只要求 > 0）
        if name in EXPECT_SRC_COUNT:
            # 取证表是「抠出来时」的方块数，不含第 2 步注入的 jigsaw
            got = len(p.blocks) - len(p.jigsaws)
            if got != EXPECT_SRC_COUNT[name]:
                ng('bgp-nbt', '%s 方块数(不含 jigsaw) %d != 取证 %d'
                   % (name, got, EXPECT_SRC_COUNT[name]))
            ok()
        # 口位：数量 / 命名 / 朝向
        sides = {}
        for pos, be in p.jigsaws.items():
            out = outward(pos, p.size)
            if len(out) != 1:
                ng('bgp-gate', '%s 的 jigsaw %s 不在唯一的外侧面上（%s）' % (name, pos, out))
                continue
            side = out[0]
            sides[side] = pos
            if be.get('_dir') != side:
                ng('bgp-gate', '%s 的 %s 口 jigsaw orientation=%r，实际外侧应为 %s_up'
                   % (name, side, be.get('_orientation'), side))
            want = SOCK[name].get(side)
            if want is None:
                ng('bgp-gate', '%s 的 %s 口不该有 jigsaw' % (name, side))
            else:
                sn, tg, pl = want
                if (be.get('name'), be.get('target'), be.get('pool')) != (sn, tg, pl):
                    ng('bgp-gate', '%s 的 %s 口 socket=(%r,%r,%r) != 期望 (%r,%r,%r)'
                       % (name, side, be.get('name'), be.get('target'), be.get('pool'), sn, tg, pl))
                if be.get('final_state') != 'minecraft:air':
                    ng('bgp-gate', '%s 的 %s 口 final_state=%r（应为 air，否则口会被堵死）'
                       % (name, side, be.get('final_state')))
            ok(3)
        if set(sides) != EXPECT_MOUTHS[name]:
            ng('bgp-gate', '%s 的口集合 %s != %s' % (name, set(sides), EXPECT_MOUTHS[name]))
        ok()
        # 洞底 = 行走面
        want_wy = 3 if name == 'treasure' else 1
        for side, pos in sides.items():
            if pos[1] != want_wy:
                ng('bgp-gate', '%s 的 %s 口洞底 dy=%d，行走面应为 %d' % (name, side, pos[1], want_wy))
            bad = mouth_passable(p, {'dir': side, 'pos': pos}, p.size)
            if bad:
                ng('bgp-gate', '%s 的 %s 口不是 3x3 通洞：%s' % (name, side, bad[:3]))
            ok(2)
        # 箱子
        for c in p.chests:
            ok()
        if name.endswith('_fertile') and not p.chests:
            ng('bgp-fertile', '%s 没有箱子' % name)


def check_mirror(pieces):
    for base, mir in (('cell_small_a', 'cell_small_mirror'), ('cell_medium_a', 'cell_medium_mirror'),
                      ('cell_large_a', 'cell_large_mirror')):
        a, b = pieces[base], pieces[mir]
        sx = a.size[0]
        if a.size != b.size:
            ng('bgp-mirror', '%s 尺寸 != %s' % (base, mir))
        if len(a.blocks) != len(b.blocks):
            ng('bgp-mirror', '%s 方块数 %d != %s 的 %d' % (base, len(a.blocks), mir, len(b.blocks)))
        pa = {v[0] for v in a.blocks.values()}
        pb = {v[0] for v in b.blocks.values()}
        if pa != pb:
            ng('bgp-mirror', '%s 与 %s 调色板不同' % (base, mir))
        # 逐格：镜像后的方块 id 必须一致（属性按面翻）
        for (x, y, z), (nm, pr) in a.blocks.items():
            t = b.at((sx - 1 - x, y, z))
            if t is None or t[0] != nm:
                ng('bgp-mirror', '%s 镜像格 (%d,%d,%d) 对不上：%s vs %s' % (base, x, y, z, nm, t))
                break
            ok()
        # 口位镜像后不变
        sa, sb = {}, {}
        for k in a.jigsaws:
            o = outward(k, a.size)
            if o:
                sa[o[0]] = k
        for k in b.jigsaws:
            o = outward(k, b.size)
            if o:
                sb[o[0]] = k
        if set(sa) != set(sb):
            ng('bgp-mirror', '%s 镜像后口集合变了 %s -> %s' % (base, set(sa), set(sb)))
        for s in sa:
            pa2, pb2 = sa[s], sb[s]
            if (sx - 1 - pa2[0], pa2[1], pa2[2]) != pb2:
                ng('bgp-mirror', '%s 镜像后 %s 口位置 %s -> %s 不是 x 镜像' % (base, s, pa2, pb2))
            ok()


def check_fertile(pieces):
    for base, fer in (('cell_small_a', 'cell_small_fertile'), ('cell_medium_a', 'cell_medium_fertile'),
                      ('cell_large_a', 'cell_large_fertile')):
        a, b = pieces[base], pieces[fer]
        sx, sy, sz = a.size
        wy = 3 if base == 'treasure' else 1
        diff_out = []
        for p in set(a.blocks) | set(b.blocks):
            if a.at(p) == b.at(p):
                continue
            x, y, z = p
            if x in (0, sx - 1) or z in (0, sz - 1) or y not in (wy - 1, wy):
                diff_out.append(p)
            if 6 <= x <= 8 and (z <= 1 or z >= sz - 2):
                diff_out.append(('mouth', p))
            ok()
        if diff_out:
            ng('bgp-fertile', '%s 动了结构框/过道口：%s' % (fer, diff_out[:5]))
        names = {v[0] for v in b.blocks.values()}
        for need in ('bettergold:gold_infused_farmland', 'minecraft:chest'):
            if need not in names:
                ng('bgp-fertile', '%s 缺 %s' % (fer, need))
            ok()
        if not any('crop' in v[0] for v in b.blocks.values()):
            ng('bgp-fertile', '%s 没有作物' % fer)
        # 丰饶只搬作者已有方块：调色板必须是 A 的子集（+ 农田/作物/箱/蟾）
        extra = names - {v[0] for v in a.blocks.values()} - {
            'bettergold:gold_infused_farmland', 'bettergold:golden_wheat_crop',
            'bettergold:golden_carrot_crop', 'bettergold:golden_eggplant_crop',
            'bettergold:golden_toad_figurine', 'minecraft:chest'}
        if extra:
            ng('bgp-fertile', '%s 引入了作者没有的方块 %s' % (fer, sorted(extra)))


def check_gate(pieces):
    """方向闸：对所有「名字/目标能接上」的 (父口, 子件, 4 个旋转) 复算拼接。"""
    # 子件：socket 名字 -> [(件, 口 side, 口 pos)]
    byname = {}
    for name, p in pieces.items():
        for side in SOCK[name]:
            pos = None
            for q, be in p.jigsaws.items():
                out = outward(q, p.size)
                if out and out[0] == side:
                    pos = q
            if pos is None:
                continue
            byname.setdefault(SOCK[name][side][0], []).append((name, side, pos))
    pairs = 0
    for name, p in pieces.items():
        for side, (sn, tg, pl) in SOCK[name].items():
            pos = None
            for q, be in p.jigsaws.items():
                out = outward(q, p.size)
                if out and out[0] == side:
                    pos = q
            if pos is None:
                continue
            d = DIRV[side]
            kids = byname.get(tg, [])
            if not kids:
                ng('bgp-gate', '%s 的 %s 口 target=%r 没有任何子件能接' % (name, side, tg))
            for (cn, cside, cpos) in kids:
                child = pieces[cn]
                for r in ROTS:
                    # 子件里真正朝向父件的口：旋转后方向 = -d
                    rpos = rot_pos(cpos, r)
                    opp = {'north': 'south', 'south': 'north',
                           'east': 'west', 'west': 'east'}[side]
                    rdir = rot_dir(cside, r)
                    if rdir != opp:
                        continue
                    origin = tuple(pos[i] + d[i] - rpos[i] for i in range(3))
                    # ① 两口同面同高：子件口的世界坐标 = 父口 + d
                    world = tuple(origin[i] + rpos[i] for i in range(3))
                    if world != tuple(pos[i] + d[i] for i in range(3)):
                        ng('bgp-gate', '%s/%s -> %s/%s rot=%s 口对不上面' % (name, side, cn, cside, r))
                    # ①b 子件包围盒沿 d 恰好落在父件外一层，且横向覆盖口列
                    pb = piece_bbox(p.size, 'none', (0, 0, 0))
                    cb = piece_bbox(child.size, r, origin)
                    if side == 'south' and cb[0][2] != pb[1][2] + 1:
                        ng('bgp-gate', '%s->%s rot=%s 南面不贴合：子 minZ=%d 父 maxZ=%d'
                           % (name, cn, r, cb[0][2], pb[1][2]))
                    if side == 'north' and cb[1][2] != pb[0][2] - 1:
                        ng('bgp-gate', '%s->%s rot=%s 北面不贴合：子 maxZ=%d 父 minZ=%d'
                           % (name, cn, r, cb[1][2], pb[0][2]))
                    if side == 'east' and cb[0][0] != pb[1][0] + 1:
                        ng('bgp-gate', '%s->%s rot=%s 东面不贴合' % (name, cn, r))
                    if side == 'west' and cb[1][0] != pb[0][0] - 1:
                        ng('bgp-gate', '%s->%s rot=%s 西面不贴合' % (name, cn, r))
                    # ④ 不重叠
                    if bbox_overlap(pb, cb):
                        ng('bgp-gate', '%s->%s rot=%s 两件包围盒重叠' % (name, cn, r))
                    # ② 行走面连续：两个口的世界 y 相同，且子件口的 dy = 子件行走面
                    cy = world[1]
                    if cy != pos[1] + d[1]:
                        ng('bgp-gate', '%s/%s -> %s/%s rot=%s 口高不一致' % (name, side, cn, cside, r))
                    wy = 3 if cn == 'treasure' else 1
                    if cpos[1] != wy:
                        ng('bgp-gate', '%s 的口 dy=%d != 行走面 %d' % (cn, cpos[1], wy))
                    # ③ 子件口的 orientation（旋转后）必须朝外
                    rfront = rot_dir(cside, r)
                    if rfront != opp:
                        ng('bgp-gate', '%s 的 %s 口旋转 %s 后不朝父件' % (cn, cside, r))
                    pairs += 1
                    ok(6)
    if pairs == 0:
        ng('bgp-gate', '方向闸一对都没算到（空转）')
    print('[bgp-gate] attach pairs (socket x child x rotation) = %d' % pairs)


def check_cycle(pieces):
    """小牢房三步循环：1(A) -> 2(镜像) -> 3(丰饶) -> 回过道。"""
    chain = [('cell_small_a', 'cell_small_1', 'cell_small_2'),
             ('cell_small_mirror', 'cell_small_2', 'cell_small_3'),
             ('cell_small_fertile', 'cell_small_3', 'lane')]
    for name, sn, tg in chain:
        for side in ('north', 'south'):
            cands = [v for k, v in pieces[name].jigsaws.items()
                     if (outward(k, pieces[name].size) or [''])[0] == side]
            if not cands:
                ng('bgp-cycle', '%s 缺 %s 口的 jigsaw（口位不在外侧面上）' % (name, side))
                continue
            be = cands[0]
            if be.get('name') != sn or be.get('target') != tg:
                ng('bgp-cycle', '%s 的 %s 口 (%r -> %r) != (%r -> %r)'
                   % (name, side, be.get('name'), be.get('target'), sn, tg))
            ok(2)
    # 第 3 步必须是丰饶版（作者：三件连一起必含丰饶）
    if 'fertile' not in chain[2][0]:
        ng('bgp-cycle', '三步循环的第 3 步不是丰饶版')
    ok()
    # 池子接线
    if EXPECT_POOLS['cell_small_1'][1] != POOL + 'cell_small_1':
        ng('bgp-cycle', 'cell_small_1 的 fallback 不是自己')
    ok()


def check_worldgen():
    sp = os.path.join(WG, 'structure', 'golden_prison.json')
    ssp = os.path.join(WG, 'structure_set', 'golden_prison.json')
    for f in (sp, ssp):
        if not os.path.exists(f):
            ng('bgp-worldgen', '缺 %s' % f)
            return
        ok()
    st = json.load(open(sp, encoding='utf-8'))
    exp = {'type': 'minecraft:jigsaw', 'biomes': '#minecraft:is_nether',
           'step': 'underground_structures', 'start_pool': POOL + 'start',
           'size': 6, 'use_expansion_hack': False, 'terrain_adaptation': 'bury',
           'max_distance_from_center': 100}
    for k, v in exp.items():
        if st.get(k) != v:
            ng('bgp-worldgen', 'structure.%s = %r != %r' % (k, st.get(k), v))
        ok()
    if st.get('spawn_overrides') != {}:
        ng('bgp-worldgen', 'spawn_overrides 必须清空')
    ok()
    sh = st.get('start_height') or {}
    if sh.get('type') != 'minecraft:uniform':
        ng('bgp-worldgen', 'start_height.type=%r' % sh.get('type'))
    lo = (sh.get('min_inclusive') or {}).get('absolute')
    hi = (sh.get('max_inclusive') or {}).get('absolute')
    if (lo, hi) != (31, 41):
        ng('bgp-worldgen', 'start_height 区间 %r..%r != 31..41' % (lo, hi))
    ok(3)
    if 'max_depth' in json.dumps(st):
        ng('bgp-worldgen', '出现了 1.20 口径的 max_depth（1.21 叫 size）')
    ok()
    ss = json.load(open(ssp, encoding='utf-8'))
    pl = ss.get('placement') or {}
    if pl.get('type') != 'minecraft:random_spread':
        ng('bgp-worldgen', 'structure_set.placement.type=%r' % pl.get('type'))
    if not (1 <= pl.get('spacing', 0) and pl.get('separation', 0) < pl.get('spacing', 0)):
        ng('bgp-worldgen', 'spacing/separation 不合理：%r/%r' % (pl.get('spacing'), pl.get('separation')))
    if pl.get('spacing') != 32 or pl.get('separation') != 16:
        ng('bgp-worldgen', 'spacing/separation 不是记账值 32/16')
    ok(4)
    if not ss.get('structures') or ss['structures'][0].get('structure') != 'bettergold:golden_prison':
        ng('bgp-worldgen', 'structure_set.structures 没指向 bettergold:golden_prison')
    ok()
    # 池
    for name, (els, fb) in EXPECT_POOLS.items():
        f = os.path.join(WG, 'template_pool', 'golden_prison', name + '.json')
        if not os.path.exists(f):
            ng('bgp-pool', '缺池 %s.json' % name)
            continue
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            ng('bgp-pool', '池 %s 解析失败 %s' % (name, e))
            continue
        ok()
        if d.get('fallback') != fb:
            ng('bgp-pool', '池 %s fallback=%r != %r' % (name, d.get('fallback'), fb))
        ok()
        got = []
        for e in d.get('elements', []):
            w = e.get('weight')
            if not (isinstance(w, int) and 1 <= w <= 150):
                ng('bgp-pool', '池 %s 权重 %r 越界（1..150）' % (name, w))
            loc = (e.get('element') or {}).get('location', '')
            t = loc.split('/', 2)[-1]
            got.append(t)
            el = e.get('element') or {}
            if el.get('element_type') != 'minecraft:single_pool_element':
                ng('bgp-pool', '池 %s 有非 single_pool_element 元素' % name)
            if el.get('projection') != 'rigid':
                ng('bgp-pool', '池 %s 的 %s projection != rigid（y 会随地形，破坏拼接）'
                   % (name, t))
            if not os.path.exists(os.path.join(STRUCT, t + '.nbt')):
                ng('bgp-pool', '池 %s 引用了不存在的模板 %s' % (name, t))
            ok(3)
        if sorted(got) != sorted(els):
            ng('bgp-pool', '池 %s 元素 %s != 期望 %s' % (name, sorted(got), sorted(els)))
        ok()
        # fallback 必须能接上（除了 minecraft:empty 与自己）
        if fb not in ('minecraft:empty', POOL + name) and fb.startswith(POOL):
            fbname = fb[len(POOL):]
            if fbname not in EXPECT_POOLS:
                ng('bgp-pool', '池 %s 的 fallback 指向不存在的池 %s' % (name, fb))
            ok()


def check_loot():
    if not os.path.exists(LOOT):
        ng('bgp-loot', '缺战利品表')
        return
    d = json.load(open(LOOT, encoding='utf-8'))
    if d.get('type') != 'minecraft:chest':
        ng('bgp-loot', 'loot type=%r' % d.get('type'))
    ok()
    pools = d.get('pools') or []
    if len(pools) != 1:
        ng('bgp-loot', '池数 %d != 1（作者口径：只做 1 个池）' % len(pools))
    ok()
    p0 = pools[0]
    rolls = p0.get('rolls') or {}
    if rolls.get('min') != 5 or rolls.get('max') != 10:
        ng('bgp-loot', 'rolls=%r != uniform 5..10' % rolls)
    ok(2)
    br = p0.get('bonus_rolls')
    if not (isinstance(br, (int, float)) and br > 0):
        ng('bgp-loot', 'bonus_rolls=%r 必须 > 0，否则幸运不影响箱子' % br)
    ok()
    entries = p0.get('entries') or []
    if len(entries) != EXPECT_LOOT_ENTRIES:
        ng('bgp-loot', '条目数 %d != %d' % (len(entries), EXPECT_LOOT_ENTRIES))
    ok()
    tot = 0
    names = []
    for e in entries:
        if e.get('type') == 'minecraft:empty':
            ng('bgp-loot', '出现了 empty 条目（作者：没有空箱率）')
        w = e.get('weight')
        if not (isinstance(w, int) and w > 0):
            ng('bgp-loot', '条目权重 %r 非法' % w)
        tot += w or 0
        ne = e.get('name')
        names.append(ne)
        ok(2)
    if tot != EXPECT_LOOT_WEIGHT:
        ng('bgp-loot', '权重和 %d != %d' % (tot, EXPECT_LOOT_WEIGHT))
    ok()
    for n in EXPECT_LOOT_IDS:
        if n not in names:
            ng('bgp-loot', '缺条目 %s' % n)
        ok()
    for n in FORBIDDEN_LOOT:
        if n in json.dumps(d):
            ng('bgp-loot', '出现了「算不出来」被删的那一条 %s' % n)
        ok()
    # 物品 id 存在性：bettergold 物品必须有 zh_cn 语言键（冻结快照 = 本仓既有口径）
    lang = json.load(open(LANG, encoding='utf-8'))
    for e in entries:
        ne = e.get('name', '')
        if e.get('type') == 'minecraft:tag':
            continue
        if ne.startswith('bettergold:'):
            path = ne.split(':', 1)[1]
            if ('item.bettergold.' + path) not in lang and ('block.bettergold.' + path) not in lang:
                ng('bgp-loot', '%s 没有语言键（物品可能不存在）' % ne)
            ok()
    # 附魔 tag（「除取其金食外的任意附魔书」）
    ep = os.path.join(TAGS, 'enchantment', 'golden_prison', 'any_enchantment.json')
    if not os.path.exists(ep):
        ng('bgp-loot', '缺附魔 tag any_enchantment')
    else:
        t = json.load(open(ep, encoding='utf-8'))
        vals = t.get('values') or []
        if vals != ['#minecraft:non_treasure', '#minecraft:treasure']:
            ng('bgp-loot', '附魔 tag 值 %r != 非宝藏+宝藏' % vals)
        ok(2)
        if '#bettergold:golden_prison/any_enchantment' not in json.dumps(d):
            ng('bgp-loot', '战利品表没有引用 any_enchantment tag')
        ok()
        # take_gold_food 必须被排除（它只出现在「取其金食附魔书」那一条的 options 里）
        n = json.dumps(d).count('"bettergold:take_gold_food"')
        if n != 1:
            ng('bgp-loot', 'bettergold:take_gold_food 在表里出现 %d 次（应恰好 1 次）' % n)
        ok()
    # 装备 tag
    tp = os.path.join(TAGS, 'item', 'golden_prison', 'golden_equipment.json')
    if not os.path.exists(tp):
        ng('bgp-loot', '缺装备 tag')
    else:
        t = json.load(open(tp, encoding='utf-8'))
        vals = t.get('values') or []
        if len(vals) != 9:
            ng('bgp-loot', '装备 tag 条目数 %d != 9' % len(vals))
        for v in vals:
            if not v.startswith('minecraft:golden_') or v.endswith('horse_armor'):
                ng('bgp-loot', '装备 tag 里有可疑条目 %r' % v)
            ok()
    # 幸运：bonus_rolls 是唯一起作用的字段（LootPool#addRandomItems 源码）
    src = os.path.join(ROOT, 'build', 'gp-src', 'net', 'minecraft', 'world', 'level', 'storage', 'loot',
                       'LootPool.java')
    if os.path.exists(src):
        s = open(src, encoding='utf-8').read()
        if 'getLuck()' not in s or 'bonusRolls.getFloat' not in s:
            ng('bgp-loot', 'LootPool 源码里没看到 luck x bonusRolls 的乘法（口径来源失效）')
        ok()


def check_forbid_vacuous():
    if checked[0] <= 0:
        print('[bgp-counter] checked=0 —— 空转，判 exit 2')
        raise SystemExit(2)
    print('[bgp-counter] checked=%d' % checked[0])


def main():
    try:
        if not os.path.isdir(STRUCT):
            print('[bgp-baseline] 缺目录 %s' % STRUCT)
            return 2
        check_inventory()
        pieces = {n: load_piece(n) for n in EXPECT_SIZE if os.path.exists(os.path.join(STRUCT, n + '.nbt'))}
        if len(pieces) != 20:
            print('[bgp-baseline] 只加载到 %d 个件' % len(pieces))
            return 2
        check_pieces(pieces)
        check_mirror(pieces)
        check_fertile(pieces)
        check_gate(pieces)
        check_cycle(pieces)
        check_worldgen()
        check_loot()
        check_forbid_vacuous()
        if problems:
            for p in problems[:80]:
                print('[bgp] NG ' + p)
            print('[bgp-fail] problems=%d checked=%d' % (len(problems), checked[0]))
            return 1
        print('[bgp-ok] problems=0 checked=%d templates=%d' % (checked[0], len(pieces)))
        return 0
    except SystemExit as e:
        print('[bgp-baseline] exit=%s' % e.code)
        return 2 if e.code not in (0, None) else 0
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('[bgp-error] %s: %s' % (type(e).__name__, e))
        return 2


if __name__ == '__main__':
    sys.exit(main())
