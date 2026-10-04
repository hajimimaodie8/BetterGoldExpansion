#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金属族数据生成器 —— 为新金属批量生成：语言条目、方块战利品表、标签归属。

用法:
    python generate_metal_data.py --apply

说明:
    * 语言：以文本方式往 zh_cn.json / en_us.json 末尾插入条目（不改动原有排版）。
    * 战利品表：从万坚金的 11 张家族战利品表复制改名。
    * 标签：把新金属的锭/粒/原料/材料块写进家族标签，并把器具与盔甲加进原版类别标签
      （1.21 的 enchantable/* 由类别标签拼出，不加就附不了魔）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "src" / "main" / "resources"
DATA = RES / "data"
LANG = RES / "assets" / "bettergold" / "lang"

METALS = {
    "flamegold":   {"cn": "烈燃金", "en": "Flamegold",   "special_cn": "高燃烈焰棒", "special_en": "Blazing Rod",        "special_id": "blazing_rod"},
    "voodoogold":  {"cn": "巫毒金", "en": "Voodoogold",  "special_cn": "巫毒羽毛",   "special_en": "Voodoo Feather",     "special_id": "voodoo_feather"},
    "thundergold": {"cn": "结雷金", "en": "Thundergold", "special_cn": "聚紫能晶尘", "special_en": "Amethyst Energy Dust", "special_id": "amethyst_energy_dust"},
    "indigoseagold": {"cn": "靛海金", "en": "Indigoseagold", "special_cn": "靛蓝海洋之心", "special_en": "Indigo Ocean Heart",  "special_id": "indigo_ocean_heart"},
    "illusiongold":  {"cn": "幻惑金", "en": "Illusiongold",  "special_cn": "紫颂樱花枝",   "special_en": "Chorus Cherry Branch", "special_id": "chorus_cherry_branch"},
    # 1.6（bg-16）：树棘金（核心材料 = 闪耀藤条，掉落物）/ 幽咆金（核心材料 = 集束回响碎片，合成）。
    "thornsgold":    {"cn": "树棘金", "en": "Thornsgold",   "special_cn": "闪耀藤条",     "special_en": "Glittering Vine",     "special_id": "glittering_vine"},
    "echogold":      {"cn": "幽咆金", "en": "Echogold",     "special_cn": "集束回响碎片", "special_en": "Bundled Echo Shard",  "special_id": "bundled_echo_shard"},
}

# 物品 id 后缀 -> (中文模板, 英文模板)
ITEM_NAMES = {
    "ingot": ("{cn}锭", "{en} Ingot"),
    "nugget": ("{cn}粒", "{en} Nugget"),
    "raw": ("{cn}原料", "Raw {en}"),
    "sword": ("{cn}剑", "{en} Sword"),
    "axe": ("{cn}斧", "{en} Axe"),
    "pickaxe": ("{cn}镐", "{en} Pickaxe"),
    "shovel": ("{cn}锹", "{en} Shovel"),
    "hoe": ("{cn}锄", "{en} Hoe"),
    "knife": ("{cn}刀", "{en} Knife"),
    "helmet": ("{cn}头盔", "{en} Helmet"),
    "chestplate": ("{cn}胸甲", "{en} Chestplate"),
    "leggings": ("{cn}护腿", "{en} Leggings"),
    "boots": ("{cn}靴子", "{en} Boots"),
    "upgrade_template": ("{cn}升级锻造模板", "{en} Upgrade Smithing Template"),
    "block": ("{cn}块", "{en} Block"),
    "bricks": ("{cn}砖块", "{en} Bricks"),
    "bricks_slab": ("{cn}砖台阶", "{en} Brick Slab"),
    "bricks_stairs": ("{cn}砖楼梯", "{en} Brick Stairs"),
    "bricks_wall": ("{cn}砖墙", "{en} Brick Wall"),
    "pillar": ("{cn}柱", "{en} Pillar"),
    "door": ("{cn}门", "{en} Door"),
    "trapdoor": ("{cn}活板门", "{en} Trapdoor"),
    "bars": ("{cn}栏杆", "{en} Bars"),
    "chain": ("{cn}链", "{en} Chain"),
    "lantern": ("{cn}灯笼", "{en} Lantern"),
}
BLOCK_SUFFIXES = ["block", "bricks", "bricks_slab", "bricks_stairs", "bricks_wall",
                  "pillar", "door", "trapdoor", "bars", "chain", "lantern"]

EFFECT_NAMES = {
    "high_burn": ("高燃", "High Burn"),
    "voodoo": ("巫毒", "Voodoo"),
    "tremble": ("颤栗", "Tremble"),
    "sediment": ("沉淀", "Sediment"),
    "soothe": ("安抚", "Soothe"),
    # 1.6（bg-16）：树棘金 / 幽咆金 的专属 buff。
    # ⚠ 效果 id 用英文（parasite / echo_roar），中文名按作者裁定统一叫「幽咆」
    #   （作者素材里的文件名是「音咆.png」，这里只取图、不改名）。
    "parasite": ("寄生", "Parasite"),
    "echo_roar": ("幽咆", "Echo Roar"),
}


def insert_lang(path: Path, entries: dict[str, str], apply: bool) -> int:
    """按文本插入到 JSON 末尾，保持原有格式"""
    text = path.read_text(encoding="utf-8")
    existing = set(re.findall(r'"([^"]+)"\s*:', text))
    fresh = {k: v for k, v in entries.items() if k not in existing}
    if not fresh:
        return 0
    body = ",\n".join(f'  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}'
                      for k, v in fresh.items())
    idx = text.rstrip().rfind("}")
    new_text = text[:idx].rstrip()
    if not new_text.endswith("{"):
        new_text += ","
    new_text += "\n" + body + "\n}\n"
    if apply:
        path.write_text(new_text, encoding="utf-8", newline="\n")
    return len(fresh)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    zh, en = {}, {}
    loot_files = []
    copied_loot = 0

    for mid, meta in METALS.items():
        cn, en_name = meta["cn"], meta["en"]
        # ---------- 语言 ----------
        zh[f"item.bettergold.{meta['special_id']}"] = meta["special_cn"]
        en[f"item.bettergold.{meta['special_id']}"] = meta["special_en"]
        for suffix, (z, e) in ITEM_NAMES.items():
            item_id = f"raw_{mid}" if suffix == "raw" else f"{mid}_{suffix}"
            key = f"{'block' if suffix in BLOCK_SUFFIXES else 'item'}.bettergold.{item_id}"
            zh[key] = z.format(cn=cn)
            en[key] = e.format(en=en_name)
        # 升级模板的 5 条说明（键名与万坚金一致）
        base = f"item.bettergold.smithing_template.{mid}_upgrade."
        zh[base + "applies_to"] = "金装备"
        en[base + "applies_to"] = "Golden Gear"
        zh[base + "ingredients"] = f"{cn}锭"
        en[base + "ingredients"] = f"{en_name} Ingot"
        zh[base + "upgrade_description"] = f"{cn}升级"
        en[base + "upgrade_description"] = f"{en_name} Upgrade"
        zh[base + "base_slot_description"] = "放入金制盔甲、武器或工具"
        en[base + "base_slot_description"] = "Put golden armor, weapons or tools"
        zh[base + "additions_slot_description"] = f"放入{cn}锭"
        en[base + "additions_slot_description"] = f"Put a {en_name} Ingot"

        # 盔甲纹饰材料名（generate_metal_trims.py 生成的 trim_material JSON 的 description 用它；
        # 1.4 的三条是手写的，这里补上自动化：已有的会被 insert_lang 跳过）
        zh[f"trim_material.bettergold.{mid}"] = f"{cn}质"
        en[f"trim_material.bettergold.{mid}"] = en_name

        # ---------- 战利品表：复制万坚金的 11 张 ----------
        for suffix in BLOCK_SUFFIXES:
            src = DATA / "bettergold" / "loot_table" / "blocks" / f"sturdygold_{suffix}.json"
            if not src.is_file():
                print(f"[警告] 缺少战利品表模板 {src.name}")
                continue
            text = src.read_text(encoding="utf-8").replace("sturdygold", mid)
            dst = DATA / "bettergold" / "loot_table" / "blocks" / f"{mid}_{suffix}.json"
            loot_files.append(dst)
            if args.apply:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(text, encoding="utf-8", newline="\n")
            copied_loot += 1

    for eid, (z, e) in EFFECT_NAMES.items():
        zh[f"effect.bettergold.{eid}"] = z
        en[f"effect.bettergold.{eid}"] = e

    z_zh = insert_lang(LANG / "zh_cn.json", zh, args.apply)
    z_en = insert_lang(LANG / "en_us.json", en, args.apply)
    print(f"{'已写入' if args.apply else '演练'}: 中文条目 {z_zh} 条, 英文条目 {z_en} 条, 战利品表 {copied_loot} 张")
    if not args.apply:
        print("（加 --apply 才会真正写盘）")


if __name__ == "__main__":
    main()
