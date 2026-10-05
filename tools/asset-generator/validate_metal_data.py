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
_EXPECT_TOOL_PAGES = 1 + len(ALL_METALS) * 3   # 1 页开场文字 + 六件器具 ÷ 每页 2 个 = 3 页/套
_EXPECT_ARMOR_PAGES = 1 + len(ALL_METALS) * 2  # 1 页开场文字 + 四件盔甲 ÷ 每页 2 个 = 2 页/套
_entries_now = {}
for _p in sorted((_ZH_BOOK / "entries").glob("*.json")) if (_ZH_BOOK / "entries").is_dir() else []:
    _entries_now[_p.stem] = json.loads(_p.read_text(encoding="utf-8"))
_SKELETON_ENTRIES = ("metal_tour", "upgrade_templates", "tools_per_family",
                     "armor_per_family", "golden_feast", "merchant", "antiques")
# bg-book §六 追加轮（2026-10-05）：三章（副要材料 / 核心材料 / 知识）
_BG2_ENTRY_NAMES = ("auxiliary_materials", "core_materials", "golden_knowledge")
_missing_skeleton = [n for n in _SKELETON_ENTRIES if n not in _entries_now]
if _missing_skeleton:
    _bgbook_bad("bgbook-entry-count",
                "第一轮的骨架条目被删掉了（追加轮只许新增）：%s" % _missing_skeleton)
if len(_entries_now) != len(_SKELETON_ENTRIES) + len(_BG2_ENTRY_NAMES):
    _bgbook_bad("bgbook-entry-count",
                "条目数应为 %d（骨架 7 + §六 章节 3），实际 %d"
                % (len(_SKELETON_ENTRIES) + len(_BG2_ENTRY_NAMES), len(_entries_now)))
for _entry, _expect in (("tools_per_family", _EXPECT_TOOL_PAGES), ("armor_per_family", _EXPECT_ARMOR_PAGES)):
    _got = len(_entries_now.get(_entry, {}).get("pages", []))
    if _got != _expect:
        _bgbook_bad("bgbook-pages-per-family",
                    "条目 %s 的页数 %d != 金属套数 × %d = %d"
                    "（每页 2 个配方是 Patchouli 的结构上限；加金属时这里与生成器一起红）"
                    % (_entry, _got, _expect // len(ALL_METALS), _expect))
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
if _total_pages < 60:
    _bgbook_bad("bgbook-anti-vacuum",
                "手册总页数只有 %d（骨架应 ≥ 60 页；数据树被清空会命中这条）" % _total_pages)
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
# 章 → (封面图标, sortnum, 页型序列)。页型序列就是"一行 = 左页 + 右页"的机器形态。
_BG2_CHAPTERS = {
    "auxiliary_materials": ("mixed_crystal_pile", 2,
                            ["patchouli:spotlight", "patchouli:crafting"] * 2),
    "core_materials": ("golden_cowrie", 3,
                       ["patchouli:text", "patchouli:spotlight"]
                       + ["patchouli:spotlight", "patchouli:crafting"] * 8),
    "golden_knowledge": ("sturdygold_ingot", 4,
                         ["patchouli:spotlight", "patchouli:spotlight"] * 5),
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
if _bg2_pages_total != 32:
    _bgbook2_bad("bgbook2-chapter-pages",
                 "三章合计应是 32 个 Patchouli 页（= 文档 2+9+5 = 16 行 × 2），实际 %d" % _bg2_pages_total)
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
if len(_bg2_item_refs) < 40:
    _bgbook2_bad("bgbook2-item-refs",
                 "三章只解析到 %d 个图标引用（应 43；反空转守护）" % len(_bg2_item_refs))

# 逐字文案：**期望值来自需求文档**（不是本脚本自己的表 —— 否则就是 §4 第 42 条那种空转）
if not _BG2_REQ_DOC.is_file():
    _bgbook2_bad("bgbook2-texts-verbatim", "读不到需求文档（逐字文案的期望值来源）：%s" % _BG2_REQ_DOC)
else:
    _bg2_lines = _BG2_REQ_DOC.read_text(encoding="utf-8").split("\n")

    def _bg2_rows(marker: str) -> list[list[str]]:
        out, active = [], False
        for _ln in _bg2_lines:
            if _ln.startswith(marker):
                active = True
                continue
            if active and _ln.startswith("### "):
                break
            if active and _ln.startswith("|") and "|---" not in _ln and "页" not in _ln.split("|")[1]:
                out.append([_c for _c in _ln.split("|")][1:-1])
        return out

    def _bg2_clean(_cell: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*", r"\1", _cell.strip()).strip()

    _bg2_texts = [_bg2_clean(_r[1]) for _r in _bg2_rows("### 6.1")]
    for _i, _r in enumerate(_bg2_rows("### 6.2"), start=1):
        _bg2_texts.append(_bg2_clean(_r[2]))
        if _i == 1:
            _bg2_texts.append(_bg2_clean(re.sub(r"^\s*\*\*右侧正文\*\*：", "", _r[3].split("<br>")[-1])))
    for _r in _bg2_rows("### 6.3"):
        for _col in (1, 2):
            _bg2_texts.append(_bg2_clean(_r[_col].split("<br>")[-1]))
    if len(_bg2_texts) != 22 or sum(len(_t) for _t in _bg2_texts) < 600:
        _bgbook2_bad("bgbook2-texts-verbatim",
                     "从需求文档解析到 %d 段逐字文案 / 共 %d 字（应 22 段、总字数 >= 600；反空转守护）"
                     % (len(_bg2_texts), sum(len(_t) for _t in _bg2_texts)))
    _zh_values = set(zh.values())
    _bg2_missing_texts = [_t for _t in _bg2_texts if _t not in _zh_values]
    if _bg2_missing_texts:
        _bgbook2_bad("bgbook2-texts-verbatim",
                     "需求文档里的逐字文案没有原样出现在 zh_cn.json 里（%d/%d 段缺失，首条：%s）"
                     % (len(_bg2_missing_texts), len(_bg2_texts), _bg2_missing_texts[0][:40]))

# 语言键：25 条（3 个条目名 + 22 段文案）必须**中英双端都有**
_bg2_suffixes = (["aux_1", "aux_2"]
                 + ["core_%d" % _i for _i in range(1, 10)] + ["core_1_right"]
                 + ["knowledge_%d_%s" % (_i, _s) for _i in range(1, 6) for _s in ("left", "right")])
_bg2_keys = (["bettergold.handbook.entry.%s" % _c for _c in _BG2_CHAPTERS]
             + ["bettergold.handbook.page.%s" % _s for _s in _bg2_suffixes])
if len(_bg2_keys) != 25:
    _bgbook2_bad("bgbook2-lang-bilingual",
                 "章节语言键清单是 %d 条（应 25 = 3 + 22；反空转守护）" % len(_bg2_keys))
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
if "public static float shiftedDamage(int amplifier)" not in _bgfix_fx:
    _bgfix_bad("bgfix-shifted-damage-impl", "AllEffects 里没有 shiftedDamage(int)（公式不是唯一实现）")
elif "return Math.max(0, amplifier);" not in _bgfix_fx:
    _bgfix_bad("bgfix-shifted-damage-impl", "shiftedDamage 的实现不是 max(0, amplifier)")
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
if not _shifted_body or "Math.max(0, amplifier)" not in _shifted_body:
    _bgfinal_bad("bgfinal-highburn-body",
                 "shiftedDamage 不是 `Math.max(0, amplifier)`（1 级 = 0 点的唯一真源）")
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

print(f"bg-16 两处修正（横幅落点 / 安抚对玩家）问题: {len(bg16_problems)} {bg16_problems[:8]}")
print(f"bg-book 帕秋莉手册问题: {len(bgbook_problems)} {bgbook_problems[:8]}"
      f"（手册 {len(_entries_now)} 条目 / {_total_pages} 页 / {len(_recipe_refs)} 条配方引用）")
print(f"bg-book §六 追加轮（三章逐页补全）问题: {len(bgbook2_problems)} {bgbook2_problems[:8]}"
      f"（三章 {_bg2_pages_total} 页 / {len(_bg2_recipe_refs)} 条配方引用 / {len(_bg2_item_refs)} 个图标引用）")
print(f"bg-fix 1.6 七条修正问题: {len(bgfix_problems)} {bgfix_problems[:8]}")
print(f"bg-final 1.6 收尾三件（声波击退 / 成就英译 / 高燃 1 级不点燃）问题: "
      f"{len(bgfinal_problems)} {bgfinal_problems[:8]}")

sys.exit(1 if (missing_zh or missing_en or missing_loot or missing_knife_tags or missing_weapon_tags
               or bg15w_problems or bg8_problems or bg9_problems
               or bg16_problems or bgbook_problems or bgbook2_problems or bgfix_problems
               or bgfinal_problems
               or symmetric_problems or beacon_problems) else 0)
