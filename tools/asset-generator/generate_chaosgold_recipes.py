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

11 件 vs 14 件（**逐件判定 + 依据**，见 `docs/1.7-混沌金与崩乱合金-需求立档.md` §20）
------------------------------------------------------------------------------------
| 件 | 原版来源（1.21.1 `data/minecraft/recipe/`） | 本轮的处置 |
|---|---|---|
| 剑 / 斧 / 镐 / 锹 / 锄 | `golden_*.json`（`X` = `gold_ingot`） | **工作台**，`X` → 混沌金锭 |
| 头盔 / 胸甲 / 护腿 / 靴子 | `golden_*.json`（`X` = `gold_ingot`） | **工作台**，`X` → 混沌金锭 |
| 盾牌 | `shield.json`（`o` = `iron_ingot`，`W` = `#minecraft:planks`） | **工作台**，`o` → 混沌金锭 |
| 弩 | `crossbow.json`（`&` = `iron_ingot`） | **工作台**，`&` → 混沌金锭 |
| **弓** | `bow.json` = **3 棍 + 3 线**，**一格金属都没有** | ✗ **不生成**（照字面会"零成本"合出混沌金弓）→ 待作者 |
| **三叉戟** | 原版**没有合成配方**（溺尸掉落 / 试炼密室） | ✗ **不生成**（没有"原版怎么合"可照）→ 待作者 |
| **重锤** | `mace.json` = **重核 + 微风棒**，没有锭 | ✗ **不生成**（"金属那一格"指哪一格说不清）→ 待作者 |
| **乐事小刀** | 不是原版：`farmersdelight:golden_knife` = `m` 锭 + `s` 棍（2 行） | ✗ **不生成**（作者说的是"原版"；且 14 件清单不含刀）→ 待作者 |

自检（不通过就 exit 1，别写半套）
---------------------------------
1. 每条都是合法 JSON，`type` = `crafting_shaped`、`category` = `equipment`、`count` = 1；
2. **逐格**：`pattern` + `key` 与 `VANILLA` 表（原版 JSON 的逐字抄本）**完全同形**，
   只有 `SUBSTITUTIONS` 里点名的那几个键的值被换成混沌金锭；
3. 产物 id = `bettergold:chaosgold_<件>`；
4. **反向**：key 里**不许**再出现 `minecraft:gold_ingot` / `minecraft:iron_ingot`（换漏了就是"免费金装"）；
5. 每件**至少 1 个**混沌金锭（否则它就不是混沌金装备的配方）；
6. 件数 = 11，且**恰好**是 `GEAR` 这 11 件（多一件 / 少一件都报）。
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
STICK = "minecraft:stick"
PLANKS = "minecraft:planks"          # 原版 shield 用的是 tag
STRING = "minecraft:string"
TRIPWIRE = "minecraft:tripwire_hook"

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

# 生成顺序（= 手册配方页顺序；稳定 ASCII，别随意重排）
GEAR = ["sword", "axe", "pickaxe", "shovel", "hoe",
        "helmet", "chestplate", "leggings", "boots", "shield", "crossbow"]

# **不生成**的 4 件 + 原因（关卡与文档都引用这张表，别在别处再写一份）
EXCLUDED: dict[str, str] = {
    "bow": "原版 bow.json = 3 棍 + 3 线，一格金属都没有 ⇒ 照字面会零成本合出混沌金弓",
    "trident": "原版没有三叉戟的合成配方（溺尸掉落 / 试炼密室）⇒ 无「原版怎么合」可照",
    "mace": "原版 mace.json = 重核 + 微风棒，没有锭 ⇒ 「金属那一格」指哪一格说不清",
    "knife": "乐事小刀不是原版物品（farmersdelight:golden_knife = 1 锭 + 1 棍）⇒ 超出「原版」口径",
}


def recipe(gear: str) -> dict:
    """一件混沌金装备的工作台配方：原版形状 + 金属格换成混沌金锭。"""
    _src, pattern, key = VANILLA[gear]
    new_key: dict[str, dict] = {}
    for ch, ing in key.items():
        if "item" in ing and ing["item"] in SUBSTITUTIONS:
            new_key[ch] = {"item": SUBSTITUTIONS[ing["item"]]}
        else:
            new_key[ch] = dict(ing)
    return {
        "type": "minecraft:crafting_shaped",
        "category": "equipment",
        "pattern": list(pattern),
        "key": new_key,
        "result": {"id": f"{NS}:{METAL}_{gear}", "count": 1},
    }


def targets() -> list[tuple[str, dict]]:
    return [(f"{METAL}_{gear}.json", recipe(gear)) for gear in GEAR]


def check(files: list[tuple[str, dict]]) -> list[str]:
    bad: list[str] = []
    if len(files) != len(GEAR):
        bad.append(f"生成的配方数不是 {len(GEAR)}（实际 {len(files)}）")
    got_gears = [name[len(METAL) + 1:-len(".json")] for name, _ in files]
    if got_gears != GEAR:
        bad.append(f"生成的件不是 GEAR 这 {len(GEAR)} 件：{got_gears}")
    for name, obj in files:
        gear = name[len(METAL) + 1:-len(".json")]
        if gear not in VANILLA:
            bad.append(f"{name} 不在 VANILLA 保真表里")
            continue
        src, pattern, key = VANILLA[gear]
        if obj.get("type") != "minecraft:crafting_shaped":
            bad.append(f"{name} 的 type 不是 crafting_shaped")
        if obj.get("category") != "equipment":
            bad.append(f"{name} 的 category 不是 equipment")
        # ② 逐格：pattern 必须与原版**逐字**相同（含空格 = 空格子）
        if obj.get("pattern") != list(pattern):
            bad.append(f"{name} 的 pattern 与原版 {src} 不同：{obj.get('pattern')} != {pattern}")
        obj_key = obj.get("key") or {}
        if sorted(obj_key) != sorted(key):
            bad.append(f"{name} 的图例键集合与原版 {src} 不同：{sorted(obj_key)} != {sorted(key)}")
        # 每一格：要么与原版逐字相同，要么是 SUBSTITUTIONS 里点名的替换
        for ch, want in key.items():
            got = obj_key.get(ch)
            if want.get("item") in SUBSTITUTIONS:
                if got != {"item": SUBSTITUTIONS[want["item"]]}:
                    bad.append(f"{name} 的图例 {ch} 应是 {SUBSTITUTIONS[want['item']]}，实际 {got}")
            elif got != want:
                bad.append(f"{name} 的图例 {ch} 应与原版 {src} 一致（{want}），实际 {got}")
        # ③ 产物
        if obj.get("result") != {"id": f"{NS}:{METAL}_{gear}", "count": 1}:
            bad.append(f"{name} 的产物不是 {NS}:{METAL}_{gear} ×1：{obj.get('result')}")
        # ④ 反向：金属不许残留
        leftovers = [ch for ch, ing in obj_key.items()
                     if ing.get("item") in SUBSTITUTIONS]
        if leftovers:
            bad.append(f"{name} 还残留原版金属（{leftovers}）—— 换漏了就是免费金装")
        # ⑤ 至少一个混沌金锭
        if not any(ing.get("item") == INGOT for ing in obj_key.values()):
            bad.append(f"{name} 里一个 {INGOT} 都没有")
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
