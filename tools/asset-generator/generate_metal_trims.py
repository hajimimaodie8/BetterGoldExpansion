#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金属族纹饰生成器 —— 为每种新金属生成盔甲纹饰材料（trim_material），
并补上色卡图集置换与 #minecraft:trim_materials 标签归属。

用法:
    python generate_metal_trims.py --apply

纹饰生效需要四样齐全（缺一个都不显示）：
    1. data/bettergold/trim_material/<asset>.json
    2. assets/bettergold/textures/trims/color_palettes/<asset>.png   （已由资产生成器放好）
    3. assets/minecraft/atlases/armor_trims.json 里的 permutations 条目
    4. #minecraft:trim_materials 物品标签
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "src" / "main" / "resources"
DATA = RES / "data"
TRIM_DIR = DATA / "bettergold" / "trim_material"
ATLAS = RES / "assets" / "minecraft" / "atlases" / "armor_trims.json"
TRIM_TAG = DATA / "minecraft" / "tags" / "item" / "trim_materials.json"
PALETTE_DIR = RES / "assets" / "bettergold" / "textures" / "trims" / "color_palettes"

METALS = ["flamegold", "voodoogold", "thundergold"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    src = TRIM_DIR / "sturdygold.json"
    if not src.is_file():
        print("[错误] 找不到模板 data/bettergold/trim_material/sturdygold.json")
        raise SystemExit(1)
    template = src.read_text(encoding="utf-8")

    missing_palette = [m for m in METALS if not (PALETTE_DIR / f"{m}.png").is_file()]

    # 1) 纹饰材质 JSON
    for metal in METALS:
        text = template.replace("sturdygold", metal)
        if args.apply:
            (TRIM_DIR / f"{metal}.json").write_text(text, encoding="utf-8", newline="\n")

    # 2) 色卡图集置换
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    perms = atlas.setdefault("sources", [{}])
    target = None
    for entry in atlas["sources"]:
        if "permutations" in entry:  # 图集里带 permutations 的那一段（不写死 type，避免结构差异）
            target = entry
            break
    if target is None:
        print("[错误] armor_trims.json 里没有 paletted_permutations")
        raise SystemExit(1)
    mapping = target.setdefault("permutations", {})
    added = []
    for metal in METALS:
        if metal not in mapping:
            mapping[metal] = f"bettergold:trims/color_palettes/{metal}"
            added.append(metal)
    if args.apply and added:
        ATLAS.write_text(json.dumps(atlas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 3) #minecraft:trim_materials
    tag = json.loads(TRIM_TAG.read_text(encoding="utf-8"))
    values = list(tag.get("values", []))
    tag_added = []
    for metal in METALS:
        value = f"bettergold:{metal}_ingot"
        if value not in values:
            values.append(value)
            tag_added.append(value)
    if args.apply and tag_added:
        tag["replace"] = False
        tag["values"] = values
        TRIM_TAG.write_text(json.dumps(tag, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"{'已写入' if args.apply else '演练'}: 纹饰材质 {len(METALS)} 个, "
          f"图集置换新增 {len(added)} 条 (共 {len(mapping)}), 标签新增 {len(tag_added)} 条")
    print(f"色卡缺失: {missing_palette if missing_palette else '无'}")


if __name__ == "__main__":
    main()
