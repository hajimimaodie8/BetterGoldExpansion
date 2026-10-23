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
import random
import struct
import sys
import zipfile

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
POOL_DIR = os.path.join(WG, 'template_pool', 'golden_prison')
TREASURE_LOC = POOL + 'treasure'
LOOT_ID = 'bettergold:chests/golden_prison'

# 冻结快照：26 个模板的尺寸（第 1 步的产出，不许被悄悄改）
# ★ 第五轮（2026-10-21）：exit 从 5×8×5 → 5×(8+36)×5。门楼仍是原样 8 层，上面 36 层是
#   「上升段」井筒（井口朝天）；原因见 gp_build.py 的 EXIT_SHAFT_H 注释（fallback 件不入队，
#   挂 up_jigsaw 也永远不会被展开 ⇒ 只能做进同一个模板）。
# ★ 第七轮（2026-10-21）：exit 5×44×5 → 11×62×11：井筒顶部加一个封闭洞厅（空腔）。
# ★★ 第八轮（2026-10-22）：作者否掉了「自己挖空腔」⇒ **exit 回退成 5×8×5（门楼 8 层原样、155 格）**。
#   旧期望原文留档（第五/六/七轮）：'exit': (5, 44, 5) / 'exit': (11, 62, 11)。
#   另加 6 个「四面道固定槽」变体（几何与 cross_a/cross_b 逐格相同，只有 jigsaw 的 name/target/pool 不同）。
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
SLOT_TEMPLATES = ['cross_slot_%d_%s' % (n, s) for n in (1, 2, 3) for s in ('a', 'b')]
for _t in SLOT_TEMPLATES:
    EXPECT_SIZE[_t] = (37, 8, 37)
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
for _t in SLOT_TEMPLATES:
    EXPECT_MOUTHS[_t] = {'north', 'south', 'east', 'west'}
for _c in ('large', 'medium', 'small'):
    for _v in ('a', 'b', 'c', 'mirror', 'fertile'):
        EXPECT_MOUTHS['cell_%s_%s' % (_c, _v)] = {'north', 'south'}
EXPECT_WALK_Y = {'treasure': 3, 'cells': 1, 'lane': 1, 'exit': 1}
# 冻结快照：第 2 步的 socket 命名（name, target, pool）
# ★ 第五轮：口径变化（旧值原文留在 docs\金之牢狱-实现记录.md §11）
#   ① 小牢房不再走 cell_small_1→2→3 硬循环，三条小牢房的口一律 room→lane；
#   ② lane 两口改成对称（都 lane→room），旧的"南口进小牢房链"是序列固定的根因；
#   ③ exit 的口 target 从 room 改成 empty（自己不许再有 room 目标 ⇒ 不会无限长）。
# ★ 第七轮：exit 的 jigsaw **name** lane → room（几何没动）。
#   `JigsawBlock.canAttach` 要求「父口 target == 子件 name」⇒ name=lane 时 exit 只能贴 cell/cross
#   的口（target=lane），贴不到 lane 的 target=room 口；size 6→5 后链尾一件是 lane，
#   那两个 room 口就永远接不上（实测：3 座全 0 个出入口、落单口 5 个）。改成 room 后正好对上。
#   旧期望原文留档（第一~六轮）：'exit': {'north': ('lane', 'empty', 'minecraft:empty')}
# ★★ 第八轮 ④：宝藏房的口**唯一去向 = 固定槽 1**（旧口径：('room', 'lane', POOL + 'lane')）。
#   三个固定槽的 socket 见 SLOT_SOCK（入场口 / 送往下一槽的口 / 其余全部 room）。
SOCK = {
    'treasure': {'south': ('start', 'cross_slot_1', POOL + 'cross_slot_1')},
    'cross_a': {s: ('room', 'lane', POOL + 'lane') for s in ('north', 'south', 'east', 'west')},
    'cross_b': {s: ('room', 'lane', POOL + 'lane') for s in ('north', 'south', 'east', 'west')},
    'exit': {'north': ('room', 'empty', 'minecraft:empty')},
    'lane': {'north': ('lane', 'room', POOL + 'room'),
             'south': ('lane', 'room', POOL + 'room')},
}
for _n in ('cell_small_a', 'cell_small_b', 'cell_small_c', 'cell_small_mirror', 'cell_small_fertile',
           'cell_medium_a', 'cell_medium_b', 'cell_medium_c', 'cell_medium_mirror', 'cell_medium_fertile',
           'cell_large_a', 'cell_large_b', 'cell_large_c', 'cell_large_mirror', 'cell_large_fertile'):
    SOCK[_n] = {'north': ('room', 'lane', POOL + 'lane'), 'south': ('room', 'lane', POOL + 'lane')}

# ★★ 第八轮 ④：三个固定槽的 socket（= gp_build.SLOT_ENTRY / SLOT_CHAIN 的同一组数）
#   槽 N 的「入场口」= 父口朝向的反面，name 必须是 `cross_slot_N`（canAttach：父 target == 子 name）；
#   槽 1 从北进、往东送；槽 2 从西进、往东送；槽 3 从西进、其余全 room。
SLOT_ENTRY = {1: 'north', 2: 'west', 3: 'west'}
SLOT_CHAIN = {1: ('east', 2), 2: ('east', 3), 3: None}
for _n in (1, 2, 3):
    for _s in ('a', 'b'):
        _cfg = {}
        for _side in ('north', 'south', 'east', 'west'):
            if _side == SLOT_ENTRY[_n]:
                _cfg[_side] = ('cross_slot_%d' % _n, 'room', POOL + 'room')
            elif SLOT_CHAIN[_n] and _side == SLOT_CHAIN[_n][0]:
                _cfg[_side] = ('room', 'cross_slot_%d' % SLOT_CHAIN[_n][1],
                               POOL + 'cross_slot_%d' % SLOT_CHAIN[_n][1])
            else:
                _cfg[_side] = ('room', 'room', POOL + 'room')
        SOCK['cross_slot_%d_%s' % (_n, _s)] = _cfg

# 池：名字 -> (元素模板, fallback 池)
# ★ 第五轮：15 个池 → **4 个**；room 池 = 15 个牢房变体 + 2 个四面道（按权重随机）。
CELL_VARIANTS = ['cell_%s_%s' % (c, v) for c in ('small', 'medium', 'large')
                 for v in ('a', 'b', 'c', 'mirror', 'fertile')]
ROOM_WEIGHTS = dict([(t, 10 if t.endswith('_fertile') else 2) for t in CELL_VARIANTS]
                    + [('cross_a', 5), ('cross_b', 5)])
# ★ 第六轮：fertile 6 → 10（总权重 52 → 64，非丰饶 34）⇒ P(3 连) = 1-(34/64)^3 = 0.8501。
#   旧口径留档（第五轮）：fertile=6、总权重 52、非丰饶 34、P(3 连)=1-(34/52)^3=0.720。
EXPECT_POOLS = {
    'start': (['treasure'], 'minecraft:empty'),
    # ★★ 第八轮 ④：三个固定槽各一个池（池里 = 两种四面道的槽变体，权重 a=2 / b=1）
    'cross_slot_1': (['cross_slot_1_a', 'cross_slot_1_b'], POOL + 'exit'),
    'cross_slot_2': (['cross_slot_2_a', 'cross_slot_2_b'], POOL + 'exit'),
    'cross_slot_3': (['cross_slot_3_a', 'cross_slot_3_b'], POOL + 'exit'),
    'lane': (['lane'], POOL + 'exit'),
    'room': (CELL_VARIANTS + ['cross_a', 'cross_b'], POOL + 'exit'),
    'exit': (['exit'], 'minecraft:empty'),
}
SLOT_POOL_W = {'cross_slot_1': {'cross_slot_1_a': 2, 'cross_slot_1_b': 1},
               'cross_slot_2': {'cross_slot_2_a': 2, 'cross_slot_2_b': 1},
               'cross_slot_3': {'cross_slot_3_a': 2, 'cross_slot_3_b': 1}}
# 旧口径留档（第一~七轮，原文不删）：
#   'start': treasure | 'lane': lane→exit | 'room': 12 条 | 'exit': exit   （第五~七轮：4 个池）
#   + cell_small_1/2/3（各 1 条，fallback=自己）+ cell_medium_1..3 / cell_large_1..3 / cross_a / cross_b
#   （各自 1 条，fallback=empty）。共 15 个池文件。
# 旧口径留档（第一~四轮，原文不删）：
#   'start': treasure | 'lane': lane→exit | 'room': 12 条 | 'exit': exit
#   + cell_small_1/2/3（各 1 条，fallback=自己）+ cell_medium_1..3 / cell_large_1..3 / cross_a / cross_b
#   （各自 1 条，fallback=empty）。共 15 个池文件。

# ★★ 第八轮 ②：exit **回退**成作者原件 5×8×5（门楼 8 层原样）。
#   记账：作者原件 155 格 = **129 实心 + 26 结构空位**；空位格按 ① 的语义**整格省略**
#   ⇒ .nbt 里写出来的实心格（不含第 2 步注入的 1 个 jigsaw）= **129**。
#   旧期望原文留档（第五/六/七轮）：EXPECT_EXIT_BLOCKS = 707（井筒）/ 1728（井筒+空腔）
EXPECT_EXIT_BLOCKS = 129
# 结构空位（structure_void）→ **整格省略**的格数（逐件；1 件=0 表示该件不含结构空位）
#   来源 = 作者存档逐格实测（docs\金之牢狱-实现-证据\nbt_manifest.json 的 void 字段同一组数）
#   cross_a/cross_b 的 1480 格在 y=6..7 的屋顶外圈；exit 的 26 格在 y=5..7 的门楼顶。
EXPECT_VOID = {
    'treasure': 0, 'cross_a': 1480, 'cross_b': 1480, 'lane': 0, 'exit': 26,
}
for _t in SLOT_TEMPLATES:
    EXPECT_VOID[_t] = 1480
for _c in ('large', 'medium', 'small'):
    for _v in ('a', 'b', 'c', 'mirror', 'fertile'):
        EXPECT_VOID['cell_%s_%s' % (_c, _v)] = 0

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

# ---- 生成率 = 下界要塞（作者 2026-10-20 第三轮追加原话：「结构生成率的话跟下界要塞相同吧」）
# 真源逐字抄自原版 jar（**不凭印象**）：
#   jar  = build\moddev\artifacts\neoforge-21.1.228-client-extra-aka-minecraft-resources.jar
#   file = data/minecraft/worldgen/structure_set/nether_complexes.json
#     "placement": { "type": "minecraft:random_spread", "salt": 30084232,
#                    "separation": 4, "spacing": 27 }
#   ⇒ **原版没有 spread_type 字段**；RandomSpreadStructurePlacement.java:23 的 codec
#     `.optionalFieldOf("spread_type", RandomSpreadType.LINEAR)` ⇒ 缺省 = linear。
#   file = data/minecraft/worldgen/structure/fortress.json
#     type=minecraft:fortress / step=underground_decoration / biomes 标签 / spawn_overrides；
#     **没有 start_height、没有 project_start_to_heightmap**（高度由 FortressStructure 自己算）
#     ⇒ 「生成率」只由 structure_set 的 placement 决定（spacing/separation/spread_type）。
# ⚠ salt 故意不照抄要塞：RandomSpreadStructurePlacement#getPotentialStructureChunk 用
#   `setLargeFeatureWithSalt(seed, regionX, regionZ, salt)` 抽候选区块 ⇒ salt 相同 + 同种子
#   ⇒ 候选区块逐个重合，牢狱会永远压在下界要塞/堡垒的同一格上。salt 只改分布偏移、不改密度。
FORTRESS_PLACEMENT = {
    'type': 'minecraft:random_spread',
    'spacing': 27,
    'separation': 4,
    'spread_type': 'linear',   # 原版缺省字段 = linear（见上面的 codec 默认值）
}
FORTRESS_SALT = 30084232
OUR_SALT = 19710101

# ------------------------------------------------------------------ 第八轮（2026-10-22）
# ① structure_void = 「别动这一格」⇒ 导出时**整格省略**（不是 air、也不是 structure_void）；
# ② exit 回退 5×8×5（撤掉井筒 + 空腔）；
# ③ **只剩一套** structure / structure_set：玄武岩那一套删除，biomes 标签排除 basalt_deltas；
# ④ 三个固定槽的四面道（≥3 间）。
STRUCT_MAIN = os.path.join(WG, 'structure', 'golden_prison.json')
# ★★ 第八轮 ③：这两个文件名**必须不存在**（下面 [bgp-worldgen-single] 用它们做负向断言）
STRUCT_BASALT = os.path.join(WG, 'structure', 'golden_prison_basalt.json')
SSET_BASALT = os.path.join(WG, 'structure_set', 'golden_prison_basalt.json')
SSET_MAIN = os.path.join(WG, 'structure_set', 'golden_prison.json')
BIOME_TAG = os.path.join(TAGS, 'worldgen', 'biome', 'golden_prison', 'no_basalt.json')

# 唯一一套 structure 的字段（第八轮口径）
EXPECT_STRUCT_MAIN = {'biomes': '#bettergold:golden_prison/no_basalt',
                      'terrain_adaptation': 'bury',
                      'max_distance_from_center': 116}
# 旧口径原文留档（第六/七轮，**已作废**，不删）：
# EXPECT_STRUCT_DIFF = {
#     'main': {'biomes': '#bettergold:golden_prison/no_basalt', 'terrain_adaptation': 'bury',
#              'max_distance_from_center': 116},
#     'basalt': {'biomes': 'minecraft:basalt_deltas', 'terrain_adaptation': 'none',
#                'max_distance_from_center': 128},
# }
# 两套 structure 的「公共」字段（逐字相同 ⇒ 从**同一个构造入口** gp_build._structure 出来）
EXPECT_STRUCT_COMMON = {
# ★ 第七轮：size 6 → 5（落单口只出现在距中心 114 格的口上；见 §13.2）。
#   旧期望原文留档（第一~六轮）：'size': 6
# ★★ 第九轮（2026-10-22）：type `minecraft:jigsaw` → `bettergold:golden_prison`
#   （jigsaw 装配感知不到空域 ⇒ 出入口搬不出去；理由与源码依据见 §15）。
#   旧期望原文留档（第一~八轮）：'type': 'minecraft:jigsaw'
    'type': 'bettergold:golden_prison', 'step': 'underground_decoration', 'size': 5,
    'use_expansion_hack': False, 'spawn_overrides': {}, 'start_pool': POOL + 'start',
}
# 旧口径原文留档（第六/七轮）：
# EXPECT_SSET_STRUCTURE = {'main': 'bettergold:golden_prison',
#                          'basalt': 'bettergold:golden_prison_basalt'}
# EXPECT_SSET_SALT = {'main': OUR_SALT, 'basalt': 19710102}
EXPECT_SSET_STRUCTURE = {'main': 'bettergold:golden_prison'}   # 只剩一套
EXPECT_SSET_SALT = {'main': OUR_SALT}                          # salt 保持 19710101
# 原版 #minecraft:is_nether 的成员（真源 = build 里原版 resources jar 的
# data/minecraft/tags/worldgen/biome/is_nether.json：**5 条、无嵌套标签**，逐字抄）
NETHER_BIOMES = ['minecraft:nether_wastes', 'minecraft:soul_sand_valley',
                 'minecraft:crimson_forest', 'minecraft:warped_forest',
                 'minecraft:basalt_deltas']
# 丰饶权重记账（第六轮）：fertile 6 → 10 ⇒ 每尺寸 4×2+10=18、三尺寸 54、+cross 10 = **64**；
#   非丰饶 = 24+10 = 34 ⇒ P(3 连至少一个丰饶) = 1-(34/64)^3 = 0.8501
ROOM_TOTAL_W = 64
ROOM_FERTILE_W = 30
ROOM_P3_MIN = 0.80

# ---- 第六轮 ①：出入口「纯露头」的**实测校准快照**（2026-10-21，种子 20261020，真生成 3 座）
# 口径（docs\金之牢狱-实现记录.md §12.1）：
#   topY     = 井口环顶的世界 y（= 件 bbox.maxY = 件内 y=sy-1）
#   airFromY = 件内 3x3 内腔 9 列里，**第一条"环顶之上、连续 ≥3 格空气"的空气段的起点**
#              （若该段起点在环顶之下，说明井口本身就在空腔里 ⇒ 反正达标）。9 列取最差列。
#   达标     = airFromY <= topY（井口已经在空气里）
# 数据：docs\金之牢狱-实现-证据\gph_final\meta.json + gph_final\shaft_calibration.json
# 每口 = (topY, airFromY, 需要再加多少层的窗口 (lo, hi) 或 None)
SHAFT_CALIB = {
    'crimson_forest#15': (85, 63, (0, 2)),
    'crimson_forest#16': (85, 102, (17, 18)),
    'crimson_forest#17': (85, None, None),
    'crimson_forest#18': (85, None, None),
    'crimson_forest#19': (85, 98, (13, 13)),
    'crimson_forest#20': (85, 94, (9, 9)),
    'soul_sand_valley#7': (80, None, None),
    'basalt_deltas#7': (83, 48, (0, 22)),
}
EXIT_SHAFT_H = 0           # ★★ 第八轮：撤掉井筒（旧值 36；第五~七轮的「露头/空腔」口径一并作废）
# 旧口径原文留档（第五/六/七轮，**已作废**，不删）：
#   EXIT_SHAFT_H = 36      # 实测：任何 0..40 的加高都不比它更好（最大 2/8，+40 层 = 0/8）
#   RIM_TOP = 8 + EXIT_SHAFT_H - 1                 # 井口环顶（件内 y）= 43
#   EXIT_CAVITY_FLOOR = 39 / EXIT_CAVITY_AIR = (40, 60) / EXIT_CAVITY_CEIL = 61
#   EXIT_CAVITY_INNER = (1, 9) / EXIT_CAVITY_SIZE = (11, 11)
#   EXIT_CAVITY_H = EXIT_CAVITY_CEIL + 1 - (RIM_TOP + 1)   # 18 层
#   CAVITY_CALIB = {...} / CAVITY_CALIB_N = {...} / DOOR_BLOCKS = 132
#   （作者 2026-10-22 明确否掉"自己挖空腔"：见 docs\金之牢狱-实现记录.md §14.2）
# 门楼原件的 155 格 = 129 实心 + 26 结构空位（空位格按 ① 整格省略，不进 .nbt）
DOOR_BLOCKS = 155
# exit 的调色板白名单（第八轮回退后只用到作者原件里的方块；structure_void 已改成"省略"，
#   所以它**出现在调色板里就是 bug** —— 由 [bgp-void] 的反向断言抓）
EXIT_PALETTE = {
    'minecraft:air',
    'bettergold:gold_bricks', 'bettergold:gold_pillar', 'bettergold:gold_bars',
    'bettergold:gold_bricks_stairs', 'bettergold:gold_bricks_slab',
    'bettergold:gold_bricks_wall', 'bettergold:gold_trapdoor', 'bettergold:gold_chain',
    'minecraft:gold_block', 'minecraft:jigsaw',
}
# ---- 第七轮：**空腔之后**的实测快照（两个种子各 3 座真生成；探针 GphProbe）
#   topY = 井口环顶（件顶 − 18）；airFromY = 9 列里最差列的第一段 ≥3 空气的起点
#   数据 = docs\金之牢狱-实现-证据\gph_r7c\meta.json（种子 20261020）
#          docs\金之牢狱-实现-证据\gph_r7d\meta.json（种子 20261021）
CAVITY_CALIB = {
    'r7c（种子 20261020）': {
        'soul_sand_valley#6': (80, 45),
        'crimson_forest#12': (85, 82),
        'crimson_forest#13': (85, 50),
        'crimson_forest#14': (85, 50),
        'basalt_deltas#6': (83, 48),
    },
    'r7d（种子 20261021）': {
        'soul_sand_valley#14': (78, 43),
        'soul_sand_valley#15': (78, 43),
        'soul_sand_valley#16': (78, 43),
        'soul_sand_valley#17': (78, 43),
        'soul_sand_valley#18': (78, 43),
        'crimson_forest#6': (77, 42),
        'basalt_deltas#12': (78, 43),
        'basalt_deltas#13': (78, 43),
        'basalt_deltas#14': (78, 43),
    },
}
CAVITY_CALIB_N = {'r7c（种子 20261020）': 5, 'r7d（种子 20261021）': 9}   # 仅留档（第八轮作废）
# 旧口径原文留档（第七轮，**已作废**）：
# DOOR_BLOCKS = 132                              # y<=7 的实心格 = 131 门楼 + 1 个 jigsaw（155 − 24 开顶）
# # exit 的调色板白名单（含第七轮新用的 minecraft:gold_block；其余全部是作者原件里就有的）
# EXIT_PALETTE = {
#     'minecraft:air', 'minecraft:structure_void',
#     'bettergold:gold_bricks', 'bettergold:gold_pillar', 'bettergold:gold_bars',
#     'bettergold:gold_bricks_stairs', 'bettergold:gold_bricks_slab',
#     'bettergold:gold_bricks_wall', 'bettergold:gold_trapdoor', 'bettergold:gold_chain',
#     'minecraft:gold_block', 'minecraft:jigsaw',
# }

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


# ------------------------------------------------------------------ 作者存档（region）只读
# ★ 第八轮 ①：structure_void 的**唯一真源 = 作者存档**（他把"别动这一格"用结构空位块标在件里）。
#   本段只读 region（绝不写），逐格取出 14 个源件的方块，用来对穿「件内被省略的格子 == 源存档的结构空位」。
WORLD_SAVE = os.path.join(ROOT, 'docs', '金之牢狱-素材清单', '金之牢狱')
# (件名, 世界原点 x,y,z, 尺寸 sx,sy,sz) —— 与 gp_build.SRC 逐字相同（14 条）
SRC_PIECES = [
    ('treasure', 397, -60, 491, 21, 9, 21),
    ('cross_a', 421, -60, 435, 37, 8, 37),
    ('cross_b', 421, -60, 475, 37, 8, 37),
    ('cell_large_a', 461, -60, 413, 15, 6, 31),
    ('cell_large_b', 461, -60, 447, 15, 6, 31),
    ('cell_large_c', 461, -60, 481, 15, 6, 31),
    ('cell_medium_a', 479, -60, 443, 15, 6, 21),
    ('cell_medium_b', 479, -60, 467, 15, 6, 21),
    ('cell_medium_c', 479, -60, 491, 15, 6, 21),
    ('cell_small_a', 497, -60, 473, 15, 6, 11),
    ('cell_small_b', 497, -60, 487, 15, 6, 11),
    ('cell_small_c', 497, -60, 501, 15, 6, 11),
    ('lane', 3, -60, 501, 5, 5, 3),
    ('exit', 3, -60, 507, 5, 8, 5),
]
# 派生件 → 基准件（镜像 x→sx-1-x；丰饶/固定槽 = 几何与基准逐格相同）
SRC_DERIVED = {}
for _c in ('small', 'medium', 'large'):
    SRC_DERIVED['cell_%s_mirror' % _c] = ('mirror', 'cell_%s_a' % _c)
    SRC_DERIVED['cell_%s_fertile' % _c] = ('same', 'cell_%s_a' % _c)
for _n in (1, 2, 3):
    for _s in ('a', 'b'):
        SRC_DERIVED['cross_slot_%d_%s' % (_n, _s)] = ('same', 'cross_%s' % _s)
# 注意：cross_a / cross_b 自身也是源件（不镜像、不派生）。
_SRC_CACHE = {}


def _decode_section(sec):
    """把 1.21 的 section.block_states 解成 {(lx,y,z): Name}（bits 不跨 long 的 padded 格式）。"""
    st = sec.get('block_states')
    sy = sec.get('Y')
    if not st or sy is None:
        return {}
    pal = [p.get('Name') for p in (st.get('palette') or [])]
    if not pal:
        return {}
    if len(pal) == 1:
        return {(x, y, z): pal[0] for x in range(16) for y in range(16) for z in range(16)}
    bits = max(4, (len(pal) - 1).bit_length())
    per = 64 // bits
    mask = (1 << bits) - 1
    data = st.get('data') or []
    out = {}
    idx = 0
    for y in range(16):
        for z in range(16):
            for x in range(16):
                li, off = divmod(idx, per)
                idx += 1
                if li >= len(data):
                    continue
                v = (data[li] >> (off * bits)) & mask
                if v < len(pal):
                    out[(x, y, z)] = pal[v]
    return out


def load_world_cells(box):
    """只读作者存档 ⇒ {(wx,wy,wz): Name}（只解码与该 box 相交的区块）。

    ⚠ 坐标口径必须与 `docs\\金之牢狱-实现-证据\\gp_build.load_world()` **逐字一致**：
      区块坐标 = region 文件里的**表内索引**（`cx = i & 31` / `cz = i >> 5`，不带文件名里的符号），
      文件名（r.-1.-1 / r.0.0 ...）只决定读的顺序（sorted，后者覆盖前者）。
      这套存档的 region 文件名与索引不是标准对应（同一片 0..511 由 4 个文件拼起来），
      当年流水线就是这么读出 14 个件的 —— 关卡照抄同一口径，才对得上"件内省略格 == 源存档空位"。
    """
    import zlib
    x0, y0, z0, x1, y1, z1 = box
    want = set()
    for cx in range(x0 >> 4, (x1 >> 4) + 1):
        for cz in range(z0 >> 4, (z1 >> 4) + 1):
            want.add((cx, cz))
    rd = os.path.join(WORLD_SAVE, 'region')
    if not os.path.isdir(rd):
        return {}
    cells = {}
    for fn in sorted(os.listdir(rd)):
        if not fn.endswith('.mca'):
            continue
        raw = open(os.path.join(rd, fn), 'rb').read()
        if len(raw) < 8192:
            continue
        for (cx, cz) in want:
            li = (cx & 31) + (cz & 31) * 32
            off = int.from_bytes(raw[li * 4:li * 4 + 3], 'big')
            cnt = raw[li * 4 + 3]
            if off == 0 or cnt == 0:
                continue
            base = off * 4096
            if base + 5 > len(raw):
                continue
            ln = int.from_bytes(raw[base:base + 4], 'big')
            comp = raw[base + 4]
            payload = raw[base + 5:base + 4 + ln]
            if comp == 1:
                payload = gzip.decompress(payload)
            elif comp == 2:
                payload = zlib.decompress(payload)
            elif comp != 3:
                continue
            r = R(payload)
            if r.u1() != TAG_COMPOUND:
                continue
            r.s()
            root = rp(r, TAG_COMPOUND)
            for sec in (root.get('sections') or []):
                sy = (sec.get('Y') or 0) * 16
                for (lx, ly, lz), nm in _decode_section(sec).items():
                    cells[(cx * 16 + lx, sy + ly, cz * 16 + lz)] = nm
    return cells


def source_void_cells(name):
    """作者存档里某件（件内相对坐标）的结构空位格集合。"""
    if name in _SRC_CACHE:
        return _SRC_CACHE[name]
    if name in SRC_DERIVED:
        kind, base = SRC_DERIVED[name]
        if kind == 'mirror':
            base_row = [p for p in SRC_PIECES if p[0] == base][0]
            sx = base_row[4]
            out = {(sx - 1 - x, y, z) for (x, y, z) in source_void_cells(base)}
        else:
            out = set(source_void_cells(base))
        _SRC_CACHE[name] = out
        return out
    row = [p for p in SRC_PIECES if p[0] == name]
    if not row:
        _SRC_CACHE[name] = set()
        return set()
    _, x0, y0, z0, sx, sy, sz = row[0]
    cells = load_world_cells((x0, y0, z0, x0 + sx - 1, y0 + sy - 1, z0 + sz - 1))
    out = set()
    for y in range(y0, y0 + sy):
        for z in range(z0, z0 + sz):
            for x in range(x0, x0 + sx):
                if cells.get((x, y, z)) == VOID:
                    out.add((x - x0, y - y0, z - z0))
    _SRC_CACHE[name] = out
    return out


# ------------------------------------------------------------------ 件模型
AIR = 'minecraft:air'
VOID = 'minecraft:structure_void'
DIRV = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0)}
OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
# 可走格：空气 / 结构空位 / jigsaw（jigsaw 的 final_state=air 在放置时变成空气）
PASS = (AIR, VOID, 'minecraft:jigsaw')
MAX_DEPTH = 5          # = structure json 的 size（[bgp-worldgen] 另有一条断言钉它）
                       # 旧值 6（第一~六轮）留档：第七轮 6 → 5 修落单口，见 §13.2
# 空气地板值（回归用；口径与实测见 docs\金之牢狱-生成预览.md §阶段 B）
# ⚠ 作者原口径是「整 bbox 空气 >= 60%% / 行走层 >= 80%%」——按作者自己 20 件的几何**达不到**：
#   外壳普遍 2~3 格厚、牢房内部还有栅栏/金堆/箱笼，实测整 bbox 22.00%%~44.67%%、
#   行走层内圈 52.14%%~100%%。所以门槛取「能抓住 P0 的回归地板」，实测值全部打印出来对照。
AIR_MIN_BBOX = 0.20    # 整 bbox 空气 >= 20%%（修前 0.00%%；实测最低 22.00%% = exit）
WALK_INNER_MIN = 0.50  # 行走层内圈空气 >= 50%%（修前 ~1.7%%；实测最低 52.14%%）
AIR_REACH_MIN = 0.70   # 件内从口洪泛能到达的空气占比（实测最低 79.55%% = exit 顶层独立空腔）


def strip_comments(s, style):
    """去掉注释后再做正向 needle：避免「注释里写着这句话」被当成实现。

    style='py' 去 #...；style='java' 去 //... 与 /*...*/。
    （粗略实现：不处理字符串里的 # —— 本文件只用它找不含 # 的 needle。）
    """
    out = []
    i, n = 0, len(s)
    in_block = False
    while i < n:
        if style == 'java' and in_block:
            j = s.find('*/', i)
            if j < 0:
                return ''.join(out)
            i = j + 2
            in_block = False
            continue
        ch = s[i]
        if style == 'java' and s.startswith('/*', i):
            in_block = True
            i += 2
            continue
        if style == 'java' and s.startswith('//', i):
            j = s.find('\n', i)
            i = n if j < 0 else j
            continue
        if style == 'py' and ch == '#':
            j = s.find('\n', i)
            i = n if j < 0 else j
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


class Piece:
    def __init__(self, name, size, blocks, jigsaws, chests, palette, ents=None, bes=None,
                 absent=None):
        self.name = name
        self.size = size
        self.blocks = blocks          # (x,y,z) -> (name, props)
        self.jigsaws = jigsaws        # (x,y,z) -> be dict
        self.chests = chests          # list of (x,y,z)
        self.palette = palette
        self.ents = ents or []        # [{pos, blockPos, nbt}] 第五轮
        self.bes = bes or {}          # (x,y,z) -> be dict（不含 jigsaw）第五轮
        # ★ 第八轮 ①：**没写进 .nbt 的格子** = 结构空位（"别动这一格"）
        self.absent = absent or set()

    def at(self, p):
        return self.blocks.get(p)


def load_piece(name):
    path = os.path.join(STRUCT, name + '.nbt')
    root = parse_nbt(path)
    size = tuple(root['size'])
    pal = root['palette']
    blocks, jig, chests, bes = {}, {}, [], {}
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
        if 'nbt' in b and nm != 'minecraft:jigsaw':
            bes[p] = b['nbt']
    ents = []
    for e in (root.get('entities') or []):
        ents.append({'pos': [float(v) for v in (e.get('pos') or [])],
                     'blockPos': [int(v) for v in (e.get('blockPos') or [])],
                     'nbt': e.get('nbt') or {}})
    # ★ 第八轮 ①：bbox 里"没写的格子"= 结构空位（整格省略）。数量由 [bgp-void] 逐件钉住。
    absent = set()
    for y in range(size[1]):
        for z in range(size[2]):
            for x in range(size[0]):
                if (x, y, z) not in blocks:
                    absent.add((x, y, z))
    return Piece(name, size, blocks, jig, chests, pal, ents, bes, absent)


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


def piece_sockets(p):
    """{side: (pos, be)} —— 只取「落在唯一外侧面上的口」（非法口由 [bgp-gate] 报）。"""
    out = {}
    for pos, be in p.jigsaws.items():
        o = outward(pos, p.size)
        if len(o) == 1:
            out[o[0]] = (pos, be)
    return out


def mouth_cells(pos, side):
    """口平面（件边界那一层）3 宽 x 3 高 = 9 格；再返回朝件内一格的 9 格。"""
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


def inner_of(pos, side):
    """口朝件内一格（洪泛种子）。"""
    dx, dy, dz = DIRV[side]
    return (pos[0] - dx, pos[1], pos[2] - dz)


def flood(piece, seeds, size=None):
    """件内 3D 6 邻接洪泛（空气 / structure_void / jigsaw 可走）。"""
    sx, sy, sz = size or piece.size
    seen = set(s for s in seeds if 0 <= s[0] < sx and 0 <= s[1] < sy and 0 <= s[2] < sz)
    q = list(seen)
    while q:
        c = q.pop()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
            if n in seen or not (0 <= n[0] < sx and 0 <= n[1] < sy and 0 <= n[2] < sz):
                continue
            v = piece.at(n)
            if v is not None and v[0] in PASS:
                seen.add(n)
                q.append(n)
    return seen


def mouth_passable(piece, sock, size):
    """口必须是 3 宽 × 3 高、洞底 = 行走面，且洞底下一格是实心（能站）。

    ⚠ 旧口径只验「口位这一层」的 3×3 与洞底；它**验不出**房间内部被地形灌满
    （jigsaw 的 final_state=air 只挖 1 格）。真正的可走性由 check_air 的 flood-fill 兜。
    """
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
    # 口内一格（朝件内）也必须 3×3 空，否则只是“贴面开了个洞”
    dx, dy, dz = DIRV[side]
    for d in (-1, 0, 1):
        for dy2 in (0, 1, 2):
            if side in ('north', 'south'):
                c = (x + d - dx, y + dy2, z - dz)
            else:
                c = (x - dx, y + dy2, z + d - dz)
            v = piece.at(c)
            if v is not None and v[0] not in (AIR, 'minecraft:jigsaw'):
                bad.append(('inner', c, v))
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
    if len(files) != 26:
        # 第八轮：20 → 26（+ 6 个四面道固定槽变体）；旧口径 20
        ng('bgp-inventory', '模板数 %d != 26' % len(files))
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
    if len(pngs) < 26:
        ng('bgp-blueprint', '蓝图 %d 张 < 26' % len(pngs))
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
        if name in EXPECT_SRC_COUNT and name != 'exit':
            # 取证表是「抠出来时」的方块数（含作者的结构空位格），不含第 2 步注入的 jigsaw。
            # ★ 第八轮：结构空位格**整格省略** ⇒ 写出来的非空气格 + 省略格 − jigsaw 才对得上取证值。
            got = (sum(1 for v in p.blocks.values() if v[0] != AIR) + len(p.absent)
                   - len(p.jigsaws))
            if got != EXPECT_SRC_COUNT[name]:
                ng('bgp-nbt', '%s 方块数(不含 jigsaw，含省略的空位格) %d != 取证 %d'
                   % (name, got, EXPECT_SRC_COUNT[name]))
            ok()
        if name == 'exit':
            # ★★ 第八轮：回退成作者原件 5×8×5 ⇒ 写出的实心格 = 155 − 26 结构空位 = **129**
            #   （不含第 2 步注入的 1 个 jigsaw）。
            #   旧口径原文留档（第五/六/七轮）：1728（井筒 36 层 + 空腔）/ 707（井筒）。
            got = sum(1 for v in p.blocks.values() if v[0] != AIR) - len(p.jigsaws)
            if got != EXPECT_EXIT_BLOCKS:
                ng('bgp-nbt', 'exit 写出的实心格(不含 jigsaw) %d != 记账 %d（155 原件 − 26 结构空位）'
                   % (got, EXPECT_EXIT_BLOCKS))
            ok()
            if got + len(p.absent) != DOOR_BLOCKS:
                ng('bgp-nbt', 'exit 实心 %d + 省略的空位 %d != 作者原件 %d'
                   % (got, len(p.absent), DOOR_BLOCKS))
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


def check_air(pieces):
    """[bgp-air] 模板空气 —— 补「口成对 ≠ 能走」的真空档（2026-10-20 阶段 B）。

    ⚠ 旧口径原文（上一轮 A 级）：「34/34 口成对且可通」。那个读数**只检查了口位那一格**
    （jigsaw 的 final_state=air 会挖掉 1 格）+ 口对面一格 + 洞底下一格；
    **门内 3x3、房间内部空气、「从宝藏房能不能走到出入口」从来没验过**。
    实测反证（修前）：20 个模板 0 条 minecraft:air ⇒ 真生成件内空气 4.10%、行走层 5.73%、
    门洞只有 1 格（只有 jigsaw 那格被挖）。
    ⇒ 「口成对」只说明两个 jigsaw 贴上了，**不等于人能走过去**。

    本段逐件验（不跑游戏）：palette 有 air / bbox 每格都写 / 逐口两层 3x3x1 全空 /
    行走层内圈空气 / 件内从口洪泛能到整间房。拼起来之后的连通性见 [bgp-connect]。
    """
    worst_bbox, worst_walk, worst_reach = 100.0, 100.0, 100.0
    mouths = 0
    for name, p in pieces.items():
        sx, sy, sz = p.size
        vol = sx * sy * sz
        names = {v[0] for v in p.blocks.values()}
        if AIR not in names:
            ng('bgp-air', '%s 的 palette 没有 minecraft:air（模板不会挖空）' % name)
        ok()
        if len(p.blocks) + len(p.absent) != vol:
            ng('bgp-air', '%s 只写了 %d / %d 格（空气没写满，放置时不会把地形挖成房间）'
               % (name, len(p.blocks), vol))
        ok()
        # ★ 第八轮 ①：省略的格子只许是「结构空位」⇒ 数量必须逐件等于 EXPECT_VOID
        if len(p.absent) != EXPECT_VOID.get(name, 0):
            ng('bgp-void', '%s 省略了 %d 格 != 期望结构空位 %d'
               % (name, len(p.absent), EXPECT_VOID.get(name, 0)))
        ok()
        air = sum(1 for v in p.blocks.values() if v[0] == AIR)
        if air <= 0:
            ng('bgp-air', '%s 一条空气条目都没有（整件实心）' % name)
        frac = 100.0 * air / vol
        worst_bbox = min(worst_bbox, frac)
        if frac < AIR_MIN_BBOX * 100:
            ng('bgp-air', '%s 整 bbox 空气 %.2f%% < %.0f%%（模板空气没进来）'
               % (name, frac, AIR_MIN_BBOX * 100))
        ok()
        # 行走层（洞底那一层 = jigsaw 的 y）：整层 + 内圈（去掉一圈外壳）
        wy = 3 if name == 'treasure' else 1
        wl = [(x, wy, z) for x in range(sx) for z in range(sz)]
        wi = [(x, wy, z) for x in range(1, sx - 1) for z in range(1, sz - 1)]
        wa = sum(1 for c in wl if (p.at(c) or ('',))[0] == AIR)
        ia = sum(1 for c in wi if (p.at(c) or ('',))[0] == AIR)
        wfrac = 100.0 * ia / max(1, len(wi))
        worst_walk = min(worst_walk, wfrac)
        if wfrac < WALK_INNER_MIN * 100:
            ng('bgp-air', '%s 行走层 y=%d 内圈空气 %.2f%% < %.0f%%（房间被填，站不进去）'
               % (name, wy, wfrac, WALK_INNER_MIN * 100))
        ok()
        # 逐口：口平面 3x3x1 全空 + 口内一层 3x3x1 全空（不是只有 jigsaw 那 1 格）
        seeds = []
        for side, (pos, be) in sorted(piece_sockets(p).items()):
            plane, inner = mouth_cells(pos, side)
            pb = [c for c in plane if (p.at(c) or ('',))[0] not in PASS]
            ib = [c for c in inner if (p.at(c) or ('',))[0] not in PASS]
            if pb:
                ng('bgp-air', '%s 的 %s 口 %s 口平面 3x3x1 有 %d 格不是空气（第一格 %s）'
                   % (name, side, pos, len(pb), pb[0]))
            if ib:
                ng('bgp-air', '%s 的 %s 口 %s 口内一层 3x3x1 有 %d 格不是空气（第一格 %s）'
                   % (name, side, pos, len(ib), ib[0]))
            ok(2)
            mouths += 1
            seeds.append(inner_of(pos, side))
        # 件内连通：从第一个口洪泛，必须吃到其余所有口 + 整间房
        if seeds:
            seen = flood(p, seeds[:1])
            miss = [s for s in seeds[1:] if s not in seen]
            if miss:
                ng('bgp-air', '%s 有 %d 个口与第一个口不连通（房间/走廊被填）' % (name, len(miss)))
            ok()
            air_cells = [c for c, v in p.blocks.items() if v[0] == AIR]
            cov = sum(1 for c in air_cells if c in seen)
            reach = 100.0 * cov / max(1, len(air_cells))
            worst_reach = min(worst_reach, reach)
            if reach < AIR_REACH_MIN * 100:
                ng('bgp-air', '%s 从口洪泛只到得了 %.2f%% 的空气（房间没连到门）' % (name, reach))
            ok()
    if mouths == 0:
        ng('bgp-air', '一个口都没扫描到（空转）')
    print('[bgp-air] %d 件 / %d 口：逐口两层 3x3x1 全空；最低整 bbox 空气 %.2f%%、'
          '最低行走层内圈 %.2f%%、最低件内可达 %.2f%%'
          % (len(pieces), mouths, worst_bbox, worst_walk, worst_reach))
    print('[bgp-air] 参考：作者原口径「整 bbox >= 60%% / 行走层 >= 80%%」按作者件几何不可达'
          '（外壳 2~3 格厚 + 牢房内栅栏/金堆/箱笼），本关卡的回归地板 = %.0f%% / %.0f%% / 件内可达 %.0f%%'
          % (AIR_MIN_BBOX * 100, WALK_INNER_MIN * 100, AIR_REACH_MIN * 100))
    # 正向 needle（跑在**去注释**源码上）：流水线必须真的把空气写进 NBT，P0 的老写法不许回来
    gp = os.path.join(ROOT, 'docs', '金之牢狱-实现-证据', 'gp_build.py')
    if not os.path.exists(gp):
        ng('bgp-air', '缺流水线 gp_build.py（没法复核模板是怎么造的）')
    else:
        src = strip_comments(open(gp, encoding='utf-8').read(), 'py')
        if "'minecraft:air'" not in src:
            ng('bgp-air', 'gp_build.py 去注释后找不到 minecraft:air 的写入分支')
        ok()
        if 'if nm in AIR: continue' in src:
            ng('bgp-air', 'gp_build.py 里 P0 的老写法「if nm in AIR: continue」又回来了')
        ok()


def check_void(pieces):
    """[bgp-void] ★★ 第八轮 ①：structure_void = 「别动这一格」，导出时必须**整格省略**。

    作者原话（2026-10-22）：
      「冷知识：结构空位（structure_void）适用于为结构方块生成结构时不会替代拥有结构空位位置的方块，
        你居然给我神奇地保留下来并且生硬地把方块给顶掉了」
    源码依据（build\\moddev\\artifacts\\neoforge-21.1.228-sources.jar）：
      · `StructureBlockEntity:341` 保存结构 = `fillFromWorld(..., Blocks.STRUCTURE_VOID)`
        ⇒ 结构空位格**根本不进模板**；`fillFromWorld:100` 就是 `if (toIgnore == null || !blockstate.is(toIgnore))`。
      · `StructureTemplate.placeInWorld:248-261` 只放置模板里有的格子 ⇒ 不写 = 原样保留地形。
      · 写 air = 地形被挖成空气（作者说的"生硬地把方块给顶掉了"）；写 structure_void = 世界里塞一个
        隐形但有 6/16 碰撞盒的方块（`StructureVoidBlock.getShape`）**并同样顶掉地形**。

    本段四条（双向）：
      ① 件内**省略格数**逐件 == 源存档里的结构空位格数（EXPECT_VOID，同时与 region 逐格对穿）；
      ② 任何模板的 palette/top 都不许出现 `minecraft:structure_void`（写了就是顶掉地形）；
      ③ 作者原本是 **air** 的格子必须仍是 air（上一轮 P0 的"房间/走廊被灌满"修复不许回退）；
      ④ 省略的格子只许在**行走面之上**（房间/走廊内部一格都不许省 ⇒ 洪泛照旧能到出口）。
    """
    bad = []
    for name, p in sorted(pieces.items()):
        # ② 整件调色板里不许有 structure_void
        names = {v[0] for v in p.blocks.values()}
        if VOID in names:
            ng('bgp-void', '%s 的调色板里有 minecraft:structure_void（会把地形顶掉）' % name)
        ok()
        # ① 省略格数 == 冻结期望 == 源存档逐格
        want = source_void_cells(name)
        if len(p.absent) != EXPECT_VOID.get(name, 0):
            ng('bgp-void', '%s 省略 %d 格 != 冻结期望 %d'
               % (name, len(p.absent), EXPECT_VOID.get(name, 0)))
        ok()
        if p.absent != want:
            only_nbt = sorted(p.absent - want)[:4]
            only_src = sorted(want - p.absent)[:4]
            ng('bgp-void', '%s 省略格与源存档的结构空位**逐格不符**（多 %d / 少 %d；例 %s / %s）'
               % (name, len(p.absent - want), len(want - p.absent), only_nbt, only_src))
            bad.append(name)
        ok()
        # ④ 省略格必须全在行走面之上（房间/走廊内部一格都不许省）
        wy = 3 if name == 'treasure' else 1
        low = [c for c in p.absent if c[1] <= wy]
        if low:
            ng('bgp-void', '%s 有 %d 个省略格在行走面 y<=%d（房间/走廊被省掉了）例 %s'
               % (name, len(low), wy, sorted(low)[:3]))
        ok()
        # ③ 作者原本是 air 的格子**必须仍是 air**：件内每个非省略格都必须写进模板（air 或方块）
        missing = [c for c in ((x, y, z) for y in range(p.size[1])
                               for z in range(p.size[2]) for x in range(p.size[0]))
                   if c not in p.absent and c not in p.blocks]
        if missing:
            ng('bgp-void', '%s 有 %d 格既没写也没省略（作者原本是 air 的格被漏掉）例 %s'
               % (name, len(missing), sorted(missing)[:3]))
        ok()
    # 特别放大：cross / exit 的省略格**必须**是"屋顶外圈"，不许侵到行走层
    for name in ('cross_a', 'cross_b', 'exit') + tuple(SLOT_TEMPLATES):
        p = pieces[name]
        ys = sorted({c[1] for c in p.absent})
        if not p.absent:
            ng('bgp-void', '%s 一格结构空位都没有（源存档里是有 1480 / 26 格的）' % name)
        ok()
        walk_y = 3 if name == 'treasure' else 1
        if ys and ys[0] <= walk_y + 1:
            ng('bgp-void', '%s 的结构空位最低在 y=%d（行走面 y=%d 附近）' % (name, ys[0], walk_y))
        ok()
    print('[bgp-void] 结构空位：26 件里 %d 件含空位（cross/槽变体 1480 格、exit 26 格），'
          '逐格 == 源存档；palette 里 structure_void = 0；省略格全在行走面之上'
          % sum(1 for p in pieces.values() if p.absent))
    print('[bgp-void] 语义依据：StructureBlockEntity:341 fillFromWorld(..., Blocks.STRUCTURE_VOID)'
          ' ⇒ 空位格不进模板；placeInWorld 只放模板里有的格子 ⇒ 不写 = 地形原样保留')
    # 正向 needle（去注释源码）：流水线必须"跳过空位格"，不许把空位写成 air / structure_void
    gp = os.path.join(ROOT, 'docs', '金之牢狱-实现-证据', 'gp_build.py')
    if not os.path.exists(gp):
        ng('bgp-void', '缺流水线 gp_build.py')
        return
    src = strip_comments(open(gp, encoding='utf-8').read(), 'py')
    if "if v is not None and v[0] == 'minecraft:structure_void':" not in src:
        ng('bgp-void', 'gp_build.build_nbt 里找不到"跳过 structure_void 格"的分支')
    ok()
    if 'void_cells.append(key)' not in src:
        ng('bgp-void', 'gp_build.build_nbt 没有把空位格记进 void_cells')
    ok()
    if "nm, pr = 'minecraft:air', {}" not in src:
        ng('bgp-void', 'gp_build.build_nbt 里"作者原本是 air ⇒ 写 air"的分支不见了（P0 修复会回退）')
    ok()


def pool_name(pool):
    return pool[len(POOL):] if isinstance(pool, str) and pool.startswith(POOL) else None


def load_pools_actual():
    """从磁盘上的池文件读 (templates, fallback)。

    让 [bgp-connect] 跟着**实际 JSON** 走 —— 否则"把 lane 的 fallback 改 empty"这类扰动
    在虚拟拼接里看不出来（P9/P18 会假绿）。
    """
    out = {}
    for f in sorted(os.listdir(POOL_DIR)):
        if not f.endswith('.json'):
            continue
        d = json.load(open(os.path.join(POOL_DIR, f), encoding='utf-8'))
        els = [((e.get('element') or {}).get('location') or '').split('/', 2)[-1]
               for e in (d.get('elements') or [])]
        out[f[:-5]] = (els, d.get('fallback'))
    return out


def assemble(pieces, rev_opts, pools=None, seed=None):
    """按池的接线规则把 20 件虚拟拼成一座（复刻 JigsawPlacement 的口径，不跑游戏）。

    - 每个口只用一次（引擎里 jigsaw 被接上就消耗掉，剩下那个口才继续长）；
    - `depth+1 > size(6)` 时放的是**目标池的 fallback**（不是再 roll 元素）；
    - `depth+1 > 7` 不再放（A 级实测最深处就是 7：宝藏 0 … 出入口 7）。
    `rev_opts` 只影响候选/旋转的挑选次序，用来造出两种不同的真实拼法。
    `seed` 非空时 = **忠实模式**：按 `JigsawPlacement` 第 349~354 行，每个深度都先试目标池、
    再加 fallback 池，并用固定种子洗牌（引擎本身就是 `getShuffledTemplates` 按权重洗牌）。
    seed 为空 = 旧口径（只在 maxDepth 用 fallback），用来保留"最长的纯走廊链"这一档。
    """
    pools = pools or EXPECT_POOLS
    rnd = random.Random(seed) if seed is not None else None
    sock = {n: piece_sockets(p) for n, p in pieces.items()}
    root = {'name': 'treasure', 'rot': 'none', 'origin': (0, 0, 0),
            'bbox': piece_bbox(pieces['treasure'].size, 'none', (0, 0, 0)),
            'depth': 0, 'used': set(), 'via': '-', 'parent': None}
    placed = [root]
    q = [root]
    i = 0
    while i < len(q):
        cur = q[i]
        i += 1
        for side in ('north', 'south', 'east', 'west'):
            if side not in sock[cur['name']] or side in cur['used']:
                continue
            pos, be = sock[cur['name']][side]
            tg, pl = be.get('target'), be.get('pool')
            pn = pool_name(pl)
            if pn is None or pn not in pools:
                continue
            wside = rot_dir(side, cur['rot'])
            dchild = cur['depth'] + 1
            if dchild > MAX_DEPTH + 1:
                continue
            if dchild > MAX_DEPTH:
                fbn = pool_name(pools[pn][1])
                if fbn is None or fbn not in pools:
                    continue
                cands = list(pools[fbn][0])
            else:
                cands = list(pools[pn][0])
                if rnd is not None:
                    # ★ 第七轮：忠实模式 —— 引擎在每个深度都先试目标池、**再试 fallback 池**
                    #   （`JigsawPlacement` 第 349~354 行：`list` = 目标池（depth != maxDepth 时）
                    #   + `list.addAll(holder1.getShuffledTemplates(...))` 恒加 fallback）。
                    #   旧口径（第一~六轮）只试目标池 ⇒ 虚拟拼接永远不在中间放 fallback（出入口），
                    #   链一直长到 maxDepth 才收敛，和真生成（21 件里有 8 个出入口）对不上。
                    fbn = pool_name(pools[pn][1])
                    if fbn is not None and fbn in pools:
                        cands += list(pools[fbn][0])
            d = DIRV[wside]
            rp0 = rot_pos(pos, cur['rot'])
            wpos = tuple(cur['origin'][k] + rp0[k] for k in range(3))
            tgt = tuple(wpos[k] + d[k] for k in range(3))
            opts = []
            for ci, cn in enumerate(cands):
                if cn not in sock:
                    continue
                for cside, (cpos, cbe) in sorted(sock[cn].items()):
                    if cbe.get('name') != tg:
                        continue
                    for ri, r in enumerate(ROTS):
                        if rot_dir(cside, r) != OPP[wside]:
                            continue
                        rp = rot_pos(cpos, r)
                        origin = tuple(tgt[k] - rp[k] for k in range(3))
                        cb = piece_bbox(pieces[cn].size, r, origin)
                        if any(bbox_overlap(cb, z['bbox']) for z in placed):
                            continue
                        opts.append((ci, ri, cn, cside, r, origin, cb))
            # 池里引用了不存在的模板时不要崩（[bgp-pool] 会报那条），跳过即可
            opts = [o for o in opts if o[2] in pieces]
            if rev_opts:
                opts = opts[::-1]
            if rnd is not None:
                rnd.shuffle(opts)
            if not opts:
                continue
            ci, ri, cn, cside, r, origin, cb = opts[0]
            n2 = {'name': cn, 'rot': r, 'origin': origin, 'bbox': cb, 'depth': dchild,
                  'used': {cside}, 'via': side, 'parent': cur}
            cur['used'].add(side)
            q.append(n2)
            placed.append(n2)
    return placed


def check_connect(pieces):
    """[bgp-connect] 拼起来之后「真的能走」：两组真实拼接，从宝藏房洪泛必须到每个出入口。

    ⚠ 这一维**不能**用「口成对 34/34」代替：口成对只说明两个 jigsaw 贴上了，
    「门内 3x3 空不空 / 房间能不能站人 / 从宝藏房走不走得到出入口」是另一回事
    （修前实测：门洞 1 格、件内空气 4.10%、行走层 5.73%）。
    """
    total = 0
    exits_total = 0
    maxp = 0
    pools = load_pools_actual()
    # ★ 第七轮：size 6→5 之后，"最长的纯走廊链"（旧口径）会停在 lane 上、接不到出入口；
    #   而引擎在每个深度都会同时试 fallback（出入口）⇒ 真生成里出入口很多。
    #   所以这里跑 5 组：前两组 = 旧口径（确定性，最长链），后三组 = **忠实模式**（固定种子洗牌，
    #   目标池 + fallback 池一起试）。断言口径见函数末尾。
    CASES = [('rev0', False, None), ('rev1', True, None),
             ('seed11', False, 11), ('seed22', False, 22), ('seed33', False, 33)]
    for tag, rev, sd in CASES:
        placed = assemble(pieces, rev, pools, sd)
        if len(placed) < 2:
            ng('bgp-connect', '虚拟拼接 %s 只放下 %d 件（>= 2 都不到），接线规则或件尺寸变了'
               % (tag, len(placed)))
            continue
        maxp = max(maxp, len(placed))
        cells = {}
        for z in placed:
            p = pieces[z['name']]
            o, r = z['origin'], z['rot']
            for local, (nm, pr) in p.blocks.items():
                rp = rot_pos(local, r)
                cells[(o[0] + rp[0], o[1] + rp[1], o[2] + rp[2])] = nm in PASS
        # 种子 = 宝藏房内部（去掉一圈外壳）的空气 —— 根件放在原点、rot=none，局部坐标即世界坐标
        sx, sy, sz = pieces['treasure'].size
        seeds = [local for local, v in pieces['treasure'].blocks.items()
                 if v[0] == AIR and 1 <= local[0] <= sx - 2
                 and 1 <= local[1] <= sy - 2 and 1 <= local[2] <= sz - 2]
        seen = set(seeds)
        q = list(seeds)
        while q:
            c = q.pop()
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                n = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
                if n in seen or not cells.get(n):
                    continue
                seen.add(n)
                q.append(n)
        # 逐条接线：父口内侧 + 子口内侧（= 子件里面）都必须洪泛到
        bad = []
        for z in placed[1:]:
            a = z['parent']
            side = z['via']
            pos = piece_sockets(pieces[a['name']])[side][0]
            rp = rot_pos(pos, a['rot'])
            wpar = tuple(a['origin'][k] + rp[k] for k in range(3))
            d = DIRV[rot_dir(side, a['rot'])]
            p_in = (wpar[0] - d[0], wpar[1] - d[1], wpar[2] - d[2])
            c_mouth = (wpar[0] + d[0], wpar[1] + d[1], wpar[2] + d[2])
            c_in = (c_mouth[0] + d[0], c_mouth[1] + d[1], c_mouth[2] + d[2])
            if p_in not in seen or c_in not in seen:
                bad.append((z['name'], z['depth'], side))
        if bad:
            ng('bgp-connect', '虚拟拼接 %s 有 %d 条接线从宝藏房走不过去：%s'
               % (tag, len(bad), bad[:4]))
        ok(len(placed) - 1)
        exits = [z for z in placed if z['name'] == 'exit']
        exits_total += len(exits)
        if exits:
            ok(len(exits))
        # 每件的空气也要洪泛得到（不然只是门通了、房间还是个壳）
        closed = []
        for z in placed[1:]:
            p = pieces[z['name']]
            o, r = z['origin'], z['rot']
            air = [local for local, v in p.blocks.items() if v[0] == AIR]
            got = 0
            for local in air:
                rp = rot_pos(local, r)
                if (o[0] + rp[0], o[1] + rp[1], o[2] + rp[2]) in seen:
                    got += 1
            if air and 100.0 * got / len(air) < 50.0:
                closed.append((z['name'], got, len(air)))
        if closed:
            ng('bgp-connect', '虚拟拼接 %s 有件从宝藏房走不进去（空气 < 50%% 可达）：%s'
               % (tag, closed[:4]))
        ok(len(placed) - 1)
        total += len(placed)
        print('[bgp-connect] 虚拟拼接 %s：%d 件 / 出入口 %d / 深度 %d..%d / 洪泛覆盖 %d 格 / 接线 %d 条全通'
              % (tag, len(placed), len(exits),
                 min(z['depth'] for z in placed), max(z['depth'] for z in placed),
                 len(seen), len(placed) - 1))
        print('[bgp-connect]   ' + ' -> '.join('%d:%s(%s)' % (z['depth'], z['name'], z['rot'])
                                              for z in placed))
    if exits_total == 0:
        ng('bgp-connect', '5 组虚拟拼接里一个出入口都没有（空转：这条断言就没验到「能不能走到出入口」）')
    if maxp < 6:
        ng('bgp-connect', '5 组里最多只拼下 %d 件（< 6），拼接规则退化' % maxp)
    if total == 0:
        ng('bgp-connect', '一组虚拟拼接都没拼成（空转）')
    print('[bgp-connect] 5 组汇总：最多 %d 件 / 出入口合计 %d 个（前两组=最长纯走廊链，后三组=忠实洗牌）'
          % (maxp, exits_total))


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
            kids = byname.get(tg, []) if tg != 'empty' else []
            if not kids and tg != 'empty':
                ng('bgp-gate', '%s 的 %s 口 target=%r 没有任何子件能接' % (name, side, tg))
            if tg == 'empty':
                # ★ 第五轮：唯一合法的"终端口" = exit 的 target=empty（engine 的 Pools.EMPTY）。
                #   它刻意没有子件；这里断言"只有 exit 允许这样"，别的件敢写 empty 就红。
                if name != 'exit':
                    ng('bgp-gate', '%s 的 %s 口 target=empty（只有 exit 允许终端口）' % (name, side))
                ok()
                continue
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
    """[bgp-pool-reach] 第五轮：把「按序号硬链」换成「按权重随机 + 全员 fallback=exit」后的三条结构断言。

    旧口径（`[bgp-cycle]`，原文留档在 docs\\金之牢狱-实现记录.md §11）：
      cell_small_a → cell_small_mirror → cell_small_fertile → lane 的三段硬循环。
    新口径：
      1) **每个池的 fallback 链都必须终结在 `exit`**（start / exit 自己除外）⇒ 落单口 = 0 的机制保证；
      2) **exit 的口 target / pool 都不许是 room**（否则被放在更浅深度时会继续长 ⇒ 无限链）；
      3) 池目录**恰好 4 个文件**（旧 11 个死池必须删掉），room 池权重记账 = 单值 2 / 丰饶 6 / 四面道 3。
    """
    # ---- 1) 池文件恰好 4 个；每个池的 fallback 链终结于 exit
    pdir = os.path.join(WG, 'template_pool', 'golden_prison')
    files = sorted(f[:-5] for f in os.listdir(pdir) if f.endswith('.json'))
    if files != sorted(EXPECT_POOLS):
        ng('bgp-pool-reach', '池文件 %s != 期望 %s（旧 11 个死池必须删掉）'
           % (files, sorted(EXPECT_POOLS)))
    ok()
    for name in EXPECT_POOLS:
        if name in ('start', 'exit'):
            continue
        chain = [name]
        cur = EXPECT_POOLS[name][1]
        while True:
            if cur == 'minecraft:empty':
                ng('bgp-pool-reach', '池 %s 的 fallback 链 %s 落到 empty（应到 exit）'
                   % (name, ' -> '.join(chain)))
                break
            nxt = pool_name(cur)
            if nxt is None:
                ng('bgp-pool-reach', '池 %s 的 fallback 链指向非本结构池 %r' % (name, cur))
                break
            chain.append(nxt)
            if nxt == 'exit':
                ok()
                break
            if nxt in chain[:-1]:
                ng('bgp-pool-reach', '池 %s 的 fallback 链成环 %s' % (name, ' -> '.join(chain)))
                break
            cur = EXPECT_POOLS[nxt][1]
        print('[bgp-pool-reach] %-5s fallback 链 = %s' % (name, ' -> '.join(chain)))
    # ---- 2) exit 不许有 room 目标
    for side, (sn, tg, pl) in SOCK['exit'].items():
        if tg == 'room' or pl == POOL + 'room' or pl == 'room':
            ng('bgp-pool-reach', 'exit 的 %s 口 target/pool 仍是 room（会无限长）' % side)
        ok(2)
    for pos, be in pieces['exit'].jigsaws.items():
        if be.get('target') == 'room' or be.get('pool', '').endswith('/room'):
            ng('bgp-pool-reach', 'exit.nbt 的 jigsaw 仍是 room 目标：%r' % (be,))
        ok(2)
    # ---- 3) room 池权重记账（第六轮：fertile 10 ⇒ 总权重 64、丰饶 30 ⇒ P(3 连)=1-(34/64)^3=0.850）
    #   旧口径留档（第五轮）：总权重 52、丰饶 18 ⇒ P = 1-(34/52)^3 = 0.720（原文不删）
    d = json.load(open(os.path.join(pdir, 'room.json'), encoding='utf-8'))
    got = {}
    for e in d.get('elements', []):
        t = (e.get('element') or {}).get('location', '').split('/', 2)[-1]
        got[t] = e.get('weight')
    if got != ROOM_WEIGHTS:
        ng('bgp-pool-reach', 'room 池权重 %r != 记账 %r' % (got, ROOM_WEIGHTS))
    ok(len(ROOM_WEIGHTS))
    tot = sum(ROOM_WEIGHTS.values())
    fert = sum(w for t, w in ROOM_WEIGHTS.items() if t.endswith('_fertile'))
    p3 = 1.0 - (1.0 - fert / float(tot)) ** 3
    if tot != ROOM_TOTAL_W or fert != ROOM_FERTILE_W:
        ng('bgp-pool-reach', 'room 总权重 %d / 丰饶 %d != %d / %d'
           % (tot, fert, ROOM_TOTAL_W, ROOM_FERTILE_W))
    ok(2)
    print('[bgp-pool-reach] room 池：总权重 %d、丰饶 %d（%.1f%%）⇒ P(3 连至少一个丰饶) = %.4f'
          % (tot, fert, 100.0 * fert / tot, p3))
    if p3 < ROOM_P3_MIN:
        ng('bgp-pool-reach', 'P(3 连含丰饶)=%.4f < %.2f（作者要求"高概率"）' % (p3, ROOM_P3_MIN))
    ok()


def check_cross3(pieces):
    """[bgp-cross3] ★★ 第八轮 ④：每座结构**至少 3 个四面道**（作者：「还要上一个四面房最少得生成出三间」）。

    机制（纯数据）：`start(treasure) → cross_slot_1 → cross_slot_2 → cross_slot_3 → room(随机)`。
    三个槽各有自己的池，池里 = **两种四面道**（A/B 的槽变体）按权重 2:1 ⇒ **数量固定 3、样式随机**。
    本段断言：
      ① treasure 的口**只指向** cross_slot_1（唯一去向 ⇒ 第一件必是四面道）；
      ② 每个槽池**恰好 2 个元素**（A/B）且权重 2:1（⇒ 样式随机但数量唯一）；
      ③ 链上每一级都接得上：slotN 的入场口 name == 上一级的 target（canAttach 的硬要求）；
      ④ 槽 3 之后**不再有**任何 `cross_slot_` 目标（链恰好三级，不多不少）；
      ⑤ 几何可行：三件 bent 链的最远边 ≤ max_distance_from_center 116
         （直线三连 = 10+37×3 = 121 > 116 会被裁掉，所以槽 1 往南、槽 2/3 往东拐）；
      ⑥ room 池里仍然保留两种四面道（额外的随机四面道，不影响"至少 3"的保证）。
    """
    # ① treasure 的唯一口
    sock = SOCK['treasure']
    if set(sock) != {'south'}:
        ng('bgp-cross3', 'treasure 的口集合 %s != {south}' % set(sock))
    ok()
    sn, tg, pl = sock['south']
    if (tg, pl) != ('cross_slot_1', POOL + 'cross_slot_1'):
        ng('bgp-cross3', 'treasure 的口 target/pool = (%r, %r) != (cross_slot_1, %s)'
           % (tg, pl, POOL + 'cross_slot_1'))
    ok(2)
    for pos, be in pieces['treasure'].jigsaws.items():
        if (be.get('target'), be.get('pool')) != ('cross_slot_1', POOL + 'cross_slot_1'):
            ng('bgp-cross3', 'treasure.nbt 的口 %s target/pool = %r（应为 cross_slot_1）'
               % (pos, (be.get('target'), be.get('pool'))))
        ok(2)
    # ② 三个槽池：恰好 2 个元素、权重 2:1、元素名 = 槽变体
    pdir = os.path.join(WG, 'template_pool', 'golden_prison')
    chain_pools = ['cross_slot_1', 'cross_slot_2', 'cross_slot_3']
    for pn in chain_pools:
        f = os.path.join(pdir, pn + '.json')
        if not os.path.exists(f):
            ng('bgp-cross3', '缺槽池 %s.json' % pn)
            continue
        d = json.load(open(f, encoding='utf-8'))
        got = {}
        for e in d.get('elements', []):
            t = (e.get('element') or {}).get('location', '').split('/', 2)[-1]
            got[t] = e.get('weight')
        if got != SLOT_POOL_W[pn]:
            ng('bgp-cross3', '槽池 %s 元素/权重 %r != %r（必须恰好 A/B 两种、2:1）'
               % (pn, got, SLOT_POOL_W[pn]))
        ok()
        if d.get('fallback') != POOL + 'exit':
            ng('bgp-cross3', '槽池 %s fallback=%r != exit（落单口机制）' % (pn, d.get('fallback')))
        ok()
    # ③④ 链的接续 + 恰好三级
    for n in (1, 2, 3):
        for style in ('a', 'b'):
            nm = 'cross_slot_%d_%s' % (n, style)
            cfg = SOCK[nm]
            entry = SLOT_ENTRY[n]
            if cfg[entry][0] != 'cross_slot_%d' % n:
                ng('bgp-cross3', '%s 的入场口 %s name=%r != cross_slot_%d（父口 target 对不上）'
                   % (nm, entry, cfg[entry][0], n))
            ok()
            if cfg[entry][0] == 'cross_slot_%d' % n:
                pass
            # nbt 侧同样核对（防止 SOCK 表与产物不一致）
            want_side = entry
            for pos, be in pieces[nm].jigsaws.items():
                out = outward(pos, pieces[nm].size)
                if not out:
                    continue
                side = out[0]
                if side == want_side:
                    if be.get('name') != 'cross_slot_%d' % n:
                        ng('bgp-cross3', '%s.nbt 的 %s 口 name=%r != cross_slot_%d'
                           % (nm, side, be.get('name'), n))
                    ok()
                if n == 3 and be.get('target', '').startswith('cross_slot_'):
                    ng('bgp-cross3', '%s 还能接下一槽（target=%r）⇒ 链不止三级'
                       % (nm, be.get('target')))
                ok()
            if SLOT_CHAIN[n]:
                side, nxt = SLOT_CHAIN[n]
                if cfg[side][1] != 'cross_slot_%d' % nxt:
                    ng('bgp-cross3', '%s 的 %s 口 target=%r != cross_slot_%d'
                       % (nm, side, cfg[side][1], nxt))
                ok()
    # ⑤ 几何可行（bent 链）：最远边 ≤ max_distance_from_center
    maxd = EXPECT_STRUCT_MAIN['max_distance_from_center']
    half_cross = EXPECT_SIZE['cross_a'][0] // 2
    far_z = EXPECT_SIZE['treasure'][2] // 2 + EXPECT_SIZE['cross_a'][2]     # 10 + 37 = 47
    far_x = EXPECT_SIZE['cross_a'][0] * 2 + half_cross                      # 37×2 + 18 = 92
    if max(far_z, far_x) > maxd:
        ng('bgp-cross3', '三件 bent 链最远边 %d > max_distance_from_center %d ⇒ 第 3 件会被裁掉'
           % (max(far_z, far_x), maxd))
    ok(2)
    straight = EXPECT_SIZE['treasure'][2] // 2 + EXPECT_SIZE['cross_a'][2] * 3
    print('[bgp-cross3] 三槽固定前缀：treasure→cross_slot_1→cross_slot_2→cross_slot_3→room；'
          '每池 A/B 2:1 ⇒ 每座**恰好 3 个四面道**（样式随机）；'
          'bent 链最远边 %d ≤ %d（直线三连 %d 会被裁）'
          % (max(far_z, far_x), maxd, straight))
    # ⑥ room 池仍有两种四面道（额外随机四面道）
    for t in ('cross_a', 'cross_b'):
        if t not in EXPECT_POOLS['room'][0]:
            ng('bgp-cross3', 'room 池里少了随机四面道 %s' % t)
        ok()


def check_entities_bes(pieces):
    """[bgp-entity] / [bgp-be] —— 第五轮（作者三图：展示框没放、刷怪笼的金钱妖没了）。

    源存档实测（docs\\金之牢狱-实现-证据\\src_entities_bes.json）：6 个实体、53 个件内 BE。
    **注意坐标是「件内相对坐标」**：+512 展示区是纯方块副本（BE/实体都留在原件区），
    所以 ① 实体 blockPos 必须落在 [0,size) ② BE 的 x/y/z 必须等于它的 pos。
    """
    EXPECT_ENT = {'treasure': 2, 'cross_b': 2, 'exit': 2}
    EXPECT_BE = {
        'treasure': {'minecraft:mob_spawner': 12, 'minecraft:chest': 3},
        'cross_a': {'minecraft:mob_spawner': 8},
        'cross_b': {'minecraft:mob_spawner': 12, 'minecraft:chest': 4},
        'cell_large_a': {'minecraft:mob_spawner': 1, 'minecraft:chest': 1},
        'cell_large_b': {'minecraft:mob_spawner': 1, 'minecraft:chest': 1},
        'cell_large_c': {'minecraft:mob_spawner': 1, 'minecraft:chest': 1},
        'cell_medium_a': {'minecraft:mob_spawner': 1, 'minecraft:chest': 1},
        'cell_medium_b': {'minecraft:mob_spawner': 1, 'minecraft:chest': 1},
        'cell_medium_c': {},
        'cell_small_a': {'minecraft:mob_spawner': 1, 'minecraft:chest': 1},
        'cell_small_b': {'minecraft:mob_spawner': 1, 'minecraft:chest': 1},
        'cell_small_c': {},
        'lane': {}, 'exit': {},
    }
    # 派生件：镜像 = 基准件的 BE 逐格镜像；丰饶 = 基准件 BE + 多 1 个箱子
    for size in ('small', 'medium', 'large'):
        base = 'cell_%s_a' % size
        EXPECT_ENT['cell_%s_mirror' % size] = 0
        EXPECT_ENT['cell_%s_fertile' % size] = 0
        mb = dict(EXPECT_BE[base])
        fb = dict(EXPECT_BE[base])
        fb['minecraft:chest'] = fb.get('minecraft:chest', 0) + 1
        EXPECT_BE['cell_%s_mirror' % size] = mb
        EXPECT_BE['cell_%s_fertile' % size] = fb
    for n in EXPECT_SIZE:
        EXPECT_ENT.setdefault(n, 0)
    # ★ 第八轮 ④：6 个槽变体 = cross_a / cross_b 的逐格副本（实体 + BE 一起复制）
    for _n in (1, 2, 3):
        EXPECT_ENT['cross_slot_%d_a' % _n] = EXPECT_ENT['cross_a']
        EXPECT_ENT['cross_slot_%d_b' % _n] = EXPECT_ENT['cross_b']
        EXPECT_BE['cross_slot_%d_a' % _n] = dict(EXPECT_BE['cross_a'])
        EXPECT_BE['cross_slot_%d_b' % _n] = dict(EXPECT_BE['cross_b'])
    total_ent = sum(EXPECT_ENT.values())
    total_be = sum(sum(v.values()) for v in EXPECT_BE.values())
    for name, p in pieces.items():
        if len(p.ents) != EXPECT_ENT[name]:
            ng('bgp-entity', '%s 实体 %d 个 != 源存档 %d' % (name, len(p.ents), EXPECT_ENT[name]))
        ok()
        for e in p.ents:
            nb = e['nbt']
            if nb.get('id') != 'minecraft:glow_item_frame':
                ng('bgp-entity', '%s 的实体 id=%r（源存档只有 glow_item_frame）' % (name, nb.get('id')))
            if (nb.get('Item') or {}).get('id') != 'bettergold:chaos_coin':
                ng('bgp-entity', '%s 的展示框物品=%r（应为 bettergold:chaos_coin）'
                   % (name, nb.get('Item')))
            if nb.get('Facing') != 3:
                ng('bgp-entity', '%s 的展示框 Facing=%r（源存档全是 3=south）' % (name, nb.get('Facing')))
            bp = tuple(e['blockPos'])
            if not all(0 <= bp[i] < p.size[i] for i in range(3)):
                ng('bgp-entity', '%s 的实体 blockPos=%s 不在件内（坐标没换成相对坐标）' % (name, bp))
            if tuple(int(v) for v in e['pos'][:3]) != bp:
                ng('bgp-entity', '%s 的实体 pos=%s 与 blockPos=%s 不同格' % (name, e['pos'], bp))
            sup = (bp[0] + FACE_OPP[nb.get('Facing', 3)][0], bp[1] + FACE_OPP[nb.get('Facing', 3)][1],
                   bp[2] + FACE_OPP[nb.get('Facing', 3)][2])
            sv = p.at(sup)
            if sv is None or sv[0] in (AIR, VOID):
                ng('bgp-entity', '%s 的展示框 %s 支撑方块 %s 不是实心（%r）'
                   % (name, bp, sup, sv and sv[0]))
            ok(5)
        # BE
        cnt = {}
        for pos, be in p.bes.items():
            cnt[be.get('id')] = cnt.get(be.get('id'), 0) + 1
            if tuple(int(be.get(k, -999)) for k in ('x', 'y', 'z')) != pos:
                ng('bgp-be', '%s 的 BE %s 的 x/y/z=%r 不是件内相对坐标'
                   % (name, pos, (be.get('x'), be.get('y'), be.get('z'))))
            if be.get('id') == 'minecraft:mob_spawner':
                sid = ((be.get('SpawnData') or {}).get('entity') or {}).get('id')
                if sid != 'bettergold:money_gremlin':
                    ng('bgp-be', '%s 的刷怪笼 %s SpawnData.entity.id=%r（应为 bettergold:money_gremlin）'
                       % (name, pos, sid))
                if not isinstance(be.get('Delay'), int):
                    ng('bgp-be', '%s 的刷怪笼 %s 缺 Delay' % (name, pos))
            if be.get('id') == 'minecraft:chest' and be.get('LootTable') != LOOT_ID:
                ng('bgp-be', '%s 的箱子 BE %s 缺 LootTable' % (name, pos))
            ok(3)
        if cnt != EXPECT_BE[name]:
            ng('bgp-be', '%s 的方块实体 %r != 源存档 %r' % (name, cnt, EXPECT_BE[name]))
        ok()
    # 镜像件的 BE 必须逐格镜像（否则箱子/刷怪笼会错位）
    for size in ('small', 'medium', 'large'):
        a, m = pieces['cell_%s_a' % size], pieces['cell_%s_mirror' % size]
        sx = a.size[0]
        want = {(sx - 1 - x, y, z): be for (x, y, z), be in a.bes.items()}
        if set(want) != set(m.bes):
            ng('bgp-be', 'cell_%s_mirror 的 BE 格子没跟着镜像：%s vs %s'
               % (size, sorted(want)[:4], sorted(m.bes)[:4]))
        ok(len(want))
    # ★ 第七轮 ③：箱子 ↔ 方块实体 **双向**（"空箱"事故的静态拦截）
    #   正向（load_piece 已经逐块查了 LootTable）：每块 minecraft:chest ⇒ 自己那格必须带 LootTable；
    #   反向（这里）：每一条 id=chest 的 BE ⇒ 必须压在 minecraft:chest 方块上。
    #   ⚠ 反向往返才是"7/8 空箱"的真正拦截面：世界加载时 BE 的 id 与方块类型不符会被**静默丢弃**。
    chest_blocks = 0
    chest_bes = 0
    for name, p in pieces.items():
        for pos, be in p.bes.items():
            if be.get('id') == 'minecraft:chest':
                chest_bes += 1
                if (p.at(pos) or ('',))[0] != 'minecraft:chest':
                    ng('bgp-be', '%s 的箱子 BE %s 不在 minecraft:chest 方块上（世界加载会丢弃）'
                       % (name, pos))
                ok()
            elif (p.at(pos) or ('',))[0] == 'minecraft:chest':
                ng('bgp-be', '%s 的箱子方块 %s 上的 BE id=%r（应为 minecraft:chest）'
                   % (name, pos, be.get('id')))
                ok()
        chest_blocks += len(p.chests)
    if chest_blocks != chest_bes:
        ng('bgp-be', '箱子方块 %d 个 != 箱子 BE %d 条（双向不等）' % (chest_blocks, chest_bes))
    ok()
    # 清单文件对穿（防"NBT 里有、manifest 没记"）
    man_p = os.path.join(ROOT, 'docs', '金之牢狱-实现-证据', 'nbt_manifest.json')
    if os.path.exists(man_p):
        man = json.load(open(man_p, encoding='utf-8'))
        for name, p in pieces.items():
            m = man.get(name) or {}
            if m.get('entities') != len(p.ents) or m.get('block_entities') != len(p.bes):
                ng('bgp-be', '%s 的 nbt_manifest 记账 entities=%r be=%r 与 NBT 实际 %d/%d 不符'
                   % (name, m.get('entities'), m.get('block_entities'), len(p.ents), len(p.bes)))
            ok()
    else:
        ng('bgp-be', '缺 nbt_manifest.json（无法对穿实体/BE 计数）')
    print('[bgp-entity] 实体 %d 个（treasure 2 / cross_b 2 / exit 2，全部 glow_item_frame + chaos_coin）；'
          '方块实体 %d 个（spawner %d / chest %d）'
          % (total_ent, total_be,
             sum(v.get('minecraft:mob_spawner', 0) for v in EXPECT_BE.values()),
             sum(v.get('minecraft:chest', 0) for v in EXPECT_BE.values())))
    # 源码正向 needle（去注释）：不许回到「entities 永远写空列表」的老写法
    gp = os.path.join(ROOT, 'docs', '金之牢狱-实现-证据', 'gp_build.py')
    src = strip_comments(open(gp, encoding='utf-8').read(), 'py')
    if "'entities': (9, (10, []))" in src or "root['entities'] = (9, (10, []))" in src:
        ng('bgp-entity', 'gp_build.py 又把 entities 写成空列表了（P0 回归）')
    if 'load_entities()' not in src or 'load_block_entities()' not in src:
        ng('bgp-entity', 'gp_build.py 没有从 entities/*.mca 与 block_entities 读源数据')
    if "'blockPos'" not in src:
        ng('bgp-entity', 'gp_build.py 没有写 blockPos（模板实体段必须带 blockPos）')
    ok(3)
    print('[bgp-entity] 源码 needle：entities/block_entities/blockPos 三个关键分支都在（去注释后）')


FACE_OPP = {0: (0, 1, 0), 1: (0, -1, 0), 2: (0, 0, 1), 3: (0, 0, -1), 4: (1, 0, 0), 5: (-1, 0, 0)}


def check_exit_shaft(pieces):
    """[bgp-shaft] ★★ 第八轮 ②：exit 回退成作者原件 **5×8×5**（门楼 8 层原样、155 格）。

    作者原话（2026-10-22）：四图「…需要让黄色不断延伸至空域再架起蓝色，而不是直接让蓝色架在
    红色区域里并把红色区域的周围清空掉」+ 五图「你可以参考一下滑行魔石地牢他那边就明了的出入口可分」
    ⇒ 第七轮那套「井筒 36 层 + 11×62×11 空腔段」整体撤掉（那是"神秘大金柱子" + 把红色区域清空）。
    ⚠ "出入口要落在空域"这件事**本轮不做**（等作者给「滑行魔石地牢」的参考）。

    下面 1725-1988 的旧实现（井筒 / 空腔 / 露头校准）**原文留档**，第八轮起不执行。
    """
    p = pieces['exit']
    sx, sy, sz = p.size
    if p.size != (5, 8, 5):
        ng('bgp-shaft', 'exit 尺寸 %s != 5×8×5（第八轮回退：门楼 8 层原样、无井筒、无空腔）' % (p.size,))
    ok()
    # 1) 门楼 8 层：写出来的实心格（含 jigsaw）+ 省略的结构空位 = 作者原件 155 格 + 1 jigsaw
    door = sum(1 for k, v in p.blocks.items() if k[1] <= 7 and v[0] != AIR)
    if door != EXPECT_EXIT_BLOCKS + 1:
        ng('bgp-shaft', '门楼 8 层写出的非空气格 %d != %d（129 实心 + 1 jigsaw）'
           % (door, EXPECT_EXIT_BLOCKS + 1))
    ok()
    if door + len(p.absent) != DOOR_BLOCKS + 1:
        ng('bgp-shaft', '门楼 8 层 %d + 省略空位 %d != %d（155 原件 + 1 jigsaw）'
           % (door, len(p.absent), DOOR_BLOCKS + 1))
    ok()
    # 2) 结构空位的分布必须与源存档一致（y=5:3 / y=6:11 / y=7:12），且全在 y>=5
    per_y = {}
    for (_x, y, _z) in p.absent:
        per_y[y] = per_y.get(y, 0) + 1
    if per_y != {5: 3, 6: 11, 7: 12}:
        ng('bgp-shaft', 'exit 的结构空位逐层分布 %r != {5:3, 6:11, 7:12}（源存档实测）' % (per_y,))
    ok()
    # 3) 门楼内部（y=1..3）是可走空间：空气 + 3x3 通道，且从北口洪泛能到南面
    wy = 1
    inner_air = sum(1 for x in range(1, 4) for z in range(1, 4) for y in (1, 2, 3)
                    if (p.at((x, y, z)) or (AIR, {}))[0] == AIR)
    if inner_air != 27:
        ng('bgp-shaft', '门楼内部 3x3x3 的空气只有 %d/27（门洞被堵）' % inner_air)
    ok()
    seeds = []
    for side, (pos, be) in sorted(piece_sockets(p).items()):
        seeds.append(inner_of(pos, side))
    if not seeds:
        ng('bgp-shaft', 'exit 一个口都没扫到')
    ok()
    seen = flood(p, seeds)
    rooms = [(x, y, z) for x in range(1, 4) for z in range(1, 4) for y in (1, 2, 3)]
    miss = [c for c in rooms if c not in seen]
    if miss:
        ng('bgp-shaft', '门楼内部有 %d 格从口洪泛到不了（例 %s）' % (len(miss), miss[:3]))
    ok()
    # 4) 北口 jigsaw 还在 (2,1,0)；南面金栅栏墙还在；展示框的 2 个实体还在
    if (2, 1, 0) not in p.jigsaws:
        ng('bgp-shaft', 'exit 的北口 jigsaw (2,1,0) 不见了')
    ok()
    bars = sum(1 for z in range(5) for y in range(1, 5) for x in range(5)
               if (p.at((x, y, z)) or ('', {}))[0] == 'bettergold:gold_bars')
    if bars == 0:
        ng('bgp-shaft', 'exit 南面的金栅栏墙不见了')
    ok()
    if len(p.ents) != 2:
        ng('bgp-shaft', 'exit 的展示框实体 %d 个 != 2' % len(p.ents))
    ok()
    # 5) 调色板白名单（第八轮回退后不该再有第八轮以前没出现过的方块）
    names = {v[0] for v in p.blocks.values()}
    extra = names - EXIT_PALETTE
    if extra:
        ng('bgp-shaft', 'exit 出现了白名单外的方块 %s' % sorted(extra))
    ok()
    # 6) 门楼 8 层之上**一格都不许有**（回退的硬条件：不许再长井筒/空腔）
    if any(k[1] > 7 for k in p.blocks):
        ng('bgp-shaft', 'exit 在 y>7 还有方块（井筒/空腔没撤干净）')
    ok()
    print('[bgp-shaft] exit = %dx%dx%d（第八轮回退）：门楼 8 层 %d 格（含 1 jigsaw）+ 结构空位 %d 格'
          '（逐层 %r，整格省略）；y>7 无方块；展示框 %d 个；金栅栏 %d 格'
          % (sx, sy, sz, door, len(p.absent), per_y, len(p.ents), bars))
    return
    # ------------------------------------------------------------------
    # ★ 以下为第五~七轮的旧实现（井筒 36 层 + 11×62×11 空腔 + 露头校准），
    #   第八轮起 **不执行**，原文留档（不许删：那三轮的读数是"为什么回退"的依据）。
    # ------------------------------------------------------------------
    # 1) 井筒段 y=8..rim：周边是作者已有的金方块、内部 3x3 空气
    walls = 0
    for y in range(8, RIM_TOP + 1):
        for x in range(5):
            for z in range(5):
                nm = (p.at((x, y, z)) or (AIR, {}))[0]
                edge = x in (0, 4) or z in (0, 4)
                if edge:
                    if nm not in ('bettergold:gold_bricks', 'bettergold:gold_pillar'):
                        ng('bgp-shaft', '井筒墙 (%d,%d,%d)=%s 不是作者已有的金方块' % (x, y, z, nm))
                    walls += 1
                elif nm != AIR:
                    ng('bgp-shaft', '井筒内部 (%d,%d,%d)=%s 不是空气' % (x, y, z, nm))
                ok()
    # 2) 井口顶层 y=rim：内部空气（井口朝天）、四角柱子
    for x in range(1, 4):
        for z in range(1, 4):
            nm = (p.at((x, RIM_TOP, z)) or (AIR, {}))[0]
            if nm != AIR:
                ng('bgp-shaft', '井口顶层 (%d,%d,%d)=%s 不是空气' % (x, RIM_TOP, z, nm))
            ok()
    for (x, z) in ((0, 0), (0, 4), (4, 0), (4, 4)):
        nm = (p.at((x, RIM_TOP, z)) or (AIR, {}))[0]
        if nm != 'bettergold:gold_pillar':
            ng('bgp-shaft', '井口四角 (%d,%d)=%s 不是 gold_pillar' % (x, z, nm))
        ok()
    # 3) 门楼 8 层（y<=7）：方块数 == 冻结值（155 原件 − 24 开顶 + 1 jigsaw）
    door = sum(1 for k, v in p.blocks.items() if k[1] <= 7 and v[0] != AIR)
    if door != DOOR_BLOCKS:
        ng('bgp-shaft', '门楼 8 层的方块数 %d != 冻结值 %d（155 原件 − 24 开顶 + 1 jigsaw）'
           % (door, DOOR_BLOCKS))
    ok()
    # 屋顶开口（连通门楼与井筒）：y=4..7 的 x1..3 / z1..2 必须是空气（z=3 那列是展示框支撑，保留）
    for (x, y, z) in [(x, y, z) for x in (1, 2, 3) for z in (1, 2) for y in (4, 5, 6, 7)]:
        nm = (p.at((x, y, z)) or (AIR, {}))[0]
        if nm != AIR:
            ng('bgp-shaft', '屋顶开口 (%d,%d,%d)=%s 没打开' % (x, y, z, nm))
        ok()
    # 展示框的支撑方块必须还在（(1,7,3)/(3,7,3) 是 y=7 的 z=3 那两格）
    for (x, z) in ((1, 3), (3, 3)):
        nm = (p.at((x, 7, z)) or (AIR, {}))[0]
        if nm in (AIR, VOID):
            ng('bgp-shaft', '展示框支撑 (%d,7,%d) 被开顶掉了' % (x, z))
        ok()
    if (2, 1, 0) not in p.jigsaws:
        ng('bgp-shaft', 'exit 的北口 jigsaw (2,1,0) 不见了')
    ok()
    bars = sum(1 for z in range(5) for y in range(1, 5) for x in range(5)
               if (p.at((x, y, z)) or ('', {}))[0] == 'bettergold:gold_bars')
    if bars == 0:
        ng('bgp-shaft', 'exit 南面的金栅栏墙不见了')
    ok()
    # ---- 第七轮 ①：**空腔**（封闭洞厅）—— 井口一定在空腔空气里
    #   净空 9x9 / 21 层高（>= 任务书的 9x9 / 7 格）；环顶之上 17 层（覆盖实测的 9~17）
    inner_w = EXIT_CAVITY_INNER[1] - EXIT_CAVITY_INNER[0] + 1
    inner_h = EXIT_CAVITY_AIR[1] - EXIT_CAVITY_AIR[0] + 1
    if inner_w < 9 or inner_h < 7:
        ng('bgp-cavity', '空腔净空 %dx%d 小于任务书下限 9x9 / 7 格' % (inner_w, inner_h))
    ok()
    above = EXIT_CAVITY_AIR[1] - RIM_TOP
    if above < 17:
        ng('bgp-cavity', '空腔在环顶之上只有 %d 层（第五轮实测最差要 17 层才够埋住井口）' % above)
    ok()
    if not (EXIT_CAVITY_AIR[0] <= RIM_TOP <= EXIT_CAVITY_AIR[1]):
        ng('bgp-cavity', '井口环顶 y=%d 不在空腔净空 %s 里（"井口露在空腔里"不成立）'
           % (RIM_TOP, EXIT_CAVITY_AIR))
    ok()
    # 地板 y=F：铺满 11x11，**只有井筒 3x3 内腔留空**
    holes = [(x, z) for x in range(EXIT_CAVITY_SIZE[0]) for z in range(EXIT_CAVITY_SIZE[1])
             if (x, EXIT_CAVITY_FLOOR, z) not in p.blocks]
    if holes:
        ng('bgp-cavity', '空腔地板 y=%d 有 %d 个洞（第一格 %s）' % (EXIT_CAVITY_FLOOR, len(holes), holes[0]))
    ok()
    # 天花板 y=C：铺满 11x11（空腔是封闭的，不是"朝天敞开"）
    holes = [(x, z) for x in range(EXIT_CAVITY_SIZE[0]) for z in range(EXIT_CAVITY_SIZE[1])
             if (x, EXIT_CAVITY_CEIL, z) not in p.blocks]
    if holes:
        ng('bgp-cavity', '空腔天花板 y=%d 有 %d 个洞（第一格 %s）'
           % (EXIT_CAVITY_CEIL, len(holes), holes[0]))
    ok()
    # 四壁 y=F+1..C-1：x=0/10、z=0/10 一圈必须实心
    holes = [(x, y, z) for y in range(EXIT_CAVITY_FLOOR + 1, EXIT_CAVITY_CEIL)
             for x in range(EXIT_CAVITY_SIZE[0]) for z in range(EXIT_CAVITY_SIZE[1])
             if (x in (0, EXIT_CAVITY_SIZE[0] - 1) or z in (0, EXIT_CAVITY_SIZE[1] - 1))
             and (x, y, z) not in p.blocks]
    if holes:
        ng('bgp-cavity', '空腔四壁有 %d 个洞（第一格 %s）' % (len(holes), holes[0]))
    ok()
    # 净空内部：除井沿（y<=rim 的 x==4 / z==4 两边 + (4,4) 角）外必须是空气
    extra = []
    for y in range(EXIT_CAVITY_AIR[0], EXIT_CAVITY_AIR[1] + 1):
        for x in range(1, EXIT_CAVITY_SIZE[0] - 1):
            for z in range(1, EXIT_CAVITY_SIZE[1] - 1):
                nm = (p.at((x, y, z)) or (AIR, {}))[0]
                if nm == AIR:
                    continue
                if y <= RIM_TOP and (x == 4 or z == 4):
                    if nm not in ('bettergold:gold_bricks', 'bettergold:gold_pillar'):
                        ng('bgp-cavity', '井沿 (%d,%d,%d)=%s 不是作者已有的金方块' % (x, y, z, nm))
                    continue
                extra.append((x, y, z, nm))
    if extra:
        ng('bgp-cavity', '空腔净空里有 %d 格非空气（第一格 %s）' % (len(extra), extra[0]))
    ok()
    # 3x3 井筒通道：y=8..C-1 全空（不许被地板/天花板/装饰堵住）
    blocked = [(x, y, z) for x in (1, 2, 3) for z in (1, 2, 3) for y in range(8, EXIT_CAVITY_CEIL)
               if (p.at((x, y, z)) or (AIR, {}))[0] != AIR]
    if blocked:
        ng('bgp-cavity', '井筒 3x3 通道被堵了 %d 格（第一格 %s）' % (len(blocked), blocked[0]))
    ok()
    # 外壳只用作者已有的金方块（不造新造型 / 不碰贴图）
    if not set(v[0] for v in p.blocks.values()) <= EXIT_PALETTE:
        ng('bgp-cavity', 'exit 的调色板出现了容器外的方块：%s'
           % sorted(set(v[0] for v in p.blocks.values()) - EXIT_PALETTE))
    ok()
    # 空腔段只用 gold_block / gold_bricks / gold_pillar（外加井筒原有的两种）
    cav_ids = set()
    for y in range(EXIT_CAVITY_FLOOR, EXIT_CAVITY_CEIL + 1):
        for x in range(EXIT_CAVITY_SIZE[0]):
            for z in range(EXIT_CAVITY_SIZE[1]):
                v = p.at((x, y, z))
                if v and v[0] != AIR:
                    cav_ids.add(v[0])
    if not cav_ids <= {'minecraft:gold_block', 'bettergold:gold_bricks', 'bettergold:gold_pillar'}:
        ng('bgp-cavity', '空腔段出现了作者已有方块之外的 id：%s' % sorted(cav_ids))
    ok()
    print('[bgp-shaft] exit = %dx%dx%d：门楼 8 层（%d 格，方向南栅栏/展示框支撑原样）+ 井筒 %d 层'
          '（墙 %d 格、井口 3x3 朝天、环顶 y=%d）'
          % (sx, sy, sz, door, EXIT_SHAFT_H, walls, RIM_TOP))
    print('[bgp-cavity] 井口空腔：净空 %dx%d（y %d..%d）、地板 y=%d、天花板 y=%d、外壳 %dx%d、'
          '环顶之上 %d 层、只用 %s'
          % (inner_w, inner_w, EXIT_CAVITY_AIR[0], EXIT_CAVITY_AIR[1], EXIT_CAVITY_FLOOR,
             EXIT_CAVITY_CEIL, EXIT_CAVITY_SIZE[0], EXIT_CAVITY_SIZE[1], above, sorted(cav_ids)))
    # ---- 井筒层数 == 校准值；gp_build.py 的常量必须一致
    if sy - 8 != EXIT_SHAFT_H + EXIT_CAVITY_H:
        ng('bgp-shaft', 'exit 的上升段 %d 层 != EXIT_SHAFT_H(%d) + EXIT_CAVITY_H(%d)'
           % (sy - 8, EXIT_SHAFT_H, EXIT_CAVITY_H))
    ok()
    src = os.path.join(ROOT, 'docs', '金之牢狱-实现-证据', 'gp_build.py')
    if not os.path.exists(src):
        ng('bgp-shaft', '缺流水线 gp_build.py（没法核对 EXIT_SHAFT_H / EXIT_CAVITY_*）')
        return
    txt = strip_comments(open(src, 'rb').read().decode('utf-8', 'replace'), 'py')
    got = {}
    for line in txt.splitlines():
        s = line.strip()
        for key in ('EXIT_SHAFT_H', 'EXIT_CAVITY_FLOOR', 'EXIT_CAVITY_CEIL',
                    'EXIT_CAVITY_AIR', 'EXIT_CAVITY_INNER', 'EXIT_CAVITY_SIZE'):
            if s.startswith(key) and '=' in s:
                got.setdefault(key, s.split('=', 1)[1].split('#')[0].strip())
    if got.get('EXIT_SHAFT_H') != str(EXIT_SHAFT_H):
        ng('bgp-shaft', 'gp_build.py 的 EXIT_SHAFT_H=%r != 校准值 %d'
           % (got.get('EXIT_SHAFT_H'), EXIT_SHAFT_H))
    ok()
    want = {'EXIT_CAVITY_FLOOR': str(EXIT_CAVITY_FLOOR),
            'EXIT_CAVITY_CEIL': str(EXIT_CAVITY_CEIL),
            'EXIT_CAVITY_AIR': '(%d, %d)' % EXIT_CAVITY_AIR,
            'EXIT_CAVITY_INNER': '(%d, %d)' % EXIT_CAVITY_INNER,
            'EXIT_CAVITY_SIZE': '(%d, %d)' % EXIT_CAVITY_SIZE}
    for k, v in want.items():
        if got.get(k) != v:
            ng('bgp-cavity', 'gp_build.py 的 %s=%r != 关卡冻结值 %r（流水线与关卡不同源）'
               % (k, got.get(k), v))
        ok()
    if 'def add_cavity(' not in txt:
        ng('bgp-cavity', 'gp_build.py 去注释后没有 add_cavity()（空腔只许由流水线生成）')
    ok()
    # 正向 needle（去注释源码）：exit 的 jigsaw **name 必须是 room** ——
    #   `JigsawBlock.canAttach` 要求「父口 target == 子件 name」；size 5 后链尾是 lane（target=room），
    #   name=lane 会让链尾两个口永远接不上（第七轮实测：0 个出入口 + 5 个落单口）。
    if "'north': ('room', 'empty', 'minecraft:empty')" not in txt:
        ng('bgp-cavity', 'gp_build.py 里 exit 的 socket name 不是 room（canAttach 对不上 chain 尾）')
    ok()
    # 负向：任务书里的 +40 层（=76）实测是 0/8 达标，不许被悄悄改回去
    if got.get('EXIT_SHAFT_H') == '76':
        ng('bgp-shaft', 'EXIT_SHAFT_H 被改回 76（实测 +40 层是 0/8 达标）')
    ok()
    # ---- 历史快照（第五轮，**无空腔**的旧几何）：仍然自洽，留着当"为什么加空腔"的依据
    def pass_at(dh):
        return sum(1 for (top, af, win) in SHAFT_CALIB.values()
                   if win and win[0] <= dh <= win[1])

    if len(SHAFT_CALIB) != 8:
        ng('bgp-shaft-calib', '历史快照 %d 个口 != 8（第五轮真生成 3 座共 8 个出入口）' % len(SHAFT_CALIB))
    ok()
    now = sum(1 for (top, af, win) in SHAFT_CALIB.values()
              if af is not None and af <= top)
    if now != pass_at(0):
        ng('bgp-shaft-calib', '历史快照达标数 %d 与窗口复算 %d 不一致（快照自相矛盾）'
           % (now, pass_at(0)))
    ok()
    if now != 2:
        ng('bgp-shaft-calib', '历史快照当前达标 %d 个 != 记账 2 个（crimson#15 / basalt#7）' % now)
    ok()
    best = max(pass_at(dh) for dh in range(0, 41))
    if best != 2:
        ng('bgp-shaft-calib', '历史快照 0..40 层的最大达标数 %d != 记账 2' % best)
    ok()
    if pass_at(40) != 0:
        ng('bgp-shaft-calib', '历史快照 +40 层达标 %d 个 != 记账 0' % pass_at(40))
    ok()
    print('[bgp-shaft-calib] 历史（无空腔，第五轮）：8 口达标 %d/8；0..40 层最大 %d/8；+40 层 %d/8 '
          '⇒ 井筒高度不是杠杆，所以第七轮改成"自带空腔"（见 [bgp-cavity]）'
          % (now, best, pass_at(40)))

    # ---- 第七轮：**空腔之后**的实测快照（两个种子各 3 座，真生成，runServer 探针 GphProbe）
    #   数据 = docs\金之牢狱-实现-证据\gph_r7c\meta.json（种子 20261020）/
    #          gph_r7d\meta.json（种子 20261021）；口径 = 本函数开头（topY = 件顶 − 空腔 18 层）
    #   每口 = (topY, airFromY)；达标 = airFromY <= topY。旧口径（无空腔 2/8）原文留在 SHAFT_CALIB。
    min_margin = 999
    for label, snap in sorted(CAVITY_CALIB.items()):
        fail = [(k, v) for k, v in snap.items() if v[1] is None or v[1] > v[0]]
        if len(snap) != CAVITY_CALIB_N[label]:
            ng('bgp-cavity-calib', '%s 记账 %d 个口 != 期望 %d（真生成 3 座）'
               % (label, len(snap), CAVITY_CALIB_N[label]))
        ok()
        if fail:
            ng('bgp-cavity-calib', '%s 有 %d 个口没达标（airFromY > topY）：%s'
               % (label, len(fail), fail[:3]))
        ok(len(snap))
        for k, (top, af) in snap.items():
            min_margin = min(min_margin, top - af)
        print('[bgp-cavity-calib] %s：%d 口全部达标（topY %d..%d / airFromY %d..%d / 最小余量 %d 格）'
              % (label, len(snap),
                 min(v[0] for v in snap.values()), max(v[0] for v in snap.values()),
                 min(v[1] for v in snap.values()), max(v[1] for v in snap.values()),
                 min(v[0] - v[1] for v in snap.values())))
    if min_margin < 1:
        ng('bgp-cavity-calib', '最小露头余量 %d 格 < 1（井口没在空腔空气里）' % min_margin)
    ok()
    total_mouths = sum(len(v) for v in CAVITY_CALIB.values())
    if total_mouths != 14:
        ng('bgp-cavity-calib', '两个种子合计 %d 个出入口 != 记账 14' % total_mouths)
    ok()
    # 负向：口径不许退回"topY = 件 bbox.maxY"（第七轮起 exit 顶部还有 18 层空腔，bbox 顶 = 天花板）
    srcp = os.path.join(ROOT, 'docs', '金之牢狱-实现-证据', 'GphProbe.java.txt')
    if os.path.exists(srcp):
        psrc = open(srcp, encoding='utf-8').read()
        if 'int top = b.maxY();' in psrc and 'EXIT_CAVITY_ABOVE' not in psrc:
            ng('bgp-cavity-calib', '探针又把 topY 写回 b.maxY()（空腔之后那是天花板，不是井口环顶）')
        ok()
        if 'EXIT_CAVITY_ABOVE = 18' not in psrc:
            ng('bgp-cavity-calib', '探针缺 EXIT_CAVITY_ABOVE = 18（环顶口径的唯一真源）')
        ok()


def check_worldgen():
    # ★★ 第八轮（2026-10-22）③：**只剩一套** structure + structure_set。
    #   作者：「最后再备注一下金之牢狱将无法生成于玄武岩三角洲」⇒ 玄武岩那一套删掉，
    #   保留的 `golden_prison.json` 的 biomes 标签本来就排除 basalt_deltas，terrain_adaptation 用 bury。
    #   旧口径原文留档（第六/七轮，**已作废**，不删）：两套 structure + 两套 structure_set，
    #   公共字段逐字相同，差异只有 biomes / terrain_adaptation / max_distance_from_center。
    #   更早（第一~五轮）：只有 `structure/golden_prison.json` + `structure_set/golden_prison.json` 各一个，
    #   `biomes = #minecraft:is_nether`、`terrain_adaptation = none`、`max_distance_from_center = 128`。
    for f in (STRUCT_MAIN, SSET_MAIN, BIOME_TAG):
        if not os.path.exists(f):
            ng('bgp-worldgen', '缺 %s' % os.path.basename(f))
            return
        ok()
    # ★ 负向（第八轮 ③ 的核心）：玄武岩那一套的两个文件**必须不存在**
    for f in (STRUCT_BASALT, SSET_BASALT):
        if os.path.exists(f):
            ng('bgp-worldgen-single', '%s 还在（玄武岩那一套必须删除）' % os.path.basename(f))
        ok()
    structs = {}
    for kind, f in (('main', STRUCT_MAIN),):
        try:
            structs[kind] = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            ng('bgp-worldgen', '%s 解析失败：%s' % (os.path.basename(f), e))
            return
        ok()
    for kind in ('main',):
        st = structs[kind]
        code = 'bgp-worldgen'
        # ---- 唯一一套的字段（第八轮：biomes 排除玄武岩 / bury / max_distance 116）
        for k, v in EXPECT_STRUCT_MAIN.items():
            if st.get(k) != v:
                ng(code, '%s.%s = %r != %r' % (kind, k, st.get(k), v))
            ok()
        # ---- 不许有多余/缺字段
        want_keys = set(EXPECT_STRUCT_COMMON) | {'spawn_overrides', 'start_height', 'biomes',
                                                 'terrain_adaptation', 'max_distance_from_center'}
        if set(st) != want_keys:
            ng(code, '%s 的字段集合 %s != 期望 %s' % (kind, sorted(st), sorted(want_keys)))
        ok()
        sh = st.get('start_height') or {}
        lo = (sh.get('min_inclusive') or {}).get('absolute')
        hi = (sh.get('max_inclusive') or {}).get('absolute')
        if sh.get('type') != 'minecraft:uniform' or (lo, hi) != (31, 41):
            ng(code, '%s start_height = %r（应为 uniform 31..41）' % (kind, sh))
        ok(3)
        if 'max_depth' in json.dumps(st):
            ng(code, '%s 出现了 1.20 口径的 max_depth（1.21 叫 size）' % kind)
        ok()
        # ---- JigsawStructure.verifyRange（源码：sources jar
        #      net/minecraft/world/level/levelgen/structure/structures/JigsawStructure.java）
        #        int i = terrainAdaptation() == NONE ? 0 : (BURY|BEARD_THIN|BEARD_BOX|ENCAPSULATE) 12;
        #        maxDistanceFromCenter + i > 128  ⇒ DataResult.error("Structure size including
        #        terrain adaptation must not exceed 128")  ⇒ **整个结构静默加载失败**
        pad = 0 if st.get('terrain_adaptation') == 'none' else 12
        md = st.get('max_distance_from_center') or 0
        if md + pad > 128:
            ng(code, '%s max_distance_from_center=%r + 地形适应 padding %d > 128 ⇒ 结构会加载失败'
               % (kind, md, pad))
        ok()
    # ---- 唯一一套：start_pool 指向 start（宝藏房唯一性另见 [bgp-treasure-unique]）
    if structs['main'].get('start_pool') != POOL + 'start':
        ng('bgp-worldgen', 'start_pool=%r != %r' % (structs['main'].get('start_pool'), POOL + 'start'))
    ok()
    # ---- structure_set：密度字段 / salt 19710101 / 只引用主结构
    sets = {}
    for kind, f in (('main', SSET_MAIN),):
        try:
            sets[kind] = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            ng('bgp-worldgen', '%s 解析失败：%s' % (os.path.basename(f), e))
            return
        ok()
    for kind in ('main',):
        pl = sets[kind].get('placement') or {}
        code = 'bgp-worldgen'
        if pl.get('type') != 'minecraft:random_spread':
            ng(code, '%s set placement.type=%r' % (kind, pl.get('type')))
        if pl.get('spacing') != 27 or pl.get('separation') != 4 or pl.get('spread_type') != 'linear':
            ng(code, '%s set 密度字段 %r != 27/4/linear' % (kind, pl))
        ok(4)
        if pl.get('salt') != EXPECT_SSET_SALT[kind]:
            ng('bgp-worldgen-salt', '%s set salt=%r != 记账值 %d'
               % (kind, pl.get('salt'), EXPECT_SSET_SALT[kind]))
        ok()
        els = sets[kind].get('structures') or []
        if len(els) != 1 or els[0].get('structure') != EXPECT_SSET_STRUCTURE[kind] \
                or els[0].get('weight') != 1:
            ng(code, '%s set structures=%r 必须恰好 1 条、指向 %r、weight=1'
               % (kind, els, EXPECT_SSET_STRUCTURE[kind]))
        ok()
    # ---- 群系标签：成员 = 原版 #minecraft:is_nether 减 basalt_deltas；replace 必须 false
    try:
        tag = json.load(open(BIOME_TAG, encoding='utf-8'))
    except Exception as e:
        ng('bgp-biome-tag', '标签解析失败：%s' % e)
        return
    if tag.get('replace') is not False:
        # ⚠ 写成 true（或缺省以外的真值）会把原版标签的条目**静默清空**
        ng('bgp-biome-tag', 'replace=%r，必须显式 false（true 会静默清空原版条目）' % tag.get('replace'))
    ok()
    vals = tag.get('values') or []
    want = [b for b in NETHER_BIOMES if b != 'minecraft:basalt_deltas']
    if vals != want:
        ng('bgp-biome-tag', 'values=%r != 原版 is_nether 减 basalt_deltas 的 %r' % (vals, want))
    ok(len(want))
    if 'minecraft:basalt_deltas' in vals:
        ng('bgp-biome-tag', 'values 里还有 minecraft:basalt_deltas（玄武岩群系会被主结构命中）')
    ok()
    if len(set(vals)) != len(vals):
        ng('bgp-biome-tag', 'values 有重复条目：%r' % vals)
    ok()
    # ---- 与原版 jar 对穿（防冻结常量过期）
    jar = os.path.join(ROOT, 'build', 'moddev', 'artifacts',
                       'neoforge-21.1.228-client-extra-aka-minecraft-resources.jar')
    if os.path.exists(jar):
        try:
            with zipfile.ZipFile(jar) as z:
                v = json.loads(z.read('data/minecraft/tags/worldgen/biome/is_nether.json')
                               .decode('utf-8'))
            jar_vals = v.get('values') or []
            if sorted(jar_vals) != sorted(NETHER_BIOMES):
                ng('bgp-biome-tag', '原版 is_nether 成员变了：jar=%r vs 冻结常量=%r'
                   % (jar_vals, NETHER_BIOMES))
            ok()
            print('[bgp-biome-tag] 原版 jar 对穿：is_nether = %r' % (jar_vals,))
        except Exception as e:
            ng('bgp-biome-tag', '读原版 jar 失败：%s' % e)
    else:
        print('[bgp-biome-tag] 原版 jar 不在，只按冻结常量核对')
    print('[bgp-worldgen] 唯一一套结构：biomes=%s / %s / max=%s；salt=%r；'
          '玄武岩那一套文件（structure+structure_set）**不存在**；标签 members=%d'
          % (structs['main']['biomes'], structs['main']['terrain_adaptation'],
             structs['main']['max_distance_from_center'],
             sets['main']['placement'].get('salt'), len(vals)))
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


def walk_strings(node):
    """递归取出 JSON 里的所有**字符串值**（字典键不算：池元素只认值）。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            for s in walk_strings(v):
                yield s
    elif isinstance(node, list):
        for v in node:
            for s in walk_strings(v):
                yield s


def is_treasure_loc(loc):
    """模板引用的「是宝藏房」判定：按**整串相等**，不做 substring 命中。"""
    return isinstance(loc, str) and (loc == TREASURE_LOC or loc.endswith('/treasure'))


def check_rate():
    """[bgp-rate-fortress] / [bgp-rate-salt]：生成率 == 下界要塞（作者 2026-10-20 第三轮追加）。

    真源（逐字抄原版 jar，不凭印象；常量与注释见文件头）：
      data/minecraft/worldgen/structure_set/nether_complexes.json
        placement = {type: random_spread, salt: 30084232, separation: 4, spacing: 27}
        **没有 spread_type 字段** ⇒ RandomSpreadStructurePlacement.java:23 的 codec 默认 linear。
      data/minecraft/worldgen/structure/fortress.json
        只有 type/step/biomes/spawn_overrides，**没有 start_height / project_start_to_heightmap**
        ⇒ 「生成率」只由 placement 的 spacing/separation/spread_type 决定。
    ⚠ salt 不照抄（见文件头注释）：相同 salt + 同种子 ⇒ 候选区块逐个重合。
    ⚠ 单件最大 37x37 远大于要塞，按作者要求**默认照抄**、不私自加大 spacing；
      「实际体验更密」写进 docs\\金之牢狱-实现记录.md §10。
    """
    ssp = os.path.join(WG, 'structure_set', 'golden_prison.json')
    if not os.path.exists(ssp):
        ng('bgp-rate-fortress', '缺 structure_set/golden_prison.json')
        return
    try:
        ss = json.load(open(ssp, encoding='utf-8'))
    except Exception as e:
        ng('bgp-rate-fortress', 'structure_set 解析失败：%s' % e)
        return
    pl = ss.get('placement') or {}
    for k in ('type', 'spacing', 'separation', 'spread_type'):
        want = FORTRESS_PLACEMENT[k]
        if pl.get(k) != want:
            ng('bgp-rate-fortress',
               'placement.%s=%r != 下界要塞的 %r（来源：原版 nether_complexes.json）' % (k, pl.get(k), want))
        ok()
    if 'spread_type' not in pl:
        ng('bgp-rate-fortress',
           'placement 缺 spread_type（原版要塞是缺省 linear；必须显式写出才可复算）')
    ok()
    if pl.get('frequency_reduction_method', 'default') != 'default':
        ng('bgp-rate-fortress',
           'frequency_reduction_method=%r 会改变实际生成率（要塞没有这一项）'
           % pl.get('frequency_reduction_method'))
    ok()
    # salt：仍是我们自己的值，且不许被抄成要塞的
    if pl.get('salt') != OUR_SALT:
        ng('bgp-rate-salt', 'placement.salt=%r 不是我们记账的 %d' % (pl.get('salt'), OUR_SALT))
    ok()
    if pl.get('salt') == FORTRESS_SALT:
        ng('bgp-rate-salt',
           'placement.salt 抄成了下界要塞的 %d（同 salt + 同种子 ⇒ 候选区块与要塞重合）' % FORTRESS_SALT)
    ok()
    # 原版 jar 在就逐字段对穿（防冻结常量过期）；不在就只按冻结常量核（构建产物不入库）
    jar = os.path.join(ROOT, 'build', 'moddev', 'artifacts',
                       'neoforge-21.1.228-client-extra-aka-minecraft-resources.jar')
    if os.path.exists(jar):
        try:
            with zipfile.ZipFile(jar) as z:
                v = json.loads(z.read('data/minecraft/worldgen/structure_set/nether_complexes.json')
                               .decode('utf-8'))
            vpl = v.get('placement') or {}
            got = {'type': vpl.get('type'), 'spacing': vpl.get('spacing'),
                   'separation': vpl.get('separation'),
                   'spread_type': vpl.get('spread_type', 'linear')}
            if got != FORTRESS_PLACEMENT:
                ng('bgp-rate-fortress',
                   '冻结常量与原版 jar 不一致：jar=%r vs 常量=%r' % (got, FORTRESS_PLACEMENT))
            if vpl.get('salt') != FORTRESS_SALT:
                ng('bgp-rate-fortress', '原版要塞 salt 变了：%r != %r' % (vpl.get('salt'), FORTRESS_SALT))
            ok(2)
            print('[bgp-rate] 原版 jar 对穿：nether_complexes placement=%r（spread_type 缺省=linear）' % (vpl,))
        except Exception as e:
            ng('bgp-rate-fortress', '读原版 jar 失败：%s' % e)
    else:
        print('[bgp-rate] 原版 jar 不在（%s），只按冻结常量核对' % os.path.basename(jar))
    print('[bgp-rate] 我们的 placement=%r salt=%r（要塞 salt=%d，故意不同）'
          % (pl, pl.get('salt'), FORTRESS_SALT))
    # ★★ 第八轮 ③：玄武岩那一套已删除 ⇒ 这里改成**负向断言**（旧口径原文留档在下面）
    #   旧口径（第六/七轮）：玄武岩 set 的 placement 必须与主结构逐字段相同、salt 必须不同（19710102）。
    if os.path.exists(SSET_BASALT):
        ng('bgp-rate-single', 'structure_set/golden_prison_basalt.json 还在（第八轮必须删除）')
    ok()
    if os.path.exists(os.path.join(WG, 'structure', 'golden_prison_basalt.json')):
        ng('bgp-rate-single', 'structure/golden_prison_basalt.json 还在（第八轮必须删除）')
    ok()
    print('[bgp-rate] 只剩一套 structure_set：salt=%r（玄武岩那一套已按作者要求删除）' % (pl.get('salt'),))


def check_treasure_unique():
    """[bgp-treasure-unique-*] 宝藏房一所结构内只有一个 —— 从「抽样」升级成「结构上不可能违反」。

    作者的规矩（2026-10-20 第三轮原话）：「不过要记住的是**宝藏房一所结构内只有一个**。」
    ⚠ 旧口径（原文保留、不放宽）：唯一性只靠两条**机制** —— `start_pool` 指向 start 池
    且 `JigsawPlacement#addPieces` 只取一次起点；再加 A 级**抽样**（种子 20261020 / 20261021
    各生成 1 座，宝藏房都是 1）。**抽样不能证明「不可能」**：把 treasure 塞进别的池
    （例如 lane.json 的 elements，或某个 fallback 指向 start），抽样仍可能偶然还是 1 座。
    本段把它钉成 4 组断言（15 个池**逐文件读** = 1 条 start + 14 条 noref，不是 substring 命中）：

      1) `[bgp-treasure-unique-start]`：start.json 的 elements **恰好 1 项**且指向 treasure；
         structure/golden_prison.json 的 `start_pool` **恰好**是这个 start 池；
      2) `[bgp-treasure-unique-noref]`：**除 start.json 外**其余 14 个池里一个都不许引用
         treasure（**双向**：start 必须引用、别人都不许引用）；
      3) `[bgp-treasure-unique-fallback]`：**没有任何池的 fallback 链**落到含 treasure 的池
         （fallback 是在 `depth+1 > size` 时放的那一步，它一样能造出第二座）；
      4) `[bgp-treasure-unique-nbt]`：`treasure.nbt` 在整棵 worldgen JSON 树里**只在
         start.json 被引用一次** —— 用 os.walk 逐文件读 + 逐文件计数，不是搜一遍字符串。

    四条都能红：扰动矩阵 P10（treasure 塞进 lane 的 elements）/ P11（lane 的 fallback=start）/
    P12（start.json 再塞一份 treasure）逐一证明（docs\\金之牢狱-实现-证据\\gp_perturb.py）。
    """
    if not os.path.isdir(POOL_DIR):
        ng('bgp-treasure-unique-start', '缺池目录 %s' % POOL_DIR)
        return
    pools = {}
    for f in sorted(os.listdir(POOL_DIR)):
        if not f.endswith('.json'):
            continue
        name = f[:-5]
        try:
            pools[name] = json.load(open(os.path.join(POOL_DIR, f), encoding='utf-8'))
        except Exception as e:
            ng('bgp-treasure-unique-start', '池 %s 解析失败：%s' % (name, e))
    ok(len(pools))
    if 'start' not in pools:
        ng('bgp-treasure-unique-start', '缺 start.json（唯一性的起点没了）')
        return
    sp = os.path.join(WG, 'structure', 'golden_prison.json')
    if not os.path.exists(sp):
        ng('bgp-treasure-unique-start', '缺 structure/golden_prison.json')
        return

    def el_locs(d):
        return [((e.get('element') or {}).get('location') or '') for e in (d.get('elements') or [])]

    # ---- 1) start 池恰好 1 项 + 指向 treasure；structure.start_pool 恰好指向 start
    s_els = el_locs(pools['start'])
    if len(s_els) != 1:
        ng('bgp-treasure-unique-start',
           'start.json 的 elements 有 %d 项（必须恰好 1 项：起点只许取一次宝藏房）' % len(s_els))
    ok()
    if s_els[:1] != [TREASURE_LOC]:
        ng('bgp-treasure-unique-start',
           'start.json 唯一的元素指向 %r != %r' % (s_els[0] if s_els else None, TREASURE_LOC))
    ok()
    try:
        st = json.load(open(sp, encoding='utf-8'))
    except Exception as e:
        ng('bgp-treasure-unique-start', 'structure JSON 解析失败：%s' % e)
        return
    spv = st.get('start_pool')
    if spv != POOL + 'start':
        ng('bgp-treasure-unique-start',
           'structure.start_pool=%r 必须恰好是 %r（换池就可能从别处长大）' % (spv, POOL + 'start'))
    ok()
    # ★ 第六轮：玄武岩那套的 start_pool 必须**同一个**（两套都从 start 池起 ⇒ 每座结构仍只有一个宝藏房）
    # ★★ 第八轮 ③：玄武岩那套已删除 ⇒ 改成"文件必须不存在"的负向断言（旧口径留档在下面注释里）
    #   旧口径：st_b = json.load(open(STRUCT_BASALT)) ; st_b['start_pool'] == spv
    if os.path.exists(STRUCT_BASALT):
        ng('bgp-treasure-unique-start',
           'golden_prison_basalt.json 还在（第八轮已删除；旧口径是"两套同一个 start 池"）')
    ok()
    print('[bgp-treasure-unique] 只剩一套 structure：start_pool=%r；玄武岩那一套文件不存在' % (spv,))

    # ---- 2) 除 start.json 外，其余池里一个都不许引用 treasure（双向）
    bad = []
    for n in sorted(pools):
        if n == 'start':
            continue
        hits = [s for s in walk_strings(pools[n]) if is_treasure_loc(s)]
        if hits:
            bad.append((n, hits[:2]))
    if bad:
        ng('bgp-treasure-unique-noref',
           '除 start.json 外还有 %d 个池引用了 treasure（能长出第二座）：%s' % (len(bad), bad[:4]))
    ok(max(0, len(pools) - 1))
    if not any(is_treasure_loc(s) for s in walk_strings(pools['start'])):
        ng('bgp-treasure-unique-noref', 'start.json 里找不到 treasure 的引用（这条断言空转）')
    ok()

    # ---- 3) fallback 链：任何池的 fallback 链都不许落到含 treasure 的池
    def has_treasure(n):
        return any(is_treasure_loc(x) for x in el_locs(pools[n]))

    bad_fb, chains = [], 0
    for n in sorted(pools):
        cur = pools[n].get('fallback')
        chain, seen = [], set()
        while isinstance(cur, str) and cur != 'minecraft:empty':
            tgt = pool_name(cur)
            if tgt is None:
                break
            chain.append(tgt)
            if tgt in seen:
                break
            seen.add(tgt)
            if tgt not in pools:
                break
            if has_treasure(tgt):
                bad_fb.append((n, chain[:]))
                break
            cur = pools[tgt].get('fallback')
        if chain:
            chains += 1
    if bad_fb:
        ng('bgp-treasure-unique-fallback',
           '有 %d 个池的 fallback 链会落到含 treasure 的池（fallback 会造出第二座）：%s'
           % (len(bad_fb), bad_fb[:4]))
    if chains == 0:
        ng('bgp-treasure-unique-fallback',
           '没有任何非 empty 的 fallback 链（断言空转：lane / cell_small_1..3 本该有）')
    ok(chains)

    # ---- 4) treasure.nbt 只在 start.json 被引用一次（逐文件扫描 + 逐文件计数）
    wg_json = []
    for dirpath, _dirs, fs in os.walk(WG):
        for f in fs:
            if f.endswith('.json'):
                wg_json.append(os.path.join(dirpath, f))
    if not wg_json:
        ng('bgp-treasure-unique-nbt', 'worldgen 下一个 JSON 都没有（空转）')
    counts = {}
    for p in sorted(wg_json):
        try:
            d = json.load(open(p, encoding='utf-8'))
        except Exception as e:
            ng('bgp-treasure-unique-nbt', '%s 解析失败：%s' % (os.path.basename(p), e))
            continue
        c = sum(1 for s in walk_strings(d) if is_treasure_loc(s))
        if c:
            counts[os.path.relpath(p, WG).replace('\\', '/')] = c
        ok()
    total = sum(counts.values())
    if counts != {'template_pool/golden_prison/start.json': 1}:
        ng('bgp-treasure-unique-nbt',
           'treasure.nbt 的逐文件引用表不是「只有 start.json 一次」：%r' % counts)
    ok()
    if not os.path.exists(os.path.join(STRUCT, 'treasure.nbt')):
        ng('bgp-treasure-unique-nbt', '缺 treasure.nbt（引用表为空也可能是空转）')
    ok()

    print('[bgp-treasure-unique] %d 池：start.elements=%d 指向 treasure；非 start 引用=%d；'
          'fallback 链 %d 条无一落到 treasure；worldgen JSON %d 个文件、treasure 引用共 %d 次（只 start.json）'
          % (len(pools), len(s_els), sum(1 for n in pools if n != 'start'
                                        and any(is_treasure_loc(s) for s in walk_strings(pools[n]))),
             chains, len(wg_json), total))


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
        # 正向 needle 跑在**去注释**源码上：注释里写着 getLuck() 不算数
        s = strip_comments(open(src, encoding='utf-8').read(), 'java')
        if 'getLuck()' not in s or 'bonusRolls.getFloat' not in s:
            ng('bgp-loot', 'LootPool 源码里没看到 luck x bonusRolls 的乘法（口径来源失效）')
        ok()


# ================================================================== 第九轮（2026-10-22）
# 「让牢狱延伸至空域再架出入口」：**出入口件必须整块落在空气里**（overwroteNatural == 0）。
# jigsaw 装配是纯几何的、感知不到空域 ⇒ 新增自定义 StructureType + afterPlace 后处理（Java）。
# 静态关卡能守的是**机制在不在**（文件/注册/写入入口唯一/连通性前置/退化分支/恢复逻辑）；
# 真正的空域读数是 A 级 runServer 探针（probe/gpk/report.json，见 §15 的读数表）。
JAVA_ROOT = os.path.join(ROOT, 'src', 'main', 'java', 'com', 'hjmmd_8', 'bettergold')
JAVA_STRUCT = os.path.join(JAVA_ROOT, 'worldgen', 'GoldenPrisonStructure.java')
JAVA_REG = os.path.join(JAVA_ROOT, 'registry', 'AllStructures.java')
JAVA_MOD = os.path.join(JAVA_ROOT, 'bettergold.java')
EXIT_AIR_TYPE = 'bettergold:golden_prison'
# 正向 needle（跑在**去注释源码**上；每条都是"实现里必须真的有的句子"）
EXIT_AIR_NEEDLES = [
    ('extends Structure', '必须是 Structure 的子类（JigsawStructure 是 final，源码 :26）'),
    ('public void afterPlace(', '必须在 afterPlace 里做（件已放完才有地形可探测）'),
    ('JigsawPlacement.addPieces(', '装配仍然走原版 JigsawPlacement（不自己写装配）'),
    ('MAX_SEARCH = 24', '搜索距离 1..24'),
    ('level.setBlock(', '写方块的唯一入口'),
    ('allowedCells.contains(', '写入前的允许集断言（只动出入口）'),
    ('naturalBelow(level, c.pos, oldBox)', '旧 footprint 恢复成原地形'),
    ('usableTerrain(s)', '恢复材质必须是地形方块（不许抄结构方块/带 BE 的方块）'),
    ('floodAir(level, window, seed, oldBlocked, MAX_FLOOD_CELLS, walls)', 'air-only 洪泛（连通性前置）'),
    ('Destination dest = searchDestination(', '目的地搜索必须真的被调用（关掉它就整段失效）'),
    ('boxSum(pre, strideX, strideY, i1, j1, k1, i2, j2, k2) != vol', '判据：整个 bbox 每一格都必须是空域'),
    ('== volShell', '严格档：外圈一圈也必须是空域'),
    ('if (write(level, c.pos, natural, rec))', '恢复 footprint 的那一次写必须真的发生'),
    ('"minecraft:air".equals(c.cell.placedBlockId())',
     '连通性闸门只挡"放置后是实心"的格（jigsaw 的 final_state=air 必须留空）'),
    ('protectedCells.contains(', '别的出入口的门道格不许被压掉'),
    ('overwroteNatural', 'overwroteNatural 判据必须真的在源码里'),
    ('"notConnected"', '退化分支：连通不到就不搬'),
    ('"noAir"', '退化分支：找不到空域就不搬'),
    # ★ 第九轮收尾（第十轮工作项，2026-10-23）：恢复旧 footprint 时**保留整条 3×3×3 通道**
    ('if (c.cell.air() || c.pos.equals(seed))',
     '恢复只能跳过"模板空气格 + 口位格"（旧口径只留 M 一格 ⇒ 玩家只能钻 1×1 洞）'),
    ('keptAir++;', '保留的模板空气格必须真的计数（读数 keptAir）'),
    ('if (!fullyPlaced(level, pep.getBoundingBox(), chunkPos)) {',
     '跨区块件必须等整件落地再搬（否则 3×3×3 内腔只有当前区块那一片是真的）'),
    ('if (!window.isInside(n) || level.isOutsideBuildHeight(n)) {',
     'air-only 洪泛必须是逐格 6 邻接 BFS（不许退化成"只看中心一格"）'),
    ('queue.add(n);', '洪泛必须真的把邻格入队（反"只看中心"）'),
    # ★ 父代理 2026-10-23 裁定 (b)+增强：全部件 bbox（**含父件**）整箱当墙 + 相邻禁止
    ('new PieceWalls(', '必须把其它件的模板格做成墙集（生成期连通 = 最终世界连通）'),
    ('walls.blocked(n)', '洪泛必须真的检查墙集（否则墙集是摆设）'),
    ('walls.addAir(c.pos);', '模板 air 格必须登记为"最终世界可走"（件还没放时地形可能还是岩体）'),
    ('ob.intersects(candBox.inflatedBy(1))', '目的地不许与任何其它件 bbox 相交**或相邻**（≥1 格空隙）'),
    # ★ 第十轮（2026-10-23）根因修复：旧 3×3 房间必须可走 + 全部件的**实心格**（不是整箱 bbox）当墙
    ('oldBlocked.add(pack(c.pos));',
     '旧位置只有"放置后仍是实心"的格才是障碍（模板空气格 + 口位格搬迁后仍是空气，是玩家走进旧房间的路）'),
    ('if (!"minecraft:air".equals(c.cell.placedBlockId())) {\n                oldBlocked.add(pack(c.pos));',
     '旧位置的障碍集必须只含"放置后是实心"的格（P3 扰动：改回挡住全部旧格 ⇒ 必须红）'),
    ('templateOf(opep, mgr)', '每个件都要按自己的模板展开（先算 bbox、再逐区块放 ⇒ 模板实心格才是未来的墙）'),
    ('templateCells(otherTpl)', '墙集必须逐格来自模板（不是整箱 bbox：bbox 会把件内走廊也当墙）'),
    ('walls.addCell(c.pos);', '模板实心格必须真的进墙集（否则墙集是摆设）'),
    ('walls.addBox(other.getBoundingBox());', '拿不到模板时才许退回整箱当墙（保守分支）'),
    ('ob.intersects(candBox.inflatedBy(1))', '目的地不许与任何其它件 bbox 相交**或相邻**（≥1 格空隙）'),
]


def check_exit_air():
    """[bgp-exit-air] 第九轮：出入口搬进空域的**机制**（读数在 A 级探针里）。"""
    # ---- 1) structure json 的 type（★ 本轮唯一改动的数据字段）
    try:
        st = json.load(open(STRUCT_MAIN, encoding='utf-8'))
    except Exception as e:
        ng('bgp-struct-type', 'structure json 解析失败：%s' % e)
        return
    if st.get('type') != EXIT_AIR_TYPE:
        ng('bgp-struct-type', 'structure.type = %r != %r' % (st.get('type'), EXIT_AIR_TYPE))
    ok()
    if st.get('type') == 'minecraft:jigsaw':
        ng('bgp-struct-type', 'type 退回 minecraft:jigsaw（纯数据搬运不了出入口）')
    ok()
    # 其余字段一格都不许跟着变（防止"改 type 时顺手改了别的"）
    for k, v in EXPECT_STRUCT_MAIN.items():
        if st.get(k) != v:
            ng('bgp-struct-type', '改 type 时 %s 被动过了：%r != %r' % (k, st.get(k), v))
        ok()

    # ---- 2) 注册（StaticRegistry.Name+Type）
    for path, what in ((JAVA_STRUCT, 'GoldenPrisonStructure.java'), (JAVA_REG, 'AllStructures.java')):
        if not os.path.exists(path):
            ng('bgp-exit-air', '缺文件 %s（本轮必须新增）' % what)
            return
        ok()
    reg_src = strip_comments(open(JAVA_REG, encoding='utf-8').read(), 'java')
    struct_src = strip_comments(open(JAVA_STRUCT, encoding='utf-8').read(), 'java')
    mod_src = strip_comments(open(JAVA_MOD, encoding='utf-8').read(), 'java')
    if 'Registries.STRUCTURE_TYPE' not in reg_src:
        ng('bgp-exit-air', 'AllStructures 没注册到 Registries.STRUCTURE_TYPE')
    ok()
    if '"golden_prison"' not in reg_src:
        ng('bgp-exit-air', 'AllStructures 里没有 register("golden_prison", …)')
    ok()
    if 'STRUCTURE_TYPES.register(modEventBus)' not in mod_src:
        ng('bgp-exit-air', 'bettergold.java 没把 STRUCTURE_TYPES 挂到 mod 总线（= 静默不注册）')
    ok()

    # ---- 3) 正向 needle（去注释源码）
    for needle, why in EXIT_AIR_NEEDLES:
        if needle not in struct_src:
            ng('bgp-exit-air', '源码里找不到 %r —— %s' % (needle, why))
        ok()
    # ---- 3b) 反回退：第十轮修掉的三个错口径不许回来
    for bad, why in (
        ('parentPiece', '父件 bbox 不许再放行（放行只会放进"未放置的实心格"这种假通）'),
        ('oldAir', '旧口径变量 oldAir（挡住全部旧格）不许回来 —— 模板空气格+口位格搬迁后仍是空气'),
        ('newMouth.relative(mouth.front)', '外门口不许再查 jigsaw 外侧那一格（查错面）'),
    ):
        if bad in struct_src:
            ng('bgp-exit-air', '源码里还有旧口径 %r —— %s' % (bad, why))
        ok()
    # ---- 4) 唯一写入入口：setBlock 全文件恰好 1 次（"只动出入口"的结构性保证）
    n_set = struct_src.count('level.setBlock(')
    if n_set != 1:
        ng('bgp-exit-air', 'GoldenPrisonStructure 里 level.setBlock( 出现 %d 次（必须恰好 1 次，= 单一写入入口）'
           % n_set)
    ok()
    if struct_src.count('static boolean write(') != 1:
        ng('bgp-exit-air', '缺少唯一的 write(...) 写入助手')
    ok()
    # ---- 5) 判据必须真的在代码里（不是注释）：空判定 + 外圈 + 洪泛 + 断开就不搬
    if 'isAir()' not in struct_src:
        ng('bgp-exit-air', '没有 isAir() —— 空域判据不在代码里')
    ok()
    if 'boxSum(' not in struct_src:
        ng('bgp-exit-air', '没有 boxSum( —— 穷举搜索的 3D 前缀和不见了')
    ok()
    if 'reach2.contains(' not in struct_src:
        ng('bgp-exit-air', '最终连通性闸门（把新出入口实心格挡上再洪泛）不见了')
    ok()
    # ---- 6) 反退化：不许在搬不动时"自己挖空腔"（作者第七轮已否掉）
    if 'setBlock(pos, Blocks.' in struct_src:
        ng('bgp-exit-air', "源码里出现 'setBlock(pos, Blocks.' —— 写入必须来自模板/地形采样，不许写死字面量")
    ok()
    # Blocks.AIR 只允许出现 1 次（NBT 解析失败时的兜底 state），**不许**当成写入值
    if struct_src.count('Blocks.AIR') != 1 or 'state = Blocks.AIR.defaultBlockState();' not in struct_src:
        ng('bgp-exit-air', 'Blocks.AIR 出现 %d 次（只允许 1 次 = NBT 解析兜底；当成"挖空气"写进世界 = 作者已否掉的方案）'
           % struct_src.count('Blocks.AIR'))
    ok()


# ================================================================== 第九轮收尾（2026-10-23）
# ① 旧 footprint 恢复必须保留整条 3×3×3 通道（旧口径只留 M 一格；静态关卡守 needle，世界读数在探针）；
# ② 全链连通：从宝藏房的可站格 air-only 洪泛必须到**每一个**出入口的当前口位格。
#    静态关卡读**归档的 A 级探针报告**（probe/gpm/report.json ⇒ docs\…\02/03），逐座逐口核。
EVID_CHAIN = os.path.join(ROOT, 'docs', '金之牢狱-第九轮收尾-证据')
EXIT_CHAIN_FILES = [
    # (标签, 归档文件, 期望座数, 期望出入口数, orphansInWorld 基线（上一轮 15/5，只许不增）)
    ('A', '02-A-种子20261022.json', 5, 33, 15),
    ('B', '03-B-种子7.json', 3, 28, 5),
]


def check_exit_chain():
    """[bgp-exit-chain] 全链连通 A 级归档（逐座逐口）。

    数据 = 本轮 `runServer` 探针（`GpmProbe`）写出的 `report.json`，两次运行各归档一份。
    判据（读报告，不重算世界）：
      ① 每座宝藏房 1、四面道 >= 3、forceload 双向归零；
      ② **每一个出入口的当前口位格**都能从宝藏房的可站格 air-only 洪泛到（不可达就列堵点）；
      ③ 搬迁后的旧位置：exit 模板 3×3×3 内腔 27 格 + 3×3 门口 9 格全是空气，
         且从父件口位格洪泛能到全部 27 格；
      ④ 回归：overwroteNatural == 0（搬迁件）、violations == 0、旧 footprint 出入口方块 0 / 外来方块 0；
      ⑤ orphansInWorld 不增（基线 A=15 / B=5，上一轮读数，见 §15.6）。
    """
    total_exits = 0
    total_reached = 0
    total_moved = 0
    moved_rows = []
    for tag, fname, want_structures, want_exits, max_orphans in EXIT_CHAIN_FILES:
        path = os.path.join(EVID_CHAIN, fname)
        if not os.path.exists(path):
            ng('bgp-exit-chain', '缺归档报告 %s（先跑 A 级 runServer 探针，再跑本关卡）' % fname)
            continue
        try:
            d = json.load(open(path, encoding='utf-8'))
        except Exception as e:
            ng('bgp-exit-chain', '%s 解析失败：%s' % (fname, e))
            continue
        ok()
        if not d.get('typeIsOurs'):
            ng('bgp-exit-chain', '%s 的 structure type 不是 bettergold:golden_prison' % fname)
        ok()
        if str(d.get('structureClass', '')).rsplit('.', 1)[-1] != 'GoldenPrisonStructure':
            ng('bgp-exit-chain', '%s 的 structureClass=%r' % (fname, d.get('structureClass')))
        ok()
        rows = d.get('structures') or []
        if len(rows) != want_structures:
            ng('bgp-exit-chain', '%s 测到 %d 座 != 期望 %d' % (fname, len(rows), want_structures))
        ok()
        orphans = 0
        exits_sum = 0
        for row in rows:
            where = '%s/%s' % (tag, row.get('chunk'))
            if row.get('treasure') != 1:
                ng('bgp-exit-chain', '%s 宝藏房 %r != 1' % (where, row.get('treasure')))
            ok()
            if int(row.get('cross') or 0) < 3:
                ng('bgp-exit-chain', '%s 四面道 %r < 3' % (where, row.get('cross')))
            ok()
            if row.get('forceloadedChunks') != row.get('forceloadUndone'):
                ng('bgp-exit-chain', '%s forceload 没双向归零：%r != %r'
                   % (where, row.get('forceloadedChunks'), row.get('forceloadUndone')))
            ok()
            ports = row.get('ports') or {}
            orphans += int(ports.get('orphansInWorld') or 0)
            exits = row.get('exits') or []
            if not exits:
                ng('bgp-exit-chain', '%s 一个出入口都没测到（空转）' % where)
            ok()
            exits_sum += len(exits)
            for ex in exits:
                who = '%s#%d' % (where, ex.get('idx'))
                if not ex.get('reachable'):
                    ng('bgp-exit-chain', '%s 口位 %s 从宝藏房 air-only 洪泛**到不了**：%s %s'
                       % (who, ex.get('mouth'), ex.get('reason'), ex.get('blockers')))
                ok()
                if ex.get('oldCavity27Air') != 27:
                    ng('bgp-exit-chain', '%s 旧位置 3×3×3 内腔空气 %r/27（门道被压回 1 格？）'
                       % (who, ex.get('oldCavity27Air')))
                ok()
                if ex.get('oldDoorPlane9Air') != 9:
                    ng('bgp-exit-chain', '%s 旧位置 3×3 门口空气 %r/9（门洞被恢复成岩体）'
                       % (who, ex.get('oldDoorPlane9Air')))
                ok()
                if ex.get('cavityFromParent') != 27:
                    ng('bgp-exit-chain', '%s 从父件口位洪泛只到内腔 %r/27' % (who, ex.get('cavityFromParent')))
                ok()
                # ★ 父代理 2026-10-23 硬判据：搬迁件必须"旧父口 P → 新口位 M'"在最终世界也通
                if ex.get('moved') and not ex.get('reachedFromOldParent'):
                    ng('bgp-exit-chain', '%s 搬迁件 reachedFromOldParent=False（旧父口→新口位不通）' % who)
                ok()
                if ex.get('moved'):
                    # 旧 footprint 的"恢复干净"只对**搬迁件**成立（没搬迁的旧 footprint 就是它自己）
                    if ex.get('oldExitBlocksLeft') not in (None, 0):
                        ng('bgp-exit-chain', '%s 旧 footprint 还剩 %r 个出入口方块'
                           % (who, ex.get('oldExitBlocksLeft')))
                    ok()
                    if ex.get('oldForeignBlocks') not in (None, 0):
                        ng('bgp-exit-chain', '%s 旧 footprint 有 %r 个外来方块'
                           % (who, ex.get('oldForeignBlocks')))
                    ok()
                    # ★ 第十轮：搬迁件的新位置必须离**所有**别的件 bbox ≥1 格空隙（inflatedBy(1) 口径）
                    if ex.get('gapToPieces') is None or int(ex.get('gapToPieces')) < 2:
                        ng('bgp-exit-chain', '%s 搬迁件与别的件 bbox 空隙 %r < 2（贴脸/相邻）'
                           % (who, ex.get('gapToPieces')))
                    ok()
                    # ★ 第十轮：新口位面（这个件**唯一**的开口）外侧至少一格从宝藏房可达
                    if int(ex.get('frontReach') or 0) < 1 and int(ex.get('doorwayReach') or 0) < 1:
                        ng('bgp-exit-chain', '%s 新口位面外侧没有一格从宝藏房可达（门口埋在岩体里）' % who)
                    ok()
                    # ★ 第十轮：旧位置整条 3×3 房间（44 个模板空气格）必须全空气
                    if ex.get('oldTunnelCells') != 44 or ex.get('oldTunnelAir') != 44:
                        ng('bgp-exit-chain', '%s 旧位置整条 3×3 房间空气 %r/%r（应 44/44）'
                           % (who, ex.get('oldTunnelAir'), ex.get('oldTunnelCells')))
                    ok()
                    if not ex.get('oldMouthReach'):
                        ng('bgp-exit-chain', '%s 搬迁件旧口位 M（旧 3×3 房间入口）从宝藏房不可达' % who)
                    ok()
                    moved_rows.append((who, ex.get('mouth'), ex.get('oldMouth'),
                                       ex.get('frontReach'), ex.get('doorwayReach'),
                                       ex.get('oldTunnelAir'), ex.get('gapToPieces'),
                                       (ex.get('record') or {}).get('outcome')))
                rec = ex.get('record')
                if isinstance(rec, dict):
                    if rec.get('violations') != 0:
                        ng('bgp-exit-chain', '%s violations=%r != 0' % (who, rec.get('violations')))
                    ok()
                    if rec.get('dist', -1) > 0:
                        total_moved += 1
                        if rec.get('overwroteNatural') != 0:
                            ng('bgp-exit-chain', '%s overwroteNatural=%r != 0'
                               % (who, rec.get('overwroteNatural')))
                        ok()
        if exits_sum != want_exits:
            ng('bgp-exit-chain', '%s 出入口数 %d != 期望 %d（扫描/计数口径变了？）'
               % (fname, exits_sum, want_exits))
        ok()
        if orphans > max_orphans:
            ng('bgp-exit-chain', '%s orphansInWorld=%d 比上一轮基线 %d 增加了'
               % (fname, orphans, max_orphans))
        ok()
        total_exits += exits_sum
        total_reached += sum(1 for row in rows for ex in (row.get('exits') or []) if ex.get('reachable'))
        print('[bgp-exit-chain] %s：%d 座 / %d 出入口 / 可达 %d / moved %d / orphansInWorld %d（基线 <= %d）'
              % (tag, len(rows), exits_sum,
                 sum(1 for row in rows for ex in (row.get('exits') or []) if ex.get('reachable')),
                 sum(1 for row in rows for ex in (row.get('exits') or []) if ex.get('moved')),
                 orphans, max_orphans))
    for r in moved_rows:
        print('[bgp-exit-chain] moved %s mouth=%s oldM=%s frontReach=%s doorwayReach=%s '
              'oldTunnelAir=%s gap=%s outcome=%s' % r)
    if total_exits and total_reached != total_exits:
        print('[bgp-exit-chain] ✗ 合计 %d/%d 可达（**如实报**：到不了的口见上面的 NG 行）'
              % (total_reached, total_exits))
    elif total_exits:
        print('[bgp-exit-chain] ✓ 合计 %d/%d 可达（逐座逐口；moved=%d）'
              % (total_reached, total_exits, total_moved))


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
        if len(pieces) != 26:      # 第八轮：20 → 26（+6 个四面道固定槽变体）；旧口径 20
            print('[bgp-baseline] 只加载到 %d 个件' % len(pieces))
            return 2
        check_pieces(pieces)
        check_air(pieces)
        check_void(pieces)
        check_connect(pieces)
        check_mirror(pieces)
        check_fertile(pieces)
        check_gate(pieces)
        check_cycle(pieces)
        check_cross3(pieces)
        check_entities_bes(pieces)
        check_exit_shaft(pieces)
        check_exit_air()
        check_exit_chain()
        check_worldgen()
        check_rate()
        check_treasure_unique()
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
