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
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RECIPES = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"

# 金属 id -> 该金属「原料配方」的主材料（升级锻造模板里替换金钱贝的那一个，
# 也是 raw_<金属>.json 里的 "exchange" 字段）
#
# 1.5：raw_sturdygold.json 只是**模板**（本体不含 exchange/result 字段，走序列化器的缺省回落）；
# 下面每一套金属生成出来的 raw_<金属>.json 都会**显式写出**自己的 exchange 与 result ——
# 这是 1.4「原料合成配方串格」bug 的修复方式（详见 RawSturdygoldRecipe 的类注释）。
METALS = {
    "flamegold": "blazing_rod",
    "voodoogold": "voodoo_feather",
    "thundergold": "amethyst_energy_dust",
    "indigoseagold": "indigo_ocean_heart",
    "illusiongold": "chorus_cherry_branch",
}

# 原料合成配方的模板文件（1.5 起对非万坚金金属注入 exchange / result 两个字段）
RAW_CRAFT_TEMPLATE = "raw_sturdygold.json"

# 本模组的自定义配方序列化器（"配方类型"，不是物品 id）：原料合成配方用它。
# 它绝不能跟着金属改名（改了就报 Unknown recipe_serializer），所以替换时要先保护起来 ——
# 但**保护范围必须只限 type 字段**。
#
# 1.4 串格 bug 的根因就在这里：早先的写法是保护裸串 `"bettergold:raw_sturdygold"`，
# 而熔炼 / 高炉模板里 `"ingredient": { "item": "bettergold:raw_sturdygold" }` 是**同一个裸串**，
# 于是它被一起保护、替换完又一起还原成万坚金原料。结果四个金属的「原料 → 锭」配方
# 输入全都是 raw_sturdygold：
#   * JEI / 配方书里连着四格「万坚金原料 → 各金属锭」；
#   * 熔炉里放 raw_flamegold，`getRecipeFor` 会命中这几条同输入的配方之一（顺序不定），
#     可能烧出 sturdygold_ingot —— 这是实打实的功能 bug，不只是显示问题。
RAW_RECIPE_TYPE = "bettergold:raw_sturdygold"
RAW_RECIPE_TYPE_GUARD = "@@RAW_RECIPE_TYPE@@"

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
            src_text = src.read_text(encoding="utf-8")
            text = src_text
            # 升级模板配方：金钱贝换成该金属的专属材料
            if tpl == "sturdygold_upgrade_template.json":
                text = text.replace("bettergold:golden_cowrie", f"bettergold:{special}")
            # 注意：原料配方用的是本模组的自定义序列化器 bettergold:raw_sturdygold，
            # 那是"配方类型"不是物品 id，绝不能跟着改名（改了就报 Unknown recipe_serializer）。
            # 保护它时**只匹配 type 字段**（用正则容忍任意空白，不要写成裸串）：
            # 写成裸串 '"bettergold:raw_sturdygold"' 会把熔炼 / 高炉模板里的 ingredient 一并保护，
            # 替换完再还原，输入就永远是万坚金原料了（== 1.4 的串格 bug）。
            # ingredient 必须走下面那次普通的 sturdygold → <metal> 改名。
            text, guarded = re.subn(r'("type"\s*:\s*)"bettergold:raw_sturdygold"',
                                    r'\1"@@RAW_RECIPE_TYPE@@"', text)
            text = text.replace("sturdygold", metal)
            text = text.replace("@@RAW_RECIPE_TYPE@@", RAW_RECIPE_TYPE)
            # 1.5：原料合成配方必须显式声明自己的兑换物与产物。
            # 1.4 这里不写字段，RawSturdygoldRecipe 又是硬编码的，于是三个新金属合出来
            # 永远是万坚金原料（配方 id 各不相同，读出来却是同一条）。模板 raw_sturdygold.json
            # 保持不带字段（它是"缺省回落"的活样本），其余金属一律注入。
            if tpl == RAW_CRAFT_TEMPLATE and metal != "sturdygold":
                obj = json.loads(text)
                obj["exchange"] = f"bettergold:{special}"
                obj["result"] = f"bettergold:raw_{metal}"
                text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
            # 兜底 1：模板里**确实有** raw_sturdygold 这个 type 字段，替换后却没保护上
            # → 序列化器已被改名成 bettergold:raw_<metal>（编译期不报错，进游戏才 Unknown recipe_serializer）。
            # 注意判据必须是"type 字段"，不能只看裸串 —— 熔炼模板的 ingredient 里也有同一个裸串。
            if not guarded and re.search(r'"type"\s*:\s*"bettergold:raw_sturdygold"', src_text):
                raise SystemExit(f"[错误] {tpl} 的 {RAW_RECIPE_TYPE} 没被保护，序列化器可能被改名")
            # 兜底 2：产物里绝不允许出现 bettergold:raw_<metal> 这种不存在的序列化器
            if f'"type": "bettergold:raw_{metal}"' in text:
                raise SystemExit(f"[错误] {tpl} 产物里出现了不存在的序列化器 bettergold:raw_{metal}")
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

    # 「原料 → 锭」链条自检（1.4 就是这里串了格：三个新金属的输入全被留成 raw_sturdygold）。
    # 检查三件事：
    #   1. 每条 raw_<金属>_{smelting,blasting}.json 的 ingredient 就是它自己的原料、result 是自己的锭；
    #   2. **四条链的输入两两不同** —— 这条才是真正能拦住"串格"的不变量
    #      （只查"输入是自己的原料"看不出两条链指向同一个输入）；
    #   3. 没有任何 @@ 占位符 / raw_sturdygold 残留。
    chain_bad: list[str] = []
    seen_input: dict[tuple[str, str], str] = {}
    for metal in ["sturdygold", *METALS]:
        for kind in ("smelting", "blasting"):
            name = f"raw_{metal}_{kind}.json"
            p = RECIPES / name
            if not p.is_file():
                chain_bad.append(f"缺文件 {name}")
                continue
            text = p.read_text(encoding="utf-8")
            expect_in = f'"item": "bettergold:raw_{metal}"'
            expect_out = f'"id": "bettergold:{metal}_ingot"'
            if expect_in not in text:
                chain_bad.append(f"{name} 的 ingredient 不是 bettergold:raw_{metal}")
            if expect_out not in text:
                chain_bad.append(f"{name} 的 result 不是 bettergold:{metal}_ingot")
            if "@@" in text:
                chain_bad.append(f"{name} 残留占位符")
            # 同一个 recipe type 下，四条链的输入必须两两不同（熔炼与高炉各查各的，
            # 同一金属的熔炼 / 高炉共用输入是正常的）
            other = seen_input.get((kind, expect_in))
            if other is not None:
                chain_bad.append(f"{name} 与 {other} 的输入相同（{expect_in}）→ 串格")
            seen_input[(kind, expect_in)] = name
    print(f"原料→锭 链条校验失败: {len(chain_bad)} {chain_bad[:4]}")

    # 「原料合成配方」自检（1.5 修的就是这里）：raw_<金属>.json 必须显式声明自己的
    # exchange（兑换物）与 result（产物），且**各金属的产物两两不同**。
    # 万坚金本体的 raw_sturdygold.json 是"缺省回落"的样本：允许不带字段，
    # 此时按序列化器默认值（金钱贝 / raw_sturdygold）理解。
    raw_bad: list[str] = []
    seen_result: dict[str, str] = {}
    for metal in ["sturdygold", *METALS]:
        name = f"raw_{metal}.json"
        p = RECIPES / name
        if not p.is_file():
            raw_bad.append(f"缺文件 {name}")
            continue
        obj = json.loads(p.read_text(encoding="utf-8"))
        if obj.get("type") != RAW_RECIPE_TYPE:
            raw_bad.append(f"{name} 的 type 不是 {RAW_RECIPE_TYPE}")
        if "@@" in p.read_text(encoding="utf-8"):
            raw_bad.append(f"{name} 残留占位符")
        # 缺省字段按序列化器的默认值理解（万坚金本体的模板就不带字段）
        result = obj.get("result", "bettergold:raw_sturdygold")
        exchange = obj.get("exchange", "bettergold:golden_cowrie")
        if result != f"bettergold:raw_{metal}":
            raw_bad.append(f"{name} 的 result 不是 bettergold:raw_{metal}（实际 {result}）")
        if metal != "sturdygold" and exchange != f"bettergold:{METALS[metal]}":
            raw_bad.append(f"{name} 的 exchange 不是 bettergold:{METALS[metal]}（实际 {exchange}）")
        other = seen_result.get(result)
        if other is not None:
            raw_bad.append(f"{name} 与 {other} 的产物相同（{result}）→ 串格")
        seen_result[result] = name
    print(f"原料合成配方校验失败: {len(raw_bad)} {raw_bad[:4]}")

    if chain_bad or raw_bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
