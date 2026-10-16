#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金属族「形态子集」的 **Python 唯一真源**（1.7 bg-n10 轮1 后半）。

⚠ 这是 Java 侧 `material/MetalFamily.java` 的嵌套枚举 `MetalFamily.Form` 与
`AllMetals.java` 里 `Spec.forms(...)` / `Spec.withoutForms(...)` 的**镜像**。
两边必须逐字一致 —— `validate_metal_data.py` 的 `[bgn10-forms-parity]` 断言会读
`MetalFamily.java` 的枚举与 `AllMetals.java` 的调用字面来核对，改一边必红。

**加族只许改三处**：① 本文件 ② `AllMetals.java` 的 Spec ③ 各生成器的 `METALS` 清单。

口径（作者 2026-10-16 裁定，立档 §4.0 第 ⑪d 行「按照现有的贴图标准来」）：
  * 形态 = 材料链（锭/粒/原料/块/升级锻造模板）+ **11 种建材**
    （块 + 砖块 + 砖楼梯 + 砖台阶 + 砖墙 + 柱 + 栏杆 + 门 + 活板门 + 链 + 灯笼）；
  * **锭与块是必备形态**（Java 侧 register() 会当场报错）；
  * 器具 / 武器 / 盔甲**不在形态表里**：它们恒定注册，不需要开关；
  * 没声明的形态 ⇒ 不注册、不产出贴图/模型/方块状态/战利品表/标签归属/配方，
    字段为 null（Java 侧）。
"""
from __future__ import annotations

# ==================== 形态全集（顺序 = Java Form 枚举顺序） ====================
ALL_FORMS = [
    "ingot", "nugget", "raw", "block",
    "bricks", "bricks_stairs", "bricks_slab", "bricks_wall",
    "pillar", "bars", "door", "trapdoor", "chain", "lantern",
    "upgrade_template",
]

#: 11 种「建材」形态（材料块 + 砖块系列 + 柱 + 栏杆 + 门 + 活板门 + 链 + 灯笼）
BUILDING_FORMS = [
    "block", "bricks", "bricks_stairs", "bricks_slab", "bricks_wall",
    "pillar", "bars", "door", "trapdoor", "chain", "lantern",
]

#: 必备形态（关掉它们 = 配置错误；Java 侧 register() 抛异常）
REQUIRED_FORMS = ["ingot", "block"]

#: 各族声明的形态集合；**不在表里的族 = 全集**（既有 8 族逐字不变）
#:   chaosgold   混沌金：没有「原料」（zip 无该贴图，歧义 ⑱c 未裁）与「升级锻造模板」（zip 无，歧义 ㉑）
#:   chaosalloy  崩乱合金：只做 锭 + 块 + 模板（11 种建材 / 粒 / 原料 全部不做）
FORMS: dict[str, list[str]] = {
    "chaosgold": [f for f in ALL_FORMS if f not in ("raw", "upgrade_template")],
    "chaosalloy": ["ingot", "block", "upgrade_template"],
}

#: 器具 / 武器 / 盔甲：恒定注册，不参与形态子集（列在这里只为让下游少写一份清单）
GEAR_SUFFIXES = [
    "sword", "axe", "pickaxe", "shovel", "hoe", "knife",
    "mace", "bow", "crossbow", "trident", "shield",
    "helmet", "chestplate", "leggings", "boots",
]

#: 「本轮产哪些类别的配方」—— **不是**形态问题，是轮次边界（立档 §5 的轮次表）：
#:   material = 原料/锭/粒/块那几条；building = 建材那几条；gear = 升级锻造模板 + 锻造升级
#:   缺省（不在表里的族）= 三类全产（既有 8 族逐字不变）
#:   chaosgold  轮2：材料 + 建材（锻造升级要 `chaosgold_upgrade_template`，而 zip 里没有这张
#:              贴图 —— 立档歧义 ㉑ 未裁 ⇒ 属轮3/轮4）
#:   chaosalloy 轮7：锭/块/模板/器具/盔甲/禁果 ⇒ 本轮**一个配方都不产**
#:              （它的模板配方也不是 `sturdygold_upgrade_template` 那条模板能表达的：
#:               作者截图给的是「6 混沌金锭 + 原版下界合金模板 + 崩乱合金锭 + 混沌金块」）
RECIPE_SCOPE: dict[str, set[str]] = {
    "chaosgold": {"material", "building"},
    "chaosalloy": set(),
}
DEFAULT_RECIPE_SCOPE: set[str] = {"material", "building", "gear"}


def forms_of(metal: str) -> list[str]:
    """该族声明的形态（不在表里 = 全集）"""
    return list(FORMS.get(metal, ALL_FORMS))


def has(metal: str, form: str) -> bool:
    """该族是否声明了某形态"""
    return form in forms_of(metal)


def building_of(metal: str) -> list[str]:
    """该族实际注册的建材形态（顺序 = BUILDING_FORMS）"""
    declared = forms_of(metal)
    return [f for f in BUILDING_FORMS if f in declared]


def loot_blocks_of(metal: str) -> list[str]:
    """该族需要的方块战利品表后缀（= 建材形态；块也有一张）"""
    return building_of(metal)


def recipe_scope_of(metal: str) -> set[str]:
    """该族本轮要产出的配方类别（material / building / gear）"""
    return set(RECIPE_SCOPE.get(metal, DEFAULT_RECIPE_SCOPE))


def recipe_forms_of(metal: str) -> list[str]:
    """该族本轮要产出配方的形态（材料 + 建材；器具/甲胄不算形态）"""
    scope = recipe_scope_of(metal)
    out: list[str] = []
    if "material" in scope:
        for form in ("raw", "ingot", "nugget", "block"):
            if has(metal, form):
                out.append(form)
    if "building" in scope:
        for form in building_of(metal):
            if form not in out:
                out.append(form)
    if "gear" in scope:
        for form in ("upgrade_template",):
            if has(metal, form):
                out.append(form)
    return out


def jvm_class_hint() -> str:
    """给 `[bgn10-forms-parity]` 用：Java 侧形态名与顺序的说明串（不许改格式）"""
    return "MetalFamily.Form: " + ", ".join(ALL_FORMS)
