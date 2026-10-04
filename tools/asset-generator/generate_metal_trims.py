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
    3. **两份图集置换**：
       a. assets/minecraft/atlases/armor_trims.json —— 穿戴在身上的模型用
          （`trims/models/armor/<pattern>_<asset>`，源贴图是原版 36 张 `trims/models/armor/*`）；
       b. assets/minecraft/atlases/blocks.json —— **物品形态的纹饰**用
          （`trims/items/<部位>_trim_<asset>`，源贴图是原版 4 张 `trims/items/*_trim`）。
       只补 a 不补 b，表现就是「穿在身上有颜色、背包里的盔甲纹饰不显示/显示成白色」——
       1.5 修正⑦ 的真因之一。
    4. #minecraft:trim_materials 物品标签

另外 `item_model_index` 必须**互不相同**且**不要落在原版 0.1~1.0 上**：
该值就是物品属性 `minecraft:trim_type` 的返回值，原版盔甲物品模型的 `overrides` 是一张
「0.1→quartz、0.2→iron … 1.0→amethyst」的表，撞上去就会显示成那个原版材质的颜色
（六个金属原来都是 0.1 = quartz = 白灰阶，作者看到的「纹饰都是白色」就是这个）。
本生成器按 ITEM_MODEL_INDEX 表写入 0.01~0.07（都在原版区间之下）。
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
# 物品形态纹饰用的图集（1.5 修正⑦ 新增）：源贴图是原版 4 张 trims/items/*_trim
ITEMS_ATLAS = RES / "assets" / "minecraft" / "atlases" / "blocks.json"
ITEM_TRIM_TEXTURES = [
    "trims/items/helmet_trim",
    "trims/items/chestplate_trim",
    "trims/items/leggings_trim",
    "trims/items/boots_trim",
]
TRIM_TAG = DATA / "minecraft" / "tags" / "item" / "trim_materials.json"
PALETTE_DIR = RES / "assets" / "bettergold" / "textures" / "trims" / "color_palettes"

METALS = ["flamegold", "voodoogold", "thundergold", "indigoseagold", "illusiongold",
          # 1.6（bg-16）：两套新金属（纹饰四样由这个生成器一次补齐）
          "thornsgold", "echogold"]

# item_model_index：必须互不相同、且避开原版 0.1~1.0（见文件头说明）
ITEM_MODEL_INDEX = {
    "sturdygold": 0.01,
    "unwanted_antique": 0.02,
    "flamegold": 0.03,
    "voodoogold": 0.04,
    "thundergold": 0.05,
    "indigoseagold": 0.06,
    "illusiongold": 0.07,
    # 1.6：接着往下取，仍然全部落在原版 0.1~1.0 **之外**
    "thornsgold": 0.08,
    "echogold": 0.09,
}


def add_permutations(atlas_path: Path, textures: list[str], metals: list[str]):
    """给一份图集（新建或追加）补 paletted_permutations 源，返回（新增条数, 需要写的路径或 None, 图集内容）"""
    if atlas_path.is_file():
        atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    else:
        atlas = {"sources": []}
    sources = atlas.setdefault("sources", [])
    target = None
    for entry in sources:
        if "permutations" in entry:
            target = entry
            break
    created = False
    if target is None:
        target = {
            "type": "paletted_permutations",
            "textures": list(textures),
            "palette_key": "trims/color_palettes/trim_palette",
            "permutations": {},
        }
        sources.append(target)
        created = True
    mapping = target.setdefault("permutations", {})
    added = 0
    for metal in metals:
        if metal not in mapping:
            mapping[metal] = f"bettergold:trims/color_palettes/{metal}"
            added += 1
    return added, (atlas_path if (added or created) else None), atlas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    src = TRIM_DIR / "sturdygold.json"
    if not src.is_file():
        print("[错误] 找不到模板 data/bettergold/trim_material/sturdygold.json")
        raise SystemExit(1)

    missing_palette = [m for m in METALS if not (PALETTE_DIR / f"{m}.png").is_file()]

    # 1) 纹饰材质 JSON（item_model_index 逐个不同，避开原版 0.1~1.0）
    template = json.loads(src.read_text(encoding="utf-8"))
    order = ["asset_name", "description", "ingredient", "item_model_index"]
    for metal in METALS:
        data = json.loads(json.dumps(template))
        data["asset_name"] = metal
        data["ingredient"] = f"bettergold:{metal}_ingot"
        data["description"] = {
            "color": data["description"]["color"],
            "translate": f"trim_material.bettergold.{metal}",
        }
        data["item_model_index"] = ITEM_MODEL_INDEX[metal]
        out = {k: data[k] for k in order if k in data}
        if args.apply:
            (TRIM_DIR / f"{metal}.json").write_text(
                json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # 2) 色卡图集置换：a) 穿戴模型用的 armor_trims   b) 物品形态用的 blocks
    added_armor, write_armor, atlas_armor = add_permutations(ATLAS, [], METALS)
    added_items, write_items, atlas_items = add_permutations(ITEMS_ATLAS, ITEM_TRIM_TEXTURES, METALS)
    if args.apply and write_armor is not None:
        ATLAS.write_text(json.dumps(atlas_armor, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
    if args.apply and write_items is not None:
        ITEMS_ATLAS.write_text(json.dumps(atlas_items, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8", newline="\n")
    added = added_armor + added_items

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
          f"图集置换新增 {added} 条 (armor_trims +{added_armor} / blocks +{added_items}), "
          f"标签新增 {len(tag_added)} 条")
    print(f"色卡缺失: {missing_palette if missing_palette else '无'}")


if __name__ == "__main__":
    main()
