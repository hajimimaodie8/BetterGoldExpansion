#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
崩乱合金（chaosalloy）配方生成器 —— 1.7 bg-n10r7（轮7）。

用法:
    python generate_chaosalloy_recipes.py --apply      # 写盘
    python generate_chaosalloy_recipes.py              # 演练（只打印与自检）

为什么单独一个脚本（而不是塞进 generate_metal_recipes.py）
--------------------------------------------------------
既有那个生成器是「拿万坚金的配方当模板、把 sturdygold 换成 <族>」的**批量替换**写法。
崩乱合金这 19 条配方**四条都不在那个模板的形状里**：

  ① 锭   = 4 下界合金锭 + 4 混沌金块 + 1 高精度炼金油（**无序、9 项**，作者原话）
  ② 模板 = 6 混沌金锭 + 原版下界合金升级模板 + 崩乱合金锭 + 混沌金块（**另一种 3×3 排布**）
  ③ 锻造 = base 是**混沌金装备**（不是原版金装备 / 胚底），addition 是崩乱合金锭
  ④ 块   = 唯一的"标准形"，但它的 9 个材料是崩乱合金锭（与既有 8 族同构）

⇒ 与其在批量替换器里塞 4 个 if 分支（那正是 1.4「熔炼串格」的同一种病），不如单独一个
   只产这一族、每条配方都写全、并且**自己能自检**的小脚本。

依据（全部来自作者原话 / 立档，逐条可查）
------------------------------------------
* `docs/1.7-混沌金与崩乱合金-需求立档.md` §2.9 可执行口径 1：锭 = 4×netherite_ingot +
  4×chaosgold_block + 1×refined_alchemic_oil → 1（**无序**，共 9 项正好占满 3×3）。
* 同节"模板配方（100% 读出）"：
      混沌金锭  下界合金升级模板  混沌金锭
      混沌金锭  崩乱合金锭        混沌金锭
      混沌金锭  混沌金块          混沌金锭
  ⇒ 6 混沌金锭 + 1 原版模板 + 1 崩乱合金锭 + 1 混沌金块。**有序 / 无序**（立档 §4 ⑪-c 未裁）
  ⇒ 本轮按**有序**（照截图逐格），与万坚金模板那条 `crafting_shaped` 的既有形状同构。
* §2.9「块属性 = 下界合金块 3 倍」+ §2.10「装备 14 件」⇒ 块与锻造链。
* §4.0 ⑪d：崩乱合金只有 锭 + 块 + 模板 + 器具 + 盔甲 + 禁果。

自检（不通过就 exit 1，别写半套）
----------------------------------
1. 每条配方都是合法 JSON；
2. 锭配方的 9 个材料**逐项**等于作者给的 4+4+1（数量断言，不是"大致对"）；
3. 模板配方的 3×3 逐格等于立档那张图；
4. 15 条锻造配方的 base 是**混沌金**同名装备、addition 是崩乱合金锭、template 是本模板；
5. **反向**：不许出现 base 是原版金 / 胚底（那是既有 8 族的形状，抄错了会静默串格）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[2]
RECIPES = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"

NS = "bettergold"
METAL = "chaosalloy"
BASE_METAL = "chaosgold"        # 崩乱合金的锻造 base = 混沌金装备（作者原话「混沌金装备 + 崩乱合金锭 + 本模板」）

# 作者给的锭配方材料（立档 §2.9 可执行口径 1）—— 逐项写死，自检时按这个表核
INGOT_INPUTS = (
    [{"item": "minecraft:netherite_ingot"}] * 4
    + [{"item": f"{NS}:chaosgold_block"}] * 4
    + [{"item": f"{NS}:refined_alchemic_oil"}]
)

# 模板 3×3（立档 §2.9 "模板配方（100% 读出）"）：G = 混沌金锭, T = 原版模板, A = 崩乱合金锭, C = 混沌金块
TEMPLATE_PATTERN = ["GIG", "GAG", "GCG"]
TEMPLATE_KEY = {
    "G": {"item": f"{NS}:chaosgold_ingot"},
    "I": {"item": "minecraft:netherite_upgrade_smithing_template"},
    "A": {"item": f"{NS}:chaosalloy_ingot"},
    "C": {"item": f"{NS}:chaosgold_block"},
}

# 14 件（创造页装备分区那 14 件，作者口径「14 件」）+ 乐事联动小刀（与既有 8 族同构）
GEAR = ["sword", "mace", "trident", "bow", "crossbow",
        "axe", "pickaxe", "shovel", "hoe", "shield",
        "helmet", "chestplate", "leggings", "boots"]
KNIFE = "knife"
FD_CONDITION = [{"type": "neoforge:mod_loaded", "modid": "farmersdelight"}]


def ingot_recipe() -> dict:
    return {
        "type": "minecraft:crafting_shapeless",
        "ingredients": list(INGOT_INPUTS),
        "result": {"id": f"{NS}:{METAL}_ingot", "count": 1},
    }


def block_from_ingot_recipe() -> dict:
    return {
        "type": "minecraft:crafting_shaped",
        "pattern": ["III", "III", "III"],
        "key": {"I": {"item": f"{NS}:{METAL}_ingot"}},
        "result": {"id": f"{NS}:{METAL}_block", "count": 1},
    }


def ingot_from_block_recipe() -> dict:
    """块 → 9 锭（与既有 8 族 `*_ingot_from_block.json` 逐字同构；不让块变成死路）"""
    return {
        "type": "minecraft:crafting_shapeless",
        "ingredients": [{"item": f"{NS}:{METAL}_block"}],
        "result": {"id": f"{NS}:{METAL}_ingot", "count": 9},
    }


def template_recipe() -> dict:
    return {
        "type": "minecraft:crafting_shaped",
        "pattern": list(TEMPLATE_PATTERN),
        "key": dict(TEMPLATE_KEY),
        "result": {"id": f"{NS}:{METAL}_upgrade_template", "count": 1},
    }


def forbidden_fruit_recipe() -> dict:
    """崩乱禁果 = 混沌禁果 + 崩乱合金锭（**无序**，作者原话「混沌金苹果 + 崩乱合金锭，无序」）。

    ⚠「混沌金苹果」的所指（立档 §4 歧义 ㉒）按 §4.0「全部按字面」+ 轮4 的既成事实
    读作**混沌禁果** {@code chaosgold_forbidden_fruit}（zip 里那张贴图就叫「混沌金禁果」）。
    """
    return {
        "type": "minecraft:crafting_shapeless",
        "ingredients": [
            {"item": f"{NS}:chaosgold_forbidden_fruit"},
            {"item": f"{NS}:{METAL}_ingot"},
        ],
        "result": {"id": f"{NS}:{METAL}_forbidden_fruit", "count": 1},
    }


def smithing_recipe(gear: str) -> dict:
    obj: dict = {}
    if gear == KNIFE:
        # 小刀是乐事联动件（没装乐事时 bettergold:chaosalloy_knife 根本不注册）⇒ 与既有 8 族一样带条件
        obj["neoforge:conditions"] = FD_CONDITION
    obj.update({
        "type": "minecraft:smithing_transform",
        "template": {"item": f"{NS}:{METAL}_upgrade_template"},
        "base": {"item": f"{NS}:{BASE_METAL}_{gear}"},
        "addition": {"item": f"{NS}:{METAL}_ingot"},
        "result": {"id": f"{NS}:{METAL}_{gear}", "count": 1},
    })
    return obj


def targets() -> list[tuple[str, dict]]:
    out = [
        (f"{METAL}_ingot.json", ingot_recipe()),
        (f"{METAL}_block_from_ingot.json", block_from_ingot_recipe()),
        (f"{METAL}_ingot_from_block.json", ingot_from_block_recipe()),
        (f"{METAL}_upgrade_template.json", template_recipe()),
        (f"{METAL}_forbidden_fruit.json", forbidden_fruit_recipe()),
    ]
    for gear in GEAR + [KNIFE]:
        out.append((f"smithing_{METAL}_{gear}.json", smithing_recipe(gear)))
    return out


def check(files: list[tuple[str, dict]]) -> list[str]:
    bad: list[str] = []

    # ① 锭：9 项且逐项等于 4 下界合金 + 4 混沌金块 + 1 高精度炼金油
    ingot = dict(files).get(f"{METAL}_ingot.json", {})
    if ingot.get("type") != "minecraft:crafting_shapeless":
        bad.append("锭配方不是无序合成")
    got = json.dumps(ingot.get("ingredients"), sort_keys=True)
    want = json.dumps(INGOT_INPUTS, sort_keys=True)
    if got != want:
        bad.append(f"锭配方的 9 项材料不是 4 下界合金锭 + 4 混沌金块 + 1 高精度炼金油")
    if len(ingot.get("ingredients") or []) != 9:
        bad.append(f"锭配方的材料数不是 9（实际 {len(ingot.get('ingredients') or [])}）")

    # ② 模板：3×3 逐格
    tpl = dict(files).get(f"{METAL}_upgrade_template.json", {})
    if tpl.get("pattern") != TEMPLATE_PATTERN:
        bad.append(f"模板配方的排布不是 {TEMPLATE_PATTERN}")
    if tpl.get("key") != TEMPLATE_KEY:
        bad.append("模板配方的图例不是 混沌金锭 / 原版模板 / 崩乱合金锭 / 混沌金块")
    used = sorted(c for row in TEMPLATE_PATTERN for c in row)
    if used.count("G") != 6:
        bad.append(f"模板配方里混沌金锭不是 6 个（实际 {used.count('G')}）")

    # ③ 15 条锻造：base = 混沌金同名装备，addition = 崩乱合金锭
    n_smithing = 0
    for name, obj in files:
        if not name.startswith(f"smithing_{METAL}_"):
            continue
        n_smithing += 1
        gear = name[len(f"smithing_{METAL}_"):-len(".json")]
        if obj.get("type") != "minecraft:smithing_transform":
            bad.append(f"{name} 不是 smithing_transform")
        if obj.get("template", {}).get("item") != f"{NS}:{METAL}_upgrade_template":
            bad.append(f"{name} 的 template 不是本族模板")
        if obj.get("base", {}).get("item") != f"{NS}:{BASE_METAL}_{gear}":
            bad.append(f"{name} 的 base 不是混沌金同名装备（{NS}:{BASE_METAL}_{gear}）")
        if obj.get("addition", {}).get("item") != f"{NS}:{METAL}_ingot":
            bad.append(f"{name} 的 addition 不是崩乱合金锭")
        if obj.get("result", {}).get("id") != f"{NS}:{METAL}_{gear}":
            bad.append(f"{name} 的产物不是 {NS}:{METAL}_{gear}")
        # ④ 反向：base 不许是原版金 / 胚底 / 别的族
        base_item = obj.get("base", {}).get("item", "")
        if base_item.startswith("minecraft:") or "_blank" in base_item:
            bad.append(f"{name} 的 base 落到了原版金 / 胚底（{base_item}）—— 那是既有 8 族的形状")
        if gear == KNIFE and obj.get("neoforge:conditions") != FD_CONDITION:
            bad.append(f"{name}（乐事小刀）缺 mod_loaded:farmersdelight 条件")
        if gear != KNIFE and "neoforge:conditions" in obj:
            bad.append(f"{name} 不该带条件（只有小刀是乐事联动件）")
    if n_smithing != len(GEAR) + 1:
        bad.append(f"锻造配方数不是 {len(GEAR) + 1}（实际 {n_smithing}）")

    # ⑤ 块两条都在
    for name in (f"{METAL}_block_from_ingot.json", f"{METAL}_ingot_from_block.json"):
        if name not in dict(files):
            bad.append(f"缺 {name}")

    # ⑥ 崩乱禁果：无序、2 项（混沌禁果 + 崩乱合金锭）
    fruit = dict(files).get(f"{METAL}_forbidden_fruit.json", {})
    if fruit.get("type") != "minecraft:crafting_shapeless":
        bad.append("崩乱禁果配方不是无序合成")
    fruit_ings = sorted(i.get("item") for i in fruit.get("ingredients", []))
    if fruit_ings != sorted([f"{NS}:chaosgold_forbidden_fruit", f"{NS}:{METAL}_ingot"]):
        bad.append(f"崩乱禁果配方的材料不是 混沌禁果 + 崩乱合金锭（实际 {fruit_ings}）")
    if fruit.get("result", {}).get("id") != f"{NS}:{METAL}_forbidden_fruit":
        bad.append("崩乱禁果配方的产物不是 chaosalloy_forbidden_fruit")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = targets()
    bad = check(files)

    written = 0
    for name, obj in files:
        text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
        json.loads(text)          # ① 自检：合法 JSON（不合法这里就抛）
        if args.apply:
            (RECIPES / name).write_text(text, encoding="utf-8", newline="\n")
            written += 1

    print(f"{'已写入' if args.apply else '演练'}: {written or len(files)} 个崩乱合金配方"
          f"（1 锭 + 1 块→锭 + 1 锭→块 + 1 模板 + {len(GEAR) + 1} 锻造）")
    print(f"配方自检失败: {len(bad)} {bad[:4]}")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
