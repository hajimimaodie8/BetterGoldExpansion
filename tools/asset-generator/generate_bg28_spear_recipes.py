#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1.8 阶段 3 · 段 0：14 件长矛的合成配方（作者 2026-11-19 批准）。

形状 = **与 SpearCore 官方矛同形**（读 `libs/spearcore-1.21.1-neo-3.2.1.jar` 里的
`data/spearcore/recipe/iron_spear.json` 逐格照抄）：

    "  a"      a = 对应材料（锭 / 原版下界合金锭 / 没用的老古董）
    " b "      b = minecraft:stick
    "b  "      成品 1 件

⚠ 官方下界合金矛是 `smithing_transform`，**不套用**到本模组的任何一件
（作者明确：13/14 族一律走「斜排 1 材料 + 2 棍」）。
⚠ 14 件（不是 13）：10 贵金属 + 混沌金 + 崩乱合金 + 古董 + 夜叉 —— 父代理 2026-11-19 已确认
「13 是笔误，按 14 做、一条都不许删」。

用法：`python tools/asset-generator/generate_bg28_spear_recipes.py`
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECIPES = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "recipe")

# (产物 id, a 的材料 id)
SPEARS = [
    ("sturdygold_spear", "bettergold:sturdygold_ingot"),
    ("flamegold_spear", "bettergold:flamegold_ingot"),
    ("windgold_spear", "bettergold:windgold_ingot"),
    ("thornsgold_spear", "bettergold:thornsgold_ingot"),
    ("echogold_spear", "bettergold:echogold_ingot"),
    ("frostgold_spear", "bettergold:frostgold_ingot"),
    ("indigoseagold_spear", "bettergold:indigoseagold_ingot"),
    ("voodoogold_spear", "bettergold:voodoogold_ingot"),
    ("thundergold_spear", "bettergold:thundergold_ingot"),
    ("illusiongold_spear", "bettergold:illusiongold_ingot"),
    ("chaosgold_spear", "bettergold:chaosgold_ingot"),
    ("chaosalloy_spear", "bettergold:chaosalloy_ingot"),
    # 不属于任何金属族的两件：材料 = 各自的修复材料（与 SpearRegistration 的 Stats 一致）
    ("antique_spear", "bettergold:unwanted_antique"),
    ("yaksha_spear", "minecraft:netherite_ingot"),
]


def payload(spear: str, material: str) -> dict:
    return {
        "type": "minecraft:crafting_shaped",
        "category": "equipment",
        "pattern": ["  a", " b ", "b  "],
        "key": {
            "a": {"item": material},
            "b": {"item": "minecraft:stick"},
        },
        "result": {"id": "bettergold:" + spear, "count": 1},
    }


def main() -> None:
    os.makedirs(RECIPES, exist_ok=True)
    for spear, material in SPEARS:
        path = os.path.join(RECIPES, spear + ".json")
        data = json.dumps(payload(spear, material), ensure_ascii=False, indent=2) + "\n"
        with open(path, "wb") as f:
            f.write(data.encode("utf-8"))
        print("wrote", os.path.relpath(path, ROOT))
    print("total", len(SPEARS))


if __name__ == "__main__":
    main()
