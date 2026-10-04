#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验：MetalFamily 会注册出来的每个物品/方块，在 zh_cn / en_us 里是否都有语言条目。"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JAVA = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold"
LANG = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang"

METALS = ["flamegold", "voodoogold", "thundergold", "indigoseagold", "illusiongold",
          # 1.6（bg-16）：两套新金属 —— 关卡扫描表必须跟着加，否则新族的语言键"零检查"也全绿
          "thornsgold", "echogold"]
ITEMS = ["ingot", "nugget", "sword", "axe", "pickaxe", "shovel", "hoe", "knife", "helmet", "chestplate",
         "leggings", "boots", "upgrade_template"]
# 1.5 武器轮（规格 12.1）：六套金属各 5 类武器（含万坚金）。
# 万坚金也在内 —— 规格 12.1 的耐久 / 附魔表专门写了万坚金 6144/30，说明作者要万坚金也有全套。
WEAPONS = ["mace", "bow", "crossbow", "trident", "shield"]
ALL_METALS = ["sturdygold", *METALS]
RAW = ["raw_{m}"]
BLOCKS = ["block", "bricks", "bricks_slab", "bricks_stairs", "bricks_wall", "pillar", "door",
          "trapdoor", "bars", "chain", "lantern"]
TEMPLATE_KEYS = ["applies_to", "ingredients", "upgrade_description",
                 "base_slot_description", "additions_slot_description"]
SPECIAL = ["blazing_rod", "voodoo_feather", "amethyst_energy_dust",
           "indigo_ocean_heart", "chorus_cherry_branch",
           # 1.6（bg-16）：两套新金属的核心材料
           "glittering_vine", "bundled_echo_shard"]
EFFECTS = ["high_burn", "voodoo", "tremble", "sediment", "soothe",
           # 1.6（bg-16）：寄生（树棘金）/ 幽咆（幽咆金，素材文件名是「音咆.png」）
           "parasite", "echo_roar"]
# 1.5 修正轮：五件「胚底」（MetalBlanks；纯合成中间物，作者澄清「没有金制系列工具」）。
# 它们仍然存在、仍然要语言键，但**不是武器**（见下面的附魔标签反向不变量）。
BLANKS = [f"golden_{w}_blank" for w in WEAPONS]

zh = json.loads((LANG / "zh_cn.json").read_text(encoding="utf-8"))
en = json.loads((LANG / "en_us.json").read_text(encoding="utf-8"))

missing_zh, missing_en, checked = [], [], 0


def need(key: str) -> None:
    global checked
    checked += 1
    if key not in zh:
        missing_zh.append(key)
    if key not in en:
        missing_en.append(key)


for m in ALL_METALS:
    ids = [f"{m}_{s}" for s in ITEMS] + [f"raw_{m}"] + [f"{m}_{w}" for w in WEAPONS]
    for i in ids:
        need(f"item.bettergold.{i}")
    for b in BLOCKS:
        need(f"block.bettergold.{m}_{b}")
    for t in TEMPLATE_KEYS:
        need(f"item.bettergold.smithing_template.{m}_upgrade.{t}")
    # 盔甲纹饰材料名（trim_material JSON 的 description 用它；缺了纹饰提示会是裸键名）
    need(f"trim_material.bettergold.{m}")

for s in SPECIAL + BLANKS:
    need(f"item.bettergold.{s}")

for e in EFFECTS:
    need(f"effect.bettergold.{e}")

print(f"检查语言键 {checked} 个（{len(ALL_METALS)} 套金属的全部物品与方块 + 5 件胚底）")
print(f"缺中文: {len(missing_zh)} {missing_zh[:8]}")
print(f"缺英文: {len(missing_en)} {missing_en[:8]}")

# 顺带检查战利品表
loot_dir = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "loot_table" / "blocks"
missing_loot = [f"{m}_{b}" for m in METALS for b in BLOCKS if not (loot_dir / f"{m}_{b}.json").is_file()]
print(f"缺战利品表: {len(missing_loot)} {missing_loot[:8]}")

# ==================== 小刀标签（决定「能不能在附魔台附魔」） ====================
# 1.21 的附魔能力不再来自 Tier：附魔台走
#   EnchantmentMenu#slotsChanged → itemstack.isEnchantable()
#   → EnchantmentHelper.getEnchantmentCost(stack.getEnchantmentValue())
#   → EnchantmentHelper.getAvailableEnchantmentResults → stack.isPrimaryItemFor(holder)
#   → IItemExtension#supportsEnchantment → enchantment.isSupportedItem(stack)
#   → stack.is(definition.supportedItems)     ← 全是**物品标签**
# FD 把 #minecraft:enchantable/{sword,sharp_weapon,weapon,fire_aspect,durability,mining,mining_loot}
# 全部定义成 "#farmersdelight:tools/knives"（见 FD jar 的 data/minecraft/tags/item/enchantable/*.json），
# 所以**小刀不在这个标签里 = 附魔台一个选项都不给**（cost 直接为 0）。
# 这是 1.5 修正①的真根因：靛海金刀 / 幻惑金刀漏登记 → 只有那两把不能附魔。
KNIVES = [f"{m}_knife" for m in METALS] + ["sturdygold_knife", "antique_knife", "netherite_antique_knife"]
KNIFE_TAGS = [
    REPO / "src/main/resources/data/farmersdelight/tags/item/tools/knives.json",
    REPO / "src/main/resources/data/c/tags/item/tools/knife.json",
]
missing_knife_tags = []
for tag_path in KNIFE_TAGS:
    values = set(json.loads(tag_path.read_text(encoding="utf-8")).get("values", []))
    for k in KNIVES:
        if f"bettergold:{k}" not in values:
            missing_knife_tags.append(f"{tag_path.name} <- bettergold:{k}")
print(f"小刀标签缺成员: {len(missing_knife_tags)} {missing_knife_tags[:8]}")

# ==================== 1.5 武器轮的附魔类别标签（规格 12.1 第 3 条） ====================
# 和修正①同源的坑：1.21 的附魔台走 `stack.is(definition.supportedItems)`，
# `supported_items` 全是物品标签 —— 武器不在 `#minecraft:enchantable/*` 里，
# 附魔台一个选项都不给。逐件要进的标签见规格 12.1 的表。
#
# 1.5 修正轮新增**反向不变量**：五件「胚底」一件都不许出现在这些标签里。
# 上一轮曾把它们当武器登记进 durability / mace / bow / crossbow / trident / weapon / sharp_weapon，
# 作者澄清「胚底纯用于合成、没有金制系列工具」后，那些成员必须全部撤掉。
ENCHANTABLE = REPO / "src/main/resources/data/minecraft/tags/item/enchantable"
WEAPON_TAGS = {
    "durability": WEAPONS,
    "mace": ["mace"],
    "bow": ["bow"],
    "crossbow": ["crossbow"],
    "trident": ["trident"],
    "weapon": ["trident"],
    "sharp_weapon": ["trident"],
}
missing_weapon_tags = []
for tag, weapons in WEAPON_TAGS.items():
    path = ENCHANTABLE / f"{tag}.json"
    if not path.is_file():
        missing_weapon_tags.append(f"缺文件 {path.name}")
        continue
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("replace", None) is True:
        # replace=true 会把原版成员整个替换掉（原版三叉戟 / 弓 / 弩 / 盾 / 重锤会失去附魔能力）
        missing_weapon_tags.append(f"{path.name} 用了 replace=true（会覆盖原版成员）")
    values = set(obj.get("values", []))
    for w in weapons:
        for m in ALL_METALS:
            item = f"bettergold:{m}_{w}"
            if item not in values:
                missing_weapon_tags.append(f"{path.name} <- {item}")
    for blank in BLANKS:
        if f"bettergold:{blank}" in values:
            missing_weapon_tags.append(f"{path.name} 混进了胚底 bettergold:{blank}（胚底不是武器）")
print(f"武器附魔标签缺成员/多余胚底: {len(missing_weapon_tags)} {missing_weapon_tags[:8]}")

# ==================== bg-15w 第 6 / 8 项 + 续工轮 §7.2 / §3.8：tooltip 键 + 条件配方 ====================
# 这几类的失败方式都是静默的，所以都要有关卡（照 §2.4 的习惯）：
#   ① §7.2 靛海金 tooltip 走 ItemTooltipEvent 后处理 + 语言键
#      tooltip.bettergold.water_movement_efficiency（键名写错 = 界面上显示裸键，不报错）；
#      上一轮那个白字行的键 tooltip.bettergold.swim_speed_per_piece **必须已删除**（作者要求）。
#   ② §3.8（续工轮改正后的口径）：**检测到装了 mut 才隐藏**胚底 ⇒ 两份条件配方并存：
#        smithing_<金属>_<武器>.json      base = 自产胚底          + not(mod_loaded(mut))
#        smithing_mut_<金属>_<武器>.json  base = mut:golden_<武器> + mod_loaded(mut)
#      条件漏了 = 没装 mut 时引用不存在物品 ⇒ 配方解析失败刷错误日志。
bg15w_problems = []

SWIM_TOOLTIP_KEY = "tooltip.bettergold.water_movement_efficiency"
DELETED_TOOLTIP_KEY = "tooltip.bettergold.swim_speed_per_piece"
if SWIM_TOOLTIP_KEY not in zh:
    bg15w_problems.append(f"zh_cn 缺 {SWIM_TOOLTIP_KEY}")
if SWIM_TOOLTIP_KEY not in en:
    bg15w_problems.append(f"en_us 缺 {SWIM_TOOLTIP_KEY}")
if DELETED_TOOLTIP_KEY in zh or DELETED_TOOLTIP_KEY in en:
    bg15w_problems.append(f"旧白字行键 {DELETED_TOOLTIP_KEY} 仍在（作者要求整块删除）")

RECIPE_DIR = REPO / "src/main/resources/data/bettergold/recipe"
MUT_WEAPONS = ["mace", "bow", "crossbow", "trident", "shield"]
SMITHING_METALS = ["sturdygold", "flamegold", "voodoogold", "thundergold", "indigoseagold", "illusiongold"]
MUT_LOADED_COND = [{"type": "neoforge:mod_loaded", "modid": "mut"}]
MUT_NOT_LOADED_COND = [{"type": "neoforge:not", "value": {"type": "neoforge:mod_loaded", "modid": "mut"}}]

for w in MUT_WEAPONS:
    # 5 条胚底工作台配方：必须存在，且条件 = not(mod_loaded(mut))
    p = RECIPE_DIR / f"golden_{w}_blank.json"
    if not p.is_file():
        bg15w_problems.append(f"缺胚底工作台配方 {p.name}（没装 mut 时这条路要能用）")
    else:
        obj = json.loads(p.read_text(encoding="utf-8"))
        if obj.get("neoforge:conditions") != MUT_NOT_LOADED_COND:
            bg15w_problems.append(f"{p.name} 的条件不是 not(mod_loaded(mut))：{obj.get('neoforge:conditions')}")

for m in SMITHING_METALS:
    for w in MUT_WEAPONS:
        # 自产胚底那条
        p = RECIPE_DIR / f"smithing_{m}_{w}.json"
        if not p.is_file():
            bg15w_problems.append(f"缺锻造升级配方 {p.name}（以胚底为 base 的那条）")
        else:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if obj.get("neoforge:conditions") != MUT_NOT_LOADED_COND:
                bg15w_problems.append(f"{p.name} 的条件不是 not(mod_loaded(mut))：{obj.get('neoforge:conditions')}")
            if obj.get("base", {}).get("item") != f"bettergold:golden_{w}_blank":
                bg15w_problems.append(f"{p.name} 的 base 不是 bettergold:golden_{w}_blank")
            if obj.get("result", {}).get("id") != f"bettergold:{m}_{w}":
                bg15w_problems.append(f"{p.name} 的产物不是 bettergold:{m}_{w}")
        # MUT 那条
        q = RECIPE_DIR / f"smithing_mut_{m}_{w}.json"
        if not q.is_file():
            bg15w_problems.append(f"缺锻造升级配方 {q.name}（以 mut:golden_{w} 为 base 的那条）")
        else:
            obj = json.loads(q.read_text(encoding="utf-8"))
            if obj.get("neoforge:conditions") != MUT_LOADED_COND:
                bg15w_problems.append(f"{q.name} 缺 neoforge:mod_loaded:mut 条件")
            if obj.get("base", {}).get("item") != f"mut:golden_{w}":
                bg15w_problems.append(f"{q.name} 的 base 不是 mut:golden_{w}")
            if obj.get("result", {}).get("id") != f"bettergold:{m}_{w}":
                bg15w_problems.append(f"{q.name} 的产物不是 bettergold:{m}_{w}")
            # 反向：MUT 那条不许再引用胚底
            if f"bettergold:golden_{w}_blank" in json.dumps(obj):
                bg15w_problems.append(f"{q.name} 里不该出现胚底 golden_{w}_blank")

# 反向：**凡是引用胚底的配方都必须带 not(mod_loaded(mut)) 条件**（否则装了 mut 时胚底还会露出来）
# ⚠ 模式必须贴着**胚底全名**（`bettergold:golden_<武器>_blank`）：
#   写成宽松的 `bettergold:golden_` 会命中一大片不相干的物品
#   （`golden_cowrie_crate` / `golden_apple_pie` / `golden_egg` …）⇒ 假红。
blank_names = [f"bettergold:golden_{w}_blank" for w in MUT_WEAPONS]
for p in RECIPE_DIR.glob("*.json"):
    text = p.read_text(encoding="utf-8")
    if not any(name in text for name in blank_names):
        continue
    obj = json.loads(text)
    if obj.get("neoforge:conditions") != MUT_NOT_LOADED_COND:
        bg15w_problems.append(f"{p.name} 引用了胚底却没有 not(mod_loaded(mut)) 条件")

print(f"bg-15w 续工轮（tooltip 键 + 双向条件配方 + 胚底条件可见）问题: {len(bg15w_problems)} {bg15w_problems[:8]}")

# ==================== bg-15w §八 追加轮②（17:44）：装备顺序 + 水中游泳速度 ====================
# 这两类的失败方式也都是静默的：
#   ① §8.1 装备分区顺序 —— 表在 `CreativeSections.GEAR_SLOT`，**一表两用**（既定顺序、又判
#      「是不是金属装备」）。作者两次报「顺序变回去了」而代码是对的 ⇒ 顺序本身就是验收项；
#      并且**斧镐锹锄不许从表里删掉**（删了它们连槽位都进不去 = 静默掉出装备分区）。
#   ② §8.3 水中游泳速度 —— 修饰符**只能一个 id**（多个 id = 双倍；同一件多挂 = 只算一件），
#      且**不许**塞进 `getDefaultAttributeModifiers()`（那会变成陆地也加速）。
bg8_problems = []

# --- ① 装备分区顺序 ---
# ⚠ 2026-10-03（bg-15w §九 9.1）：**作者更正了 §8.1** —— 斧镐锹锄在「弩之后、盾之前」。
#   所以下面这张期望表是 §9.1 的 14 件全序，`OMITTED_BUT_KEPT` 那一套"漏项排最后"的口径
#   **已被推翻**（§8.1 的旧表只作历史留档，见 CreativeSections 的注释）。
GEAR_SLOT_EXPECTED = ["sword", "mace", "trident", "bow", "crossbow",
                      "axe", "pickaxe", "shovel", "hoe",
                      "shield", "helmet", "chestplate", "leggings", "boots"]
# §9.1 里被作者"补回来"的那四件：它们必须**在表里**（一表两用，删了会静默掉出装备分区），
# 而且位次必须落在 弩(crossbow 4) 与 盾(shield 9) 之间 ⇒ 5..8。
FOUR_TOOLS = ["axe", "pickaxe", "shovel", "hoe"]

creative = (JAVA / "material" / "CreativeSections.java").read_text(encoding="utf-8")
g_start = creative.find("GEAR_SLOT = Map.ofEntries(")
g_end = creative.find(");", g_start) if g_start >= 0 else -1
if g_start < 0 or g_end < 0:
    bg8_problems.append("CreativeSections.java 里找不到 GEAR_SLOT = Map.ofEntries(...)（反空转守护）")
    gear_pairs = []
else:
    gear_pairs = re.findall(r'Map\.entry\("([a-z_]+)",\s*(\d+)\)', creative[g_start:g_end])
if len(gear_pairs) != len(GEAR_SLOT_EXPECTED):
    bg8_problems.append(f"GEAR_SLOT 条目数 {len(gear_pairs)} != {len(GEAR_SLOT_EXPECTED)}（反空转守护 / 表被动过）")
else:
    gear = {name: int(rank) for name, rank in gear_pairs}
    by_rank = [name for name, _ in sorted(gear.items(), key=lambda kv: kv[1])]
    if by_rank != GEAR_SLOT_EXPECTED:
        bg8_problems.append(f"GEAR_SLOT 顺序不是 §9.1 最终顺序：{by_rank}")
    if sorted(gear.values()) != list(range(len(GEAR_SLOT_EXPECTED))):
        bg8_problems.append(f"GEAR_SLOT 位次不是 0..{len(GEAR_SLOT_EXPECTED) - 1} 各一次：{sorted(gear.values())}")
    # §9.1 的核心：斧镐锹锄在弩之后、盾之前（位次 5..8），而且不许从表里消失
    for item in FOUR_TOOLS:
        if item not in gear:
            bg8_problems.append(
                f"GEAR_SLOT 里少了 {item} —— 一表两用，删了它会静默掉出装备分区（§8.1/§9.1 都写死的红线）")
    if "crossbow" in gear and "shield" in gear:
        lo, hi = gear["crossbow"], gear["shield"]
        for item in FOUR_TOOLS:
            if item in gear and not (lo < gear[item] < hi):
                bg8_problems.append(
                    f"{item} 的位次 {gear[item]} 不在弩({lo}) 与 盾({hi}) 之间（§9.1：弩之后的斧镐锹锄排这里）")
    if [n for n in by_rank if n in FOUR_TOOLS] and [n for n in by_rank if n in FOUR_TOOLS] != FOUR_TOOLS:
        bg8_problems.append(f"斧镐锹锄之间的相对顺序不是 {FOUR_TOOLS}：{[n for n in by_rank if n in FOUR_TOOLS]}")
print(f"装备分区顺序（§9.1 更正 §8.1）问题: {len(bg8_problems)} {bg8_problems[:8]}")

# --- ② 真正的游泳速度（bg-15w §8.3 · 作者 2026-10-02 19:42 **整节重做**）---
# ⚠ 本节断言在 2026-10-02 19:42 之后**整块换成新口径**。
#   旧口径（已被作者推翻，见需求 §8.3，断言也随之改掉，不是漏写）：
#     `MetalEvents#onSwimSpeedTick` 里**运行期**给 `Attributes.MOVEMENT_SPEED` 挂
#     `ADD_MULTIPLIED_TOTAL` 条件修饰符（仅 `isInWater()`），值 = 0.25 × 件数、
#     **全仓唯一 id** `bettergold:swim_speed_water`。
#     被推翻的原因：`MOVEMENT_SPEED` 在 `LivingEntity#travel` 的水中分支里**不是最终乘数**，
#     端到端位移超线性（实测 1.7574/2.6031/3.4941/4.4116）。
#   新口径：`MetalFamily.MetalArmorItem#getDefaultAttributeModifiers()` 里挂
#     `NeoForgeMod.SWIM_SPEED`（`neoforge:swim_speed`，`PercentageAttribute` 基值 1.0）、
#     `ADD_VALUE` +0.25（四件 2.0 = 200%）、**每个部位一个 id** `swim_speed_water_<部位>`。
#     ⚠ id 的规律**随场景反转**：物品常驻属性是"每件各挂一份" ⇒ 必须不同 id；
#     "运行期只维护一个总值" ⇒ 必须同一个 id（本文件 §13.5 与本仓两种都踩过）。
#   这几类的失败方式都是静默的，所以都要有关卡：
#     · 属性挂错（写成 MOVEMENT_SPEED）⇒ 陆地也跟着加速；
#     · 四件共用同一个 id ⇒ 按 id 去重 ⇒ 穿 4 件只算 1 件（本仓真实事故，docs/1.5-规格.md §13.5）；
#     · 旧实现没删干净 ⇒ 两套逻辑并存、效果双份。
swim_problems = []
metal_events = (JAVA / "material" / "MetalEvents.java").read_text(encoding="utf-8")
metal_family = (JAVA / "material" / "MetalFamily.java").read_text(encoding="utf-8")


def strip_comments(source: str) -> str:
    """去掉块注释与行注释 —— 判据必须在**代码**上成立。

    ⚠ 本关卡自己的教训（`mcmod_experience` §3.4）：注释里提到被禁的写法会让断言**假绿**。
    本轮又实测到同一形状的**第二次**：旧实现被删后留了一段"墓碑注释"解释它为什么被推翻，
    那段注释里**逐字写着**旧常量名 / 旧 id / `MOVEMENT_SPEED` ⇒ "旧实现必须不存在"与
    "不许出现 MOVEMENT_SPEED" 这两条负向断言，若在含注释的文本上跑就永远绿。
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    source = re.sub(r"//[^\n]*", "", source)
    return source


def method_body(source: str, signature: str) -> str:
    i = source.find(signature)
    if i < 0:
        return ""
    j = source.find("{", i)
    if j < 0:
        return ""
    depth = 0
    for k in range(j, len(source)):
        if source[k] == "{":
            depth += 1
        elif source[k] == "}":
            depth -= 1
            if depth == 0:
                return strip_comments(source[j:k + 1])
    return ""


events_code = strip_comments(metal_events)
armor_body = method_body(metal_family, "public ItemAttributeModifiers getDefaultAttributeModifiers()")

if not armor_body:
    swim_problems.append("MetalFamily 里找不到 getDefaultAttributeModifiers 方法体（反空转守护）")
else:
    # ① 新属性必须在、且必须是 SWIM_SPEED
    if "NeoForgeMod.SWIM_SPEED" not in armor_body:
        swim_problems.append("getDefaultAttributeModifiers 里没有 NeoForgeMod.SWIM_SPEED（§8.3 新口径没落地）")
    # ② 负向：常驻属性表里**不许**出现 MOVEMENT_SPEED（那会变成陆地也加速）
    if "MOVEMENT_SPEED" in armor_body:
        swim_problems.append("getDefaultAttributeModifiers 里出现了 MOVEMENT_SPEED（会变成陆地也加速）")
    # ③ ADD_MULTIPLIED_TOTAL 是旧口径；§8.3 写死用 ADD_VALUE（基值 1.0）
    if "ADD_MULTIPLIED_TOTAL" in armor_body:
        swim_problems.append("getDefaultAttributeModifiers 里出现了 ADD_MULTIPLIED_TOTAL（§8.3 写死 ADD_VALUE）")
    # ④ 既有那条（浅水）与它的四部位 id 一个字都不许动
    if "WATER_MOVEMENT_EFFICIENCY" not in armor_body:
        swim_problems.append("getDefaultAttributeModifiers 里没有 WATER_MOVEMENT_EFFICIENCY（浅水那条被删了？）")
    if '"swim_speed_" + this.getType().getName()' not in armor_body:
        swim_problems.append("四部位各自的 id swim_speed_<部位> 不见了（1.5 修正⑤ 修过的 bug 被回退）")
    # ⑤ 新 id 必须**每个部位一个**（不是全仓唯一那一个）
    if '"swim_speed_water_" + this.getType().getName()' not in armor_body:
        swim_problems.append(
            "新属性没用「每部位一个 id」swim_speed_water_<部位>（共用一个 id ⇒ 穿 4 件只算 1 件）")
    # ⑥ 适用范围：非靛海金（swimSpeedPerPiece <= 0）必须原样返回，不波及另外五套金属
    if "swimSpeedPerPiece <= 0.0F" not in armor_body:
        swim_problems.append("getDefaultAttributeModifiers 缺 swimSpeedPerPiece <= 0.0F 的短路（会波及另外五套金属）")

# 反空转守护 + 唯一真源：新 id 的拼法在 src/main/java 里**恰好一处**
id_literal = '"swim_speed_water_" + this.getType().getName()'
id_hits = sum(f.read_text(encoding="utf-8").count(id_literal)
              for f in (REPO / "src" / "main" / "java").rglob("*.java"))
if id_hits != 1:
    swim_problems.append(f"{id_literal} 在 src/main/java 里出现 {id_hits} 次（必须恰好 1 次）")

if "SWIM_SPEED_PER_PIECE = 0.25F" not in metal_family:
    swim_problems.append("MetalFamily 里 SWIM_SPEED_PER_PIECE 不是 0.25F（每件 +25% 的值被改过）")

# ★ 负向：旧口径必须**整块**消失（在**去注释后**的代码上判，墓碑注释不算）
for needle, why in [
    ("onSwimSpeedTick", "旧的运行期入口 onSwimSpeedTick 还在"),
    ("SWIM_SPEED_WATER_PER_PIECE", "旧常量 SWIM_SPEED_WATER_PER_PIECE 还在"),
    ("SWIM_SPEED_WATER_ID", "旧的唯一 id 常量 SWIM_SPEED_WATER_ID 还在"),
    ("waterSwimPieces", "旧的 waterSwimPieces 还在"),
    ("swimSpeedWaterId", "旧的 swimSpeedWaterId 还在"),
]:
    if needle in events_code:
        swim_problems.append(f"MetalEvents（去注释后）里仍能找到「{needle}」（{why}）")

# 反向：旧口径的"墓碑注释"必须在（写明被谁在什么时候推翻），否则后人会以为是漏写
if "19:42" not in metal_events or "被作者" not in metal_events:
    swim_problems.append("MetalEvents 里缺少「旧 MOVEMENT_SPEED 方案已被作者 19:42 推翻」的墓碑注释")

bg8_problems.extend(swim_problems)
print(f"游泳速度 SWIM_SPEED（§8.3 新口径）问题: {len(swim_problems)} {swim_problems[:8]}")
print(f"bg-15w §八 追加轮② 问题合计: {len(bg8_problems)} {bg8_problems[:8]}")

# ==================== bg-15y：六套金属的标签一致性 + 信标基座归属 ====================
# 现象（作者原话）：「靛海金柱、幻惑金柱没法作为信标基座」。
# 根因：`generate_metal_tags.py` 往 #minecraft:beacon_base_blocks 里一直只加
#       `{m}_block` + `{m}_bricks`，**柱子从来没进过生成器**；1.4 那 5 根柱子是**手写**进产物 JSON 的
#       （commit b5f68d3 的 diff 直接在 JSON 里加行；同一 commit 的生成器里 beacon 那行只有 block/bricks），
#       于是 1.5 新增两套金属时只补上了 块/砖，柱漏在标签外。
# 失败方式是静默的（标签少一条 = 游戏里只表现为"柱子上放信标没反应"，不报错），所以要有**两层**关卡：
#   ① 「六套金属在每个口径上应当对称的标签里成员资格一致」的不变量（下面 SYMMETRIC_TAGS，34 个标签）；
#   ② #minecraft:beacon_base_blocks 的**显式成员表**（口径 = 1.4 既有：块 / 砖 / 柱，
#      外加金系两块 gold_bricks / gold_pillar —— 它们不属于任何金属族循环，
#      原先只以"手写产物条目"的形式存在，现在也由生成器显式列出，不能被顺手删掉）。
DATA_ROOT = REPO / "src/main/resources/data"
BEACON_TAG_REL = "minecraft/tags/block/beacon_base_blocks.json"
BEACON_SUFFIXES = ["block", "bricks", "pillar"]
BEACON_ALSO = ["bettergold:gold_bricks", "bettergold:gold_pillar"]
TAGS_GEN = REPO / "tools/asset-generator/generate_metal_tags.py"


def tag_members(rel: str, seen: tuple[str, ...] = ()) -> set[str]:
    """标签的**有效成员**：把 `#bettergold:*` / `#c:*` 这类桥接引用递归展开。

    ⚠ 必须展开间接引用，否则**假红**：`#minecraft:mineable/pickaxe` 里万坚金块是靠
    `#bettergold:storage_blocks`（块标签）进来的 —— 显式条目只有 10 条，另五套是 11 条。
    口径与运行时一致：标签解析本身就是递归的。
    """
    if rel in seen:
        return set()
    p = DATA_ROOT / rel
    if not p.is_file():
        return set()
    obj = json.loads(p.read_text(encoding="utf-8"))
    out: set[str] = set()
    for v in obj.get("values", []):
        if not isinstance(v, str):
            continue
        if not v.startswith("#"):
            out.add(v)
            continue
        ns, _, name = v[1:].partition(":")
        for kind in ("item", "block"):
            sub = f"{ns}/tags/{kind}/{name}.json"
            if (DATA_ROOT / sub).is_file():
                out |= tag_members(sub, (*seen, rel))
    return out


# 标签 -> 每套金属应当有的 id 模板（{m} = 金属 id）。只列**口径上六套必须一致**的标签；
# 有意不对称的（`bettergold:sturdygold_tools`：按名字就只有万坚金，且全仓 Java 无引用）不在此表。
_METAL_BLOCKS = ["block", "bricks", "bricks_slab", "bricks_stairs", "bricks_wall",
                 "pillar", "door", "trapdoor", "bars", "chain", "lantern"]
SYMMETRIC_TAGS: dict[str, list[str]] = {
    "bettergold/tags/item/ingots.json": ["{m}_ingot"],
    "bettergold/tags/item/nuggets.json": ["{m}_nugget"],
    "bettergold/tags/item/raw_materials.json": ["raw_{m}"],
    "bettergold/tags/item/storage_blocks.json": ["{m}_block"],
    "bettergold/tags/block/storage_blocks.json": ["{m}_block"],
    "c/tags/item/ingots.json": ["{m}_ingot"],
    "c/tags/item/nuggets.json": ["{m}_nugget"],
    "c/tags/item/raw_materials.json": ["raw_{m}"],
    "c/tags/item/storage_blocks.json": ["{m}_block"],
    "c/tags/block/storage_blocks.json": ["{m}_block"],
    "minecraft/tags/item/beacon_payment_items.json": ["{m}_ingot"],
    "minecraft/tags/block/mineable/pickaxe.json": [f"{{m}}_{b}" for b in _METAL_BLOCKS],
    "minecraft/tags/block/needs_diamond_tool.json": [f"{{m}}_{b}" for b in _METAL_BLOCKS],
    "minecraft/tags/block/walls.json": ["{m}_bricks_wall"],
    BEACON_TAG_REL: [f"{{m}}_{s}" for s in BEACON_SUFFIXES],
    "minecraft/tags/item/swords.json": ["{m}_sword"],
    "minecraft/tags/item/pickaxes.json": ["{m}_pickaxe"],
    "minecraft/tags/item/axes.json": ["{m}_axe"],
    "minecraft/tags/item/shovels.json": ["{m}_shovel"],
    "minecraft/tags/item/hoes.json": ["{m}_hoe"],
    "minecraft/tags/item/head_armor.json": ["{m}_helmet"],
    "minecraft/tags/item/chest_armor.json": ["{m}_chestplate"],
    "minecraft/tags/item/leg_armor.json": ["{m}_leggings"],
    "minecraft/tags/item/foot_armor.json": ["{m}_boots"],
    "minecraft/tags/item/trim_materials.json": ["{m}_ingot"],
    "minecraft/tags/item/enchantable/durability.json": [f"{{m}}_{w}" for w in WEAPONS],
    "minecraft/tags/item/enchantable/mace.json": ["{m}_mace"],
    "minecraft/tags/item/enchantable/bow.json": ["{m}_bow"],
    "minecraft/tags/item/enchantable/crossbow.json": ["{m}_crossbow"],
    "minecraft/tags/item/enchantable/trident.json": ["{m}_trident"],
    "minecraft/tags/item/enchantable/weapon.json": ["{m}_trident"],
    "minecraft/tags/item/enchantable/sharp_weapon.json": ["{m}_trident"],
    "farmersdelight/tags/item/tools/knives.json": ["{m}_knife"],
    "c/tags/item/tools/knife.json": ["{m}_knife"],
}

symmetric_problems: list[str] = []
for _rel, _templates in SYMMETRIC_TAGS.items():
    _members = tag_members(_rel)
    if not _members:
        symmetric_problems.append(f"{_rel} 读不到任何成员（反空转守护：文件没了 / 路径写错）")
        continue
    # ① 六套金属逐个对照
    per_metal = {}
    for _m in ALL_METALS:
        _want = {f"bettergold:{t.format(m=_m)}" for t in _templates}
        _miss = sorted(_want - _members)
        per_metal[_m] = len(_miss)
        if _miss:
            symmetric_problems.append(f"{_rel} <- {_m} 缺 {_miss}")
    # ② 「成员数相同」的不变量（同一模板算出来的期望数 ⇒ 等价于六套一致）
    if len(set(per_metal.values())) != 1:
        symmetric_problems.append(f"{_rel} 六套金属缺失数不一致 {per_metal}")
print(f"六套金属标签一致性（{len(SYMMETRIC_TAGS)} 个标签 × {len(ALL_METALS)} 套金属）问题: "
      f"{len(symmetric_problems)} {symmetric_problems[:8]}")

# 信标基座标签的显式成员表（1.4 口径：块 / 砖 / 柱 + 金系两块 gold_bricks / gold_pillar）
beacon_problems: list[str] = []
_beacon_members = tag_members(BEACON_TAG_REL)
_beacon_expect = ([f"bettergold:{m}_{s}" for m in ALL_METALS for s in BEACON_SUFFIXES]
                  + BEACON_ALSO)
for _id in _beacon_expect:
    if _id not in _beacon_members:
        beacon_problems.append(f"#minecraft:beacon_base_blocks 里没有 {_id}（当不了信标金字塔基座）")
# 六套金属必须**各 3 条**（块 / 砖 / 柱）—— 任何一套少一条都要红，而不是只看"总数 20"
for _m in ALL_METALS:
    _n = sum(1 for s in BEACON_SUFFIXES if f"bettergold:{_m}_{s}" in _beacon_members)
    if _n != len(BEACON_SUFFIXES):
        beacon_problems.append(f"{_m} 在信标基座标签里有 {_n} 条，期望 {len(BEACON_SUFFIXES)} 条（块/砖/柱）")

# 生成器侧守卫：修的是**生成器**，产物 JSON 只是它的输出。
# 若有人把生成器改回去（去掉 pillar / 不再遍历 ALL_METALS / 丢掉金系两块），下次重跑就会把 bug 带回来。
_gen_src = TAGS_GEN.read_text(encoding="utf-8")
if 'BEACON_SUFFIXES = ["block", "bricks", "pillar"]' not in _gen_src:
    beacon_problems.append("generate_metal_tags.py 的 BEACON_SUFFIXES 不是 [block, bricks, pillar]（柱子又掉了？）")
if "for m in ALL_METALS:" not in _gen_src:
    beacon_problems.append("generate_metal_tags.py 的信标基座段没有遍历 ALL_METALS（万坚金会漏出六套口径）")
if 'BEACON_NON_FAMILY = ["bettergold:gold_bricks", "bettergold:gold_pillar"]' not in _gen_src:
    beacon_problems.append("generate_metal_tags.py 的 BEACON_NON_FAMILY 不对（金砖块/金柱又变成没人管的手写条目）")
print(f"信标基座标签 #minecraft:beacon_base_blocks 问题: {len(beacon_problems)} {beacon_problems[:8]}")
print(f"  （期望 {len(_beacon_expect)} 条 = 六套金属 × {len(BEACON_SUFFIXES)} + {len(BEACON_ALSO)} 条金系；"
      f"实际有效成员 {len(_beacon_members)} 条）")

# ==================== bg-15w §九 追加轮③（2026-10-03）：三项 ====================
#   ① §9.1 装备顺序 —— 已在上面（bg8_problems）改成 §9.1 的最终顺序并加了"斧镐锹锄在弩之后、盾之前"的断言；
#   ② §9.2 清 3 张重复原料配方 —— 删掉的是 1.4 遗留的 shapeless（不是生成器产物）；失败方式是静默的
#      （JEI / 配方书里多出一张图，游戏不报错），所以要**负向断言**钉住"这三个文件不许回来"，
#      并断言"每种金属的原料合成配方恰好一张、且是自定义那张（会返玻璃瓶）"；
#   ③ §9.3 靛海金器具免水下挖掘惩罚 —— 挂在 `ItemAttributeModifierEvent` 上；
#      属性挂错 / 范围写成"全部金属"都不会报错，只能靠关卡钉住"只有靛海金 + 只有器具 + 值 0.8"。
bg9_problems: list[str] = []

# --- ② 重复原料配方 ---
LEGACY_RAW_RECIPES = ["flamegold_raw.json", "voodoogold_raw.json", "thundergold_raw.json"]
RAW_CUSTOM_TYPE = "bettergold:raw_sturdygold"
RAW_EXCHANGE = {
    "sturdygold": "bettergold:golden_cowrie",
    "flamegold": "bettergold:blazing_rod",
    "voodoogold": "bettergold:voodoo_feather",
    "thundergold": "bettergold:amethyst_energy_dust",
    "indigoseagold": "bettergold:indigo_ocean_heart",
    "illusiongold": "bettergold:chorus_cherry_branch",
    # 1.6（bg-16）：树棘金的核心材料是**掉落物**（闪耀藤条），幽咆金的是**合成**（集束回响碎片）
    "thornsgold": "bettergold:glittering_vine",
    "echogold": "bettergold:bundled_echo_shard",
}
checked_raw = 0
for _m in ALL_METALS:
    _p = DATA_ROOT / "bettergold" / "recipe" / f"raw_{_m}.json"
    if not _p.is_file():
        bg9_problems.append(f"缺自定义原料配方 raw_{_m}.json（六种金属都必须有且只有它这一张）")
        continue
    _obj = json.loads(_p.read_text(encoding="utf-8"))
    checked_raw += 1
    if _obj.get("type") != RAW_CUSTOM_TYPE:
        bg9_problems.append(f"raw_{_m}.json 的 type 不是 {RAW_CUSTOM_TYPE}（实际 {_obj.get('type')}）")
    # ⚠ 万坚金那一份是"缺省回落"的活样本（模板刻意不写这两个字段），所以按序列化器默认值理解
    _res = _obj.get("result", "bettergold:raw_sturdygold")
    if _res != f"bettergold:raw_{_m}":
        bg9_problems.append(f"raw_{_m}.json 的 result 不是 bettergold:raw_{_m}（实际 {_res}）")
    _ex = _obj.get("exchange", "bettergold:golden_cowrie")
    if _ex != RAW_EXCHANGE[_m]:
        bg9_problems.append(f"raw_{_m}.json 的 exchange 不是 {RAW_EXCHANGE[_m]}（实际 {_ex}）")
if checked_raw != len(ALL_METALS):
    bg9_problems.append(f"只检查到 {checked_raw} 张自定义原料配方，期望 {len(ALL_METALS)}（反空转守护）")

# ★ 负向：1.4 那三张 shapeless 必须整块消失（文件层面；配方 id 由运行时探针复算）
for _legacy in LEGACY_RAW_RECIPES:
    if (DATA_ROOT / "bettergold" / "recipe" / _legacy).is_file():
        bg9_problems.append(
            f"{_legacy} 还在 —— 它与 raw_{_legacy.replace('_raw.json', '')}.json 输入输出逐项相同，"
            f"会让 JEI/配方书显示两张图（§9.2 要清的就是它）")
# 同类旁证：万坚金 / 靛海金 / 幻惑金**从来就**没有这一张 ⇒ 那三张是漏删的遗留
for _m in ["sturdygold", "indigoseagold", "illusiongold"]:
    if (DATA_ROOT / "bettergold" / "recipe" / f"{_m}_raw.json").is_file():
        bg9_problems.append(f"{_m}_raw.json 竟然存在（旁证不成立：另外三种金属只有自定义那一张）")

# 生成器侧守卫：`raw_<金属>.json` 的唯一真源是 generate_metal_recipes.py；
# 它**不许**把 legacy 那种 `*_raw.json` 当成模板产出（否则下次重跑又把重复配方带回来）。
GEN_RECIPES = REPO / "tools/asset-generator/generate_metal_recipes.py"
_gen_recipes_src = GEN_RECIPES.read_text(encoding="utf-8")
if 'RAW_CRAFT_TEMPLATE = "raw_sturdygold.json"' not in _gen_recipes_src:
    bg9_problems.append("generate_metal_recipes.py 的 RAW_CRAFT_TEMPLATE 不是 raw_sturdygold.json")
for _legacy in LEGACY_RAW_RECIPES:
    if _legacy in _gen_recipes_src:
        bg9_problems.append(
            f"generate_metal_recipes.py 里出现了 {_legacy} —— 生成器不许再产出 legacy 那种重复配方")
# 反空转守护：生成器必须**确实**会写 raw_<金属>.json（否则"没产出 legacy"只是因为什么都没产出）
if 'f"raw_{metal}.json"' not in _gen_recipes_src and "raw_{metal}" not in _gen_recipes_src:
    bg9_problems.append("generate_metal_recipes.py 里看不到 raw_<metal>.json 的产出路径（反空转守护）")
# 保留的那张必须真的会返玻璃瓶（否则"保留自定义那张"的理由就不成立了）
_raw_recipe_src = strip_comments(
    (JAVA / "recipe" / "RawSturdygoldRecipe.java").read_text(encoding="utf-8"))
if "GLASS_BOTTLE" not in _raw_recipe_src or "ALCHEMIC_FUEL" not in _raw_recipe_src:
    bg9_problems.append("RawSturdygoldRecipe 不再对 alchemic_fuel 返还 glass_bottle（§9.2 保留它的理由）")
print(f"§9.2 重复原料配方（六套各一张 + 三张 legacy 必须消失）问题: {len(bg9_problems)} {bg9_problems[:8]}")

# --- ③ 靛海金器具：免水下挖掘惩罚 ---
_before9_3 = len(bg9_problems)
_submerged_body = method_body(metal_events, "public static void onItemAttributeModifiers(")
if not _submerged_body:
    bg9_problems.append("MetalEvents 里找不到 onItemAttributeModifiers 方法体（反空转守护）")
else:
    # 参数类型在**签名**里（不在方法体里）⇒ 在"去注释后的整份源码"上判
    if "onItemAttributeModifiers" not in events_code or "ItemAttributeModifierEvent" not in events_code:
        bg9_problems.append("onItemAttributeModifiers 的参数不是 ItemAttributeModifierEvent")
    if "SUBMERGED_MINING_SPEED" not in _submerged_body:
        bg9_problems.append("onItemAttributeModifiers 里没有 Attributes.SUBMERGED_MINING_SPEED")
    if "ADD_VALUE" not in _submerged_body:
        bg9_problems.append("onItemAttributeModifiers 里没有 ADD_VALUE（§9.3 写死用 ADD_VALUE）")
    if "EquipmentSlotGroup.MAINHAND" not in _submerged_body:
        bg9_problems.append("onItemAttributeModifiers 的槽位组不是 EquipmentSlotGroup.MAINHAND")
    if "submergedMiningImmunity" not in _submerged_body:
        bg9_problems.append("onItemAttributeModifiers 没有用 family.submergedMiningImmunity 早退（会波及五套金属）")
    if "isTool(" not in _submerged_body:
        bg9_problems.append("onItemAttributeModifiers 没有用 family.isTool(...)（会把盔甲也算进去）")
    if "family == null" not in _submerged_body:
        bg9_problems.append("onItemAttributeModifiers 缺 family == null 的廉价早退（事件在热路径上）")
    if "SUBMERGED_MINING_IMMUNITY_ID" not in _submerged_body:
        bg9_problems.append("onItemAttributeModifiers 没用那个固定 id 常量（§9.3：单栈单条、一个固定 id）")
    # 加法值必须是 0.8（0.2 + 0.8 = 1.0）
    if "SUBMERGED_MINING_IMMUNITY_BONUS" not in _submerged_body:
        bg9_problems.append("onItemAttributeModifiers 没用 SUBMERGED_MINING_IMMUNITY_BONUS 常量")
if "SUBMERGED_MINING_IMMUNITY_BONUS = 0.8F" not in metal_events:
    bg9_problems.append("MetalEvents 里 SUBMERGED_MINING_IMMUNITY_BONUS 不是 0.8F（0.2+0.8=1.0）")

# 固定 id 的字面量在 src/main/java 里**恰好一次**（反空转 + 唯一真源）。
# ⚠ 判据跑在**去注释后**的源码上（注释里提到它会喂饱正向断言，见 mcmod_experience §3.4），
#   并且**跳过 `probe/`**（临时探针会自己拼一份同一个 id，收尾整块删除 —— 见关卡末尾的 grep 口径）。
_id_hits = 0
for _f in (REPO / "src" / "main" / "java").rglob("*.java"):
    if "probe" in _f.parts:
        continue
    _id_hits += strip_comments(_f.read_text(encoding="utf-8")).count('"submerged_mining_immunity"')
if _id_hits != 1:
    bg9_problems.append(f'"submerged_mining_immunity" 在 src/main/java（不含 probe/）里出现 {_id_hits} 次（必须恰好 1 次）')

# 家族开关：字段 + Spec 默认 false + setter 都在
if "public final boolean submergedMiningImmunity;" not in metal_family:
    bg9_problems.append("MetalFamily 里没有 public final boolean submergedMiningImmunity 字段")
if "public boolean submergedMiningImmunity = false;" not in metal_family:
    bg9_problems.append("MetalFamily.Spec 的 submergedMiningImmunity 默认值不是 false")
if "public Spec submergedMiningImmunity()" not in metal_family:
    bg9_problems.append("MetalFamily.Spec 里没有 submergedMiningImmunity() 归位方法")

# 适用范围：**只有靛海金**归位时打开（全仓恰好一次，且必须落在 INDIGOSEAGOLD 的 spec 块里）
_all_metals_src = (JAVA / "material" / "AllMetals.java").read_text(encoding="utf-8")
_open_hits = _all_metals_src.count(".submergedMiningImmunity()")
if _open_hits != 1:
    bg9_problems.append(f"AllMetals 里 .submergedMiningImmunity() 出现 {_open_hits} 次（必须恰好 1 次 = 只有靛海金）")
else:
    _blk_start = _all_metals_src.find('new MetalFamily.Spec("indigoseagold"')
    _blk_end = _all_metals_src.find("));", _blk_start) if _blk_start >= 0 else -1
    _blk = _all_metals_src[_blk_start:_blk_end] if _blk_start >= 0 and _blk_end > _blk_start else ""
    if not _blk:
        bg9_problems.append("AllMetals 里找不到 INDIGOSEAGOLD 的 Spec 块（反空转守护）")
    elif ".submergedMiningImmunity()" not in _blk:
        bg9_problems.append("submergedMiningImmunity() 不在 INDIGOSEAGOLD 的 Spec 块里（范围不对）")

# ★ 负向：旧写法不许出现 —— 不许给物品塞 Item.Properties#attributes 去改挖掘速度，
#   也不许把这条挂到盔甲那条 getDefaultAttributeModifiers 里（那会变成"穿甲也免疫"，不是需求）
if "SUBMERGED_MINING_SPEED" in armor_body:
    bg9_problems.append("MetalArmorItem#getDefaultAttributeModifiers 里出现了 SUBMERGED_MINING_SPEED"
                        "（§9.3 只针对【器具】，不含盔甲）")
print(f"§9.3 靛海金器具免水下挖掘惩罚问题: {len(bg9_problems) - _before9_3} "
      f"{bg9_problems[_before9_3:][:8]}")
print(f"bg-15w §九 追加轮③ 问题合计: {len(bg9_problems)} {bg9_problems[:8]}")


# ==================== bg-16（2026-10-04）：两处修正的静态断言 ====================
# §5.2 创造页横幅的 Z 深度 bug —— 真因不是"z 不够"而是"画得太晚"：
#   `AbstractContainerScreen#render` 第 141 行 `RenderSystem.disableDepthTest()` 把深度测试整个关掉
#   ⇒ z 参数不参与遮挡，只有绘制顺序说话；而 `ScreenEvent.Render.Post` 是
#   `ClientHooks#drawScreenInternal` 在 `renderWithTooltip(...)`（tooltip 最后画）**之后**才发的
#   ⇒ 旧落点必然压住 tooltip。正解 = `ContainerScreenEvent.Render.Foreground`
#   （`renderLabels` 之后、tooltip 之前），并且坐标必须改成**容器相对**（该事件在 translate(leftPos,topPos) 之内）。
# §5.1 安抚对玩家生效 —— 判据是 `PlayerTickEvent.Post` 里 `hasEffect(SOOTHE)` 的**双向**维护：
#   在身 ⇒ 给 MOVEMENT_SPEED / JUMP_STRENGTH 挂 ×0 的 **transient** 修饰符，不在身 ⇒ removeModifier；
#   左右键的每一个 cancellable 入口各一条取消。**零持久状态**是可逆性的结构保证。
bg16_problems: list[str] = []

_banners_path = JAVA / "client" / "CreativeSectionBanners.java"
if not _banners_path.is_file():
    bg16_problems.append("找不到 client/CreativeSectionBanners.java（反空转守护）")
    _banners = ""
else:
    _banners = strip_comments(_banners_path.read_text(encoding="utf-8"))

# 正向：新的落点与容器相对坐标
if "ContainerScreenEvent.Render.Foreground" not in _banners:
    bg16_problems.append("§5.2 横幅没有改用 ContainerScreenEvent.Render.Foreground（仍会压住 tooltip）")
if "onContainerScreenForeground" not in _banners:
    bg16_problems.append("§5.2 横幅的入口方法名不是 onContainerScreenForeground（反空转守护）")
if "getContainerScreen()" not in _banners:
    bg16_problems.append("§5.2 横幅没有从 ContainerScreenEvent 取容器界面（getContainerScreen）")
if "int left = ITEM_AREA_X;" not in _banners or "int top = ITEM_AREA_Y;" not in _banners:
    bg16_problems.append("§5.2 横幅没有用容器相对坐标 [bg16-banner-relative-coords]"
                         "（Foreground 事件在 translate(leftPos, topPos) 之内）")

# 负向：旧的落点与旧的坐标基准一个都不许留（判据跑在去注释后的源码上）
if "ScreenEvent.Render.Post" in _banners:
    bg16_problems.append("§5.2 横幅仍挂着旧的 ScreenEvent.Render.Post [bg16-banner-old-event]"
                         "（= tooltip 之后，会压住物品名字）")
if any(tok in _banners for tok in ("guiLeft", "guiTop", "getGuiLeft", "getGuiTop")):
    bg16_problems.append("§5.2 横幅里仍出现 guiLeft/guiTop/getGuiLeft/getGuiTop"
                         " [bg16-banner-no-absolute-coords]"
                         "（Foreground 事件在 translate(leftPos, topPos) 之内 ⇒ 只能用容器相对坐标）")

# §5.1 安抚的玩家分支
_metal_events_path = JAVA / "material" / "MetalEvents.java"
_metal_events_full = _metal_events_path.read_text(encoding="utf-8") if _metal_events_path.is_file() else ""
_metal_events_bg16 = strip_comments(_metal_events_full)


def _slice_method(src: str, name: str) -> str:
    """按方法名截出「签名 → 下一个顶格右花括号」的块（缺失返回空串，供反空转判定）。"""
    i = src.find(name)
    if i < 0:
        return ""
    j = src.find("\n    }", i)
    return src[i:j + 6] if j > i else src[i:]


_freeze_body = _slice_method(_metal_events_bg16, "onSoothePlayerFreeze")
if not _freeze_body:
    bg16_problems.append("§5.1 找不到 onSoothePlayerFreeze（反空转守护）")
else:
    for _needle, _why in (
            ("hasEffect(AllEffects.SOOTHE)", "没有以「身上有没有安抚」为唯一判据"),
            ("MOVEMENT_SPEED", "没有把移动速度乘 0（禁止移动）"),
            ("JUMP_STRENGTH", "没有把跳跃力度乘 0（禁止跳跃）"),
            ("isClientSide", "没有只让服务端算属性（客户端读同步值）"),
            ("sootheFreeze(", "没有走统一的挂/摘修饰符助手"),
            ("SOOTHE_FREEZE_SPEED_ID", "禁止移动没有用固定 id 常量"),
            ("SOOTHE_FREEZE_JUMP_ID", "禁止跳跃没有用固定 id 常量")):
        if _needle not in _freeze_body:
            bg16_problems.append(f"§5.1 onSoothePlayerFreeze {_why}（缺 {_needle}）")
    # ★ 可逆性：玩家分支**不许**碰实体持久数据（那是"永久变傻/永久不能动"的唯一来源）
    if "getPersistentData" in _freeze_body:
        bg16_problems.append("§5.1 玩家分支写了实体持久数据 [bg16-soothe-player-no-persistent-data]"
                             "（可逆性靠「零持久状态」，不许写 NBT）")

# 挂/摘修饰符的助手：必须是「×0 的 ADD_MULTIPLIED_TOTAL + transient + 双向可摘」
_helper_body = _slice_method(_metal_events_bg16, "private static void sootheFreeze(")
if not _helper_body:
    bg16_problems.append("§5.1 找不到 sootheFreeze(...) 助手（反空转守护）")
else:
    for _needle, _why in (
            ("ADD_MULTIPLIED_TOTAL", "禁止移动/跳跃必须用 ADD_MULTIPLIED_TOTAL（ADD_VALUE 对基值 0.1/0.42 是错的）"),
            ("addOrUpdateTransientModifier", "必须用 transient 修饰符（不落盘才能保证可逆）"),
            ("removeModifier(", "不挂安抚时必须把修饰符摘掉（双向维护）"),
            ("Operation.", "没有显式指定运算方式")):
        if _needle not in _helper_body:
            bg16_problems.append(f"§5.1 sootheFreeze {_why}（缺 {_needle}）")
    if "getPersistentData" in _helper_body:
        bg16_problems.append("§5.1 sootheFreeze 写了实体持久数据 [bg16-soothe-helper-no-persistent-data]"
                             "（可逆性靠「零持久状态」，不许写 NBT）")

# 两个 id 的字面量在 src/main/java（不含 probe/）里各**恰好一次**（反空转 + 唯一真源）
for _lit in ("soothe_freeze_speed", "soothe_freeze_jump"):
    _hits = 0
    for _f in (REPO / "src" / "main" / "java").rglob("*.java"):
        if "probe" in _f.parts:
            continue
        _hits += strip_comments(_f.read_text(encoding="utf-8")).count(f'"{_lit}"')
    if _hits != 1:
        bg16_problems.append(f'§5.1 字面量 "{_lit}" 在 src/main/java（不含 probe/）里出现 {_hits} 次（必须恰好 1 次）')

# 左右键的每一个 cancellable 入口各一条（漏一条就是静默失效：那个键照样有用）
for _handler, _key in (
        ("onSootheAttack", "左键攻击实体"),
        ("onSootheBreak", "破坏方块"),
        ("onSootheLeftClickBlock", "左键点方块"),
        ("onSootheRightClickBlock", "右键方块"),
        ("onSootheRightClickItem", "右键用物品"),
        ("onSootheEntityInteractSpecific", "右键实体精确部位"),
        ("onSootheEntityInteract", "右键实体")):
    _body = _slice_method(_metal_events_bg16, _handler)
    if not _body or "setCanceled(true)" not in _body:
        bg16_problems.append(f"§5.1 缺「{_key}」的取消处理器（{_handler} 不存在或没有 setCanceled）")
    elif "isSoothed(" not in _body:
        bg16_problems.append(f"§5.1 「{_key}」的处理器没有用统一判据 isSoothed(...)")

if "private static boolean isSoothed(" not in _metal_events_bg16:
    bg16_problems.append("§5.1 没有统一的 isSoothed(...) 判据方法")

# 反向不变量：既有的安抚机制**一个字都没动**（玩家分支是"新增"，不是改写生物那一套）。
# 那个「非 Mob 直接 return」的守卫在 SootheState 里**恰好三处**（begin / restore / recoverIfStale）——
# 改掉任何一处都是"生物会被永久变傻"的一半，所以判据取「恰好 3 次」而不是「至少 1 次」。
_soothe_state_path = JAVA / "material" / "SootheState.java"
_soothe_state = strip_comments(_soothe_state_path.read_text(encoding="utf-8")) if _soothe_state_path.is_file() else ""
_non_mob_guard = _soothe_state.count("!(entity instanceof Mob mob)")
if _non_mob_guard != 3:
    bg16_problems.append(f"§5.1 SootheState 的「非 Mob 直接 return」守卫出现 {_non_mob_guard} 次"
                         " [bg16-soothe-state-untouched]（begin / restore / recoverIfStale 必须各一处）")
if "public static void restore(LivingEntity entity)" not in _soothe_state:
    bg16_problems.append("§5.1 SootheState.restore 的签名被改动了 [bg16-soothe-state-untouched]"
                         "（既有生物机制必须原样不变）")

# ==================== bg-16（2026-10-04）批 1 / 批 2：两套新金属 + 三个散件 ====================
# 每条断言都带**稳定的 ASCII id**（`[bg16-...]`），供扰动矩阵逐条自证（见 mcmod_experience §3.4）。
_RES = REPO / "src" / "main" / "resources"
_DATA = _RES / "data"


def _bg16_bad(tag: str, msg: str) -> None:
    bg16_problems.append(f"{msg} [{tag}]")


# ---------- 1) 两族 Spec：**不覆盖任何数值字段**（§0.1 的省事结论；覆盖反而容易写错） ----------
_all_metals_src2 = (JAVA / "material" / "AllMetals.java").read_text(encoding="utf-8")
for _metal, _traits in (
        ("thornsgold", (".contactCactusThorns()", ".parasiteOnAttack()", ".cactusResist()",
                        ".parasiteReflect()", ".cactusImmune()")),
        ("echogold", (".contactSonicBoom()", ".echoRoarOnAttack()", ".sonicResist()",
                      ".echoRoarReflect()"))):
    _start = _all_metals_src2.find(f'new MetalFamily.Spec("{_metal}"')
    _end = _all_metals_src2.find("));", _start) if _start >= 0 else -1
    _blk = _all_metals_src2[_start:_end] if _start >= 0 and _end > _start else ""
    if not _blk:
        _bg16_bad("bg16-spec-block", f"AllMetals 里找不到 {_metal} 的 Spec 块（反空转守护）")
        continue
    for _field in ("durability", "miningSpeed", "attackDamageBonus", "enchantmentValue",
                   "armorDefense", "armorDurability", "armorToughness", "armorKnockbackResistance"):
        if _field in strip_comments(_blk):
            _bg16_bad("bg16-spec-no-numeric-override",
                      f"{_metal} 的 Spec 覆盖了数值字段 {_field}（1.6 要求吃默认值，一个都不许覆盖）")
    for _trait in _traits:
        if _trait not in strip_comments(_blk):
            _bg16_bad("bg16-spec-traits", f"{_metal} 的 Spec 缺 trait {_trait}")
    for _must in (".specialWeaponMetal(true, 2048)", ".coreItem("):
        if _must not in strip_comments(_blk):
            _bg16_bad("bg16-spec-shape", f"{_metal} 的 Spec 缺 {_must}")

# ---------- 2) 创造页顺序：METAL_ORDER 八行 + 两族位置 ----------
_creative = strip_comments((JAVA / "material" / "CreativeSections.java").read_text(encoding="utf-8"))
_expected_order = ["flamegold", "sturdygold", "thornsgold", "echogold",
                   "indigoseagold", "voodoogold", "thundergold", "illusiongold"]
_order_block_start = _creative.find("METAL_ORDER = List.of(")
_order_block_end = _creative.find(");", _order_block_start)
_order_block = _creative[_order_block_start:_order_block_end] if _order_block_start >= 0 else ""
_found_order = [m for m in _expected_order if f'"{m}"' in _order_block]
if _found_order != _expected_order:
    _bg16_bad("bg16-metal-order", f"METAL_ORDER 不是 1.6 的顺序（实际命中 {_found_order}）")
_idx_thorns = _order_block.find('"thornsgold"')
_idx_echo = _order_block.find('"echogold"')
_idx_sturdy = _order_block.find('"sturdygold"')
_idx_indigo = _order_block.find('"indigoseagold"')
if not (_idx_sturdy < _idx_thorns < _idx_echo < _idx_indigo):
    _bg16_bad("bg16-metal-order-position",
              "METAL_ORDER 里两族的位置不对（必须在万坚金之后、靛海金之前，且树棘金在前）")

# ---------- 3) 闪耀藤条：GLM 存在 + **已登记进 global_loot_modifiers**（漏了就是静默不生效） ----------
_glm_json = _DATA / "bettergold" / "loot_modifiers" / "leaves_glittering_vine.json"
if not _glm_json.is_file():
    _bg16_bad("bg16-glm-file", "缺 loot_modifiers/leaves_glittering_vine.json")
else:
    _glm = json.loads(_glm_json.read_text(encoding="utf-8"))
    if _glm.get("type") != "bettergold:add_glittering_vine":
        _bg16_bad("bg16-glm-type", f"GLM 的 type 不是 bettergold:add_glittering_vine（实际 {_glm.get('type')}）")
_global_glm = _DATA / "neoforge" / "loot_modifiers" / "global_loot_modifiers.json"
_global_ids = json.loads(_global_glm.read_text(encoding="utf-8")).get("entries", []) if _global_glm.is_file() else []
if "bettergold:leaves_glittering_vine" not in _global_ids:
    _bg16_bad("bg16-glm-registered",
              "leaves_glittering_vine 没进 data/neoforge/loot_modifiers/global_loot_modifiers.json（静默不生效）")
_glm_src = strip_comments((JAVA / "registry" / "AllLootModifiers.java").read_text(encoding="utf-8"))
for _needle, _tag, _why in (
        ('GLM.register("add_glittering_vine"', "bg16-glm-codec", "生成器/代码里没注册 add_glittering_vine 这个 codec"),
        ("BASE_CHANCE = 0.06F", "bg16-glm-chance", "闪耀藤条基础概率不是 6%"),
        ("CHANCE_PER_FORTUNE = 0.06F", "bg16-glm-fortune", "时运每级加成不是 +6%"),
        ("BlockTags.LEAVES", "bg16-glm-leaves", "掉落判据里没有 #minecraft:leaves"),
        ("Blocks.VINE", "bg16-glm-vine", "掉落判据里没有 minecraft:vine"),
        ("MetalFamily.of(tool)", "bg16-glm-tool", "工具判据没有走 MetalFamily.of(tool)"),
        ("family.isTool(", "bg16-glm-istool", "工具范围漏了 isTool(...)"),
        ("family.isWeapon(", "bg16-glm-isweapon", "工具范围漏了 isWeapon(...)"),
        ("Enchantments.FORTUNE", "bg16-glm-fortune-lookup", "没有读时运附魔等级")):
    if _needle not in _glm_src:
        _bg16_bad(_tag, _why)

# ---------- 4) 堆肥：NeoForge 数据地图（1.21.1 没有 Item.Properties#compostable） ----------
# ⚠ 数据地图的 id = **文件路径的命名空间** + 路径：data/<ns>/data_maps/<registry>/<path>.json ⇒ <ns>:<path>。
#    读它的是 `ComposterBlock#getValue`，读的正是 **neoforge:compostables**
#    （NeoForgeDataMaps.COMPOSTABLES = DataMapType.builder(id("compostables"), …)，jar 内真实路径
#    = data/neoforge/data_maps/item/compostables.json）。
#    bg-16 收口轮修的真 bug（A 级实机抓出）：原先放在 data/bettergold/data_maps/item/compostables.json
#    ⇒ 注册出来的是**从未注册过**的 bettergold:compostables ⇒ 整条被**静默丢弃**
#    （不报错 / 不崩 / runData 与静态关卡全绿；实测 getValue(闪耀藤条) = -1.0、getData = null，而原版小麦 0.65）。
#    三条断言：新位置必须在、旧位置必须不存在、值仍是 0.65。
_compost = _DATA / "neoforge" / "data_maps" / "item" / "compostables.json"
_compost_old = _DATA / "bettergold" / "data_maps" / "item" / "compostables.json"
if _compost_old.is_file():
    _bg16_bad("bg16-compost-old-path",
              "data/bettergold/data_maps/item/compostables.json 又出现了"
              "（数据地图命名空间写错 ⇒ 静默丢弃；必须只在 data/neoforge/data_maps/item/ 下）")
if not _compost.is_file():
    _bg16_bad("bg16-compost-file",
              "缺 data/neoforge/data_maps/item/compostables.json（闪耀藤条可堆肥靠它；"
              "放 data/bettergold/... 会注册成 bettergold:compostables ⇒ 静默丢弃）")
else:
    _cv = json.loads(_compost.read_text(encoding="utf-8")).get("values", {})
    _entry = _cv.get("bettergold:glittering_vine")
    _chance = _entry.get("chance") if isinstance(_entry, dict) else _entry
    if _chance != 0.65:
        _bg16_bad("bg16-compost-chance", f"闪耀藤条的堆肥概率不是 0.65（实际 {_chance}）")

# 同类扫描（不变量）：resources 里**每一张**数据地图的 `data/<ns>/data_maps/<registry>/<file>` 都必须
# 与注册它的那个 DataMapType 的命名空间一致；不在白名单里 ⇒ 红（写错 = 静默丢弃，见上）。
_ALLOWED_DATA_MAPS = {("neoforge", "item/compostables")}
_found_data_maps = []
for _p in _RES.rglob("data_maps/*/*.json"):
    _parts = _p.relative_to(_RES).parts          # data/<ns>/data_maps/<registry>/<file>.json
    if len(_parts) >= 5:
        _found_data_maps.append((_parts[1], f"{_parts[3]}/{Path(_parts[4]).stem}"))
_unknown_data_maps = [m for m in _found_data_maps if m not in _ALLOWED_DATA_MAPS]
if not _found_data_maps:
    _bg16_bad("bg16-datamap-anti-vacuum", "反空转守护：resources 里一张数据地图文件都没扫到")
if _unknown_data_maps:
    _bg16_bad("bg16-datamap-namespace",
              f"数据地图文件的命名空间/路径不在白名单里 {_unknown_data_maps}"
              "（命名空间写错 = 静默丢弃；新加一张表要先与它的 DataMapType 对齐再写进白名单）")

# ---------- 5) 集束回响碎片：3×3 有序（中心幽匿脉络 + 外圈 8 回响碎片） ----------
_recipe = _DATA / "bettergold" / "recipe" / "bundled_echo_shard.json"
if not _recipe.is_file():
    _bg16_bad("bg16-recipe-file", "缺 recipe/bundled_echo_shard.json")
else:
    _r = json.loads(_recipe.read_text(encoding="utf-8"))
    if _r.get("type") != "minecraft:crafting_shaped":
        _bg16_bad("bg16-recipe-type", f"集束回响碎片不是有序合成（{_r.get('type')}）")
    if _r.get("pattern") != ["EEE", "EVE", "EEE"]:
        _bg16_bad("bg16-recipe-pattern", f"集束回响碎片的形状不是「中心幽匿脉络 + 外圈 8 回响碎片」（{_r.get('pattern')}）")
    _keys = _r.get("key", {})
    if _keys.get("E", {}).get("item") != "minecraft:echo_shard" or _keys.get("V", {}).get("item") != "minecraft:sculk_vein":
        _bg16_bad("bg16-recipe-key", "集束回响碎片的材料不是 8 回响碎片 + 1 幽匿脉络")
    if (_r.get("result") or {}).get("id") != "bettergold:bundled_echo_shard":
        _bg16_bad("bg16-recipe-result", "集束回响碎片的产物不是 bettergold:bundled_echo_shard")

# ---------- 6) 免疫仙人掌：两处落点 + **不许新增 mixin** ----------
_events_src = strip_comments((JAVA / "material" / "MetalEvents.java").read_text(encoding="utf-8"))
for _needle, _tag, _why in (
        ("onCactusItemImmunity", "bg16-cactus-item", "缺「掉落物形态免疫仙人掌」的处理器"),
        ("EntityInvulnerabilityCheckEvent", "bg16-cactus-item-event", "物品形式没有用 EntityInvulnerabilityCheckEvent"),
        ("onArmorHurtCactusImmunity", "bg16-cactus-armor", "缺「装备不因仙人掌伤害掉耐久」的处理器"),
        ("ArmorHurtEvent", "bg16-cactus-armor-event", "装备耐久没有用 ArmorHurtEvent"),
        ("ItemEntity", "bg16-cactus-itementity", "物品形式没有判 ItemEntity"),
        ("DamageTypes.SONIC_BOOM", "bg16-sonic-damage", "缺监守者声波伤害类型"),
        ("DamageTypes.CACTUS", "bg16-cactus-damage", "缺仙人掌伤害类型"),
        ("PARASITE_SOURCE_KEY", "bg16-parasite-source", "寄生没有记「施加者是谁」（回血用）"),
        ("PARASITE_HEAL_CHANCE", "bg16-parasite-heal", "寄生没有用 36% 回血概率常量")):
    if _needle not in _events_src:
        _bg16_bad(_tag, _why)
_mixins = _RES / "bettergold.mixins.json"
_mixins_txt = _mixins.read_text(encoding="utf-8") if _mixins.is_file() else ""
if "cactus" in _mixins_txt.lower() or "Cactus" in _mixins_txt:
    _bg16_bad("bg16-no-mixin", "bettergold.mixins.json 里出现了仙人掌相关 mixin（本轮两处落点都不需要 mixin）")

# 家族开关：Spec 默认 false + 两个 setter 在位 + 两族各归位一次
_mf_src = (JAVA / "material" / "MetalFamily.java").read_text(encoding="utf-8")
for _field in ("contactCactusThorns", "contactSonicBoom", "parasiteOnAttack", "echoRoarOnAttack",
               "cactusResist", "sonicResist", "parasiteReflect", "echoRoarReflect", "cactusImmune"):
    if f"public boolean {_field} = false;" not in _mf_src:
        _bg16_bad("bg16-spec-default", f"MetalFamily.Spec 的 {_field} 默认值不是 false")
    if f"public Spec {_field}()" not in _mf_src:
        _bg16_bad("bg16-spec-setter", f"MetalFamily.Spec 缺 {_field}() 归位方法")
    if f"this.{_field} = spec.{_field};" not in _mf_src:
        _bg16_bad("bg16-family-copy", f"MetalFamily 没有把 Spec.{_field} 复制到本体（事件里读的是 family.{_field}）")

# ---------- 7) 两个 buff：形状 + 数值常量 ----------
_effects_src = strip_comments((JAVA / "registry" / "AllEffects.java").read_text(encoding="utf-8"))
for _needle, _tag, _why in (
        ('EFFECTS.register("parasite"', "bg16-parasite-effect", "AllEffects 没注册 parasite"),
        ('EFFECTS.register("echo_roar"', "bg16-echo-effect", "AllEffects 没注册 echo_roar"),
        ("parasiteTick(", "bg16-parasite-tick", "寄生没有走 MetalEvents.parasiteTick"),
        ("echoRoarTick(", "bg16-echo-tick", "幽咆没有走 MetalEvents.echoRoarTick"),
        ("duration % 20 == 0", "bg16-effect-second", "两个 buff 不是每秒结算（duration % 20）")):
    if _needle not in _effects_src:
        _bg16_bad(_tag, _why)
for _needle, _value in (("PARASITE_TICKS = 16 * 20", "16 秒"), ("ECHO_ROAR_TICKS = 6 * 20", "6 秒"),
                        ("PARASITE_DAMAGE_PER_LEVEL = 1.0F", "每级 1 点"),
                        ("ECHO_ROAR_DAMAGE_PER_LEVEL = 1.0F", "每级 1 点"),
                        ("PARASITE_HEAL_CHANCE = 0.36F", "36% 回血"),
                        ("ECHO_ROAR_RADIUS = 1", "3×3×3（±1）"),
                        ("CONTACT_SONIC_DAMAGE = 3.0F", "建材声波 3 点")):
    if _needle not in _mf_src:
        _bg16_bad("bg16-trait-constant", f"MetalFamily 里 {_needle} 不在位（应为{_value}）")

# ---------- 8) 批 2：金玫瑰丛 ----------
_blocks_src = strip_comments((JAVA / "registry" / "AllBlocks.java").read_text(encoding="utf-8"))
for _needle, _tag, _why in (
        ('BLOCKS.register("golden_rose_bush"', "bg16-rose-block", "AllBlocks 没注册 golden_rose_bush"),
        ("TallFlowerBlock", "bg16-rose-tall-flower", "金玫瑰丛不是双层花（TallFlowerBlock）"),
        ("GOLDEN_ROSE_BUSH_ITEM", "bg16-rose-item", "金玫瑰丛没有 BlockItem"),
        ("ofFullCopy(net.minecraft.world.level.block.Blocks.ROSE_BUSH)", "bg16-rose-properties",
         "金玫瑰丛的属性没有照抄原版玫瑰丛")):
    if _needle not in _blocks_src:
        _bg16_bad(_tag, _why)
_rose_assets = _RES / "assets" / "bettergold"
for _rel, _tag in (("blockstates/golden_rose_bush.json", "bg16-rose-blockstate"),
                   ("models/block/golden_rose_bush_top.json", "bg16-rose-model-top"),
                   ("models/block/golden_rose_bush_bottom.json", "bg16-rose-model-bottom"),
                   ("models/item/golden_rose_bush.json", "bg16-rose-item-model"),
                   ("textures/block/golden_rose_bush_top.png", "bg16-rose-tex-top"),
                   ("textures/block/golden_rose_bush_bottom.png", "bg16-rose-tex-bottom")):
    if not (_rose_assets / _rel).is_file():
        _bg16_bad(_tag, f"金玫瑰丛缺 assets/bettergold/{_rel}")
_rose_loot = _DATA / "bettergold" / "loot_table" / "blocks" / "golden_rose_bush.json"
if not _rose_loot.is_file():
    _bg16_bad("bg16-rose-loot", "金玫瑰丛缺掉落表（双层花必须带 half=lower 条件，否则上下两半各掉一次）")
else:
    _rl = json.dumps(json.loads(_rose_loot.read_text(encoding="utf-8")), ensure_ascii=False)
    if '"half"' not in _rl or '"lower"' not in _rl:
        _bg16_bad("bg16-rose-loot-condition", "金玫瑰丛的掉落表没有 half=lower 条件（会双倍掉落）")
# 负向：纯装饰 ⇒ 它不许出现在任何 trait 逻辑里
if "golden_rose_bush" in _events_src or "GOLDEN_ROSE_BUSH" in _events_src:
    _bg16_bad("bg16-rose-no-trait", "金玫瑰丛出现在了 MetalEvents 里（作者要求「纯装饰」，不许有功能）")

# ---------- 9) 批 2：炼金珍材盒 + 珍宝礼物 12 张 ----------
_items_src = strip_comments((JAVA / "registry" / "AllItems.java").read_text(encoding="utf-8"))
if 'ITEMS.register("alchemy_materials_box"' not in _items_src:
    _bg16_bad("bg16-box-item", "AllItems 没注册 alchemy_materials_box")
_gift_src = strip_comments((JAVA / "item" / "GiftBoxItem.java").read_text(encoding="utf-8"))
for _needle, _tag, _why in (("ALCHEMY", "bg16-box-kind", "GiftBoxItem 没有 ALCHEMY 这一档"),
                            ("case ALCHEMY -> rollAlchemy(", "bg16-box-dispatch", "开盒没有派发到 rollAlchemy"),
                            ("MetalFamily.all()", "bg16-box-pool", "珍材盒的池子不是从家族表现算（写死清单会漏新族）"),
                            ("chest(\"buried_treasure\")", "bg16-treasure-buried", "珍宝礼物没有追加 chests/buried_treasure"),
                            ('chest("trial_chambers/reward")', "bg16-treasure-trial", "珍宝礼物丢了 trial_chambers 那张")):
    if _needle not in _gift_src:
        _bg16_bad(_tag, _why)
_treasure_count = _gift_src.count("chest(\"")
if _treasure_count != 12:
    _bg16_bad("bg16-treasure-count",
              f"TREASURE_TABLES 是 {_treasure_count} 张（1.6 应为 12 张：实际原有的 11 张 + buried_treasure）")
_trades_src = strip_comments((JAVA / "event" / "VillageTrades.java").read_text(encoding="utf-8"))
for _needle, _tag, _why in (("computeIfAbsent(4", "bg16-trade-level", "珍材盒不在第 4 级（专家）"),
                            ("GIFT_GOLD_TICKET.get(), 7", "bg16-trade-price", "珍材盒价格不是 7 张礼品金票"),
                            ("ALCHEMY_MATERIALS_BOX", "bg16-trade-item", "第 4 级那条交易卖的不是珍材盒")):
    if _needle not in _trades_src:
        _bg16_bad(_tag, _why)
for _key in ("item.bettergold.alchemy_materials_box", "block.bettergold.golden_rose_bush"):
    if _key not in zh or _key not in en:
        _bg16_bad("bg16-spare-lang", f"三个散件缺语言键 {_key}")

# ---------- 7) 金属弩的**实际蓄力口径**（bg-16 收口轮：规格写的「20 tick」已被 A 级实测推翻） ----------
# 事实（【读源码】+【实测】）：原版「装满」判定在 CrossbowItem#releaseUsing 里除以的是
#   **static** 的 `CrossbowItem.getChargeDuration`（基础 1.25F × 20 = **25 tick**），压根不读我们覆写的
#   `getUseDuration`（= chargeDuration + 3 = **23**）⇒ `f_max = 23/25 = 0.92 < 1`，按住 23 tick 装不上；
#   按住超过 getUseDuration 之后 useItemRemaining 转负、松手时 i = 实际按住 tick 数 ⇒ **真正装满要 ≥ 25 tick**。
#   实测：真玩家按住 40 tick，期间 CHARGED_PROJECTILES 恒空、松手那一 tick 才 charged=true
#   （docs/bg16-证据/10-A级-runClient读数.txt、…/12-新发现-真问题.md §二）。
# 本轮处置 = **代码不动 + 文档/注释就地更正**（原文保留）。
# 这条断言守两件事：① 口径不许被**静默**改回 20 tick；② 谁真去改装载判定（覆写 releaseUsing），
# 就**必须**同步改文档口径，不许让文档与代码再次分家。
_weapons_src = (JAVA / "material" / "MetalWeapons.java").read_text(encoding="utf-8")
_weapons_code = strip_comments(_weapons_src)
_cb_start = _weapons_code.find("class MetalCrossbowItem")
_cb_next = _weapons_code.find("public static class ", _cb_start + 1) if _cb_start >= 0 else -1
_crossbow_blk = _weapons_code[_cb_start:_cb_next] if _cb_start >= 0 and _cb_next > _cb_start else ""
if not _crossbow_blk:
    _bg16_bad("bg16-crossbow-caliber", "反空转守护：MetalWeapons.java 里找不到 MetalCrossbowItem 类体")
else:
    if "CROSSBOW_CHARGE_SECONDS = 1.0F" not in _weapons_code:
        _bg16_bad("bg16-crossbow-caliber", "CROSSBOW_CHARGE_SECONDS 不是 1.0F（规格 12.2 的「1 秒」被改过）")
    if "Mth.floor(f * 20.0F)" not in _crossbow_blk:
        _bg16_bad("bg16-crossbow-caliber", "chargeDuration 的秒→tick 换算不是 Mth.floor(f * 20.0F)")
    if "return chargeDuration(stack, entity) + 3;" not in _crossbow_blk:
        _bg16_bad("bg16-crossbow-caliber",
                  "getUseDuration 不是 chargeDuration(...) + 3（它只决定「举着的时长上限」= 23）")
    if "releaseUsing(" in _crossbow_blk:
        _bg16_bad("bg16-crossbow-caliber",
                  "MetalCrossbowItem 覆写了 releaseUsing（= 装载门槛真被改了）：实际口径已变，"
                  "必须同步更新 docs/1.5-规格.md §12.2 的「⚠ 更正」块与 docs/1.6-规格.md 的口径后再改这条断言")
# 反空转守护 + 文档侧：口径更正必须在位（原文保留 + 新口径写明）
_spec15 = (REPO / "docs" / "1.5-规格.md").read_text(encoding="utf-8")
_spec16 = (REPO / "docs" / "1.6-规格.md").read_text(encoding="utf-8")
if "沿用原版的 25 tick 分母" not in _spec15 or "已被实测推翻" not in _spec15:
    _bg16_bad("bg16-crossbow-caliber-doc15",
              "docs/1.5-规格.md §12.2 缺「已被实测推翻」的就地标注或「沿用原版的 25 tick 分母」的新口径")
if "沿用原版的 25 tick 分母" not in _spec16:
    _bg16_bad("bg16-crossbow-caliber-doc16",
              "docs/1.6-规格.md 缺弩的 25 tick 新口径标注（§6.4 / §7.4 第 2 条的收口段）")

print(f"bg-16 两处修正（横幅落点 / 安抚对玩家）问题: {len(bg16_problems)} {bg16_problems[:8]}")

sys.exit(1 if (missing_zh or missing_en or missing_loot or missing_knife_tags or missing_weapon_tags
               or bg15w_problems or bg8_problems or bg9_problems
               or bg16_problems
               or symmetric_problems or beacon_problems) else 0)
