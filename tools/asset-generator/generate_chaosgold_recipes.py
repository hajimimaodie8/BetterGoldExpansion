#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混沌金（chaosgold）**器具 / 盔甲的工作台配方**生成器 —— 1.7 `bg-n10rg`。

用法:
    python generate_chaosgold_recipes.py --apply      # 写盘
    python generate_chaosgold_recipes.py              # 演练（只打印与自检）

作者原话（2026-10-17，**新的权威口径**）
----------------------------------------
> 「**混沌金是用工作台公式制作的，原版装备在工作台上面怎么来合成它就怎么来**」

⇒ 落法：**逐格照原版**（1.21.1 的 `data/minecraft/recipe/*.json`），只把**金属那一格**换成
   `bettergold:chaosgold_ingot`；木棍 / 木板 / 线 / 绊线钩这些**辅料保持原版**。
   （`count` 一律 1、`category` 一律 `equipment`，与原版一致。）

为什么单独一个脚本
------------------
既有 8 族的器具/盔甲走的是 **`smithing_*` 锻造**（base = 原版金装备 + 本族升级模板 + 本族锭），
而**混沌金没有升级锻造模板**（zip 里没这张贴图，立档 §4.0 ㉑ / §7 第 3 条）⇒ 它的装备
从来没有任何获取途径。本轮作者给出的解法是**工作台**，不是锻造 ⇒ 形状与既有的
`generate_metal_recipes.py`（批量替换万坚金模板）**完全不是一回事**，硬塞进去就是
1.4「四条熔炼串格」的同一种病（批量替换器里塞 if 分支）。所以它自己一个脚本、每条写全、自己能自检。

15 件 = 11 件（`bg-n10rg`）+ 4 件（`bg-n10rc2`）—— 逐件判定 + 依据见
`docs/1.7-混沌金与崩乱合金-需求立档.md` §20（11 件）与 §21（补的 4 件）
------------------------------------------------------------------------------------
| 件 | 原版来源（1.21.1 `data/minecraft/recipe/`） | 处置 |
|---|---|---|
| 剑 / 斧 / 镐 / 锹 / 锄 | `golden_*.json`（`X` = `gold_ingot`） | **工作台**，`X` → 混沌金锭 |
| 头盔 / 胸甲 / 护腿 / 靴子 | `golden_*.json`（`X` = `gold_ingot`） | **工作台**，`X` → 混沌金锭 |
| 盾牌 | `shield.json`（`o` = `iron_ingot`，`W` = `#minecraft:planks`） | **工作台**，`o` → 混沌金锭 |
| 弩 | `crossbow.json`（`&` = `iron_ingot`） | **工作台**，`&` → 混沌金锭 |
| **弓** | `bow.json` = ` " #X" / "# X" / " #X"`（`#` = 棍 ×3、`X` = 线 ×3） | **工作台**：**棍那一格换成混沌金锭**（3 锭 + 3 线） |
| **重锤** | `mace.json` = `" # " / " I "`（`#` = **重核**、`I` = 微风棒） | **工作台**：**重核那一格换成混沌金块**（1 块 + 1 微风棒） |
| **三叉戟** | 原版**没有合成配方**（溺尸掉落 / 试炼密室） | **原创形状**（不是原版形状！见 `EXTRA` 的 `note`），**待作者确认** |
| **乐事小刀** | 不是原版：`farmersdelight:golden_knife` = `"m" / "s"`（1 锭 + 1 棍） | **工作台** + `neoforge:mod_loaded(farmersdelight)` 条件（没装乐事 ⇒ 不产出） |

1.7 作者 2026-10-24 第 ⑨ 条（`gpt` 轮）：**四件形状逐格重写**（上表那四行的形状描述随之作废，
旧形状原文留档在 `EXTRA[...]["note"]` 与 `VANILLA["shield"/"crossbow"]` 的注释里）
------------------------------------------------------------------------------------------
| 件 | 新形状（逐格） | 格数 |
|---|---|---|
| 重锤 | 上 = 混沌金块、下 = 木棍（2 行，列位照抄原版上排中 / 下排中） | 1 块 + 1 棍 |
| 三叉戟 | 中 = 木棍；上 (0,1)、右 (1,2)、右上 (0,2)、左下 (2,0) = 混沌金锭 | 4 锭 + 1 棍 |
| 弩 | 上排 3 格 + 下排中间 1 格 = 混沌金锭；中 = 绊线钩；左 / 右 = 线 | 4 锭 + 2 线 + 1 钩 |
| 盾牌 | 3×3 除左下 / 右下两角外全填，中心 = 普通苹果 | **6 锭** + 1 苹果（⚠ 派单写"7 锭 + 1 苹果 = 8 格，两角空"：3×3 只有 9 格，8 + 2 空 = 10 格算术不成立；按位置落 = 6 + 1，见 §29） |
| 混沌金苹果（禁果） | **只核对不改**：既有 `chaosgold_forbidden_fruit.json` = 无序 1 苹果 + 8 混沌金锭，材料数与"围一圈"一致（无序本就不限摆法） | 8 锭 + 1 苹果 |

⚠ **`bg-n10rg` 的 4 件"停下报告"已被 `bg-n10rc2` 关闭**（作者 2026-10-18「第一个可以考虑」）：
旧口径的 4 条理由**原文留在**下面的 `EXCLUDED` 注释里（那 4 条判定当时是对的，裁定只是换了答案）。

自检（不通过就 exit 1，别写半套）
---------------------------------
1. 每条都是合法 JSON，`type` = `crafting_shaped`、`category` = `equipment`、`count` = 1；
2. **逐格**：`pattern` + `key` 与来源表（原版 JSON 的逐字抄本）**完全同形**，
   只有**点名的那几个键**被换成混沌金材料（11 件走 `SUBSTITUTIONS`，4 件走 `EXTRA.subs`）；
3. 产物 id = `bettergold:chaosgold_<件>`；
4. **反向**：key 里**不许**再出现 `minecraft:gold_ingot` / `minecraft:iron_ingot`（换漏了就是"免费金装"）；
5. 每件**至少 1 格**混沌金材料（锭或块 —— 重锤那格是**块**，见 §21）；
6. 件数 = 15，且**恰好**是 `GEAR` 这 15 件（多一件 / 少一件都报）；
7. **条件**：乐事刀那条**必须**带 `neoforge:mod_loaded(farmersdelight)`，其余 14 条**不许**带任何
   `neoforge:conditions`（没装乐事的机器上，其余 14 件照样要能合出来）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[2]
RECIPES = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"

NS = "bettergold"
METAL = "chaosgold"
INGOT = NS + ":chaosgold_ingot"
BLOCK = NS + ":chaosgold_block"
# 混沌金**材料**的两件（mace 那一格是块，其余都是锭）⇒ 自检 ⑤ 认这两件，不写死成锭
METAL_ITEMS = (INGOT, BLOCK)
STICK = "minecraft:stick"
PLANKS = "minecraft:planks"          # 原版 shield 用的是 tag
STRING = "minecraft:string"
TRIPWIRE = "minecraft:tripwire_hook"
HEAVY_CORE = "minecraft:heavy_core"
BREEZE_ROD = "minecraft:breeze_rod"
# 乐事小刀的连带条件（本仓 optional 口径 A：**物品**始终存在、配方按 mod_loaded 挂/不挂）
FD_CONDITION = {"type": "neoforge:mod_loaded", "modid": "farmersdelight"}

# ---------------------------------------------------------------------------------------
# 原版 1.21.1 的形状（**逐字抄自** `data/minecraft/recipe/<file>`，只把 JSON 折成 Python 字面量）
# 格式: 件 -> (原版配方文件名, pattern, key)
# ⚠ 这张表是**保真锚点**：生成器不"发明"形状，只在这张表上做"金属格替换"。
# ---------------------------------------------------------------------------------------
VANILLA: dict[str, tuple[str, list[str], dict[str, dict]]] = {
    "sword": ("golden_sword.json", ["X", "X", "#"], {
        "X": {"item": "minecraft:gold_ingot"}, "#": {"item": STICK}}),
    "axe": ("golden_axe.json", ["XX", "X#", " #"], {
        "X": {"item": "minecraft:gold_ingot"}, "#": {"item": STICK}}),
    "pickaxe": ("golden_pickaxe.json", ["XXX", " # ", " # "], {
        "X": {"item": "minecraft:gold_ingot"}, "#": {"item": STICK}}),
    "shovel": ("golden_shovel.json", ["X", "#", "#"], {
        "X": {"item": "minecraft:gold_ingot"}, "#": {"item": STICK}}),
    "hoe": ("golden_hoe.json", ["XX", " #", " #"], {
        "X": {"item": "minecraft:gold_ingot"}, "#": {"item": STICK}}),
    "helmet": ("golden_helmet.json", ["XXX", "X X"], {
        "X": {"item": "minecraft:gold_ingot"}}),
    "chestplate": ("golden_chestplate.json", ["X X", "XXX", "XXX"], {
        "X": {"item": "minecraft:gold_ingot"}}),
    "leggings": ("golden_leggings.json", ["XXX", "X X", "X X"], {
        "X": {"item": "minecraft:gold_ingot"}}),
    "boots": ("golden_boots.json", ["X X", "X X"], {
        "X": {"item": "minecraft:gold_ingot"}}),
    # 原版盾牌：6 木板（tag）+ 1 铁锭 ⇒ 只换铁锭那一格
    # ⚠ 1.7 作者 2026-10-24 第 ⑨-4 条之后**不再走这张表**（形状改由 `EXTRA["shield"]` 逐格给出）；
    #   本条原文留档 = 旧形状 `["WoW", "WWW", " W "]` 的来源。
    "shield": ("shield.json", ["WoW", "WWW", " W "], {
        "W": {"tag": PLANKS}, "o": {"item": "minecraft:iron_ingot"}}),
    # 原版弩：2 棍 + 1 铁锭 + 1 线 + 3 绊线钩 ⇒ 只换铁锭那一格
    # ⚠ 1.7 作者 2026-10-24 第 ⑨-3 条之后**不再走这张表**（形状改由 `EXTRA["crossbow"]` 逐格给出）；
    #   本条原文留档 = 旧形状 `["#&#", "~$~", " # "]` 的来源。
    "crossbow": ("crossbow.json", ["#&#", "~$~", " # "], {
        "#": {"item": STICK}, "&": {"item": "minecraft:iron_ingot"},
        "~": {"item": STRING}, "$": {"item": TRIPWIRE}}),
}

# 要被换成混沌金锭的**原版金属**（两张都出现过：金锭在 golden_*，铁锭在 shield / crossbow）
SUBSTITUTIONS = {"minecraft:gold_ingot": INGOT, "minecraft:iron_ingot": INGOT}

# ---------------------------------------------------------------------------------------
# 1.7 `bg-n10rc2`（作者 2026-10-18「第一个可以考虑」）：`bg-n10rg` 停下报告的 4 件补齐
#
# 形状来源**逐件写清**（这是本轮唯一"要判断"的地方，所以表里直接带 `note`）：
#   bow      —— 原版 `bow.json` 逐字（`#` 棍 ×3 / `X` 线 ×3）；**金属格 = 棍那一格** ⇒ 3 锭 + 3 线。
#               ⚠ 不能做成"3 棍 + 3 线"（那样一格混沌金都不用，= 零成本白送混沌金弓）。
#   mace     —— 原版 `mace.json` 逐字（`#` 重核 / `I` 微风棒）；**金属格 = 重核那一格**
#               ⇒ **重核 → 混沌金块** + 1 微风棒（块是"重的核"在本仓最接近的对应物）。
#   trident  —— ⚠ 原版**没有**配方 ⇒ 这是**原创形状**（3×3：上排 3 锭 + 中列再 1 锭 + 底部 1 棍），
#               **不是原版形状**，已在 `docs/1.7-...md` §21 明确写「原创、待作者确认」。
#   knife    —— 不是原版：`farmersdelight:golden_knife` 逐字（`m` 金锭 / `s` 棍）
#               ⇒ 1 混沌金锭 + 1 棍，并挂 `neoforge:mod_loaded(farmersdelight)`。
# ---------------------------------------------------------------------------------------
EXTRA: dict[str, dict] = {
    "bow": {
        "source": "data/minecraft/recipe/bow.json",
        "pattern": [" #X", "# X", " #X"],
        "key": {"#": {"item": STICK}, "X": {"item": STRING}},
        "subs": {"#": INGOT},                     # 棍 → 混沌金锭
        "condition": None,
        "original_shape": False,
        "note": "原版形状逐字；金属格 = 棍那一格（3 锭 + 3 线）",
    },
    # -----------------------------------------------------------------------------------
    # 1.7 作者 2026-10-24 第 ⑨ 条（`gpt` 轮）：**四条配方逐格改**（旧形状原文留档在每条 note 里）
    #
    # ⚠ 旧形状（原文留档，未删）：mace = 原版 `[" # ", " I "]`（# 重核 → 混沌金块、I 微风棒）
    #   ⇒ 作者「上 = 混沌金块，下 = 木棍」：把**微风棒那一格换成木棍**（"下" = 原版下排中间）。
    "mace": {
        "source": "data/minecraft/recipe/mace.json（列位照抄：上排中 / 下排中）",
        "pattern": [" B ", " S "],
        "key": {"B": {"item": BLOCK}, "S": {"item": STICK}},
        "subs": {},
        "condition": None,
        "original_shape": True,
        "note": "作者 2026-10-24 第 ⑨-1 条：上 = 混沌金块（原版重核那一格）、下 = 木棍（原版微风棒那一格）；"
                "2 行、列位照抄原版。旧形状原文留档：pattern `[\" # \", \" I \"]` + key "
                "`# → 混沌金块 / I → 微风棒`。",
    },
    # ⚠ 旧形状（原文留档，未删）：trident = 原创 `["XXX", " X ", " # "]`（上排 3 锭 + 中列 1 锭 + 底部 1 棍）。
    #   作者 2026-10-24 第 ⑨-2 条改成：中 = 木棍；上、右、右上、左下 = 混沌金锭（4 锭 + 1 棍）。
    #   逐格落位（行, 列）：上 (0,1) / 右上 (0,2) / 中 (1,1)=棍 / 右 (1,2) / 左下 (2,0)。
    "trident": {
        "source": "（原版没有 trident.json —— 形状由作者 2026-10-24 第 ⑨-2 条逐格给出）",
        "pattern": [" XX", " SX", "X  "],
        "key": {"X": {"item": INGOT}, "S": {"item": STICK}},
        "subs": {},
        "condition": None,
        "original_shape": True,
        "note": "作者 2026-10-24 第 ⑨-2 条：中 = 木棍；上 (0,1)、右 (1,2)、右上 (0,2)、左下 (2,0) = 混沌金锭"
                "（4 锭 + 1 棍）。旧形状原文留档：pattern `[\"XXX\", \" X \", \" # \"]`。",
    },
    # ⚠ 旧形状（原文留档，未删）：crossbow = 原版 `["#&#", "~$~", " # "]`
    #   （`#` 棍 ×3 / `&` 铁锭 → 混沌金锭 / `~` 线 ×2 / `$` 绊线钩）。
    #   作者 2026-10-24 第 ⑨-3 条改成：中 = 绊线钩；左、右 = 线；**最上面一排 3 格** + **最下面中间 1 格**
    #   = 混沌金锭（4 锭 + 2 线 + 1 钩）。
    "crossbow": {
        "source": "data/minecraft/recipe/crossbow.json（列位照抄，金属格按第 ⑨-3 条重排）",
        "pattern": ["XXX", "L$R", " X "],
        "key": {"X": {"item": INGOT}, "L": {"item": STRING}, "R": {"item": STRING},
                "$": {"item": TRIPWIRE}},
        "subs": {},
        "condition": None,
        "original_shape": True,
        "note": "作者 2026-10-24 第 ⑨-3 条：上排 3 格 + 下排中间 1 格 = 混沌金锭（共 4）；"
                "中 = 绊线钩；左 / 右 = 线（各 1）。旧形状原文留档：pattern `[\"#&#\", \"~$~\", \" # \"]`"
                "（# 棍 ×3、& 铁锭、~ 线 ×2、$ 绊线钩）。",
    },
    # ⚠ 旧形状（原文留档，未删）：shield = 原版 `["WoW", "WWW", " W "]`
    #   （`W` 木板 tag ×6 / `o` 铁锭 → 混沌金锭）。
    #   作者 2026-10-24 第 ⑨-4 条改成：3×3 **除左下、右下两角**外全是混沌金锭 + **中间放一个普通苹果**。
    #   ⚠ 逐格落位（行, 列）：上排 3 格 (0,0)(0,1)(0,2)、中排左右 (1,0)(1,2)、下排中间 (2,1)
    #     = **6 锭**；中心 (1,1) = 苹果；左下 (2,0) / 右下 (2,2) = 空。
    #   ⚠ 派单同时写了「7 锭 + 1 苹果 = 8 格，两角空」—— 3×3 只有 9 格，8 + 2 空 = 10 格**算术不成立**；
    #     苹果占中心就必然顶掉一格锭 ⇒ 按**位置描述**（除两角外全锭、中心苹果）落 = **6 锭 + 1 苹果**。
    #     已在 `docs/1.7-...md` §29 ⑨-4 记账（这是本轮唯一的"需求自相矛盾"点）。
    "shield": {
        "source": "data/minecraft/recipe/shield.json（格位照抄原版 7 格：除下排两角外全填）",
        "pattern": ["XXX", "XAX", " X "],
        "key": {"X": {"item": INGOT}, "A": {"item": "minecraft:apple"}},
        "subs": {},
        "condition": None,
        "original_shape": True,
        "note": "作者 2026-10-24 第 ⑨-4 条：3×3 除左下 / 右下两角外全填（7 格），中心 = 普通苹果"
                "⇒ 混沌金锭 6 + 苹果 1。旧形状原文留档：pattern `[\"WoW\", \"WWW\", \" W \"]`"
                "（W 木板 tag ×6、o 铁锭）。",
    },
    "knife": {
        "source": "data/farmersdelight/recipe/golden_knife.json",
        "pattern": ["m", "s"],
        "key": {"m": {"item": "minecraft:gold_ingot"}, "s": {"item": STICK}},
        "subs": {"m": INGOT},                     # 金锭 → 混沌金锭
        "condition": FD_CONDITION,
        "original_shape": False,
        "note": "乐事 golden_knife 逐字 + mod_loaded(farmersdelight) 条件（1 锭 + 1 棍）",
    },
}

# 不参与 `VANILLA` 替换的四件（见 `EXTRA`）；1.7 第 ⑨ 条把其中 4 件的形状**逐格**重写了。
SHAPE_EXPECT = {
    # 件 -> {物品 id: 格数}（作者 2026-10-24 第 ⑨ 条给的数；**独立于 pattern/key 的硬数字**）
    #   ⚠ 这里是"计数"，位置由 `validate_metal_data.py` 的 `[gpt9-*]` 段**逐格**钉住
    #     （作者提醒：只比计数抓不到位置错）。
    "mace": {BLOCK: 1, STICK: 1},
    "trident": {INGOT: 4, STICK: 1},
    "crossbow": {INGOT: 4, STRING: 2, TRIPWIRE: 1},
    # 盾牌：3×3 除左下/右下两角外 7 格 = 6 锭 + 中心 1 苹果（派单写"7 锭 + 1 苹果"，
    #   3×3 里算术不成立，按位置描述落；见 §29 ⑨-4 的记账）
    "shield": {INGOT: 6, "minecraft:apple": 1},
}

# 生成顺序（= 手册配方页顺序；稳定 ASCII，别随意重排）
# 前 11 件 = `bg-n10rg` 的原顺序（**不改**，前 6 个配方页因此逐字不动）；
# 后 4 件 = `bg-n10rc2` 补的（配对成页：弩+弓 / 重锤+三叉戟 / 刀单独一页）。
GEAR = ["sword", "axe", "pickaxe", "shovel", "hoe",
        "helmet", "chestplate", "leggings", "boots", "shield", "crossbow",
        "bow", "mace", "trident", "knife"]

# **不生成**的件 + 原因 —— 现在是 **空表**（0 件）。
# ⚠ 旧口径（`bg-n10rg`，2026-10-17）**原文留档、已作废**（作者 2026-10-18「第一个可以考虑」）：
#     EXCLUDED = {
#         "bow": "原版 bow.json = 3 棍 + 3 线，一格金属都没有 ⇒ 照字面会零成本合出混沌金弓",
#         "trident": "原版没有三叉戟的合成配方（溺尸掉落 / 试炼密室）⇒ 无「原版怎么合」可照",
#         "mace": "原版 mace.json = 重核 + 微风棒，没有锭 ⇒ 「金属那一格」指哪一格说不清",
#         "knife": "乐事小刀不是原版物品（farmersdelight:golden_knife = 1 锭 + 1 棍）⇒ 超出「原版」口径",
#     }
# 那 4 条判定**当时是对的**（照字面确实抄不出混沌金版）；裁定只是把答案从"停下报告"换成
# "按 §21 的四条读法补齐"。⇒ 本表保留（空），关卡仍按 `EXCLUDED` 断言"该有的必须 0 件"。
EXCLUDED: dict[str, str] = {}

# ---------------------------------------------------------------------------------------
# 1.7 `bg-n10up`（2026-10-18）：**混沌金锭的上游**（作者补的最后一个功能缺口）
#
# 作者原话（**新的权威口径**，逐字）
# > 「用 **9 个混沌金粒** 合成的，然后**混沌金粒由烧炼混沌金币获得**，而
# >  **混沌金币是由混沌金币串合成分解出的三个**」
#
# 落法（**照字面，一条不多**）：
#   ① `chaos_coin_string` → **3 × `chaos_coin`**
#      作者最早那句是「在合成表上**无序转换**」⇒ **`crafting_shapeless`**（不是 shaped）；
#      **币串被消耗 1 个**（`ingredients` 里就它一个、没有 `count`、没有剩余物 ⇒ 不是返瓶类）。
#   ② `chaos_coin` →（**烧炼**）→ `chaosgold_nugget`：**只做 `minecraft:smelting` 一条**。
#      xp / time / category = **既有「原料 → 锭」那一档**（8 条 `raw_*_smelting` 实测全是
#      `1.0 / 200 / misc`）；这三项在这里是**常量**，`check_upstream()` 会拿它们与那 8 条
#      **逐项比对**，不是凭印象填的数字（依据与记账见 `docs/1.7-...md` §23）。
#      ⚠ 「也应该能高炉 / 烟熏吧」= **不自己加**（作者只说了"烧炼"）⇒ 进"待作者确认"。
#      ⚠⚠ **旧口径，已被作者 2026-10-18 推翻**：原文保留（上一行不删）。作者本轮亲口要求
#         「混沌金币要用**高炉**也能烧成粒」⇒ 现在**两条都做**：`minecraft:smelting`（保留，200 tick）
#         + `minecraft:blasting`（**新增**，100 tick = 熔炉的一半，xp 同为 1.0、category 同为 misc，
#         与既有 8 条 `raw_*_blasting` 逐项同档）。落点见 `bg-n10fix` ①、`docs/1.7-...md` §24.1。
#   ③ 9 × `chaosgold_nugget` → 1 × `chaosgold_ingot`：**既有**（`bg-n10` 起就有
#      `chaosgold_ingot_from_nugget.json`，`generate_metal_recipes.py` 从万坚金模板产出，
#      `NNN / NNN / NNN`）⇒ **本脚本不重复生成**（再来一条同形配方 = 两条同产物打架），
#      只在 `check_upstream()` 里**逐格**钉住它 + 钉住它的**逆**（1 锭 → 9 粒）仍在。
# ---------------------------------------------------------------------------------------
COIN_STRING = NS + ":chaos_coin_string"
COIN = NS + ":chaos_coin"
NUGGET = NS + ":chaosgold_nugget"
STRING_TO_COIN_FILE = "chaos_coin_from_string.json"
COIN_SMELT_FILE = "chaos_coin_smelting.json"
# 1.7 `bg-n10fix` ①（2026-10-18 作者亲口要"高炉"）：第二条加热配方 = `minecraft:blasting`
COIN_BLAST_FILE = "chaos_coin_blasting.json"
# 「同档」锚点：既有 8 条 `raw_*_smelting` 的实测值（自检里逐项比对，改一处就红）
SMELT_EXPERIENCE = 1.0
SMELT_TIME = 200
SMELT_CATEGORY = "misc"
# 「同档」锚点：高炉 = 熔炉的**一半时间**、xp 相同（既有 8 条 `raw_*_blasting` 实测 1.0 / 100 / misc）
BLAST_EXPERIENCE = 1.0
BLAST_TIME = 100
BLAST_CATEGORY = "misc"
# ③ 既有那两条（本脚本**不写**它们，只核对）
INGOT_FROM_NUGGET_FILE = "chaosgold_ingot_from_nugget.json"
NUGGET_FROM_INGOT_FILE = "chaosgold_nugget_from_ingot.json"


def upstream_recipes() -> dict[str, dict]:
    """上游三条（**只有这三条**）。dict 保持插入顺序 = 写盘顺序 = 手册页顺序。"""
    return {
        STRING_TO_COIN_FILE: {
            "type": "minecraft:crafting_shapeless",
            "ingredients": [{"item": COIN_STRING}],
            "result": {"id": COIN, "count": 3},
        },
        COIN_SMELT_FILE: {
            "type": "minecraft:smelting",
            "category": SMELT_CATEGORY,
            "ingredient": {"item": COIN},
            "result": {"id": NUGGET},
            "experience": SMELT_EXPERIENCE,
            "cookingtime": SMELT_TIME,
        },
        COIN_BLAST_FILE: {
            "type": "minecraft:blasting",
            "category": BLAST_CATEGORY,
            "ingredient": {"item": COIN},
            "result": {"id": NUGGET},
            "experience": BLAST_EXPERIENCE,
            "cookingtime": BLAST_TIME,
        },
    }


def upstream_targets() -> list[tuple[str, dict]]:
    return list(upstream_recipes().items())


def _raw_smelting_anchor() -> dict:
    """既有「原料 → 锭」那一档的真实值（**唯一依据**，不在代码里另写一份）。"""
    return json.loads((RECIPES / "raw_sturdygold_smelting.json").read_text(encoding="utf-8"))


def _raw_blasting_anchor() -> dict:
    """既有「原料 → 锭」的**高炉**那一档（同上：读真实文件，不另写一份）。"""
    return json.loads((RECIPES / "raw_sturdygold_blasting.json").read_text(encoding="utf-8"))


def check_upstream(files: list[tuple[str, dict]]) -> list[str]:
    """上游两条 + 第 3 条（既有的 9 → 1）的**逐项 / 逐格**自检。"""
    bad: list[str] = []
    names = [name for name, _ in files]
    if names != [STRING_TO_COIN_FILE, COIN_SMELT_FILE, COIN_BLAST_FILE]:
        bad.append(f"上游配方不是恰好这三条（顺序也要稳定）：{names}")
    got = dict(files)

    # ① 币串 → 3 币：无序、恰好消耗 1 个币串、产物恰好 3 个
    coin_from_string = got.get(STRING_TO_COIN_FILE) or {}
    if coin_from_string.get("type") != "minecraft:crafting_shapeless":
        bad.append(f"{STRING_TO_COIN_FILE} 不是 crafting_shapeless（作者口径是「无序转换」）")
    ing = coin_from_string.get("ingredients")
    if not isinstance(ing, list) or len(ing) != 1:
        bad.append(f"{STRING_TO_COIN_FILE} 的 ingredients 不是恰好 1 项：{ing!r}")
    elif ing[0] != {"item": COIN_STRING}:
        bad.append(f"{STRING_TO_COIN_FILE} 的唯一原料不是 {COIN_STRING}（消耗 1 个、不许带 count）：{ing[0]!r}")
    if coin_from_string.get("result") != {"id": COIN, "count": 3}:
        bad.append(f"{STRING_TO_COIN_FILE} 的产物不是 {COIN} ×3：{coin_from_string.get('result')!r}")

    # ② 币 →（烧炼）→ 粒：只做 smelting 一条；xp / time / category 与既有同档逐项一致
    smelt = got.get(COIN_SMELT_FILE) or {}
    if smelt.get("type") != "minecraft:smelting":
        bad.append(f"{COIN_SMELT_FILE} 的 type 不是 minecraft:smelting（本轮只做熔炉一条）")
    if smelt.get("ingredient") != {"item": COIN}:
        bad.append(f"{COIN_SMELT_FILE} 的输入不是 {COIN}：{smelt.get('ingredient')!r}")
    if smelt.get("result") != {"id": NUGGET}:
        bad.append(f"{COIN_SMELT_FILE} 的产物不是 {NUGGET} ×1：{smelt.get('result')!r}")
    try:
        anchor = _raw_smelting_anchor()
    except Exception as exc:                              # noqa: BLE001
        bad.append(f"读不到同档锚点 raw_sturdygold_smelting.json：{exc!r}")
        anchor = {}
    for field, mine in (("category", smelt.get("category")),
                        ("experience", smelt.get("experience")),
                        ("cookingtime", smelt.get("cookingtime"))):
        if mine != anchor.get(field):
            bad.append(f"{COIN_SMELT_FILE} 的 {field}={mine!r} 与既有同档 raw_sturdygold_smelting 的 "
                       f"{anchor.get(field)!r} 不一致")
    if (smelt.get("experience"), smelt.get("cookingtime")) != (SMELT_EXPERIENCE, SMELT_TIME):
        bad.append("常量 SMELT_EXPERIENCE / SMELT_TIME 与产物不一致（改了产物没改常量？）")

    # ②-b 币 →（**高炉**）→ 粒：作者 2026-10-18 亲口要；xp / time / category 与既有同档**逐项**一致
    blast = got.get(COIN_BLAST_FILE) or {}
    if blast.get("type") != "minecraft:blasting":
        bad.append(f"{COIN_BLAST_FILE} 的 type 不是 minecraft:blasting（作者本轮点名要高炉）")
    if blast.get("ingredient") != {"item": COIN}:
        bad.append(f"{COIN_BLAST_FILE} 的输入不是 {COIN}：{blast.get('ingredient')!r}")
    if blast.get("result") != {"id": NUGGET}:
        bad.append(f"{COIN_BLAST_FILE} 的产物不是 {NUGGET} ×1：{blast.get('result')!r}")
    try:
        blast_anchor = _raw_blasting_anchor()
    except Exception as exc:                              # noqa: BLE001
        bad.append(f"读不到同档锚点 raw_sturdygold_blasting.json：{exc!r}")
        blast_anchor = {}
    for field, mine in (("category", blast.get("category")),
                        ("experience", blast.get("experience")),
                        ("cookingtime", blast.get("cookingtime"))):
        if mine != blast_anchor.get(field):
            bad.append(f"{COIN_BLAST_FILE} 的 {field}={mine!r} 与既有同档 raw_sturdygold_blasting 的 "
                       f"{blast_anchor.get(field)!r} 不一致")
    # 高炉 = 熔炉的**一半时间**、xp 相同（作者口径；与 8 条 raw_* 的两档关系一致）
    if (blast.get("experience"), blast.get("cookingtime")) != (BLAST_EXPERIENCE, BLAST_TIME):
        bad.append("常量 BLAST_EXPERIENCE / BLAST_TIME 与产物不一致（改了产物没改常量？）")
    if (BLAST_TIME, BLAST_EXPERIENCE) != (SMELT_TIME // 2, SMELT_EXPERIENCE):
        bad.append("高炉档与熔炉档不是「一半时间 / xp 相同」")

    # ③ 第 3 条 = **既有**的 9 粒 → 1 锭：本脚本不生成它，但必须逐格核对它没被本轮撞坏
    if INGOT_FROM_NUGGET_FILE in got:
        bad.append(f"{INGOT_FROM_NUGGET_FILE} 不该由本脚本生成（它归 generate_metal_recipes.py）")
    p3 = RECIPES / INGOT_FROM_NUGGET_FILE
    if not p3.is_file():
        bad.append(f"缺既有的 {INGOT_FROM_NUGGET_FILE}（9 粒 → 1 锭）")
    else:
        o3 = json.loads(p3.read_text(encoding="utf-8"))
        if o3.get("type") != "minecraft:crafting_shaped":
            bad.append(f"{INGOT_FROM_NUGGET_FILE} 不是 crafting_shaped")
        if o3.get("pattern") != ["NNN", "NNN", "NNN"]:
            bad.append(f"{INGOT_FROM_NUGGET_FILE} 的 pattern 不是 3×3 满格：{o3.get('pattern')!r}")
        if o3.get("key") != {"N": {"item": NUGGET}}:
            bad.append(f"{INGOT_FROM_NUGGET_FILE} 的 key 不是恰好 N={NUGGET}：{o3.get('key')!r}")
        if o3.get("result") != {"id": INGOT}:
            bad.append(f"{INGOT_FROM_NUGGET_FILE} 的产物不是 {INGOT} ×1：{o3.get('result')!r}")
        cells = [o3.get("key", {}).get(ch, {}) for row in o3.get("pattern") or [] for ch in row]
        if len(cells) != 9 or any(c != {"item": NUGGET} for c in cells):
            bad.append(f"{INGOT_FROM_NUGGET_FILE} 的 9 格不是逐格都为 {NUGGET}：{cells!r}")
    # 它的逆（1 锭 → 9 粒）必须还在、且没被改成别的数量
    p3r = RECIPES / NUGGET_FROM_INGOT_FILE
    if not p3r.is_file():
        bad.append(f"缺既有的 {NUGGET_FROM_INGOT_FILE}（1 锭 → 9 粒，9 → 1 的逆）")
    else:
        o3r = json.loads(p3r.read_text(encoding="utf-8"))
        if o3r.get("type") != "minecraft:crafting_shapeless":
            bad.append(f"{NUGGET_FROM_INGOT_FILE} 不是 crafting_shapeless")
        if o3r.get("ingredients") != [{"item": INGOT}]:
            bad.append(f"{NUGGET_FROM_INGOT_FILE} 的原料不是恰好 1 个 {INGOT}：{o3r.get('ingredients')!r}")
        if o3r.get("result") != {"id": NUGGET, "count": 9}:
            bad.append(f"{NUGGET_FROM_INGOT_FILE} 的产物不是 {NUGGET} ×9：{o3r.get('result')!r}")
    return bad


def _spec(gear: str) -> tuple[str, list[str], dict[str, dict], dict[str, str], dict | None, bool]:
    """件 -> (来源说明, pattern, key, {图例字符: 换成的物品 id}, 条件, 是否原创形状)。

    11 件走 `VANILLA` + `SUBSTITUTIONS`（原版金锭 / 铁锭 → 混沌金锭，自动推导）；
    4 件走 `EXTRA`（每个键换成什么都写在表里，因为 `bow` 换的是**棍**、`mace` 换的是**块**）。
    """
    if gear in EXTRA:
        e = EXTRA[gear]
        return e["source"], e["pattern"], e["key"], dict(e["subs"]), e["condition"], e["original_shape"]
    src, pattern, key = VANILLA[gear]
    subs = {ch: SUBSTITUTIONS[ing["item"]] for ch, ing in key.items()
            if ing.get("item") in SUBSTITUTIONS}
    return src, pattern, key, subs, None, False


def recipe(gear: str) -> dict:
    """一件混沌金装备的工作台配方：来源形状 + 点名的金属格换成混沌金材料。"""
    _src, pattern, key, subs, condition, _orig = _spec(gear)
    new_key: dict[str, dict] = {}
    for ch, ing in key.items():
        if ch in subs:
            new_key[ch] = {"item": subs[ch]}
        else:
            new_key[ch] = dict(ing)
    obj = {
        "type": "minecraft:crafting_shaped",
        "category": "equipment",
        "pattern": list(pattern),
        "key": new_key,
        "result": {"id": f"{NS}:{METAL}_{gear}", "count": 1},
    }
    if condition:
        # ⚠ 条件必须写在最前面（与既有的 smithing_*_knife.json 同形；NeoForge 的加载器不看键序，
        #   但"配方文件第一眼要先看见它是有条件的"这件事值得保持一致）
        return {"neoforge:conditions": [dict(condition)], **obj}
    return obj


def targets() -> list[tuple[str, dict]]:
    return [(f"{METAL}_{gear}.json", recipe(gear)) for gear in GEAR]


def check(files: list[tuple[str, dict]]) -> list[str]:
    bad: list[str] = []
    if len(files) != len(GEAR):
        bad.append(f"生成的配方数不是 {len(GEAR)}（实际 {len(files)}）")
    got_gears = [name[len(METAL) + 1:-len(".json")] for name, _ in files]
    if got_gears != GEAR:
        bad.append(f"生成的件不是 GEAR 这 {len(GEAR)} 件：{got_gears}")
    if list(EXCLUDED):
        bad.append(f"EXCLUDED 应当没有成员（4 件已补齐），实际还有：{sorted(EXCLUDED)}")
    for name, obj in files:
        gear = name[len(METAL) + 1:-len(".json")]
        if gear not in EXTRA and gear not in VANILLA:
            bad.append(f"{name} 既不在 VANILLA 也不在 EXTRA 表里")
            continue
        src, pattern, key, subs, condition, _orig = _spec(gear)
        if obj.get("type") != "minecraft:crafting_shaped":
            bad.append(f"{name} 的 type 不是 crafting_shaped")
        if obj.get("category") != "equipment":
            bad.append(f"{name} 的 category 不是 equipment")
        # ② 逐格：pattern 必须与来源**逐字**相同（含空格 = 空格子）
        if obj.get("pattern") != list(pattern):
            bad.append(f"{name} 的 pattern 与来源 {src} 不同：{obj.get('pattern')} != {pattern}")
        obj_key = obj.get("key") or {}
        if sorted(obj_key) != sorted(key):
            bad.append(f"{name} 的图例键集合与来源 {src} 不同：{sorted(obj_key)} != {sorted(key)}")
        # 每一格：要么与来源逐字相同，要么是点名的替换
        for ch, want in key.items():
            got = obj_key.get(ch)
            if ch in subs:
                if got != {"item": subs[ch]}:
                    bad.append(f"{name} 的图例 {ch} 应是 {subs[ch]}，实际 {got}")
            elif got != want:
                bad.append(f"{name} 的图例 {ch} 应与来源 {src} 一致（{want}），实际 {got}")
        # ③ 产物
        if obj.get("result") != {"id": f"{NS}:{METAL}_{gear}", "count": 1}:
            bad.append(f"{name} 的产物不是 {NS}:{METAL}_{gear} ×1：{obj.get('result')}")
        # ④ 反向：原版金属不许残留
        leftovers = [ch for ch, ing in obj_key.items()
                     if ing.get("item") in SUBSTITUTIONS]
        if leftovers:
            bad.append(f"{name} 还残留原版金属（{leftovers}）—— 换漏了就是免费金装")
        # ⑤ 至少一格混沌金材料（锭或块：重锤那格是块）
        if not any(ing.get("item") in METAL_ITEMS for ing in obj_key.values()):
            bad.append(f"{name} 里一格混沌金材料（{METAL_ITEMS}）都没有")
        # ⑦ 条件：只有乐事刀能带，且必须带；其余必须**没有** conditions
        conds = obj.get("neoforge:conditions")
        if gear == "knife":
            if conds != [FD_CONDITION]:
                bad.append(f"{name} 的 neoforge:conditions 不是恰好 mod_loaded(farmersdelight)：{conds}")
        elif conds is not None:
            bad.append(f"{name} 不该带 neoforge:conditions（只有乐事刀要挂）：{conds}")
        # ⑧ 1.7 第 ⑨ 条：四条改过的配方**逐项计数**必须等于作者给的数（位置由关卡逐格钉）
        want_counts = SHAPE_EXPECT.get(gear)
        if want_counts is not None:
            got_counts: dict[str, int] = {}
            for ch, ing in obj_key.items():
                per = sum(row.count(ch) for row in obj.get("pattern") or [])
                item_id = ing.get("item")
                if item_id is None:
                    bad.append(f"{name} 的图例 {ch} 不是具体物品（第 ⑨ 条的四件都逐格点名）：{ing!r}")
                    continue
                got_counts[item_id] = got_counts.get(item_id, 0) + per
            got_counts = {k: v for k, v in got_counts.items() if v}
            if got_counts != want_counts:
                bad.append(f"{name} 的逐项计数 {got_counts} ≠ 作者第 ⑨ 条给的 {want_counts}")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = targets()
    bad = check(files)
    # ★ 1.7 `bg-n10up`：上游两条（① 币串 → 3 币 / ② 币 →（烧炼）→ 粒）。第 3 条是既有配方，
    #   由 `generate_metal_recipes.py` 产出 ⇒ 这里**只核对**，不写盘（见 `check_upstream`）。
    up = upstream_targets()
    up_bad = check_upstream(up)
    written = 0
    for name, obj in files + up:
        text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
        json.loads(text)                      # 合法 JSON（不合法这里就抛）
        if args.apply:
            (RECIPES / name).write_text(text, encoding="utf-8", newline="\n")
            written += 1
    print(f"{'已写入' if args.apply else '演练'}: {written or (len(files) + len(up))} 条混沌金配方"
          f"（工作台 {len(GEAR)} 件 + 上游 {len(up)} 条；不生成 {len(EXCLUDED)} 件：{sorted(EXCLUDED)}）")
    print(f"配方自检失败: {len(bad)} {bad[:4]}")
    print(f"上游自检失败: {len(up_bad)} {up_bad[:4]}")
    if bad or up_bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
