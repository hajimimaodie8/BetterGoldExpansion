#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金属族资产生成器 —— 从作者给的素材压缩包，批量生成一套新金属的贴图 / 方块状态 / 模型。

用法:
    python generate_metal_assets.py --zip "E:\\mc\\mc资料\\更有用的金 新约6.zip" --apply

原理:
    万坚金(sturdygold)那一套的 blockstate / block model / item model 就是现成模板，
    新金属的贴图后缀与它完全一致（_block / _bricks / _pillar / _door_top / _trapdoor /
    _bars / _chain / _lantern ...），所以只要把模板文件名与内容里的 `sturdygold`
    整体替换成新金属 id，再按中文名把贴图改名拷过去即可。

加第 4 种金属: 在 METALS 里加一条（中文名 -> 英文 id），并在 SPECIAL_TEXTURES 里
补上它独有的材料/图标，然后重跑。
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "src" / "main" / "resources" / "assets" / "bettergold"
BASE_METAL = "sturdygold"  # 模板来源

# 每套金属: zip 里的中文文件夹名 -> 英文 id, 中文名（用于语言文件）
METALS = {
    "flamegold":    {"cn": "烈燃金", "folder": "烈燃金"},
    "voodoogold":   {"cn": "巫毒金", "folder": "巫毒金"},
    "thundergold":  {"cn": "结雷金", "folder": "结雷金"},
    "indigoseagold": {"cn": "靛海金", "folder": "靛海金"},
    "illusiongold": {"cn": "幻惑金", "folder": "幻惑金"},
}

# 中文名后缀 -> 目标路径(相对 assets/bettergold)。{id} 会替换成英文 id
#
# 命名坑（作者素材的写法不统一，两种都得列上）：
#   * 「门 物品」在靛海金里**有空格**（靛海金门 物品.png）、在幻惑金里**没空格**（幻惑金门物品.png）；
#   * 「链 物品」「灯笼 物品」两套都有空格；
#   * 新约7 的「纹饰色卡」放在各金属文件夹里（<中文名>纹饰色卡.png），
#     老压缩包里它在顶级目录「盔甲纹饰材料色卡/<中文名>.png」（两条路都留着）。
SUFFIX_MAP = {
    "锭":            "textures/item/{id}_ingot.png",
    "粒":            "textures/item/{id}_nugget.png",
    "原料":          "textures/item/raw_{id}.png",
    "块":            "textures/block/{id}_block.png",
    "砖块":          "textures/block/{id}_bricks.png",
    "柱":            "textures/block/{id}_pillar.png",
    "门 上":         "textures/block/{id}_door_top.png",
    "门 下":         "textures/block/{id}_door_bottom.png",
    "门 物品":       "textures/item/{id}_door.png",
    "门物品":        "textures/item/{id}_door.png",
    "活板门":        "textures/block/{id}_trapdoor.png",
    "栏杆":          "textures/block/{id}_bars.png",
    "链":            "textures/block/{id}_chain.png",
    "链 物品":       "textures/item/{id}_chain.png",
    "灯笼":          "textures/block/{id}_lantern.png",
    "灯笼 物品":     "textures/item/{id}_lantern.png",
    "剑":            "textures/item/{id}_sword.png",
    "斧":            "textures/item/{id}_axe.png",
    "镐":            "textures/item/{id}_pickaxe.png",
    "锹":            "textures/item/{id}_shovel.png",
    "锄":            "textures/item/{id}_hoe.png",
    "刀":            "textures/item/{id}_knife.png",
    "头盔":          "textures/item/{id}_helmet.png",
    "胸甲":          "textures/item/{id}_chestplate.png",
    "护腿":          "textures/item/{id}_leggings.png",
    "靴子":          "textures/item/{id}_boots.png",
    "盔甲1":         "textures/models/armor/{id}_layer_1.png",
    "盔甲2":         "textures/models/armor/{id}_layer_2.png",
    "升级锻造模板":  "textures/item/{id}_upgrade_template.png",
    "纹饰色卡":      "textures/trims/color_palettes/{id}.png",
}

# 各金属独有的材料与 buff 图标（zip 里没有金属名前缀）
SPECIAL_TEXTURES = {
    "flamegold":   {"高燃烈焰棒": "textures/item/blazing_rod.png",
                    "高燃": "textures/mob_effect/high_burn.png"},
    "voodoogold":  {"巫毒羽毛": "textures/item/voodoo_feather.png",
                    "巫毒": "textures/mob_effect/voodoo.png"},
    "thundergold": {"聚紫能晶尘": "textures/item/amethyst_energy_dust.png",
                    "颤栗": "textures/mob_effect/tremble.png"},
    "indigoseagold": {"靛蓝海洋之心": "textures/item/indigo_ocean_heart.png",
                      "沉淀": "textures/mob_effect/sediment.png"},
    "illusiongold": {"紫颂樱花枝": "textures/item/chorus_cherry_branch.png",
                     "安抚": "textures/mob_effect/soothe.png"},
}

# 纹饰色卡目录
PALETTE_DIR = "盔甲纹饰材料色卡"

# 灯笼贴图（16×48 动画帧序列）必须配的 .mcmeta，内容与 1.4 四套金属逐字一致
LANTERN_MCMETA = '{\n  "animation": {\n    "frametime": 8\n  }\n}\n'

# 只搬运"金属族"该有的资产，万坚金那些派/蛋糕/箱子之类的装饰不在此列
BLOCKSTATE_TEMPLATES = [
    "{m}_block", "{m}_bricks", "{m}_bricks_slab", "{m}_bricks_stairs", "{m}_bricks_wall",
    "{m}_pillar", "{m}_door", "{m}_trapdoor", "{m}_bars", "{m}_chain", "{m}_lantern",
]
BLOCK_MODEL_TEMPLATES = [
    "{m}_block", "{m}_bricks",
    "{m}_bricks_inner_stairs", "{m}_bricks_outer_stairs",
    "{m}_bricks_slab", "{m}_bricks_slab_double", "{m}_bricks_slab_top",
    "{m}_bricks_stairs",
    "{m}_bricks_wall_inventory", "{m}_bricks_wall_post",
    "{m}_bricks_wall_side", "{m}_bricks_wall_side_tall",
    "{m}_bars_cap", "{m}_bars_cap_alt", "{m}_bars_post", "{m}_bars_post_ends",
    "{m}_bars_side", "{m}_bars_side_alt",
    "{m}_chain",
    "{m}_door_bottom_left", "{m}_door_bottom_left_open",
    "{m}_door_bottom_right", "{m}_door_bottom_right_open",
    "{m}_door_top_left", "{m}_door_top_left_open",
    "{m}_door_top_right", "{m}_door_top_right_open",
    "{m}_lantern", "{m}_lantern_hanging",
    "{m}_pillar",
    "{m}_trapdoor_bottom", "{m}_trapdoor_open", "{m}_trapdoor_top",
]
ITEM_MODEL_TEMPLATES = [
    "raw_{m}", "{m}_ingot", "{m}_nugget",
    "{m}_block", "{m}_bricks", "{m}_bricks_slab", "{m}_bricks_stairs", "{m}_bricks_wall",
    "{m}_pillar", "{m}_door", "{m}_trapdoor", "{m}_bars", "{m}_chain", "{m}_lantern",
    "{m}_sword", "{m}_axe", "{m}_pickaxe", "{m}_shovel", "{m}_hoe", "{m}_knife",
    "{m}_helmet", "{m}_chestplate", "{m}_leggings", "{m}_boots",
    "{m}_upgrade_template",
]


def fail(msg: str) -> None:
    print(f"[错误] {msg}")
    sys.exit(1)


def read_zip_textures(zip_path: Path) -> dict[str, bytes]:
    """把压缩包里所有 png 读进内存: {完整条目名: 字节}"""
    out: dict[str, bytes] = {}
    with zipfile.ZipFile(zip_path) as z:
        for e in z.namelist():
            if e.lower().endswith(".png"):
                out[e] = z.read(e)
    return out


def write(path: Path, data: bytes | str, apply: bool, log: list[str], rel: Path) -> None:
    log.append(str(rel).replace("\\", "/"))
    if not apply:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8", newline="\n")
    else:
        path.write_bytes(data)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True, help="素材压缩包路径")
    ap.add_argument("--apply", action="store_true", help="真正写入（不加则只演练）")
    args = ap.parse_args()

    zip_path = Path(args.zip)
    if not zip_path.is_file():
        fail(f"找不到压缩包 {zip_path}")

    textures = read_zip_textures(zip_path)
    written: list[str] = []
    missing: list[str] = []
    unknown: list[str] = []

    for metal_id, meta in METALS.items():
        cn = meta["cn"]
        folder = meta["folder"]
        prefix = f"{folder}/"
        entries = {k[len(prefix):]: v for k, v in textures.items() if k.startswith(prefix)}
        lantern = False

        # 1) 贴图：按中文名后缀映射
        for name, data in sorted(entries.items()):
            stem = name[:-4]  # 去掉 .png
            suffix = stem[len(cn):] if stem.startswith(cn) else None
            special = SPECIAL_TEXTURES.get(metal_id, {})
            if stem in special:
                rel = Path(special[stem])
            elif suffix in SUFFIX_MAP:
                rel = Path(SUFFIX_MAP[suffix].format(id=metal_id))
            else:
                unknown.append(f"{folder}/{name}")
                continue
            write(ASSETS / rel, data, args.apply, written, rel)
            if str(rel).endswith("_lantern.png"):
                lantern = True

        # 1b) 灯笼贴图是 **16×48 的动画帧序列**（作者素材与 1.4 四套金属一致），
        #     必须配一份 .mcmeta 才会被图集当作动画；缺了它整张 16×48 会被静态采样，渲染纵向拉长。
        #     已存在（1.4 生成过的）就不动，避免无谓改写。
        lantern_rel = Path(f"textures/block/{metal_id}_lantern.png")
        lantern_mcmeta = Path(str(lantern_rel) + ".mcmeta")
        if (lantern or (ASSETS / lantern_rel).is_file()) and not (ASSETS / lantern_mcmeta).is_file():
            write(ASSETS / lantern_mcmeta, LANTERN_MCMETA, args.apply, written, lantern_mcmeta)

        # 1c) 专属材料的物品模型：1.4 的 blazing_rod / voodoo_feather / amethyst_energy_dust
        #     是手写的 models/item/<id>.json，忘了给新金属补就会在客户端刷
        #     「Unable to load model: bettergold:item/indigo_ocean_heart」并把物品渲染成紫黑格。
        #     这里按 SPECIAL_TEXTURES 里落在 textures/item/ 的那几条自动补标准 generated 模型；
        #     已存在的（1.4 手写的三条）原样不动。
        for special_name in [Path(p).stem for p in SPECIAL_TEXTURES.get(metal_id, {}).values()
                             if p.startswith("textures/item/")]:
            model_rel = Path("models/item") / f"{special_name}.json"
            if not (ASSETS / model_rel).is_file():
                text = ('{\n    "parent": "minecraft:item/generated",\n'
                        '    "textures": {\n'
                        f'        "layer0": "bettergold:item/{special_name}"\n'
                        '    }\n}\n')
                write(ASSETS / model_rel, text, args.apply, written, model_rel)

        # 2) 模板类 JSON：文件名与内容里的 sturdygold 整体替换
        for bucket, templates in (
            ("blockstates", BLOCKSTATE_TEMPLATES),
            ("models/block", BLOCK_MODEL_TEMPLATES),
            ("models/item", ITEM_MODEL_TEMPLATES),
        ):
            for tpl in templates:
                src_rel = Path(bucket) / (tpl.format(m=BASE_METAL) + ".json")
                dst_rel = Path(bucket) / (tpl.format(m=metal_id) + ".json")
                src = ASSETS / src_rel
                if not src.is_file():
                    missing.append(str(src_rel).replace("\\", "/"))
                    continue
                text = src.read_text(encoding="utf-8")
                text = text.replace(BASE_METAL, metal_id)
                write(ASSETS / dst_rel, text, args.apply, written, dst_rel)

    # 3) 纹饰色卡（两条路，缺一不生效的那四样之一）
    #    新约7 起色卡在各金属文件夹里（<中文名>纹饰色卡.png）→ 上面 SUFFIX_MAP 的「纹饰色卡」已经搬走；
    #    老压缩包把它放在顶级目录「盔甲纹饰材料色卡/<中文名>.png」→ 这里兼容。
    for metal_id, meta in METALS.items():
        if f"{meta['folder']}/{meta['cn']}纹饰色卡.png" in textures:
            continue                      # 新约7 起：色卡在金属文件夹里，SUFFIX_MAP 已经搬走
        if (ASSETS / f"textures/trims/color_palettes/{metal_id}.png").is_file():
            continue                      # 仓库里已经有这张色卡（1.4 生成的），不必再从包里取
        entry = f"{PALETTE_DIR}/{meta['cn']}.png"
        if entry in textures:
            rel = Path(f"textures/trims/color_palettes/{metal_id}.png")
            write(ASSETS / rel, textures[entry], args.apply, written, rel)
        else:
            missing.append(entry)

    print(f"{'已写入' if args.apply else '演练（未写入）'}: {len(written)} 个文件")
    for m, meta in METALS.items():
        n = sum(1 for w in written if m in w)
        print(f"  {meta['cn']:<6} {m:<12} {n} 个")
    if missing:
        print(f"[警告] 缺少模板/素材 {len(missing)} 个: {missing[:8]}")
    if unknown:
        print(f"[警告] 素材里未识别的文件 {len(unknown)} 个: {unknown[:8]}")
    if not missing and not unknown:
        print("全部模板与素材均已匹配。")


if __name__ == "__main__":
    main()
