#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金属族配方生成器 —— 从万坚金家族的配方复制出新金属的整条配方链。

用法:
    python generate_metal_recipes.py --apply

覆盖:
    原料熔炼/高炉、锭↔粒、锭↔块、砖块与台阶/楼梯/墙、栏杆/链/灯笼、门/活板门、柱、
    器具与盔甲的锻造升级、升级锻造模板自身的合成（金钱贝换成该金属专属材料）。
    乐事联动小刀那条配方等 FD 轮次再加（现在小刀物品还没注册）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RECIPES = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"

METALS = {
    "flamegold": "blazing_rod",
    "voodoogold": "voodoo_feather",
    "thundergold": "amethyst_energy_dust",
}

# 万坚金家族的配方模板（小刀那条留到 FD 轮次）
TEMPLATES = [
    "raw_sturdygold.json",
    "raw_sturdygold_smelting.json",
    "raw_sturdygold_blasting.json",
    "sturdygold_block_from_ingot.json",
    "sturdygold_ingot_from_block.json",
    "sturdygold_ingot_from_nugget.json",
    "sturdygold_nugget_from_ingot.json",
    "sturdygold_bricks_from_block.json",
    "sturdygold_bricks_slab.json",
    "sturdygold_bricks_stairs.json",
    "sturdygold_bricks_wall.json",
    "sturdygold_bars_from_ingot.json",
    "sturdygold_chain.json",
    "sturdygold_lantern.json",
    "sturdygold_door_from_ingot.json",
    "sturdygold_trapdoor_from_ingot.json",
    "craft_sturdygold_pillar.json",
    "sturdygold_upgrade_template.json",
    "smithing_sturdygold_sword.json",
    "smithing_sturdygold_axe.json",
    "smithing_sturdygold_pickaxe.json",
    "smithing_sturdygold_shovel.json",
    "smithing_sturdygold_hoe.json",
    "smithing_sturdygold_helmet.json",
    "smithing_sturdygold_chestplate.json",
    "smithing_sturdygold_leggings.json",
    "smithing_sturdygold_boots.json",
    "smithing_sturdygold_knife.json",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    written, missing = [], []
    for metal, special in METALS.items():
        for tpl in TEMPLATES:
            src = RECIPES / tpl
            if not src.is_file():
                missing.append(tpl)
                continue
            text = src.read_text(encoding="utf-8")
            # 升级模板配方：金钱贝换成该金属的专属材料
            if tpl == "sturdygold_upgrade_template.json":
                text = text.replace("bettergold:golden_cowrie", f"bettergold:{special}")
            # 注意：原料配方用的是本模组的自定义序列化器 bettergold:raw_sturdygold，
            # 那是"配方类型"不是物品 id，绝不能跟着改名（改了就报 Unknown recipe_serializer）。
            # 先把它保护起来，替换完再还原。
            guard = "@@RAW_RECIPE_TYPE@@"
            text = text.replace('"bettergold:raw_sturdygold"', f'"{guard}"')
            text = text.replace("sturdygold", metal)
            text = text.replace(guard, "bettergold:raw_sturdygold")
            dst = RECIPES / tpl.replace("sturdygold", metal)
            if args.apply:
                dst.write_text(text, encoding="utf-8", newline="\n")
            written.append(dst)

    print(f"{'已写入' if args.apply else '演练'}: {len(written)} 个配方文件"
          f"（{len(TEMPLATES)} 模板 × {len(METALS)} 套）")
    if missing:
        print(f"[警告] 缺模板: {sorted(set(missing))}")

    # 顺便校验所有新配方都是合法 JSON
    bad = []
    for p in written:
        if args.apply:
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                bad.append(f"{p.name}: {exc}")
    print(f"JSON 校验失败: {len(bad)} {bad[:3]}")


if __name__ == "__main__":
    main()
