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

METALS = ["flamegold", "voodoogold", "thundergold", "indigoseagold", "illusiongold"]
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
           "indigo_ocean_heart", "chorus_cherry_branch"]
EFFECTS = ["high_burn", "voodoo", "tremble", "sediment", "soothe"]
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

# --- ① 装备分区顺序（作者 17:44 字面：剑 重锤 三叉戟 弓 弩 盾牌 头胸腿靴，斧镐锹锄排最后） ---
GEAR_SLOT_EXPECTED = ["sword", "mace", "trident", "bow", "crossbow", "shield",
                       "helmet", "chestplate", "leggings", "boots",
                       "axe", "pickaxe", "shovel", "hoe"]
# 作者列表里**没有**的四件：必须仍在表里（§8.1 的保守做法），只是位次最后
OMITTED_BUT_KEPT = ["axe", "pickaxe", "shovel", "hoe"]

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
        bg8_problems.append(f"GEAR_SLOT 顺序不是作者字面：{by_rank}")
    if sorted(gear.values()) != list(range(len(GEAR_SLOT_EXPECTED))):
        bg8_problems.append(f"GEAR_SLOT 位次不是 0..{len(GEAR_SLOT_EXPECTED) - 1} 各一次：{sorted(gear.values())}")
    for item in OMITTED_BUT_KEPT:
        if item not in gear:
            bg8_problems.append(
                f"GEAR_SLOT 里少了 {item} —— 作者列表没提它不等于要删（删了它会静默掉出装备分区）")
    # 那四件必须排在被描述的那 10 件之后
    described_max = max(gear[n] for n in GEAR_SLOT_EXPECTED[:10] if n in gear)
    for item in OMITTED_BUT_KEPT:
        if item in gear and gear[item] <= described_max:
            bg8_problems.append(f"{item} 的位次 {gear[item]} 不在那 10 件之后（期望 > {described_max}）")
print(f"装备分区顺序（§8.1）问题: {len(bg8_problems)} {bg8_problems[:8]}")

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

sys.exit(1 if (missing_zh or missing_en or missing_loot or missing_knife_tags or missing_weapon_tags
               or bg15w_problems or bg8_problems) else 0)
