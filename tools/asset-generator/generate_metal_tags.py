#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金属族标签生成器 —— 把新金属并入家族标签、通用标签桥接与原版类别标签。

用法:
    python generate_metal_tags.py --apply

要点:
    * 家族标签（bettergold:ingots / nuggets / raw_materials / storage_blocks）只在这里加一次，
      c:ingots / c:nuggets / c:raw_materials / c:storage_blocks / minecraft:beacon_payment_items /
      minecraft:mineable/pickaxe 会自动跟着有（那些文件里写的是 "#bettergold:xxx"）。
    * 1.21 的 #minecraft:enchantable/* 全部由类别标签拼出 —— 器具不进 swords/pickaxes/... 就附不了魔；
      盔甲不进 head/chest/leg/foot_armor 则既不能附魔也不能打纹饰。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "src" / "main" / "resources" / "data"

METALS = ["flamegold", "voodoogold", "thundergold"]
BLOCKS = ["block", "bricks", "bricks_slab", "bricks_stairs", "bricks_wall",
          "pillar", "door", "trapdoor", "bars", "chain", "lantern"]
TOOLS = {"swords": "sword", "pickaxes": "pickaxe", "axes": "axe", "shovels": "shovel", "hoes": "hoe"}
ARMOR = {"head_armor": "helmet", "chest_armor": "chestplate", "leg_armor": "leggings", "foot_armor": "boots"}

# 目标文件 -> 要并入的物品/方块 id 列表
def build_plan() -> dict[Path, list[str]]:
    plan: dict[Path, list[str]] = {}

    def add(path: Path, values: list[str]) -> None:
        plan.setdefault(path, []).extend(values)

    for m in METALS:
        add(DATA / "bettergold" / "tags" / "item" / "ingots.json", [f"bettergold:{m}_ingot"])
        add(DATA / "bettergold" / "tags" / "item" / "nuggets.json", [f"bettergold:{m}_nugget"])
        add(DATA / "bettergold" / "tags" / "item" / "raw_materials.json", [f"bettergold:raw_{m}"])
        add(DATA / "bettergold" / "tags" / "item" / "storage_blocks.json", [f"bettergold:{m}_block"])
        add(DATA / "bettergold" / "tags" / "block" / "storage_blocks.json", [f"bettergold:{m}_block"])

        for tag, suffix in TOOLS.items():
            add(DATA / "minecraft" / "tags" / "item" / f"{tag}.json", [f"bettergold:{m}_{suffix}"])
        for tag, suffix in ARMOR.items():
            add(DATA / "minecraft" / "tags" / "item" / f"{tag}.json", [f"bettergold:{m}_{suffix}"])

        add(DATA / "minecraft" / "tags" / "block" / "mineable" / "pickaxe.json",
            [f"bettergold:{m}_{b}" for b in BLOCKS])
        add(DATA / "minecraft" / "tags" / "block" / "needs_diamond_tool.json",
            [f"bettergold:{m}_{b}" for b in BLOCKS])
        add(DATA / "minecraft" / "tags" / "block" / "walls.json", [f"bettergold:{m}_bricks_wall"])
        add(DATA / "minecraft" / "tags" / "block" / "beacon_base_blocks.json",
            [f"bettergold:{m}_block", f"bettergold:{m}_bricks"])
    return plan


def merge(path: Path, values: list[str], apply: bool) -> tuple[int, int]:
    """把 values 并入标签文件（保持 replace:false 与原有条目顺序）"""
    if path.is_file():
        obj = json.loads(path.read_text(encoding="utf-8"))
        current = list(obj.get("values", []))
    else:
        obj, current = {"replace": False, "values": []}, []
    added = [v for v in values if v not in current]
    if added:
        obj["replace"] = False
        obj["values"] = current + added
        if apply:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8", newline="\n")
    return len(added), len(current) + len(added)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    plan = build_plan()
    total_added = 0
    for path, values in sorted(plan.items(), key=lambda kv: str(kv[0])):
        added, size = merge(path, values, args.apply)
        total_added += added
        rel = path.relative_to(DATA)
        flag = "" if added else "  (已是最新)"
        print(f"{str(rel):<58} +{added:<3} 共 {size}{flag}")
    print(f"{'已写入' if args.apply else '演练'}: 共新增 {total_added} 条标签归属")


if __name__ == "__main__":
    main()
