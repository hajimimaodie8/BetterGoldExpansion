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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metal_forms as MF   # noqa: E402  「形态子集」的 Python 唯一真源（1.7 bg-n10）

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
    # 1.6（bg-16）：两套新金属。素材 = `更有用的金 新约9.zip`，仍然是「每套金属一个顶级文件夹」的布局。
    "thornsgold":   {"cn": "树棘金", "folder": "树棘金"},
    "echogold":     {"cn": "幽咆金", "folder": "幽咆金"},
    # 1.7（bg-n10 轮1 后半 / 轮2）：素材 = `更有用的金 新约10.zip`（归档副本在
    # `docs/新约10-素材清单/新约10/<中文名>/`）。⚠ 原始 zip 一个字节都不许动（立档 §0.2.1）
    # ⇒ 本轮用 `--from-dir` 读**归档副本**，连打开都不打开那个 zip。
    #   形态子集见 metal_forms.py：chaosgold 缺 raw/模板；chaosalloy 只有锭/块/模板。
    "chaosgold":    {"cn": "混沌金", "folder": "混沌金"},
    "chaosalloy":   {"cn": "崩乱合金", "folder": "崩乱合金"},
}

# 新约9 起，五类武器的贴图与「三叉戟实体 32×32 / 盾牌实体 64×64」放在**各自的金属文件夹**里
# （`树棘金/树棘金弓2.png` …），与本脚本的 SUFFIX_MAP 无关 —— 它们由 `generate_weapon_assets.py`
# 负责（那边有 bow/crossbow/trident/shield 的模型与 override 逻辑）。
# 这里显式跳过、不报"未识别"，**避免两处各写一份映射**（单点真源）。
WEAPON_SUFFIXES = {
    "重锤", "弓", "弓1", "弓2", "弓3", "弓4",
    "弩", "弩1", "弩2", "弩3", "弩4", "弩5", "弩6",
    "三叉戟", "三叉戟2", "盾牌",
    # 1.7（bg-n10 轮1 后半）：新约10 的三叉戟**物品图标**带一个空格（`混沌金三叉戟 物品.png`），
    # 与 `三叉戟`（32×32 实体贴图）不是同一张 ⇒ 必须也列进"由 generate_weapon_assets 负责"的
    # 跳过清单，否则会被报成"未识别的文件"（旧两批素材没有这种写法，故 1.4/1.6 都没列）。
    "三叉戟 物品",
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
    # 1.6（bg-16）：树棘金 = 闪耀藤条 + 寄生（buff 图标）；幽咆金 = 集束回响碎片 + 幽咆。
    # ⚠ 作者素材文件名是「音咆.png」（与本轮裁定的统一名「幽咆」不一致）——
    #   这里**只按作者的文件名取值**，落盘的目标名是我们自己的 `echo_roar`，不改作者的图/文件名。
    "thornsgold":   {"闪耀藤条": "textures/item/glittering_vine.png",
                     "寄生": "textures/mob_effect/parasite.png"},
    "echogold":     {"集束回响碎片": "textures/item/bundled_echo_shard.png",
                     "音咆": "textures/mob_effect/echo_roar.png"},
    # 1.7（bg-n10 轮1 后半 / 轮2）：这批的「专属」不是药材而是**尚未注册的后续轮次物品**
    # （混沌金币已注册 = chaosgold 的 coreItem；禁果/附魔书属轮4，两失衡图标属轮7）
    # ⇒ 映射照样登记（贴图已在 src 里，逐个核对过字节一致），**物品注册**由各自轮次做。
    "chaosgold":    {"混沌金币": "textures/item/chaos_coin.png",
                     "混沌金禁果": "textures/item/chaosgold_forbidden_fruit.png",
                     "混沌金附魔书": "textures/item/chaosgold_enchanting_book.png"},
    "chaosalloy":   {"崩乱禁果": "textures/item/chaosalloy_forbidden_fruit.png",
                     "力量失衡": "textures/mob_effect/power_imbalance.png",
                     "抗性失衡": "textures/mob_effect/resistance_imbalance.png"},
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

# --------------------------------------------------------------------------------------
# 1.7（bg-n10 轮1 后半）：**形态子集**（metal_forms.py 的 Python 唯一真源）
# --------------------------------------------------------------------------------------
# 没声明某形态的族**不产出**该形态的模板/贴图 —— 否则会留下引用不存在物品的
# blockstate / model / 战利品表（客户端紫黑格、标签"必需条目缺失"整张被丢弃）。
# 下面这张表把"模板名 / 贴图后缀"映射回形态；**表里没有的 = 器具 / 武器 / 盔甲**
# （它们恒定注册，不受形态子集影响）。
TEMPLATE_FORM = {
    "raw": "raw", "ingot": "ingot", "nugget": "nugget", "block": "block",
    "bricks": "bricks",
    "bricks_inner_stairs": "bricks_stairs", "bricks_outer_stairs": "bricks_stairs",
    "bricks_stairs": "bricks_stairs",
    "bricks_slab": "bricks_slab", "bricks_slab_double": "bricks_slab", "bricks_slab_top": "bricks_slab",
    "bricks_wall_inventory": "bricks_wall", "bricks_wall_post": "bricks_wall",
    "bricks_wall_side": "bricks_wall", "bricks_wall_side_tall": "bricks_wall",
    # ⚠ 下面这 4 个**裸名**是 1.7 实测漏掉的（`{m}_bars` / `{m}_door` / `{m}_trapdoor` /
    #   `{m}_bricks_wall` 在 blockstate 与 item 模板里都是裸名，不带 `_side` / `_bottom` 后缀）——
    #   漏了它们 ⇒ `template_form()` 返回 None ⇒ 当成"武器/盔甲、恒产出"⇒ 崩乱合金多出 4 件细节件。
    #   本仓关卡 `[bgn10-forms-assets]` 正是在做完之后把这条抓出来的（第二形态的"生成器不等于全覆盖"）。
    "bricks_wall": "bricks_wall",
    "bars": "bars",
    "door": "door",
    "trapdoor": "trapdoor",
    "pillar": "pillar",
    "bars_cap": "bars", "bars_cap_alt": "bars", "bars_post": "bars", "bars_post_ends": "bars",
    "bars_side": "bars", "bars_side_alt": "bars",
    "chain": "chain",
    "door_bottom_left": "door", "door_bottom_left_open": "door", "door_bottom_right": "door",
    "door_bottom_right_open": "door", "door_top_left": "door", "door_top_left_open": "door",
    "door_top_right": "door", "door_top_right_open": "door",
    "trapdoor_bottom": "trapdoor", "trapdoor_open": "trapdoor", "trapdoor_top": "trapdoor",
    "lantern": "lantern", "lantern_hanging": "lantern",
    "upgrade_template": "upgrade_template",
}

# SUFFIX_MAP 的键 → 形态（**只在贴图侧**用；表里没有的键 = 武器/盔甲/专属材料，恒放行）
SUFFIX_FORM = {
    "锭": "ingot", "粒": "nugget", "原料": "raw", "块": "block",
    "砖块": "bricks", "柱": "pillar",
    "门 上": "door", "门 下": "door", "门 物品": "door", "门物品": "door",
    "活板门": "trapdoor", "栏杆": "bars", "链": "chain", "链 物品": "chain",
    "灯笼": "lantern", "灯笼 物品": "lantern",
    "升级锻造模板": "upgrade_template",
}


def template_form(tpl: str) -> str | None:
    """模板串（含 {m} / raw_{m}）→ 它所属的形态；None = 不属于任何形态（武器 / 盔甲）"""
    name = tpl.replace("raw_{m}", "raw").replace("{m}_", "").replace("{m}", "")
    return TEMPLATE_FORM.get(name)


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


def read_dir_textures(root: Path) -> dict[str, bytes]:
    """
    把**已解压的归档副本**读进内存（1.7 bg-n10 轮1 后半新增）。

    条目名 = 相对路径（`<中文名>/<文件名>.png`），与 zip 布局逐字一致 ⇒ 下游代码不用改。
    ⚠ 只读：归档目录一个字节都不许写（立档 §0.2.1「归档副本只增不改」）。
    """
    out: dict[str, bytes] = {}
    for p in sorted(root.rglob("*.png")):
        out[p.relative_to(root).as_posix()] = p.read_bytes()
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
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--zip", help="素材压缩包路径（**只读**打开；原始 zip 绝不许改）")
    src.add_argument("--from-dir", help="已解压的素材目录（1.7 bg-n10 起；只读）")
    ap.add_argument("--apply", action="store_true", help="真正写入（不加则只演练）")
    args = ap.parse_args()

    if args.zip:
        zip_path = Path(args.zip)
        if not zip_path.is_file():
            fail(f"找不到压缩包 {zip_path}")
        textures = read_zip_textures(zip_path)
    else:
        root = Path(args.from_dir)
        if not root.is_dir():
            fail(f"找不到素材目录 {root}")
        textures = read_dir_textures(root)
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
            elif suffix in WEAPON_SUFFIXES:
                # 五类武器（含三叉戟实体 / 盾牌实体）：由 generate_weapon_assets.py 负责，见上方常量注释
                continue
            elif suffix in SUFFIX_MAP:
                # 形态子集：该族没声明的形态**不落贴图**（表里没有的后缀 = 武器/盔甲，恒放行）
                form = SUFFIX_FORM.get(suffix)
                if form is not None and not MF.has(metal_id, form):
                    continue
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
                # 形态子集（1.7 bg-n10 轮1 后半）：没声明的形态不产出模板（None = 武器/盔甲，恒产出）
                tpl_form = template_form(tpl)
                if tpl_form is not None and not MF.has(metal_id, tpl_form):
                    continue
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
