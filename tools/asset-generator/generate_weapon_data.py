#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1.5 武器轮数据生成器 —— 五类 × 六金属的锻造升级配方（联动 MUT 的条件配方）+ 附魔类别标签。

用法:
    python generate_weapon_data.py            # 演练
    python generate_weapon_data.py --apply    # 写入（并删除已作废的旧配方文件）

================================================================================
bg-15w（2026-10-02）第 8 项 + **续工轮 §3.8 口径改正**：胚底「检测到装了 mut 才隐藏」
================================================================================
作者原话（追加轮）：「**我是让你检测有没有装更多锻造模板重生才自动隐藏胚底，
而不是直接进游戏就直接把胚底隐藏**」。

⇒ 本脚本从「无条件隐藏」改成**两份条件配方并存**（条件在**数据层**，由 NeoForge 求值）：

  | 对象 | 条件 | 效果 |
  |---|---|---|
  | 5 条 `golden_<武器>_blank.json`（工作台配方） | `not(mod_loaded(mut))` | **没装** mut 才加载 |
  | 30 条 `smithing_<金属>_<武器>.json`（base = 自产胚底） | `not(mod_loaded(mut))` | **没装** mut 才加载 |
  | 30 条 `smithing_mut_<金属>_<武器>.json`（base = `mut:golden_<武器>`） | `mod_loaded(mut)` | **装了** mut 才加载 |

  ⚠ 同一对 (金属, 武器) 的两条锻造配方**必须用不同的配方 id 才可能并存**
  （`smithing_<金属>_<武器>` = 自产胚底那条，需求 §3.8 的改正表点名了这个文件名；
  MUT 那条加 `_mut_` 中缀）。上一轮那条 `_mut_` 配方用的是**同一个 id**
  （`smithing_<金属>_<武器>`），所以它只能二选一 —— 本轮按改正表拆开。
  ⚠ 改 id 的唯一影响是：老存档里已经解锁过的**旧 id**（如果玩家玩过 1.5 预览版）会失效一次，
  物品 / 能力 / 数值都不受影响。

  ⚠ 为什么条件必须有：NeoForge 里引用**不存在的物品**的配方会**解析失败**——
  日志刷错误、配方被静默跳过。没装 mut 时 `mut:golden_*` 不存在 ⇒ 那条必须带 `mod_loaded`。

  ⚠ `mut`（MoreUpgradeTemplate，modId=`mut`）是 **optional**（作者裁定）。

  创造页那一半在 Java 侧：`CreativeTabSections#materialsCandidates` 判
  `ModList.get().isLoaded("mut")`，**装了才排除**五件胚底。

  ⚠⚠ 仍要让作者知情的后果：**装了 mut** 的存档拿不到自产胚底这条路（设计如此）；
  **没装 mut** 时一切照旧（胚底可见、可合成、可升级）——这正是本轮改正要的。

配方字段除 `base` 与新增的 `neoforge:conditions` 外，逐字照抄原 `smithing_<金属>_<武器>.json`：
    template = bettergold:<金属>_upgrade_template
    base     = mut:golden_<武器>
    addition = bettergold:<金属>_ingot
    result   = bettergold:<金属>_<武器> ×1

================================================================================
（以下为历史留档：1.5 修正轮的五条「胚底」工作台配方，本轮已**不生成**）
================================================================================
作者原话：「那只是胚底，纯用于合成用的！……它没有实际用途，根本就没有相应的金制器具……

  1. 金制重锤胚底   [金块]
                    [木棍]                                                  2×1
  2. 金制弓箭胚底   原版弓配方把 3 根木棍换成 3 金锭（3 金锭 + 3 线）          3×3
  3. 金制弩胚底     [金锭][铁锭][金锭] / [线][半线钩][线] / [·][金锭][·]      3×3
  4. 金制三叉戟胚底 [·][金锭][金锭] / [·][木棍][金锭] / [金锭][·][·]          3×3
  5. 金制盾牌胚底   [金锭][金锭][金锭] / [金锭][金锭][金锭] / [·][金锭][·]    3×3（7 个金锭）

这五条配方产出的「胚底」是最普通的 `Item`（见 `material/MetalBlanks.java`），
**不进任何 `#minecraft:enchantable/*` 标签**，本轮起也不进创造页。

附魔类别标签（规格 12.1 第 3 条）：1.21 的附魔台走 `stack.is(definition.supportedItems)`，
`supported_items` 全是物品标签，不在标签里 = 附魔台一个选项都不给。
**只有六套金属的 30 件武器进这些标签**；胚底是合成材料，一件都不进。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RECIPES = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"
TAGS = REPO / "src" / "main" / "resources" / "data" / "minecraft" / "tags" / "item" / "enchantable"

METALS = ["sturdygold", "flamegold", "voodoogold", "thundergold", "indigoseagold", "illusiongold"]
WEAPONS = ["mace", "bow", "crossbow", "trident", "shield"]

# 外部模组（已核实，见需求 §3.8 与附二的复现步骤）
MUT_MODID = "mut"
MUT_WEAPON_ITEMS = {w: f"{MUT_MODID}:golden_{w}" for w in WEAPONS}

# 两条条件（字段名已从 NeoForge 源码核实：NotCondition 用 `value`、ModLoadedCondition 用 `modid`）
MUT_LOADED = {"type": "neoforge:mod_loaded", "modid": MUT_MODID}
MUT_NOT_LOADED = {"type": "neoforge:not", "value": MUT_LOADED}

# 胚底 id = golden_<武器>_blank（blank = 胚底）；统一后缀集中在这一处
BLANK_SUFFIX = "_blank"

# ==================== 本轮开关（改回来只需动这里） ====================
# True  = 当前口径：**检测到装了 mut 才隐藏**胚底（两条 `not(mod_loaded(mut))` 条件）
# False = 无条件可见：连条件都不写（胚底配方与以胚底为 base 的锻造配方永远加载；
#         注意此时 MUT 那 30 条**也**会加载，两条升级路并存 —— 作者要改回老路时再用）
HIDE_BLANKS_WHEN_MUT_LOADED = True

problems: list[str] = []


def blank_path(weapon: str) -> str:
    """该武器对应的胚底物品路径，例如 golden_mace_blank"""
    return f"golden_{weapon}{BLANK_SUFFIX}"


def j(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def write(rel: Path, text: str, apply: bool, out: list[str]) -> None:
    out.append(str(rel).replace("\\", "/"))
    if not apply:
        return
    rel.parent.mkdir(parents=True, exist_ok=True)
    rel.write_text(text, encoding="utf-8", newline="\n")


# ==================== 12.5 的五条胚底配方（**历史留档**：本轮不生成） ====================
# 键 = 配方 id（= 产物 id 的路径），值 = 3×3 归一化后的 pattern + key
# ⚠ bg-15w 第 8 项起 `HIDE_BLANKS = True`，本段只作为「一句话改回来」的现成素材保留
#   （把 HIDE_BLANKS 改回 False 即恢复自产胚底那条路），**不再写进资源目录**。
BASE_RECIPES: dict[str, dict] = {
    # 1. 金制重锤胚底：1 金块 + 1 木棍，竖排
    blank_path("mace"): {
        "type": "minecraft:crafting_shaped",
        "pattern": ["A", "B"],
        "key": {
            "A": {"item": "minecraft:gold_block"},
            "B": {"item": "minecraft:stick"},
        },
        "result": {"id": f"bettergold:{blank_path('mace')}", "count": 1},
    },
    # 2. 金制弓箭胚底：原版弓配方（3 木棍 + 3 线）把木棍换成金锭
    #    归一化成 3×3（行首补一个空格），与原版 bow.json 的 [" #X", "# X", " #X"] 同构
    blank_path("bow"): {
        "type": "minecraft:crafting_shaped",
        "pattern": [" #X", "# X", " #X"],
        "key": {
            "#": {"item": "minecraft:gold_ingot"},
            "X": {"item": "minecraft:string"},
        },
        "result": {"id": f"bettergold:{blank_path('bow')}", "count": 1},
    },
    # 3. 金制弩胚底：金锭 3（左上 / 右上 / 中下）+ 铁锭 1（中上）+ 线 2（中左 / 中右）+ 半线钩 1（正中）
    blank_path("crossbow"): {
        "type": "minecraft:crafting_shaped",
        "pattern": ["GIG", "SHS", " G "],
        "key": {
            "G": {"item": "minecraft:gold_ingot"},
            "I": {"item": "minecraft:iron_ingot"},
            "S": {"item": "minecraft:string"},
            "H": {"item": "minecraft:tripwire_hook"},
        },
        "result": {"id": f"bettergold:{blank_path('crossbow')}", "count": 1},
    },
    # 4. 金制三叉戟胚底：木棍在正中，上 / 右 / 右上 / 左下 共 4 个金锭
    blank_path("trident"): {
        "type": "minecraft:crafting_shaped",
        "pattern": [" GG", " SG", "G  "],
        "key": {
            "G": {"item": "minecraft:gold_ingot"},
            "S": {"item": "minecraft:stick"},
        },
        "result": {"id": f"bettergold:{blank_path('trident')}", "count": 1},
    },
    # 5. 金制盾牌胚底：3×3 除左下、右下外全是金锭（7 个）
    #    （与原版盾牌同构，但原版中上是铁锭；作者这次写的是「全是金锭」，按字面落档，见 12.7 第 3 条）
    blank_path("shield"): {
        "type": "minecraft:crafting_shaped",
        "pattern": ["GGG", "GGG", " G "],
        "key": {
            "G": {"item": "minecraft:gold_ingot"},
        },
        "result": {"id": f"bettergold:{blank_path('shield')}", "count": 1},
    },
}

# 规格 12.5 的格子图字面量（自检用：改错立刻暴露）
SPEC_PATTERNS: dict[str, list[str]] = {
    blank_path("mace"): ["A", "B"],
    blank_path("bow"): [" #X", "# X", " #X"],
    blank_path("crossbow"): ["GIG", "SHS", " G "],
    blank_path("trident"): [" GG", " SG", "G  "],
    blank_path("shield"): ["GGG", "GGG", " G "],
}

# ==================== 附魔类别标签（规格 12.1 第 3 条） ====================
# 键 = 标签文件名；值 = 该类里要放哪些武器（每件都会展开成「六套金属」= 6 个物品）。
# **胚底一件都不进**（作者澄清它们不是武器；这也正是 1.5 修正轮要撤掉的那批成员）。
#
# 原版 jar 里的实际成员（12.6 的证据）：
#   * durability 是一串 #minecraft:* 类别标签 + 具体物品（bow / crossbow / trident / shield / mace...），
#     我们的物品不在那些类别里 ⇒ 必须逐件显式加；
#   * vanishing 原版只有 "#minecraft:enchantable/durability" + 指南针 / 南瓜 / 头颅，
#     所以我们的武器进了 durability 就自动进 vanishing，**不需要**再逐件写；
#   * weapon 原版 = "#minecraft:enchantable/sharp_weapon" + mace，
#     sharp_weapon = "#minecraft:swords" + "#minecraft:axes" ——
#     三叉戟要拿锋利 / 亡灵杀手就得同时进 weapon 与 sharp_weapon（规格 12.1 明确要求）；
#   * mace / bow / crossbow / trident 四个类别原版只列了原版那一件，必须显式加我们的。
ENCHANTABLE_TAGS: dict[str, list[str]] = {
    "durability": WEAPONS,
    "mace": ["mace"],
    "bow": ["bow"],
    "crossbow": ["crossbow"],
    "trident": ["trident"],
    "weapon": ["trident"],
    "sharp_weapon": ["trident"],
}


def item_paths(weapon: str) -> list[str]:
    """该武器在 bettergold 命名空间下的全部**武器**物品路径（六套金属 = 6 件）"""
    return [f"{m}_{weapon}" for m in METALS]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    out: list[str] = []

    # ---------- 五条胚底工作台配方（没装 mut 才加载） ----------
    for name, obj in BASE_RECIPES.items():
        recipe = obj
        if HIDE_BLANKS_WHEN_MUT_LOADED:
            # ⚠ 条件写在最前（NeoForge 约定：conditions 是配方的顶层键）
            recipe = {"neoforge:conditions": [MUT_NOT_LOADED], **obj}
        write(RECIPES / f"{name}.json", j(recipe), args.apply, out)

    # ---------- 5 类 × 6 金属的锻造升级：两份条件配方并存 ----------
    #   smithing_<金属>_<武器>.json      base = 自产胚底          + not(mod_loaded(mut))
    #   smithing_mut_<金属>_<武器>.json  base = mut:golden_<武器> + mod_loaded(mut)
    for metal in METALS:
        for weapon in WEAPONS:
            blank_obj = {
                "type": "minecraft:smithing_transform",
                "template": {"item": f"bettergold:{metal}_upgrade_template"},
                "base": {"item": f"bettergold:{blank_path(weapon)}"},
                "addition": {"item": f"bettergold:{metal}_ingot"},
                "result": {"id": f"bettergold:{metal}_{weapon}", "count": 1},
            }
            mut_obj = {
                "type": "minecraft:smithing_transform",
                "template": {"item": f"bettergold:{metal}_upgrade_template"},
                "base": {"item": MUT_WEAPON_ITEMS[weapon]},
                "addition": {"item": f"bettergold:{metal}_ingot"},
                "result": {"id": f"bettergold:{metal}_{weapon}", "count": 1},
            }
            if HIDE_BLANKS_WHEN_MUT_LOADED:
                blank_obj = {"neoforge:conditions": [MUT_NOT_LOADED], **blank_obj}
                mut_obj = {"neoforge:conditions": [MUT_LOADED], **mut_obj}
            write(RECIPES / f"smithing_{metal}_{weapon}.json", j(blank_obj), args.apply, out)
            write(RECIPES / f"smithing_mut_{metal}_{weapon}.json", j(mut_obj), args.apply, out)

    # ---------- 附魔类别标签（只有六套金属的武器） ----------
    for tag, weapons in ENCHANTABLE_TAGS.items():
        values: list[str] = []
        for weapon in weapons:
            values.extend(f"bettergold:{p}" for p in item_paths(weapon))
        write(TAGS / f"{tag}.json", j({"replace": False, "values": values}), args.apply, out)

    # ==================== 自检 ====================
    # 0. 本轮开关的分支自检
    if not HIDE_BLANKS_WHEN_MUT_LOADED:
        problems.append("[配置] HIDE_BLANKS_WHEN_MUT_LOADED=False：胚底无条件可见，"
                        "MUT 那 30 条**也会**加载（两条升级路并存），需人工确认后再用")
    # 1. 五条胚底配方：必须有序、产物 = 同名 ×1、pattern 每行等长、每个非空字符都在 key 里
    #    （无论是否隐藏，模板本身都要保持可用的正确形状 —— 它是"一句话改回来"的那份素材）
    for name, obj in BASE_RECIPES.items():
        if obj["type"] != "minecraft:crafting_shaped":
            problems.append(f"{name} 不是有序配方")
        if obj["result"]["id"] != f"bettergold:{name}" or obj["result"]["count"] != 1:
            problems.append(f"{name} 的产物不是 bettergold:{name} ×1")
        width = len(obj["pattern"][0])
        for row in obj["pattern"]:
            if len(row) != width:
                problems.append(f"{name} 的 pattern 每行长度不一致")
            for ch in row:
                if ch != " " and ch not in obj["key"]:
                    problems.append(f"{name} 的 pattern 用了没定义的键 '{ch}'")
        # pattern 不得超出 3×3
        if width > 3 or len(obj["pattern"]) > 3:
            problems.append(f"{name} 的 pattern 超过 3×3")
        # 产物必须是「胚底」命名的物品（不是武器）
        if not name.endswith(BLANK_SUFFIX):
            problems.append(f"{name} 的产物不是胚底（缺 {BLANK_SUFFIX} 后缀）")
    # 2. 格子图与规格 12.5 逐字一致
    for name, want in SPEC_PATTERNS.items():
        if BASE_RECIPES[name]["pattern"] != want:
            problems.append(f"{name} 的格子图与规格 12.5 不一致：{BASE_RECIPES[name]['pattern']} != {want}")
    # 3. 材料种类核对（规格 12.5 的第 3、4、5 条点明了精确数量）
    def count_of(name: str, item: str) -> int:
        obj = BASE_RECIPES[name]
        keys = [k for k, v in obj["key"].items() if v["item"] == item]
        return sum(row.count(k) for row in obj["pattern"] for k in keys)

    if count_of(blank_path("mace"), "minecraft:gold_block") != 1:
        problems.append("金制重锤胚底的金块不是 1 个")
    if count_of(blank_path("mace"), "minecraft:stick") != 1:
        problems.append("金制重锤胚底的木棍不是 1 个")
    if count_of(blank_path("bow"), "minecraft:gold_ingot") != 3 or count_of(blank_path("bow"), "minecraft:string") != 3:
        problems.append("金制弓箭胚底不是 3 金锭 + 3 线")
    if count_of(blank_path("crossbow"), "minecraft:gold_ingot") != 3:
        problems.append("金制弩胚底的金锭不是 3 个（左上 / 右上 / 中下）")
    if count_of(blank_path("crossbow"), "minecraft:iron_ingot") != 1:
        problems.append("金制弩胚底的铁锭不是 1 个（中上）")
    if count_of(blank_path("crossbow"), "minecraft:string") != 2:
        problems.append("金制弩胚底的线不是 2 个（中左 / 中右）")
    if count_of(blank_path("crossbow"), "minecraft:tripwire_hook") != 1:
        problems.append("金制弩胚底的半线钩不是 1 个（正中）")
    if count_of(blank_path("trident"), "minecraft:gold_ingot") != 4 or count_of(blank_path("trident"), "minecraft:stick") != 1:
        problems.append("金制三叉戟胚底不是 4 金锭 + 1 木棍")
    if count_of(blank_path("shield"), "minecraft:gold_ingot") != 7:
        problems.append("金制盾牌胚底的金锭不是 7 个")
    # 4. 锻造升级：两份条件配方都要对（同 (金属, 武器) 两条 id 必须不同）
    if len(METALS) * len(WEAPONS) != 30:
        problems.append("锻造升级配方不是 5 类 × 6 金属 = 30 条")
    for metal in METALS:
        for weapon in WEAPONS:
            pairs = [
                (RECIPES / f"smithing_{metal}_{weapon}.json",
                 f"bettergold:{blank_path(weapon)}",
                 [MUT_NOT_LOADED] if HIDE_BLANKS_WHEN_MUT_LOADED else None),
                (RECIPES / f"smithing_mut_{metal}_{weapon}.json",
                 MUT_WEAPON_ITEMS[weapon],
                 [MUT_LOADED] if HIDE_BLANKS_WHEN_MUT_LOADED else None),
            ]
            for path, want_base, want_conds in pairs:
                if not args.apply:
                    continue
                if not path.is_file():
                    problems.append(f"锻造升级配方没写出来: {path.name}")
                    continue
                obj = json.loads(path.read_text(encoding="utf-8"))
                if obj["base"]["item"] != want_base:
                    problems.append(f"{path.name} 的 base 不是 {want_base}")
                if obj["result"]["id"] != f"bettergold:{metal}_{weapon}":
                    problems.append(f"{path.name} 的产物不是 {metal}_{weapon}")
                if obj["template"]["item"] != f"bettergold:{metal}_upgrade_template":
                    problems.append(f"{path.name} 的模板不是 {metal}_upgrade_template")
                if obj["addition"]["item"] != f"bettergold:{metal}_ingot":
                    problems.append(f"{path.name} 的加法不是 {metal}_ingot")
                conds = obj.get("neoforge:conditions")
                if want_conds is None:
                    if conds is not None:
                        problems.append(f"{path.name} 在非条件态不该有条件：{conds}")
                elif conds != want_conds:
                    problems.append(f"{path.name} 的条件不是 {want_conds}：{conds}")
                # 反向：以 MUT 金武器为 base 的那条**不许**再引用胚底
                if "mut" in path.name and f"bettergold:{blank_path(weapon)}" in json.dumps(obj):
                    problems.append(f"{path.name} 里不该出现胚底 {blank_path(weapon)}")
    # 5. 五条胚底工作台配方：条件必须正好是 not(mod_loaded(mut))（没装 mut 才加载）
    if args.apply and HIDE_BLANKS_WHEN_MUT_LOADED:
        for name in BASE_RECIPES:
            path = RECIPES / f"{name}.json"
            if not path.is_file():
                problems.append(f"胚底工作台配方没写出来: {path.name}")
                continue
            obj = json.loads(path.read_text(encoding="utf-8"))
            if obj.get("neoforge:conditions") != [MUT_NOT_LOADED]:
                problems.append(f"{path.name} 的条件不是 not(mod_loaded(mut))：{obj.get('neoforge:conditions')}")
    # 5. 附魔标签成员（每件武器 6 个物品；胚底一个都不许进）
    for tag, weapons in ENCHANTABLE_TAGS.items():
        want = {f"bettergold:{p}" for w in weapons for p in item_paths(w)}
        path = TAGS / f"{tag}.json"
        if args.apply:
            if not path.is_file():
                problems.append(f"标签 {tag} 没写出来")
                continue
            got = set(json.loads(path.read_text(encoding="utf-8"))["values"])
            if got != want:
                problems.append(f"标签 {tag} 的成员与预期不符（缺 {sorted(want - got)[:3]}，多 {sorted(got - want)[:3]}）")
            for weapon in WEAPONS:
                if f"bettergold:{blank_path(weapon)}" in got:
                    problems.append(f"标签 {tag} 里混进了胚底 {blank_path(weapon)}（胚底不是武器）")
    # 6. 每件武器都必须进 durability（否则附魔台一个选项都没有）
    for weapon in WEAPONS:
        if weapon not in ENCHANTABLE_TAGS["durability"]:
            problems.append(f"{weapon} 没进 enchantable/durability")

    mode = "检测到 mut 才隐藏" if HIDE_BLANKS_WHEN_MUT_LOADED else "无条件可见"
    print(f"{'已写入' if args.apply else '演练（未写入）'}: {len(out)} 项"
          f"（{len(BASE_RECIPES)} 条胚底工作台配方 + "
          f"{len(METALS) * len(WEAPONS) * 2} 条锻造升级（自产胚底 / MUT 各 30）+ "
          f"{len(ENCHANTABLE_TAGS)} 附魔标签；口径 = {mode}）")
    if HIDE_BLANKS_WHEN_MUT_LOADED:
        print("没装 mut：胚底 5 条工作台配方 + 30 条 smithing_<金属>_<武器> 加载；"
              "smithing_mut_* 那 30 条不加载（正常）")
        print("装了 mut：反过来 —— 胚底与以胚底为 base 的那 30 条不加载（属正常，不是 datagen 坏了）")
    if problems:
        print(f"[错误] {len(problems)} 条:")
        for p in problems:
            print("   ", p)
        sys.exit(1)
    print("自检通过：五张胚底格子图与规格 12.5 逐字一致；"
          "两份 30 条锻造升级的 base / 条件正确；7 个附魔标签只含六套金属的武器。")


if __name__ == "__main__":
    main()
