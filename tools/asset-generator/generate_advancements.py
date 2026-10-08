#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-ach：生成 51 个进度（成就）JSON + 供关卡使用的清单。

真源 = 本文件末尾的 ``ADVANCEMENTS`` 表（每条的 id / parent / 图标 / 判定 / 文案键）。
产出：
  1. ``src/main/resources/data/bettergold/advancement/<path>.json`` 共 51 个；
  2. ``tools/asset-generator/advancement_manifest.json``（关卡与语言键核对用的机器清单）。

口径（全部【读源码】核实过，见 docs/1.6-规格.md 的 bg-ach 节）：
  * 1.21.1 的 ``Advancement`` codec：``parent`` / ``display`` / ``rewards`` / ``criteria``(必需非空) /
    ``requirements``(可省，省略 = 每个 criteria 各自一组 = 全部 AND) / ``sends_telemetry_event``。
  * ``DisplayInfo`` codec：``icon``(ItemStack.STRICT_CODEC，形如 ``{"id":...,"count":1}``) /
    ``title`` / ``description`` / ``background`` / ``frame``(默认 task) / ``show_toast``(默认 true) /
    ``announce_to_chat``(默认 true) / ``hidden``(默认 false)。
  * ``inventory_changed`` 的 ``conditions.items`` 是 ``List<ItemPredicate>``：
    **1 条** ⇒ 只拿"本次变化的那一格"去比（`InventoryChangeTrigger.java:99-101`）；
    **≥2 条** ⇒ 扫整个背包、逐条都要有（同一格可以满足多条）⇒ 天然是 **AND**。
    单条 ``ItemPredicate`` 自己的 ``items`` 是 ``HolderSet``（list / tag）⇒ 天然是 **OR**。
  * ``player_hurt_entity`` 的 ``damage.type.source_entity.equipment.mainhand`` 形状照抄原版
    ``data/minecraft/advancement/adventure/overoverkill.json``（"用某种主手物品命中"的原版范式）。
  * ``placed_block`` / ``item_used_on_block`` 的 ``conditions.location`` 是 LootItemCondition 列表
    （列表内部 **AND**）⇒ 想表达 OR 只能拆成多个 criteria 放进同一个 requirement 组。
  * ``recipe_crafted`` 的 ``recipe_id`` 是**裸 ResourceLocation**（不查注册表）
    ⇒ 引用"条件注册的物品"时**不会**引起解析失败（这正是 root 判据选它的原因）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Windows 控制台是 GBK：非 GBK 字符（U+21D2 之类）会让 print 直接抛 UnicodeEncodeError，
# 于是"关卡红了"变成"关卡崩了"（扰动实测会记成"没命中"）。这里兜底成替换符。
# ==== bg-final 实测教训（2026-10-05）：本文件原先没有这一行，于是只要 bg-final 断言里的
# 消息带 U+21D2，进程就死在那一句 print 上、连"问题: N"都不打 ⇒ 扰动矩阵看起来像"没红"。====
try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "advancement"
LANG = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang"
MANIFEST = Path(__file__).resolve().parent / "advancement_manifest.json"

NS = "bettergold"

# ---------------------------------------------------------------- 物品清单（真源，逐个核过）
METALS = ["flamegold", "sturdygold", "thornsgold", "echogold",
          "indigoseagold", "voodoogold", "thundergold", "illusiongold"]
# 与 material/MetalFamily.java:671-745 的注册后缀逐字一致
GEAR_SUFFIX = ["sword", "axe", "pickaxe", "shovel", "hoe",
               "mace", "bow", "crossbow", "trident", "shield"]
ARMOR_SUFFIX = ["helmet", "chestplate", "leggings", "boots"]


def gear(metal: str) -> list[str]:
    return [f"{NS}:{metal}_{s}" for s in GEAR_SUFFIX]


# ⚠ bg-ach §七.6（作者 2026-10-05：「**乐事的刀不会触发有关获得器具的进度**」）：
#   「获得任意一种 XX金武器工具」这 8 条成就**不把刀算进去**。
#   本仓的刀（`<metal>_knife`，走可选依赖 FD 的 `KnifeItem`）**就在 `GEAR_SUFFIX` 之外** ⇒
#   按物品 id 排除这条规则**天然成立**（不需要再按标签排除）；
#   本轮把它**显式钉成断言**（validate_advancements.py 的 `[bgach-no-knife-in-gear]`），
#   免得以后有人"顺手"把 knife 加回 GEAR_SUFFIX 而静默改变 8 条成就的口径。
#
# ⛔⛔ **bg-fix3 §二（作者 2026-10-07）把上面这条口径整个作废**：
#   作者原话「**乐事联动的刀仍然无法触发获得任意一种器具的成就**」＝**缺陷**（不是"不应该触发"）。
#   ⇒ 现行口径：**乐事小刀必须能触发**这 8 条「获得任意一种 XX金武器工具」成就。
#   ⚠ 旧口径原文**逐字保留在上面**（未删），只在此就地标注作废；全文对照落在
#     `docs/1.6-规格.md` §二十二。
#   ⚠ `GEAR_SUFFIX` **仍然不含 knife**（它是"该族 10 件武器工具"的清单，刀走另一条判据）——
#     刀的纳入方式是给每条武器成就加一条 `have_knife` 判据，见 `WEAPON_KNIFE_TAG`。
KNIVES = [f"{NS}:{m}_knife" for m in METALS]

# bg-fix3 §二：每条武器成就的"刀"判据读的物品标签（`<族>_knives`）。
#   **为什么不把 8 个 `_knife` id 直接写进 `have` 的 items 列表**（本轮实测的硬约束）：
#   `ItemPredicate.items` 是 `RegistryCodecs.homogeneousList(Registries.ITEM)` ⇒ **解析期**就要在
#   冻结的物品注册表里查到 id，查不到 ⇒ 报 `Unknown element` 并**丢掉整份成就 JSON**
#   （mcmod_experience `ex/04` 第 65 条；手册物品在 root 上踩过同一条）。
#   而乐事小刀**只在装了 FD 时**才注册（`fd/FdItems` 反射创建）⇒ 直接写裸 id 会让 8 条成就
#   在"没装乐事"的环境里**整批消失**。
#   ⇒ 唯一安全形态 = `items` 指向**一张标签**（`HolderSet` 的 tag 分支，写 `"#ns:tag"` 单个字符串），
#     标签里那一行写成 `{"id": ..., "required": false}` ⇒ 没装 FD 时**静默跳过**、标签照常加载
#     （空集 ⇒ 判据永不达成，但**不报错、不丢文件**）。标签由 `generate_metal_tags.py` 生成。
def weapon_knife_tag(metal: str) -> str:
    return f"{NS}:{metal}_knives"


# ⚠ **旧口径原文保留（未删），bg-fix3 §二 之后它已经不成立了**：
#   「已知不一致（记录在 docs/1.6-规格.md §18.3，**没有自行改手册**）：手册「器具同框」那一页
#    （bg-book §3.4 / 生成器 `TOOLS = [sword, axe, pickaxe, shovel, hoe, knife]`）把刀算作器具，
#    而进度这边不算 —— 两处口径不同，作者一句话即可统一。」
#   ⇒ 2026-10-07 作者的那句话就是「**乐事联动的刀仍然无法触发获得任意一种器具的成就**」：
#     刀算器具 ⇒ **两处口径现已一致**（手册含刀、进度也含刀），§17.5 第 4 条随之关闭。


def armor(metal: str) -> list[str]:
    return [f"{NS}:{metal}_{s}" for s in ARMOR_SUFFIX]


# 8 个核心材料（MetalSpecialItems.java + AllItems.GOLDEN_COWRIE）
CORE_MATERIALS = [
    f"{NS}:blazing_rod", f"{NS}:golden_cowrie", f"{NS}:glittering_vine",
    f"{NS}:bundled_echo_shard", f"{NS}:indigo_ocean_heart", f"{NS}:voodoo_feather",
    f"{NS}:amethyst_energy_dust", f"{NS}:chorus_cherry_branch",
]
# 8 个原料（MetalFamily:662 `raw_` + id）—— 同时就是它们的配方 id
RAW_MATERIALS = [f"{NS}:raw_{m}" for m in
                 ["flamegold", "voodoogold", "thundergold", "indigoseagold",
                  "illusiongold", "thornsgold", "echogold", "sturdygold"]]

# 金食物（非乐事）= 本仓所有带 FOOD 组件、id 属于"金食物"的物品（靠 Java 真源逐条列；关卡会复核）
GOLD_FOODS = [
    "minecraft:golden_apple", "minecraft:golden_carrot",
    f"{NS}:golden_chocolate_bar", f"{NS}:brewed_hot_cocoa", f"{NS}:golden_ice_cream",
    f"{NS}:golden_sugar_cane_stick", f"{NS}:golden_eggplant", f"{NS}:fried_golden_egg",
    f"{NS}:golden_chocolate_cookie", f"{NS}:golden_honey_cookie", f"{NS}:golden_bread",
    f"{NS}:golden_egg_sandwich",
]
STURDYGOLD_FOODS = [
    f"{NS}:sturdygold_apple", f"{NS}:sturdygold_carrot", f"{NS}:sturdygold_chocolate_bar",
    f"{NS}:sturdygold_brewed_hot_cocoa", f"{NS}:sturdygold_ice_cream",
    f"{NS}:sturdygold_sugar_cane_stick", f"{NS}:sturdygold_eggplant", f"{NS}:sturdygold_bread",
    f"{NS}:sturdygold_fried_golden_egg", f"{NS}:sturdygold_chocolate_cookie",
    f"{NS}:sturdygold_honey_cookie", f"{NS}:sturdygold_egg_sandwich",
]
# 乐事联动金食物（fd/FdItems.java）
FD_GOLD_FOODS = [
    f"{NS}:alchemical_meat", f"{NS}:alchemical_meat_skewer", f"{NS}:alchemical_meat_sandwich",
    f"{NS}:golden_glow_custard", f"{NS}:golden_apple_cider", f"{NS}:golden_pie_crust",
    f"{NS}:golden_apple_pie_slice", f"{NS}:golden_chocolate_pie_slice", f"{NS}:golden_cake_slice",
]
FD_STURDYGOLD_FOODS = [
    f"{NS}:sturdygold_alchemical_meat", f"{NS}:sturdygold_alchemical_meat_skewer",
    f"{NS}:sturdygold_alchemical_meat_sandwich", f"{NS}:sturdygold_glow_custard",
    f"{NS}:sturdygold_apple_cider", f"{NS}:sturdygold_apple_pie_slice",
    f"{NS}:sturdygold_chocolate_pie_slice", f"{NS}:sturdygold_cake_slice",
]
ANTIQUE_TOOLS = [f"{NS}:antique_{s}" for s in ["sword", "axe", "pickaxe", "shovel", "hoe"]]
NETHERITE_ANTIQUE_TOOLS = [f"{NS}:netherite_antique_{s}" for s in
                           ["sword", "axe", "pickaxe", "shovel", "hoe"]]

# ---------------------------------------------------------------- bg-fix4 §一（2026-10-08）
# 作者原话（逐字）：「**古董屠刀和幽冥断骸刀无法触发上古藏品和皇骸永存的进度**」。
# 根因（本文件复核确认）：两条成就的 `criteria.have.conditions.items[0].items` 各只有上面那
#   **5 件**——`antique_knife` / `netherite_antique_knife` 根本不在白名单里 ⇒ 拿到刀也不匹配。
# ★ 与 `bg-fix3` §二 是**同族问题、同一条硬约束**：两把刀都在 `fd/FdItems.java:192/196` 注册
#   ⇒ **只在装了乐事时才存在** ⇒ 把裸 id 写进 `items` 会让这两条成就在"没装乐事"的环境里
#   **整份 JSON 解析失败并消失**（`ItemPredicate.items` 是 `homogeneousList`，解析期查注册表）。
# ⇒ 落法（照 `bg-fix3` §二 已 A 级验证过的安全范式）：
#   ① `generate_metal_tags.py` 生成两张**无条件存在**的标签（各 1 条 `required:false` 条目）；
#   ② 两条成就各**再加一条**判据 `have_knife`，`items` 指向那张标签（`"#ns:tag"` **单个字符串**）；
#   ③ `requirements` 变成 `[["have", "have_knife"]]`（**组内 OR** ⇒ "5 件古董工具 **或** 屠刀"）。
#   ⚠ 不许把 `#tag` 混进 `items` 的**列表**里（`ensureHomogenous` 只接受同一种 Holder 形态）。
ANTIQUE_KNIFE_TAG = f"{NS}:antique_knives"
NETHERITE_ANTIQUE_KNIFE_TAG = f"{NS}:netherite_antique_knives"
# 4 个礼品盒 + 1.6 的炼金珍材盒（都是 GiftBoxItem，都由易金商人卖）
GIFT_BOXES = [f"{NS}:treasure_gift_box", f"{NS}:curio_box", f"{NS}:idol_gift_box",
              f"{NS}:gourmet_box", f"{NS}:alchemy_materials_box"]

# ---------------------------------------------------------------- 判据构造器
FD_CONDITION = [{"type": "neoforge:mod_loaded", "modid": "farmersdelight"}]


def c_inv(items: list[str], structure: str | None = None) -> dict:
    """inventory_changed：items 单条 ⇒ 只比"变化的那一格"（OR 语义）；多条 ⇒ 扫全背包 AND。"""
    predicates = [{"items": i} for i in items]
    cond: dict = {"items": predicates}
    if structure:
        cond["player"] = [{
            "condition": "minecraft:entity_properties",
            "entity": "this",
            "predicate": {"location": {"structures": structure}},
        }]
    return {"trigger": "minecraft:inventory_changed", "conditions": cond}


def c_inv_tag(tag_id: str) -> dict:
    """``inventory_changed``：``items`` 指向**一个物品标签**（`HolderSet` 的 tag 分支）。

    bg-fix3（2026-10-07）新增 —— 用来引用"**只在装了某个可选模组时才存在**的物品"：
    标签里那一行写 ``{"id": ..., "required": false}``（见 ``generate_metal_tags.py``），
    没装时静默跳过、标签照常加载 ⇒ **判据永不达成，但不报错、不丢文件**。
    ⚠ 必须写成一个**单元素列表**（= 一个 ``ItemPredicate``）：``items.size() == 1`` 时
    `InventoryChangeTrigger` 只拿"本次变化的那一格"去比（`InventoryChangeTrigger.java:108`）。
    ⚠ ``tag_id`` 必须是**完整的** `namespace:path`（不是裸 path）—— 少了命名空间会解析成
    `#handbook` 这种不存在的标签，而 `HolderSetCodec.lookupTag` 对"标签不存在"是
    `DataResult.error("Missing tag: …")` ⇒ **整份成就 JSON 被丢掉**（实测踩过一次）。
    """
    assert ":" in tag_id, f"标签 id 必须是 namespace:path，收到 {tag_id!r}"
    return {"trigger": "minecraft:inventory_changed",
            "conditions": {"items": [{"items": f"#{tag_id}"}]}}


def c_recipe(recipe_id: str) -> dict:
    return {"trigger": "minecraft:recipe_crafted", "conditions": {"recipe_id": recipe_id}}


def c_trade(items: list[str]) -> dict:
    return {"trigger": "minecraft:villager_trade", "conditions": {"item": {"items": items}}}


def c_skeletons(weapons: list[str]) -> dict:
    return {
        "trigger": "minecraft:player_hurt_entity",
        "conditions": {
            "entity": [{
                "condition": "minecraft:entity_properties",
                "entity": "this",
                "predicate": {"type": "#minecraft:skeletons"},
            }],
            "damage": {"type": {"source_entity": {
                "type": "minecraft:player",
                "equipment": {"mainhand": {"items": weapons}},
            }}},
        },
    }


def c_till_farmland() -> dict:
    return {
        "trigger": "minecraft:item_used_on_block",
        "conditions": {"location": [
            {"condition": "minecraft:location_check",
             "predicate": {"block": {"blocks": f"{NS}:gold_infused_farmland"}}},
            {"condition": "minecraft:match_tool", "predicate": {"items": "#minecraft:hoes"}},
        ]},
    }


def c_plant_crop(block: str) -> dict:
    return {
        "trigger": "minecraft:placed_block",
        "conditions": {"location": [
            {"condition": "minecraft:block_state_property", "block": block},
        ]},
    }


# ---------------------------------------------------------------- 51 条表（真源）
def build() -> list[dict]:
    A: list[dict] = []

    def add(path, key, title, desc, icon, parent, criteria, requirements,
            frame="task", fd=False):
        A.append(dict(path=path, key=key, title=title, desc=desc, icon=icon,
                      parent=parent, criteria=criteria, requirements=requirements,
                      frame=frame, fd=fd))

    # ---- §3.1 根与炼制（3）
    # ⚠ bg-ach §七.2（作者 2026-10-05）：「"制作"条件什么的请给它无视掉，只要是**获得某样物品就能够触发**
    #   成就（但**除了「这件商品很适合你哦~」这个成就**）」⇒ 凡原文写「制作 X」的成就一律改成
    #   `minecraft:inventory_changed`（合成 / 拾取 / 交易 / 任何途径获得都会触发）；
    #   **唯一例外** = merchant/gift_box（仍是 `villager_trade`，见 §3.4）。
    #   ⚠ 作者给的**标题 / 简介文案一个字都没动**（§5.3 陷阱 4「逐字用」）：简介里那句「制作 X」
    #     保留为原文、与判定口径分离 —— 这是本轮记在 docs/1.6-规格.md §18.2 的已知差异。
    #
    # ⛔ **bg-fix3 §四（作者 2026-10-07）：根也要改「获得」** ——
    #   作者原话「旧时代的炼金术师继承者进度**触发条件是获得**新生代炼金术学员手册」。
    #   ⚠ 旧口径原文保留（它曾是 §七.2 里**唯一**故意留着 `recipe_crafted` 的一条）：
    #     `{"craft_handbook": c_recipe(f"{NS}:alchemy_student_handbook")}`，理由 =「手册物品在
    #     **没装 Patchouli 时根本不注册**，而 `recipe_crafted.recipe_id` 是**裸 ResourceLocation**
    #     （不查注册表）⇒ 不会引起解析失败」（§14.3）。
    #   ⇒ 现行落法：`inventory_changed` + `items` 指向标签 `#bettergold:handbook`
    #     （标签里那一行 `{"id":"bettergold:alchemy_student_handbook","required":false}`）
    #     —— 既满足"获得即触发"，又保持"没装 Patchouli 时不报错、其余 50 条照常加载"。
    #   ⇒ **全 51 条成就从此一条 `recipe_crafted` 都没有了**（关卡 `[bgfix3-recipe-crafted-none]` 守着）。
    add("root", "root", "旧时代炼金术的继承者", "以炼制\"贵金\"为主要目标，出发！",
        "minecraft:gold_ingot", None,
        {"have_handbook": c_inv_tag(f"{NS}:handbook")},
        [["have_handbook"]])
    add("alchemy/mixed_crystal_pile", "mixed_crystal_pile",
        "炼制\"贵金\"所需I", "制作混合晶石堆", f"{NS}:mixed_crystal_pile", "root",
        {"have": c_inv([f"{NS}:mixed_crystal_pile"])}, [["have"]])
    # ⛔ **bg-fix3 §五（作者 2026-10-07）把根链改成"链式"** ——
    #   ★★ **总原则（作者 2026-10-07 原话：「需要第二个改成我现在的，所有现在给你发的改动
    #     都是我现在的版本」）：作者随后发来的改动 = 他的"当前版本" ⇒ 一律以最新文档为准；
    #     旧结构 / 旧排列（例如上一轮的「并列」）只作历史留档、不再当有效口径。**
    #     ⚠ 旧口径原文一律**就地标注、不删**（本注释下方每条 ⚠ 都是这种标注）。
    #     📌 **bg-fix3b（2026-10-07 复核）：下面这条链式根链与作者文档 §五 的字面逐字一致
    #       ⇒ 本轮未改动任何 parent。** 依据：`docs/1.6-规格.md` §23。
    #   作者本轮重述的根链：「旧时代的炼金术继承者 — 炼制"贵金"所需I — 炼制"贵金"所需II —
    #   寻途千里的珍宝 — 9 个分支，八个金属相关，一个齐活，烧炼，拿下！」
    #   ⚠ **与上一轮裁定冲突**：上一轮（bg-ach §14.1 / §17.4 第 4 条）按作者的「**并列**」把
    #     炼制I / 炼制II / 寻途 都挂在 root 下。
    #     ★ 旧口径原文（**已被作者 2026-10-07 当前版本取代**，逐字保留、不删）：
    #       mixed_crystal_pile.parent = "root"   （炼制I  —— 链首，新旧完全一致）
    #       alchemic_fuel.parent      = "root"   （炼制II —— 旧口径「并列」）
    #       any_core_material.parent  = "root"   （寻途    —— 旧口径「并列」）
    #   ⇒ 现行：`mixed_crystal_pile`（root 下）→ `alchemic_fuel` → `any_core_material`（寻途）。
    #   ⚠ 作者一句话即可改回并列（把这两条的 parent 改回 "root"；该口径已作废，只作历史留档）。
    #   ⚠ **需求没覆盖的新选择（本轮取值，记在 docs/1.6-规格.md §22 与汇报里）**：
    #     作者只重述了 4 节链、没提两条农业成就 ⇒ 「土地也要染上黄金」与「也是吃上科技啊呸」
    #     **仍留在 root 下**（否则它们会变成从 root 不可达的孤点）。
    add("alchemy/alchemic_fuel", "alchemic_fuel",
        "炼制\"贵金\"所需II", "制作炼金燃油", f"{NS}:alchemic_fuel", "alchemy/mixed_crystal_pile",
        {"have": c_inv([f"{NS}:alchemic_fuel"])}, [["have"]])

    # ---- §3.2 珍宝与 8 个核心材料（10）
    # ⛔ bg-fix3 §五：寻途的 parent 由 "root" 改成链上一节（炼制所需II）—— 旧口径原文见上。
    add("treasure/any_core_material", "core_material",
        "寻途千里的珍宝", "获得任意一种\"贵金\"核心材料",
        f"{NS}:golden_cowrie", "alchemy/alchemic_fuel",
        {"have": c_inv([CORE_MATERIALS])}, [["have"]])
    treasure_parent = "treasure/any_core_material"
    add("treasure/blazing_rod", "blazing_rod", "超 燃 大 火 杆 ！", "制作一个高燃烈焰棒",
        f"{NS}:blazing_rod", treasure_parent,
        {"have": c_inv([f"{NS}:blazing_rod"])}, [["have"]])
    add("treasure/golden_cowrie", "golden_cowrie", "留于炽海的旧忆之贝", "获得一个金钱贝",
        f"{NS}:golden_cowrie", treasure_parent,
        {"have": c_inv([f"{NS}:golden_cowrie"])}, [["have"]])
    add("treasure/glittering_vine", "glittering_vine", "暗中之藤，光芒乍现", "获得一个闪耀藤条",
        f"{NS}:glittering_vine", treasure_parent,
        {"have": c_inv([f"{NS}:glittering_vine"])}, [["have"]])
    add("treasure/bundled_echo_shard", "bundled_echo_shard",
        "装填，捆绑，然后赶紧…", "制作一个集束回响碎片", f"{NS}:bundled_echo_shard", treasure_parent,
        {"have": c_inv([f"{NS}:bundled_echo_shard"])}, [["have"]])
    add("treasure/indigo_ocean_heart", "indigo_ocean_heart", "淀入深海", "制作一个靛蓝海洋之心",
        f"{NS}:indigo_ocean_heart", treasure_parent,
        {"have": c_inv([f"{NS}:indigo_ocean_heart"])}, [["have"]])
    add("treasure/voodoo_feather", "voodoo_feather", "复制品般的无光之毛", "获得一个巫毒羽毛",
        f"{NS}:voodoo_feather", treasure_parent,
        {"have": c_inv([f"{NS}:voodoo_feather"])}, [["have"]])
    add("treasure/amethyst_energy_dust", "amethyst_energy_dust", "红紫回旋 大·爆炸",
        "制作一个聚紫能晶尘", f"{NS}:amethyst_energy_dust", treasure_parent,
        {"have": c_inv([f"{NS}:amethyst_energy_dust"])}, [["have"]])
    # ⚠ §七.3 改名：「未外重叠的花香」→「末外重叠的花香」（只改这一个字）
    add("treasure/chorus_cherry_branch", "chorus_cherry_branch", "末外重叠的花香",
        "制作一个紫颂樱花枝", f"{NS}:chorus_cherry_branch", treasure_parent,
        {"have": c_inv([f"{NS}:chorus_cherry_branch"])}, [["have"]])
    add("treasure/any_raw_metal", "raw_metal", "齐活，烧炼，拿下！",
        "制作出任意一种\"贵金\"原料", f"{NS}:raw_sturdygold", treasure_parent,
        {"have": c_inv(RAW_MATERIALS)}, [["have"]])

    # ---- §3.3 八条金属线（25）
    # 每条线：核心材料成就 → 锭 →（武器工具 / 整套盔甲）；万坚金多一条挑战 ⑲
    lines = [
        # (金属, 锭成就标题, 锭成就简介, 武器成就标题, 盔甲成就标题, 核心材料 parent)
        ("flamegold", "我 获 得 了 烈 燃 金 ！！！", "当务之急就是缺一个老虎在那向前奔跑…",
         "高 温 恒 续", "何 你 火", "treasure/blazing_rod"),
        ("sturdygold", "这以后将是我们人生中第一桶金", "我们可以用这个金属做很多事哦！",
         "染上黄金吧，指的是你的血", "连我的血也沾染了黄金啊", "treasure/golden_cowrie"),
        ("thornsgold", "我被一块金属锭？扎到了？！", "可它明明看起来那么光滑…",
         "摄取之绿", "看似吉利服实则移动的仙人掌", "treasure/glittering_vine"),
        ("echogold", "就这样轰轰烈烈的登场", "感觉可以拿这玩意做大音箱！",
         "等着看好戏吧，关于鼓手的", "苏打色的战甲配上劲爆的音乐", "treasure/bundled_echo_shard"),
        ("indigoseagold", "坠海浮靛", "这块金属～是水炼的，是水炼的",
         "以强力水压重击", "深海游行者", "treasure/indigo_ocean_heart"),
        ("voodoogold", "毒液渗透之物", "这块金属所散发出的毒素十分让人不安",
         "极具威胁的灭绝性毒素", "你的全身发紫可能看着就不好惹", "treasure/voodoo_feather"),
        ("thundergold", "这块金属一定要是这种雷霆粉吗", "那不是粉色，是品红！",
         "手段麻痹之雷", "我只是个路过的避雷针", "treasure/amethyst_energy_dust"),
        ("illusiongold", "永恒迷幻", "这块金属所散发出的花香，令人着迷",
         "要不要休息一下呀～", "就这样静下心来吧～", "treasure/chorus_cherry_branch"),
    ]
    for metal, ingot_title, ingot_desc, weapon_title, armor_title, core_parent in lines:
        base = f"metal/{metal}"
        ingot = f"{base}/ingot"
        add(ingot, f"{metal}_ingot", ingot_title, ingot_desc, f"{NS}:{metal}_ingot", core_parent,
            {"have": c_inv([f"{NS}:{metal}_ingot"])}, [["have"]])
        # ⛔ bg-fix3 §二（2026-10-07）：刀的纳入方式 = 给这条武器成就**再加一条判据**
        #   `have_knife`（items 指向该族的 `<族>_knives` 标签），两条判据放进**同一个
        #   requirement 组**（组内 OR）⇒ 「10 件武器工具 **或** 乐事小刀」都算获得。
        #   ⚠ 旧口径（原文保留，未删）：本轮之前这里只有 `{"have": c_inv([gear(metal)])}` +
        #     `[["have"]]`，刀被 `[bgach-no-knife-in-gear]` 的负向断言挡在外面。
        add(f"{base}/weapon", f"{metal}_weapon", weapon_title,
            f"获得任意一种{ {'flamegold': '烈燃金', 'sturdygold': '万坚金', 'thornsgold': '树棘金',
                              'echogold': '幽咆金', 'indigoseagold': '靛海金', 'voodoogold': '巫毒金',
                              'thundergold': '结雷金', 'illusiongold': '幻惑金'}[metal] }武器工具",
            f"{NS}:{metal}_sword", ingot,
            {"have": c_inv([gear(metal)]),
             "have_knife": c_inv_tag(weapon_knife_tag(metal))},
            [["have", "have_knife"]])
        # ★ 作者 2026-10-05 核定：**只有万坚金那条**把「整套盔甲」挂在「染上黄金吧」（武器）之下
        #   —— 因为那一条在武器处一分为三（骷髅打金服 / 整套盔甲 / 奢华一票→商人线）；
        #   其余 7 套的武器与盔甲都是「锭」的两个并列孩子。
        # ⛔ **bg-fix3 §五（作者 2026-10-07）把上面这条推翻**：作者本轮给的排版是
        #   「原材料 - 材料锭 - 材料剑 - 材料盔甲」= **四级链** ⇒ **八族一律** 盔甲挂在武器之下
        #   （旧口径原文保留在上面，未删）。
        armor_parent = f"{base}/weapon"
        # ⛔ bg-fix3 §五②：**八条盔甲全部改成「挑战进度」**（frame=challenge）。
        #   旧口径（原文保留）：`frame` 省略 = 默认 `task`，全 51 条里只有
        #   `metal/sturdygold/skeleton`（骷髅打金服）是 challenge。
        add(f"{base}/armor", f"{metal}_armor", armor_title,
            f"获得一整套{ {'flamegold': '烈燃金', 'sturdygold': '万坚金', 'thornsgold': '树棘金',
                            'echogold': '幽咆金', 'indigoseagold': '靛海金', 'voodoogold': '巫毒金',
                            'thundergold': '结雷金', 'illusiongold': '幻惑金'}[metal] }盔甲",
            f"{NS}:{metal}_chestplate", armor_parent,
            {f"armor_{s}": c_inv([f"{NS}:{metal}_{s}"]) for s in ARMOR_SUFFIX},
            # ⚠ requirements 的语义：**组内是 OR、组间是 AND**（`AdvancementRequirements#test`）
            #   ⇒ "一整套"必须是「每个部位各自一组」，写成一个大组就等于"任意一件"。
            [[f"armor_{s}"] for s in ARMOR_SUFFIX],
            frame="challenge")
        if metal == "sturdygold":
            # ⑲ 骷髅打金服（紫色挑战）—— parent 挂在「染上黄金吧」之下（作者 2026-10-05 核定）
            add(f"{base}/skeleton", "sturdygold_skeleton", "骷髅打金服",
                "用万坚金武器工具攻击骷髅使其掉落金骨粉", f"{NS}:golden_bone_meal",
                f"{base}/weapon", {"hit": c_skeletons(gear("sturdygold"))}, [["hit"]],
                frame="challenge")

    # ---- §3.4 商人线（4）
    add("merchant/gold_ticket", "gift_gold_ticket", "奢华一票", "获得礼品金票",
        f"{NS}:gift_gold_ticket", "metal/sturdygold/weapon",
        {"have": c_inv([f"{NS}:gift_gold_ticket"])}, [["have"]])
    add("merchant/gift_box", "gift_box", "这件商品很适合你哦～",
        "从易金商人那获得任意一种礼品盒", f"{NS}:treasure_gift_box", "merchant/gold_ticket",
        {"traded": c_trade(GIFT_BOXES)}, [["traded"]])
    # ⛔ bg-fix4 §一（2026-10-08）：**两把刀也要算数** —— 各加一条 `have_knife` 判据
    #   （items 指向 `#bettergold:antique_knives` / `#bettergold:netherite_antique_knives`），
    #   与 `have` 放进**同一个 requirement 组**（组内 OR）。
    #   ⚠ 旧口径（原文保留，未删）：本轮之前这里是 `{"have": c_inv([ANTIQUE_TOOLS])}` + `[["have"]]`，
    #     古董屠刀 / 幽冥断骸刀拿到也不解锁（作者本轮复报的缺陷）。
    add("merchant/antique_tool", "antique_tool", "上古藏品", "获得任意一种古董武器工具",
        f"{NS}:antique_sword", "merchant/gift_box",
        {"have": c_inv([ANTIQUE_TOOLS]),
         "have_knife": c_inv_tag(ANTIQUE_KNIFE_TAG)}, [["have", "have_knife"]])
    add("merchant/netherite_antique_tool", "netherite_antique_tool", "皇骸永存",
        "好好保养这份藏品吧", f"{NS}:netherite_antique_sword", "merchant/antique_tool",
        {"have": c_inv([NETHERITE_ANTIQUE_TOOLS]),
         "have_knife": c_inv_tag(NETHERITE_ANTIQUE_KNIFE_TAG)}, [["have", "have_knife"]])

    # ---- §3.5 农业与食物（9）
    farm = "agriculture/gold_infused_dirt"
    add("agriculture/gold_infused_dirt", "gold_infused_dirt", "土地也要染上黄金", "制作金染土",
        f"{NS}:gold_infused_dirt", "root",
        {"have": c_inv([f"{NS}:gold_infused_dirt"])}, [["have"]])
    add("agriculture/eggplant_seeds", "eggplant_seeds", "光辉岁月之种",
        "在遗迹堡垒里获得金钱茄种子", f"{NS}:golden_eggplant_seeds", farm,
        {"have": c_inv([f"{NS}:golden_eggplant_seeds"], structure="minecraft:bastion_remnant")},
        [["have"]])
    add("agriculture/golden_egg", "golden_egg", "好大的金蛋～",
        "使用金种子喂给鸡从而获取金蛋", f"{NS}:golden_egg", farm,
        {"have": c_inv([f"{NS}:golden_egg"])}, [["have"]])
    add("agriculture/plant_gold_crop", "plant_gold_crop", "开垦我的金色土地",
        "为金染土进行耕地，并种植任意一种金作物", f"{NS}:golden_wheat", farm,
        {
            "till": c_till_farmland(),
            "plant_wheat": c_plant_crop(f"{NS}:golden_wheat_crop"),
            "plant_eggplant": c_plant_crop(f"{NS}:golden_eggplant_crop"),
            # bgfinal3（作者 2026-10-06 裁定「需要」）：金胡萝卜那半边补上。
            # ⚠ 金胡萝卜**不是** `BlockItem#place` 种下去的，而是 `ModEvents#onRightClickGoldenCarrot`
            #   里 `setBlock` + `setCanceled` 自定义种的 ⇒ 判据虽然同样是原版 `placed_block`，
            #   但**必须**由那段代码自己补一次 `CriteriaTriggers.PLACED_BLOCK.trigger(...)`
            #   （照 `BlockItem.java:78-85` 的姿势），否则这条 criteria 永远不达成。
            "plant_carrot": c_plant_crop(f"{NS}:golden_carrot_crop"),
        },
        [["till"], ["plant_wheat", "plant_eggplant", "plant_carrot"]])
    add("agriculture/midas_feast_1", "midas_feast_1", "米达斯之宴I", "获得所有金食物",
        f"{NS}:golden_bread", "agriculture/plant_gold_crop",
        {f"food_{f.replace(':', '_')}": c_inv([f]) for f in GOLD_FOODS},
        # "获得**所有**" ⇒ 每个食物各自一组（组间 AND）；写成一个大组就变成"任意一种"了
        [[f"food_{f.replace(':', '_')}"] for f in GOLD_FOODS])
    add("agriculture/sturdygold_feast_1", "sturdygold_feast_1", "再镀进化I",
        "获得所有万坚金食物", f"{NS}:sturdygold_bread", "agriculture/midas_feast_1",
        {f"food_{f.replace(':', '_')}": c_inv([f]) for f in STURDYGOLD_FOODS},
        [[f"food_{f.replace(':', '_')}"] for f in STURDYGOLD_FOODS])
    add("agriculture/alchemical_meat", "alchemical_meat", "也是吃上科技啊呸，炼金术之肉了",
        "获得炼金贝肉", f"{NS}:alchemical_meat", "root",
        {"have": c_inv([f"{NS}:alchemical_meat"])}, [["have"]], fd=True)
    add("agriculture/midas_feast_2", "midas_feast_2", "米达斯之宴II",
        "获得所有乐事联动的金食物", f"{NS}:alchemical_meat_skewer", "agriculture/alchemical_meat",
        {f"food_{f.replace(':', '_')}": c_inv([f]) for f in FD_GOLD_FOODS},
        [[f"food_{f.replace(':', '_')}"] for f in FD_GOLD_FOODS], fd=True)
    add("agriculture/sturdygold_feast_2", "sturdygold_feast_2", "再镀进化II",
        "获得所有乐事联动的万坚金食物", f"{NS}:sturdygold_alchemical_meat_skewer",
        "agriculture/midas_feast_2",
        {f"food_{f.replace(':', '_')}": c_inv([f]) for f in FD_STURDYGOLD_FOODS},
        [[f"food_{f.replace(':', '_')}"] for f in FD_STURDYGOLD_FOODS], fd=True)

    return A


LANG_PREFIX = "advancements.bettergold"

# ---------------------------------------------------------------------------
# 英文口径（1.6 收尾轮 bg-final 第 2 件，2026-10-05）
#
# ⚠ 旧口径（原文保留，未删）：作者 51 条标题/简介是他写的中文梗，需求文档 §5.3 陷阱 4 写
#   「英文缺失就留空或音译，别自己编」。「音译」对这类标题不成立、「留空」会在英文客户端显示空白标题
#   ⇒ 上一轮取第三条：**英文条目 = 中文原文逐字**（`EN_POLICY = "copy_zh"`，一个字都没自己编）。
#   作者本轮裁定：**102 条英文值必须是真的英译**（键名不动 / zh_cn 一个字不动 / 成就 id 不动）。
#
# 术语一律沿用既有 `assets/bettergold/lang/en_us.json` 与
# `docs/发布/1.5.0/CHANGELOG-1.5.0.md` 的写法，不新造：
#   Sturdygold / Flamegold / Voodoogold / Thundergold / Indigoseagold / Illusiongold /
#   Thornsgold / Echogold、Mixed Crystal Pile、Alchemic Fuel、Blazing Rod、Golden Cowrie、
#   Glittering Vine、Bundled Echo Shard、Indigo Ocean Heart、Voodoo Feather、
#   Amethyst Energy Dust、Chorus Cherry Branch、Gold-Infused Dirt、Golden Bone Meal、
#   Gold Trader、Alchemical Cowrie Meat、Sonic Roar / Sediment / Soothe（手册 en_us 与 1.5 变更日志）。
# 标题保持"梗"的语气、简介保持"怎么做"的字面意思；两条都不许与中文原值逐字相同
# （validate_advancements.py 的 [bgfinal-adv-lang-translated] 守着这条，纯符号/数字类标题才可豁免）。
# ---------------------------------------------------------------------------
EN_POLICY = "translate"

EN: dict[str, tuple[str, str]] = {  # advancement key -> (title, description)
    "root": ("Heir to the Old Alchemy",
             'Set out with smelting "noble gold" as your main goal!'),
    "mixed_crystal_pile": ("What Noble Gold Needs I", "Craft a Mixed Crystal Pile."),
    "alchemic_fuel": ("What Noble Gold Needs II", "Craft some Alchemic Fuel."),
    "core_material": ("Treasure of a Thousand-Mile Journey",
                      'Obtain any kind of "noble gold" core material.'),
    "blazing_rod": ("S U P E R  B L A Z I N G  R O D !", "Craft a Blazing Rod."),
    "golden_cowrie": ("An Old-Memory Shell Left in the Blazing Sea",
                      "Obtain a Golden Cowrie."),
    "glittering_vine": ("A Vine in the Dark, Suddenly Aglow",
                        "Obtain a Glittering Vine."),
    "bundled_echo_shard": ("Load It, Bundle It, and Then Hurry...",
                           "Craft a Bundled Echo Shard."),
    "indigo_ocean_heart": ("Sinking Into the Deep Sea",
                           "Craft an Indigo Ocean Heart."),
    "voodoo_feather": ("A Lightless Feather, Like a Copy",
                       "Obtain a Voodoo Feather."),
    "amethyst_energy_dust": ("Red-Purple Whirl: Big Bang",
                             "Craft some Amethyst Energy Dust."),
    "chorus_cherry_branch": ("Overlapping Fragrance, Unfolding",
                             "Craft a Chorus Cherry Branch."),
    "raw_metal": ("All Set, Smelt It, Taken!",
                  'Craft any kind of raw "noble gold" material.'),
    "flamegold_ingot": ("I  G O T  F L A M E G O L D !!!",
                        "The urgent thing is that we are one tiger-running-forward short..."),
    "flamegold_weapon": ("H I G H  H E A T  K E P T  U P",
                         "Obtain any kind of Flamegold weapon or tool."),
    "flamegold_armor": ("W H A T  A  F I R E  Y O U  A R E",
                        "Obtain a full set of Flamegold armor."),
    "sturdygold_ingot": ("Our First Pot of Gold in Life",
                         "We can do a lot of things with this metal!"),
    "sturdygold_weapon": ("Gild Yourself - I Mean Your Blood",
                          "Obtain any kind of Sturdygold weapon or tool."),
    "sturdygold_armor": ("Even My Blood Is Stained With Gold",
                         "Obtain a full set of Sturdygold armor."),
    "sturdygold_skeleton": ("Skeleton Gold Farm",
                            "Hit a skeleton with a Sturdygold weapon or tool so it drops Golden Bone Meal."),
    "thornsgold_ingot": ("Did an Ingot Just Prick Me?!",
                         "But it looked so smooth..."),
    "thornsgold_weapon": ("The Green That Takes In",
                          "Obtain any kind of Thornsgold weapon or tool."),
    "thornsgold_armor": ("Looks Like a Ghillie Suit, Is Actually a Walking Cactus",
                         "Obtain a full set of Thornsgold armor."),
    "echogold_ingot": ("A Roaring Entrance Just Like That",
                       "Feels like you could build a big speaker out of this!"),
    "echogold_weapon": ("Wait for the Show - This One Is About the Drummer",
                        "Obtain any kind of Echogold weapon or tool."),
    "echogold_armor": ("Soda-Colored Armor With Blasting Music",
                       "Obtain a full set of Echogold armor."),
    "indigoseagold_ingot": ("Indigo Floating on the Sunken Sea",
                            "This metal~ was smelted with water, smelted with water."),
    "indigoseagold_weapon": ("Struck Hard by Crushing Water Pressure",
                             "Obtain any kind of Indigoseagold weapon or tool."),
    "indigoseagold_armor": ("Deep-Sea Walker",
                            "Obtain a full set of Indigoseagold armor."),
    "voodoogold_ingot": ("Something Seeped Through With Venom",
                         "The toxin this metal gives off is deeply unsettling."),
    "voodoogold_weapon": ("An Exterminating Toxin of Great Threat",
                          "Obtain any kind of Voodoogold weapon or tool."),
    "voodoogold_armor": ("Purple All Over - Probably Not to Be Messed With",
                         "Obtain a full set of Voodoogold armor."),
    "thundergold_ingot": ("Must This Metal Really Be Thunder-Pink?",
                          "That is not pink, it is magenta!"),
    "thundergold_weapon": ("A Numbing Bolt of Lightning",
                           "Obtain any kind of Thundergold weapon or tool."),
    "thundergold_armor": ("I Am Just a Passing Lightning Rod",
                          "Obtain a full set of Thundergold armor."),
    "illusiongold_ingot": ("Eternal Illusion",
                           "The scent of flowers this metal gives off is mesmerizing."),
    "illusiongold_weapon": ("Why Not Take a Little Rest~",
                            "Obtain any kind of Illusiongold weapon or tool."),
    "illusiongold_armor": ("Just Calm Your Heart Like This~",
                           "Obtain a full set of Illusiongold armor."),
    "gift_gold_ticket": ("One Ticket to Luxury", "Obtain a Gift Gold Ticket."),
    "gift_box": ("This Item Suits You Very Well~",
                 "Get any kind of gift box from the Gold Trader."),
    "antique_tool": ("Ancient Collection",
                     "Obtain any kind of antique weapon or tool."),
    "netherite_antique_tool": ("The Royal Remains Endure Forever",
                               "Take good care of this piece of your collection."),
    "gold_infused_dirt": ("Even the Land Must Be Gilded",
                          "Craft some Gold-Infused Dirt."),
    "eggplant_seeds": ("Seeds of Glorious Years",
                       "Get Golden Eggplant Seeds inside a bastion remnant."),
    "golden_egg": ("What a Big Golden Egg~",
                   "Feed golden seeds to a chicken to get a Golden Egg."),
    "plant_gold_crop": ("Tilling My Golden Land",
                        "Till Gold-Infused Dirt and plant any kind of golden crop."),
    "midas_feast_1": ("Midas' Feast I", "Obtain all golden foods."),
    "sturdygold_feast_1": ("Gilding Evolution I",
                           "Obtain all Sturdygold foods."),
    "alchemical_meat": ("Eating Technology, Pfft - Alchemy Meat",
                        "Obtain Alchemical Cowrie Meat."),
    "midas_feast_2": ("Midas' Feast II",
                      "Obtain all Farmer's Delight golden foods."),
    "sturdygold_feast_2": ("Gilding Evolution II",
                           "Obtain all Farmer's Delight Sturdygold foods."),
}


def lang_entries(A: list[dict]) -> list[tuple[str, str, str]]:
    """返回 [(key, zh, en), ...]，顺序固定 = 表序 × title/description。

    英译**缺一条就报错**（不许静默写成空串或退回中文）——这是"102 条全都要真英译"的机器形态。
    """
    assert EN_POLICY == "translate", f"EN_POLICY 不是 translate（{EN_POLICY}）"
    missing = [a["key"] for a in A if a["key"] not in EN]
    assert not missing, f"这些成就在 EN 表里没有英译：{missing}"
    extra = sorted(set(EN) - {a["key"] for a in A})
    assert not extra, f"EN 表里有成就表之外的键：{extra}"
    out = []
    for a in A:
        en_title, en_desc = EN[a["key"]]
        assert en_title.strip(), f"{a['key']}.title 的英译是空的"
        assert en_desc.strip(), f"{a['key']}.description 的英译是空的"
        for suffix, zh, en in (("title", a["title"], en_title),
                               ("description", a["desc"], en_desc)):
            key = f"{LANG_PREFIX}.{a['key']}.{suffix}"
            out.append((key, zh, en))
    assert len(out) == len(A) * 2, f"语言键条数不是 2×{len(A)}"
    return out


def _append_lang(path: Path, entries: list[tuple[str, str]]) -> tuple[int, int]:
    """**定点追加**（共享文件协议）：只改末尾那一处，别处一个字节都不动。

    返回 (原行数, 新行数)，行数按 LF 计。
    """
    raw = path.read_bytes()
    before_lf = raw.count(b"\n")
    text = raw.decode("utf-8")
    if "\r\n" in text:
        nl = "\r\n"
    else:
        nl = "\n"
    stripped = text.rstrip()
    assert stripped.endswith("}"), f"{path.name} 不是以 }} 结尾"
    body = json.loads(text)
    assert isinstance(body, dict), f"{path.name} 顶层不是对象"

    todo = [(k, v) for k, v in entries if k not in body]
    want = dict(entries)
    changed = [(k, want[k]) for k in body if k in want and k.startswith(LANG_PREFIX)
               and body[k] != want[k]]
    already = [k for k, _ in entries if k in body and body[k] == want[k]]
    for k in [k for k, _ in entries if k in body and not k.startswith(LANG_PREFIX)]:
        assert body[k] == want[k], f"{path.name} 里 {k} 不是本轮的键却值不同，拒绝改动"

    # 缩进取文件里第一条"带冒号的行"的行首空白
    indent = "  "
    for line in text.split(nl):
        if line.startswith(" ") and ":" in line:
            indent = line[:len(line) - len(line.lstrip())]
            break

    # ---- 先做"原地改值"（只对本轮自己的键，逐行定点替换，绝不动别处）----
    for k, v in changed:
        old_repr = json.dumps(body[k], ensure_ascii=False)
        new_repr = json.dumps(v, ensure_ascii=False)
        old_line = f'{indent}"{k}": {old_repr}'
        lines = text.split(nl)
        hits = [i for i, ln in enumerate(lines) if ln.rstrip() in (old_line, old_line + ",")]
        assert len(hits) == 1, f"{path.name} 的 {k} 命中 {len(hits)} 行，拒绝改动"
        i = hits[0]
        lines[i] = lines[i].rstrip().replace(old_repr, new_repr, 1)
        text = nl.join(lines)
        body = json.loads(text)
        print(f"{path.name}: 改正 {k} 的值（原地逐行替换，1 行）")

    if not todo:
        print(f"{path.name}: 无需追加新键（{len(already)} 条已在、{len(changed)} 条已改正）")
        if changed:
            path.write_bytes(text.encode("utf-8"))
        return before_lf, path.read_bytes().count(b"\n")

    # 定位最后一个 '}'（= 文件末尾那个），把它前面的位置作为插入点
    close = text.rindex("}")
    head = text[:close]
    indent = "  "
    for line in head.split(nl):
        if line.startswith(" ") and ":" in line:
            indent = line[:len(line) - len(line.lstrip())]
            break
    # head 目前以空白/换行结尾；取出最后一行，判断要不要补逗号
    head_lines = head.split(nl)
    last = head_lines[-1]
    if last.strip() == "":
        head_lines = head_lines[:-1]
        last = head_lines[-1]
    if not last.rstrip().endswith(","):
        head_lines[-1] = last.rstrip() + ","
    new_lines = [f'{indent}{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},'
                 for k, v in todo]
    new_lines[-1] = new_lines[-1][:-1]  # 最后一条不加尾逗号
    new_text = nl.join(head_lines) + nl + nl.join(new_lines) + nl + "}"
    tail_after = text[close + 1:]
    new_text += tail_after

    after = json.loads(new_text)
    # 不许覆盖：原有每一条的键值必须逐条相同，且原有键集合必须还在
    for k, v in body.items():
        assert k in after and after[k] == v, f"{path.name} 的既有键 {k} 被改动了！"
    for k, v in todo:
        assert after[k] == v, f"{path.name} 追加的 {k} 值不对"
    assert len(after) == len(body) + len(todo), f"{path.name} 键数不对"
    path.write_bytes(new_text.encode("utf-8"))
    after_lf = path.read_bytes().count(b"\n")
    print(f"{path.name}: {len(body)} 键 / {before_lf} LF → {len(after)} 键 / {after_lf} LF"
          f"（追加 {len(todo)} 条，跳过已存在 {len(already)} 条）")
    return before_lf, after_lf


def to_json_obj(a: dict) -> dict:
    obj: dict = {}
    if a["parent"]:
        obj["parent"] = f"{NS}:{a['parent']}"
    display = {
        "icon": {"id": a["icon"], "count": 1},
        "title": {"translate": f"{LANG_PREFIX}.{a['key']}.title"},
        "description": {"translate": f"{LANG_PREFIX}.{a['key']}.description"},
    }
    if a["parent"] is None:
        display["background"] = "minecraft:textures/block/gold_block.png"
    if a["frame"] != "task":
        display["frame"] = a["frame"]
    obj["display"] = display
    obj["criteria"] = a["criteria"]
    obj["requirements"] = a["requirements"]
    obj["sends_telemetry_event"] = False
    if a["fd"]:
        obj["neoforge:conditions"] = FD_CONDITION
    # 字段顺序固定，便于 diff
    return {k: obj[k] for k in
            (["parent"] if "parent" in obj else [])
            + ["display", "criteria", "requirements", "sends_telemetry_event"]
            + (["neoforge:conditions"] if a["fd"] else [])}


def main() -> int:
    A = build()
    assert len(A) == 51, f"成就条数不是 51（实际 {len(A)}）"
    ids = [a["path"] for a in A]
    assert len(set(ids)) == 51, "有重复的成就路径"
    keys = [a["key"] for a in A]
    assert len(set(keys)) == 51, "有重复的语言键"
    for a in A:
        if a["path"] != "root":
            assert a["parent"] in ids, f"{a['path']} 的 parent {a['parent']} 不在表里"
        assert a["criteria"], f"{a['path']} 没有判据"
        names = set(a["criteria"])
        for group in a["requirements"]:
            assert group, f"{a['path']} 有空 requirement 组"
            for n in group:
                assert n in names, f"{a['path']} 的 requirement 引用了不存在的判据 {n}"
        covered = {n for g in a["requirements"] for n in g}
        assert covered == names, f"{a['path']} 有判据没被 requirements 引用"

    DATA.mkdir(parents=True, exist_ok=True)
    written = []
    for a in A:
        p = DATA / f"{a['path']}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(to_json_obj(a), ensure_ascii=False, indent=2) + "\n"
        p.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))
        written.append(p)

    manifest = {
        "count": len(A),
        "lang_prefix": LANG_PREFIX,
        "advancements": [
            {"id": f"{NS}:{a['path']}", "path": a["path"], "key": a["key"],
             "parent": f"{NS}:{a['parent']}" if a["parent"] else None,
             "icon": a["icon"], "frame": a["frame"], "fd": a["fd"],
             "title": a["title"], "description": a["desc"],
             "triggers": sorted({c["trigger"] for c in a["criteria"].values()}),
             "recipe_ids": sorted({c["conditions"]["recipe_id"]
                                   for c in a["criteria"].values()
                                   if c["trigger"] == "minecraft:recipe_crafted"})}
            for a in A
        ],
        "lists": {
            "core_materials": CORE_MATERIALS, "raw_materials": RAW_MATERIALS,
            "gear_suffix": GEAR_SUFFIX, "armor_suffix": ARMOR_SUFFIX, "metals": METALS,
            "gold_foods": GOLD_FOODS, "sturdygold_foods": STURDYGOLD_FOODS,
            "fd_gold_foods": FD_GOLD_FOODS, "fd_sturdygold_foods": FD_STURDYGOLD_FOODS,
            # bg-fix3 §二 起：刀**算**器具 ⇒ 这份清单是"必须被 `have_knife` 判据覆盖"的正向清单
            #   （旧口径原文保留：它曾经是"8 条武器成就里一个刀都不许有"的负向清单）。
            "knives": KNIVES,
            # bg-fix3 §二/§四：两条判据读的**物品标签**（`generate_metal_tags.py` 生成，
            #   条目一律 `required:false` ⇒ 没装对应可选模组时不报错）。
            "knife_tags": {m: weapon_knife_tag(m) for m in METALS},
            "handbook_tag": f"{NS}:handbook",
            # bg-fix4 §一（2026-10-08）：两条古董成就的「刀」判据读的标签（同样 `required:false`）
            "antique_knife_tags": {
                "antique_tool": ANTIQUE_KNIFE_TAG,
                "netherite_antique_tool": NETHERITE_ANTIQUE_KNIFE_TAG,
            },
        },
    }
    MANIFEST.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
                         .replace("\r\n", "\n").encode("utf-8"))

    print(f"生成成就 JSON: {len(written)} 个 → {DATA.relative_to(REPO)}")
    print(f"清单: {MANIFEST.relative_to(REPO)}")
    print(f"带乐事条件的成就: {[a['path'] for a in A if a['fd']]}")
    print(f"challenge: {[a['path'] for a in A if a['frame'] != 'task']}")
    # bg-fix3：两条"标签判据"的自证读数（刀/手册标签各覆盖几条成就、recipe_crafted 还剩几条）
    # bg-fix4 §一：+2 张古董刀标签 ⇒ 带刀判据的成就 8 → **10** 条
    _all_knife_tags = [f"#{weapon_knife_tag(m)}" for m in METALS] \
        + [f"#{ANTIQUE_KNIFE_TAG}", f"#{NETHERITE_ANTIQUE_KNIFE_TAG}"]
    _knife_crits = [a["path"] for a in A
                    if any(t in json.dumps(a["criteria"], ensure_ascii=False) for t in _all_knife_tags)]
    print(f"带『乐事小刀』判据的成就: {len(_knife_crits)} 条 → {_knife_crits}")
    _handbook_crits = [a["path"] for a in A
                       if f"#{NS}:handbook" in json.dumps(a["criteria"], ensure_ascii=False)]
    print(f"带『手册』标签判据的成就: {_handbook_crits}")
    print(f"仍是 recipe_crafted 的成就: "
          f"{[a['path'] for a in A if any(c['trigger'] == 'minecraft:recipe_crafted' for c in a['criteria'].values())]}")
    print(f"语言键: {len(A) * 2} 条/语言（{LANG_PREFIX}.<key>.title/.description）")

    if "--lang" in sys.argv:
        entries = lang_entries(A)
        assert len(entries) == 102, f"语言键条数不是 102（{len(entries)}）"
        for lang, idx in (("zh_cn", 1), ("en_us", 2)):
            _append_lang(LANG / f"{lang}.json", [(k, (zh, en)[idx - 1])
                                                 for k, zh, en in entries])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
