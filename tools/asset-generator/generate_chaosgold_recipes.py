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
    "shield": ("shield.json", ["WoW", "WWW", " W "], {
        "W": {"tag": PLANKS}, "o": {"item": "minecraft:iron_ingot"}}),
    # 原版弩：2 棍 + 1 铁锭 + 1 线 + 3 绊线钩 ⇒ 只换铁锭那一格
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
    "mace": {
        "source": "data/minecraft/recipe/mace.json",
        "pattern": [" # ", " I "],
        "key": {"#": {"item": HEAVY_CORE}, "I": {"item": BREEZE_ROD}},
        "subs": {"#": BLOCK},                     # 重核 → 混沌金块（⚠ 是块，不是锭）
        "condition": None,
        "original_shape": False,
        "note": "原版形状逐字；金属格 = 重核那一格 → 混沌金块（1 块 + 1 微风棒）",
    },
    "trident": {
        "source": "（原版没有 trident.json —— 本形状是原创）",
        "pattern": ["XXX", " X ", " # "],
        "key": {"X": {"item": INGOT}, "#": {"item": STICK}},
        "subs": {},                               # 表里本来就写着混沌金锭，没有替换
        "condition": None,
        "original_shape": True,
        "note": "原创形状（不是原版形状，原版没有三叉戟配方）：上排 3 锭 + 中列再 1 锭 + 底部 1 棍",
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
    return bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = targets()
    bad = check(files)
    written = 0
    for name, obj in files:
        text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
        json.loads(text)                      # 合法 JSON（不合法这里就抛）
        if args.apply:
            (RECIPES / name).write_text(text, encoding="utf-8", newline="\n")
            written += 1
    print(f"{'已写入' if args.apply else '演练'}: {written or len(files)} 条混沌金工作台配方"
          f"（{len(GEAR)} 件；不生成 {len(EXCLUDED)} 件：{sorted(EXCLUDED)}）")
    print(f"配方自检失败: {len(bad)} {bad[:4]}")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
