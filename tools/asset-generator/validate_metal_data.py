#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验：MetalFamily 会注册出来的每个物品/方块，在 zh_cn / en_us 里是否都有语言条目。"""
from __future__ import annotations
import json
import re
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

# ---------- 6b) 免疫仙人掌：判据必须把「核心材料」也算进去（bg-16 裁定落实轮，2026-10-04） ----------
# 作者裁定的原话范围：「核心材料也要免疫仙人掌」「范围＝八套金属的 coreItem 全部」，
# 并要求「八族 coreItem 逐一断言 immune=true」（那条是 A 级探针侧的断言）。
# 事实：核心材料（MetalSpecialItems / AllItems 注册的那些）**不在**任何族的 allItems 里
#   ⇒ 它们没进 BY_ITEM ⇒ 原先那句 `MetalFamily.of(...) != null && family.cactusImmune`
#   对它们恒为 false，也就是「闪耀藤条这类核心材料不免疫」——那正是本轮要修的行为。
# 现行落点 = MetalFamily.isCactusImmune(Item)：家族索引命中 ⇒ 看该族旗标；
#   否则看它是不是某族的 coreItem ⇒ **一律免疫**（与旗标无关，这是作者这一轮给的范围）。
# ⚠ 八族的 coreItem 符号**从 AllMetals.java 现算**，不写死清单 —— 写死清单 = 加族时静默漏（§2.2）。
_all_metals_code = strip_comments(_all_metals_src)
_core_items = re.findall(r"\.coreItem\(\(\)\s*->\s*([A-Za-z0-9_.]+)\.get\(\)\)", _all_metals_code)
if len(_core_items) != 8:
    _bg16_bad("bg16-cactus-coreitem-anti-vacuum",
              f"AllMetals.java 里现算出 {len(_core_items)} 个 `.coreItem(() -> X.get())`（应为八族 8 个）")
elif len(set(_core_items)) != 8:
    _bg16_bad("bg16-cactus-coreitem-distinct",
              f"八族里有重复的 coreItem 符号：{sorted(_core_items)}")
_core_owner_body = method_body(_mf_src, "public static @Nullable MetalFamily coreItemOwner(")
if not _core_owner_body:
    _bg16_bad("bg16-cactus-coreitem-owner",
              "MetalFamily 缺 coreItemOwner(Item)（核心材料的单独查表；反空转守护）")
elif "BY_ID.values()" not in _core_owner_body or "core.get() == item" not in _core_owner_body:
    _bg16_bad("bg16-cactus-coreitem-owner",
              "coreItemOwner 没有遍历家族表并逐族比较 coreItem（判别 cores 的写法被改过）")
_immune_body = method_body(_mf_src, "public static boolean isCactusImmune(")
if not _immune_body:
    _bg16_bad("bg16-cactus-coreitem-predicate",
              "MetalFamily 缺 isCactusImmune(Item)（免疫仙人掌的统一判据；反空转守护）")
else:
    if "cactusImmune" not in _immune_body:
        _bg16_bad("bg16-cactus-coreitem-predicate",
                  "isCactusImmune 没有读该族的 cactusImmune 旗标（家族索引那条分支丢了）")
    if "coreItemOwner(" not in _immune_body:
        _bg16_bad("bg16-cactus-coreitem-predicate",
                  "isCactusImmune 没有走 coreItemOwner(（核心材料那条分支丢了）")
    if "return coreItemOwner(item) != null;" not in _immune_body:
        _bg16_bad("bg16-cactus-coreitem-blanket",
                  "isCactusImmune 的核心材料分支不是「是某族 coreItem ⇒ 一律免疫」"
                  "（作者裁定的范围＝八套金属的 coreItem 全部）")
_immune_evt = method_body(_events_src, "public static void onCactusItemImmunity(")
if not _immune_evt:
    _bg16_bad("bg16-cactus-coreitem-event",
              "MetalEvents 里找不到 onCactusItemImmunity 方法体（反空转守护）")
elif "MetalFamily.isCactusImmune(" not in _immune_evt:
    _bg16_bad("bg16-cactus-coreitem-event",
              "onCactusItemImmunity 没走 MetalFamily.isCactusImmune(（核心材料仍会被仙人掌摧毁）")

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

# ---------- 7) 金属弩的蓄力口径（bg-16 裁定落实轮，2026-10-04：作者裁定「真改」⇒ 本模组弩 20 tick） ----------
# 事实（【读源码】neoforge 21.1.228 sources）：
#   `public static int CrossbowItem#getChargeDuration(ItemStack, LivingEntity)`（`CrossbowItem.java:257-260`，
#   基础 `1.25F × 20 = 25`）被 `getPowerForTime`（`:274-281` ← **装载门槛**，经 `releaseUsing` `:102-121`）、
#   `getUseDuration`（`:253-255`）、`onUseTick`（`:224`）、客户端 `ItemProperties`（`:193`）读。
#   而 `CrossbowItem#useOnRelease` 恒 `true`（`:307-309`）⇒ `LivingEntity#updateUsingItem`（`:3151-3163`）
#   不会自动收手 ⇒ 松手时 `i = 实际按住的 tick 数`（**不被** `getUseDuration` 截断）
#   ⇒ **装载门槛精确等于那个分母**：分母 20 ⇒ 按住 19 不装、20 装。
# 落点 = `mixin/CrossbowChargeDurationMixin.java`（MixinExtras `@ModifyReturnValue`、`require = 1` 写死），
#   登记在 `bettergold.mixins.json` 的 **common** 列表（双端；**不在** client 列表）。
# 硬要求：**不许波及原版弩与任何第三方弩** ⇒ 守卫必须 `instanceof MetalCrossbowItem`，否则 `return original;`。
# 上一轮那条「实际沿用原版 25 tick / 代码不动」的口径**已被本裁定取代**（原文在文档里保留，不许静默删）。
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
                  "MetalCrossbowItem 覆写了 releaseUsing：那是**另一条落点**，与本轮选的 mixin 会分家，"
                  "二选一（本轮选 mixin）；改完同步文档后再改这条断言")

# 7b) mixin 落点本身：文件 + 注入形状 + require + **守卫（不波及其它弩）**
_mixin_crossbow = JAVA / "mixin" / "CrossbowChargeDurationMixin.java"
_cb_mixin_code = ""
if not _mixin_crossbow.is_file():
    _bg16_bad("bg16-crossbow-mixin-file",
              "缺 mixin/CrossbowChargeDurationMixin.java（本模组弩 20 tick 的落点）")
else:
    _cb_mixin_code = strip_comments(_mixin_crossbow.read_text(encoding="utf-8"))
if _cb_mixin_code:
    for _needle, _tag, _why in (
            ("@Mixin(CrossbowItem.class)", "bg16-crossbow-mixin-target",
             "mixin 的目标不是 CrossbowItem"),
            ("ModifyReturnValue", "bg16-crossbow-mixin-injector",
             "没用 @ModifyReturnValue（改的是返回值，不是语句）"),
            ('"getChargeDuration(Lnet/minecraft/world/item/ItemStack;'
             'Lnet/minecraft/world/entity/LivingEntity;)I"', "bg16-crossbow-mixin-descriptor",
             "目标方法没写完整描述符（原版改签名时会静默找不到注入点）"),
            ("require = 1", "bg16-crossbow-mixin-require",
             "require 没写死成 1（形状改了就不会当场报错）"),
            ('@At("RETURN")', "bg16-crossbow-mixin-at",
             "注入点不是 RETURN"),
            ("instanceof MetalWeapons.MetalCrossbowItem", "bg16-crossbow-mixin-guard",
             "没有 instanceof 守卫（会波及原版弩与第三方弩）"),
            ("return original;", "bg16-crossbow-mixin-passthrough",
             "没有把非本模组物品原样放回（会波及原版弩与第三方弩）"),
            ("return MetalWeapons.MetalCrossbowItem.chargeDuration(stack, shooter);",
             "bg16-crossbow-mixin-value",
             "返回值不是 MetalCrossbowItem.chargeDuration(...)（20 tick 口径没接上）")):
        if _needle not in _cb_mixin_code:
            _bg16_bad(_tag, _why)
    # 结构性顺序：守卫必须在「换算成 20 tick」之前（反了 = 先改后判，原版弩也会被改）
    _guard_at = _cb_mixin_code.find("instanceof MetalWeapons.MetalCrossbowItem")
    _value_at = _cb_mixin_code.find("chargeDuration(stack, shooter)")
    if _guard_at < 0 or _value_at < 0 or _guard_at > _value_at:
        _bg16_bad("bg16-crossbow-mixin-guard-first",
                  "「instanceof 守卫」没有出现在「返回 20 tick」之前（顺序反了 = 原版弩也会被改）")
# 列表：必须在 **`mixins`**（Sponge Mixin 里"双端"那个列表就叫这个名字）里，
# 且不许误登记进 `client` / `server`（漏了列表 = 静默不加载；放错列表 = 服务端/客户端没有这条行为）。
# ⚠ 本仓实测教训（bg-17，2026-10-04）：**写 `"common"` 是无效键** —— Mixin 只认 `mixins` / `client` / `server`，
#   未知键被**静默忽略**（`required: true` 也不会报错，因为那个列表空 ⇒ 没有东西需要 apply）
#   ⇒ A 级实测里 `CrossbowItem.getChargeDuration(本模组弩)` 仍是 **25**、mixin 一次都没加载。
_cb_name = "CrossbowChargeDurationMixin"
_mixins_json = json.loads(_mixins_txt) if _mixins_txt.strip() else {}
if _cb_name not in _mixins_json.get("mixins", []):
    _bg16_bad("bg16-crossbow-mixin-listed",
              "bettergold.mixins.json 的 mixins 列表里没有 CrossbowChargeDurationMixin"
              "（注意：双端列表的键名是 `mixins`，写 `common` 会被静默忽略 = mixin 不加载）")
if _cb_name in _mixins_json.get("client", []):
    _bg16_bad("bg16-crossbow-mixin-side",
              "CrossbowChargeDurationMixin 被登记进了 client 列表；它改的是双端的 getChargeDuration，必须走 mixins")
if _cb_name in _mixins_json.get("server", []):
    _bg16_bad("bg16-crossbow-mixin-side",
              "CrossbowChargeDurationMixin 被登记进了 server 列表；它改的是双端的 getChargeDuration，必须走 mixins")

# 7c) 文档侧：**上一轮的原文保留**（不许静默删）+ **本裁定的新口径在位**
_spec15 = (REPO / "docs" / "1.5-规格.md").read_text(encoding="utf-8")
_spec16 = (REPO / "docs" / "1.6-规格.md").read_text(encoding="utf-8")
if "已被实测推翻" not in _spec15 or "沿用原版的 25 tick 分母" not in _spec15:
    _bg16_bad("bg16-crossbow-caliber-doc15",
              "docs/1.5-规格.md §12.2 缺上一轮的「已被实测推翻 / 沿用原版的 25 tick 分母」原文（不许静默删）")
if "已被本裁定取代" not in _spec15 or "本模组弩：蓄力 = 20 tick" not in _spec15:
    _bg16_bad("bg16-crossbow-caliber-doc15-new",
              "docs/1.5-规格.md §12.2 缺本裁定的新口径（须含「已被本裁定取代」与「本模组弩：蓄力 = 20 tick」）")
if "沿用原版的 25 tick 分母" not in _spec16:
    _bg16_bad("bg16-crossbow-caliber-doc16",
              "docs/1.6-规格.md 缺上一轮 25 tick 口径的收口段（原文保留）")
if "已被本裁定取代" not in _spec16 or "本模组弩：蓄力 = 20 tick" not in _spec16:
    _bg16_bad("bg16-crossbow-caliber-doc16-new",
              "docs/1.6-规格.md 缺本裁定的新口径（须含「已被本裁定取代」与「本模组弩：蓄力 = 20 tick」）")

# ==================== bg-book（2026-10-04）：帕秋莉手册 ====================
# 本轮形状由两条**读 jar 得到**的事实决定（`Patchouli-1.21.1-93-NEOFORGE.jar`，Modrinth `maven.modrinth:patchouli`）：
#
#  ① **"全是 JSON"只对书/类别/条目成立，"右键打开"这一下必须有代码**：
#     - `ItemModBook#use` 打开哪本书来自**堆叠上的 `patchouli:book` 数据组件**
#       （`ItemModBook#getBookId`：`stack.has(PatchouliDataComponents.BOOK) ? stack.get(BOOK) : null`）；
#     - 而 `ItemModBook` 的构造器是 `super(new Item.Properties().stacksTo(1))`、**不接受自定义 Properties**
#       ⇒ 没法给"我方物品"挂默认组件 ⇒ 不能复用它；
#     - `book.json` 的 `custom_book_item` 只是**物品栈字符串**（`Book#lambda$new$1` →
#       `ItemStackUtil.deserializeStack` → 内部走原版 `ItemParser`），解析失败**只 warn** 然后给
#       `ItemStack.EMPTY`（静默）；而且它只在 `dont_generate_book` 为真时才生效。
#     ⇒ 落点 = 我方自己的 `Item` 子类 + `PatchouliAPI.get().openBookGUI(ServerPlayer, bookId)`
#       （与 `ItemModBook#use` 同一条路径，`PatchouliAPIImpl#openBookGUI` 不要求书已注册）。
#
#  ② **配方页的结构上限 = 每页 2 个配方**：`PageDoubleRecipe` 只有 `recipe` / `recipe2` 两个槽
#     （`@SerializedName("recipe")` / `("recipe2")`），页面类型表（`ClientBookRegistry#addPageTypes`）
#     里没有"N 个配方"那一档 ⇒ 器具（6 件）= 3 页、盔甲（4 件）= 2 页。
#     **要"6 件一页"唯一出路是自定义 page type**（= 自己写一整页客户端渲染），本轮不做。
#
#  ③ 口径 = **没装 Patchouli 就不注册手册物品**（口径 B，与农夫乐事的"总是注册、功能软依赖"相反）
#     ⇒ 所有对 Patchouli 类型的引用**只许在方法体内、且在 `isLoaded(...)` 早退之后**：
#     写在字段 / 构造器 / 静态初始化块里 = **类加载即炸**，守卫根本没机会执行。
#     配套：构建里**故意只加 compileOnly、不加 localRuntime** —— 否则 dev 永远装着 Patchouli，
#     "没装"这一档就再也造不出来（本轮两种环境实测就靠 `run/mods` 放/拿 jar）。
bgbook_problems: list[str] = []


def _bgbook_bad(tag: str, msg: str) -> None:
    bgbook_problems.append(f"{msg} [{tag}]")


_HANDBOOK_ITEM = "alchemy_student_handbook"
# ⚠ Patchouli 1.20+ 把"书"的布局劈成两半（**本轮 A 级实测抓到的，不是我们的选择**）：
#   data/bettergold/patchouli_books/<book>/book.json    <- 唯一留在**数据包**侧的文件
#   assets/bettergold/patchouli_books/<book>/<lang>/**  <- 类别 / 条目 / 页面全在**客户端资源**侧
# 而且 book.json 必须 `"use_resource_pack": true`（1.20 起数据包侧的内容加载已被移除）。
# 把内容放在 data/ 下 ⇒ Patchouli 抛 `IllegalArgumentException: Book … has use_resource_pack set
# to false. This behaviour was removed in 1.20.` 并**整本书被跳过**（`Book.java:148` ←
# `BookRegistry.loadBook`），表现是"物品在、右键打不开、日志里一条 ERROR"。
_BOOK_ROOT = _DATA / "bettergold" / "patchouli_books" / "alchemy_handbook"
_ASSET_ROOT = _RES / "assets" / "bettergold" / "patchouli_books" / "alchemy_handbook"
_ZH_BOOK = _ASSET_ROOT / "zh_cn"
_EN_BOOK = _ASSET_ROOT / "en_us"

# ---------- 1) 依赖声明：optional（**不是 required**）+ 只写下限 + AFTER ----------
# 判据跑在**去掉注释**后的文本上（TOML 的注释以 `#` 开头）：否则注释里提一句 `type="required"`
# 就会让负向断言**假红**（mcmod_experience §3.4 那条"注释既能喂饱正向断言、也能误伤负向断言"）。
_mods_toml_raw = (REPO / "src/main/resources/META-INF/neoforge.mods.toml").read_text(encoding="utf-8")
_mods_toml_txt = re.sub(r"(?m)#[^\n]*", "", _mods_toml_raw)
_dep_blocks = re.findall(r"\[\[dependencies\.[^\]]+\]\](.*?)(?=\[\[|\Z)", _mods_toml_txt, re.S)
_patchouli_blocks = [b for b in _dep_blocks if re.search(r'modId\s*=\s*"patchouli"', b)]
if not _patchouli_blocks:
    _bgbook_bad("bgbook-dep-optional", "neoforge.mods.toml 里没有 patchouli 的依赖声明块")
else:
    _dep = _patchouli_blocks[0]
    if not re.search(r'type\s*=\s*"optional"', _dep):
        _bgbook_bad("bgbook-dep-optional", "patchouli 依赖不是 optional（没装它就会拒载）")
    if re.search(r'type\s*=\s*"(required|incompatible)"', _dep):
        _bgbook_bad("bgbook-dep-optional", "patchouli 依赖被写成了 required / incompatible")
    if not re.search(r'versionRange\s*=\s*"\[1\.21\.1-93,\)"', _dep):
        _bgbook_bad("bgbook-dep-versionrange",
                    "patchouli 的 versionRange 不是只写下限的 [1.21.1-93,)（写了上界 = 它更新一次就拒载）")
    if not re.search(r'ordering\s*=\s*"AFTER"', _dep):
        _bgbook_bad("bgbook-dep-ordering",
                    "patchouli 依赖没有 ordering=AFTER（本模组要往它的体系里登记书 / 类别）")

# ---------- 2) 构建：compileOnly，且**故意没有 localRuntime** ----------
# 同样跑在去注释后的文本上（注释里提一句 localRuntime 不该让它假红）
_gradle_txt = strip_comments((REPO / "build.gradle").read_text(encoding="utf-8"))
if 'compileOnly "maven.modrinth:patchouli:${patchouli_version}"' not in _gradle_txt:
    _bgbook_bad("bgbook-gradle-compile-only", "build.gradle 没有 patchouli 的 compileOnly 依赖行")
if re.search(r"localRuntime\s+\"maven\.modrinth:patchouli", _gradle_txt):
    _bgbook_bad("bgbook-gradle-no-localruntime",
                "build.gradle 给 patchouli 加了 localRuntime ⇒ dev 环境永远装着它，"
                "「没装 Patchouli」这一档再也造不出来（本轮的两种环境实测依赖它）")
if "patchouli_version=" not in (REPO / "gradle.properties").read_text(encoding="utf-8"):
    _bgbook_bad("bgbook-gradle-version", "gradle.properties 里没有 patchouli_version（版本号必须只有一处真源）")

# ---------- 3) 类加载隔离：全仓只有 patchouli/PatchouliCompat.java 能引用 Patchouli 的类型 ----------
_ref_files = []
for _p in sorted(JAVA.rglob("*.java")):
    if "probe" in _p.parts:  # 探针（临时验证代码）不算生产代码；收尾整块删除
        continue
    _txt = strip_comments(_p.read_text(encoding="utf-8"))
    if "vazkii.patchouli" in _txt or "vazkii/patchouli" in _txt:
        _ref_files.append(_p)
if [p.name for p in _ref_files] != ["PatchouliCompat.java"]:
    _bgbook_bad("bgbook-isolation-single-file",
                "引用 vazkii.patchouli 的生产代码文件必须**只有** patchouli/PatchouliCompat.java，实际 "
                + str([str(p.relative_to(REPO)) for p in _ref_files]))
_compat_path = JAVA / "patchouli" / "PatchouliCompat.java"
_compat_code = strip_comments(_compat_path.read_text(encoding="utf-8")) if _compat_path.is_file() else ""
if not _compat_code:
    _bgbook_bad("bgbook-isolation-single-file", "反空转守护：找不到 patchouli/PatchouliCompat.java")
else:
    # 判据只看**方法体**里的使用点：`import vazkii.patchouli.…` 本来就在最上面（那是允许的）
    _compat_body = "\n".join(
        _l for _l in _compat_code.splitlines() if not _l.strip().startswith("import "))
    _guard_at = _compat_body.find("isLoaded()")
    _api_positions = [i for i in (_compat_body.find("PatchouliAPI"), _compat_body.find("PatchouliSounds"))
                      if i >= 0]
    _first_api = min(_api_positions) if _api_positions else -1
    if _guard_at < 0:
        _bgbook_bad("bgbook-isolation-guard", "PatchouliCompat 里没有 isLoaded() 早退守卫")
    elif _first_api >= 0 and _guard_at > _first_api:
        _bgbook_bad("bgbook-isolation-guard",
                    "PatchouliCompat 的 isLoaded() 守卫出现在第一次触碰 Patchouli 类型**之后**"
                    "（顺序反了 = 没装时照样会去解析对方的类）")
    for _i, _line in enumerate(_compat_code.splitlines()):
        if _line.strip().startswith("import "):
            continue
        if not re.search(r"Patchouli(API|Sounds|DataComponents|Items)", _line):
            continue
        if re.match(r"^\s*(public|private|protected|static|final|transient)\s+[\w.<>\[\],\s]+\s+\w+\s*[=;]",
                    _line):
            _bgbook_bad("bgbook-isolation-no-field",
                        "PatchouliCompat 第 %d 行把 Patchouli 类型写进了字段声明（类加载即炸）" % (_i + 1))
    _static_blk = re.search(r"static\s*\{[^}]*\}", _compat_code)
    if _static_blk and "Patchouli" in _static_blk.group(0):
        _bgbook_bad("bgbook-isolation-no-static-init",
                    "PatchouliCompat 的静态初始化块里出现了 Patchouli 类型（类加载即炸）")

# ---------- 4) 物品注册必须在环境判定之内 ----------
_module_path = JAVA / "patchouli" / "HandbookModule.java"
_module_code = strip_comments(_module_path.read_text(encoding="utf-8")) if _module_path.is_file() else ""
if not _module_code:
    _bgbook_bad("bgbook-item-guarded", "反空转守护：找不到 patchouli/HandbookModule.java")
elif 'isLoaded("patchouli")' not in _module_code:
    _bgbook_bad("bgbook-item-guarded",
                "HandbookModule 没有用 ModList.get().isLoaded(\"patchouli\") 作为第一道闸")
_all_items_code = strip_comments((JAVA / "registry" / "AllItems.java").read_text(encoding="utf-8"))
if "HandbookModule.register(ITEMS)" not in _all_items_code:
    _bgbook_bad("bgbook-item-guarded", "AllItems 没有通过 HandbookModule.register(ITEMS) 做条件注册")
if re.search(r'ITEMS\.register\(\s*"' + _HANDBOOK_ITEM + r'"', _all_items_code):
    _bgbook_bad("bgbook-item-guarded",
                "AllItems 直接注册了手册物品（绕过了环境判定 ⇒ 没装 Patchouli 时它也会存在）")

# ---------- 5) 创造页：材料分区第一位 ----------
_cts_code = strip_comments((JAVA / "material" / "CreativeTabSections.java").read_text(encoding="utf-8"))
_mat_start = _cts_code.find("List<Slot> MATERIALS")
_mat_end = _cts_code.find(");", _mat_start) if _mat_start >= 0 else -1
_mat_blk = _cts_code[_mat_start:_mat_end] if _mat_start >= 0 and _mat_end > _mat_start else ""
if not _mat_blk:
    _bgbook_bad("bgbook-creative-first", "反空转守护：找不到 CreativeTabSections.MATERIALS 的段列表")
else:
    _hb_at = _mat_blk.find("isHandbook")
    _other_at = _mat_blk.find('"其他材料"')
    if _hb_at < 0:
        _bgbook_bad("bgbook-creative-first", "材料分区的段列表里没有手册那一段")
    elif _other_at >= 0 and _hb_at > _other_at:
        _bgbook_bad("bgbook-creative-first",
                    "手册那一段不在材料分区**第一位**（作者要的是「材料位第一」）")

# ---------- 6) 书的数据树：结构 ----------
if not (_BOOK_ROOT / "book.json").is_file():
    _bgbook_bad("bgbook-book-json", "缺 patchouli_books/alchemy_handbook/book.json")
else:
    _book = json.loads((_BOOK_ROOT / "book.json").read_text(encoding="utf-8"))
    if _book.get("custom_book_item") != "bettergold:%s" % _HANDBOOK_ITEM:
        _bgbook_bad("bgbook-book-custom-item",
                    "book.json 的 custom_book_item 不是 bettergold:alchemy_student_handbook"
                    "（它是**物品栈字符串**，写错只 warn 后变成 ItemStack.EMPTY = 静默）")
    if _book.get("dont_generate_book") is not True:
        _bgbook_bad("bgbook-book-dont-generate",
                    "book.json 没有 dont_generate_book=true"
                    "（否则 Patchouli 会另生成自带书物品；custom_book_item 也只在它为真时生效）")
    for _k in ("name", "landing_text"):
        _v = _book.get(_k)
        if not isinstance(_v, str) or not _v.startswith("bettergold.handbook"):
            _bgbook_bad("bgbook-book-keys", "book.json 的 %s 不是 bettergold.handbook.* 语言键" % _k)
    if _book.get("use_resource_pack") is not True:
        _bgbook_bad("bgbook-book-resource-pack",
                    "book.json 没有 use_resource_pack=true：Patchouli 1.20 起数据包侧的内容加载已被移除"
                    "（缺了会抛 IllegalArgumentException 并**整本书被跳过**、右键打不开）")
    if _book.get("i18n") is not True:
        _bgbook_bad("bgbook-book-i18n", "book.json 没有 i18n=true（类别 / 条目要按语言目录取文件）")

# 布局劈两半：数据包侧**只许**有 book.json；类别 / 条目必须在 assets 侧（负向断言守住本轮抓到的真 bug）
for _lang_dir in ("zh_cn", "en_us"):
    _stray = _BOOK_ROOT / _lang_dir
    if _stray.exists():
        _bgbook_bad("bgbook-book-split",
                    "内容仍留在数据包侧 %s：Patchouli 1.20 起内容必须在 assets/，data/ 下只留 book.json"
                    % _stray.relative_to(REPO))
if not (_ASSET_ROOT / "zh_cn" / "entries").is_dir() or not (_ASSET_ROOT / "en_us" / "entries").is_dir():
    _bgbook_bad("bgbook-book-split", "assets 侧缺 zh_cn/entries 或 en_us/entries（布局被搬回 data/ 了？）")

_zh_files = sorted(str(p.relative_to(_ZH_BOOK)).replace("\\", "/")
                   for p in _ZH_BOOK.rglob("*.json")) if _ZH_BOOK.is_dir() else []
_en_files = sorted(str(p.relative_to(_EN_BOOK)).replace("\\", "/")
                   for p in _EN_BOOK.rglob("*.json")) if _EN_BOOK.is_dir() else []
if _zh_files != _en_files:
    _bgbook_bad("bgbook-book-bilingual",
                "zh_cn 与 en_us 的书文件集合不一致（差集 = %s）" % sorted(set(_zh_files) ^ set(_en_files)))
if len(_zh_files) < 11:
    _bgbook_bad("bgbook-book-anti-vacuum",
                "zh_cn 下的书 JSON 只有 %d 个（4 类别 + 7 条目 = 11；数据树被清空会命中这条）"
                % len(_zh_files))

# 四个类别：顺序（sortnum）= 作者给的顺序，**材料类必须第一**，图标逐一钉住（§3.3）
_EXPECT_CATEGORIES = [("alchemy_start", "bettergold:raw_sturdygold"),
                      ("gear_upgrade", "bettergold:sturdygold_sword"),
                      ("golden_feast", "bettergold:sturdygold_apple"),
                      ("merchant_antiques", "bettergold:gold_exchange_counter")]
_cats_now = []
for _p in sorted((_ZH_BOOK / "categories").glob("*.json")) if (_ZH_BOOK / "categories").is_dir() else []:
    _c = json.loads(_p.read_text(encoding="utf-8"))
    _cats_now.append((_c.get("sortnum", 999), _p.stem, _c.get("icon")))
_cats_now.sort()
if [(c[1], c[2]) for c in _cats_now] != _EXPECT_CATEGORIES:
    _bgbook_bad("bgbook-categories",
                "四个类别（按 sortnum）必须是 %s，实际 %s"
                % (_EXPECT_CATEGORIES, [(c[1], c[2]) for c in _cats_now]))

# ---------- 7) 条目 / 页面：页数从"金属套数"现算 + 配方引用不许死链 + 每页 ≤ 2 个配方 ----------
_KNOWN_PAGE_TYPES = {"patchouli:text", "patchouli:crafting", "patchouli:smithing", "patchouli:spotlight",
                     "patchouli:smelting", "patchouli:blasting", "patchouli:smoking", "patchouli:campfire",
                     "patchouli:stonecutting", "patchouli:image", "patchouli:empty", "patchouli:link",
                     "patchouli:relations", "patchouli:entity", "patchouli:quest", "patchouli:multiblock",
                     "patchouli:template"}
# ⛔ **bg-book §八（2026-10-06）作废并删除了下面两个条目**（§8.1「删除手册四类里的『装备的升级』
#    类别（整个类别）」）⇒ 它们**不再是产物**，而是"必须不存在"（见下面的负向断言）。
#    ⚠ 旧期望**原文保留在这里**（未删）：`_EXPECT_TOOL_PAGES = 1 + len(ALL_METALS) * 3`（= 25）、
#      `_EXPECT_ARMOR_PAGES = 1 + len(ALL_METALS) * 2`（= 17）；两个条目的全文对照（页型序列 / 页数 /
#      分组）落在 `docs/1.6-规格.md` §十九。
_RETIRED_ENTRIES = ("tools_per_family", "armor_per_family")
_entries_now = {}
for _p in sorted((_ZH_BOOK / "entries").glob("*.json")) if (_ZH_BOOK / "entries").is_dir() else []:
    _entries_now[_p.stem] = json.loads(_p.read_text(encoding="utf-8"))
# 第一轮骨架 7 项 − §八 作废 2 项 − §九 作废 2 项 = **3**
#   ⛔ §九（2026-10-06 20:02）作废的是「商人与古董」类别下的两个旧占位
#      `merchant` / `antiques`（§9.1 作者原话「之前你设的那两个就可以就此毙掉了」），
#      由 §九 的 3 章（`merchant_intro` / `merchant_gift_box` / `merchant_antique_gear`）取代。
#   ⚠ 旧期望 `("metal_tour", "upgrade_templates", "golden_feast", "merchant", "antiques")`
#     **原文保留在这里**（未删）；两个旧条目的全文对照落在 `docs/1.6-规格.md` §21。
# ⛔ **bg-fix3 §三（作者 2026-10-07）：「将手册中『贵金的材料链』与『升级锻造模版』两部分删去」**
#   ⇒ 骨架里剩下的 `metal_tour` / `upgrade_templates` **本轮也作废**（它们才是那两个"部分"：
#     条目名的语言键值逐字就是「贵金的材料链」/「升级锻造模板」）。
#   ⚠ 旧期望原文保留（未删）：`_SKELETON_ENTRIES = ("metal_tour", "upgrade_templates", "golden_feast")`。
#   ⇒ 骨架只剩 **1** 条（`golden_feast`）；两个条目的全文对照落在 `docs/1.6-规格.md` §二十二。
_SKELETON_ENTRIES = ("golden_feast",)
# bg-fix3 §三 作废的两个骨架条目：产物里**必须不存在**（负向断言），生成器里**必须仍在**
# RETIRED_ENTRIES 且页数照常算得出来（8 族材料链 9 页 / 8 张模板 5 页）。
_BGFIX3_RETIRED_ENTRIES = ("metal_tour", "upgrade_templates")
_BGFIX3_RETIRED_PAGES = {"metal_tour": 9, "upgrade_templates": 5}
# bg-book §六 追加轮（2026-10-05）：三章（副要材料 / 核心材料 / 知识）
_BG2_ENTRY_NAMES = ("auxiliary_materials", "core_materials", "golden_knowledge")
# bg-book §八 追加轮（2026-10-06）：「装备的强化」9 章（1 章联动/胚底 + 8 章金属）
_BG8_ENTRY_NAMES = ("gear_linkage",) + tuple("gear_%s" % _c for _c in
    ("flamegold", "sturdygold", "thornsgold", "echogold",
     "indigoseagold", "voodoogold", "thundergold", "illusiongold"))
# bg-book §九 追加轮（2026-10-06 20:02）：「商人与古董」3 章（替掉该类别旧占位两节）
_BG9_ENTRY_NAMES = ("merchant_intro", "merchant_gift_box", "merchant_antique_gear")
# ⛔ §九 作废的两个旧占位（必须不存在于产物里；见上面的 `_bgbook9_bad` 段）
_BG9_RETIRED_ENTRIES = ("merchant", "antiques")
for _retired in _RETIRED_ENTRIES:
    for _side in (_ZH_BOOK, _EN_BOOK):
        if (_side / "entries" / ("%s.json" % _retired)).exists():
            _bgbook_bad("bgbook8-old-entries-gone",
                        "§八 作废的条目 %s 又回到了产物里（%s）：它的 42 页已由「装备的强化」的"
                        "每族 7 页锻造取代" % (_retired, _side.name))
for _retired in _BG9_RETIRED_ENTRIES:
    for _side in (_ZH_BOOK, _EN_BOOK):
        if (_side / "entries" / ("%s.json" % _retired)).exists():
            _bgbook_bad("bgbook9-old-placeholders-gone",
                        "§九 作废的「商人与古董」旧占位 %s 又回到了产物里（%s）：它的 11 页已由"
                        "「关于易金商人 / 礼品盒 / 古董器具」3 章 20 页取代" % (_retired, _side.name))
# ⛔ bg-fix3 §三：两个骨架条目（「贵金的材料链」/「升级锻造模板」）的负向断言 + 生成器侧守卫。
for _retired in _BGFIX3_RETIRED_ENTRIES:
    for _side in (_ZH_BOOK, _EN_BOOK):
        if (_side / "entries" / ("%s.json" % _retired)).exists():
            _bgbook_bad("bgfix3-old-skeleton-gone",
                        "bg-fix3 §三 作废的骨架条目 %s 又回到了产物里（%s）：作者 2026-10-07 要求把"
                        "「贵金的材料链 / 升级锻造模版」两部分删去" % (_retired, _side.name))
_bgbook_gen_src = Path(__file__).resolve().parent / "generate_handbook_data.py"
_bgbook_gen_txt = _bgbook_gen_src.read_text(encoding="utf-8")
# ⚠ **负向字符串检查必须跑在"去注释"的源码上**（mcmod_experience ex/03 §3.15 ①）：
#   本轮实测 —— 生成器里留了一句"旧结构原文保留"的注释
#   `# [entry_metal_tour, entry_upgrade_templates, entry_golden_feast]`，
#   它让"ENTRIES 列表里不许出现 entry_metal_tour,"这条**负向**断言**假红**。
#   生成器是 Python ⇒ 工程通用的 strip_comments() 只认 `//` 与 `/* */`，这里要**另剥一次 `#`**。
_bgbook_gen_code = re.sub(r"#[^\n]*", "", _bgbook_gen_txt)
# 生成器里这两个函数必须**原样保留**（内容不凭空消失）且仍在 `RETIRED_ENTRIES` 里；
# 同时 `ENTRIES = [ … ]` 那一段里**不许**再引用它们（否则下次重跑又把它们写回产物）。
#
# ⚠ **本轮扰动实测抓到的一条假绿**（记在 docs/1.6-规格.md §二十二）：第一版这里是
#   `src.split("ENTRIES = [")[1].split("]")[0]` —— 而 `RETIRED_ENTRIES = [` **也含**
#   子串 `ENTRIES = [`，于是 `[1]` 取到的是 **RETIRED 那个列表**、`ENTRIES` 块根本没被检查：
#   扰动 P15（把 `entry_metal_tour,` 塞回 ENTRIES）**仍然绿**。
#   ⇒ 改法：**行锚定**地切出 ENTRIES 块（`^ENTRIES = \[$` … `^\]$`），并配反空转守护。
_bgbook_entries_match = re.search(r"(?ms)^ENTRIES = \[$(.*?)^\]\s*$", _bgbook_gen_code)
if _bgbook_entries_match is None:
    _bgbook_bad("bgfix3-generator-retired",
                "生成器里切不出 `ENTRIES = [ … ]` 块（行锚定正则失配 ⇒ 下面的负向断言会空转）")
_bgbook_entries_block = _bgbook_entries_match.group(1) if _bgbook_entries_match else ""
if _bgbook_entries_match is not None and "entry_golden_feast" not in _bgbook_entries_block:
    _bgbook_bad("bgfix3-generator-retired",
                "切出来的 ENTRIES 块里没有 entry_golden_feast（切错块了 ⇒ 反空转守护）")
_bgbook_retired_match = re.search(r"(?ms)^RETIRED_ENTRIES = \[(.*?)^\]", _bgbook_gen_code)
_bgbook_retired_block = _bgbook_retired_match.group(1) if _bgbook_retired_match else ""
for _retired in _BGFIX3_RETIRED_ENTRIES:
    if f"def entry_{_retired}(" not in _bgbook_gen_code:
        _bgbook_bad("bgfix3-generator-retired",
                    "生成器里 `entry_%s` 的构造函数被删掉了 —— 作废内容必须**原样保留**（不凭空消失）"
                    % _retired)
    if f"entry_{_retired}," in _bgbook_entries_block:
        _bgbook_bad("bgfix3-generator-retired",
                    "生成器的 `ENTRIES` 列表里又出现了 `entry_%s`（下次重跑会把它写回产物）" % _retired)
    if f"entry_{_retired}" not in _bgbook_retired_block:
        _bgbook_bad("bgfix3-generator-retired",
                    "生成器的 `RETIRED_ENTRIES` 里没有 `entry_%s`（作废条目失去唯一的留档入口）" % _retired)
_missing_skeleton = [n for n in _SKELETON_ENTRIES if n not in _entries_now]
if _missing_skeleton:
    _bgbook_bad("bgbook-entry-count",
                "第一轮的骨架条目被删掉了（§八 只作废 %s、§九 只作废 %s）：%s"
                % (list(_RETIRED_ENTRIES), list(_BG9_RETIRED_ENTRIES), _missing_skeleton))
if len(_entries_now) != (len(_SKELETON_ENTRIES) + len(_BG2_ENTRY_NAMES)
                         + len(_BG8_ENTRY_NAMES) + len(_BG9_ENTRY_NAMES)):
    _bgbook_bad("bgbook-entry-count",
                "条目数应为 %d（骨架 %d + §六 章节 3 + §八 强化 9 + §九 商人与古董 3；"
                "bg-fix3 §三 又作废 2 条骨架条目），实际 %d"
                % (len(_SKELETON_ENTRIES) + len(_BG2_ENTRY_NAMES)
                   + len(_BG8_ENTRY_NAMES) + len(_BG9_ENTRY_NAMES),
                   len(_SKELETON_ENTRIES), len(_entries_now)))
_valid_categories = {"bettergold:%s" % c[0] for c in _EXPECT_CATEGORIES}
_total_pages = 0
_recipe_refs = set()
for _name, _e in sorted(_entries_now.items()):
    if _e.get("category") not in _valid_categories:
        _bgbook_bad("bgbook-entry-category",
                    "条目 %s 的 category 不是四个类别之一：%s" % (_name, _e.get("category")))
    if not str(_e.get("name", "")).startswith("bettergold.handbook.entry."):
        _bgbook_bad("bgbook-entry-name", "条目 %s 的 name 不是 bettergold.handbook.entry.* 语言键" % _name)
    for _pg in _e.get("pages", []):
        _total_pages += 1
        if _pg.get("type") not in _KNOWN_PAGE_TYPES:
            _bgbook_bad("bgbook-page-type",
                        "条目 %s 用了未知页面类型 %s" % (_name, _pg.get("type")))
        for _overflow in ("recipe3", "recipe4", "recipes"):
            if _overflow in _pg:
                _bgbook_bad("bgbook-page-recipe-cap",
                            "条目 %s 的页里出现 %s：Patchouli 的配方页**只有** recipe / recipe2 两个槽"
                            "（写别的键不会报错，只会被忽略 ⇒ 配方静默不显示）" % (_name, _overflow))
        for _rk in ("recipe", "recipe2"):
            if _rk in _pg:
                _recipe_refs.add(_pg[_rk])
if _total_pages < 143:
    # ⚠ **bg-fix3 §三 改变了这里的期望值**：作废 `metal_tour`(9) + `upgrade_templates`(5) = −14 页
    #   ⇒ 157 → **143**。旧阈值（≥60，消息里写「§八 之后应 ≥ 148 页」）原文留在这里作历史留档。
    _bgbook_bad("bgbook-anti-vacuum",
                "手册总页数只有 %d（bg-fix3 §三 之后应为 143 页 = 157 − 14；数据树被清空会命中这条）"
                % _total_pages)
_missing_recipe_files = sorted(
    r for r in _recipe_refs
    if not (_DATA / "bettergold" / "recipe" / (r.split(":", 1)[1] + ".json")).is_file())
if _missing_recipe_files:
    _bgbook_bad("bgbook-recipe-refs",
                "手册引用了**不存在的配方**（死链，游戏里那一页会空掉）：%s" % _missing_recipe_files[:5])
if not _recipe_refs:
    _bgbook_bad("bgbook-recipe-refs", "反空转守护：一页配方页都没解析到（配方引用检查会假绿）")

# ---------- 8) 语言键：书 JSON 里引用的每一个键都必须在 zh_cn / en_us 里存在 ----------
_LANG_KEY_RE = re.compile(r"^bettergold\.handbook\.[a-z0-9_.]+$")


def _collect_lang_keys(node, out):
    if isinstance(node, dict):
        for _k, _v in node.items():
            if _k in ("name", "description", "landing_text", "subtitle", "title", "text") \
                    and isinstance(_v, str) and _LANG_KEY_RE.match(_v):
                out.add(_v)
            _collect_lang_keys(_v, out)
    elif isinstance(node, list):
        for _v in node:
            _collect_lang_keys(_v, out)


_referenced_keys = set()
for _root_for_keys in (_BOOK_ROOT, _ASSET_ROOT):
    for _p in sorted(_root_for_keys.rglob("*.json")) if _root_for_keys.is_dir() else []:
        _collect_lang_keys(json.loads(_p.read_text(encoding="utf-8")), _referenced_keys)
_referenced_keys.add("item.bettergold.%s" % _HANDBOOK_ITEM)
for _key in sorted(_referenced_keys):
    if _key not in zh or _key not in en:
        _bgbook_bad("bgbook-lang-keys", "手册引用的语言键缺中文或英文：%s" % _key)
if len(_referenced_keys) < 25:
    _bgbook_bad("bgbook-lang-anti-vacuum",
                "从书 JSON 里解析到的手册语言键只有 %d 个（解析失败 / 键被删会命中这条）"
                % len(_referenced_keys))

# ---------- 9) 图标 + 模型（本轮唯一新增的贴图，按作者素材哈希钉住） ----------
import hashlib  # noqa: E402  （只在本节用到，放这里免得动文件头）

_icon_path = _RES / "assets" / "bettergold" / "textures" / "item" / ("%s.png" % _HANDBOOK_ITEM)
if not _icon_path.is_file():
    _bgbook_bad("bgbook-icon", "缺手册物品图标 textures/item/%s.png" % _HANDBOOK_ITEM)
else:
    _icon_bytes = _icon_path.read_bytes()
    _iw = int.from_bytes(_icon_bytes[16:20], "big")
    _ih = int.from_bytes(_icon_bytes[20:24], "big")
    _isha = hashlib.sha256(_icon_bytes).hexdigest()
    if (_iw, _ih) != (16, 16):
        _bgbook_bad("bgbook-icon", "手册图标不是 16×16（实际 %d x %d）" % (_iw, _ih))
    if _isha != "c4d9e4e7e91bca9dfbcb8886db4578b345e913cbe47e74a0779494d7787bee24":
        _bgbook_bad("bgbook-icon",
                    "手册图标哈希与作者给的素材不一致（这是本轮唯一被新增的贴图，钉哈希防替换）")
_model_path = _RES / "assets" / "bettergold" / "models" / "item" / ("%s.json" % _HANDBOOK_ITEM)
if not _model_path.is_file():
    _bgbook_bad("bgbook-model", "缺手册物品模型 models/item/%s.json（客户端会紫黑格）" % _HANDBOOK_ITEM)
else:
    _model = json.loads(_model_path.read_text(encoding="utf-8"))
    if _model.get("parent") != "minecraft:item/generated" or "overrides" in _model:
        _bgbook_bad("bgbook-model",
                    "手册模型不是 item/generated 单层（纯功能物品不许有 override / 谓词）")

# ---------- 10) 文档侧：口径必须落档（含"每页 2 个配方是 Patchouli 的结构上限"） ----------
_spec16_book = (REPO / "docs" / "1.6-规格.md").read_text(encoding="utf-8")
for _needle, _tag, _why in (
        ("bg-book", "bgbook-doc", "docs/1.6-规格.md 里没有 bg-book 节"),
        ("Patchouli 的结构上限", "bgbook-doc-page-cap",
         "docs/1.6-规格.md 没写明「每页 2 个配方是 Patchouli 的结构上限」"),
        ("故意不加 localRuntime", "bgbook-doc-compile-only",
         "docs/1.6-规格.md 没写明「故意不加 localRuntime」这条口径")):
    if _needle not in _spec16_book:
        _bgbook_bad(_tag, _why)

# ==================== bg-book §六 追加轮（2026-10-05）：「炼金的起步」三章逐页补全 ====================
#
# 形状由**读 Patchouli jar 的字节码**决定（不是猜的）：
#   * `PageDoubleRecipe extends PageWithText` ⇒ **配方页自带 `text` 字段**（图标 + 文案 + 配方同页可表达）；
#   * `PageSpotlight#render` 的图标是 `stacks[(ticksInBook / 20) % stacks.length]`
#     ⇒ 列表里的图标**每 20 tick 换一个** —— 这正是作者说的「随排版顺序**不断变化**」；
#   * 需求 §6.2 第 1 行的图标列写「（无）」、而图标本身（"中上角：炼金珍材盒"）写在**右侧**列
#     ⇒ 文档的**一行 = 书的一屏 = 跨页** ⇒ 落地 = 一行两个 Patchouli 页
#     （左页 = 图标 + 逐字文案；右页 = 配方，或右图标 + 右文案）。
#     章1 2 行 → 4 页；章2 9 行 → 18 页；章3 5 行 → 10 页；合计 **32 页 = 文档说的 16「跨页」**。
#     （另一种读法「一行 = 1 个 Patchouli 页」= 16 页，无法表达"左侧文案 + 左上角图标"；两种都写在规格 §12。）
bgbook2_problems: list[str] = []


def _bgbook2_bad(tag: str, msg: str) -> None:
    bgbook2_problems.append("%s [%s]" % (msg, tag))


_BG2_REQ_DOC = (REPO.parent / "mod_experience" / "开工需求"
                / "20261004-1733_bg-book_patchouli-handbook.md")
# ⚠ **冻结快照**（bg-append 追加轮，2026-10-05）：上一轮的本关卡直接读 `开工需求\` 那份**活页**，
#   而那份文档**会被设计会话继续追加/就地修改** ⇒ 作者 20:40 一改 §6.3 的表，本关卡就**红**了
#   （实测：解析出 24 段而不是 22 段，于是「8/22 段缺失」）。
#   ⇒ 逐字文案的期望值必须来自**仓库内、随代码一起受版本控制**的冻结快照：
#     `tools/asset-generator/bgappend-requirements-snapshot/`（内容取自 2026-10-05 20:40 的版本）。
#   口径写在 docs/1.6-规格.md §17.3：**外部活页只作输入，期望值一律以快照为准**。
_BG2_SNAPSHOT_DIR = (REPO / "tools" / "asset-generator" / "bgappend-requirements-snapshot")
_BG2_SNAPSHOT = _BG2_SNAPSHOT_DIR / "bg-book-6.1-6.3.md"
# 章 → (封面图标, sortnum, 页型序列)。页型序列就是"一行 = 左页 + 右页"的机器形态。
#   ⚠ **bg-book §八（2026-10-06）**：章3 的**第 1 页（汇总页）已被作者删除**（§8.1）⇒
#     它的页型序列由 5 行（10 页）变成 **4 行（8 页）**，三章合计 32 → **30**。
#     旧期望 `["patchouli:spotlight", "patchouli:spotlight"] * 5` 与 `!= 32` **原文保留在注释里**（未删）。
_BG2_CHAPTERS = {
    "auxiliary_materials": ("mixed_crystal_pile", 2,
                            ["patchouli:spotlight", "patchouli:crafting"] * 2),
    "core_materials": ("golden_cowrie", 3,
                       ["patchouli:text", "patchouli:spotlight"]
                       + ["patchouli:spotlight", "patchouli:crafting"] * 8),
    "golden_knowledge": ("sturdygold_ingot", 4,
                         ["patchouli:spotlight", "patchouli:spotlight"] * 4),
}
_bg2_pages_total = 0
_bg2_recipe_refs = set()
_bg2_item_refs = set()
for _cname, (_cicon, _csort, _cseq) in _BG2_CHAPTERS.items():
    _zh_p = _ZH_BOOK / "entries" / ("%s.json" % _cname)
    _en_p = _EN_BOOK / "entries" / ("%s.json" % _cname)
    if not _zh_p.is_file() or not _en_p.is_file():
        _bgbook2_bad("bgbook2-chapter-entries", "章节条目缺文件（zh/en 各需一份）：%s" % _cname)
        continue
    _zh_e = json.loads(_zh_p.read_text(encoding="utf-8"))
    _en_e = json.loads(_en_p.read_text(encoding="utf-8"))
    _want_icon = "bettergold:%s" % _cicon
    if _zh_e.get("icon") != _want_icon or _en_e.get("icon") != _want_icon:
        _bgbook2_bad("bgbook2-chapter-entries",
                     "%s 的章节封面图标不是 %s（实际 %r / %r）"
                     % (_cname, _want_icon, _zh_e.get("icon"), _en_e.get("icon")))
    if _zh_e.get("sortnum") != _csort or _en_e.get("sortnum") != _csort:
        _bgbook2_bad("bgbook2-chapter-entries", "%s 的 sortnum 不是 %d" % (_cname, _csort))
    if _zh_e.get("category") != "bettergold:alchemy_start":
        _bgbook2_bad("bgbook2-chapter-entries",
                     "%s 不挂在「炼金的起步」类别下（实际 %r）" % (_cname, _zh_e.get("category")))
    if _zh_e.get("name") != "bettergold.handbook.entry.%s" % _cname:
        _bgbook2_bad("bgbook2-chapter-entries",
                     "%s 的 name 不是 bettergold.handbook.entry.%s" % (_cname, _cname))
    if _zh_e.get("pages") != _en_e.get("pages"):
        _bgbook2_bad("bgbook2-chapter-entries", "%s 的 zh/en 页列表不一致（结构必须双端相同）" % _cname)
    _seq_now = [str(_p.get("type")) for _p in _zh_e.get("pages", [])]
    if _seq_now != _cseq:
        _bgbook2_bad("bgbook2-chapter-pages",
                     "%s 的页型序列不是「一行一跨页 = 左页 + 右页」：期望 %s，实际 %s"
                     % (_cname, _cseq, _seq_now))
    _bg2_pages_total += len(_seq_now)
    for _pg in _zh_e.get("pages", []):
        if _pg.get("type") not in _KNOWN_PAGE_TYPES:
            _bgbook2_bad("bgbook2-page-type", "%s 用了未知页面类型 %s" % (_cname, _pg.get("type")))
        for _overflow in ("recipe3", "recipe4", "recipes"):
            if _overflow in _pg:
                _bgbook2_bad("bgbook2-recipe-cap",
                             "%s 的页里出现 %s（Patchouli 只有 recipe / recipe2 两个槽，多写的键静默被忽略）"
                             % (_cname, _overflow))
        for _rk in ("recipe", "recipe2"):
            if _rk in _pg:
                _bg2_recipe_refs.add(_pg[_rk])
        _it = _pg.get("item")
        for _one in ([_it] if isinstance(_it, str) else (_it or [])):
            _bg2_item_refs.add(str(_one))
if _bg2_pages_total != 30:
    _bgbook2_bad("bgbook2-chapter-pages",
                 "三章合计应是 30 个 Patchouli 页（= 文档 2+9+4 = 15 行 × 2；"
                 "§八 删掉了章3 的第 1 页 ⇒ 原期望 32 已作废），实际 %d" % _bg2_pages_total)
_bg2_missing_recipes = sorted(
    _r for _r in _bg2_recipe_refs
    if not (_DATA / "bettergold" / "recipe" / (_r.split(":", 1)[1] + ".json")).is_file())
if _bg2_missing_recipes:
    _bgbook2_bad("bgbook2-recipe-refs",
                 "三章引用了不存在的配方（死链，游戏里那一页会空掉）：%s" % _bg2_missing_recipes[:5])
if len(_bg2_recipe_refs) < 13:
    _bgbook2_bad("bgbook2-recipe-refs",
                 "三章只解析到 %d 个配方引用（应 13；反空转守护）" % len(_bg2_recipe_refs))
_bg2_missing_items = sorted(
    _i for _i in _bg2_item_refs
    if ("item.bettergold.%s" % _i.split(":", 1)[1]) not in zh
    and ("block.bettergold.%s" % _i.split(":", 1)[1]) not in zh)
if _bg2_missing_items:
    _bgbook2_bad("bgbook2-item-refs",
                 "三章的图标引用了不存在的物品/方块（死链）：%s" % _bg2_missing_items[:5])
if len(_bg2_item_refs) != 19:
    # ⚠ **§八 改变了这里的期望值**：章3 的第 1 页（两张轮换图标表 = 8 锭 + 8 模板）已删除 ⇒
    #   唯一图标引用从 35 降到 **19**（章1 2 + 章2 9 + 章3 8）。旧阈值 35 原文保留在这里（未删）。
    #   改成"恰好 19"比阈值更硬：任何"顺手加一个图标"都会当场红。
    _bgbook2_bad("bgbook2-item-refs",
                 "三章解析到 %d 个图标引用（应恰好 19；§八 删掉章3 第 1 页后由 35 降下来）"
                 % len(_bg2_item_refs))

# 逐字文案：**期望值来自冻结快照**（不是本脚本自己的表 —— 否则就是 §4 第 42 条那种空转）
if not _BG2_SNAPSHOT.is_file():
    _bgbook2_bad("bgbook2-texts-verbatim", "读不到冻结快照（逐字文案的期望值来源）：%s" % _BG2_SNAPSHOT)
    _bg2_texts = []
else:
    _bg2_lines = _BG2_SNAPSHOT.read_text(encoding="utf-8").split("\n")

    def _bg2_rows(marker: str) -> list[list[str]]:
        out, active = [], False
        for _ln in _bg2_lines:
            if _ln.startswith(marker):
                active = True
                continue
            if active and _ln.startswith("### "):
                break
            if not (active and _ln.startswith("|")) or "|---" in _ln:
                continue
            _cells = [c for c in _ln.split("|")][1:-1]
            # ⚠ bg-append 追加轮修的两处**解析根因**（上一轮这里是 `"页" not in _cells[0]`）：
            #   ① 表头判据不能用"第一格含『页』"——§6.3 的表头单元格是「页 | 左（含左上角图标 +
            #      逐字文案） | 右（...）」但它**含 `<br>` 与表格竖线**，被切坏之后 "页" 不在第一格
            #      ⇒ 表头被当成数据行、后续每一行整体错位一列，文案数量从 22 变成 24（实测红）；
            #   ② 第 1 行**没有第二列**（§6.3 第 1 行是跨两列的汇总行，`left` 就是文案本身）
            #      ⇒ `_r[1]` 直接 IndexError。改成"行号列必须是纯数字"+"按列号取、越界给空串"。
            if not re.fullmatch(r"\d+", _cells[0].strip().replace("*", "")):
                continue
            out.append(_cells)
        return out

    def _bg2_cell(_row: list[str], _idx: int) -> str:
        return _row[_idx] if _idx < len(_row) else ""

    def _bg2_clean(_cell: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*", r"\1", _cell.strip()).strip()

    _bg2_texts = [_bg2_clean(_bg2_cell(_r, 1)) for _r in _bg2_rows("### 6.1")]
    for _i, _r in enumerate(_bg2_rows("### 6.2"), start=1):
        _bg2_texts.append(_bg2_clean(_bg2_cell(_r, 2)))
        if _i == 1:
            _bg2_texts.append(_bg2_clean(
                re.sub(r"^\s*\*\*右侧正文\*\*：", "", _bg2_cell(_r, 3).split("<br>")[-1])))
    for _r in _bg2_rows("### 6.3"):
        # ⚠ §七 之后的形状：章3 第 1 行是**汇总行** —— 左页只有一句正文（在单元格 1），
        #   **右页只有一张图标、没有正文**（单元格 2 的 "（随排版顺序变化）" 是图标说明，不是文案）。
        #   判据用**形状**（"图标：" 之后没有 `<br>` 文案段）而不是行号，免得以后行序一变就静默失准。
        #   若照旧把图标说明也当成正文，会多出 1 段并报「1 段缺失」（实测红过）。
        for _col in (1, 2):
            _body = _bg2_cell(_r, _col).split("<br>")[-1].strip()
            if _body.startswith("图标："):
                continue  # 该格只有图标说明、没有正文
            _bg2_texts.append(_bg2_clean(_body))
    # §6.3 第 1 行是**汇总行**（bg-book §七.1：作者要求删掉原来那两段长文案、只留一句）
    # ⇒ 它的文案在第 1 个单元格里，另外两个单元格只有图标说明（没有正文）。
    _bg2_texts = [_t for _t in _bg2_texts if _t]
    if len(_bg2_texts) != 21 or sum(len(_t) for _t in _bg2_texts) < 600:
        _bgbook2_bad("bgbook2-texts-verbatim",
                     "从冻结快照解析到 %d 段逐字文案 / 共 %d 字（应 21 段 = 2 + 9 + 1 + 9、"
                     "总字数 >= 600；反空转守护）"
                     % (len(_bg2_texts), sum(len(_t) for _t in _bg2_texts)))
    _zh_values = set(zh.values())
    _bg2_missing_texts = [_t for _t in _bg2_texts if _t not in _zh_values]
    if _bg2_missing_texts:
        _bgbook2_bad("bgbook2-texts-verbatim",
                     "冻结快照里的逐字文案没有原样出现在 zh_cn.json 里（%d/%d 段缺失，首条：%s）"
                     % (len(_bg2_missing_texts), len(_bg2_texts), _bg2_missing_texts[0][:40]))

# 语言键：24 条（3 个条目名 + 21 段文案/标题键）必须**中英双端都有**
#   ⚠ bg-append 追加轮：`knowledge_1_left` / `knowledge_1_right` **已被作者要求删除**
#     （§七.1「把那些东西都汇总起来」）⇒ 换成 `knowledge_1_summary`（整页只剩这一句）。
_bg2_suffixes = (["aux_1", "aux_2"]
                 + ["core_%d" % _i for _i in range(1, 10)] + ["core_1_right"]
                 + ["knowledge_1_summary"]
                 + ["knowledge_%d_%s" % (_i, _s) for _i in range(2, 6) for _s in ("left", "right")])
_bg2_keys = (["bettergold.handbook.entry.%s" % _c for _c in _BG2_CHAPTERS]
             + ["bettergold.handbook.page.%s" % _s for _s in _bg2_suffixes])
if len(_bg2_keys) != 24:
    _bgbook2_bad("bgbook2-lang-bilingual",
                 "章节语言键清单是 %d 条（应 24 = 3 + 21；反空转守护）" % len(_bg2_keys))
for _k in _bg2_keys:
    if _k not in zh or _k not in en:
        _bgbook2_bad("bgbook2-lang-bilingual", "章节语言键缺中文或英文：%s" % _k)

# 文档侧：§六 追加轮的形状 / 推断值 / 第 8 条结论必须落档
for _needle, _tag, _why in (
        ("1 行 = 1 跨页", "bgbook2-doc",
         "docs/1.6-规格.md 没写「§6 的一行 = 一个跨页 = 两个 Patchouli 页」这条形状"),
        ("bettergold:sturdygold_ingot", "bgbook2-doc",
         "docs/1.6-规格.md 没写章3 封面图标的推断值"),
        ("stopBeingAngry", "bgbook2-doc",
         "docs/1.6-规格.md 没写第 8 条的动作（stopBeingAngry）"),
        ("AngerLevel", "bgbook2-doc",
         "docs/1.6-规格.md 没写「AngerLevel 在 1.21.1 不存在」"),
        ("无击退", "bgbook2-doc",
         "docs/1.6-规格.md 没写幽咆金「并击退目标」与代码现状不符（核实项②）")):
    if _needle not in _spec16_book:
        _bgbook2_bad(_tag, _why)

# ==================== bg-fix（会话标记 bg-fix，2026-10-05）：1.6 的七条修正 ====================
#
# 每一条都带**稳定的 ASCII id**（`[bgfix-...]`），供扰动矩阵逐条自证（mcmod_experience §3.4）。
# 判据一律跑在**去注释**后的源码上（注释既能喂饱正向断言、也能误伤负向断言）。
bgfix_problems: list[str] = []


def _bgfix_bad(tag: str, msg: str) -> None:
    bgfix_problems.append("%s [%s]" % (msg, tag))


_bgfix_cfg = strip_comments((JAVA / "config" / "Config.java").read_text(encoding="utf-8"))
_bgfix_mev = strip_comments((JAVA / "material" / "MetalEvents.java").read_text(encoding="utf-8"))
_bgfix_mod = strip_comments((JAVA / "event" / "ModEvents.java").read_text(encoding="utf-8"))
_bgfix_mf = strip_comments((JAVA / "material" / "MetalFamily.java").read_text(encoding="utf-8"))
_bgfix_am = strip_comments((JAVA / "material" / "AllMetals.java").read_text(encoding="utf-8"))
_bgfix_fx = strip_comments((JAVA / "registry" / "AllEffects.java").read_text(encoding="utf-8"))
_bgfix_glm = strip_comments((JAVA / "registry" / "AllLootModifiers.java").read_text(encoding="utf-8"))
_bgfix_items = strip_comments((JAVA / "registry" / "AllItems.java").read_text(encoding="utf-8"))
_bgfix_book = strip_comments((JAVA / "patchouli" / "HandbookModule.java").read_text(encoding="utf-8"))

# ---------- 第 2 条 · buff 显示名 → 音咆（**只改显示名**） ----------
if zh.get("effect.bettergold.echo_roar") != "\u97f3\u5486":
    _bgfix_bad("bgfix-echo-name-zh",
               "zh_cn 的 effect.bettergold.echo_roar 不是「音咆」（实际 %r）"
               % zh.get("effect.bettergold.echo_roar"))
if en.get("effect.bettergold.echo_roar") != "Sonic Roar":
    _bgfix_bad("bgfix-echo-name-en",
               "en_us 的 effect.bettergold.echo_roar 不是 \"Sonic Roar\"（实际 %r）"
               % en.get("effect.bettergold.echo_roar"))
# 负向：**金属名**（幽咆金）相关语言键不许出现「音咆」（作者只改 buff 的显示名）
_echo_metal_keys = [k for k in zh if k.startswith("item.bettergold.echogold")
                    or k.startswith("block.bettergold.echogold")
                    or k.startswith("trim_material.bettergold.echogold")
                    or k.startswith("item.bettergold.smithing_template.echogold")]
if len(_echo_metal_keys) < 10:
    _bgfix_bad("bgfix-echo-metal-name-untouched",
               "幽咆金相关语言键只找到 %d 条（反空转守护：应 >= 10）" % len(_echo_metal_keys))
_bad_echo_metal = [k for k in _echo_metal_keys if "\u97f3\u5486" in str(zh.get(k))]
if _bad_echo_metal:
    _bgfix_bad("bgfix-echo-metal-name-untouched",
               "金属名（幽咆金）被顺手改成了音咆：%s" % _bad_echo_metal[:5])
if zh.get("item.bettergold.echogold_ingot") != "\u5e7d\u5486\u91d1\u952d":
    _bgfix_bad("bgfix-echo-metal-name-untouched",
               "item.bettergold.echogold_ingot 不再是「幽咆金锭」（金属名被改）")
if 'EFFECTS.register("echo_roar"' not in _bgfix_fx:
    _bgfix_bad("bgfix-echo-id-unchanged", "AllEffects 里的 echo_roar 注册 id 不见了（id 不许改）")

# ---------- 第 3 条 · 闪耀藤条判据收窄为「特殊金属」（除万坚金） ----------
if "isSpecialMetal()" not in _bgfix_glm:
    _bgfix_bad("bgfix-vine-special-metal", "闪耀藤条判据没有用 family.isSpecialMetal()（没收窄，万坚金仍会掉）")
else:
    _i_special = _bgfix_glm.find("isSpecialMetal()")
    _i_istool = _bgfix_glm.find("family.isTool(")
    if _i_istool < 0:
        _bgfix_bad("bgfix-vine-special-metal", "工具判据里找不到 family.isTool(（反空转守护）")
    elif _i_special > _i_istool:
        _bgfix_bad("bgfix-vine-special-metal", "isSpecialMetal() 落在 isTool( 之后 ⇒ 万坚金仍会掉藤条")
if "family != null && (family.isTool(" in _bgfix_glm:
    _bgfix_bad("bgfix-vine-old-broad",
               "仍留着旧口径 `family != null && (family.isTool(`（= 任意一族，万坚金会掉藤条）")
if 'STURDYGOLD_ID = "sturdygold"' not in _bgfix_mf:
    _bgfix_bad("bgfix-special-metal-predicate", "MetalFamily 里没有 STURDYGOLD_ID 常量")
if "public boolean isSpecialMetal()" not in _bgfix_mf:
    _bgfix_bad("bgfix-special-metal-predicate", "MetalFamily 里没有 isSpecialMetal()")
elif "!STURDYGOLD_ID.equals(this.id)" not in _bgfix_mf:
    _bgfix_bad("bgfix-special-metal-predicate",
               "isSpecialMetal() 的判据不是 !STURDYGOLD_ID.equals(this.id)")
_n_specs = _bgfix_am.count("new MetalFamily.Spec(")
if _n_specs != 8:
    _bgfix_bad("bgfix-special-metal-predicate",
               "AllMetals 里的 MetalFamily.Spec 不是 8 个（实际 %d；反空转守护）" % _n_specs)

# ---------- 第 4 条 · 紫颂樱花枝配方：1 个樱花树苗 → 恶魂之泪 ----------
_ccb_path = _DATA / "bettergold" / "recipe" / "chorus_cherry_branch.json"
if not _ccb_path.is_file():
    _bgfix_bad("bgfix-chorus-recipe", "缺 data/bettergold/recipe/chorus_cherry_branch.json")
else:
    _ccb = json.loads(_ccb_path.read_text(encoding="utf-8"))
    _ccb_ing = [str(i.get("item")) for i in _ccb.get("ingredients", [])]
    if _ccb.get("type") != "minecraft:crafting_shapeless":
        _bgfix_bad("bgfix-chorus-recipe", "樱花枝配方不是 crafting_shapeless（实际 %r）" % _ccb.get("type"))
    if _ccb_ing.count("minecraft:cherry_sapling") != 7 or _ccb_ing.count("minecraft:ghast_tear") != 1:
        _bgfix_bad("bgfix-chorus-recipe",
                   "樱花枝配方必须是 7 樱花树苗 + 1 恶魂之泪（实际 sapling=%d tear=%d）"
                   % (_ccb_ing.count("minecraft:cherry_sapling"),
                      _ccb_ing.count("minecraft:ghast_tear")))
    if _ccb_ing.count("minecraft:chorus_flower") != 1:
        _bgfix_bad("bgfix-chorus-recipe", "樱花枝配方里的紫颂花不是 1 个")
    if (_ccb.get("result") or {}).get("id") != "bettergold:chorus_cherry_branch":
        _bgfix_bad("bgfix-chorus-recipe",
                   "樱花枝配方的产物被动了（应是 bettergold:chorus_cherry_branch）")

# ---------- 第 5 条 · 万坚金武器工具击杀骷髅类 => 80% 掉金骨粉 ----------
if 'ITEMS.register("golden_bone_meal"' not in _bgfix_items:
    _bgfix_bad("bgfix-skeleton-drop",
               "金骨粉物品不存在（bettergold:golden_bone_meal 没注册）—— 第 5 条依赖它，不许自己造物品")
for _needle, _why in (
        ("SKELETON_GOLDEN_BONE_MEAL_CHANCE = 0.8F", "击杀掉率不是 80%"),
        ("AbstractSkeleton", "「骷髅类型」判据没走 AbstractSkeleton"),
        ("GOLDEN_BONE_MEAL.get()", "掉落物不是金骨粉"),
        ("event.getDrops().add(", "没有把金骨粉加进击杀掉落"),
        ("isSturdygoldAttackWeapon(", "武器判据没有复用万坚金那一处（又写了一份）")):
    if _needle not in _bgfix_mev:
        _bgfix_bad("bgfix-skeleton-drop", "MetalEvents 里 %s 不在位（%s）" % (_needle, _why))
_i_skel = _bgfix_mev.find("AbstractSkeleton")
_i_high = _bgfix_mev.find("AllEffects.HIGH_BURN) && !entity.isOnFire()")
if _i_skel < 0 or _i_high < 0:
    _bgfix_bad("bgfix-skeleton-precedes-highburn", "找不到骨架/高燃标记（反空转守护）")
elif _i_skel > _i_high:
    _bgfix_bad("bgfix-skeleton-precedes-highburn",
               "骷髅掉落在「高燃掉熟食」早退之后 ⇒ 永不触发（静默失效）")
_ld_files = []
for _p in JAVA.rglob("*.java"):
    if "LivingDropsEvent" in strip_comments(_p.read_text(encoding="utf-8")):
        _ld_files.append(_p.name)
_ld_files = sorted(_ld_files)
# 白名单：本仓**本来就有两个**击杀掉落处理点（ModEvents = 猪灵掉金钱贝；MetalEvents = 高燃掉熟食）。
# bg-fix 第 5 条只许**加进 MetalEvents.onLivingDrops**，不许再添第三个事件（陷阱 #5）。
if _ld_files != ["MetalEvents.java", "ModEvents.java"]:
    _bgfix_bad("bgfix-skeleton-single-event",
               "LivingDropsEvent 的处理点落在 %s（白名单 = MetalEvents.java + ModEvents.java；不许再添第三个）"
               % _ld_files)
if _bgfix_mev.count("public static void onLivingDrops(") != 1:
    _bgfix_bad("bgfix-skeleton-single-event", "MetalEvents 里 onLivingDrops 处理点不是恰好 1 个")
if "public static boolean isSturdygoldAttackWeapon(" not in _bgfix_mod:
    _bgfix_bad("bgfix-skeleton-weapon-judgement",
               "ModEvents.isSturdygoldAttackWeapon 不是 public ⇒ 武器判据被写了两份")

# ---------- 第 6 条 · 高燃 / 沉淀：曲线整体后移一级 ----------
# ⚠ **本条的期望值已被 bg-fix2 第 5 条（2026-10-06）取代**（原文按"不删"规矩留在这里）：
#    旧期望 = `return Math.max(0, amplifier);`（1 级 0 点 / 2 级 1 点）
#    新期望 = `return Math.max(1, amplifier + 1);`（1 级 1 点 / 2 级 2 点 / 3 级 3 点）—— 见本文件末尾的
#    `bg-fix2` 段（`[bgfix2-shifted-damage-level-eq-damage]`）。这里改成断言"**不是**旧口径"，
#    免得同一条事实在两处各写一份期望值（§2.4）。
if "public static float shiftedDamage(int amplifier)" not in _bgfix_fx:
    _bgfix_bad("bgfix-shifted-damage-impl", "AllEffects 里没有 shiftedDamage(int)（公式不是唯一实现）")
elif "return Math.max(0, amplifier);" in _bgfix_fx:
    _bgfix_bad("bgfix-shifted-damage-impl",
               "shiftedDamage 还是旧口径 `max(0, amplifier)`（0/1/2）—— 已被 bg-fix2 第 5 条取代")
if _bgfix_fx.count("shiftedDamage(amplifier)") != 2:
    _bgfix_bad("bgfix-shifted-damage-used",
               "shiftedDamage(amplifier) 出现 %d 次（高燃 + 沉淀必须各一次）"
               % _bgfix_fx.count("shiftedDamage(amplifier)"))
if "amplifier + 2" in _bgfix_fx:
    _bgfix_bad("bgfix-shifted-damage-used", "AllEffects 里还留着旧口径 `amplifier + 2`")
if _bgfix_fx.count("duration % 20 == 0") != 5:
    _bgfix_bad("bgfix-shifted-damage-frequency",
               "每秒结算判据的条数不是 5（频率被改动了；反空转守护）")
if "float level = (amplifier + 1) * MetalFamily.ECHO_ROAR_DAMAGE_PER_LEVEL;" not in _bgfix_mev:
    _bgfix_bad("bgfix-parasite-echo-unchanged",
               "音咆的「伤害 = 等级」公式被动了（本条只许改高燃 / 沉淀）")

# ---------- 第 7 条 · 16 条配置项 = 唯一真源 ----------
_BGFIX_FAMILIES = ["flamegold", "voodoogold", "thundergold", "indigoseagold",
                   "illusiongold", "thornsgold", "echogold", "sturdygold"]
_BGFIX_WEAPON_KEYS = {f: f + "WeaponBuffChance" for f in _BGFIX_FAMILIES}
_BGFIX_WEAPON_KEYS["sturdygold"] = "sturdygoldWeaponAbilityChance"
_BGFIX_ARMOR_KEYS = {f: f + "ArmorBuffChance" for f in _BGFIX_FAMILIES if f != "sturdygold"}
_BGFIX_MULT_KEY = "sturdygoldArmorAbilityIntervalMultiplier"
_EXISTING_CONFIG_KEYS = ["logDirtBlock", "magicNumber", "magicNumberIntroduction", "items",
                         "goldLootMode", "goldLootItems", "voodooExtractRatio",
                         "voodooFlatPerLevel", "thunderSoundMode"]
_cfg_keys = re.findall(r'\.define(?:InRange|ListAllowEmpty)?\(\s*"([^"]+)"', _bgfix_cfg)
if len(_cfg_keys) != 25:
    _bgfix_bad("bgfix-config-16-keys",
               "Config.java 的键总数不是 25（既有 9 + 新增 16；实际 %d: %s）" % (len(_cfg_keys), _cfg_keys))
for _k in _EXISTING_CONFIG_KEYS:
    if _k not in _cfg_keys:
        _bgfix_bad("bgfix-config-existing-keys",
                   "既有配置键 %s 不见了/被改名（配置键名是存档红线）" % _k)
for _f, _k in _BGFIX_WEAPON_KEYS.items():
    if _k not in _cfg_keys:
        _bgfix_bad("bgfix-config-16-keys", "缺武器侧配置键 %s（%s）" % (_k, _f))
for _f, _k in _BGFIX_ARMOR_KEYS.items():
    if _k not in _cfg_keys:
        _bgfix_bad("bgfix-config-16-keys", "缺盔甲侧配置键 %s（%s）" % (_k, _f))
if _BGFIX_MULT_KEY not in _cfg_keys:
    _bgfix_bad("bgfix-config-16-keys", "缺万坚金间隔系数键 %s" % _BGFIX_MULT_KEY)
_BGFIX_DEFAULTS = [
    ("flamegoldWeaponBuffChance", 1.0), ("voodoogoldWeaponBuffChance", 1.0),
    ("thundergoldWeaponBuffChance", 1.0), ("indigoseagoldWeaponBuffChance", 1.0),
    ("illusiongoldWeaponBuffChance", 0.16), ("thornsgoldWeaponBuffChance", 1.0),
    ("echogoldWeaponBuffChance", 1.0), ("sturdygoldWeaponAbilityChance", 1.0),
    ("flamegoldArmorBuffChance", 0.25), ("voodoogoldArmorBuffChance", 0.25),
    ("thundergoldArmorBuffChance", 0.25), ("indigoseagoldArmorBuffChance", 0.25),
    ("illusiongoldArmorBuffChance", 0.04), ("thornsgoldArmorBuffChance", 0.25),
    ("echogoldArmorBuffChance", 0.25), ("sturdygoldArmorAbilityIntervalMultiplier", 1.0),
]
for _k, _d in _BGFIX_DEFAULTS:
    _m = re.search(r'\.defineInRange\(\s*"%s"\s*,\s*([0-9.]+)D' % re.escape(_k), _bgfix_cfg)
    if not _m:
        _bgfix_bad("bgfix-config-defaults", "找不到键 %s 的 defineInRange 默认值" % _k)
    elif abs(float(_m.group(1)) - _d) > 1e-9:
        _bgfix_bad("bgfix-config-defaults", "键 %s 的默认值不是 %s（实际 %s）" % (_k, _d, _m.group(1)))
_cfg_cc = method_body(_bgfix_mev, "private static float counterChance(")
if "armorBuffChance(family.id)" not in _cfg_cc:
    _bgfix_bad("bgfix-config-single-source", "counterChance 没从配置读（armorBuffChance(family.id) 不在位）")
if "0.25F" in _cfg_cc or "sootheReflectPerPiece" in _cfg_cc:
    _bgfix_bad("bgfix-config-single-source",
               "counterChance 里还留着一份硬编码概率（0.25F / sootheReflectPerPiece）")
_cfg_afe = method_body(_bgfix_mev, "public static void applyFamilyWeaponEffect(")
if "weaponBuffChance(family.id)" not in _cfg_afe:
    _bgfix_bad("bgfix-config-single-source",
               "applyFamilyWeaponEffect 没从配置读（weaponBuffChance(family.id) 不在位）")
if "nextFloat() < family.sootheOnAttackChance" in _cfg_afe:
    _bgfix_bad("bgfix-config-single-source",
               "幻惑金仍在用 sootheOnAttackChance 掷骰 = 第二处硬编码概率（会掷两次 ⇒ 0.16x0.16）")
if _cfg_afe.count("sootheOnAttackChance") != 1:
    _bgfix_bad("bgfix-config-single-source",
               "applyFamilyWeaponEffect 里 sootheOnAttackChance 出现 %d 次（只许当一次存在位判据）"
               % _cfg_afe.count("sootheOnAttackChance"))
if "weaponChance <= 0.0F" not in _cfg_afe:
    _bgfix_bad("bgfix-config-zero-never", "武器侧配置 0 时没有 return（「改 0 ⇒ 永不触发」不成立）")
_cfg_abs = method_body(_bgfix_mev, "public static void onAbsorptionTick(")
if "absorptionInterval(family.absorptionIntervalTicks)" not in _cfg_abs:
    _bgfix_bad("bgfix-config-single-source",
               "万坚金间隔没从配置读（absorptionInterval(family.absorptionIntervalTicks) 不在位）")
if "% family.absorptionIntervalTicks" in _cfg_abs:
    _bgfix_bad("bgfix-config-single-source",
               "onAbsorptionTick 仍直接用族常量取模（配置系数没生效）")
if "weaponBuffChance(com.hjmmd_8.bettergold.material.AllMetals.STURDYGOLD.id)" not in _bgfix_mod:
    _bgfix_bad("bgfix-config-single-source",
               "万坚金武器「能力概率」没有走同一个配置入口（Config.weaponBuffChance）")
if "abilityChance <= 0.0F" not in _bgfix_mod:
    _bgfix_bad("bgfix-config-zero-never", "ModEvents 里武器侧配置 0 时没有 return")
for _fn, _tag in (("public static float weaponBuffChance(String familyId)", "weaponBuffChance"),
                  ("public static float armorBuffChance(String familyId)", "armorBuffChance")):
    _b = method_body(_bgfix_cfg, _fn)
    if _b.count('case "') != 8:
        _bgfix_bad("bgfix-config-case-count",
                   "%s 的 case 数不是 8（实际 %d）" % (_tag, _b.count('case "')))
for _k in list(_BGFIX_WEAPON_KEYS.values()) + list(_BGFIX_ARMOR_KEYS.values()) + [_BGFIX_MULT_KEY]:
    if not re.fullmatch(r"[a-z][A-Za-z0-9]*", _k):
        _bgfix_bad("bgfix-config-key-ascii", "配置键不是英文 camelCase：%s" % _k)

# ---------- 第 1 条 · 炼金术学员手册：1 书 + 1 金锭、无序合成（+ patchouli 条件） ----------
_bgfix_hb = _DATA / "bettergold" / "recipe" / "alchemy_student_handbook.json"
if not _bgfix_hb.is_file():
    _bgfix_bad("bgfix-handbook-recipe",
               "缺 data/bettergold/recipe/alchemy_student_handbook.json（第 1 条没落地）")
else:
    _hb = json.loads(_bgfix_hb.read_text(encoding="utf-8"))
    if _hb.get("type") != "minecraft:crafting_shapeless":
        _bgfix_bad("bgfix-handbook-recipe", "手册配方不是无序合成（实际 %r）" % _hb.get("type"))
    _hb_ing = [str(i.get("item")) for i in _hb.get("ingredients", [])]
    if sorted(_hb_ing) != ["minecraft:book", "minecraft:gold_ingot"]:
        _bgfix_bad("bgfix-handbook-recipe",
                   "手册配方材料不是「1 书 + 1 金锭」（实际 %s）" % sorted(_hb_ing))
    if (_hb.get("result") or {}).get("id") != "bettergold:alchemy_student_handbook":
        _bgfix_bad("bgfix-handbook-recipe", "手册配方产物不是 bettergold:alchemy_student_handbook")
    if int((_hb.get("result") or {}).get("count", 0)) != 1:
        _bgfix_bad("bgfix-handbook-recipe", "手册配方产出数量不是 1")
    _hb_cond = json.dumps(_hb.get("neoforge:conditions", []), ensure_ascii=False)
    if "neoforge:mod_loaded" not in _hb_cond or "patchouli" not in _hb_cond:
        _bgfix_bad("bgfix-handbook-conditional",
                   "手册配方没有 neoforge:mod_loaded(patchouli) 条件"
                   "（没装 Patchouli 时手册物品不注册 ⇒ 配方解析失败刷错误）")
if '"alchemy_student_handbook"' not in _bgfix_book:
    _bgfix_bad("bgfix-handbook-item-id", "HandbookModule.ITEM_PATH 不再是 alchemy_student_handbook")

# ---------- 文档：新口径必须落档（docs/1.6-规格.md 的 bg-fix 追加节） ----------
_bgfix_spec = (REPO / "docs" / "1.6-规格.md").read_text(encoding="utf-8")
for _needle, _tag, _why in (
        ("bg-fix", "bgfix-doc", "docs/1.6-规格.md 里没有 bg-fix 追加节"),
        ("\u97f3\u5486", "bgfix-doc-echo", "docs/1.6-规格.md 没写「音咆」这个新显示名"),
        ("isSpecialMetal", "bgfix-doc-vine", "docs/1.6-规格.md 没写藤条收窄到 isSpecialMetal"),
        ("ghast_tear", "bgfix-doc-chorus", "docs/1.6-规格.md 没写樱花枝配方换成恶魂之泪"),
        ("golden_bone_meal", "bgfix-doc-skeleton", "docs/1.6-规格.md 没写金骨粉掉落"),
        ("shiftedDamage", "bgfix-doc-curve", "docs/1.6-规格.md 没写高燃/沉淀的新公式"),
        ("sturdygoldArmorAbilityIntervalMultiplier", "bgfix-doc-config",
         "docs/1.6-规格.md 没写 16 条配置项")):
    if _needle not in _bgfix_spec:
        _bgfix_bad(_tag, _why)

# ---------- §七 第 8 条 · 幻惑金建材：对玩家发起敌意的中立生物 ⇒（踩踏 / 贴近）瞬间变被动 ----------
if "contactPacifyNeutral" not in _bgfix_mf:
    _bgfix_bad("bgfix-pacify-flag", "MetalFamily 里没有 contactPacifyNeutral（第 8 条的族旗标）")
if "public boolean contactPacifyNeutral = false;" not in _bgfix_mf:
    _bgfix_bad("bgfix-pacify-flag", "Spec 里没有 contactPacifyNeutral 的默认字段")
if "public Spec contactPacifyNeutral()" not in _bgfix_mf:
    _bgfix_bad("bgfix-pacify-flag", "Spec 里没有 contactPacifyNeutral() 归位方法")
_n_pacify_calls = _bgfix_am.count(".contactPacifyNeutral()")
if _n_pacify_calls != 1:
    _bgfix_bad("bgfix-pacify-flag",
               "AllMetals 里 .contactPacifyNeutral() 出现 %d 次（应恰好 1 次 = 幻惑金）" % _n_pacify_calls)
_i_ill = _bgfix_am.find('new MetalFamily.Spec("illusiongold"')
_i_pac = _bgfix_am.find(".contactPacifyNeutral()")
_i_next_spec = _bgfix_am.find("new MetalFamily.Spec(", _i_ill + 1)
if _i_ill < 0:
    _bgfix_bad("bgfix-pacify-flag", "AllMetals 里找不到 illusiongold 的 Spec（反空转守护）")
elif _i_pac < _i_ill or (_i_next_spec > 0 and _i_pac > _i_next_spec):
    _bgfix_bad("bgfix-pacify-flag", "contactPacifyNeutral() 不在幻惑金那一份 Spec 里")

_scan_body = method_body(_bgfix_mev, "private static void scanContact(")
_apply_body = method_body(_bgfix_mev, "public static void applyContact(")
_break_body = method_body(_bgfix_mev, "public static void onBreakBlock(")
_use_body = method_body(_bgfix_mev, "public static void onRightClickBlock(")
for _body, _what in ((_scan_body, "scanContact"), (_apply_body, "applyContact"),
                     (_break_body, "onBreakBlock"), (_use_body, "onRightClickBlock")):
    if not _body:
        _bgfix_bad("bgfix-pacify-step-only", "取不到方法体：%s（反空转守护）" % _what)
if "pacifyHostileNeutrals(" not in _scan_body:
    _bgfix_bad("bgfix-pacify-step-only",
               "scanContact（踩踏 / 贴近）里没有调用 pacifyHostileNeutrals ⇒ 第 8 条不会触发")
for _body, _what in ((_apply_body, "applyContact"), (_break_body, "onBreakBlock"),
                     (_use_body, "onRightClickBlock")):
    if "pacifyHostileNeutrals(" in _body:
        _bgfix_bad("bgfix-pacify-step-only",
                   "%s 也调了 pacifyHostileNeutrals ⇒ 破坏 / 右键也会触发（作者只要踩踏 / 贴近）" % _what)

_pac_body = method_body(_bgfix_mev, "private static boolean pacifyHostileNeutrals(")
_pred_body = method_body(_bgfix_mev, "private static boolean isHostileNeutralTowardsPlayer(")
if not _pac_body:
    _bgfix_bad("bgfix-pacify-predicate", "找不到 pacifyHostileNeutrals 方法体（反空转守护）")
if not _pred_body:
    _bgfix_bad("bgfix-pacify-predicate", "找不到 isHostileNeutralTowardsPlayer 方法体（反空转守护）")
for _needle, _why in (("stopBeingAngry()", "动作不是原版 NeutralMob#stopBeingAngry()"),
                      ("isClientSide()", "缺客户端早退"),
                      ("isAlive()", "缺存活判定")):
    if _needle not in _pac_body:
        _bgfix_bad("bgfix-pacify-predicate", "%s：方法体里没有 %s" % (_why, _needle))
for _needle, _why in (("instanceof net.minecraft.world.entity.NeutralMob", "判据不是 NeutralMob"),
                      ("getTarget() instanceof net.minecraft.world.entity.player.Player",
                       "缺「当前攻击目标是玩家」那一支"),
                      ("isAngry()", "缺怒气计时判据（isAngry）"),
                      ("isAngryAt(player)", "缺「怒气指向在场玩家」那一支"),
                      ("level().players()", "没有遍历在场玩家")):
    if _needle not in _pred_body:
        _bgfix_bad("bgfix-pacify-predicate", "%s：判据里没有 %s" % (_why, _needle))
if "getBrain()" in _pac_body or "ATTACK_TARGET" in _pac_body:
    _bgfix_bad("bgfix-pacify-no-brain",
               "顺手加了 brain 记忆清理 —— 1.21.1 的 6 个 NeutralMob 实现类（蜜蜂/铁傀儡/北极熊/狼/"
               "末影人/僵尸猪灵）没有一个是脑驱动的（脑驱动的 Piglin/Hoglin/Zoglin/Breeze/Warden "
               "都不实现 NeutralMob）")
for _needle, _tag, _why in (
        ("stopBeingAngry", "bgfix-pacify-doc", "docs/1.6-规格.md 没写第 8 条的动作"),
        ("踩踏 / 贴近", "bgfix-pacify-doc", "docs/1.6-规格.md 没写「只在踩踏 / 贴近触发」")):
    if _needle not in _bgfix_spec:
        _bgfix_bad(_tag, _why)

# ===========================================================================
# bg-final（1.6 收尾轮，2026-10-05）：三件已裁定的收尾
#   ① 幽咆金建材的声波**真的击退**（手册原文就写着 knock the target back）
#   ② 102 条成就英文值**真英译**（断言在 validate_advancements.py 的 [bgfinal-adv-lang-*]）
#   ③ 高燃 **1 级不点燃**（端到端 0/1/2，与沉淀对齐）
# 每条断言都带稳定 ASCII id（[bgfinal-...]），判据一律跑在**去注释**后的源码上。
# ===========================================================================
# ==================== bg-append 追加轮（2026-10-05）：三份需求各自的新增节 ====================
#
# 覆盖范围（逐条对应需求文档的**追加轮**，不是为了凑数）：
#   * `bg-book` §七  —— 手册章3 的七处修正（汇总页 / 锭表 / 模板标题 / 建筑方块 / 制成 / 固定顺序）；
#   * `bg-fix` §八  —— 幽咆金声波音效（建材 + 音咆两处都要）+ 16 条配置项的**汉化**；
#   * `bg-fix` §九  —— 金玫瑰丛：cutout 渲染层 + 两条配方；
#   * `bg-ach` §七  —— **由 `validate_advancements.py` 守**（[bgach-craft-to-have*] /
#                       [bgach-no-knife-in-gear] / [bgach-recipe-crafted-scope]，
#                       那边本来就跑在去注释源码 + 成就产物上，重复一份没有意义）。
# 每条断言都带**稳定的 ASCII id**（`[bgappend-*]`），供扰动矩阵逐条自证（mcmod_experience §3.4）。
bgappend_problems: list[str] = []


def _bgappend_bad(tag: str, msg: str) -> None:
    bgappend_problems.append("%s [%s]" % (msg, tag))


def _bgappend_jload(_p):
    try:
        return json.loads(_p.read_text(encoding="utf-8"))
    except Exception as _e:  # noqa: BLE001 —— 解析失败也要变成一条"问题"，不能炸脚本
        _bgappend_bad("bgappend-json", "读不了 / 解析失败：%s（%s）" % (_p, _e))
        return {}


# ---------- A. bg-book §七：手册章3 的七处修正 ----------
_BG3_ZH = _ZH_BOOK / "entries" / "golden_knowledge.json"
_BG3_EN = _EN_BOOK / "entries" / "golden_knowledge.json"
# 章3 第 1 行（汇总行）的两张图标表 + 两个标题（作者 §七 第 2/3/4 条）
_BG3_INGOT_IDS = ["bettergold:flamegold_ingot", "bettergold:sturdygold_ingot",
                  "bettergold:thornsgold_ingot", "bettergold:echogold_ingot",
                  "bettergold:indigoseagold_ingot", "bettergold:voodoogold_ingot",
                  "bettergold:thundergold_ingot", "bettergold:illusiongold_ingot"]
_BG3_TEMPLATE_IDS = ["bettergold:%s_upgrade_template" % _s for _s in
                     ("flamegold", "sturdygold", "thornsgold", "echogold",
                      "indigoseagold", "voodoogold", "thundergold", "illusiongold")]
_BG3_INGOT_TITLE = "\u5404\u79cd\u5404\u6837\u7684\"\u8d35\u91d1\"\u952d"          # 各种各样的"贵金"锭
_BG3_TEMPLATE_TITLE = "\"\u8d35\u91d1\"\u88c5\u5907\u7684\u5347\u7ea7\u953b\u9020\u6a21\u7248"  # "贵金"装备的升级锻造模版
_BG3_BUILDING_ORDER = ["_block", "_bricks", "_pillar", "_bricks_stairs", "_bricks_slab",
                       "_bricks_wall", "_bars", "_door", "_trapdoor", "_chain", "_lantern"]
_BG3_OLD_TEXT_KEYS = ["bettergold.handbook.page.knowledge_1_left",
                      "bettergold.handbook.page.knowledge_1_right"]
_BG3_ZH_E = _bgappend_jload(_BG3_ZH)
_BG3_EN_E = _bgappend_jload(_BG3_EN)
_BG3_PAGES = _BG3_ZH_E.get("pages") or []
# ⚠ **bg-book §八（2026-10-06）改变了本节的期望**：章3 的第 1 页（§七 改成"汇总页"的那一跨页）
#   已被 §8.1 **整页删除** ⇒ 页数 10 → **8**。
#   旧期望（原文保留，未删）与它下面那**六条**断言（`bgappend-book-k3-p1-ingots` /
#   `-p1-ingot-title` / `-p1-summary` ×2 / `-p1-templates` / `-p1-template-title`）**已随该页作废**：
#   它们守的两张轮换图标表（八族锭 / 八张升级模板）与两个标题现在**不该再出现在任何一页上**，
#   改由 `[bgbook8-k3-p1-gone]`（bgbook8 段）用**负向**判据守住；上面 `_BG3_INGOT_IDS` /
#   `_BG3_TEMPLATE_IDS` / `_BG3_INGOT_TITLE` / `_BG3_TEMPLATE_TITLE` 四个常量**原样保留**，
#   正是给那条负向断言当"不该再出现"的清单用。
#   旧代码形状（留档）：`if len(_BG3_PAGES) != 10: ... else: _p0, _p1 = _BG3_PAGES[0], _BG3_PAGES[1]`
#   + 六条 `_bgappend_bad("bgappend-book-k3-p1-*", ...)`。
if len(_BG3_PAGES) != 8:
    _bgappend_bad("bgappend-book-k3-pages",
                  "章3（「贵金」的知识）的 Patchouli 页数不是 8（4 行 × 2；§八 删掉了第 1 页，"
                  "旧期望 10 已作废；实际 %d）—— 反空转守护" % len(_BG3_PAGES))
else:
    # §七.1：原来那两段长文案**不许再被任何一页引用**，也不许再出现在语言值里
    #   （键**留在 lang 里作历史留档**是允许的 —— 见该键注释；被引用/被复用才是回退）
    _bg3_refs = set()
    for _pg in _BG3_PAGES:
        if isinstance(_pg.get("text"), str):
            _bg3_refs.add(_pg["text"])
    _bg3_still = sorted(k for k in _BG3_OLD_TEXT_KEYS if k in _bg3_refs)
    if _bg3_still:
        _bgappend_bad("bgappend-book-k3-old-text-gone",
                      "§七.1 要求删掉的两段长文案又被页面引用了：%s" % _bg3_still)
    _bg3_old_values = [zh.get(k) for k in _BG3_OLD_TEXT_KEYS if zh.get(k)]
    for _v in _bg3_old_values:
        if _v in set(zh.values()) - {_v}:
            _bgappend_bad("bgappend-book-k3-old-text-gone",
                          "§七.1 删掉的那两段长文案又被复制到别的语言键里了：%s…" % _v[:30])
    # §七.5/§七.6：全部手册文案里不许再有「作为的建筑方块」
    _bg3_bad_phrase = sorted(k for k, v in zh.items()
                             if k.startswith("bettergold.handbook.") and "作为的建筑方块" in str(v))
    if _bg3_bad_phrase:
        _bgappend_bad("bgappend-book-building-blocks",
                      "手册文案里还有「作为的建筑方块」（§七.6 要求全换成「制成的建筑方块」）：%s"
                      % _bg3_bad_phrase[:5])
    # 负向：幻惑金那句"瞬间变被动形态"已被 bg-fix §8.1 作废 ⇒ 手册里**不得**再出现
    _bg3_passive = sorted(k for k, v in zh.items()
                          if k.startswith("bettergold.handbook.") and "被动形态" in str(v))
    if _bg3_passive:
        _bgappend_bad("bgappend-book-no-pacify-text",
                      "手册里还留着「瞬间变为被动形态」（bg-fix §8.1 已整条作废）：%s" % _bg3_passive)
    if _BG3_ZH_E.get("pages") != _BG3_EN_E.get("pages"):
        _bgappend_bad("bgappend-book-k3-bilingual",
                      "章3 的 zh/en 页列表不一致（结构必须双端相同）")

# §七.7：建筑方块图标的**固定顺序**（锭块 → 砖块 → 柱 → 楼梯 → 台阶 → 砖墙 → 栏杆 → 门 → 活板门 → 链 → 灯笼）
#   落点 = 生成器的 `METAL_BLOCK_SUFFIX_ORDER`（真源）+ 从产物里反查 11 个方块 id 都真实存在。
_BGDOC_GEN = (REPO / "tools" / "asset-generator" / "generate_handbook_data.py")
if not _BGDOC_GEN.is_file():
    _bgappend_bad("bgappend-book-block-order", "读不到手册生成器：%s" % _BGDOC_GEN)
else:
    _bgdoc_src = _BGDOC_GEN.read_text(encoding="utf-8")
    _bgdoc_m = re.search(r"METAL_BLOCK_SUFFIX_ORDER\s*=\s*\[(.*?)\]", _bgdoc_src, re.S)
    if not _bgdoc_m:
        _bgappend_bad("bgappend-book-block-order",
                      "生成器里没有 METAL_BLOCK_SUFFIX_ORDER（§七.7 的固定顺序没有落成常量）")
    else:
        _bgdoc_order = re.findall(r'"([^"]+)"', _bgdoc_m.group(1))
        if _bgdoc_order != _BG3_BUILDING_ORDER:
            _bgappend_bad("bgappend-book-block-order",
                          "建筑方块图标顺序不是 §七.7 的固定顺序：%s" % _bgdoc_order)
        if len(_bgdoc_order) != 11:
            _bgappend_bad("bgappend-book-block-order",
                          "建筑方块的形态数不是 11（实际 %d）—— 反空转守护" % len(_bgdoc_order))
        _bgdoc_missing = sorted("bettergold:sturdygold" + _sfx for _sfx in _bgdoc_order
                                if ("block.bettergold.sturdygold" + _sfx) not in zh)
        if _bgdoc_missing:
            _bgappend_bad("bgappend-book-block-order",
                          "§七.7 点名的形态里有语言文件里不存在的方块：%s" % _bgdoc_missing)

# ---------- B. bg-fix §八.3：幽咆金的「监守者声波音效」（**两处都要**） ----------
if _bgfix_mev.count("playSonicBoomSound(") != 3:
    _bgappend_bad("bgappend-sonic-sound-sites",
                  "playSonicBoomSound 的出现次数不是 3（1 处定义 + 建材 + 音咆；实际 %d）"
                  % _bgfix_mev.count("playSonicBoomSound("))
for _needle, _tag, _why in (
        ("SoundEvents.WARDEN_SONIC_BOOM", "bgappend-sonic-sound-id",
         "声波音效不是 SoundEvents.WARDEN_SONIC_BOOM（§8.5 #2 的推断值）"),
        ("SoundSource.HOSTILE", "bgappend-sonic-sound-source",
         "声波音效的 SoundSource 不是 HOSTILE（原版 Warden 用的就是它）")):
    if _needle not in _bgfix_mev:
        _bgappend_bad(_tag, _why)
# 音效必须**跟在节流之后**（防空放）：建材那条在 contactThrottled 分支之后、且只在真的挨打时响
_sonic_body = method_body(_bgfix_mev, "private static void sonicContact(")
if not _sonic_body:
    _bgappend_bad("bgappend-sonic-sound-throttled", "找不到 sonicContact 方法体（反空转守护）")
elif "playSonicBoomSound(" in _sonic_body and "contactThrottled(" not in _sonic_body:
    _bgappend_bad("bgappend-sonic-sound-throttled",
                  "sonicContact 里放音效却没有 contactThrottled（会每 tick 刷屏）")
_echo_body = method_body(_bgfix_mev, "public static void echoRoarTick(")
if not _echo_body:
    _bgappend_bad("bgappend-sonic-sound-throttled", "找不到 echoRoarTick 方法体（反空转守护）")
else:
    if "playSonicBoomSound(" not in _echo_body:
        _bgappend_bad("bgappend-sonic-sound-sites", "音咆 buff 每跳没有声波音效（§8.3 点名的第二处）")
    # ⚠ 判据用**守卫表达式**而不是变量名：`if (hitAny)` 被改成 `if (false)` 时调用点还在、
    #   关卡不能因此放过（扰动实测抓出来的：只查 "hitAny" 会漏掉这种"调用还在但永不执行"的改法）
    #
    # ⚠⚠ **本条期望值已被 bg-fix2 第 2 条（2026-10-06）取代**（旧期望 `if (hitAny)` 原文保留在上面这段注释里）：
    #    旧口径 = 只有 hurt 落地才响 ⇒ 创造模式玩家 hurt 恒 false ⇒ 站在幽咆金建材上永远听不到
    #    （作者实测复报）。新口径 = **音效与伤害解耦**：守卫变量改成 `sawVictim`（= 本次确实对着一个
    #    未被节流的候选受害者判定过），并且必须在 `victim.hurt(` **之前**置位。详见本文件末尾
    #    `bg-fix2` 段的 `[bgfix2-sonic-decoupled]` / `[bgfix2-sonic-decoupled-echo]`。
    if "if (sawVictim)" not in _echo_body:
        _bgappend_bad("bgappend-sonic-sound-throttled",
                      "echoRoarTick 里没有 `if (sawVictim)` 守卫"
                      "（旧判据 `hitAny` 已被 bg-fix2 第 2 条取代；现在要求"
                      "「本次确实对着候选受害者判定过」就响）")

# ---------- C. bg-fix §八.4：16 条配置项的**汉化**（`bettergold.configuration.<key>`） ----------
#   真源 = Config.java 里那 16 个键（上面 bg-fix 段已逐个核实过）；这里只查"界面中文有没有"。
_BGAPPEND_CFG_KEYS = sorted(set("bettergold.configuration." + _k for _k in
                                list(_BGFIX_WEAPON_KEYS.values())
                                + list(_BGFIX_ARMOR_KEYS.values()) + [_BGFIX_MULT_KEY]))
if len(_BGAPPEND_CFG_KEYS) != 16:
    _bgappend_bad("bgappend-config-i18n", "16 条配置键的清单不是 16 条 —— 反空转守护")
#   反空转的另一半：这些键**必须真的存在于 Config.java**（否则关卡的"清单"是自己编的）
_bgappend_cfg_missing = sorted(k.split(".", 2)[2] for k in _BGAPPEND_CFG_KEYS
                               if k.split(".", 2)[2] not in _cfg_keys)
if _bgappend_cfg_missing:
    _bgappend_bad("bgappend-config-i18n",
                  "本地化清单里有 Config.java 里不存在的键：%s" % _bgappend_cfg_missing)
_bgappend_i18n_missing = sorted(k for k in _BGAPPEND_CFG_KEYS if k not in zh or k not in en)
if _bgappend_i18n_missing:
    _bgappend_bad("bgappend-config-i18n",
                  "配置界面缺中文/英文显示名：%s" % _bgappend_i18n_missing)
#   中文侧必须是中文（不是把英文 key 抄一遍）；英文侧必须是英文
_BGAPPEND_CJK = re.compile(r"[\u4e00-\u9fff]")
_bgappend_not_cjk = sorted(k for k in _BGAPPEND_CFG_KEYS
                           if not _BGAPPEND_CJK.search(str(zh.get(k, ""))))
if _bgappend_not_cjk:
    _bgappend_bad("bgappend-config-i18n-zh",
                  "这些配置项的中文显示名里没有中日韩文字（只是抄了键名？）：%s" % _bgappend_not_cjk)
_bgappend_zh_in_en = sorted(k for k in _BGAPPEND_CFG_KEYS
                            if _BGAPPEND_CJK.search(str(en.get(k, ""))))
if _bgappend_zh_in_en:
    _bgappend_bad("bgappend-config-i18n-en",
                  "这些配置项的英文显示名里混进了中文：%s" % _bgappend_zh_in_en)

# ---------- E. 文档侧：本轮的**新口径必须落档**（docs/1.6-规格.md 的新节） ----------
#   这一条同时是"不许只改代码不写规格"的机器守卫（§7.1 的交付清单）。
for _needle, _tag, _why in (
        ("bg-append", "bgappend-doc", "docs/1.6-规格.md 里没有本轮的节（bg-append 追加轮）"),
        ("PageSpotlight", "bgappend-doc-spotlight",
         "docs/1.6-规格.md 没写「Patchouli 的 spotlight 页只有一个图标槽」这条结构事实（§七.3 的落法依据）"),
        ("METAL_BLOCK_SUFFIX_ORDER", "bgappend-doc-block-order",
         "docs/1.6-规格.md 没写建筑方块固定顺序的落点（§七.7）"),
        ("冻结快照", "bgappend-doc-snapshot",
         "docs/1.6-规格.md 没写「逐字文案的期望值改为仓库内冻结快照」这条口径（本轮解析根因的修法）")):
    if _needle not in _bgfix_spec:
        _bgappend_bad(_tag, _why)

# ---------- D. bg-fix §九：金玫瑰丛（cutout 渲染层 + 两条配方） ----------
#   §9.1 的根因 = 少一行 `setRenderLayer(...GOLDEN_ROSE_BUSH..., cutout)`；
#   §9.2 = 有序 3×3（玫瑰丛居中 + 8 金粒）；§9.3 = 无序 1 丛 → 2 黄染料。
_BGAPPEND_CLIENT = strip_comments((JAVA / "bettergoldClient.java").read_text(encoding="utf-8"))
if "setRenderLayer(AllBlocks.GOLDEN_ROSE_BUSH.get(), cutout)" not in _BGAPPEND_CLIENT:
    _bgappend_bad("bgappend-rose-render-layer",
                  "bettergoldClient 里没有给金玫瑰丛注册 cutout 渲染层（§9.1：黑边根因）")
#   负向对照：其余方块**不许**被这轮顺手改动（白名单行数不变 = 只有新增那 1 行）
#   计数口径：13 条显式注册（GOLD_* 5 + 金雕摆件 3 + 作物 3 + 门/活板门/栏杆/链里 GOLD_ 的那几条…
#   以**实测 17** 为准）+ 家族循环体里 4 条（lantern/door/trapdoor/bars）——本轮之前是 16。
if _BGAPPEND_CLIENT.count("ItemBlockRenderTypes.setRenderLayer(") != 17:
    _bgappend_bad("bgappend-rose-render-layer-scope",
                  "setRenderLayer 的调用点数不是 17（本轮新增 1 行后应为 17；改动越界了）"
                  "：实际 %d" % _BGAPPEND_CLIENT.count("ItemBlockRenderTypes.setRenderLayer("))
_rose_recipe = _DATA / "bettergold" / "recipe" / "golden_rose_bush.json"
if not _rose_recipe.is_file():
    _bgappend_bad("bgappend-rose-recipe", "缺金玫瑰丛的合成配方（§9.2）")
else:
    _rr = _bgappend_jload(_rose_recipe)
    if _rr.get("type") != "minecraft:crafting_shaped":
        _bgappend_bad("bgappend-rose-recipe", "金玫瑰丛的配方不是有序合成（§9.2 推断值：有序 3×3）")
    _pattern = _rr.get("pattern") or []
    _key = _rr.get("key") or {}
    if len(_pattern) != 3 or any(len(_row) != 3 for _row in _pattern):
        _bgappend_bad("bgappend-rose-recipe", "金玫瑰丛的图案不是 3×3：%r" % (_pattern,))
    else:
        _mid = _pattern[1][1]
        if _mid not in _key or _key[_mid].get("item") != "minecraft:rose_bush":
            _bgappend_bad("bgappend-rose-recipe", "3×3 的正中央不是原版玫瑰丛：%r" % (_pattern,))
        _ring = [c for r in _pattern for c in r if c != _mid]
        if len(_ring) != 8 or len(set(_ring)) != 1:
            _bgappend_bad("bgappend-rose-recipe", "外圈不是同一材料的 8 格：%r" % (_pattern,))
        elif _key.get(_ring[0], {}).get("item") != "minecraft:gold_nugget":
            _bgappend_bad("bgappend-rose-recipe",
                          "外圈材料不是金粒（§9.2）：%r" % (_key.get(_ring[0]),))
    if (_rr.get("result") or {}).get("id") != "bettergold:golden_rose_bush" \
            or (_rr.get("result") or {}).get("count") != 1:
        _bgappend_bad("bgappend-rose-recipe", "金玫瑰丛配方的产出不对：%r" % (_rr.get("result"),))
_rose_dye = _DATA / "bettergold" / "recipe" / "yellow_dye_from_golden_rose_bush.json"
if not _rose_dye.is_file():
    _bgappend_bad("bgappend-rose-dye", "缺「金玫瑰丛 → 黄色染料」的配方（§9.3）")
else:
    _rd = _bgappend_jload(_rose_dye)
    _rd_ings = [_i.get("item") for _i in (_rd.get("ingredients") or [])]
    if _rd.get("type") != "minecraft:crafting_shapeless" or _rd_ings != ["bettergold:golden_rose_bush"]:
        _bgappend_bad("bgappend-rose-dye",
                      "黄染料配方不是「无序 + 单个金玫瑰丛」：%r / %r" % (_rd.get("type"), _rd_ings))
    if (_rd.get("result") or {}).get("id") != "minecraft:yellow_dye" \
            or (_rd.get("result") or {}).get("count") != 2:
        _bgappend_bad("bgappend-rose-dye",
                      "黄染料产量不是 2（§9.3；⚠「染料 vs 燃料」是需求 §9.4 #2 的待确认项，"
                      "本轮按「染料」落地）：%r" % (_rd.get("result"),))

bgfinal_problems: list[str] = []


def _bgfinal_bad(tag: str, msg: str) -> None:
    bgfinal_problems.append("%s [%s]" % (msg, tag))


def _bgfinal_block(body: str, header: str) -> tuple[str, str]:
    """按花括号配平切出 `header` 那个块，返回 (块文本, 去掉该块之后的剩余文本)。

    找不到 header / 块不配平时返回 ("", body) —— 调用方必须把空块当成"反空转失败"。
    """
    i = body.find(header)
    if i < 0:
        return "", body
    j = body.find("{", i)
    if j < 0:
        return "", body
    depth = 0
    for k in range(j, len(body)):
        if body[k] == "{":
            depth += 1
        elif body[k] == "}":
            depth -= 1
            if depth == 0:
                return body[i:k + 1], body[:i] + body[k + 1:]
    return "", body


# ---------- ① 声波击退 ----------
_bgfinal_mev = _bgfix_mev          # MetalEvents（已去注释）
_bgfinal_mf = _bgfix_mf            # MetalFamily（已去注释）
_sonic_body = method_body(_bgfinal_mev, "private static void sonicContact(")
_kb_body = method_body(_bgfinal_mev, "private static void applyBlockSonicKnockback(")
if not _sonic_body:
    _bgfinal_bad("bgfinal-sonic-knockback-present",
                 "MetalEvents 里找不到 sonicContact 方法体（反空转守护）")
if not _kb_body:
    _bgfinal_bad("bgfinal-sonic-knockback-present",
                 "MetalEvents 里找不到 applyBlockSonicKnockback 方法体（反空转守护）")
if _sonic_body and _kb_body:
    # 正向：真的推了，且方向是「方块中心 → 受害者」
    for _needle, _why in (("pos.getCenter()", "没有拿方块中心当原点"),
                          ("applyBlockSonicKnockback(victim, center)", "没有调用那一处推"),
                          ("victim.hurt(", "没有伤害调用")):
        if _needle not in _sonic_body:
            _bgfinal_bad("bgfinal-sonic-knockback-present", "%s：sonicContact 里没有 %s"
                         % (_why, _needle))
    for _needle, _why in (("victim.push(", "没有走 Entity#push("),
                          ("subtract(blockCenter)", "方向不是「方块中心 → 受害者」"),
                          (".normalize()", "方向没有归一化"),
                          ("KNOCKBACK_RESISTANCE", "没乘 (1 - 击退抗性)"),
                          ("1.0D - resistance", "没乘 (1 - 击退抗性)")):
        if _needle not in _kb_body:
            _bgfinal_bad("bgfinal-sonic-knockback-present", "%s：applyBlockSonicKnockback 里没有 %s"
                         % (_why, _needle))
    # 只推一次 + 只在这一次结算里推（在节流之后、且 push 只出现一次）
    if _sonic_body.count("push(") != 0:
        _bgfinal_bad("bgfinal-sonic-knockback-once",
                     "sonicContact 里出现了行内 push(（推的落点必须在唯一那一处 helper 里）")
    if _kb_body.count("push(") != 1:
        _bgfinal_bad("bgfinal-sonic-knockback-once",
                     "applyBlockSonicKnockback 里 push( 出现 %d 次（期望恰好 1 次）"
                     % _kb_body.count("push("))
    _i_throttle = _sonic_body.find("contactThrottled(")
    _i_call = _sonic_body.find("applyBlockSonicKnockback(")
    _i_hurt = _sonic_body.find("victim.hurt(")
    if _i_throttle < 0 or _i_call < 0 or _i_call < _i_throttle:
        _bgfinal_bad("bgfinal-sonic-knockback-once",
                     "推的调用点不在 contactThrottled(...) 之后 -> 可能每 tick 都推")
    if _i_hurt < 0 or _i_call < _i_hurt:
        _bgfinal_bad("bgfinal-sonic-knockback-damage-gated",
                     "推的调用点不在 victim.hurt(...) 之后 -> 免疫 / 无敌帧差额为 0 时也会被推"
                     "（原版 SonicBoom.java:79-83 是 `if (target.hurt(...)) { push }`）")
    if "if (!victim.hurt(" not in _sonic_body:
        _bgfinal_bad("bgfinal-sonic-knockback-damage-gated",
                     "没有 `if (!victim.hurt(...)) { continue; }` 这道闸门")
    # 幅度：必须由「原版声波基准 × 伤害比」推出来，而不是凭空拍一个数
    _m_dmg = re.search(r"CONTACT_SONIC_DAMAGE\s*=\s*([0-9.]+)F", _bgfinal_mf)
    _m_ref = re.search(r"SONIC_BOOM_REFERENCE_DAMAGE\s*=\s*([0-9.]+)F", _bgfinal_mf)
    _m_h = re.search(r"SONIC_BOOM_KNOCKBACK_HORIZONTAL\s*=\s*([0-9.]+)D", _bgfinal_mf)
    _m_v = re.search(r"SONIC_BOOM_KNOCKBACK_VERTICAL\s*=\s*([0-9.]+)D", _bgfinal_mf)
    if not (_m_dmg and _m_ref and _m_h and _m_v):
        _bgfinal_bad("bgfinal-sonic-knockback-magnitude",
                     "MetalFamily 里找不到四个基准常量（反空转守护："
                     "CONTACT_SONIC_DAMAGE / SONIC_BOOM_REFERENCE_DAMAGE / "
                     "SONIC_BOOM_KNOCKBACK_HORIZONTAL / SONIC_BOOM_KNOCKBACK_VERTICAL）")
    else:
        _want_h = float(_m_h.group(1)) * (float(_m_dmg.group(1)) / float(_m_ref.group(1)))
        _want_v = float(_m_v.group(1)) * (float(_m_dmg.group(1)) / float(_m_ref.group(1)))
        if abs(_want_h - 0.75) > 1e-9 or abs(_want_v - 0.15) > 1e-9:
            _bgfinal_bad("bgfinal-sonic-knockback-magnitude",
                         "由原版基准 × 伤害比推出的击退强度 = %.4f / %.4f，期望 0.75 / 0.15"
                         "（2.5×3/10 与 0.5×3/10）" % (_want_h, _want_v))
        _deriv = _bgfinal_mf[_bgfinal_mf.find("CONTACT_SONIC_KNOCKBACK_HORIZONTAL ="):]
        _deriv = _deriv[: _deriv.find(";")]
        for _needle in ("SONIC_BOOM_KNOCKBACK_HORIZONTAL", "CONTACT_SONIC_DAMAGE",
                        "SONIC_BOOM_REFERENCE_DAMAGE"):
            if _needle not in _deriv:
                _bgfinal_bad("bgfinal-sonic-knockback-magnitude",
                             "水平击退常量不是由 %s 推出来的（变成了拍脑袋的魔数）" % _needle)
    # 范围边界：击退只服务幽咆金这一条，其余接触效果一个都没有
    _java_sources = list((JAVA).rglob("*.java"))
    # ⚠ 计数一律跑在**去注释**后的文本上，否则 javadoc 里写一句 {@link #applyBlockSonicKnockback}
    #   就会把这个桶多算一次（本轮实测：含注释 3 → 去注释 2）。
    _kb_files = sorted(str(p.relative_to(REPO)) for p in _java_sources
                       if "CONTACT_SONIC_KNOCKBACK_" in strip_comments(p.read_text(encoding="utf-8")))
    if len(_kb_files) != 2:
        _bgfinal_bad("bgfinal-sonic-knockback-single-site",
                     "引用 CONTACT_SONIC_KNOCKBACK_* 的文件 = %s（期望恰好 2 个：MetalFamily 定义 + "
                     "MetalEvents 使用）-> 别的接触效果被顺手加上击退了" % _kb_files)
    _helper_hits = sum(strip_comments(p.read_text(encoding="utf-8")).count("applyBlockSonicKnockback") - 1
                       for p in _java_sources
                       if "applyBlockSonicKnockback" in strip_comments(p.read_text(encoding="utf-8")))
    if _helper_hits != 1:
        _bgfinal_bad("bgfinal-sonic-knockback-single-site",
                     "applyBlockSonicKnockback 的调用点 = %d 个（期望恰好 1 个）" % _helper_hits)
    _contact_body = method_body(_bgfinal_mev, "public static void applyContact(")
    if not _contact_body:
        _bgfinal_bad("bgfinal-sonic-knockback-single-site",
                     "找不到 applyContact 方法体（反空转守护）")
    elif "push(" in _contact_body:
        _bgfinal_bad("bgfinal-sonic-knockback-single-site",
                     "applyContact 里出现了行内 push( -> 击退被写进了共用的接触入口")
    # 其余三条接触效果仍在（阴性对照：这一轮没把它们改坏）
    for _needle, _why in (("CACTUS_CONTACT_KEY", "树棘金建材的接触伤害没了"),
                          ("contactDamage(entity, family)", "靛海金建材的接触伤害没了"),
                          ("family.contactBenefit", "幻惑金建材的正面效果没了"),
                          ("family.contactFire", "烈燃金建材的点火没了")):
        if _needle not in _contact_body:
            _bgfinal_bad("bgfinal-sonic-knockback-families-untouched", "%s（缺 %s）" % (_why, _needle))
    if _bgfinal_mev.count("setRemainingFireTicks") != 1:
        _bgfinal_bad("bgfinal-sonic-knockback-families-untouched",
                     "MetalEvents 里 setRemainingFireTicks 出现 %d 次（烈燃金点火那条应当恰好 1 次）"
                     % _bgfinal_mev.count("setRemainingFireTicks"))

# ---------- ③ 高燃 1 级不点燃 ----------
_bgfinal_fx = _bgfix_fx            # AllEffects（已去注释）
_hb_class = method_body(_bgfinal_fx, 'EFFECTS.register("high_burn"')
_hb_body = method_body(_hb_class, "public boolean applyEffectTick(")
_sd_class = method_body(_bgfinal_fx, 'EFFECTS.register("sediment"')
_sd_body = method_body(_sd_class, "public boolean applyEffectTick(")
_shifted_body = method_body(_bgfinal_fx, "public static float shiftedDamage(")
if not _hb_body:
    _bgfinal_bad("bgfinal-highburn-body", "AllEffects 里找不到高燃的 applyEffectTick 方法体（反空转守护）")
if not _sd_body:
    _bgfinal_bad("bgfinal-highburn-body", "AllEffects 里找不到沉淀的 applyEffectTick 方法体（反空转守护）")
if not _shifted_body or "Math.max(0, amplifier)" in _shifted_body:
    _bgfinal_bad("bgfinal-highburn-body",
                 "shiftedDamage 还是 `Math.max(0, amplifier)`（1 级 = 0 点）—— 已被 bg-fix2 第 5 条取代，"
                 "现行应为 `Math.max(1, amplifier + 1)`（1 级 1 点）")
if _hb_body:
    _blk, _rest = _bgfinal_block(_hb_body, "if (damage > 0.0F)")
    if not _blk:
        _bgfinal_bad("bgfinal-highburn-zero-no-fire",
                     "高燃 applyEffectTick 里没有 `if (damage > 0.0F) {` 守卫块"
                     "（点数为 0 时必须既不 hurt 也不刷燃烧）")
    else:
        for _needle in ("entity.hurt(", "setRemainingFireTicks"):
            if _needle not in _blk:
                _bgfinal_bad("bgfinal-highburn-zero-no-fire", "守卫块里没有 %s" % _needle)
        for _needle, _why in (("setRemainingFireTicks", "1 级（0 点）仍会刷新燃烧计时 -> 原版每 20 tick 自补 1 点"),
                              (".hurt(", "1 级（0 点）仍会走一次 hurt（还会白占一次无敌帧）")):
            if _needle in _rest:
                _bgfinal_bad("bgfinal-highburn-zero-no-fire", "守卫块之外还有 %s：%s" % (_needle, _why))
    if "shiftedDamage(amplifier)" not in _hb_body:
        _bgfinal_bad("bgfinal-highburn-zero-no-fire",
                     "高燃没有用共用的 shiftedDamage(amplifier)（公式必须只有一处真源）")
    if _bgfinal_fx.count("setRemainingFireTicks") != 1:
        _bgfinal_bad("bgfinal-highburn-zero-no-fire",
                     "AllEffects 里 setRemainingFireTicks 出现 %d 次（高燃那一处应当恰好 1 次）"
                     % _bgfinal_fx.count("setRemainingFireTicks"))
    # 2 级及以上照旧点燃：守卫块里的 hurt 伤害必须还是那次结算的值
    if "damage" not in _hb_body:
        _bgfinal_bad("bgfinal-highburn-level2-still-burns", "高燃不再按 damage 结算（2 级及以上也不点燃了）")
if _sd_body and "setRemainingFireTicks" in _sd_body:
    _bgfinal_bad("bgfinal-highburn-sediment-untouched",
                 "沉淀的结算里出现了 setRemainingFireTicks（沉淀本来就不点燃，别顺手加）")
if _sd_body and "inWall()" not in _sd_body:
    _bgfinal_bad("bgfinal-highburn-sediment-untouched", "沉淀的伤害类型不再是 in_wall()")

# ---------- 文档侧：新口径必须落档（docs/1.6-规格.md） ----------
for _needle, _tag, _why in (
        ("bg-final", "bgfinal-doc", "docs/1.6-规格.md 里没有 bg-final 这一轮的节"),
        ("SonicBoom.java:79-83", "bgfinal-doc", "docs/1.6-规格.md 没写击退的源码依据"),
        ("0.75", "bgfinal-doc", "docs/1.6-规格.md 没写水平击退强度 0.75"),
        ("已选 (b)", "bgfinal-doc", "docs/1.6-规格.md 的 §11.6.2「★A 两条出路」没有就地标注已选 (b)"),
        ("1 级 0 / 2 级 1 / 3 级 2", "bgfinal-doc", "docs/1.6-规格.md 没写高燃的端到端 0/1/2 曲线")):
    if _needle not in _bgfix_spec:
        _bgfinal_bad(_tag, _why)

# ===========================================================================
# bg-fix2（会话标记 bg-fix2，2026-10-06）：六条「作者实测未生效」的复报
# ===========================================================================
# 每一条都带**稳定 ASCII id**（`[bgfix2-...]`），判据跑在**去注释**后的源码 / 已解析的 JSON 上。
#
# ⚠ 第 1 条（靛海金纹饰色卡）本轮**只取证、不改贴图**（红线：要改任何贴图先停下报告）。
#   本段只钉「四处嫌疑都是干净的」这类**修复前后都成立**的不变量；
#   「靛海金的色卡逐像素 == 原版 quartz」这条**现状取证**刻意**不**写成阻塞断言 ——
#   把"已知缺陷"写成契约，会在作者裁定恢复色卡时反过来拦住修复
#   （`mcmod_experience` §2.2 的「关卡把旧路径写成契约」教训）。它落在
#   `validate_trim_assets.py` 的审计输出与 `docs/1.6-规格.md` 的 bg-fix2 节里。
bgfix2_problems: list[str] = []


def _bgfix2_bad(tag: str, msg: str) -> None:
    bgfix2_problems.append("%s [%s]" % (msg, tag))


_TRIM_MATERIAL = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "trim_material"
_PALETTES = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "textures" / "trims" / "color_palettes"
_ADV = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "advancement"
_BGFIX2_TRIMS = ["sturdygold", "unwanted_antique", "flamegold", "voodoogold", "thundergold",
                 "indigoseagold", "illusiongold", "thornsgold", "echogold"]


def _png_ihdr(data: bytes):
    """只读 IHDR：返回 (width, height, bitdepth, colortype)，不是 PNG 返回 None。"""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    import struct
    pos = 8
    while pos + 8 <= len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        if typ == b"IHDR":
            w, h = struct.unpack(">II", data[pos + 8:pos + 16])
            return w, h, data[pos + 16], data[pos + 17]
        pos += 12 + ln
    return None


# ---------- 第 5 条 · 高燃 / 沉淀 = 「等级 = 点数」（1 级 1 点 / 2 级 2 点） ----------
_sd2_body = method_body(_bgfix_fx, "public static float shiftedDamage(")
if not _sd2_body:
    _bgfix2_bad("bgfix2-shifted-damage-level-eq-damage",
                "AllEffects 里找不到 shiftedDamage 方法体（反空转守护）")
else:
    if "Math.max(1, amplifier + 1)" not in _sd2_body:
        _bgfix2_bad("bgfix2-shifted-damage-level-eq-damage",
                    "shiftedDamage 不是 `Math.max(1, amplifier + 1)`"
                    "（= 等级 = 点数：1 级 1 点 / 2 级 2 点 / 3 级 3 点；与寄生同口径）")
    if "Math.max(0, amplifier)" in _sd2_body:
        _bgfix2_bad("bgfix2-shifted-damage-level-eq-damage",
                    "shiftedDamage 里还留着旧口径 `Math.max(0, amplifier)`")
    if _sd2_body.count("return ") != 1:
        _bgfix2_bad("bgfix2-shifted-damage-level-eq-damage",
                    "shiftedDamage 方法体里 return 不是恰好 1 处（公式不是唯一实现）")
if _bgfix_fx.count("shiftedDamage(amplifier)") != 2:
    _bgfix2_bad("bgfix2-shifted-damage-used-twice",
                "shiftedDamage(amplifier) 出现 %d 次，期望恰好 2（高燃 + 沉淀各一次；反空转守护）"
                % _bgfix_fx.count("shiftedDamage(amplifier)"))

_hb2_class = method_body(_bgfix_fx, 'EFFECTS.register("high_burn"')
_hb2_body = method_body(_hb2_class, "public boolean applyEffectTick(")
if not _hb2_body:
    _bgfix2_bad("bgfix2-highburn-level1-burns", "找不到高燃 applyEffectTick 方法体（反空转守护）")
else:
    _hb2_blk, _hb2_rest = _bgfinal_block(_hb2_body, "if (damage > 0.0F)")
    if not _hb2_blk:
        _bgfix2_bad("bgfix2-highburn-level1-burns",
                    "高燃里找不到 `if (damage > 0.0F) { ... }` 守卫块")
    else:
        for _n in ("entity.hurt(", "setRemainingFireTicks", "HIGH_BURN_FIRE_TICKS"):
            if _n not in _hb2_blk:
                _bgfix2_bad("bgfix2-highburn-level1-burns",
                            "守卫块里没有 %s（1 级必须既 hurt 又重新点燃）" % _n)
    # 负向：不许再出现"点数为 0 就提前 return / 不点燃"这类按旧曲线写死的分支
    for _n, _why in (("damage <= 0.0F", "又在按「点数为 0」提前收手"),
                     ("damage == 0.0F", "又在按「点数为 0」提前收手"),
                     ("<= 0) {", "又出现「点数 <= 0」的守卫")):
        if _n in _hb2_body:
            _bgfix2_bad("bgfix2-highburn-level1-burns", "%s：高燃里出现了 %s" % (_why, _n))
_sd2_body_sediment = method_body(_bgfix_fx, 'EFFECTS.register("sediment"')
_sd2_tick = method_body(_sd2_body_sediment, "public boolean applyEffectTick(")
if not _sd2_tick:
    _bgfix2_bad("bgfix2-sediment-level-eq-damage", "找不到沉淀 applyEffectTick 方法体（反空转守护）")
elif "shiftedDamage(amplifier)" not in _sd2_tick:
    _bgfix2_bad("bgfix2-sediment-level-eq-damage",
                "沉淀没有用共用的 shiftedDamage(amplifier)（两条曲线必须同一处真源）")

# ---------- 第 2 条 · 声波音效与伤害解耦（两处） ----------
_sonic2 = method_body(_bgfix_mev, "private static void sonicContact(")
if not _sonic2:
    _bgfix2_bad("bgfix2-sonic-decoupled", "找不到 sonicContact 方法体（反空转守护）")
else:
    _i_snd = _sonic2.find("playSonicBoomSound(")
    _i_hurt2 = _sonic2.find("victim.hurt(")
    if _i_snd < 0:
        _bgfix2_bad("bgfix2-sonic-decoupled", "sonicContact 里没有 playSonicBoomSound（建材那条没声）")
    elif _i_hurt2 >= 0 and _i_snd > _i_hurt2:
        _bgfix2_bad("bgfix2-sonic-decoupled",
                    "音效调用点在 `victim.hurt(` **之后** -> 又变成「伤害没落地就不响」"
                    "（创造模式玩家 hurt 恒 false，正是作者听不到的原因）")
    if "contactThrottled(" not in _sonic2:
        _bgfix2_bad("bgfix2-sonic-decoupled",
                    "sonicContact 里没有 contactThrottled（会每 tick 刷屏 = 空放）")
_echo2 = method_body(_bgfix_mev, "public static void echoRoarTick(")
if not _echo2:
    _bgfix2_bad("bgfix2-sonic-decoupled-echo", "找不到 echoRoarTick 方法体（反空转守护）")
else:
    if "playSonicBoomSound(" not in _echo2:
        _bgfix2_bad("bgfix2-sonic-decoupled-echo", "音咆 buff 每跳没有声波音效（第二处）")
    if "if (sawVictim)" not in _echo2:
        _bgfix2_bad("bgfix2-sonic-decoupled-echo",
                    "echoRoarTick 的守卫不是 `if (sawVictim)`（音效又被挂到 hurt 的返回值上）")
    if "if (hitAny)" in _echo2:
        _bgfix2_bad("bgfix2-sonic-decoupled-echo", "旧的 `if (hitAny)` 守卫还在（口径没换干净）")
    _i_set = _echo2.find("sawVictim = true;")
    _i_hurt3 = _echo2.find("victim.hurt(")
    if _i_set < 0:
        _bgfix2_bad("bgfix2-sonic-decoupled-echo", "没有 `sawVictim = true;`（反空转守护）")
    elif _i_hurt3 >= 0 and _i_set > _i_hurt3:
        _bgfix2_bad("bgfix2-sonic-decoupled-echo",
                    "`sawVictim = true;` 在 victim.hurt( 之后 -> 又变成只有伤害落地才响")
    if "contactThrottled(" not in _echo2:
        _bgfix2_bad("bgfix2-sonic-decoupled-echo", "echoRoarTick 里没有节流（会每 tick 刷屏）")

# ---------- 第 4 条 · 金骨粉「攻击就掉 + 挤掉 80% 条目（礼品金票豁免）」 ----------
if _bgfix_mod.count("SKELETON_SQUEEZE_RATIO") < 2:
    _bgfix2_bad("bgfix2-skeleton-squeeze-ratio",
                "SKELETON_SQUEEZE_RATIO 出现次数 < 2（定义 + 使用；反空转守护）")
if "SKELETON_SQUEEZE_RATIO = 0.8F" not in _bgfix_mod:
    _bgfix2_bad("bgfix2-skeleton-squeeze-ratio", "挤掉比例不是 0.8F（作者要的「百分之 80」）")
_income_body = method_body(_bgfix_mod, "public static void onLivingIncomingDamage(")
if not _income_body:
    _bgfix2_bad("bgfix2-skeleton-attack-squeeze",
                "找不到 onLivingIncomingDamage 方法体（反空转守护）")
else:
    for _n, _why in (("AbstractSkeleton", "攻击那条没有「骷髅类」判据"),
                     ("rollGoldLootAgainstSkeleton(", "攻击那条没有走「挤掉 80% 条目」的掷骰")):
        if _n not in _income_body:
            _bgfix2_bad("bgfix2-skeleton-attack-squeeze", "%s（缺 %s）" % (_why, _n))
    # 顺序：骷髅判据必须在真正 addFreshEntity 之前（否则挤掉白算）
    _i_skel = _income_body.find("AbstractSkeleton")
    _i_add = _income_body.find("addFreshEntity(")
    if _i_skel < 0 or _i_add < 0 or _i_skel > _i_add:
        _bgfix2_bad("bgfix2-skeleton-attack-squeeze", "骷髅判据不在掉落之前（顺序错）")
_squeeze_body = method_body(_bgfix_mod, "private static Item rollGoldLootAgainstSkeleton(")
if not _squeeze_body:
    _bgfix2_bad("bgfix2-skeleton-attack-squeeze",
                "找不到 rollGoldLootAgainstSkeleton 方法体（反空转守护）")
else:
    for _n, _why in (("isSqueezeExempt(item)", "没有豁免判定（礼品金票会被一起挤掉）"),
                     ("AllItems.GOLDEN_BONE_MEAL.get()", "没有真的换成金骨粉"),
                     ("SKELETON_SQUEEZE_RATIO", "没有用那个 0.8 常量（变成拍脑袋的魔数）"),
                     ("random.nextInt(pool.size())", "取法变了（原有 rollGoldLoot 是等概率取一条）"),
                     ("pool.set(", "没有真的改池里的条目（「挤掉」没落地）"),
                     ("buildGoldLootPool(", "没有复用同一份掉落池清单")):
        if _n not in _squeeze_body:
            _bgfix2_bad("bgfix2-skeleton-attack-squeeze", "%s（缺 %s）" % (_why, _n))
_exempt_body = method_body(_bgfix_mod, "private static boolean isSqueezeExempt(")
if not _exempt_body:
    _bgfix2_bad("bgfix2-skeleton-ticket-exempt", "找不到 isSqueezeExempt 方法体（反空转守护）")
elif "AllItems.GIFT_GOLD_TICKET.get()" not in _exempt_body:
    _bgfix2_bad("bgfix2-skeleton-ticket-exempt",
                "豁免的不是礼品金票（作者点名「但除了礼品金票」）")
if "GIFT_TICKET_CHANCE = 0.06F" not in _bgfix_mod:
    _bgfix2_bad("bgfix2-skeleton-ticket-untouched",
                "礼品金票自己那条 6% 被改了（它不在「挤掉」范围内）")
else:
    _i_ticket = _income_body.find("GIFT_TICKET_CHANCE") if _income_body else -1
    _i_squeeze_call = _income_body.find("rollGoldLootAgainstSkeleton(") if _income_body else -1
    if _i_ticket < 0 or _i_squeeze_call < 0 or _i_ticket > _i_squeeze_call:
        _bgfix2_bad("bgfix2-skeleton-ticket-untouched",
                    "礼品金票那一掷不在挤掉之前（随机数顺序被改动）")
# 死亡掉落那条**原样保留**（作者要的是「不只是死亡掉落」）
if "SKELETON_GOLDEN_BONE_MEAL_CHANCE = 0.8F" not in _bgfix_mev:
    _bgfix2_bad("bgfix2-skeleton-death-drop-kept",
                "MetalEvents 的击杀掉落常量不在了（作者要的是「不只是死亡掉落」）")
_drops_body = method_body(_bgfix_mev, "public static void onLivingDrops(")
if not _drops_body:
    _bgfix2_bad("bgfix2-skeleton-death-drop-kept", "找不到 onLivingDrops 方法体（反空转守护）")
else:
    for _n in ("AbstractSkeleton", "GOLDEN_BONE_MEAL.get()", "event.getDrops().add(",
               "isSturdygoldAttackWeapon("):
        if _n not in _drops_body:
            _bgfix2_bad("bgfix2-skeleton-death-drop-kept", "击杀掉落那条被改坏了（缺 %s）" % _n)

# ---------- 第 3 条 · 闪耀藤条：除万坚金外的全部（7 族） ----------
_isour = method_body(_bgfix_glm, "private static boolean isOurTool(")
if not _isour:
    _bgfix2_bad("bgfix2-vine-all-but-sturdygold", "找不到 isOurTool 方法体（反空转守护）")
else:
    for _n, _why in (("family.isSpecialMetal()", "判据不是「特殊金属」"),
                     ("family.isTool(", "少了器具那一半"),
                     ("family.isWeapon(", "少了武器那一半")):
        if _n not in _isour:
            _bgfix2_bad("bgfix2-vine-all-but-sturdygold", "%s（缺 %s）" % (_why, _n))
_is_special = method_body(_bgfix_mf, "public boolean isSpecialMetal(")
if not _is_special:
    _bgfix2_bad("bgfix2-vine-all-but-sturdygold", "找不到 isSpecialMetal 方法体（反空转守护）")
elif "!STURDYGOLD_ID.equals(this.id)" not in _is_special:
    _bgfix2_bad("bgfix2-vine-all-but-sturdygold",
                "isSpecialMetal 不再是「排除万坚金」（作者：只有万坚金不挖）")
# 反空转：八族（八族 - 1 = 7 族能掉）；低于 8 说明扫描表/注册表被改坏了
# ⚠ 计数必须跑在 **AllMetals.java** 上（`new MetalFamily.Spec(` 的字面量形态）——
#   MetalFamily.java 里只有嵌套类 `Spec` 的定义，在那里数它恒为 0（本段第一版就踩了这个 = 假红）。
_spec_count = _bgfix_am.count("new MetalFamily.Spec(")
if _spec_count != 8:
    _bgfix2_bad("bgfix2-vine-all-but-sturdygold",
                "AllMetals 里的 MetalFamily.Spec 不是 8 个（实际 %d；反空转守护）" % _spec_count)
for _n, _why in (("BASE_CHANCE = 0.06F", "6% 基础概率被改"),
                 ("CHANCE_PER_FORTUNE = 0.06F", "时运系数被改")):
    if _n not in _bgfix_glm:
        _bgfix2_bad("bgfix2-vine-chance", "%s（缺 %s）" % (_why, _n))

# ---------- 第 6 条 · 成就：全开放（无 hidden）+ 制作改获得 ----------
_adv_files = sorted(_ADV.rglob("*.json"))
if len(_adv_files) != 51:
    _bgfix2_bad("bgfix2-adv-51", "成就 JSON 数 = %d，期望 51（反空转守护）" % len(_adv_files))
_hidden_files, _inv_files, _rc_files, _cond_files = [], [], [], []
for _f in _adv_files:
    _t = _f.read_text(encoding="utf-8")
    if '"hidden"' in _t:
        _hidden_files.append(_f.name)
    if "inventory_changed" in _t:
        _inv_files.append(_f.name)
    if "recipe_crafted" in _t:
        _rc_files.append(_f.name)
    if "farmersdelight" in _t:
        _cond_files.append(_f.name)
if _hidden_files:
    _bgfix2_bad("bgfix2-adv-no-hidden", "有 %d 个成就带了 hidden（作者要「全开放别隐藏」）：%s"
                % (len(_hidden_files), _hidden_files[:5]))
# ⛔ **bg-fix3 §四（作者 2026-10-07）改变了这里的期望值**：root 也改成「获得」⇒
#   `recipe_crafted` 在产物里**一条都不剩**。
#   ⚠ 旧期望原文保留（未删）：`if len(_rc_files) != 1 or _rc_files[0] != "root.json":`
#     `_bgfix2_bad("bgfix2-adv-recipe-crafted-root-only", "recipe_crafted 只许留在 root"
#     "（手册物品是条件注册，见 §14.3）；实际 = %s")`。
if _rc_files:
    _bgfix2_bad("bgfix2-adv-recipe-crafted-root-only",
                "recipe_crafted 在 bg-fix3 §四 之后应**一条都不剩**（root 也改成 inventory_changed 了；"
                "旧口径是「只许留在 root」）；实际 = %s" % _rc_files)
# 「制作改获得」点名的 9 条（bg-ach §七.2）+ 一个反空转阈值：
# 51 条里有很多本来就该用别的 trigger（villager_trade / player_hurt_entity / placed_block …），
# 所以阈值取「≥ 40」只当反空转守护，真正的判据是下面那 9 条逐个用 inventory_changed。
_BGFIX2_CRAFT_TO_HAVE = [
    "alchemy/mixed_crystal_pile", "alchemy/alchemic_fuel", "treasure/blazing_rod",
    "treasure/bundled_echo_shard", "treasure/indigo_ocean_heart",
    "treasure/amethyst_energy_dust", "treasure/chorus_cherry_branch",
    "treasure/any_raw_metal", "agriculture/gold_infused_dirt",
]
_missing_inv = [r for r in _BGFIX2_CRAFT_TO_HAVE
                if not (_ADV / (r + ".json")).is_file()
                or "inventory_changed" not in (_ADV / (r + ".json")).read_text(encoding="utf-8")]
if _missing_inv:
    _bgfix2_bad("bgfix2-adv-inventory-changed",
                "这 %d 条成就没有用 inventory_changed（制作没改成获得）：%s"
                % (len(_missing_inv), _missing_inv))
if len(_inv_files) < 40:
    _bgfix2_bad("bgfix2-adv-inventory-changed",
                "只有 %d 个成就用 inventory_changed（< 40 ⇒ 反空转失败：扫描没扫到东西）"
                % len(_inv_files))
if len(_cond_files) != 3:
    _bgfix2_bad("bgfix2-adv-fd-conditions",
                "乐事条件加载的条数 = %d，期望恰好 3（㊾/㊿/51）" % len(_cond_files))

# ---------- 第 1 条 · 纹饰色卡：四处嫌疑必须一直是干净的（修复前后都成立） ----------
_trim_jsons = sorted(_TRIM_MATERIAL.glob("*.json"))
if len(_trim_jsons) != 9:
    _bgfix2_bad("bgfix2-trim-nine-materials",
                "trim_material JSON 数 = %d，期望 9（反空转守护）" % len(_trim_jsons))
_indexes, _missing_palette = [], []
for _j in _trim_jsons:
    _d = json.loads(_j.read_text(encoding="utf-8"))
    _indexes.append(_d["item_model_index"])
    _pal = _PALETTES / (_d["asset_name"] + ".png")
    if not _pal.is_file():
        _missing_palette.append(_d["asset_name"])
        continue
    _ihdr = _png_ihdr(_pal.read_bytes())
    if _ihdr is None:
        _bgfix2_bad("bgfix2-trim-palette-8x1", "%s 不是 PNG" % _pal.name)
    elif _ihdr[0] != 8 or _ihdr[1] != 1 or _ihdr[2] != 8:
        _bgfix2_bad("bgfix2-trim-palette-8x1",
                    "%s 不是 8x1 / 8 位（实际 %s）" % (_pal.name, _ihdr))
if _missing_palette:
    _bgfix2_bad("bgfix2-trim-palette-present", "缺色卡：%s" % _missing_palette)
if len(set(_indexes)) != len(_indexes):
    _bgfix2_bad("bgfix2-trim-model-index-distinct",
                "item_model_index 有撞车（撞车会让某件盔甲命中别人的 override）；实际 = %s" % _indexes)
if any(0.1 - 1e-9 <= v <= 1.0 + 1e-9 for v in _indexes):
    _bgfix2_bad("bgfix2-trim-model-index-outside-vanilla",
                "有 item_model_index 落在原版 0.1~1.0 区间内（会命中原版 override）；实际 = %s" % _indexes)
_armor_atlas = json.loads((REPO / "src" / "main" / "resources" / "assets" / "minecraft" /
                           "atlases" / "armor_trims.json").read_text(encoding="utf-8"))
_armor_perms = {}
for _s in _armor_atlas["sources"]:
    _armor_perms.update(_s.get("permutations", {}))
_blocks_atlas = json.loads((REPO / "src" / "main" / "resources" / "assets" / "minecraft" /
                            "atlases" / "blocks.json").read_text(encoding="utf-8"))
_blocks_perms = {}
for _s in _blocks_atlas["sources"]:
    _blocks_perms.update(_s.get("permutations", {}))
if len(_armor_perms) < 9 or len(_blocks_perms) < 9:
    _bgfix2_bad("bgfix2-trim-atlas-both",
                "图集置换条数 < 9（反空转守护）：armor_trims=%d blocks=%d"
                % (len(_armor_perms), len(_blocks_perms)))
for _m in _BGFIX2_TRIMS:
    if _m not in _armor_perms:
        _bgfix2_bad("bgfix2-trim-atlas-both", "armor_trims.json 缺 %s（穿在身上那条链）" % _m)
    if _m not in _blocks_perms:
        _bgfix2_bad("bgfix2-trim-atlas-both", "blocks.json 缺 %s（物品形态那条链）" % _m)
_trim_models_src = strip_comments((JAVA / "client" / "ArmorTrimItemModels.java").read_text(encoding="utf-8"))
if "MetalFamily.all()" not in _trim_models_src:
    _bgfix2_bad("bgfix2-trim-model-generic",
                "ArmorTrimItemModels 不是按家族表泛化（白名单可能漏了靛海金）")
# 唯一允许写死的材质名 = unwanted_antique（1.3 的老古董，不属于任何 MetalFamily）
for _m in [m for m in _BGFIX2_TRIMS if m != "unwanted_antique"]:
    if '"%s"' % _m in _trim_models_src:
        _bgfix2_bad("bgfix2-trim-model-generic",
                    "ArmorTrimItemModels 里出现了写死的金属名 \"%s\"（应当由 MetalFamily.all() 泛化）"
                    % _m)

# ---------- 文档侧：bg-fix2 的新口径必须落档（docs/1.6-规格.md） ----------
for _needle, _why in (("bg-fix2", "docs/1.6-规格.md 里没有 bg-fix2 这一轮的节"),
                      ("Math.max(1, amplifier + 1)", "没写高燃 / 沉淀的现行公式"),
                      ("1 级 1 点 / 2 级 2 点", "没写「等级 = 点数」这条新口径"),
                      ("sawVictim", "没写音效与伤害解耦的新判据"),
                      ("SKELETON_SQUEEZE_RATIO", "没写金骨粉「挤掉 80% 条目」的常量"),
                      ("靛海金", "没写第 1 条（靛海金色卡）的取证结论")):
    if _needle not in _bgfix_spec:
        _bgfix2_bad("bgfix2-doc", "%s（缺 %s）" % (_why, _needle))

# ==================== bg-book §八 追加轮（2026-10-06）：「装备的强化」9 章 ====================
#
# 需求：`开工需求\20261004-1733_bg-book_patchouli-handbook.md` 的 **§八**（`最后更新` 10-06 13:25）。
# 三条口径（逐条都有出处）：
#
#   ① **每页 2 个配方是 Patchouli 的结构上限**（`PageDoubleRecipe` 只有 `recipe` / `recipe2`
#      两个槽）⇒ §8.3~§8.10 的「后页…**按固定顺序挂 14 件**」= **门禁项**
#      ⇒ 按作者 2026-10-04 亲自裁定的同一句话落成 **7 页 × 2 配方**（不是我们的退化方案）；
#   ② 逐字文案的期望值来源 = **仓库内冻结快照**
#      `tools/asset-generator/bgappend-requirements-snapshot/bg-book-8.md`
#      （**不读**仓库外那份活页；口径见 §17.3.1 / `mcmod_experience` `ex\03` §3.10）；
#   ③ 类别「装备的升级」⇒「**装备的强化**」：**id 与图标都不动**、只改显示名（值级更正），
#      旧名值留在语言文件里作历史留档。
#
# ⚠ 另有 **1 条代码侧断言**（`[bgbook8-voodoo-poison-independent]`）：本轮由父代理授权**顺手修掉**
#   的真 bug —— 巫毒金「穿满四件免疫中毒」原来**写在结雷金早退之后**、从未生效。
bgbook8_problems: list[str] = []


def _bgbook8_bad(tag: str, msg: str) -> None:
    bgbook8_problems.append("%s [%s]" % (msg, tag))


_BG8_SNAPSHOT = _BG2_SNAPSHOT_DIR / "bg-book-8.md"
# 八族的**排版顺序**（= 作者给的章节顺序 = 生成器 `generate_handbook_data.py` 的 METALS 顺序）
_BG8_METAL_ORDER = ["flamegold", "sturdygold", "thornsgold", "echogold",
                    "indigoseagold", "voodoogold", "thundergold", "illusiongold"]
_BG8_TEXT_LABELS = ("1_left", "1_right", "2_left")
# 「后页」的 14 件**固定顺序**（§8.3 正文逐字给出；§8.12 第 2 条列为推断值）
_BG8_FORGE_ORDER = ["sword", "mace", "trident", "bow", "crossbow", "axe", "pickaxe", "shovel",
                    "hoe", "shield", "helmet", "chestplate", "leggings", "boots"]

# ---------- 生成器覆盖（"每加一类东西问一句"）：两边的族清单 / 常量必须一致 ----------
_BG8_GEN = _BGDOC_GEN
if not _BG8_GEN.is_file():
    _bgbook8_bad("bgbook8-generator", "读不到手册生成器：%s" % _BG8_GEN)
else:
    _bg8_gen_src = _BG8_GEN.read_text(encoding="utf-8")
    _bg8_m = re.search(r"^METALS = \[(.*?)^\]", _bg8_gen_src, re.S | re.M)
    if not _bg8_m:
        _bgbook8_bad("bgbook8-generator", "读不到生成器的 METALS 清单（反空转守护）")
    else:
        _bg8_gen_order = re.findall(r'\("([a-z]+)",', _bg8_m.group(1))
        if _bg8_gen_order != _BG8_METAL_ORDER:
            _bgbook8_bad("bgbook8-generator",
                         "生成器的 METALS 顺序 %s 与本关卡的排版顺序 %s 不一致（加/改族时只长一边）"
                         % (_bg8_gen_order, _BG8_METAL_ORDER))
        if len(_bg8_gen_order) != 8:
            _bgbook8_bad("bgbook8-generator",
                         "生成器的族数不是 8（实际 %d）—— 反空转守护" % len(_bg8_gen_order))
    for _needle, _why in (("FORGE_ORDER = [", "生成器里没有 FORGE_ORDER（14 件固定顺序的真源）"),
                          ("GEAR_BLANK_ROWS = [", "生成器里没有章1 的胚底配方表"),
                          ("GEAR_CATEGORY = ", "生成器里没有 GEAR_CATEGORY"),
                          ("RETIRED_ENTRIES", "生成器里没有把两个旧条目标成作废（RETIRED_ENTRIES）")):
        if _needle not in _bg8_gen_src:
            _bgbook8_bad("bgbook8-generator", _why)

# ---------- ① 类别改名（id / 图标不动，只改显示名；旧名必须被替换） ----------
_BG8_CAT_NAME_KEY = "bettergold.handbook.category.gear_upgrade.name"
_BG8_CAT_ZH = _bgappend_jload(_ZH_BOOK / "categories" / "gear_upgrade.json")
_BG8_CAT_EN = _bgappend_jload(_EN_BOOK / "categories" / "gear_upgrade.json")
if (_BG8_CAT_ZH.get("sortnum"), _BG8_CAT_ZH.get("icon")) != (1, "bettergold:sturdygold_sword"):
    _bgbook8_bad("bgbook8-gear-category",
                 "「装备的强化」的 sortnum / 图标动了（应是 1 / bettergold:sturdygold_sword）：%r"
                 % ((_BG8_CAT_ZH.get("sortnum"), _BG8_CAT_ZH.get("icon")),))
for _e, _side in ((_BG8_CAT_ZH, "zh"), (_BG8_CAT_EN, "en")):
    if _e.get("name") != _BG8_CAT_NAME_KEY:
        _bgbook8_bad("bgbook8-gear-category", "%s 侧类别 name 不是 %s：%r"
                     % (_side, _BG8_CAT_NAME_KEY, _e.get("name")))
if zh.get(_BG8_CAT_NAME_KEY) != u"装备的强化":
    _bgbook8_bad("bgbook8-gear-category",
                 "类别中文名不是「装备的强化」（§8.1）：%r" % (zh.get(_BG8_CAT_NAME_KEY),))
if zh.get(_BG8_CAT_NAME_KEY) == u"装备的升级":
    _bgbook8_bad("bgbook8-gear-category", "类别中文名还是旧的「装备的升级」（§八 要求替换）")
if not en.get(_BG8_CAT_NAME_KEY) or en.get(_BG8_CAT_NAME_KEY) == zh.get(_BG8_CAT_NAME_KEY):
    _bgbook8_bad("bgbook8-gear-category",
                 "类别英文名缺失或与中文逐字相同：%r" % (en.get(_BG8_CAT_NAME_KEY),))

# ---------- ② 9 个章节条目：目录 / 图标 / sortnum / 页数 / 页型 / 配方逐条 ----------
_BG8_CHAPTERS = (("linkage", "golden_mace_blank"),) + tuple(
    (m, "%s_sword" % m) for m in _BG8_METAL_ORDER)
_BG8_PAGES_TOTAL = 0
_BG8_FORGE_REFS: set = set()
_BG8_BLANK_REFS: set = set()
for _idx, (_chap, _icon) in enumerate(_BG8_CHAPTERS):
    _zh_p = _ZH_BOOK / "entries" / ("gear_%s.json" % _chap)
    _en_p = _EN_BOOK / "entries" / ("gear_%s.json" % _chap)
    if not _zh_p.is_file() or not _en_p.is_file():
        _bgbook8_bad("bgbook8-chapters", "缺章节条目文件（zh/en 各需一份）：gear_%s" % _chap)
        continue
    _zh_e = json.loads(_zh_p.read_text(encoding="utf-8"))
    _en_e = json.loads(_en_p.read_text(encoding="utf-8"))
    if _zh_e.get("category") != "bettergold:gear_upgrade":
        _bgbook8_bad("bgbook8-chapters",
                     "gear_%s 不挂在「装备的强化」类别下：%r" % (_chap, _zh_e.get("category")))
    if _zh_e.get("name") != "bettergold.handbook.entry.gear_%s" % _chap:
        _bgbook8_bad("bgbook8-chapters",
                     "gear_%s 的 name 不是 bettergold.handbook.entry.gear_%s" % (_chap, _chap))
    if _zh_e.get("icon") != "bettergold:%s" % _icon:
        _bgbook8_bad("bgbook8-chapters", "gear_%s 的封面图标不是 bettergold:%s：%r"
                     % (_chap, _icon, _zh_e.get("icon")))
    if _zh_e.get("sortnum") != _idx:
        _bgbook8_bad("bgbook8-chapters", "gear_%s 的 sortnum 不是 %d" % (_chap, _idx))
    if _zh_e.get("pages") != _en_e.get("pages"):
        _bgbook8_bad("bgbook8-chapters", "gear_%s 的 zh/en 页列表不一致（结构必须双端相同）" % _chap)
    _pages = _zh_e.get("pages") or []
    _BG8_PAGES_TOTAL += len(_pages)
    _want_count = 6 if _chap == "linkage" else 10
    if len(_pages) != _want_count:
        _bgbook8_bad("bgbook8-chapters",
                     "gear_%s 的页数不是 %d（章1 = 3 文案 + 3 配方；八族 = 3 文案 + 7 锻造）：%d"
                     % (_chap, _want_count, len(_pages)))
        continue
    _want_seq = ["patchouli:text"] * 3 + (["patchouli:crafting"] * 3 if _chap == "linkage"
                                          else ["patchouli:smithing"] * 7)
    _seq = [str(_p.get("type")) for _p in _pages]
    if _seq != _want_seq:
        _bgbook8_bad("bgbook8-page-types", "gear_%s 的页型序列不是 %s：%s" % (_chap, _want_seq, _seq))
    for _i, _label in enumerate(_BG8_TEXT_LABELS):
        _want_key = "bettergold.handbook.page.gear_%s_%s" % (_chap, _label)
        if _pages[_i].get("text") != _want_key:
            _bgbook8_bad("bgbook8-page-types", "gear_%s 第 %d 页的正文键不是 %s：%r"
                         % (_chap, _i + 1, _want_key, _pages[_i].get("text")))
    for _p in _pages:
        for _overflow in ("recipe3", "recipe4", "recipes"):
            if _overflow in _p:
                _bgbook8_bad("bgbook8-page-types",
                             "gear_%s 的页里出现 %s（Patchouli 只有 recipe / recipe2 两个槽）"
                             % (_chap, _overflow))
        if _p.get("type") not in _KNOWN_PAGE_TYPES:
            _bgbook8_bad("bgbook8-page-types", "gear_%s 用了未知页面类型 %s" % (_chap, _p.get("type")))
    if _chap == "linkage":
        _want_blank = [("golden_mace_blank", "golden_trident_blank"),
                       ("golden_bow_blank", "golden_crossbow_blank"),
                       ("golden_shield_blank", None)]
        for _i, (_a, _b) in enumerate(_want_blank):
            _pg = _pages[3 + _i]
            _want_a = "bettergold:%s" % _a
            _want_b = ("bettergold:%s" % _b) if _b else None
            if _pg.get("recipe") != _want_a or _pg.get("recipe2") != _want_b:
                _bgbook8_bad("bgbook8-blank-recipes",
                             "章1 第 %d 个配方页不是 (%s, %s)：%r" % (_i + 1, _want_a, _want_b, _pg))
            # ⚠ 死链检查必须收集**页面上实际写的** id（不是期望值）—— 否则"把引用改成不存在的配方"
            #   这条扰动会**打不中** `[bgbook8-recipe-refs]`（本轮扰动 P08 实测抓到的假绿）
            for _rk in ("recipe", "recipe2"):
                if isinstance(_pg.get(_rk), str):
                    _BG8_BLANK_REFS.add(_pg[_rk])
    else:
        if len(_BG8_FORGE_ORDER) != 14:
            _bgbook8_bad("bgbook8-forge-order",
                         "FORGE_ORDER 不是 14 件（实际 %d）—— 反空转守护" % len(_BG8_FORGE_ORDER))
        for _i in range(0, len(_BG8_FORGE_ORDER), 2):
            _pg = _pages[3 + _i // 2]
            _wa = "bettergold:smithing_%s_%s" % (_chap, _BG8_FORGE_ORDER[_i])
            _wb = "bettergold:smithing_%s_%s" % (_chap, _BG8_FORGE_ORDER[_i + 1])
            if _pg.get("recipe") != _wa or _pg.get("recipe2") != _wb:
                _bgbook8_bad("bgbook8-forge-order",
                             "gear_%s 的锻造页顺序不对：第 %d 页期望 (%s, %s)，实际 %r"
                             % (_chap, _i // 2 + 1, _wa, _wb, _pg))
            for _rk in ("recipe", "recipe2"):     # 同上：收集**实际**引用（死链检查用）
                if isinstance(_pg.get(_rk), str):
                    _BG8_FORGE_REFS.add(_pg[_rk])
if _BG8_PAGES_TOTAL != 86:
    _bgbook8_bad("bgbook8-chapters",
                 "9 章合计页数不是 86（章1 6 + 八族 8×10）：%d —— 反空转守护" % _BG8_PAGES_TOTAL)
if len(_BG8_FORGE_REFS) != 112:
    _bgbook8_bad("bgbook8-forge-order",
                 "锻造页的配方引用不是 8×14 = 112 条：%d —— 反空转守护" % len(_BG8_FORGE_REFS))
if len(_BG8_BLANK_REFS) != 5:
    _bgbook8_bad("bgbook8-blank-recipes",
                 "章1 的胚底配方引用不是 5 条：%d —— 反空转守护" % len(_BG8_BLANK_REFS))
_bg8_missing_recipes = sorted(
    _r for _r in (_BG8_FORGE_REFS | _BG8_BLANK_REFS)
    if not (_DATA / "bettergold" / "recipe" / (_r.split(":", 1)[1] + ".json")).is_file())
if _bg8_missing_recipes:
    _bgbook8_bad("bgbook8-recipe-refs",
                 "§八 引用了不存在的配方（死链，游戏里那一页会空掉）：%s" % _bg8_missing_recipes[:5])

# ---------- ③ 章3 第 1 页（§七 的汇总页）必须已经删除，且"作废"要能自证 ----------
_bg8_all_pages = []
for _e in _entries_now.values():
    _bg8_all_pages.extend(_e.get("pages") or [])
_bg8_stale_text = [p.get("text") for p in _bg8_all_pages
                   if p.get("text") == "bettergold.handbook.page.knowledge_1_summary"]
_bg8_stale_title = [p.get("title") for p in _bg8_all_pages
                    if p.get("title") in (_BG3_INGOT_TITLE, _BG3_TEMPLATE_TITLE)]
_bg8_stale_items = [p for p in _bg8_all_pages
                    if p.get("item") in (_BG3_INGOT_IDS, _BG3_TEMPLATE_IDS)]
if _bg8_stale_text or _bg8_stale_title or _bg8_stale_items:
    _bgbook8_bad("bgbook8-k3-p1-gone",
                 "§八 删掉的章3 第 1 页（§七 的汇总页）又回来了：text=%s title=%s 旧图标表=%d 页"
                 % (_bg8_stale_text, _bg8_stale_title, len(_bg8_stale_items)))
for _k in ("bettergold.handbook.page.knowledge_1_summary",):
    # ⚠ **记账（以实际为准）**：`docs/1.6-规格.md` §17.1 写「`knowledge_1_left` / `knowledge_1_right`
    #   两把键**留在语言文件里作历史留档**」，但**实测这两把键在两份语言文件里都不存在**
    #   （`grep 'knowledge_1'` 只有 `knowledge_1_summary` 一条）⇒ 本断言只钉**确实存在**的那一把，
    #   差异写进 §十九（不是本轮的改动，本轮没删过任何键）。
    if _k not in zh or _k not in en:
        _bgbook8_bad("bgbook8-k3-p1-gone", "历史留档键被删了（既定口径：原文不删）：%s" % _k)


# ---------- ④ 逐字文案 + 语言键：期望值来自**仓库内冻结快照** ----------
def _bg8_parse_snapshot() -> tuple:
    """从冻结快照解析 (类别新名, [(章节 id, 章节名, {label: 逐字文案})])。

    ⚠ 两处**解析形状**（都不是猜的）：
      * markdown 表里的 `\\|` 是**转义竖线**（作者原文「更多锻造模板|重生」）——
        必须先换哨兵再切列，否则那一行整体错位（本轮语言键注入脚本第一版就踩了）；
      * 数据行判据 = 第一格是「1 左 / 1 右 / 2 左 / 2 右 / 3 左 / 3 右 / 后页」，
        **不许**依赖"含不含某个字"（那是 §17.3.1 记的上一轮的坑）。
    """
    _lines = _BG8_SNAPSHOT.read_text(encoding="utf-8").split("\n")

    def _clean(_c: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*", r"\1", _c.replace("\\|", "|")).strip()

    _cat = ""
    for _l in _lines:
        if u"手册四类变为" in _l:
            _names = [_clean(x) for x in _l.split(u"：", 1)[1].rstrip(u"。").split("/")]
            if len(_names) == 4:
                _cat = _names[1]
    _out = []

    def _table(_start: int):
        _rows, _i = [], _start
        while _i < len(_lines) and not _lines[_i].startswith("#### ") \
                and not _lines[_i].startswith("##### "):
            _l = _lines[_i]
            if _l.startswith("|") and "|---" not in _l:
                _safe = _l.replace("\\|", "\x01")
                _cells = [c.replace("\x01", "|") for c in _safe.split("|")[1:-1]]
                if len(_cells) >= 2:
                    _rows.append((_cells[0].strip(), _cells[1]))
            _i += 1
        return _rows

    for _i, _l in enumerate(_lines):
        if re.match(r"^#### 8\.2 章节 1 · ", _l):
            _m = re.match(r"^#### 8\.2 章节 1 · (.+?)（封面：", _l)
            _rows = _table(_i + 1)
            _texts = [c for (a, c) in _rows if a in (u"1 左", u"1 右", u"2 左")]
            if _m and len(_texts) == 3:
                _out.append(("linkage", _clean(_m.group(1)),
                             dict(zip(_BG8_TEXT_LABELS, [_clean(t) for t in _texts]))))
    _metal_at = [_i for _i, _l in enumerate(_lines) if re.match(r"^##### 章节 \d+ · ", _l)]
    for _k, _i in enumerate(_metal_at):
        _m = re.match(r"^##### 章节 \d+ · (.+?)（封面：", _lines[_i])
        _rows = _table(_i + 1)
        _texts = [c for (a, c) in _rows if a in (u"1 左", u"1 右", u"2 左")]
        if _k < len(_BG8_METAL_ORDER) and _m and len(_texts) == 3:
            _out.append((_BG8_METAL_ORDER[_k], _clean(_m.group(1)),
                         dict(zip(_BG8_TEXT_LABELS, [_clean(t) for t in _texts]))))
    return _cat, _out


if not _BG8_SNAPSHOT.is_file():
    _bgbook8_bad("bgbook8-texts-verbatim", "读不到冻结快照（逐字文案的期望值来源）：%s" % _BG8_SNAPSHOT)
else:
    _bg8_cat, _bg8_parsed = _bg8_parse_snapshot()
    if _bg8_cat and _bg8_cat != zh.get(_BG8_CAT_NAME_KEY):
        _bgbook8_bad("bgbook8-gear-category",
                     "快照里的类别新名 %r 与语言文件里的 %r 不一致" % (_bg8_cat, zh.get(_BG8_CAT_NAME_KEY)))
    if len(_bg8_parsed) != 9:
        _bgbook8_bad("bgbook8-texts-verbatim",
                     "从冻结快照解析到 %d 章（应 9 = 1 + 8；反空转守护）" % len(_bg8_parsed))
    _bg8_texts, _bg8_bad_names = [], []
    for _chap, _name, _texts in _bg8_parsed:
        for _label in _BG8_TEXT_LABELS:
            _k = "bettergold.handbook.page.gear_%s_%s" % (_chap, _label)
            _v = _texts.get(_label, "")
            _bg8_texts.append(_v)
            if zh.get(_k) != _v:
                _bgbook8_bad("bgbook8-texts-verbatim",
                             "快照里的逐字文案没有按原样落在 %s 里（首 30 字：%s）" % (_k, _v[:30]))
        _nk = "bettergold.handbook.entry.gear_%s" % _chap
        if zh.get(_nk) != _name:
            _bg8_bad_names.append((_nk, _name, zh.get(_nk)))
    if _bg8_bad_names:
        _bgbook8_bad("bgbook8-lang-bilingual",
                     "章节名与快照标题不一致：%s" % (_bg8_bad_names[:2],))
    if len(_bg8_texts) != 27 or sum(len(_t) for _t in _bg8_texts) < 1000:
        _bgbook8_bad("bgbook8-texts-verbatim",
                     "从冻结快照解析到 %d 段逐字文案 / 共 %d 字（应 27 段 = 3 + 8×3、总字数 >= 1000；"
                     "反空转守护）" % (len(_bg8_texts), sum(len(_t) for _t in _bg8_texts)))
    _bg8_missing_texts = [_t for _t in _bg8_texts if _t not in set(zh.values())]
    if _bg8_missing_texts:
        _bgbook8_bad("bgbook8-texts-verbatim",
                     "冻结快照里的逐字文案没有原样出现在 zh_cn.json 里（%d/%d 段缺失，首条：%s）"
                     % (len(_bg8_missing_texts), len(_bg8_texts), _bg8_missing_texts[0][:40]))
    # 语言键：9 个条目名 + 27 段文案 = **36** 条，中英双端都要有（en 不许等于 zh、不许为空）
    _bg8_keys = (["bettergold.handbook.entry.gear_%s" % _c for _c, _n, _t in _bg8_parsed]
                 + ["bettergold.handbook.page.gear_%s_%s" % (_c, _l) for _c, _n, _t in _bg8_parsed
                    for _l in _BG8_TEXT_LABELS])
    if len(_bg8_keys) != 36:
        _bgbook8_bad("bgbook8-lang-bilingual",
                     "§八 的语言键清单是 %d 条（应 36 = 9 + 27；反空转守护）" % len(_bg8_keys))
    for _k in _bg8_keys:
        if _k not in zh or _k not in en:
            _bgbook8_bad("bgbook8-lang-bilingual", "§八 语言键缺中文或英文：%s" % _k)
        elif not en[_k].strip() or en[_k] == zh[_k]:
            _bgbook8_bad("bgbook8-lang-bilingual",
                         "§八 的英文值缺失或与中文逐字相同（作者只给了中文，需要忠实英译）：%s" % _k)

# ---------- ⑤ 代码侧（父代理 2026-10-06 授权顺手修的真 bug）：巫毒整套免疫中毒必须**独立判定** ----------
#  旧形状（原文留档）：结雷金先 `if (wornPieces(entity, family) < 4) return;`，
#  巫毒那条 `wornPieces(entity, voodooFamily) >= 4` 写在它**之后** ⇒ 只穿满 4 件巫毒金时
#  永远走不到，手册 §八 写的「全套巫毒金 ⇒ 免疫中毒」**从未实现**。
#  现行形状：两条各自 `if (x != null && wornPieces(...) >= 4)`，方法体里**只许有 1 处 `return;`**
#  （tickCount / 客户端那道早退）⇒ 任何一处改回 `< 4 ⇒ return` 都会当场红。
_bg8_living_tick = method_body(_bgfix_mev, "public static void onLivingTick(")
if not _bg8_living_tick:
    _bgbook8_bad("bgbook8-voodoo-poison-independent", "找不到 onLivingTick 方法体（反空转守护）")
else:
    _bg8_guards = re.findall(r"wornPieces\(entity, \w+\)[^;\n]*", _bg8_living_tick)
    if len(_bg8_guards) != 2:
        _bgbook8_bad("bgbook8-voodoo-poison-independent",
                     "onLivingTick 里的 wornPieces 判定不是 2 处（结雷金 / 巫毒金各一处；实际 %d）：%s"
                     % (len(_bg8_guards), _bg8_guards))
    for _g in _bg8_guards:
        if ">= 4" not in _g:
            _bgbook8_bad("bgbook8-voodoo-poison-independent",
                         "整套类免疫用了早退形状（%r）—— 旧 bug 正是「结雷金 < 4 ⇒ return」"
                         "把巫毒那条中毒免疫挡在后面；两条必须各判各的（if (x != null && ... >= 4)）" % _g)
    for _needle in ("if (family != null && wornPieces(entity, family) >= 4)",
                    "if (voodooFamily != null && wornPieces(entity, voodooFamily) >= 4)"):
        if _needle not in _bg8_living_tick:
            _bgbook8_bad("bgbook8-voodoo-poison-independent", "守卫不在位：%s" % _needle)
    if _bg8_living_tick.count("return;") != 1:
        _bgbook8_bad("bgbook8-voodoo-poison-independent",
                     "onLivingTick 里的 return; 不是恰好 1 处（只许 tickCount / 客户端那道早退）：%d"
                     % _bg8_living_tick.count("return;"))

# ---------- ⑥ 文档侧：§八 的口径必须落档 ----------
for _needle, _why in ((u"bg-book §八", "docs/1.6-规格.md 里没有 bg-book §八 这一轮的节"),
                      (u"后页 = 7 页 × 2 配方", "没写明门禁项的落法（14 件 = 7 页 × 2 配方）"),
                      (u"以实际为准", "没写明 §8.11 十六条的处置口径（以实际为准 + 代码侧待办）"),
                      (u"代码侧待办", "没列代码侧待办"),
                      (u"巫毒", "没写第 8 条那个真 bug（巫毒整套免疫中毒）的修法与 A 级对照")):
    if _needle not in _bgfix_spec:
        _bgbook8_bad("bgbook8-doc", "%s（缺 %s）" % (_why, _needle))

# ==================== ⑦ bgfinal3（2026-10-06）：三条作者裁定 ====================
# 作者原话：「靛海金在这里，改手册，需要」⇒ 三件：① 色卡恢复（贴图，关卡在
# `validate_metal_assets.py` / `validate_trim_assets.py`）② 手册「全套」→「任意一件」
# （**改手册不改代码**）③ 金胡萝卜补一次原版 `placed_block` 触发（成就 ㊻ 的「种植」半边）。
bgfinal3_problems = []


def _bgfinal3_bad(tag: str, msg: str) -> None:
    bgfinal3_problems.append("[%s] %s" % (tag, msg))


# ---------- ⑦-1 手册：猪灵以物易物「翻倍」的触发条件 =「任意一件」（以代码实际为准） ----------
# ⚠ **旧口径（原文保留）**：本手册文案原先写「此外**全套的**万坚金盔甲还能使猪灵以物易物的
#   获取量翻倍」；而代码从来就是「**任意一件**」（`ModEvents#wearingAnySturdygoldArmor` 的
#   javadoc 自写「单件即可，无需全套」，四个部位 `||` 相连）—— 这是 `docs/1.6-规格.md`
#   §19.4 第 3 条记的「条件比手册宽」，体检报告第 3 节第 2 行把它列为「⚠等作者裁定」。
#   **作者 2026-10-06 裁定：改手册（不是改代码）** ⇒ 本条按「以实际为准」把手册改成
#   「任意一件」，并把「其余逐字不动」也钉住（等式而非包含）。
#   ⇒ 手册文案**只许**在这一步之后仍然写「任意一件」；代码**不许**被反向改窄成一套。
_BG3_BARTER_KEY = "bettergold.handbook.page.gear_sturdygold_2_left"
_BG3_BARTER_ZH_HEAD = (u"使用万坚金升级而成的盔甲穿戴后会随着每隔 16 秒的时间为你的一颗心镀上黄金"
                       u"来抵挡一些伤害，每一件盔甲所能补充的上限为 2 颗，自然而然的会随着会随着你穿戴着"
                       u"每一件万坚金盔甲和万坚金盾牌来扩充金心的上限，此外")
_BG3_BARTER_ZH_MID = u"任意一件万坚金盔甲"
_BG3_BARTER_ZH_TAIL = u"还能使猪灵以物易物的获取量翻倍。"
_BG3_BARTER_EN_HEAD = (u"Armor upgraded from Sturdygold gilds one of your hearts in gold every 16 seconds to "
                       u"block some damage, and each piece adds a cap of 2 hearts. Naturally, every Sturdygold "
                       u"armor piece and Sturdygold shield you wear expands the golden-heart cap -- and ")
_BG3_BARTER_EN_MID = u"any single piece of Sturdygold armor"
_BG3_BARTER_EN_TAIL = u" also doubles what you get from bartering with piglins."
# 旧口径的两个短语：在两份语言文件 + 冻结快照里**都不许**再出现（负向判据）
_BG3_BARTER_OLD_ZH = u"全套的万坚金盔甲"
_BG3_BARTER_OLD_EN = u"a full set of Sturdygold armor"

_bg3_zh_val = zh.get(_BG3_BARTER_KEY) or ""
_bg3_en_val = en.get(_BG3_BARTER_KEY) or ""
if _bg3_zh_val != (_BG3_BARTER_ZH_HEAD + _BG3_BARTER_ZH_MID + _BG3_BARTER_ZH_TAIL):
    _bgfinal3_bad("bgfinal3-manual-barter-single-piece",
                  u"手册 %s 的中文值不是「…此外任意一件万坚金盔甲还能使猪灵以物易物的获取量翻倍。」"
                  u"（其余必须逐字不变；实际首 24 字：%s）" % (_BG3_BARTER_KEY, _bg3_zh_val[:24]))
if _bg3_en_val != (_BG3_BARTER_EN_HEAD + _BG3_BARTER_EN_MID + _BG3_BARTER_EN_TAIL):
    _bgfinal3_bad("bgfinal3-manual-barter-single-piece",
                  u"手册 %s 的英文值不是「…and any single piece of Sturdygold armor also doubles…」"
                  u"（中英必须同步改；实际首 24 字：%s）" % (_BG3_BARTER_KEY, _bg3_en_val[:24]))
for _tag, _v in (("zh_cn.json", _bg3_zh_val), ("en_us.json", _bg3_en_val)):
    if _BG3_BARTER_OLD_ZH in _v or _BG3_BARTER_OLD_EN in _v:
        _bgfinal3_bad("bgfinal3-manual-barter-single-piece",
                      u"%s 里还留着旧口径「全套」（已被作者 2026-10-06 裁定按代码实际改成「任意一件」）" % _tag)
_bg3_snap_text = _BG8_SNAPSHOT.read_text(encoding="utf-8") if _BG8_SNAPSHOT.is_file() else ""
# ⚠ 只查「冻结正文」那一段：`## 快照搬运记录` 表里**故意**留着旧口径原文（"原文不删"的口径），
#   拿整份文件做负向判据会把自己的搬运记录当成违规（第一版就是这么红的）。
_bg3_snap_body = _bg3_snap_text.split(u"## 快照搬运记录")[0] if _bg3_snap_text else ""
if not _bg3_snap_text:
    _bgfinal3_bad("bgfinal3-manual-barter-single-piece",
                  u"读不到冻结快照（`[bgbook8-texts-verbatim]` 的期望值来源）：%s" % _BG8_SNAPSHOT)
elif not _bg3_snap_body:
    _bgfinal3_bad("bgfinal3-manual-barter-single-piece",
                  u"冻结快照里找不到「## 快照搬运记录」分界（反空转守护）")
else:
    if _BG3_BARTER_OLD_ZH in _bg3_snap_body:
        _bgfinal3_bad("bgfinal3-manual-barter-single-piece",
                      u"冻结快照正文里还是旧口径「%s」⇒ 语言文件改了、快照没改（"
                      u"`[bgbook8-texts-verbatim]` 会跟着红）" % _BG3_BARTER_OLD_ZH)
    if _BG3_BARTER_ZH_TAIL not in _bg3_snap_body or _BG3_BARTER_ZH_MID not in _bg3_snap_body:
        _bgfinal3_bad("bgfinal3-manual-barter-single-piece",
                      u"冻结快照正文里没有新口径「%s」/「%s」" % (_BG3_BARTER_ZH_MID, _BG3_BARTER_ZH_TAIL))

# 代码侧负向：`wearingAnySturdygoldArmor` 必须仍是「任意一件」（四个部位 `||`），
# **不许**有人为了对齐手册而把它改成「全套」（那是削玩家收益的反向改动）。
_bg3_barter_body = method_body(_bgfix_mod, "public static boolean wearingAnySturdygoldArmor(")
if not _bg3_barter_body:
    _bgfinal3_bad("bgfinal3-manual-follows-code",
                  u"ModEvents 里找不到 wearingAnySturdygoldArmor 方法体（反空转守护）")
else:
    if _bg3_barter_body.count("getItemBySlot(") != 4:
        _bgfinal3_bad("bgfinal3-manual-follows-code",
                      u"wearingAnySturdygoldArmor 不再判 4 个部位（实际 %d 处 getItemBySlot）"
                      % _bg3_barter_body.count("getItemBySlot("))
    if "||" not in _bg3_barter_body:
        _bgfinal3_bad("bgfinal3-manual-follows-code",
                      u"wearingAnySturdygoldArmor 没有 `||`（「任意一件」的语义就是 OR）")
    if "&&" in _bg3_barter_body:
        _bgfinal3_bad("bgfinal3-manual-follows-code",
                      u"wearingAnySturdygoldArmor 里出现了 `&&` ⇒ 被改成了「全套」（作者裁定的"
                      u"是**改手册**、不是削玩家收益）")

# ---------- ⑦-2 金胡萝卜：种下那一处必须补一次原版 `placed_block` 触发 ----------
# 依据（【读源码】）：`BlockItem.java:78-85` 原版在"方块真的放下且 blockstate 一致"之后才
# `CriteriaTriggers.PLACED_BLOCK.trigger((ServerPlayer)player, blockpos, itemstack)`；
# `ItemUsedOnLocationTrigger.java:31-42` = `PLACED_BLOCK` 的真身，签名 3 参、判据读 `pos` 上的 BlockState。
# 金胡萝卜是自定义事件种下的（`setBlock` + `setCanceled`，不走 BlockItem#place、也没有物品形态可判）
# ⇒ 不补这一次触发，成就 ㊻ 的「种植」半边只覆盖金麦种子 / 金钱茄种子。
_bg3_carrot_body = method_body(_bgfix_mod, "public static void onRightClickGoldenCarrot(")
if not _bg3_carrot_body:
    _bgfinal3_bad("bgfinal3-carrot-placed-block-trigger",
                  u"ModEvents 里找不到 onRightClickGoldenCarrot 方法体（反空转守护）")
else:
    if _bgfix_mod.count("CriteriaTriggers.PLACED_BLOCK.trigger(") != 1:
        _bgfinal3_bad("bgfinal3-carrot-placed-block-trigger",
                      u"ModEvents 里 `CriteriaTriggers.PLACED_BLOCK.trigger(` 不是恰好 1 处（实际 %d）"
                      % _bgfix_mod.count("CriteriaTriggers.PLACED_BLOCK.trigger("))
    _bg3_can_survive = method_body(_bg3_carrot_body, "if (cropState.canSurvive(level, plantPos))")
    if not _bg3_can_survive:
        _bgfinal3_bad("bgfinal3-carrot-placed-block-trigger",
                      u"找不到 `if (cropState.canSurvive(level, plantPos))` 块（反空转守护）")
    else:
        if "CriteriaTriggers.PLACED_BLOCK.trigger(" not in _bg3_can_survive:
            _bgfinal3_bad("bgfinal3-carrot-placed-block-trigger",
                          u"那次 `PLACED_BLOCK.trigger` **不在**「种下金胡萝卜」的分支里"
                          u"（必须落在 `canSurvive` ⇒ `setBlock` 之后的那一块内）")
        if "level.setBlock(plantPos, cropState, 3)" not in _bg3_can_survive:
            _bgfinal3_bad("bgfinal3-carrot-placed-block-trigger",
                          u"`setBlock` 不在 canSurvive 块里（判据读的是 pos 上的 BlockState，"
                          u"必须在放置之后才触发）")
        elif (_bg3_can_survive.find("level.setBlock(plantPos, cropState, 3)")
              > _bg3_can_survive.find("CriteriaTriggers.PLACED_BLOCK.trigger(")):
            _bgfinal3_bad("bgfinal3-carrot-placed-block-trigger",
                          u"触发在 `setBlock` **之前** ⇒ 判据读到的还是空气，永远不达成")
        if "player instanceof ServerPlayer" not in _bg3_can_survive:
            _bgfinal3_bad("bgfinal3-carrot-placed-block-trigger",
                          u"`PLACED_BLOCK.trigger` 没有 `player instanceof ServerPlayer` 守卫"
                          u"（原版只对 ServerPlayer 触发）")
        elif (_bg3_can_survive.find("player instanceof ServerPlayer")
              > _bg3_can_survive.find("CriteriaTriggers.PLACED_BLOCK.trigger(")):
            _bgfinal3_bad("bgfinal3-carrot-placed-block-trigger",
                          u"守卫写在触发**之后**（顺序反了）")
        if "held.shrink(1)" in _bg3_can_survive and (
                _bg3_can_survive.find("CriteriaTriggers.PLACED_BLOCK.trigger(")
                > _bg3_can_survive.find("held.shrink(1)")):
            _bgfinal3_bad("bgfinal3-carrot-placed-block-trigger",
                          u"触发写在 `held.shrink(1)` **之后**（原版是 trigger 在 consume 之前；"
                          u"stack 用手上那件）")
        if "trigger(serverPlayer, plantPos, held)" not in _bg3_can_survive:
            _bgfinal3_bad("bgfinal3-carrot-placed-block-trigger",
                          u"参数不对：必须是 `trigger(serverPlayer, plantPos, held)`"
                          u"（= 原版 `trigger(ServerPlayer, BlockPos, ItemStack)`）")

# ---------- ⑦-3 文档侧：§二十 的口径必须落档（含作者授权原话） ----------
for _needle, _why in ((u"bgfinal3", "docs/1.6-规格.md 里没有 bgfinal3 这一轮的节"),
                      (u"靛海金在这里", "没落档作者本次授权的**原话**"),
                      (u"任意一件", "没写手册改成了「任意一件」（改手册不改代码）"),
                      (u"PLACED_BLOCK", "没写金胡萝卜补的那次 placed_block 触发"),
                      (u"9c966b7f80c2e2550064a822730a704e8a68aeac9047fa9f1aabfda7eb9e6b6d",
                       "没写恢复后色卡的 SHA256 锚点")):
    if _needle not in _bgfix_spec:
        _bgfinal3_bad("bgfinal3-doc", u"%s（缺 %s）" % (_why, _needle))

# ==================== ⑧ bg-book §九 追加轮（2026-10-06 20:02）：「商人与古董」3 章 ====================
#
# 需求：`开工需求\20261004-1733_bg-book_patchouli-handbook.md` 的 **§九**（`最后更新` 10-06 20:02）。
# 三条口径（逐条有出处）：
#
#   ① **形状沿用 §八**：文档表格里**每一个行标签 = 一个 Patchouli 页**（相邻两页在书里组成一屏）；
#   ② 逐字文案 / 页眉 / 章节名的期望值来源 = **仓库内冻结快照**
#      `tools/asset-generator/bgappend-requirements-snapshot/bg-book-9.md`（**不读**仓库外活页）；
#   ③ 作者在 §9.4 第 1 页右写的「两种配方」+「六种器具的配方」= **8 个配方槽**，
#      而 Patchouli 的配方页**只有 recipe / recipe2 两个槽** ⇒ 门禁项，落成 **1 页 + 3 页**。
#
# ⚠ 本节还有 **1 组代码侧断言**（`[bgbook9-dust-*]`）：§9.7 是本轮**唯一**的行为要求
#   （父代理 2026-10-06 授权"最小改动实现"）——「古董工具挖下界合金块 / 贵金建材**不就地转换、
#   但尘埃照掉**」。完整判据见 `docs/1.6-规格.md` §21 与本关卡读的那份方法体。
bgbook9_problems: list[str] = []


def _bgbook9_bad(tag: str, msg: str) -> None:
    bgbook9_problems.append("%s [%s]" % (msg, tag))


_BG9_SNAPSHOT = _BG2_SNAPSHOT_DIR / "bg-book-9.md"
_BG9_LANG = "bettergold.handbook"
# (条目 id, 封面图标, sortnum, 页数, 页型序列)
_BG9_ENTRY_META = (
    ("merchant_intro", "gold_exchange_counter", 0, 3,
     ["patchouli:text", "patchouli:crafting", "patchouli:spotlight"]),
    ("merchant_gift_box", "treasure_gift_box", 1, 7,
     ["patchouli:text"] + ["patchouli:spotlight"] * 6),
    ("merchant_antique_gear", "netherite_antique_sword", 2, 10,
     ["patchouli:spotlight", "patchouli:smithing", "patchouli:smithing", "patchouli:smithing",
      "patchouli:smithing", "patchouli:spotlight", "patchouli:spotlight", "patchouli:text",
      "patchouli:crafting", "patchouli:text"]),
)
# 有**正文**的页（其余页要么是纯配方页、要么正文在别的页上）
_BG9_PROSE_SUFFIX = {
    "merchant_intro": ["1_left", "1_right", "2_left"],
    "merchant_gift_box": ["1_left", "1_right", "2_left", "2_right", "3_left", "3_right", "4_left"],
    "merchant_antique_gear": ["1_left", "2_left", "2_right", "3_left", "4_left"],
}
# 六件器具的**顺序**（§9.4 第 1 页左逐字：「剑/斧/镐/锹/锄/刀」）
_BG9_ANTIQUE_TRUE_ORDER = ["sword", "axe", "pickaxe", "shovel", "hoe", "knife"]
# 章3 第 1 页右的「两种配方」= 两份产物**同为 netherite_antique_upgrade_smithing_template** 的锻造配方
_BG9_TEMPLATE_RECIPES = ("smithing_template_antique", "smithing_template_echo_shard")
# 章3 第 3 页右：尘埃 → 小碎片；小碎片 → 碎片
_BG9_SCRAP_RECIPES = ("netherite_dust_to_small_scrap", "small_scrap_to_scrap")
# 章1 / 章2 / 章3 的 spotlight 图标表（逐页，None = 该页不是 spotlight）
_BG9_SPOTLIGHT_EXPECT = {
    "merchant_intro": [None, None, ["bettergold:gift_gold_ticket"]],
    "merchant_gift_box": [None,
                          ["bettergold:treasure_gift_box"], ["bettergold:curio_box"],
                          ["bettergold:unwanted_antique"], ["bettergold:idol_gift_box"],
                          ["bettergold:gourmet_box"], ["bettergold:alchemy_materials_box"]],
    "merchant_antique_gear": [
        ["bettergold:antique_%s" % _t for _t in _BG9_ANTIQUE_TRUE_ORDER], None, None, None, None,
        ["bettergold:netherite_antique_sword", "bettergold:netherite_antique_knife"],
        ["bettergold:netherite_antique_%s" % _t for _t in ("axe", "pickaxe", "shovel", "hoe")],
        None, None, None],
}
# 三张带页眉的页（作者写了「上边字体『…』」）—— 页眉也由**快照**解析出期望值
_BG9_TITLE_LABELS = {"merchant_antique_gear": ["1_left", "2_left", "2_right"]}

# ---------- 生成器覆盖（"每加一类东西问一句"）：常量必须一致 ----------
_BG9_GEN = _BGDOC_GEN
if not _BG9_GEN.is_file():
    _bgbook9_bad("bgbook9-generator", "读不到手册生成器：%s" % _BG9_GEN)
else:
    _bg9_gen_src = _BG9_GEN.read_text(encoding="utf-8")
    for _needle, _why in (
            ("MERCHANT_ENTRIES = [", "生成器里没有 §九 的 3 章清单（MERCHANT_ENTRIES）"),
            ("ANTIQUE_TRUE_ORDER = [", "生成器里没有章3 六件器具的顺序真源"),
            ("ANTIQUE_TEMPLATE_RECIPES = [", "生成器里没有章3「两种配方」的表"),
            ("ANTIQUE_SCRAP_RECIPES = [", "生成器里没有章3 尘埃/碎片配方表"),
            ("MERCHANT_GIFT_ROWS = [", "生成器里没有章2 的 7 行表"),
            ("RETIRED_ENTRIES = RETIRED_ENTRIES + [entry_merchant, entry_antiques]",
             "生成器没有把 §九 作废的两个旧占位并进 RETIRED_ENTRIES")):
        if _needle not in _bg9_gen_src:
            _bgbook9_bad("bgbook9-generator", _why)
    _bg9_m = re.search(r"^ANTIQUE_TRUE_ORDER = \[(.*?)\]", _bg9_gen_src, re.M)
    if not _bg9_m:
        _bgbook9_bad("bgbook9-generator", "读不到生成器的 ANTIQUE_TRUE_ORDER（反空转守护）")
    else:
        _bg9_order = re.findall(r'"([a-z]+)"', _bg9_m.group(1))
        if _bg9_order != _BG9_ANTIQUE_TRUE_ORDER:
            _bgbook9_bad("bgbook9-generator",
                         "生成器的六件器具顺序 %s 与本关卡的 %s 不一致（§9.4 第 1 页左逐字给出的是"
                         "剑/斧/镐/锹/锄/刀）" % (_bg9_order, _BG9_ANTIQUE_TRUE_ORDER))
    if len(_BG9_ANTIQUE_TRUE_ORDER) != 6:
        _bgbook9_bad("bgbook9-generator", "六件器具不是 6 件 —— 反空转守护")
    # 生成器里**不许**出现 §9.7 的代码侧判据（那是 `ModEvents` 的落点，不是数据生成器的）。
    # ⚠ 判据必须跑在**去掉 Python 注释**的源码上 —— 否则注释里提一句就会让这条假红
    #   （本轮扰动 P19「只加注释必须仍绿」实测抓到的就是这个形状；`strip_comments` 只认
    #   `//` 与 `/* */`，对 Python 的 `#` 无效，所以这里另剥一次）。
    _bg9_gen_nocomment = re.sub(r"#[^\n]*", "", _bg9_gen_src)
    if "isDustConversionExempt" in _bg9_gen_nocomment:
        _bgbook9_bad("bgbook9-generator",
                     "生成器里出现了 isDustConversionExempt（§9.7 是 **Java 侧**的判据，"
                     "不该跑进数据生成器）")

# ---------- ① 3 个条目：目录 / 图标 / sortnum / 页数 / 页型 / 正文键 / 图标表 / 配方逐条 ----------
_BG9_PAGES_TOTAL = 0
_BG9_RECIPE_REFS: set = set()
_BG9_SPOTLIGHT_REFS: set = set()
_BG9_TEXT_KEYS: list = []
for _eid, _icon, _sort, _cnt, _seq in _BG9_ENTRY_META:
    _zh_p = _ZH_BOOK / "entries" / ("%s.json" % _eid)
    _en_p = _EN_BOOK / "entries" / ("%s.json" % _eid)
    if not _zh_p.is_file() or not _en_p.is_file():
        _bgbook9_bad("bgbook9-chapters", "缺条目文件（zh/en 各需一份）：%s" % _eid)
        continue
    _zh_e = json.loads(_zh_p.read_text(encoding="utf-8"))
    _en_e = json.loads(_en_p.read_text(encoding="utf-8"))
    if _zh_e.get("category") != "bettergold:merchant_antiques":
        _bgbook9_bad("bgbook9-chapters",
                     "%s 不挂在「商人与古董」类别下：%r" % (_eid, _zh_e.get("category")))
    if _zh_e.get("name") != "%s.entry.%s" % (_BG9_LANG, _eid):
        _bgbook9_bad("bgbook9-chapters",
                     "%s 的 name 不是 %s.entry.%s" % (_eid, _BG9_LANG, _eid))
    if _zh_e.get("icon") != "bettergold:%s" % _icon:
        _bgbook9_bad("bgbook9-chapters",
                     "%s 的封面图标不是 bettergold:%s：%r" % (_eid, _icon, _zh_e.get("icon")))
    if _zh_e.get("sortnum") != _sort:
        _bgbook9_bad("bgbook9-chapters", "%s 的 sortnum 不是 %d" % (_eid, _sort))
    if _zh_e.get("pages") != _en_e.get("pages"):
        _bgbook9_bad("bgbook9-chapters", "%s 的 zh/en 页列表不一致（结构必须双端相同）" % _eid)
    _pages = _zh_e.get("pages") or []
    _BG9_PAGES_TOTAL += len(_pages)
    if len(_pages) != _cnt:
        _bgbook9_bad("bgbook9-chapters",
                     "%s 的页数不是 %d（章1 = 3 页；章2 = 7 页；章3 = 10 页 = 1 + 1 + 3 + 5）：%d"
                     % (_eid, _cnt, len(_pages)))
        continue
    _seq_now = [str(_p.get("type")) for _p in _pages]
    if _seq_now != _seq:
        _bgbook9_bad("bgbook9-page-types", "%s 的页型序列不是 %s：%s" % (_eid, _seq, _seq_now))
    for _i, _suffix in enumerate(_BG9_PROSE_SUFFIX[_eid]):
        _key = "%s.page.%s_%s" % (_BG9_LANG, _eid, _suffix)
        _BG9_TEXT_KEYS.append(_key)
        _pg_i = None
        for _n, _p in enumerate(_pages):
            if _p.get("text") == _key:
                _pg_i = _n
        if _pg_i is None:
            _bgbook9_bad("bgbook9-page-types",
                         "%s 的第 %d 个正文页（%s）没有引用 %s" % (_eid, _i + 1, _suffix, _key))
    for _n, _p in enumerate(_pages):
        for _overflow in ("recipe3", "recipe4", "recipes"):
            if _overflow in _p:
                _bgbook9_bad("bgbook9-page-types",
                             "%s 的页里出现 %s（Patchouli 只有 recipe / recipe2 两个槽）"
                             % (_eid, _overflow))
        if _p.get("type") not in _KNOWN_PAGE_TYPES:
            _bgbook9_bad("bgbook9-page-types", "%s 用了未知页面类型 %s" % (_eid, _p.get("type")))
        _want_items = _BG9_SPOTLIGHT_EXPECT[_eid][_n]
        if _want_items is not None:
            _it = _p.get("item")
            _got_items = [_it] if isinstance(_it, str) else list(_it or [])
            if _got_items != _want_items:
                _bgbook9_bad("bgbook9-icons",
                             "%s 第 %d 页的 spotlight 图标表不是 %s：%s"
                             % (_eid, _n + 1, _want_items, _got_items))
            for _one in _got_items:
                _BG9_SPOTLIGHT_REFS.add(str(_one))
        elif _p.get("type") == "patchouli:spotlight":
            _bgbook9_bad("bgbook9-icons",
                         "%s 第 %d 页多了一张没在 §九 里的 spotlight 图标表" % (_eid, _n + 1))
        for _rk in ("recipe", "recipe2"):          # 收集**实际**引用（死链检查用，别收集期望值）
            if isinstance(_p.get(_rk), str):
                _BG9_RECIPE_REFS.add(_p[_rk])

if _BG9_PAGES_TOTAL != 20:
    _bgbook9_bad("bgbook9-chapters",
                 "3 章合计页数不是 20（3 + 7 + 10）：%d —— 反空转守护" % _BG9_PAGES_TOTAL)

# ---------- ② 配方：逐页钉住（含门禁项的 1 + 3 落法） ----------
def _bg9_pages(eid: str) -> list:
    _p = _ZH_BOOK / "entries" / ("%s.json" % eid)
    if not _p.is_file():
        return []
    return json.loads(_p.read_text(encoding="utf-8")).get("pages") or []


_bg9_intro_pages = _bg9_pages("merchant_intro")
if len(_bg9_intro_pages) == 3:
    if _bg9_intro_pages[1].get("recipe") != "bettergold:gold_exchange_counter" \
            or "recipe2" in _bg9_intro_pages[1]:
        _bgbook9_bad("bgbook9-recipes",
                     "章1「（上边挂：易金柜台配方）」那一页不是单配方 gold_exchange_counter：%r"
                     % (_bg9_intro_pages[1],))

_bg9_antq_pages = _bg9_pages("merchant_antique_gear")
if len(_bg9_antq_pages) == 10:
    _want_tpl = ("bettergold:%s" % _BG9_TEMPLATE_RECIPES[0], "bettergold:%s" % _BG9_TEMPLATE_RECIPES[1])
    if (_bg9_antq_pages[1].get("recipe"), _bg9_antq_pages[1].get("recipe2")) != _want_tpl:
        _bgbook9_bad("bgbook9-recipes",
                     "章3 第 2 页不是「两种」升级模板配方 %s：%r" % (_want_tpl, _bg9_antq_pages[1]))
    for _i in range(0, 6, 2):
        _pg = _bg9_antq_pages[2 + _i // 2]
        _wa = "bettergold:upgrade_netherite_antique_%s" % _BG9_ANTIQUE_TRUE_ORDER[_i]
        _wb = "bettergold:upgrade_netherite_antique_%s" % _BG9_ANTIQUE_TRUE_ORDER[_i + 1]
        if (_pg.get("recipe"), _pg.get("recipe2")) != (_wa, _wb):
            _bgbook9_bad("bgbook9-recipes",
                         "章3 六件器具的升级配方顺序不对：第 %d 页期望 (%s, %s)，实际 %r"
                         % (_i // 2 + 1, _wa, _wb, _pg))
    _want_scrap = ("bettergold:%s" % _BG9_SCRAP_RECIPES[0], "bettergold:%s" % _BG9_SCRAP_RECIPES[1])
    if (_bg9_antq_pages[8].get("recipe"), _bg9_antq_pages[8].get("recipe2")) != _want_scrap:
        _bgbook9_bad("bgbook9-recipes",
                     "章3「尘埃 → 小碎片 / 小碎片 → 碎片」那一页不是 %s：%r"
                     % (_want_scrap, _bg9_antq_pages[8]))
if len(_BG9_RECIPE_REFS) != 11:
    _bgbook9_bad("bgbook9-recipes",
                 "§九 的配方引用不是 11 条（1 易金柜台 + 2 升级模板 + 6 器具升级 + 2 尘埃/碎片）：%d"
                 % len(_BG9_RECIPE_REFS))
_bg9_missing_recipes = sorted(
    _r for _r in _BG9_RECIPE_REFS
    if not (_DATA / "bettergold" / "recipe" / (_r.split(":", 1)[1] + ".json")).is_file())
if _bg9_missing_recipes:
    _bgbook9_bad("bgbook9-recipe-refs",
                 "§九 引用了不存在的配方（死链，游戏里那一页会空掉）：%s" % _bg9_missing_recipes[:5])
if len(_BG9_SPOTLIGHT_REFS) != 19:
    # 章1 1 + 章2 6 + 章3（6 + 2 + 4）= 19 个**互不重复**的图标引用；反空转守护
    _bgbook9_bad("bgbook9-icons",
                 "§九 的 spotlight 图标引用不是 19 个：%d —— 反空转守护" % len(_BG9_SPOTLIGHT_REFS))
_bg9_missing_items = sorted(
    _i for _i in _BG9_SPOTLIGHT_REFS
    if ("item.bettergold.%s" % _i.split(":", 1)[1]) not in zh
    and ("block.bettergold.%s" % _i.split(":", 1)[1]) not in zh)
if _bg9_missing_items:
    _bgbook9_bad("bgbook9-icons",
                 "§九 的 spotlight 引用了没有语言键的物品/方块（图标会取不到）：%s"
                 % _bg9_missing_items[:5])

# ---------- ③ 逐字文案 / 页眉 / 章节名：期望值来自**仓库内冻结快照** ----------
def _bg9_parse_snapshot() -> tuple:
    """从冻结快照解析 (章节 id, 章节名, [(页后缀, 逐字文案 or None, 页眉 or None)])。

    解析形状与本轮的语言键注入脚本**逐字同款**（改一处必须同步两处）。
    """
    _lines = _BG9_SNAPSHOT.read_text(encoding="utf-8").split("\n")
    _ids = {1: "merchant_intro", 2: "merchant_gift_box", 3: "merchant_antique_gear"}
    _suffix = {u"1 左": "1_left", u"1 右": "1_right", u"2 左": "2_left", u"2 右": "2_right",
               u"3 左": "3_left", u"3 右": "3_right", u"4 左": "4_left"}

    def _clean(_c: str) -> str:
        _c = _c.split(u"<br>⚠")[0]        # 设计会话的批注（§9.3 第2页右）
        return re.sub(r"\*\*(.+?)\*\*", r"\1", _c).strip()

    def _prose(_c: str):
        _b = _clean(_c)
        if _b.startswith(u"（"):
            _cut = _b.find(u"）")
            if _cut >= 0:
                _b = _b[_cut + 1:].strip()
        if not _b or _b.startswith((u"上：", u"下：", u"放出")):
            return None
        return _b

    _out, _cur, _name, _rows = [], None, None, []

    def _flush():
        if _cur:
            _out.append((_cur, _name, list(_rows)))

    for _ln in _lines:
        _m = re.match(r"^#### 9\.\d 章节 (\d) · (.+?)(（封面：.*）)?$", _ln)
        if _m:
            _flush()
            _cur, _name, _rows = _ids[int(_m.group(1))], _m.group(2).strip(), []
            continue
        if _ln.startswith("#### ") or _ln.startswith("## "):
            _flush()
            _cur, _name, _rows = None, None, []
            continue
        if not _ln.startswith("|") or "|---" in _ln:
            continue
        _safe = _ln.replace("\\|", "\x01")
        _cells = [_c.replace("\x01", "|") for _c in _safe.split("|")[1:-1]]
        if len(_cells) < 2:
            continue
        _label = _cells[0].strip().replace("*", "")
        if _label in _suffix:
            _tm = re.search(u"上边字体「(.+?)」", _cells[1])
            _rows.append((_suffix[_label], _prose(_cells[1]),
                          _tm.group(1) if _tm else None))
    _flush()
    return _out


if not _BG9_SNAPSHOT.is_file():
    _bgbook9_bad("bgbook9-texts-verbatim", "读不到冻结快照（逐字文案的期望值来源）：%s" % _BG9_SNAPSHOT)
else:
    _bg9_parsed = _bg9_parse_snapshot()
    if len(_bg9_parsed) != 3:
        _bgbook9_bad("bgbook9-texts-verbatim",
                     "从冻结快照解析到 %d 章（应 3 = 关于易金商人 / 礼品盒 / 古董器具；反空转守护）"
                     % len(_bg9_parsed))
    _bg9_texts, _bg9_titles, _bg9_names = [], [], []
    for _eid, _name, _rows in _bg9_parsed:
        _bg9_names.append(_name)
        _nk = "%s.entry.%s" % (_BG9_LANG, _eid)
        if zh.get(_nk) != _name:
            _bgbook9_bad("bgbook9-texts-verbatim",
                         "快照里的章节名 %r 没有按原样落在 %s 里（实际 %r）" % (_name, _nk, zh.get(_nk)))
        _want_labels = _BG9_PROSE_SUFFIX.get(_eid, [])
        for _suffix, _p, _t in _rows:
            if _p is not None:
                if _suffix not in _want_labels:
                    _bgbook9_bad("bgbook9-texts-verbatim",
                                 "%s 的快照里多出一页正文（%s）—— 与本关卡的页表不符" % (_eid, _suffix))
                _k = "%s.page.%s_%s" % (_BG9_LANG, _eid, _suffix)
                _bg9_texts.append(_p)
                if zh.get(_k) != _p:
                    _bgbook9_bad("bgbook9-texts-verbatim",
                                 "快照里的逐字文案没有按原样落在 %s 里（首 30 字：%s）" % (_k, _p[:30]))
            if _t is not None:
                _tk = "%s.page.%s_%s_title" % (_BG9_LANG, _eid, _suffix)
                _bg9_titles.append(_t)
                if zh.get(_tk) != _t:
                    _bgbook9_bad("bgbook9-texts-verbatim",
                                 "快照里的页眉 %r 没有按原样落在 %s 里（实际 %r）"
                                 % (_t, _tk, zh.get(_tk)))
    if len(_bg9_texts) != 15 or sum(len(_t) for _t in _bg9_texts) < 600:
        _bgbook9_bad("bgbook9-texts-verbatim",
                     "从冻结快照解析到 %d 段逐字文案 / 共 %d 字（应 15 段 = 3 + 7 + 5、"
                     "总字数 >= 600；反空转守护）"
                     % (len(_bg9_texts), sum(len(_t) for _t in _bg9_texts)))
    if len(_bg9_titles) != 3 or _bg9_titles != [u"古董武器工具", u"下界合金古董武器", u"下界合金古董工具"]:
        _bgbook9_bad("bgbook9-texts-verbatim",
                     "从冻结快照解析到的页眉不是那三条「上边字体『…』」：%r" % (_bg9_titles,))
    _bg9_missing_texts = [_t for _t in _bg9_texts if _t not in set(zh.values())]
    if _bg9_missing_texts:
        _bgbook9_bad("bgbook9-texts-verbatim",
                     "冻结快照里的逐字文案没有原样出现在 zh_cn.json 里（%d/%d 段缺失，首条：%s）"
                     % (len(_bg9_missing_texts), len(_bg9_texts), _bg9_missing_texts[0][:40]))
    # ⚠ **待作者补原文**：§9.3 第 2 页右那处**空引号**（文档里写成 `〔待补〕` 占位）
    #   ⇒ 本轮**不自行编文案**，逐字把占位落进语言文件，并在这里**钉住它仍然存在**
    #   （谁把它填成自己编的章节名，这条就当场红）—— 口径写进 `docs/1.6-规格.md` §21。
    _BG9_PLACEHOLDER = u"〔待补〕"
    _bg9_todo_key = "%s.page.merchant_gift_box_2_right" % _BG9_LANG
    if _BG9_PLACEHOLDER not in (zh.get(_bg9_todo_key) or ""):
        _bgbook9_bad("bgbook9-todo-placeholder",
                     "空引号那一处（%s）里的占位 %r 不见了 —— 作者还没补原文，"
                     "不许自己编章节名（口径见 §21）" % (_bg9_todo_key, _BG9_PLACEHOLDER))
    if _BG9_PLACEHOLDER not in _BG9_SNAPSHOT.read_text(encoding="utf-8"):
        _bgbook9_bad("bgbook9-todo-placeholder",
                     "冻结快照里也没有占位 %r ⇒ 快照被改写成了作者没给过的文案" % _BG9_PLACEHOLDER)
    if u"待作者补原文" not in _bgfix_spec:
        _bgbook9_bad("bgbook9-todo-placeholder",
                     "docs/1.6-规格.md 没写明那一处是**待作者补原文**")
    # 语言键：3 条目名 + 15 正文 + 3 页眉 = **21** 条，中英双端都要有（en 不许等于 zh / 不许为空）
    _bg9_keys = (["%s.entry.%s" % (_BG9_LANG, _e) for _e, _i, _s, _c, _q in _BG9_ENTRY_META]
                 + list(_BG9_TEXT_KEYS)
                 + ["%s.page.%s_%s_title" % (_BG9_LANG, _e, _l)
                    for _e, _ls in _BG9_TITLE_LABELS.items() for _l in _ls])
    if len(_bg9_keys) != 21:
        _bgbook9_bad("bgbook9-lang-bilingual",
                     "§九 的语言键清单是 %d 条（应 21 = 3 + 15 + 3；反空转守护）" % len(_bg9_keys))
    for _k in _bg9_keys:
        if _k not in zh or _k not in en:
            _bgbook9_bad("bgbook9-lang-bilingual", "§九 语言键缺中文或英文：%s" % _k)
        elif not en[_k].strip() or en[_k] == zh[_k]:
            _bgbook9_bad("bgbook9-lang-bilingual",
                         "§九 的英文值缺失或与中文逐字相同（作者只给了中文，需要忠实英译）：%s" % _k)
    # ⚠ 值级更正**只有一处**（§9.2 第 2 页左的「主要货币」，依据 VillageTrades:49-50）：
    #   旧口径不许出现在语言文件里，但**必须**留在快照的《快照搬运记录》里（原文不删）。
    _BG9_OLD_EMERALD = u"易金商人的支出与支入的货币并不是绿宝石"
    if _BG9_OLD_EMERALD in set(zh.values()):
        _bgbook9_bad("bgbook9-texts-verbatim",
                     "值级更正前的旧口径 %r 还在 zh_cn.json 里（应只留在快照的搬运记录里）"
                     % _BG9_OLD_EMERALD)
    _bg9_snap_all = _BG9_SNAPSHOT.read_text(encoding="utf-8")
    if _BG9_OLD_EMERALD not in _bg9_snap_all:
        _bgbook9_bad("bgbook9-texts-verbatim",
                     "旧口径原文 %r 没有留在快照里（既定口径：原文不删）" % _BG9_OLD_EMERALD)
    # ⚠ **被退回的那次改写**（§9.3 第 1 页右："不会开出锻造模板 / 不联通第三方"那两句）：
    #   本轮第一版按父代理口令改成了「并不能保证避开锻造模板…」，**随后被本轮的 A 级实测推翻前提**
    #   （探针开 2000 次万宝礼物盒 ⇒ `smithing_templates=0`）⇒ 现行值 = **作者原文**。
    #   三条判据：① 正文必须是作者原文；② **快照正文**里不许再出现被退回的那版；
    #   ③ 被退回的那版**必须**留在快照的《快照搬运记录》里（原文不删 + 全过程记账）。
    _BG9_AUTHOR_TEMPLATE = u"不会在该礼品盒内开出锻造模板"
    _BG9_REVERTED_TEMPLATE = u"并不能保证避开锻造模板"
    if _BG9_AUTHOR_TEMPLATE not in (zh.get("%s.page.merchant_gift_box_1_right" % _BG9_LANG) or ""):
        _bgbook9_bad("bgbook9-texts-verbatim",
                     "手册里「不会在该礼品盒内开出锻造模板」那句不是**作者原文**了"
                     "（本轮已按 A 级实测 0/2000 回退，见 §21.3 第 2/3 条）")
    _bg9_snap_body = _bg9_snap_all.split(u"## 快照搬运记录")[0]
    if not _bg9_snap_body:
        _bgbook9_bad("bgbook9-texts-verbatim", "快照里找不到《快照搬运记录》分界（反空转守护）")
    elif _BG9_REVERTED_TEMPLATE in _bg9_snap_body:
        _bgbook9_bad("bgbook9-texts-verbatim",
                     "快照正文里还是那版**被退回的改写**「%s」（现行值必须是作者原文）"
                     % _BG9_REVERTED_TEMPLATE)
    if _BG9_REVERTED_TEMPLATE not in _bg9_snap_all:
        _bgbook9_bad("bgbook9-texts-verbatim",
                     "被退回的那版改写没有留在快照的《快照搬运记录》里"
                     "（口径：改了又退回也要原文不删 + 记账）")

# ---------- ④ 代码侧（§9.7，本轮唯一的行为要求）：古董工具挖「下界合金块 / 贵金建材」**只掉尘埃、不转换** ----------
_bg9_blockdrops = method_body(_bgfix_mod, "public static void onBlockDrops(")
if not _bg9_blockdrops:
    _bgbook9_bad("bgbook9-dust-convert-exempt", "找不到 onBlockDrops 方法体（反空转守护）")
else:
    # ⚠ `clear()` 在 onBlockDrops 里有**两**处是**正确**的：① 远古残骸那条（镐 + 远古残骸 ⇒
    #   1~3 碎片，**不受 §9.7 影响**、保持无条件）；② 尘埃那条（本轮被例外集合守卫包住）。
    #   ⇒ 判据写成"恰好 2 处 + 其中**恰好 1 处**被 `if (!conversionExempt)` 守卫"。
    if _bg9_blockdrops.count("event.getDrops().clear();") != 2:
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "onBlockDrops 里 `event.getDrops().clear();` 不是恰好 2 处（远古残骸那条 + 尘埃那条；"
                     "实际 %d）" % _bg9_blockdrops.count("event.getDrops().clear();"))
    _bg9_guarded = re.findall(r"if \(!conversionExempt\) \{\s*event\.getDrops\(\)\.clear\(\);",
                              _bg9_blockdrops)
    if len(_bg9_guarded) != 1:
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "被 `if (!conversionExempt)` 守卫的 `clear()` 不是恰好 1 处（实际 %d）⇒ 要么"
                     "下界合金块 / 贵金建材**仍会被就地转换**（§9.7 的 ① 没关掉），要么把远古残骸"
                     "那条也一起关掉了" % len(_bg9_guarded))
    if "isDustConversionExempt(event.getState())" not in _bg9_blockdrops:
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "onBlockDrops 没有按**方块状态**判例外集合（必须 `event.getState()`）")
    if "new ItemStack(AllItems.NETHERITE_DUST.get(), count)" not in _bg9_blockdrops:
        _bgbook9_bad("bgbook9-dust-extra-drop",
                     "尘埃那一行不见了 ⇒ §9.7 的 ② 「尘埃该掉落还是会掉落」被一起关掉了")
    for _needle, _why in (("float chance = 0.06F + 0.06F * fortune;",
                           "概率公式被改了（应是 0.06 + 0.06×时运）"),
                          ("int count = 1 + fortune / 2;",
                           "数量公式被改了（应是 1 + 时运/2）"),
                          ("Blocks.ANCIENT_DEBRIS",
                           "黄泉引骸镐的「远古残骸 → 1~3 碎片」那条不见了（它不受 §9.7 影响）"),
                          ("random.nextFloat() < chance && !event.getDrops().isEmpty()",
                           "判定式被改了（§9.7 只许动 `clear()` 那两行，判定 / 随机数序列不许动）")):
        if _needle not in _bg9_blockdrops:
            _bgbook9_bad("bgbook9-dust-convert-exempt", _why)
_bg9_exempt = method_body(_bgfix_mod, "private static boolean isDustConversionExempt(")
if not _bg9_exempt:
    _bgbook9_bad("bgbook9-dust-convert-exempt", "找不到 isDustConversionExempt 方法体（反空转守护）")
else:
    if "Blocks.NETHERITE_BLOCK" not in _bg9_exempt:
        _bgbook9_bad("bgbook9-dust-convert-exempt", "例外集合里没有「下界合金块」")
    if "MetalFamily.of(state.getBlock()) != null" not in _bg9_exempt:
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "例外集合没有走 `MetalFamily.of(block)` 的**家族索引**"
                     "（= 八族建材；写死清单会漏项 —— AGENTS 红线 2 的同一种形态）")
    for _banned in ("_bricks", "_bricks_stairs", "_lantern", "_trapdoor", "_bars"):
        if _banned in _bg9_exempt:
            _bgbook9_bad("bgbook9-dust-convert-exempt",
                         "例外集合里出现了写死的方块名后缀 %r ⇒ 以后加一族金属 / 加一种形态就会漏"
                         % _banned)
# 跨文件不变量：家族索引覆盖的正是**11 种形态**（§9.8 推断值 3 的那张清单）
_bg9_mf_src = strip_comments((JAVA / "material" / "MetalFamily.java").read_text(encoding="utf-8"))
_bg9_allblocks = re.search(r"this\.allBlocks = List\.of\((.*?)\);", _bg9_mf_src, re.S)
if not _bg9_allblocks:
    _bgbook9_bad("bgbook9-dust-convert-exempt", "读不到 MetalFamily 的 allBlocks 清单（反空转守护）")
else:
    _bg9_forms = re.findall(r"this\.(\w+)", _bg9_allblocks.group(1))
    if len(_bg9_forms) != 11:
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "MetalFamily.allBlocks 不是 11 种形态（实际 %d：%s）—— §9.7 的例外集合"
                     "＝八族建材×11，形态数变了本关卡要跟着改" % (len(_bg9_forms), _bg9_forms))

# ---------- ⑤ 文档侧：§九 的口径必须落档 ----------
for _needle, _why in ((u"bg-book §九", "docs/1.6-规格.md 里没有 bg-book §九 这一轮的节"),
                      (u"待作者补原文", "没写明空引号那一处**待作者补原文**"),
                      (u"不就地转换", "没写 §9.7 的新行为要求（不就地转换）"),
                      (u"以实际为准", "没写明十二条核对的处置口径（以实际为准 + 代码侧待办）"),
                      (u"代码侧待办", "没列代码侧待办"),
                      (u"锻造模板", "没写「万宝礼物盒不过滤锻造模板」这条**代码侧待办**")):
    if _needle not in _bgfix_spec:
        _bgbook9_bad("bgbook9-doc", "%s（缺 %s）" % (_why, _needle))

# ==================== bg-fix3（2026-10-07）：六条修正（第三批）====================
#
# 本段只放"跨文件 / 文档落档"这一类判据（产物侧的判据在 `validate_advancements.py`
# 与上面的 bg-book 段里；生成器侧的作废守卫在 `bgfix3-generator-retired`）。
bgfix3_problems: list[str] = []


def _bgfix3_bad(tag: str, msg: str) -> None:
    bgfix3_problems.append("%s [%s]" % (msg, tag))


# ---------- ① 新标签的"可选条目"机制本身必须还在生成器里（唯一真源） ----------
#   ⚠ 第一版这里假定"计划表是一张 8 键字面量字典"，于是用正则数键数 ⇒ 实际生成器是
#     **按 `ALL_METALS` 循环**填表的（`OPTIONAL_ITEM_TAG_VALUES["%s_knives" % _m] = [...]`）
#     ⇒ 数出 0 张、**假红**。改成：源码侧只钉"那几行字面量还在"，**张数由产物侧数**（下面）。
_bgfix3_tags_src = strip_comments(
    (Path(__file__).resolve().parent / "generate_metal_tags.py").read_text(encoding="utf-8"))
for _needle, _why in (
        ("OPTIONAL_ITEM_TAG_VALUES", "标签生成器里没有 `OPTIONAL_ITEM_TAG_VALUES` 这张计划表"),
        ('"%s_knives" % _m', "计划表里没有按族生成的 `<族>_knives` 标签"),
        ('"handbook"', "计划表里没有 `handbook` 标签（root 改「获得」靠的就是它）"),
        ('"required": False', "可选条目没有写成 `\"required\": false`（没装可选模组时整条标签会被丢弃）"),
        ("for _m in ALL_METALS", "刀标签不是按 8 族循环生成的（写死清单会漏族 —— AGENTS 红线 2）")):
    if _needle not in _bgfix3_tags_src:
        _bgfix3_bad("bgfix3-tag-generator", "%s（缺 %s）" % (_why, _needle))

# 产物侧：9 张"可选条目标签"必须在，且每张**恰好 1 条** value 写成 `required: false`
_bgfix3_tag_dir = _DATA / "bettergold" / "tags" / "item"
_bgfix3_tag_paths = sorted(_bgfix3_tag_dir.glob("*_knives.json")) + \
                    [_bgfix3_tag_dir / "handbook.json"]
if len(_bgfix3_tag_paths) != 9:
    _bgfix3_bad("bgfix3-tag-generator",
                "可选条目标签文件不是 9 张（8 族刀 + handbook），实际 %d：%s"
                % (len(_bgfix3_tag_paths), [p.name for p in _bgfix3_tag_paths]))
for _tp in _bgfix3_tag_paths:
    if not _tp.is_file():
        _bgfix3_bad("bgfix3-tag-generator", "缺标签文件 %s" % _tp.name)
        continue
    _tobj = json.loads(_tp.read_text(encoding="utf-8"))
    _tvals = _tobj.get("values") or []
    if len(_tvals) != 1 or not isinstance(_tvals[0], dict) \
            or _tvals[0].get("required") is not False:
        _bgfix3_bad("bgfix3-tag-generator",
                    "%s 的 values 不是「恰好 1 条 {\"id\": …, \"required\": false}」：%s"
                    % (_tp.name, _tvals))

# ---------- ② 文档侧：§二十二 的口径必须落档 ----------
_bgfix3_spec = (REPO / "docs" / "1.6-规格.md").read_text(encoding="utf-8")
for _needle, _why in (
        ("bg-fix3", "docs/1.6-规格.md 里没有 bg-fix3 节"),
        ("贵金的材料链", "没写手册被删掉的那两节名（贵金的材料链）"),
        ("升级锻造模板", "没写手册被删掉的那两节名（升级锻造模板）"),
        ("have_knife", "没写乐事小刀的落法（have_knife 判据）"),
        ("#bettergold:handbook", "没写 root 改「获得」的标签落法"),
        ('"required": false', "没写 required:false 这条机制（没装可选模组时不报错）"),
        ("链式", "没写根链改链式这条口径"),
        ("旧口径", "没写旧口径就地标注的位置")):
    if _needle not in _bgfix3_spec:
        _bgfix3_bad("bgfix3-doc", "%s（缺 %s）" % (_why, _needle))

print(f"bgfinal3 三条裁定（靛海金文档口径 / 手册任意一件 / 金胡萝卜 placed_block）问题: "
      f"{len(bgfinal3_problems)} {bgfinal3_problems[:8]}")
print(f"bg-16 两处修正（横幅落点 / 安抚对玩家）问题: {len(bg16_problems)} {bg16_problems[:8]}")
print(f"bg-book 帕秋莉手册问题: {len(bgbook_problems)} {bgbook_problems[:8]}"
      f"（手册 {len(_entries_now)} 条目 / {_total_pages} 页 / {len(_recipe_refs)} 条配方引用）")
print(f"bg-book §六 追加轮（三章逐页补全）问题: {len(bgbook2_problems)} {bgbook2_problems[:8]}"
      f"（三章 {_bg2_pages_total} 页 / {len(_bg2_recipe_refs)} 条配方引用 / {len(_bg2_item_refs)} 个图标引用）")
print(f"bg-append 追加轮（手册七处修正 / 声波音效 / 配置汉化 / 金玫瑰丛）问题: "
      f"{len(bgappend_problems)} {bgappend_problems[:8]}")
print(f"bg-fix 1.6 七条修正问题: {len(bgfix_problems)} {bgfix_problems[:8]}")
print(f"bg-final 1.6 收尾三件（声波击退 / 成就英译 / 高燃 1 级不点燃）问题: "
      f"{len(bgfinal_problems)} {bgfinal_problems[:8]}")
print(f"bg-fix2 六条未生效复报（色卡取证 / 声波解耦 / 藤条 / 金骨粉 / 高燃沉淀 / 成就）问题: "
      f"{len(bgfix2_problems)} {bgfix2_problems[:8]}")
print(f"bg-book §八 追加轮（「装备的强化」9 章 / 类别改名 / 巫毒整套免疫中毒）问题: "
      f"{len(bgbook8_problems)} {bgbook8_problems[:8]}"
      f"（9 章 {_BG8_PAGES_TOTAL} 页 / 锻造引用 {len(_BG8_FORGE_REFS)} 条 / 胚底引用 {len(_BG8_BLANK_REFS)} 条）")
print(f"bg-book §九 追加轮（「商人与古董」3 章 / §9.7 不就地转换 / 空引号占位）问题: "
      f"{len(bgbook9_problems)} {bgbook9_problems[:8]}"
      f"（3 章 {_BG9_PAGES_TOTAL} 页 / 配方引用 {len(_BG9_RECIPE_REFS)} 条 / 图标引用 {len(_BG9_SPOTLIGHT_REFS)} 个）")
print(f"bg-fix3 六条修正（藤条判据 / 乐事刀 / 手册删两节 / root 改获得 / 排版 / 标签机制）问题: "
      f"{len(bgfix3_problems)} {bgfix3_problems[:8]}")

sys.exit(1 if (missing_zh or missing_en or missing_loot or missing_knife_tags or missing_weapon_tags
               or bg15w_problems or bg8_problems or bg9_problems
               or bg16_problems or bgbook_problems or bgbook2_problems or bgfix_problems
               or bgfinal_problems or bgappend_problems or bgfix2_problems or bgbook8_problems
               or bgfinal3_problems or bgbook9_problems or bgfix3_problems
               or symmetric_problems or beacon_problems) else 0)
