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
    * "六套金属应当一致"的标签（#minecraft:beacon_base_blocks 等）必须显式覆盖万坚金 ——
      万坚金的数据是 1.3 手写的、不在 METALS 循环里，见 ALL_METALS / BEACON_SUFFIXES 的注释。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "src" / "main" / "resources" / "data"

METALS = ["flamegold", "voodoogold", "thundergold", "indigoseagold", "illusiongold",
          # 1.6（bg-16）：两套新金属。加这一行就自动带上 家族标签 / 工具类别 / 盔甲类别 /
          # mineable+needs_diamond_tool，以及信标基座段（那段遍历 ALL_METALS ⇒ 块/砖/柱各一条）。
          "thornsgold", "echogold"]
# 万坚金（sturdygold）是本模组最早的一套金属：它的数据 / 标签是 1.3 **手写**的，不进 METALS 循环
# （进了会在 #minecraft:mineable/pickaxe 里留下与 "#bettergold:storage_blocks" 桥接重复的条目）。
# 但凡口径是"六套金属一致"的标签，都必须显式把万坚金算进来 —— 见下面的 BEACON_SUFFIXES。
STURDYGOLD = "sturdygold"
ALL_METALS = [STURDYGOLD, *METALS]
BLOCKS = ["block", "bricks", "bricks_slab", "bricks_stairs", "bricks_wall",
          "pillar", "door", "trapdoor", "bars", "chain", "lantern"]
# #minecraft:beacon_base_blocks 的成员口径（1.4 既有口径，commit b5f68d3 手写进 JSON）：
#   「金砖块 + 万坚金块/砖 + 烈燃/巫毒/结雷 的 块/砖/柱」= 14 条 ⇒ 金属的**块 / 砖 / 柱**三类都能当信标金字塔基座。
# ⚠ bg-15y 修的 bug 就在这一行：这里原先只有 block / bricks，**柱子从来没进过生成器**
#   （1.4 的 5 根柱子是直接手写进产物 JSON 的，生成器只是没删它们）；
#   1.5 新增两套金属时生成器照常补了 块/砖，于是靛海金柱 / 幻惑金柱漏出标签。
#   现在改成六套金属一次性列全 ⇒ 就算产物 JSON 被删掉、从零重建，结果也逐字一致。
BEACON_SUFFIXES = ["block", "bricks", "pillar"]
# 金系那两块（**不是** MetalFamily：gold 那套没有 block，只有 1.3 手写的金砖块 / 金柱）。
# 列在这里，让 #minecraft:beacon_base_blocks **整份**都由生成器负责，不留手写条目
# （原来这两条只存在于产物 JSON 里 —— 与"柱子"同一种成因：手写条目没人管）。
BEACON_NON_FAMILY = ["bettergold:gold_bricks", "bettergold:gold_pillar"]
TOOLS = {"swords": "sword", "pickaxes": "pickaxe", "axes": "axe", "shovels": "shovel", "hoes": "hoe"}
ARMOR = {"head_armor": "helmet", "chest_armor": "chestplate", "leg_armor": "leggings", "foot_armor": "boots"}

# --------------------------------------------------------------------------------------
# bg-fix3（2026-10-07）：**带"可选条目"的物品标签**（条目写成 {"id": ..., "required": false}）
# --------------------------------------------------------------------------------------
# 依据（【读源码】patched 1.21.1，落在 docs/1.6-规格.md §二十二）：
#   * `TagEntry.FULL_CODEC` 有 `"required"` 字段（`Codec.BOOL.optionalFieldOf("required", true)`）；
#   * `TagLoader` 里"**必需**条目缺失" ⇒ `LOGGER.error("Couldn't load tag … as it is missing …")`
#     并**整条 tag 丢弃**；写 `required:false` 的条目缺失 ⇒ `TagEntry#build` 返回 true、**静默跳过**，
#     tag 照常加载（可能为空集）。
#
# 用途：成就判据里要引用"**只在装了某个可选模组时才存在**的物品"时（乐事小刀 / 帕秋莉手册物品），
#   唯一既能把物品纳入判据、又不会在"没装"时把整份 JSON 弄坏的写法 = **成就的 items 指向本标签**
#   （`ItemPredicate.items` 是 `HolderSet` ⇒ 接受 `"#ns:tag"` 这种**单个字符串**形式），
#   标签里那些条目写成 `required:false`。
#   ⚠ 不许把 tag 塞进 `items` 的**列表**里同别的 id 混写：`HolderSetCodec` 的
#     `ExtraCodecs.ensureHomogenous(Holder::kind)` 只接受同一种 Holder 形态 ⇒ 混合列表解码失败。
#   ⚠ 也不许"用 neoforge:conditions 把整个成就文件关掉"：那样没装乐事时这 8 条成就**整个消失**。
OPTIONAL_ITEM_TAG_VALUES: dict[str, list[dict]] = {}
# 8 把乐事小刀（`<族>_knife`，FdItems 反射注册 ⇒ 没装 FD 时物品不存在）
#   → 8 条「获得任意一种 XX金武器工具」成就的 `have_knife` 判据各读自己那一张标签。
for _m in ALL_METALS:
    OPTIONAL_ITEM_TAG_VALUES["%s_knives" % _m] = [
        {"id": "bettergold:%s_knife" % _m, "required": False}]
# 手册物品（bg-book：**没装 Patchouli 时根本不注册**）→ 根成就「旧时代炼金术的继承者」的
#   判据由 `recipe_crafted` 改成 `inventory_changed`（作者 2026-10-07「触发条件是**获得**」）。
OPTIONAL_ITEM_TAG_VALUES["handbook"] = [
    {"id": "bettergold:alchemy_student_handbook", "required": False}]

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

    # 信标基座：金系两块 + 六套金属 × {块, 砖, 柱}。
    # ⚠ 这一段**必须**留在 METALS 循环外并遍历 ALL_METALS：
    #   ① 柱子（pillar）原先完全不在生成器里（bg-15y 的 bug 根因）；
    #   ② 万坚金不在 METALS 里，但它同样要有块/砖/柱三件。
    add(DATA / "minecraft" / "tags" / "block" / "beacon_base_blocks.json", BEACON_NON_FAMILY)
    for m in ALL_METALS:
        add(DATA / "minecraft" / "tags" / "block" / "beacon_base_blocks.json",
            [f"bettergold:{m}_{s}" for s in BEACON_SUFFIXES])
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


def write_optional_tag(path: Path, values: list[dict], apply: bool) -> tuple[int, int]:
    """写一张**完全由本生成器拥有**的可选条目标签（内容≠计划就整份重写）。

    ⚠ 与 `merge()` 的"只增不删"不同：这 9 张标签没有任何手写历史（bg-fix3 新建），
    所以按"生成器是唯一真源"整份重写 —— 手改回去下次重跑就会被纠正。
    ⇒ 返回 (写入前的条目数, 写入后的条目数)。
    """
    want = {"replace": False, "values": list(values)}
    before = 0
    if path.is_file():
        try:
            before = len(json.loads(path.read_text(encoding="utf-8")).get("values", []))
        except Exception:  # noqa: BLE001  坏文件也照样被重写
            before = 0
        if json.loads(path.read_text(encoding="utf-8")) == want:
            return before, len(values)
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(want, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    return before, len(values)


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

    # bg-fix3：9 张"可选条目"标签（8 把乐事小刀 + 手册物品），见文件头 `OPTIONAL_ITEM_TAG_VALUES`
    optional_changed = 0
    for name, values in sorted(OPTIONAL_ITEM_TAG_VALUES.items()):
        path = DATA / "bettergold" / "tags" / "item" / ("%s.json" % name)
        before, after = write_optional_tag(path, values, args.apply)
        if before != after:
            optional_changed += 1
        print(f"{'可选标签 ' + str(path.relative_to(DATA)):<58} {before} -> {after}"
              f"{'' if before != after else '  (已是最新)'}")
    print(f"{'已写入' if args.apply else '演练'}: 可选条目标签 {len(OPTIONAL_ITEM_TAG_VALUES)} 张，"
          f"其中内容变化 {optional_changed} 张")


if __name__ == "__main__":
    main()
