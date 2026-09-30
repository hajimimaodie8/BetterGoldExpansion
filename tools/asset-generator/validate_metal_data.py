#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验：MetalFamily 会注册出来的每个物品/方块，在 zh_cn / en_us 里是否都有语言条目。"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LANG = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang"

METALS = ["flamegold", "voodoogold", "thundergold"]
ITEMS = ["ingot", "nugget", "sword", "axe", "pickaxe", "shovel", "hoe", "helmet", "chestplate",
         "leggings", "boots", "upgrade_template"]
RAW = ["raw_{m}"]
BLOCKS = ["block", "bricks", "bricks_slab", "bricks_stairs", "bricks_wall", "pillar", "door",
          "trapdoor", "bars", "chain", "lantern"]
TEMPLATE_KEYS = ["applies_to", "ingredients", "upgrade_description",
                 "base_slot_description", "additions_slot_description"]
SPECIAL = ["blazing_rod", "voodoo_feather", "amethyst_energy_dust"]
EFFECTS = ["high_burn", "voodoo", "tremble"]

zh = json.loads((LANG / "zh_cn.json").read_text(encoding="utf-8"))
en = json.loads((LANG / "en_us.json").read_text(encoding="utf-8"))

missing_zh, missing_en, checked = [], [], 0
for m in METALS:
    ids = [f"{m}_{s}" for s in ITEMS] + [f"raw_{m}"]
    for i in ids:
        key = f"item.bettergold.{i}"
        checked += 1
        if key not in zh:
            missing_zh.append(key)
        if key not in en:
            missing_en.append(key)
    for b in BLOCKS:
        key = f"block.bettergold.{m}_{b}"
        checked += 1
        if key not in zh:
            missing_zh.append(key)
        if key not in en:
            missing_en.append(key)
    for t in TEMPLATE_KEYS:
        key = f"item.bettergold.smithing_template.{m}_upgrade.{t}"
        checked += 1
        if key not in zh:
            missing_zh.append(key)
        if key not in en:
            missing_en.append(key)

for s in SPECIAL:
    checked += 1
    if f"item.bettergold.{s}" not in zh:
        missing_zh.append(f"item.bettergold.{s}")
    if f"item.bettergold.{s}" not in en:
        missing_en.append(f"item.bettergold.{s}")

for e in EFFECTS:
    checked += 1
    if f"effect.bettergold.{e}" not in zh:
        missing_zh.append(f"effect.bettergold.{e}")
    if f"effect.bettergold.{e}" not in en:
        missing_en.append(f"effect.bettergold.{e}")

print(f"检查语言键 {checked} 个（对应 3 套金属的全部物品与方块）")
print(f"缺中文: {len(missing_zh)} {missing_zh[:8]}")
print(f"缺英文: {len(missing_en)} {missing_en[:8]}")

# 顺带检查战利品表
loot_dir = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "loot_table" / "blocks"
missing_loot = [f"{m}_{b}" for m in METALS for b in BLOCKS if not (loot_dir / f"{m}_{b}.json").is_file()]
print(f"缺战利品表: {len(missing_loot)} {missing_loot[:8]}")
sys.exit(1 if (missing_zh or missing_en or missing_loot) else 0)
