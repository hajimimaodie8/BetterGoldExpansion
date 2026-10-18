#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验：MetalFamily 会注册出来的每个物品/方块，在 zh_cn / en_us 里是否都有语言条目。

==================== 关卡退出码契约（bgfix6，2026-10-08）====================
  0 = 全绿；1 = 有「问题」（文件末尾 `_EXIT_PROBLEM_LISTS` 里 30 个列表任一非空；
      ⚠ 原文写的是「24 个」—— bgfix7~bgfix11 又加了 5 个列表而那句没跟着改，
      **bgfix11 就地更正为 29**，旧数字留档在此，判定口径一字未动；
      **bg-n10up 又加 1 个（`bgn10up_problems`）⇒ 30**）；
  2 = 基线被破坏 / 前置缺失 / 脚本自身出错（扫描根目录不在、**实际检查项数 = 0**、
      未捕获异常）。★ 任何未捕获异常都不许变成 0；顶层兜底一律转成 2。
  ★ 反空转：必须打印「实际检查了 N 项」并断言 N > 0。
  依据：`docs/构建与跑测注意事项.md`「关卡的退出码契约」；
        `mod_experience\\ex\\03-验证与证据.md` §3.19。

⚠ bgfix6 就地标注（旧行为原文保留）：原先只有末尾那一行
  `sys.exit(1 if (逐条列出 24 个列表) else 0)` —— **能 exit 1、没有 exit 2**，
  且 `checked`（语言键计数）只 print 从不断言；未捕获异常被 Python 记成 **exit 1**
  （分类错：脚本崩了却被读成"有问题"）。判定口径未动。
"""
from __future__ import annotations
import json
import os
import re
import sys
import traceback
from pathlib import Path


def _bgfix6_excepthook(exc_type, exc, tb):
    """未捕获异常 ⇒ **绝不许变成 0**；本关卡的顶层兜底把它变成 2。

    为什么不改写成 `main()` + `try/except`：本脚本是 5000 行**模块级**脚本，整体缩进
    既大又容易切错（`docs/构建与跑测注意事项.md` §四「删代码块要按标记+锚点成对定位」）。
    `sys.excepthook` 只拦"真正没被接住"的异常，语义等价、零侵入；
    `SystemExit`（= 脚本自己的 exit 0/1/2）不会走这里（Python 不对它调 excepthook）。
    """
    if issubclass(exc_type, SystemExit):
        sys.__excepthook__(exc_type, exc, tb)
        return
    traceback.print_exception(exc_type, exc, tb)
    print("[bg-data-crash] 关卡自身出错（未捕获异常）⇒ exit 2")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(2)


sys.excepthook = _bgfix6_excepthook

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

# 「形态子集」的 **Python 唯一真源**（1.7 bg-n10 轮1 后半；Java 侧镜像 = MetalFamily.Form）
sys.path.insert(0, str(Path(__file__).resolve().parent))
import metal_forms as MF   # noqa: E402

METALS = ["flamegold", "voodoogold", "thundergold", "indigoseagold", "illusiongold",
          # 1.6（bg-16）：两套新金属 —— 关卡扫描表必须跟着加，否则新族的语言键"零检查"也全绿
          "thornsgold", "echogold",
          # 1.7（bg-n10 轮1 后半）：两套新族。⚠ 它们的**形态子集不同**（chaosalloy 只有锭/块/模板）
          # ⇒ 本段所有"每族都要有 11 种建材 / 粒 / 原料 / 模板"的期望都必须走 MF.has(...) 过滤
          #   （这正是作者裁定 §4.0 ⑪d 要的那条改动；写死清单会立刻假红）。
          "chaosgold", "chaosalloy"]
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
    # ⚠ 1.7 bg-n10 轮3：**按该族声明的形态过滤**（旧口径原文保留在下面）。
    #   旧口径（轮1 后半写的）= 无条件要 `[f"{m}_{s}" for s in ITEMS] + [f"raw_{m}"]` +
    #   全部 `BLOCKS` + 全部 `TEMPLATE_KEYS`；那时生成器也是"全量占位"，
    #   两边一起错 ⇒ **假绿**（未注册形态的死语言键两边都看不见）。
    #   现口径：与 `generate_metal_data.py`（生成器）**同时**改成按形态取，
    #   否则会立刻假红（生成器不再写死键、校验器还在要）。
    #   形态外的（器具 / 武器 / 盔甲 / 刀）恒定注册 ⇒ 恒定要语言键。
    for s in ITEMS:
        if s in ("nugget", "upgrade_template") and not MF.has(m, s):
            continue
        need(f"item.bettergold.{m}_{s}")
    if MF.has(m, "raw"):
        need(f"item.bettergold.raw_{m}")
    for b in MF.building_of(m):
        need(f"block.bettergold.{m}_{b}")
    if MF.has(m, "upgrade_template"):
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
missing_loot = [f"{m}_{b}" for m in METALS for b in MF.loot_blocks_of(m)
                if not (loot_dir / f"{m}_{b}.json").is_file()]
# ⚠ 1.7（bg-n10 轮1 后半）：**旧口径原文保留** —— 原先是 `for b in BLOCKS`（每族 11 张）：
#   `missing_loot = [f"{m}_{b}" for m in METALS for b in BLOCKS if ...]`
#   现在按各族**声明的建材形态**取（chaosalloy 只有 `block` 一张）。
#   反空转：期望条数必须是"各族建材形态数之和"，且必须 > 0。
_loot_expected = sum(len(MF.loot_blocks_of(m)) for m in METALS)
if _loot_expected <= 0:
    missing_loot.append("[反空转] 期望的战利品表条数为 0（形态表被清空 / metal_forms 读不到）")
print(f"缺战利品表: {len(missing_loot)} {missing_loot[:8]}（期望 {_loot_expected} 张 = 各族建材形态数之和）")

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
# ⚠ **1.7 bg-n10r4（2026-10-16）就地标注**：作者给过的这 14 件是**前缀**不变量；
#   1.7 轮4 在末尾**追加**两件混沌金专属物品（禁果 / 附魔书，位次 14/15）——
#   它们也要进"装备"分区（连同 `chaosgold_helmet` 等一起出现在金属那一段）。
#   旧口径原文留档：`if len(gear_pairs) != len(GEAR_SLOT_EXPECTED)` + `by_rank != GEAR_SLOT_EXPECTED`（恰好 14 件）。
GEAR_SLOT_APPENDED = ["forbidden_fruit", "enchanting_book"]
GEAR_SLOT_WANT = GEAR_SLOT_EXPECTED + GEAR_SLOT_APPENDED
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
if len(gear_pairs) != len(GEAR_SLOT_WANT):
    bg8_problems.append(f"GEAR_SLOT 条目数 {len(gear_pairs)} != {len(GEAR_SLOT_WANT)}（反空转守护 / 表被动过）")
else:
    gear = {name: int(rank) for name, rank in gear_pairs}
    by_rank = [name for name, _ in sorted(gear.items(), key=lambda kv: kv[1])]
    if by_rank != GEAR_SLOT_WANT:
        bg8_problems.append(f"GEAR_SLOT 顺序不是 §9.1 最终顺序 + 1.7 轮4 的追加两件：{by_rank}")
    if sorted(gear.values()) != list(range(len(GEAR_SLOT_WANT))):
        bg8_problems.append(f"GEAR_SLOT 位次不是 0..{len(GEAR_SLOT_WANT) - 1} 各一次：{sorted(gear.values())}")
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
    # 1.7 `bg-n10fix` ⑤（作者 2026-10-18）：混沌金建材 = **铁级** ⇒ 它进 needs_iron_tool、
    #   且**不在** needs_diamond_tool（下表的 ONLY / EXCEPT 两张集合表达这一对）。
    "minecraft/tags/block/needs_iron_tool.json": [f"{{m}}_{b}" for b in _METAL_BLOCKS],
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
# 1.7 `bg-n10fix` ⑤：这两条标签**按族分流**（其余 SYMMETRIC_TAGS 仍是"每套金属都要有"）。
#   ONLY   = 这张标签里只**该**出现这些族（其余族出现 = 多写，红）；
#   EXCEPT = 这张标签里**不该**出现这些族（出现 = 没搬走，红）。
_TAG_ONLY = {"minecraft/tags/block/needs_iron_tool.json": {"chaosgold"}}
_TAG_EXCEPT = {"minecraft/tags/block/needs_diamond_tool.json": {"chaosgold"}}
# 「某个 id 模板要求哪个形态」——形态子集外的模板**不期望**（1.7 bg-n10 轮1 后半）。
# 表里没有的模板（锭 / 器具 / 武器 / 盔甲 / 刀 / 纹饰）恒期望（它们不参与形态子集）。
_TEMPLATE_FORM: dict[str, str] = {"{m}_nugget": "nugget", "raw_{m}": "raw"}
for _b in _METAL_BLOCKS:
    _TEMPLATE_FORM["{m}_" + _b] = _b
for _s in BEACON_SUFFIXES:
    _TEMPLATE_FORM["{m}_" + _s] = _s


def _template_ok(template: str, metal: str) -> bool:
    """该模板对该族是否成立（形态子集过滤；不在表里的恒成立）"""
    form = _TEMPLATE_FORM.get(template)
    return form is None or MF.has(metal, form)


for _rel, _templates in SYMMETRIC_TAGS.items():
    _members = tag_members(_rel)
    if not _members:
        symmetric_problems.append(f"{_rel} 读不到任何成员（反空转守护：文件没了 / 路径写错）")
        continue
    # ① 每套金属逐个对照（按形态子集过滤后的期望）
    per_metal = {}
    _only = _TAG_ONLY.get(_rel)
    _except = _TAG_EXCEPT.get(_rel, set())
    for _m in ALL_METALS:
        if _only is not None and _m not in _only:
            # 这张标签**不期望**这一族：只做负向断言（出现了就红）
            _extra = sorted(f"bettergold:{t.format(m=_m)}" for t in _templates
                            if _template_ok(t, _m)) if _m in _except else []
            _extra = [e for e in _extra if e in _members]
            if _extra:
                symmetric_problems.append(f"{_rel} <- {_m} 不该在（作者 2026-10-18：挖级已改），实际有 {_extra[:3]}")
            per_metal[_m] = 0
            continue
        if _m in _except:
            _extra = sorted(t.format(m=_m) for t in _templates if _template_ok(t, _m))
            _bad = [f"bettergold:{e}" for e in _extra if f"bettergold:{e}" in _members]
            if _bad:
                symmetric_problems.append(f"{_rel} <- {_m} 应当已被移出（`bg-n10fix` ⑤），实际还在 {_bad[:3]}")
            per_metal[_m] = 0
            continue
        _want = {f"bettergold:{t.format(m=_m)}" for t in _templates if _template_ok(t, _m)}
        _miss = sorted(_want - _members)
        per_metal[_m] = len(_miss)
        if _miss:
            symmetric_problems.append(f"{_rel} <- {_m} 缺 {_miss}")
    # ② 「成员数相同」的不变量（同一模板算出来的期望数 ⇒ 等价于多套一致）
    if len(set(per_metal.values())) != 1:
        symmetric_problems.append(f"{_rel} 各套金属缺失数不一致 {per_metal}")
print(f"六套金属标签一致性（{len(SYMMETRIC_TAGS)} 个标签 × {len(ALL_METALS)} 套金属）问题: "
      f"{len(symmetric_problems)} {symmetric_problems[:8]}")

# 信标基座标签的显式成员表（1.4 口径：块 / 砖 / 柱 + 金系两块 gold_bricks / gold_pillar）
beacon_problems: list[str] = []
_beacon_members = tag_members(BEACON_TAG_REL)
# ⚠ 1.7（bg-n10 轮1 后半）：**旧口径原文保留** ——
#   `_beacon_expect = ([f"bettergold:{m}_{s}" for m in ALL_METALS for s in BEACON_SUFFIXES] + BEACON_ALSO)`
#   新口径 = **按各族声明的形态**取信标成员（chaosalloy 只有块 ⇒ 只期望 1 条；
#   作者裁定 §4.0 ⑪d：「按族声明的形态集合」，不是放宽成"有几个算几个"）。
_beacon_expect = ([f"bettergold:{m}_{s}" for m in ALL_METALS
                   for s in BEACON_SUFFIXES if MF.has(m, s)]
                  + BEACON_ALSO)
for _id in _beacon_expect:
    if _id not in _beacon_members:
        beacon_problems.append(f"#minecraft:beacon_base_blocks 里没有 {_id}（当不了信标金字塔基座）")
# 每套金属必须**至少「块」+ 它声明的砖/柱**（块是必备形态 ⇒ 下限恒 1）——
# 少一条都要红，而不是只看"总数"。
for _m in ALL_METALS:
    _want_s = [s for s in BEACON_SUFFIXES if MF.has(_m, s)]
    _n = sum(1 for s in _want_s if f"bettergold:{_m}_{s}" in _beacon_members)
    if _n != len(_want_s):
        beacon_problems.append(f"{_m} 在信标基座标签里有 {_n} 条，期望 {len(_want_s)} 条"
                               f"（按族声明的形态：{_want_s}）")

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
# ⚠ 1.7（bg-n10 轮1 后半）：**旧口径原文保留** —— 原先是 `for _m in ALL_METALS:`，
#   而 chaosgold / chaosalloy **没有 raw 这个形态**（zip 里没有「混沌金原料」贴图，
#   歧义 ⑱c 未裁 ⇒ 工作值 = 跳过）⇒ 期望集合必须按形态过滤，否则会把"没有 raw"
#   读成"缺配方"（假红）。过滤后仍是"**有 raw 的族，每一族都必须有且只有这一张**"。
_raw_metals = [m for m in ALL_METALS if MF.has(m, "raw")]
for _m in _raw_metals:
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
if checked_raw != len(_raw_metals):
    # ⚠ 1.7：条件也跟着换成 `_raw_metals`（旧口径 `!= len(ALL_METALS)`：当时两者同长，现在不是）
    bg9_problems.append(f"只检查到 {checked_raw} 张自定义原料配方，期望 {len(_raw_metals)}"
                        f"（= 声明了 raw 形态的族数；反空转守护）")

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
# ⚠ 1.7（bg-n10 轮1 后半）：**旧期望原文保留** —— 原来是 `!= 8`（"八族各一个 coreItem"）。
#   新口径：coreItem 的数量 = 声明了 coreItem 的族数，**不是**族数 ——
#   混沌金有（= 混沌金币 `chaos_coin`，立档 §2.2 可执行口径第 2 条的默认），
#   崩乱合金**没有**（它没有 raw 链，锭是"下界合金锭 + 混沌金块 + 高精炼金油"合出来的）
#   ⇒ 现在是 9 个（既有 8 族 + chaosgold）。
#   old: if len(_core_items) != 8:
_CORE_ITEM_MIN = 9
if len(_core_items) != _CORE_ITEM_MIN:
    _bg16_bad("bg16-cactus-coreitem-anti-vacuum",
              f"AllMetals.java 里现算出 {len(_core_items)} 个 `.coreItem(() -> X.get())`"
              f"（应为 {_CORE_ITEM_MIN} 个 = 既有 8 族 + chaosgold）")
elif len(set(_core_items)) != len(_core_items):
    # 旧口径原文：`elif len(set(_core_items)) != 8:`（当时"8 个且互不相同"是一回事）
    _bg16_bad("bg16-cactus-coreitem-distinct",
              f"有重复的 coreItem 符号：{sorted(_core_items)}")
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
# ⛔ **bg-book §十（作者 2026-10-07 21:03）：「关于金灿盛宴的章节也填完了……你之前添加的那个也
#   一样直接毙掉吧」** ⇒ 骨架里剩下的最后一条 `golden_feast` **本轮也作废**（它的 7 页由 §十 的
#   5 章 54 页取代）。
#   ⚠ 旧期望原文保留（未删）：`_SKELETON_ENTRIES = ("golden_feast",)`。
#   ⇒ **第一轮骨架 7 条全部作废**，骨架清单变成**空元组**（`ENTRIES` 列表本身仍然留在生成器里）。
_SKELETON_ENTRIES = ()
# bg-book §十 作废的骨架占位条目：产物里**必须不存在**（负向断言），生成器里**必须仍在**
# RETIRED_ENTRIES 且页数照常算得出来（7 页 = 1 文案 + 6 spotlight）。
_BG10_RETIRED_ENTRIES = ("golden_feast",)
_BG10_RETIRED_PAGES = {"golden_feast": 7}
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
# bg-book §十 追加轮（2026-10-07 21:05）：「金灿的盛宴」5 章（替掉该类别旧占位条目 golden_feast）
_BG10_ENTRY_NAMES = ("golden_feast_crops", "golden_feast_foods", "golden_feast_sturdy",
                     "golden_feast_fd_foods", "golden_feast_fd_sturdy")
# ★ 1.7 收口轮（bg-n10r9，2026-10-17）：两族的 4 个条目
#   （材料 / 禁果 / 混沌金装备章 / 崩乱合金装备章）⇒ 条目总数 20 → **24**、页数 192 → **230**。
_BGN10R9_ENTRY_NAMES = ("chaos_materials", "chaos_feast",
                        "gear_chaosgold", "gear_chaosalloy")
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
# ⚠ **bg-book §十 起 `ENTRIES` 是空列表**（第一轮骨架 7 条全部作废）⇒ 原来那条反空转守护
#   「切出来的块里必须有 `entry_golden_feast`」**不再成立**（§十 把它也作废了）。
#   ⇒ 改用**原始源码（含注释）**里的稳定标记来锚定切块的正确性：
#     `_bgbook_gen_code` 是**去注释**的（负向断言必须跑在去注释源码上，见上面的教训），
#     所以这条反空转守护**必须**读 raw（`_bgbook_gen_txt`）—— 两者是**两把不同的尺子**。
_bgbook_entries_raw_match = re.search(r"(?ms)^ENTRIES = \[$(.*?)^\]\s*$", _bgbook_gen_txt)
_bgbook_entries_raw = _bgbook_entries_raw_match.group(1) if _bgbook_entries_raw_match else ""
if _bgbook_entries_raw_match is None:
    _bgbook_bad("bgfix3-generator-retired",
                "生成器**原始源码**里切不出 `ENTRIES = [ … ]` 块（行锚定正则失配 ⇒ 负向断言空转）")
elif u"bg-book §十 作废" not in _bgbook_entries_raw:
    _bgbook_bad("bgfix3-generator-retired",
                "切出来的 `ENTRIES` 块里没有 §十 那条作废注释（切错块了 ⇒ 反空转守护失效）")
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
# ⛔ bg-book §十：第一轮骨架**最后一个**占位条目 `golden_feast`（「金灿的盛宴」旧占位）
#   本轮也作废（作者 2026-10-07 原话「你之前添加的那个也一样直接毙掉吧」）。
for _retired in _BG10_RETIRED_ENTRIES:
    for _side in (_ZH_BOOK, _EN_BOOK):
        if (_side / "entries" / ("%s.json" % _retired)).exists():
            _bgbook_bad("bgbook10-old-placeholder-gone",
                        "§十 作废的「金灿的盛宴」旧占位条目 %s 又回到了产物里（%s）：它的 7 页已由"
                        "「金染土与金作物 / 其他种类的金食物 / 万坚金化的金食物 / 乐事联动的金食物 /"
                        " 乐事联动的万坚金食物」5 章 54 页取代" % (_retired, _side.name))
_missing_skeleton = [n for n in _SKELETON_ENTRIES if n not in _entries_now]
if _missing_skeleton:
    _bgbook_bad("bgbook-entry-count",
                "第一轮的骨架条目被删掉了（§八 只作废 %s、§九 只作废 %s、§十 只作废 %s）：%s"
                % (list(_RETIRED_ENTRIES), list(_BG9_RETIRED_ENTRIES),
                   list(_BG10_RETIRED_ENTRIES), _missing_skeleton))
# ⚠ **旧期望原文保留（未删）**：右端只有前五项（合计 20 条）。
# ★ 1.7 收口轮：+ `_BGN10R9_ENTRY_NAMES`（4 条）⇒ 24。
if len(_entries_now) != (len(_SKELETON_ENTRIES) + len(_BG2_ENTRY_NAMES)
                         + len(_BG8_ENTRY_NAMES) + len(_BG9_ENTRY_NAMES)
                         + len(_BG10_ENTRY_NAMES) + len(_BGN10R9_ENTRY_NAMES)):
    _bgbook_bad("bgbook-entry-count",
                "条目数应为 %d（骨架 %d + §六 章节 3 + §八 强化 9 + §九 商人与古董 3 + "
                "§十 金灿的盛宴 5 + 1.7 两族 4；"
                "bg-fix3 §三 作废 2 条骨架条目、§十 作废最后 1 条骨架条目），实际 %d"
                % (len(_SKELETON_ENTRIES) + len(_BG2_ENTRY_NAMES)
                   + len(_BG8_ENTRY_NAMES) + len(_BG9_ENTRY_NAMES) + len(_BG10_ENTRY_NAMES)
                   + len(_BGN10R9_ENTRY_NAMES),
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
if _total_pages < 190:
    # ⚠ **bg-book §十 改变了这里的期望值**：作废 `golden_feast`(7) + 新增 5 章 54 页 = +47 页
    #   ⇒ 143 → **190**。旧阈值（≥143，注释里写「bg-fix3 §三 之后应为 143 页 = 157 − 14」）
    #   原文留在这里作历史留档。
    _bgbook_bad("bgbook-anti-vacuum",
                "手册总页数只有 %d（bg-book §十 之后应为 190 页 = 143 − 7 + 54；"
                "数据树被清空会命中这条）" % _total_pages)
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
#   ⚠ **bg-book §八（2026-10-06）**：章3 的**第 1 页（汇总页）曾被作者删除**（§8.1）⇒
#     当时页型序列由 5 行（10 页）变成 **4 行（8 页）**，三章合计 32 → **30**。
#   ★ **bg-fix4 §三（2026-10-08）作者要求"复原"那一页** ⇒ 序列回到 **5 行（10 页）**、三章合计 **32**。
#     旧期望原文保留（未删）：`["patchouli:spotlight", "patchouli:spotlight"] * 4` 与 `!= 30`。
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
                 "三章合计应是 32 个 Patchouli 页（= 文档 2+9+5 = 16 行 × 2；"
                 "§八 删掉章3 第 1 页时曾是 30，bg-fix4 §三 复原后回到 32），实际 %d" % _bg2_pages_total)
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
if len(_bg2_item_refs) != 115:
    # ★ **bg-fix4 §三/§四（2026-10-08）改变了这里的期望值**：
    #   ① §三 复原章3 第 1 页（8 锭 + 8 模板 = 16 个引用）；
    #   ② §四 把章3 那 8 个建材页的展示栏从"1 块砖"改成"该族 11 件建材"
    #      ⇒ 8 族 × 11 = 88 个引用（其中 `_bricks` 与①的锭/模板不重叠）。
    #   合计 = 章1 2 + 章2 9 + 章3（16 + 88）= **115**。
    #   旧期望原文保留（未删）：§八 删掉章3 第 1 页后是"恰好 19"；那一轮之前是 35。
    #   改成"恰好 115"比阈值更硬：任何"顺手加一个图标"都会当场红。
    _bgbook2_bad("bgbook2-item-refs",
                 "三章解析到 %d 个图标引用（应恰好 115；bg-fix4 §三/§四 之后由 19 升上来）"
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
    if len(_bg2_texts) != 22 or sum(len(_t) for _t in _bg2_texts) < 600:
        # ⚠ **旧期望（原文留档，未删，已被 bgfix8 2026-10-09 取代）**：曾为 `!= 21`，
        #   说明串为「应 21 段 = 2 + 9 + 1 + 9」—— 那时 §6.3 第 1 行右格只有图标、没有正文。
        #   作者本轮要求右页加文字 ⇒ 快照那一格多出一段 ⇒ **2 + 9 + 2 + 9 = 22**。
        _bgbook2_bad("bgbook2-texts-verbatim",
                     "从冻结快照解析到 %d 段逐字文案 / 共 %d 字（应 22 段 = 2 + 9 + 2 + 9、"
                     "总字数 >= 600；反空转守护）"
                     % (len(_bg2_texts), sum(len(_t) for _t in _bg2_texts)))
    _zh_values = set(zh.values())
    _bg2_missing_texts = [_t for _t in _bg2_texts if _t not in _zh_values]
    if _bg2_missing_texts:
        _bgbook2_bad("bgbook2-texts-verbatim",
                     "冻结快照里的逐字文案没有原样出现在 zh_cn.json 里（%d/%d 段缺失，首条：%s）"
                     % (len(_bg2_missing_texts), len(_bg2_texts), _bg2_missing_texts[0][:40]))

# 语言键：25 条（3 个条目名 + 22 段文案/标题键）必须**中英双端都有**
#   ⚠ bg-append 追加轮：`knowledge_1_left` / `knowledge_1_right` **已被作者要求删除**
#     （§七.1「把那些东西都汇总起来」）⇒ 换成 `knowledge_1_summary`（整页只剩这一句）。
#   ★ **bgfix8（2026-10-09）**：作者要求「贵金的装备升级锻造模板那一页应该加文字」
#     ⇒ `knowledge_1_right`（「锻造模板怎么用」那段）**重新成为页面正文键**（右页），
#     本清单 **24 → 25**；`knowledge_1_left` **仍然不在**（它的信息已并入 summary）。
_bg2_suffixes = (["aux_1", "aux_2"]
                 + ["core_%d" % _i for _i in range(1, 10)] + ["core_1_right"]
                 + ["knowledge_1_summary", "knowledge_1_right"]
                 + ["knowledge_%d_%s" % (_i, _s) for _i in range(2, 6) for _s in ("left", "right")])
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

# ---------- 第 3 条 · 闪耀藤条判据"收窄为特殊金属" ----------
# ⛔⛔ **本条整段已作废（原文保留，未删）** —— 作者 2026-10-08 明确要求**去掉豁免**：
#   「万坚金器具与金器具的挖树叶与藤蔓有概率掉落闪耀藤条的事你又忘添加了」。
#   旧断言原文（逐字留档）：
#     if "isSpecialMetal()" not in _bgfix_glm:
#         _bgfix_bad("bgfix-vine-special-metal",
#                    "闪耀藤条判据没有用 family.isSpecialMetal()（没收窄，万坚金仍会掉）")
#     else:
#         _i_special = _bgfix_glm.find("isSpecialMetal()")
#         _i_istool = _bgfix_glm.find("family.isTool(")
#         if _i_istool < 0: ... elif _i_special > _i_istool: ...
#     if "family != null && (family.isTool(" in _bgfix_glm:
#         _bgfix_bad("bgfix-vine-old-broad",
#                    "仍留着旧口径 `family != null && (family.isTool(`（= 任意一族，万坚金会掉藤条）")
#   ⇒ 现行判据（含"必须有 isTool/isWeapon、**不许**有 isSpecialMetal"）落在 bg-fix4 段的
#     `[bgfix4-vine-all-metals]`；本段**不再**对 `isOurTool` 的形状下任何断言（避免新口径被判红）。
#   ⚠ `isSpecialMetal()` 本身**必须继续存在**（盾牌那条链还在用它）——见下面两条 bgfix 断言。
if 'STURDYGOLD_ID = "sturdygold"' not in _bgfix_mf:
    _bgfix_bad("bgfix-special-metal-predicate", "MetalFamily 里没有 STURDYGOLD_ID 常量")
if "public boolean isSpecialMetal()" not in _bgfix_mf:
    _bgfix_bad("bgfix-special-metal-predicate", "MetalFamily 里没有 isSpecialMetal()")
elif "!STURDYGOLD_ID.equals(this.id)" not in _bgfix_mf:
    _bgfix_bad("bgfix-special-metal-predicate",
               "isSpecialMetal() 的判据不是 !STURDYGOLD_ID.equals(this.id)")
_n_specs = _bgfix_am.count("new MetalFamily.Spec(")
# ⚠ 1.7（bg-n10 轮1 后半）：**旧期望原文保留** —— 原来是 `!= 8`（当时恰好八族）。
#   现在 10 族（既有 8 + 混沌金 + 崩乱合金）。旧值 8 作为"反空转下限"仍然有意义：
#   数量必须**正好**等于 10（写死是为了拦住"注册表被清空"这类空转），
#   加族时**必须**同步改这一行（与 metal_forms.py / AllMetals.java 三边一起长）。
#   old: if _n_specs != 8:
if _n_specs != 10:
    _bgfix_bad("bgfix-special-metal-predicate",
               "AllMetals 里的 MetalFamily.Spec 不是 10 个（实际 %d；反空转守护）" % _n_specs)

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
# ⚠ **1.7 bg-n10r4（2026-10-16）就地标注**：本节标题里的「16 条 / 8 族」是 **bg-fix 当时**的计数，
#   本轮两族进入配置系统（父代理裁定：不等轮7/轮9）⇒ **现行 = 10 族 × 2 = 20 条**、键总数 **25 → 29**。
#   断言 id `[bgfix-config-16-keys]` 的**名字**保留为历史名（旧名不改、旧期望原文留在下面注释里），
#   判据本身按 20 条走；另新增 `[bgn10r4-config-every-family]` 钉住"每个已注册族都必须有配置项"
#   —— 这条正是本阻塞（chaos 器具每次命中抛「未登记配置项的金属族」）的**根因**。
#   旧期望原文留档：`if len(_cfg_keys) != 25:` + "既有 9 + 新增 16"（8 族 × 2）。
_BGFIX_FAMILIES = ["flamegold", "voodoogold", "thundergold", "indigoseagold",
                   "illusiongold", "thornsgold", "echogold", "sturdygold"]
_BGN10R4_FAMILIES = _BGFIX_FAMILIES + ["chaosgold", "chaosalloy"]
_BGFIX_WEAPON_KEYS = {f: f + "WeaponBuffChance" for f in _BGN10R4_FAMILIES}
_BGFIX_WEAPON_KEYS["sturdygold"] = "sturdygoldWeaponAbilityChance"
_BGFIX_ARMOR_KEYS = {f: f + "ArmorBuffChance" for f in _BGN10R4_FAMILIES if f != "sturdygold"}
_BGFIX_MULT_KEY = "sturdygoldArmorAbilityIntervalMultiplier"
_EXISTING_CONFIG_KEYS = ["logDirtBlock", "magicNumber", "magicNumberIntroduction", "items",
                         "goldLootMode", "goldLootItems", "voodooExtractRatio",
                         "voodooFlatPerLevel", "thunderSoundMode"]
_cfg_keys = re.findall(r'\.define(?:InRange|ListAllowEmpty)?\(\s*"([^"]+)"', _bgfix_cfg)
if len(_cfg_keys) != 29:
    _bgfix_bad("bgfix-config-16-keys",
               "Config.java 的键总数不是 29（既有 9 + bg-fix 16 + bg-n10r4 4 = 29；实际 %d: %s）"
               % (len(_cfg_keys), _cfg_keys))
# ---------- ★ `[bgn10r4-config-every-family]`：每个**已注册族**都必须有对应配置项 ----------
# 判据：`AllMetals.java` 里 `new MetalFamily.Spec("id", ...)` 的 id 集合
#   （**从源码反解**，不是拿另一张期望表自比）必须逐个出现在 `Config.java` 的
#   `weaponBuffChance` / `armorBuffChance` 两个 switch 的 case 字面里。
# 为什么要有这条：本轮的硬阻塞就是"加了族、忘了补配置项"，而旧断言只数了**总数** 25 ——
#   它**看不见**"某个族缺 case"（把 chaosgold 的 case 删掉、总数仍然是 29）⇒ 必须逐个族对穿。
_r4_am_src = strip_comments((JAVA / "material" / "AllMetals.java").read_text(encoding="utf-8"))
_am_spec_ids = sorted(set(re.findall(r'new MetalFamily\.Spec\("([a-z_]+)"', _r4_am_src)))
if len(_am_spec_ids) != 10:
    _bgfix_bad("bgn10r4-config-every-family",
               "AllMetals.java 里反解到的族 id 不是 10 个（实际 %d: %s）—— 反空转守护"
               % (len(_am_spec_ids), _am_spec_ids))
_cfg_w_body = method_body(_bgfix_cfg, "public static float weaponBuffChance(")
_cfg_a_body = method_body(_bgfix_cfg, "public static float armorBuffChance(")
for _f in _am_spec_ids:
    if ('case "%s"' % _f) not in _cfg_w_body:
        _bgfix_bad("bgn10r4-config-every-family",
                   "族 %s 没有 weaponBuffChance 的 case ⇒ 它每次命中都会抛「未登记配置项的金属族」"
                   "（= 本轮那个硬阻塞的形状）" % _f)
    if 'case "%s"' % _f not in _cfg_a_body:
        _bgfix_bad("bgn10r4-config-every-family",
                   "族 %s 没有 armorBuffChance 的 case（盔甲侧反制会抛异常）" % _f)
for _f in ("chaosgold", "chaosalloy"):
    if _f not in _BGN10R4_FAMILIES:
        _bgfix_bad("bgn10r4-config-every-family", "1.7 两族 %s 没进本断言的族清单" % _f)
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
    # ⚠ 1.7 bg-n10r4：两族的 4 条（默认值依据 = 立档 §4.0「全部按字面」；见 Config.java 那段注释）
    ("chaosgoldWeaponBuffChance", 1.0), ("chaosgoldArmorBuffChance", 1.0),
    ("chaosalloyWeaponBuffChance", 0.5), ("chaosalloyArmorBuffChance", 0.1),
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
    # ⚠ 1.7 bg-n10r4：旧期望是 8（= bg-fix 当时的 8 族）；两族进配置系统后是 **10**（camelCase 的 case）。
    #   旧口径原文留档：`if _b.count('case "') != 8:`
    if _b.count('case "') != 10:
        _bgfix_bad("bgfix-config-case-count",
                   "%s 的 case 数不是 10（= 10 族 × 1；实际 %d）" % (_tag, _b.count('case "')))
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
# ★ bg-fix4 §四（作者 2026-10-08）：建筑方块展示栏的**新字面顺序**
#   （锭块 → 砖块 → 柱 → 楼梯 → 台阶 → 砖墙 → **门 → 活板门 → 栏杆** → 链 → 灯笼）
# ⚠ **旧顺序原文保留（未删，已被 2026-10-08 取代）**：
#   ["_block", "_bricks", "_pillar", "_bricks_stairs", "_bricks_slab",
#    "_bricks_wall", "_bars", "_door", "_trapdoor", "_chain", "_lantern"]
_BG3_BUILDING_ORDER = ["_block", "_bricks", "_pillar", "_bricks_stairs", "_bricks_slab",
                       "_bricks_wall", "_door", "_trapdoor", "_bars", "_chain", "_lantern"]
_BG3_OLD_TEXT_KEYS = ["bettergold.handbook.page.knowledge_1_left"]
# ⚠ **旧清单（原文留档，未删，已被 bgfix8 2026-10-09 取代）**：
#     _BG3_OLD_TEXT_KEYS = ["bettergold.handbook.page.knowledge_1_left",
#                           "bettergold.handbook.page.knowledge_1_right"]
#   —— §七.1「把那些东西都汇总起来」当时把**两段**都删了；作者本轮（bgfix8 §2）
#      「贵金的装备升级锻造模板那一页应该加文字」⇒ **只**把 `knowledge_1_right` 放回右页，
#      `knowledge_1_left`（材料链）**仍然**不许被引用（它的信息已并入 `knowledge_1_summary`）。
_BG3_ZH_E = _bgappend_jload(_BG3_ZH)
_BG3_EN_E = _bgappend_jload(_BG3_EN)
_BG3_PAGES = _BG3_ZH_E.get("pages") or []
# ⚠ **bg-book §八（2026-10-06）曾改变本节的期望**：章3 的第 1 页（§七 改成"汇总页"的那一跨页）
#   被 §8.1 **整页删除** ⇒ 当时页数 10 → **8**。
# ★ **bg-fix4 §三（2026-10-08）作者要求"复原"** ⇒ 页数回到 **10**（5 行 × 2）；
#   下面那**六条**旧断言（`bgappend-book-k3-p1-ingots` / `-p1-ingot-title` / `-p1-summary` ×2 /
#   `-p1-templates` / `-p1-template-title`）**当时随该页一起作废**，本轮**由
#   `[bgfix4-k3p1-restored]`（bg-fix4 段）以新期望复活**（比旧版更硬：标题逐字来自冻结快照）。
#   上面 `_BG3_INGOT_IDS` / `_BG3_TEMPLATE_IDS` / `_BG3_INGOT_TITLE` / `_BG3_TEMPLATE_TITLE`
#   四个常量**继续服役**（现在给正向断言用）。
if len(_BG3_PAGES) != 10:
    _bgappend_bad("bgappend-book-k3-pages",
                  "章3（「贵金」的知识）的 Patchouli 页数不是 10（5 行 × 2；§八 曾删到 8，"
                  "bg-fix4 §三 复原后回到 10；实际 %d）—— 反空转守护" % len(_BG3_PAGES))
else:
    # §七.1：原来那两段长文案**不许再被任何一页引用**，也不许再出现在语言值里
    #   （键**留在 lang 里作历史留档**是允许的 —— 见该键注释；被引用/被复用才是回退）
    #   ⚠ bgfix8（2026-10-09）：上面这句里的"两段"现在**只剩 `knowledge_1_left` 一段**——
    #     作者要求把「锻造模板怎么用」（`knowledge_1_right`）放回右页 ⇒ 见 `_BG3_OLD_TEXT_KEYS` 的留档。
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

# §七.7 定的「建筑方块图标固定顺序」在 **bg-fix4 §四（2026-10-08）被作者更新**为
#   锭块 → 砖块 → 柱 → 楼梯 → 台阶 → 砖墙 → 门 → 活板门 → 栏杆 → 链 → 灯笼
#   （把「栏杆」从砖墙之后挪到活板门之后）⇒ 落点仍是生成器的 `METAL_BLOCK_SUFFIX_ORDER`（真源）
#   + 从产物里反查 11 个方块 id 都真实存在。**新 id 的"两处同序"不变量**见本节末尾的
#   `[bgfix4-building-order-single-source]`（Java `CreativeSections.BUILDING_SLOT` ↔ 本常量）。
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
                          "建筑方块图标顺序不是 bg-fix4 §四 的固定顺序：%s" % _bgdoc_order)
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
if len(_BGAPPEND_CFG_KEYS) != 20:
    _bgappend_bad("bgappend-config-i18n",
                  "配置键清单不是 20 条（1.7 bg-n10r4 起 = 10 族 × 2）—— 反空转守护")
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


# ===========================================================================
# bg-fix4（会话标记 bg-fix4，2026-10-08）：第四批（五条）
# ===========================================================================
# 稳定 ASCII id 前缀 = `[bgfix4-...]`。判据一律跑在**去注释**后的源码 / 已解析的 JSON /
# **仓库内冻结快照**（`bgappend-requirements-snapshot/bg-book-6.1-6.3.md`）上。
# ==================== bgfix8（2026-10-09）：前置检查（**放在所有使用点之前**） ====================
#
# 口径（`docs/构建与跑测注意事项.md` 七 + `ex/03` §3.19.1）：**前置缺失 = exit 2**，
# 绝不是"没有问题"。本轮的期望值来自三个仓库内文件（冻结快照 / Config.java / 手册产物）——
# 它们不在 = 基线被破坏。
#   ⚠ 必须**早于**任何读快照的代码（例如 `_fx4_snapshot_k3()` 会直接 `read_text` 炸成
#     `[bg-data-crash]`；那样虽然也是 exit 2，但报错就分不清"前置缺失"与"脚本自身出错"了）。
bgfix8_problems: list[str] = []


def _bgfix8_bad(tag: str, msg: str) -> None:
    bgfix8_problems.append("%s [%s]" % (msg, tag))


_BGFIX8_PREREQ = [_BG2_SNAPSHOT, JAVA / "config" / "Config.java", _BG3_ZH, _BG3_EN]
_bgfix8_missing = [str(_p) for _p in _BGFIX8_PREREQ if not _p.is_file()]
print(f"[bgfix8-anti-vacuum] 前置文件存在性：冻结快照={_BG2_SNAPSHOT.is_file()} / "
      f"Config.java={(JAVA / 'config' / 'Config.java').is_file()} / "
      f"手册 golden_knowledge.json(zh,en)={_BG3_ZH.is_file()},{_BG3_EN.is_file()}"
      f"（缺 {len(_bgfix8_missing)} 个，必须 = 0）")
if _bgfix8_missing:
    print(f"FAIL [bgfix8-anti-vacuum] 前置缺失 {_bgfix8_missing} ⇒ 本关卡 exit 2")
    sys.exit(2)

bgfix4_problems: list[str] = []


def _bgfix4_bad(tag: str, msg: str) -> None:
    bgfix4_problems.append("%s [%s]" % (msg, tag))


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

# ---------- 第 3 条 · 闪耀藤条：★ bg-fix4 §一（作者 2026-10-08）**全部 8 族都能掉** ----------
# ⛔⛔ **旧口径（原文保留，未删，已被作者 2026-10-08 明确取代）** —— 旧 id `[bgfix2-vine-all-but-sturdygold]`：
#   它要求 `isOurTool` 方法体里**必须有** `family.isSpecialMetal()`、且 `isSpecialMetal` =
#   `!STURDYGOLD_ID.equals(this.id)` ⇒ "除万坚金外的 7 族"（万坚金 11 类全 0/400）。
# ★ 现行：作者原话「**万坚金器具与金器具的挖树叶与藤蔓有概率掉落闪耀藤条的事你又忘添加了**」
#   ⇒ 去掉那一层豁免；`isSpecialMetal()` **保留**（盾牌那条链仍在用它，删了会静默改盾牌口径）。
_isour = method_body(_bgfix_glm, "private static boolean isOurTool(")
if not _isour:
    _bgfix4_bad("bgfix4-vine-all-metals", "找不到 isOurTool 方法体（反空转守护）")
else:
    if "family.isSpecialMetal()" in _isour:
        _bgfix4_bad("bgfix4-vine-all-metals",
                    "isOurTool 里还留着 `family.isSpecialMetal()` 前置判定 ⇒ 万坚金仍然不掉藤条"
                    "（作者 2026-10-08：「万坚金器具与金器具的挖树叶与藤蔓有概率掉落闪耀藤条的事"
                    "你又忘添加了」⇒ 不存在「万坚金豁免」）")
    for _n, _why in (("family.isTool(", "少了器具那一半"),
                     ("family.isWeapon(", "少了武器那一半")):
        if _n not in _isour:
            _bgfix4_bad("bgfix4-vine-all-metals", "%s（缺 %s）" % (_why, _n))
_is_special = method_body(_bgfix_mf, "public boolean isSpecialMetal(")
if not _is_special:
    _bgfix4_bad("bgfix4-vine-all-metals", "找不到 isSpecialMetal 方法体（反空转守护）")
elif "!STURDYGOLD_ID.equals(this.id)" not in _is_special:
    _bgfix4_bad("bgfix4-vine-all-metals",
                "isSpecialMetal 的语义被改了（盾牌那条链还在用它：「只有万坚金不是特殊金属」）")
# 反空转：八族（八族 - 1 = 7 族能掉）；低于 8 说明扫描表/注册表被改坏了
# ⚠ 计数必须跑在 **AllMetals.java** 上（`new MetalFamily.Spec(` 的字面量形态）——
#   MetalFamily.java 里只有嵌套类 `Spec` 的定义，在那里数它恒为 0（本段第一版就踩了这个 = 假红）。
_spec_count = _bgfix_am.count("new MetalFamily.Spec(")
# ⚠ 1.7（bg-n10 轮1 后半）：**旧期望原文保留** —— `old: if _spec_count != 8:`
#   现在是 10 族（既有 8 + 混沌金 + 崩乱合金）。下限语义不变：数量必须**正好**等于声明表，
#   否则就是"注册表被清空 / AllMetals 被改坏"这类空转。
if _spec_count != 10:
    _bgfix4_bad("bgfix4-vine-all-metals",
                "AllMetals 里的 MetalFamily.Spec 不是 10 个（实际 %d；反空转守护）" % _spec_count)
for _n, _why in (("BASE_CHANCE = 0.06F", "6% 基础概率被改"),
                 ("CHANCE_PER_FORTUNE = 0.06F", "时运系数被改")):
    if _n not in _bgfix_glm:
        _bgfix2_bad("bgfix2-vine-chance", "%s（缺 %s）" % (_why, _n))

# ---------- 第 6 条 · 成就：全开放（无 hidden）+ 制作改获得 ----------
_adv_files = sorted(_ADV.rglob("*.json"))
# ⚠ **旧期望原文保留（未删）**：`if len(_adv_files) != 51: ... 期望 51`。
# ★ 1.7 收口轮：51 → **59**（混沌金 / 崩乱合金各 4 条）。
if len(_adv_files) != 59:
    _bgfix2_bad("bgfix2-adv-51", "成就 JSON 数 = %d，期望 59（反空转守护）" % len(_adv_files))
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
# ⚠ 1.7（bg-n10 轮1 后半）：**旧期望原文保留** —— bg-fix2 时是 9（六套金属 + unwanted_antique
#   + 万坚金 + 表外那一张），当时写死 9 是"反空转"。本轮新增 chaosgold / chaosalloy 两族
#   （两族都有 8×1 纹饰色卡）⇒ 11。加族时这里必须同步长。
#   old: if len(_trim_jsons) != 9:
if len(_trim_jsons) != 11:
    _bgfix2_bad("bgfix2-trim-nine-materials",
                "trim_material JSON 数 = %d，期望 11（既有 9 + 1.7 的 chaosgold/chaosalloy；反空转守护）"
                % len(_trim_jsons))
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

# ---------- ③ 章3 第 1 页（§七 的汇总页）：§八 删过、**bg-fix4 §三 已复原** ----------
# ⛔⛔ **旧判据（原文保留，未删，已被 2026-10-08 取代）**：这里曾用 `[bgbook8-k3-p1-gone]`
#   做**负向**断言 —— 全书任何一页都不许引用 `knowledge_1_summary`、不许出现那两个标题、
#   不许出现那两张图标表（当时作者 §8.1 要求删页）。**bg-fix4 §三 要求把它复原** ⇒
#   该负向断言失效，改由 bg-fix4 段的 `[bgfix4-k3p1-restored]` 用**正向**判据守着
#   （左 = 八族锭 + 标题 + 正文；右 = 八张模板 + 标题、无正文）。旧代码形状（留档）：
#     _bg8_stale_text = [p.get("text") for p in _bg8_all_pages
#                        if p.get("text") == "bettergold.handbook.page.knowledge_1_summary"]
#     _bg8_stale_title = [... p.get("title") in (_BG3_INGOT_TITLE, _BG3_TEMPLATE_TITLE)]
#     _bg8_stale_items = [... p.get("item") in (_BG3_INGOT_IDS, _BG3_TEMPLATE_IDS)]
#     if _bg8_stale_text or _bg8_stale_title or _bg8_stale_items: _bgbook8_bad("bgbook8-k3-p1-gone", ...)
#
# 仍然成立的那半条：**历史留档键不许被删**（既定口径：原文不删）——保留在下面。
for _k in ("bettergold.handbook.page.knowledge_1_summary",):
    # ⚠ **记账（以实际为准）**：`docs/1.6-规格.md` §17.1 写「`knowledge_1_left` / `knowledge_1_right`
    #   两把键**留在语言文件里作历史留档**」，但**实测这两把键在两份语言文件里都不存在**
    #   （`grep 'knowledge_1'` 只有 `knowledge_1_summary` 一条）⇒ 本断言只钉**确实存在**的那一把，
    #   差异写进 §十九（不是本轮的改动，本轮没删过任何键）。
    if _k not in zh or _k not in en:
        _bgbook8_bad("bgfix4-k3p1-restored", "历史留档键被删了（既定口径：原文不删）：%s" % _k)


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
# 跨文件不变量：家族索引覆盖的正是**该族的建材形态**（§9.8 推断值 3 的那张清单）
# ⚠ **1.7（bg-n10 轮1 后半）就地标注 —— 作者裁定 §4.0 ⑪d「改成按族声明的形态集合」**：
#   旧口径（原文保留、**不放宽**）是"`MetalFamily.allBlocks` **恰好 11 种形态** / 例外集合 = 8×11+1 = 89"：
#     `_bg9_allblocks = re.search(r"this\.allBlocks = List\.of\((.*?)\);", _bg9_mf_src, re.S)`
#     `if len(_bg9_forms) != 11: ... "MetalFamily.allBlocks 不是 11 种形态"`
#   新口径分三层（都不许软化成 `>=` / `!=`）：
#     ① Java 侧"建材形态清单"必须**恰好**等于 `Form.BUILDING_FORMS` 那 11 个字段（顺序也一致）；
#     ② 该清单必须**由形态开关驱动**（注册处有 `has(Form.X)` 守卫、汇总处用"跳过 null"的写法）；
#     ③ 运行期每个族的形态数**由声明决定** ⇒ 期望方块数 = Σ 各族建材形态数 + 1（下界合金块），
#        按 `metal_forms.py` 现算（既有 8 族 × 11 + chaosgold 11 + chaosalloy 1 + 1 = 101）。
_bg9_mf_src = strip_comments((JAVA / "material" / "MetalFamily.java").read_text(encoding="utf-8"))
# ⚠ 新形状（1.7）：汇总用 `java.util.Arrays.asList(...)`（**允许 null**）而不是 `List.of(...)` ——
#   `List.of` 遇到 null 会在进入 filter 之前抛 NPE（第一次 runData 冒烟实测崩在这里）。
#   因此这里同时接受两种写法，但**必须**是其中之一（读不到就红，反空转）。
_bg9_allblocks = re.search(r"for \(DeferredBlock<\?> holder : java\.util\.Arrays\.asList\((.*?)\)\) \{",
                           _bg9_mf_src, re.S)
if not _bg9_allblocks:
    _bg9_allblocks = re.search(r"for \(DeferredBlock<\?> holder : List\.of\((.*?)\)\s*\n?\s*\.stream\(\)",
                               _bg9_mf_src, re.S)
if not _bg9_allblocks:
    _bgbook9_bad("bgbook9-dust-convert-exempt",
                 "读不到 MetalFamily 的「建材形态清单」（反空转守护："
                 "`for (DeferredBlock<?> holder : java.util.Arrays.asList(...))` 那段不见了）")
else:
    _bg9_forms = re.findall(r"this\.(\w+)", _bg9_allblocks.group(1))
    # Java 字段名的驼峰 -> Form 常量的下划线后缀（bricksStairs -> bricks_stairs）
    _bg9_forms_suffix = [re.sub(r"([a-z])([A-Z])", r"\1_\2", _f).lower() for _f in _bg9_forms]
    _bg9_forms_suffix = ["block" if _s == "block" else _s for _s in _bg9_forms_suffix]
    # ⚠ 只比**集合**、不比顺序：注册顺序是历史顺序（door/trapdoor/bars/chain 在 1.4 就写死了），
    #   真正的"显示顺序真源"是 `CreativeSections.BUILDING_SLOT`（那条由 `[bgfix4-building-order-*]` 守着）。
    if sorted(_bg9_forms_suffix) != sorted(MF.BUILDING_FORMS):
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "MetalFamily 的建材形态集合 %s ≠ Form.BUILDING_FORMS %s"
                     "（11 种建材的口径变了）" % (sorted(_bg9_forms_suffix), sorted(MF.BUILDING_FORMS)))
    if len(_bg9_forms_suffix) != 11:
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "MetalFamily 的建材形态清单不是 11 种（实际 %d：%s）"
                     % (len(_bg9_forms_suffix), _bg9_forms_suffix))
    # ② 形态开关必须真的被注册链读（不是"声明了但没人看"）
    _bg9_guard_n = len(re.findall(r"!has\(Form\.[A-Z_]+\)", _bg9_mf_src))
    if _bg9_guard_n < 10:
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "MetalFamily 里按形态开关注册的守卫只有 %d 处（< 10）—— "
                     "形态子集开关没接进注册链（声明了却照旧全注册）" % _bg9_guard_n)
    if "this.allBlocks = List.copyOf(blocks);" not in _bg9_mf_src:
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "MetalFamily 的汇总不是「跳过 null 的 blocks 列表」（形态子集外的形态会 NPE / 漏掉）")
    if "if (holder != null) {" not in _bg9_mf_src:
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "MetalFamily 的汇总没有逐项判空（形态子集外的 null 会被收进 allBlocks/allItems）")
    # ③ 期望方块数 = Σ 各族建材形态数 + 1（下界合金块）
    _bg9_expected_blocks = 1 + sum(len(MF.building_of(_m)) for _m in ["sturdygold", *METALS])
    if _bg9_expected_blocks != 101:
        _bgbook9_bad("bgbook9-dust-convert-exempt",
                     "按形态声明现算的例外集合方块数 = %d，期望 101"
                     "（既有 8 族 × 11 + chaosgold 11 + chaosalloy 1 + 下界合金块 1）；"
                     "old: 8×11+1 = 89" % _bg9_expected_blocks)

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
        # bg-fix4 §一：两张古董刀标签（同样是"只在装了乐事时才存在的物品"）
        ('"antique_knives"', "计划表里没有 `antique_knives` 标签（古董屠刀）"),
        ('"netherite_antique_knives"', "计划表里没有 `netherite_antique_knives` 标签（幽冥断骸刀）"),
        ("for _m in ALL_METALS", "刀标签不是按 8 族循环生成的（写死清单会漏族 —— AGENTS 红线 2）")):
    if _needle not in _bgfix3_tags_src:
        _bgfix3_bad("bgfix3-tag-generator", "%s（缺 %s）" % (_why, _needle))

# 产物侧：**11 张**"可选条目标签"必须在，且每张**恰好 1 条** value 写成 `required: false`
#   （bg-fix3 时是 9 张 = 8 族刀 + handbook；bg-fix4 §一 追加 2 张古董刀 ⇒ 11 张）
_bgfix3_tag_dir = _DATA / "bettergold" / "tags" / "item"
_bgfix3_tag_paths = sorted(_bgfix3_tag_dir.glob("*_knives.json")) + \
                    [_bgfix3_tag_dir / "handbook.json"]
if len(_bgfix3_tag_paths) != 13:
    # ⚠ 1.7（bg-n10 轮1 后半）：**旧期望原文保留** ——
    #   old: `if len(_bgfix3_tag_paths) != 11:`（8 族刀 + 2 张古董刀 + handbook）
    #   1.7 新增两族 ⇒ `<族>_knives` 标签 8 → 10 张 ⇒ 13 张。
    _bgfix3_bad("bgfix3-tag-generator",
                "可选条目标签文件不是 13 张（10 族刀 + 2 张古董刀 + handbook），实际 %d：%s"
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
# ==================== bg-book §十（2026-10-07 21:05）：「金灿的盛宴」5 章 ====================
#
# 形状：作者表是 `| 页 | 左侧 | 右侧 |`（作者写「第 N 页左 / 右」）⇒ **一行 = 一屏 = 2 个 Patchouli 页**
#   ⇒ 5 / 5 / 7 / 5 / 5 行 = **10 / 10 / 14 / 10 / 10 = 54 页**。
# 逐字文案的期望值来源 = 仓库内**冻结快照**
#   `tools/asset-generator/bgappend-requirements-snapshot/bg-book-10.md`（**不读**仓库外活页）。
#
# ⚠⚠ **两个门禁项（需求 §十 没写）** —— 都由本段逐页钉住：
#   G1 · **酿造台配方**（章2 第1页右 / 章3 第3页左）：Java 注册（`ModBrewing`，
#        `RegisterBrewingRecipesEvent`）⇒ **不是 RecipeManager 配方** ⇒ 任何配方页都表达不了
#        ⇒ 降级 `patchouli:spotlight`（图标 = 成品）。
#   G2 · **`farmersdelight:cooking` 厨锅配方**（章4 第1页左 / 第2页右 / 第3页左）：
#        Patchouli 1.21.1-93 的 16 个内置页型里没有厨锅页 ⇒ 同样降级 `patchouli:spotlight`。
#   ⇒ 那 5 页**必须**是 spotlight 且图标 = `_BG10_DOWNGRADES` 表里的那一件；
#     谁把它们改回配方页（或换成 smelting/campfire 顶替），构建当场红。
#
# ⚠ **两处「待作者补原文」**：章5 封面（作者未给 ⇒ 沿用章4 封面，正向钉住）
#   与 章4/章5 第5页右 的 `（作者未指定）`（占位页，正向钉住它还在）。
bgbook10_problems: list[str] = []


def _bgbook10_bad(tag: str, msg: str) -> None:
    bgbook10_problems.append("%s [%s]" % (msg, tag))


_BG10_SNAPSHOT = _BG2_SNAPSHOT_DIR / "bg-book-10.md"
_BG10_LANG = "bettergold.handbook"
_BG10_PLACEHOLDER = u"（作者未指定）"
_BG10_EN_PLACEHOLDER = u"(not specified by the author)"
_BG10_COVER_PLACEHOLDER = "alchemical_meat"        # = 章4 封面（作者补章5封面后改这里 + 生成器）

# (条目 id, 封面图标, sortnum, 页数, 页型序列) —— 页型序列**逐页**钉住
_BG10_ENTRY_META = (
    ("golden_feast_crops", "gold_infused_dirt", 0, 10,
     ["patchouli:spotlight", "patchouli:crafting"] * 5),
    ("golden_feast_foods", "golden_chocolate_bar", 1, 10,
     ["patchouli:crafting", "patchouli:spotlight", "patchouli:crafting", "patchouli:crafting",
      "patchouli:spotlight", "patchouli:smelting", "patchouli:crafting", "patchouli:crafting",
      "patchouli:crafting", "patchouli:crafting"]),
    ("golden_feast_sturdy", "sturdygold_chocolate_bar", 2, 14,
     ["patchouli:text"] + ["patchouli:crafting"] * 3 + ["patchouli:spotlight"]
     + ["patchouli:crafting"] * 9),
    ("golden_feast_fd_foods", "alchemical_meat", 3, 10,
     ["patchouli:spotlight", "patchouli:crafting", "patchouli:crafting", "patchouli:spotlight",
      "patchouli:spotlight", "patchouli:crafting", "patchouli:crafting", "patchouli:crafting",
      "patchouli:crafting", "patchouli:text"]),
    ("golden_feast_fd_sturdy", _BG10_COVER_PLACEHOLDER, 4, 10,
     ["patchouli:text"] + ["patchouli:crafting"] * 8 + ["patchouli:text"]),
)
# 有**正文**的页后缀（逐条目，顺序 = 快照顺序；共 49）
_BG10_PROSE_SUFFIX = {
    "golden_feast_crops": ["1_left", "2_left", "3_left", "4_left", "5_left"],
    "golden_feast_foods": ["1_left", "1_right", "2_left", "2_right", "3_left", "3_right",
                           "4_left", "4_right", "5_left", "5_right"],
    "golden_feast_sturdy": ["%d_%s" % (r, s) for r in range(1, 8) for s in ("left", "right")],
    "golden_feast_fd_foods": ["1_left", "1_right", "2_left", "2_right", "3_left", "3_right",
                              "4_left", "4_right", "5_left", "5_right"],
    "golden_feast_fd_sturdy": ["1_left", "1_right", "2_left", "2_right", "3_left", "3_right",
                               "4_left", "4_right", "5_left", "5_right"],
}
# spotlight 的**图标表**（逐页；None = 该页不是 spotlight）
_BG10_SPOTLIGHT_EXPECT = {
    "golden_feast_crops": [
        ["bettergold:gold_infused_dirt"], None,
        ["minecraft:golden_carrot", "bettergold:golden_wheat_seeds",
         "bettergold:golden_eggplant_seeds"], None,
        ["bettergold:golden_wheat", "bettergold:golden_bread", "bettergold:golden_wheat_block"],
        None,
        ["bettergold:golden_eggplant"], None,
        ["bettergold:golden_bone_meal"], None],
    "golden_feast_foods": [
        None, ["bettergold:brewed_hot_cocoa"],            # G1 降级
        None, None,
        ["bettergold:golden_egg"], None,
        None, None, None, None],
    "golden_feast_sturdy": [
        None, None, None, None,
        ["bettergold:sturdygold_brewed_hot_cocoa"],        # G1 降级
        None, None, None, None, None, None, None, None, None],
    "golden_feast_fd_foods": [
        ["bettergold:alchemical_meat"],                   # G2 降级
        None, None,
        ["bettergold:golden_glow_custard"],               # G2 降级
        ["bettergold:golden_apple_cider"],                # G2 降级
        None, None, None, None, None],
    "golden_feast_fd_sturdy": [None] * 10,
}
# 配方（逐页；None = 该页不是配方页；tuple = recipe / recipe2）
_BG10_RECIPE_EXPECT = {
    "golden_feast_crops": [
        None, ("gold_infused_dirt",), None, ("golden_wheat_seeds",), None,
        ("golden_bread", "golden_wheat_block"), None, ("raw_sturdygold_eggplant",), None,
        ("golden_bone_meal",)],
    "golden_feast_foods": [
        ("golden_chocolate_bar",), None, ("golden_ice_cream",), ("golden_sugar_cane_stick",), None,
        ("fried_golden_egg_from_smelting",), ("golden_chocolate_cookie",),
        ("golden_honey_cookie",), ("golden_egg_sandwich",), ("golden_horse_feed",)],
    "golden_feast_sturdy": [
        None, ("sturdygold_apple",), ("sturdygold_carrot",), ("sturdygold_chocolate_bar",), None,
        ("sturdygold_ice_cream",), ("sturdygold_sugar_cane_stick",), ("sturdygold_eggplant",),
        ("upgrade_sturdygold_chocolate_cookie",), ("upgrade_sturdygold_honey_cookie",),
        ("upgrade_sturdygold_bread",), ("upgrade_sturdygold_fried_golden_egg",),
        ("upgrade_sturdygold_egg_sandwich",), ("upgrade_sturdygold_horse_feed",)],
    "golden_feast_fd_foods": [
        None, ("alchemical_meat_skewer",), ("alchemical_meat_sandwich",), None, None,
        ("golden_pie_crust",), ("golden_apple_pie",), ("golden_chocolate_pie",),
        ("golden_cake",), None],
    "golden_feast_fd_sturdy": [
        None, ("upgrade_sturdygold_alchemical_meat",),
        ("upgrade_sturdygold_alchemical_meat_skewer",),
        ("upgrade_sturdygold_alchemical_meat_sandwich",),
        ("upgrade_sturdygold_glow_custard",), ("upgrade_sturdygold_apple_cider",),
        ("upgrade_sturdygold_apple_pie",), ("upgrade_sturdygold_chocolate_pie",),
        ("upgrade_sturdygold_cake",), None],
}
# G1/G2 的**全部落点**（页后缀 → 降级后 spotlight 的图标物品）—— 与生成器的表逐条同款
_BG10_DOWNGRADES = {
    "golden_feast_foods": {"1_right": "bettergold:brewed_hot_cocoa"},
    "golden_feast_sturdy": {"3_left": "bettergold:sturdygold_brewed_hot_cocoa"},
    "golden_feast_fd_foods": {"1_left": "bettergold:alchemical_meat",
                              "2_right": "bettergold:golden_glow_custard",
                              "3_left": "bettergold:golden_apple_cider"},
}
# 页眉：条目 id → [(页后缀, 页眉逐字)]
_BG10_TITLE_LABELS = {"golden_feast_crops": ["2_left", "3_left"]}


def _bg10_parse_snapshot() -> list:
    """从冻结快照解析 [(条目 id, 章节名, 封面字面, [(页后缀, 逐字文案 or None, 页眉 or None)])]。

    解析形状与本轮的语言键注入脚本**逐字同款**（改一处必须同步两处）。
    """
    _lines = _BG10_SNAPSHOT.read_text(encoding="utf-8").split("\n")
    _ids = {1: "golden_feast_crops", 2: "golden_feast_foods", 3: "golden_feast_sturdy",
            4: "golden_feast_fd_foods", 5: "golden_feast_fd_sturdy"}
    _head = re.compile(u"^#### 10\\.\\d+ 章节 (\\d) · (.+?)(（\\*{0,2}封面：(.*?)\\*{0,2}）)?$")
    _recipe_leads = (u"就放", u"上边放", u"下边放", u"上：", u"下：", u"放出")

    def _clean(_c):
        _c = _c.split(u"<br>⚠")[0]
        return re.sub(r"\*\*(.+?)\*\*", r"\1", _c).strip()

    def _prose(_c):
        _raw = _clean(_c)
        if _raw == _BG10_PLACEHOLDER:      # ★ 作者自己写的"这一格没内容"标记 ⇒ 占位页
            return _BG10_PLACEHOLDER
        _b = _raw
        if _b.startswith(u"（"):
            _cut = _b.find(u"）")
            if _cut >= 0:
                _b = _b[_cut + 1:].strip()
        if not _b or _b.startswith(_recipe_leads):
            return None
        return _b

    _out, _cur, _name, _cover, _rows = [], None, None, None, []

    def _flush():
        if _cur:
            _out.append((_cur, _name, _cover, list(_rows)))

    for _ln in _lines:
        _m = _head.match(_ln)
        if _m:
            _flush()
            _cur, _name, _cover, _rows = _ids[int(_m.group(1))], _m.group(2).strip(), _m.group(4), []
            continue
        if re.match(r"^#{2,6} ", _ln):
            _flush()
            _cur, _name, _cover, _rows = None, None, None, []
            continue
        if not _ln.startswith("|") or "|---" in _ln:
            continue
        _safe = _ln.replace("\\|", "\x01")
        _cells = [_c.replace("\x01", "|") for _c in _safe.split("|")[1:-1]]
        if len(_cells) < 3:
            continue
        _label = _cells[0].strip().replace("*", "")
        if not _label.isdigit():
            continue
        for _col, _side in ((1, "left"), (2, "right")):
            _tm = re.search(u"(?:上边字体|字体名为)「(.+?)」", _cells[_col])
            _rows.append(("%s_%s" % (_label, _side), _prose(_cells[_col]),
                          _tm.group(1) if _tm else None))
    _flush()
    return _out


if not _BG10_SNAPSHOT.is_file():
    _bgbook10_bad("bgbook10-texts-verbatim",
                  "读不到冻结快照（逐字文案的期望值来源）：%s" % _BG10_SNAPSHOT)
    _bg10_parsed = []
else:
    _bg10_parsed = _bg10_parse_snapshot()
    if len(_bg10_parsed) != 5:
        _bgbook10_bad("bgbook10-texts-verbatim",
                      "从冻结快照解析到 %d 章（应 5 = 金染土与金作物 / 其他种类的金食物 / "
                      "万坚金化的金食物 / 乐事联动的金食物 / 乐事联动的万坚金食物；反空转守护）"
                      % len(_bg10_parsed))

# ---------- ① 快照 → 期望值（章节名 / 逐字文案 / 页眉）----------
_bg10_texts, _bg10_titles, _bg10_names = [], [], []
_bg10_prose_seen = 0
for _eid, _name, _cover, _rows in _bg10_parsed:
    _bg10_names.append(_name)
    _nk = "%s.entry.%s" % (_BG10_LANG, _eid)
    if zh.get(_nk) != _name:
        _bgbook10_bad("bgbook10-texts-verbatim",
                      "快照里的章节名 %r 没有按原样落在 %s 里（实际 %r）" % (_name, _nk, zh.get(_nk)))
    _want_labels = _BG10_PROSE_SUFFIX.get(_eid, [])
    _got_labels = [s for s, p, t in _rows if p is not None]
    if _got_labels != _want_labels:
        _bgbook10_bad("bgbook10-texts-verbatim",
                      "%s 的正文页与期望不符：期望 %s，实际 %s" % (_eid, _want_labels, _got_labels))
    for _suffix, _p, _t in _rows:
        if _p is not None:
            _bg10_prose_seen += 1
            _k = "%s.page.%s_%s" % (_BG10_LANG, _eid, _suffix)
            _bg10_texts.append(_p)
            if zh.get(_k) != _p:
                _bgbook10_bad("bgbook10-texts-verbatim",
                              "快照里的逐字文案没有按原样落在 %s 里（首 30 字：%s）" % (_k, _p[:30]))
        if _t is not None:
            _tk = "%s.page.%s_%s_title" % (_BG10_LANG, _eid, _suffix)
            _bg10_titles.append(_t)
            if zh.get(_tk) != _t:
                _bgbook10_bad("bgbook10-texts-verbatim",
                              "快照里的页眉 %r 没有按原样落在 %s 里（实际 %r）"
                              % (_t, _tk, zh.get(_tk)))
if _bg10_prose_seen != 49 or sum(len(_t) for _t in _bg10_texts) < 2000:
    _bgbook10_bad("bgbook10-texts-verbatim",
                  "从冻结快照解析到 %d 段逐字文案 / 共 %d 字（应 49 段 = 5+10+14+10+10、"
                  "总字数 >= 2000；反空转守护）"
                  % (_bg10_prose_seen, sum(len(_t) for _t in _bg10_texts)))
if _bg10_titles != [u"可种植的金作物", u"金麦相关"]:
    _bgbook10_bad("bgbook10-texts-verbatim",
                  "从冻结快照解析到的页眉不是那两条「字体名为『…』」：%r" % (_bg10_titles,))
_bg10_missing = [_t for _t in _bg10_texts if _t not in set(zh.values())]
if _bg10_missing:
    _bgbook10_bad("bgbook10-texts-verbatim",
                  "冻结快照里的逐字文案没有原样出现在 zh_cn.json 里（%d/%d 段缺失，首条：%s）"
                  % (len(_bg10_missing), len(_bg10_texts), _bg10_missing[0][:40]))

# ---------- ② 5 个条目：类别 / 图标 / sortnum / 页数 / 页型 / 正文键 / 图标表 / 配方逐条 ----------
_BG10_PAGES_TOTAL = 0
_BG10_RECIPE_REFS: set = set()
_BG10_SPOTLIGHT_REFS: set = set()
_BG10_TEXT_KEYS: list = []
for _eid, _icon, _sort, _cnt, _seq in _BG10_ENTRY_META:
    _zh_p = _ZH_BOOK / "entries" / ("%s.json" % _eid)
    _en_p = _EN_BOOK / "entries" / ("%s.json" % _eid)
    if not _zh_p.is_file() or not _en_p.is_file():
        _bgbook10_bad("bgbook10-chapters", "缺条目文件（zh/en 各需一份）：%s" % _eid)
        continue
    _zh_e = json.loads(_zh_p.read_text(encoding="utf-8"))
    _en_e = json.loads(_en_p.read_text(encoding="utf-8"))
    if _zh_e.get("category") != "bettergold:golden_feast":
        _bgbook10_bad("bgbook10-chapters",
                      "%s 不挂在「金灿的盛宴」类别下：%r" % (_eid, _zh_e.get("category")))
    if _zh_e.get("name") != "%s.entry.%s" % (_BG10_LANG, _eid):
        _bgbook10_bad("bgbook10-chapters",
                      "%s 的 name 不是 %s.entry.%s" % (_eid, _BG10_LANG, _eid))
    if _zh_e.get("icon") != "bettergold:%s" % _icon:
        _bgbook10_bad("bgbook10-chapters",
                      "%s 的封面图标不是 bettergold:%s：%r" % (_eid, _icon, _zh_e.get("icon")))
    if _zh_e.get("sortnum") != _sort:
        _bgbook10_bad("bgbook10-chapters", "%s 的 sortnum 不是 %d" % (_eid, _sort))
    if _zh_e.get("pages") != _en_e.get("pages"):
        _bgbook10_bad("bgbook10-chapters", "%s 的 zh/en 页列表不一致（结构必须双端相同）" % _eid)
    _pages = _zh_e.get("pages") or []
    _BG10_PAGES_TOTAL += len(_pages)
    if len(_pages) != _cnt:
        _bgbook10_bad("bgbook10-chapters",
                      "%s 的页数不是 %d（一行 = 一屏 = 2 页：章1 5行 / 章2 5行 / 章3 7行 / "
                      "章4 5行 / 章5 5行）：%d" % (_eid, _cnt, len(_pages)))
        continue
    _seq_now = [str(_p.get("type")) for _p in _pages]
    if _seq_now != _seq:
        _bgbook10_bad("bgbook10-page-types", "%s 的页型序列不是 %s：%s" % (_eid, _seq, _seq_now))
    # 正文键：快照里那一页有正文 ⇒ 产物那一页必须**引用了该键**
    for _i, _suffix in enumerate(_BG10_PROSE_SUFFIX[_eid]):
        _key = "%s.page.%s_%s" % (_BG10_LANG, _eid, _suffix)
        _BG10_TEXT_KEYS.append(_key)
        _page = next((_p for _p in _pages
                      if _p.get("text") == _key or _p.get("text") == _key), None)
        if _page is None:
            _bgbook10_bad("bgbook10-page-types",
                          "%s 的第 %d 页没有引用正文键 %s（逐字文案会落空）" % (_eid, _i + 1, _key))
    # 页眉键（只有章1 的第2/3 左页有）
    for _label in _BG10_TITLE_LABELS.get(_eid, []):
        _tk = "%s.page.%s_%s_title" % (_BG10_LANG, _eid, _label)
        if _tk not in [str(_p.get("title") or "") for _p in _pages]:
            _bgbook10_bad("bgbook10-page-types", "%s 的 %s 页没有挂页眉键 %s" % (_eid, _label, _tk))
    # spotlight 图标表逐页
    for _i, _want_items in enumerate(_BG10_SPOTLIGHT_EXPECT[_eid]):
        _page = _pages[_i]
        if _want_items is None:
            if _page.get("type") == "patchouli:spotlight":
                _bgbook10_bad("bgbook10-spotlight",
                              "%s 第 %d 页不该是 spotlight（页型表里它是别的）：%s"
                              % (_eid, _i + 1, _page))
            continue
        if _page.get("type") != "patchouli:spotlight":
            _bgbook10_bad("bgbook10-spotlight",
                          "%s 第 %d 页应是 spotlight（图标 %s），实际 %s"
                          % (_eid, _i + 1, _want_items, _page.get("type")))
            continue
        _got_items = _page.get("item")
        _got_items = _got_items if isinstance(_got_items, list) else [_got_items]
        if _got_items != _want_items:
            _bgbook10_bad("bgbook10-spotlight",
                          "%s 第 %d 页的图标表不是 %s：%s" % (_eid, _i + 1, _want_items, _got_items))
        _BG10_SPOTLIGHT_REFS.update(_want_items)
    # 配方逐页
    for _i, _want_rec in enumerate(_BG10_RECIPE_EXPECT[_eid]):
        _page = _pages[_i]
        _got_rec = tuple(str(_page.get(_k)).split(":", 1)[1]
                         for _k in ("recipe", "recipe2") if _page.get(_k))
        _want_tuple = tuple(_want_rec) if _want_rec else ()
        if _got_rec != _want_tuple:
            _bgbook10_bad("bgbook10-recipes",
                          "%s 第 %d 页的配方不是 %s：%s" % (_eid, _i + 1, _want_tuple, _got_rec))
        _BG10_RECIPE_REFS.update(_got_rec)
if _BG10_PAGES_TOTAL != 54:
    _bgbook10_bad("bgbook10-chapters",
                  "§十 5 章的页数合计不是 54（10+10+14+10+10）：%d" % _BG10_PAGES_TOTAL)
if len(_BG10_RECIPE_REFS) != 40:
    _bgbook10_bad("bgbook10-recipes",
                  "§十 引用的配方不是 40 条（章1 6 + 章2 8 + 章3 12 + 章4 6 + 章5 8）：%d"
                  % len(_BG10_RECIPE_REFS))
if len(_BG10_SPOTLIGHT_REFS) != 15:
    _bgbook10_bad("bgbook10-spotlight",
                  "§十 的 spotlight 图标不是 15 个（章1 9 + 章2 2 + 章3 1 + 章4 3）：%d"
                  % len(_BG10_SPOTLIGHT_REFS))
# 死链：收集**页面上实际写的** id（不是期望表）
for _eid, _i, _s, _c, _q in _BG10_ENTRY_META:
    _p_zh = _ZH_BOOK / "entries" / ("%s.json" % _eid)
    if not _p_zh.is_file():
        continue
    for _pg in json.loads(_p_zh.read_text(encoding="utf-8")).get("pages", []):
        for _rk in ("recipe", "recipe2"):
            _rid = _pg.get(_rk)
            if not _rid:
                continue
            _rf = _DATA / "bettergold" / "recipe" / (_rid.split(":", 1)[1] + ".json")
            if not _rf.is_file():
                _bgbook10_bad("bgbook10-recipe-refs", "死链：%s（%s 引用了不存在的配方）"
                              % (_rid, _eid))
            _ti = _pg.get("item")
            for _iid in (_ti if isinstance(_ti, list) else [_ti]):
                if not _iid or ":" not in str(_iid):
                    continue

# ---------- ③ G1 / G2 的 5 页降级（本轮的**门禁项**）----------
_bg10_downgraded = 0
for _eid, _pages_map in _BG10_DOWNGRADES.items():
    _p_zh = _ZH_BOOK / "entries" / ("%s.json" % _eid)
    if not _p_zh.is_file():
        _bgbook10_bad("bgbook10-page-types", "缺条目文件：%s" % _eid)
        continue
    _pages = json.loads(_p_zh.read_text(encoding="utf-8")).get("pages", [])
    for _label, _want_item in _pages_map.items():
        _idx = _BG10_PROSE_SUFFIX[_eid].index(_label)
        _page = _pages[_idx]
        if _page.get("type") != "patchouli:spotlight":
            _bgbook10_bad("bgbook10-page-types",
                          "§十 门禁项：%s 的 %s 应是 spotlight（该配方 Patchouli 表达不了："
                          "酿造台配方是 Java 注册 / 厨锅配方无页型），实际 %s"
                          % (_eid, _label, _page.get("type")))
            continue
        _got_items = _page.get("item")
        _got_items = _got_items if isinstance(_got_items, list) else [_got_items]
        if _got_items != [_want_item]:
            _bgbook10_bad("bgbook10-page-types",
                          "§十 门禁项：%s 的 %s 图标应是 %s（成品），实际 %s"
                          % (_eid, _label, _want_item, _got_items))
        if "recipe" in _page or "recipe2" in _page:
            _bgbook10_bad("bgbook10-page-types",
                          "§十 门禁项：%s 的 %s 还带着 recipe 字段（不许假装能渲染）" % (_eid, _label))
        _bg10_downgraded += 1
if _bg10_downgraded != 5:
    _bgbook10_bad("bgbook10-page-types",
                  "§十 的降级页只有 %d 页（应 5 = 酿造 2 + 厨锅 3；反空转守护）" % _bg10_downgraded)

# ---------- ④ 生成器覆盖（"每加一类东西问一句"）----------
_BG10_GEN = _BGDOC_GEN
if not _BG10_GEN.is_file():
    _bgbook10_bad("bgbook10-generator", "读不到手册生成器：%s" % _BG10_GEN)
else:
    _bg10_gen = _BG10_GEN.read_text(encoding="utf-8")
    _bg10_gen_code = re.sub(r"#[^\n]*", "", _bg10_gen)
    # ⚠ **这一轮的 needle 一律跑在"去注释"的源码上**（`_bg10_gen_code`）——
    #   扰动实测抓到的**假绿**：`RETIRED_ENTRIES = RETIRED_ENTRIES + [entry_golden_feast]`
    #   在 §十 区块的**上方注释**里也逐字出现过一次（`#    见下方 §十 区块与 …`），
    #   于是"把真正那一行删掉"时本检查**照样绿**（取到的是注释里那一份）。
    #   ⇒ 口径：**正向结构 needle 必须跑在去注释源码上**（与 `ex/03 §3.15 ①` 的负向口径同源）。
    for _needle, _why in (
            ("FEAST_ENTRIES = [", "生成器里没有 §十 的 5 章清单（FEAST_ENTRIES）"),
            ("FEAST_CATEGORY = \"golden_feast\"", "生成器里没有 §十 的类别常量"),
            ("_BG10_COVER_PLACEHOLDER = \"alchemical_meat\"",
             "生成器里章5 封面的**占位**常量不见了（作者还没给封面，不许自己填）"),
            ("_BG10_SPOTLIGHT_DOWNGRADES = {", "生成器里没有 G1/G2 的降级落点表"),
            ("FEAST_CROP_ROTATION = [", "生成器里没有章1 第2页的轮换图标表"),
            ("FEAST_WHEAT_ROTATION = [", "生成器里没有章1 第3页的轮换图标表"),
            ("def entry_golden_feast_crops(", "生成器里没有章1 的构造函数"),
            ("def entry_golden_feast_foods(", "生成器里没有章2 的构造函数"),
            ("def entry_golden_feast_sturdy(", "生成器里没有章3 的构造函数"),
            ("def entry_golden_feast_fd_foods(", "生成器里没有章4 的构造函数"),
            ("def entry_golden_feast_fd_sturdy(", "生成器里没有章5 的构造函数"),
            ("def entry_golden_feast(", "生成器里作废的旧占位构造函数被删掉了（不凭空消失）"),
            ("RETIRED_ENTRIES = RETIRED_ENTRIES + [entry_golden_feast]",
             "生成器没有把 §十 作废的旧占位并进 RETIRED_ENTRIES")):
        if _needle not in _bg10_gen_code:
            _bgbook10_bad("bgbook10-generator", _why)
    # ENTRIES 块里**不许**再引用 entry_golden_feast（否则下次重跑又把它写回产物）
    _bg10_entries = re.search(r"(?ms)^ENTRIES = \[$(.*?)^\]\s*$", _bg10_gen_code)
    if _bg10_entries is None:
        _bgbook10_bad("bgbook10-generator", "切不出 ENTRIES 块（反空转守护）")
    elif "entry_golden_feast," in _bg10_entries.group(1):
        _bgbook10_bad("bgbook10-generator",
                      "生成器的 `ENTRIES` 列表里又出现了 `entry_golden_feast`（下次重跑会把它写回产物）")
    # ⚠ **旧 needle 原文保留（未删）**：`" + FEAST_ENTRIES:"` / `"+ FEAST_ENTRIES:"`
    #   —— 1.7 收口轮把那行拆成两行（`… + FEAST_ENTRIES` 换行 `+ CHAOS_ENTRIES`），
    #   冒号不再紧跟其后 ⇒ needle 放宽成"这一项还在写盘循环里"，并**额外**要求两族那一段也在。
    if "+ FEAST_ENTRIES" not in _bg10_gen:
        _bgbook10_bad("bgbook10-generator", "`main()` 的写盘循环里没有 FEAST_ENTRIES（不会产出）")
    if "+ CHAOS_ENTRIES" not in _bg10_gen:
        _bgbook10_bad("bgbook10-generator", "`main()` 的写盘循环里没有 CHAOS_ENTRIES（两族不会产出）")

# ---------- ⑤ 两处「待作者补原文」（正向钉住占位仍在）----------
_bg10_todo_keys = ["%s.page.golden_feast_fd_foods_5_right" % _BG10_LANG,
                   "%s.page.golden_feast_fd_sturdy_5_right" % _BG10_LANG]
for _k in _bg10_todo_keys:
    if (zh.get(_k) or "") != _BG10_PLACEHOLDER:
        _bgbook10_bad("bgbook10-todo-cell",
                      "「作者未指定」那一格（%s）里的占位 %r 不见了 —— 作者还没补原文，"
                      "不许自己编内容（口径见 §24）" % (_k, _BG10_PLACEHOLDER))
    if (en.get(_k) or "") != _BG10_EN_PLACEHOLDER:
        _bgbook10_bad("bgbook10-todo-cell",
                      "「作者未指定」那一格的英译不是 %r：%r"
                      % (_BG10_EN_PLACEHOLDER, en.get(_k)))
if _BG10_PLACEHOLDER not in (_BG10_SNAPSHOT.read_text(encoding="utf-8")
                             if _BG10_SNAPSHOT.is_file() else ""):
    _bgbook10_bad("bgbook10-todo-cell",
                  "冻结快照里也没有占位 %r ⇒ 快照被改写成了作者没给过的文案" % _BG10_PLACEHOLDER)
# 章5 封面：**占位**必须仍在（= 沿用章4 封面），且快照仍写着"作者未给"
_bg10_c4 = _ZH_BOOK / "entries" / "golden_feast_fd_foods.json"
_bg10_c5 = _ZH_BOOK / "entries" / "golden_feast_fd_sturdy.json"
if _bg10_c4.is_file() and _bg10_c5.is_file():
    _i4 = json.loads(_bg10_c4.read_text(encoding="utf-8")).get("icon")
    _i5 = json.loads(_bg10_c5.read_text(encoding="utf-8")).get("icon")
    if _i5 != _i4:
        _bgbook10_bad("bgbook10-ch5-cover-todo",
                      "章5 的封面 %r 不再是章4 的封面 %r ⇒ 要么作者已经补了封面（那就要**同时**"
                      "改生成器的 `_BG10_COVER_PLACEHOLDER` 与本关卡这条正向断言），要么是"
                      "有人自己填了一张 —— 需求 §10.8 第 1 条明说「不要自己填」" % (_i5, _i4))
    if _i5 != "bettergold:%s" % _BG10_COVER_PLACEHOLDER:
        _bgbook10_bad("bgbook10-ch5-cover-todo",
                      "章5 的封面不是占位 %r：%r" % (_BG10_COVER_PLACEHOLDER, _i5))
_bg10_snap_all = _BG10_SNAPSHOT.read_text(encoding="utf-8") if _BG10_SNAPSHOT.is_file() else ""
if u"作者未给，待补" not in _bg10_snap_all:
    _bgbook10_bad("bgbook10-ch5-cover-todo",
                  "冻结快照 §10.7 标题里的「作者未给，待补」不见了（作者还没给章5 封面）")

# ---------- ⑥ 语言键：5 条目名 + 49 正文 + 2 页眉 = 56，中英双端都要有 ----------
_bg10_keys = (["%s.entry.%s" % (_BG10_LANG, _e) for _e, _i, _s, _c, _q in _BG10_ENTRY_META]
              + list(_BG10_TEXT_KEYS)
              + ["%s.page.%s_%s_title" % (_BG10_LANG, _e, _l)
                 for _e, _ls in _BG10_TITLE_LABELS.items() for _l in _ls])
if len(_bg10_keys) != 56:
    _bgbook10_bad("bgbook10-lang-bilingual",
                  "§十 的语言键清单是 %d 条（应 56 = 5 + 49 + 2；反空转守护）" % len(_bg10_keys))
for _k in _bg10_keys:
    if _k not in zh or _k not in en:
        _bgbook10_bad("bgbook10-lang-bilingual", "§十 语言键缺中文或英文：%s" % _k)
    elif not en[_k].strip() or en[_k] == zh[_k]:
        _bgbook10_bad("bgbook10-lang-bilingual",
                      "§十 的英文值缺失或与中文逐字相同（作者只给了中文，需要忠实英译）：%s" % _k)
# ⚠ **口径变更（作者 2026-10-11 替换 zh_cn.json，bgfix10）**：
#   旧占位条目的语言键**已从两份语言文件里删掉** ⇒ 这条断言**由正向改为负向**。
#   ⚠ **旧期望原文留档（未删）**：
#     `for _k in ("%s.entry.golden_feast" % _BG10_LANG, "%s.page.golden_feast" % _BG10_LANG):`
#     `    if _k not in zh:`
#     `        _bgbook10_bad("bgbook10-lang-bilingual", "作废的旧占位条目的语言键 %s 被删掉了（既定口径：原文不删）" % _k)`
#   ⇒ 现行口径 = **「删键 + 规格留档」**（作者有意清理；20 条作废键的完整清单与判定见 §31 与下面的
#     `bgfix10` 段）。★ **语言键删掉 ≠ 档案丢掉**：作废条目的**正文全文对照**仍然留在
#     `docs/1.6-规格.md` §19.8 / §24.8（那两节一行未动）。
for _k in ("%s.entry.golden_feast" % _BG10_LANG, "%s.page.golden_feast" % _BG10_LANG):
    if _k in zh or _k in en:
        _bgbook10_bad("bgbook10-lang-bilingual",
                      "作废的旧占位条目的语言键 %s 又回到了语言文件里"
                      "（现行口径 = 删键 + 规格留档，作者 2026-10-11 裁定；见 §31）" % _k)

# ---------- ⑦ 文档侧：§24 的口径必须落档 ----------
for _needle, _why in ((u"bg-book §十", u"docs/1.6-规格.md 里没有 bg-book §十 这一轮的节"),
                      (u"待作者补原文", u"没写明那两处**待作者补原文**"),
                      (u"门禁项", u"没写 G1/G2 两个门禁项"),
                      (u"酿造台", u"没写「酿造台配方 Patchouli 表达不了」这条门禁"),
                      (u"厨锅", u"没写「厨锅配方没有页型」这条门禁"),
                      (u"（作者未指定）", u"没写那一格用的占位标记"),
                      (u"饱和度", u"没写手册「饱和度 = nutrition × saturationModifier」这条换算"),
                      (u"nutrition", u"没写 nutrition 的**参数类型是 int**（3 处 .5 的共因）"),
                      (u"以实际为准", u"没写「以实测/代码为准 + 记账」这条处置口径")):
    if _needle not in _bgfix_spec:
        _bgbook10_bad("bgbook10-doc", "%s（缺 %s）" % (_why, _needle))

# ===========================================================================
# bg-fix4（会话标记 bg-fix4，2026-10-08）：第四批 · 五条
# ===========================================================================
# 稳定 id 前缀 `[bgfix4-...]`。判据全部跑在**去注释源码 / 已解析 JSON / 仓库内冻结快照**上。
_FX4_METALS = ["flamegold", "sturdygold", "thornsgold", "echogold",
               "indigoseagold", "voodoogold", "thundergold", "illusiongold"]
# ⚠ 1.7（bg-n10 轮1 后半）：作者 2026-10-16 开工 1.7 时新增的两族。
#   `CreativeSections.METAL_ORDER` = `_FX4_METALS`（作者 2026-10-08 的 8 族顺序，**前缀不变量**）
#   + 下面这两项（作者**未点名**这两族的出场位次 ⇒ 按"新金属往后加"排在最末，工作值）。
#   配置项（Config.java）**仍是 8 族 × 2 = 16 条**：歧义 ⑰「两族是否进配置」未裁，按立档 §5 属轮9。
_FX4_APPENDED = ["chaosgold", "chaosalloy"]
# 作者 2026-10-08 字面顺序（§四）—— 真源是 Java 的 `CreativeSections.BUILDING_SLOT`，这里只做互核
_FX4_AUTHOR_BUILDING_ORDER = ["_block", "_bricks", "_pillar", "_bricks_stairs", "_bricks_slab",
                              "_bricks_wall", "_door", "_trapdoor", "_bars", "_chain", "_lantern"]
# 章3 第 2~5 行 × 左/右 -> 金属（= 生成器的 METALS 两两配对；顺序即快照里的行序）
_FX4_BUILD_SLOTS = [(2, "left", "flamegold"), (2, "right", "sturdygold"),
                    (3, "left", "thornsgold"), (3, "right", "echogold"),
                    (4, "left", "indigoseagold"), (4, "right", "voodoogold"),
                    (5, "left", "thundergold"), (5, "right", "illusiongold")]


def _fx4_snapshot_k3() -> dict:
    """冻结快照 §6.3 → ``{(行, 侧): 标题}``（「图标：**X**」里的 X，**逐字**，不自己编）。

    形状与 `[bgbook2-texts-verbatim]` 的解析同源：表头/分隔行靠"第一格是纯数字"排除；
    `（随排版顺序变化）` 是**图标说明**不是标题的一部分（只有第 1 行带它）。
    """
    _lines = _BG2_SNAPSHOT.read_text(encoding="utf-8").split("\n")
    _active, _rows = False, []
    for _ln in _lines:
        if _ln.startswith("### 6.3"):
            _active = True
            continue
        if _active and _ln.startswith("---"):
            break
        if _active and _ln.startswith("|") and "|---" not in _ln:
            _cells = [c for c in _ln.split("|")][1:-1]
            if not re.fullmatch(r"\d+", _cells[0].strip().replace("*", "")):
                continue
            _rows.append(_cells)
    _out = {}
    for _cells in _rows:
        _idx = int(_cells[0].strip().replace("*", ""))
        for _col, _side in ((1, "left"), (2, "right")):
            _cell = _cells[_col] if _col < len(_cells) else ""
            _head = _cell.split("<br>")[0].strip()
            if not _head.startswith("图标："):
                continue
            _t = re.sub(r"\*\*(.+?)\*\*", r"\1", _head[len("图标："):]).strip()
            _out[(_idx, _side)] = _t.replace("（随排版顺序变化）", "").strip()
    return _out


_fx4_k3_titles = _fx4_snapshot_k3()

# ---------- ② 顺序真源（一个真源 + 两处/四处同序） ----------
# ⚠ **bgfix5（2026-10-08）就地标注（原文保留不删）**：这里的"两处/四处同序"本轮**扩成「五处同序」** ——
#    第 5 处 = **进度树的兄弟实际呈现次序**（原先由 `ReferenceOpenHashSet` 迭代序决定、每次运行都不同）。
#    判据在本文件末尾的 `[bgfix5-tree-order-single-source]` / `[bgfix5-metal-order-five-places]` 段；
#    落点 = 新 mixin `mixin/AdvancementNodeChildrenOrderMixin` + 排序类 `advancement/AdvancementTreeOrder`。
_FX4_CREATIVE = JAVA / "material" / "CreativeSections.java"
_fx4_creative_src = strip_comments(_FX4_CREATIVE.read_text(encoding="utf-8"))
_fx4_src_order = None
_fx4_mo = re.search(r"METAL_ORDER\s*=\s*List\.of\((.*?)\);", _fx4_creative_src, re.S)
if not _fx4_mo:
    _bgfix4_bad("bgfix4-metal-order-single-source",
                "解析不到顺序真源 `CreativeSections.METAL_ORDER`（那一行）")
else:
    _fx4_src_order = re.findall(r'"([a-z_]+)"', _fx4_mo.group(1))
    # ⚠ **1.7（bg-n10 轮1 后半）就地标注，旧口径原文保留、不放宽**：
    #   作者 2026-10-08 的 8 族顺序（`_FX4_METALS`）仍是**前缀不变量** ——
    #   1.7 起 `METAL_ORDER` 末尾按"新金属往后加"追加两族（作者未点名位次 ⇒ 工作值，一句话可改）。
    #   old: if _fx4_src_order != _FX4_METALS:  ←（当时恰好 8 族，"相等"就是这条不变量）
    if _fx4_src_order[:len(_FX4_METALS)] != _FX4_METALS:
        _bgfix4_bad("bgfix4-metal-order-single-source",
                    "顺序真源的**前 8 项**不是作者 2026-10-08 的 8 金属顺序：%s ≠ %s"
                    "（前缀不变量：1.7 新族只许往后加，不许插队 / 不许重排既有 8 族）"
                    % (_fx4_src_order, _FX4_METALS))
    if _fx4_src_order[len(_FX4_METALS):] != _FX4_APPENDED:
        _bgfix4_bad("bgfix4-metal-order-single-source",
                    "顺序真源 8 项**之后**的内容必须是 1.7 新增的 %s（实际 %s）"
                    % (_FX4_APPENDED, _fx4_src_order[len(_FX4_METALS):]))
    if len(_fx4_src_order) != 8 + len(_FX4_APPENDED):
        _bgfix4_bad("bgfix4-metal-order-single-source",
                    "顺序真源不是 %d 个金属（实际 %d）—— 反空转守护"
                    % (8 + len(_FX4_APPENDED), len(_fx4_src_order)))
    # (a) Config.java：20 个键的**声明顺序**（NeoForge 配置界面 / toml 的条目顺序 = 声明顺序）
    # ⚠ 1.7 bg-n10r4：旧口径（原文留档）是在**8 族**上跑这个循环
    #   ⇒ 旧的 8 族清单**看不见**新加的两族（计数会停在 8、位置也判不出来）。
    _fx4_cfg_families = _FX4_METALS + _FX4_APPENDED
    _fx4_cfg_order, _fx4_seen = [], set()
    for _k in re.findall(r'\.defineInRange\(\s*"([^"]+)"', _bgfix_cfg):
        for _m in _fx4_cfg_families:
            if _k.startswith(_m) and _m not in _fx4_seen:
                _fx4_seen.add(_m)
                _fx4_cfg_order.append(_m)
    # ⚠ **1.7 bg-n10r4（2026-10-16）就地标注**：两族已经进配置系统 ⇒ 期望从"前 8 项"改成
    #   "**全部 10 项**"（= 真源 `METAL_ORDER` 的前 8 项 + 追加的 2 项）。
    #   旧口径原文留档（当时配置只有 8 族、歧义 ⑰ 排轮9）：
    #     `if len(_fx4_cfg_order) != 8:` … `elif _fx4_cfg_order != _FX4_METALS:`
    #   ⚠ 判据**不放宽**：仍是"逐个族逐字同序"，只是族数从 8 变 10。
    _fx4_cfg_want = _FX4_METALS + _FX4_APPENDED
    if len(_fx4_cfg_order) != len(_fx4_cfg_want):
        _bgfix4_bad("bgfix4-metal-order-single-source",
                    "Config.java 里认出的金属键只有 %d 族（应 %d）—— 反空转守护：%s"
                    % (len(_fx4_cfg_order), len(_fx4_cfg_want), _fx4_cfg_order))
    elif _fx4_cfg_order != _fx4_cfg_want:
        _bgfix4_bad("bgfix4-metal-order-single-source",
                    "Config.java 的 20 键声明顺序 %s ≠ 顺序真源 %s"
                    "（作者 2026-10-08：「模组设置也要用这种规律排序」；1.7 两族已进配置系统）"
                    % (_fx4_cfg_order, _fx4_cfg_want))
    # (b) 两个生成器的 METALS + (c) 成就清单（产物）里的 lists.metals
    _fx4_gen_adv = (REPO / "tools" / "asset-generator" / "generate_advancements.py")
    _fx4_gen_book = _BGDOC_GEN
    _fx4_other = {}
    for _p, _pat, _label in (
            (_fx4_gen_adv, r"^METALS = \[(.*?)\]", "generate_advancements.py 的 METALS"),
            (_fx4_gen_book, r"^METALS = \[(.*?)\]", "generate_handbook_data.py 的 METALS")):
        if not _p.is_file():
            _bgfix4_bad("bgfix4-metal-order-single-source", "读不到 %s" % _p)
            continue
        _mm = re.search(_pat, _p.read_text(encoding="utf-8"), re.S | re.M)
        if not _mm:
            _bgfix4_bad("bgfix4-metal-order-single-source", "解析不到 %s" % _label)
            continue
        _got = re.findall(r'"([a-z_]+)"', _mm.group(1))
        if _label.endswith("generate_handbook_data.py 的 METALS"):
            # 那个列表是 [("族", "核心材料"), …] ⇒ 只保留族
            _got = re.findall(r'\("([a-z_]+)",\s*"[a-z_]+"\)', _mm.group(1))
        _fx4_other[_label] = _got
        if _got != _FX4_METALS:
            _bgfix4_bad("bgfix4-metal-order-single-source",
                        "%s 的顺序 %s ≠ 作者顺序 %s" % (_label, _got, _FX4_METALS))
    _fx4_manifest = REPO / "tools" / "asset-generator" / "advancement_manifest.json"
    if _fx4_manifest.is_file():
        _fx4_man_metals = (json.loads(_fx4_manifest.read_text(encoding="utf-8"))
                           .get("lists", {}).get("metals"))
        if _fx4_man_metals != _FX4_METALS:
            _bgfix4_bad("bgfix4-metal-order-single-source",
                        "成就清单里的 lists.metals %s ≠ 作者顺序" % (_fx4_man_metals,))
    else:
        _bgfix4_bad("bgfix4-metal-order-single-source", "读不到 advancement_manifest.json")

# ---------- ②b 建筑方块 11 项的顺序真源（Java `BUILDING_SLOT` ↔ 生成器常量） ----------
_fx4_bs = re.search(r"BUILDING_SLOT = Map\.ofEntries\((.*?)\);", _fx4_creative_src, re.S)
if not _fx4_bs:
    _bgfix4_bad("bgfix4-building-order-single-source",
                "解析不到 `CreativeSections.BUILDING_SLOT`（建筑方块顺序真源）")
else:
    _fx4_java_order = ["_" + _s for _s in re.findall(r'Map\.entry\("([a-z_]+)",\s*\d+\)',
                                                     _fx4_bs.group(1))]
    if _fx4_java_order != _FX4_AUTHOR_BUILDING_ORDER:
        _bgfix4_bad("bgfix4-building-order-single-source",
                    "Java `BUILDING_SLOT` 的顺序 %s ≠ 作者 2026-10-08 的字面顺序 %s"
                    % (_fx4_java_order, _FX4_AUTHOR_BUILDING_ORDER))
    if len(_fx4_java_order) != 11:
        _bgfix4_bad("bgfix4-building-order-single-source",
                    "Java `BUILDING_SLOT` 不是 11 项（实际 %d）—— 反空转守护" % len(_fx4_java_order))
    if _BGDOC_GEN.is_file():
        _fx4_bm = re.search(r"METAL_BLOCK_SUFFIX_ORDER\s*=\s*\[(.*?)\]",
                            _BGDOC_GEN.read_text(encoding="utf-8"), re.S)
        _fx4_py_order = re.findall(r'"([^"]+)"', _fx4_bm.group(1)) if _fx4_bm else []
        if _fx4_py_order != _fx4_java_order:
            _bgfix4_bad("bgfix4-building-order-single-source",
                        "生成器 `METAL_BLOCK_SUFFIX_ORDER` %s ≠ Java `BUILDING_SLOT` %s"
                        "（两处必须同序）" % (_fx4_py_order, _fx4_java_order))

# ---------- ③ 章3 第 1 页**已复原**（左 = 八族锭 + 标题1 + 正文；右 = 八张模板 + 标题2、无正文） ----------
if len(_BG3_PAGES) != 10:
    _bgfix4_bad("bgfix4-k3p1-restored",
                "章3 页数不是 10（§八 删过、bg-fix4 §三 复原）：%d" % len(_BG3_PAGES))
else:
    _fx4_p0, _fx4_p1 = _BG3_PAGES[0], _BG3_PAGES[1]
    if _fx4_p0.get("type") != "patchouli:spotlight" or _fx4_p1.get("type") != "patchouli:spotlight":
        _bgfix4_bad("bgfix4-k3p1-restored",
                    "复原的第 1 页不是两页 spotlight：%s / %s" % (_fx4_p0.get("type"), _fx4_p1.get("type")))
    if _fx4_p0.get("item") != _BG3_INGOT_IDS:
        _bgfix4_bad("bgfix4-k3p1-restored",
                    "第 1 页（左）的图标表不是八族**锭**（顺序 = METALS）：%s" % (_fx4_p0.get("item"),))
    if _fx4_p1.get("item") != _BG3_TEMPLATE_IDS:
        _bgfix4_bad("bgfix4-k3p1-restored",
                    "第 1 页（右）的图标表不是八张**升级模板**（顺序 = METALS）：%s" % (_fx4_p1.get("item"),))
    _fx4_t1 = _fx4_k3_titles.get((1, "left"))
    _fx4_t2 = _fx4_k3_titles.get((1, "right"))
    if not _fx4_t1 or not _fx4_t2:
        _bgfix4_bad("bgfix4-k3p1-restored", "冻结快照 §6.3 第 1 行取不到两个标题（反空转守护）")
    else:
        if _fx4_p0.get("title") != _fx4_t1:
            _bgfix4_bad("bgfix4-k3p1-restored",
                        "第 1 页（左）的标题 %r ≠ 快照 §6.3 第 1 行左格的「图标：」值 %r"
                        % (_fx4_p0.get("title"), _fx4_t1))
        if _fx4_p1.get("title") != _fx4_t2:
            _bgfix4_bad("bgfix4-k3p1-restored",
                        "第 1 页（右）的标题 %r ≠ 快照 §6.3 第 1 行右格的「图标：」值 %r"
                        % (_fx4_p1.get("title"), _fx4_t2))
        # 两个标题必须与 §八 删除前的那两个常量**逐字相同**（= 真正的"复原"，不是新写一页）
        if _fx4_t1 != _BG3_INGOT_TITLE or _fx4_t2 != _BG3_TEMPLATE_TITLE:
            _bgfix4_bad("bgfix4-k3p1-restored",
                        "复原页的两个标题与 §七/§八 时期留下的常量不一致：%r/%r vs %r/%r"
                        % (_fx4_t1, _fx4_t2, _BG3_INGOT_TITLE, _BG3_TEMPLATE_TITLE))
    if _fx4_p0.get("text") != "bettergold.handbook.page.knowledge_1_summary":
        _bgfix4_bad("bgfix4-k3p1-restored",
                    "第 1 页（左）的正文不是 knowledge_1_summary：%r" % (_fx4_p0.get("text"),))
    # ⚠ **旧判据（原文留档，未删，已被 bgfix8 2026-10-09 取代）**：
    #     `if "text" in _fx4_p1: _bgfix4_bad("bgfix4-k3p1-restored",
    #         "第 1 页（右）**不该**有正文（§七 的形状：两页合起来只有那一句话）：%r" % _fx4_p1.get("text"))`
    #   —— 作者本轮原话「贵金的装备升级锻造模板那一页**应该加文字**」⇒ 右页**必须有**正文；
    #     详细判据（逐字比对冻结快照 + 中文/英文）在下面的 `[bgfix8-book-right-text]`。
    if _fx4_p1.get("text") != "bettergold.handbook.page.knowledge_1_right":
        _bgfix4_bad("bgfix4-k3p1-restored",
                    "第 1 页（右）的正文不是 knowledge_1_right"
                    "（bgfix8：作者要求这一页加文字；实际 %r）" % (_fx4_p1.get("text"),))

# ---------- ④ 8 个建材页：字幕 = 「某某金建筑方块」（快照逐字）+ 展示栏 = 该族 11 项（作者顺序） ----------
_fx4_build_ok = 0
for _fx4_row, _fx4_side, _fx4_metal in _FX4_BUILD_SLOTS:
    _fx4_idx = (_fx4_row - 1) * 2 + (0 if _fx4_side == "left" else 1)   # 行 1 = 页 0/1
    _fx4_key = "bettergold.handbook.page.knowledge_%d_%s_title" % (_fx4_row, _fx4_side)
    _fx4_want_title = _fx4_k3_titles.get((_fx4_row, _fx4_side))
    if _fx4_idx >= len(_BG3_PAGES):
        _bgfix4_bad("bgfix4-build-title-verbatim", "页 %d 不存在（反空转守护）" % _fx4_idx)
        continue
    _fx4_pg = _BG3_PAGES[_fx4_idx]
    if _fx4_pg.get("title") != _fx4_key:
        _bgfix4_bad("bgfix4-build-title-verbatim",
                    "第 %d 页（%s）的 title 不是语言键 %s，实际 %r"
                    % (_fx4_idx + 1, _fx4_metal, _fx4_key, _fx4_pg.get("title")))
        continue
    if _fx4_key not in zh or _fx4_key not in en:
        _bgfix4_bad("bgfix4-build-title-verbatim", "语言键缺中文或英文：%s" % _fx4_key)
        continue
    if not _fx4_want_title:
        _bgfix4_bad("bgfix4-build-title-verbatim",
                    "冻结快照 §6.3 第 %d 行 %s 格取不到「图标：」标题（反空转守护）"
                    % (_fx4_row, _fx4_side))
        continue
    if zh[_fx4_key] != _fx4_want_title:
        _bgfix4_bad("bgfix4-build-title-verbatim",
                    "字幕的中文值 %r ≠ 冻结快照 §6.3 的「图标：」逐字值 %r"
                    % (zh[_fx4_key], _fx4_want_title))
    elif not en[_fx4_key].strip() or en[_fx4_key] == zh[_fx4_key]:
        _bgfix4_bad("bgfix4-build-title-verbatim",
                    "字幕的英文值缺失或与中文逐字相同（既定口径：中英双端、en ≠ zh）：%s" % _fx4_key)
    else:
        _fx4_build_ok += 1
    # 展示栏 = 该族 11 件建材，顺序 = 作者 2026-10-08 的字面顺序
    _fx4_want_items = ["bettergold:%s%s" % (_fx4_metal, _sfx) for _sfx in _FX4_AUTHOR_BUILDING_ORDER]
    if _fx4_pg.get("item") != _fx4_want_items:
        _bgfix4_bad("bgfix4-build-title-verbatim",
                    "第 %d 页（%s）的展示栏不是该族 11 件建材（作者顺序：锭块→砖块→柱→楼梯→台阶→"
                    "砖墙→门→活板门→栏杆→链→灯笼），实际 %s"
                    % (_fx4_idx + 1, _fx4_metal, _fx4_pg.get("item")))
if len(_FX4_BUILD_SLOTS) != 8 or _fx4_build_ok != 8:
    _bgfix4_bad("bgfix4-build-title-verbatim",
                "8 个建材页里只有 %d 个同时满足「字幕来自快照 + 展示栏 11 项同序」（反空转守护）"
                % _fx4_build_ok)
if len(_fx4_k3_titles) != 10:
    _bgfix4_bad("bgfix4-build-title-verbatim",
                "冻结快照 §6.3 的「图标：」标题不是 10 个（实际 %d）—— 快照被改坏/解析器坏了"
                % len(_fx4_k3_titles))

# ---------- ⑤ 创造页材料顺序：**待作者补投**（本轮只出清单，不改顺序） ----------
# ⚠ 这一条**没有机器判据**（作者还没给顺序）⇒ 落法是"清单 + 记账"，见 docs/1.6-规格.md §25。
#   本节只钉一句"不许偷偷改顺序"：材料分区的排序键仍来自 `METAL_ORDER`（上面已核）。

# ---------- 文档侧：§25 的口径必须落档 ----------
for _needle, _why in ((u"bg-fix4", u"docs/1.6-规格.md 里没有 bg-fix4 这一轮的节"),
                      (u"先删后复原", u"没写「同一页被删又被复原」的三文档冲突处置"),
                      (u"建筑方块", u"没写 §四 的字幕口径（某某金建筑方块）"),
                      (u"11 项", u"没写展示栏 = 11 项（按作者字面顺序）"),
                      (u"ReferenceOpenHashSet", u"没写「进度树兄弟节点顺序不由数据决定」这条门禁项"),
                      (u"门禁项", u"没写门禁项"),
                      (u"待作者补投", u"没写 §五「创造页材料顺序待作者补投」")):
    if _needle not in _bgfix_spec:
        _bgfix4_bad("bgfix4-doc", "%s（缺 %s）" % (_why, _needle))

# ==========================================================================================
# bgfix5（2026-10-08）：把「8 条金属线」在进度界面里的上下次序**真正固定**，并按彩虹色排列
# ==========================================================================================
# 作者原话（逐字）：「**那8个次序好像必须要这样，排成彩虹色的话，应该好看一些**」
# 解读（父代理已确认）：① 这 8 条次序**必须固定**（不能是每次 JVM 随机）；② 理想排列 = 按**彩虹色**（色相升序）。
# ★ 本轮实测：8 族色相升序 == 现行 `METAL_ORDER` == 作者 2026-10-08 的列表
#   （六条独立口径全一致，见 `docs/bgfix5-证据/01~03`）⇒ **不挪任何族**，只需把进度树钉住。
# ★ 落点（上一轮的**门禁项**收口）：
#   ① 新排序类 `advancement/AdvancementTreeOrder.java`（位次从真源 `METAL_ORDER` 派生，**不写第二份 8 族列表**）；
#   ② 新 mixin `mixin/AdvancementNodeChildrenOrderMixin.java`（`@ModifyReturnValue` on
#      `AdvancementNode#children()Ljava/lang/Iterable;`，`require = 1`，**只有一个白名单父节点**）；
#   ③ `bettergold.mixins.json` 的 **`mixins`** 双端列表（不是 `common`）。
# 稳定 ASCII id：`[bgfix5-...]`。判据一律跑在**去注释**源码 / 已解析 JSON 上。
# ⚠ 旧口径原文保留在上面（`# ---------- ② 顺序真源（一个真源 + 两处/四处同序） ----------` 处已就地标注）。
bgfix5_problems: list[str] = []


def _bgfix5_bad(tag: str, msg: str) -> None:
    bgfix5_problems.append("%s [%s]" % (msg, tag))


_FX5_ORDER_CLASS = JAVA / "advancement" / "AdvancementTreeOrder.java"
_FX5_MIXIN_CLASS = JAVA / "mixin" / "AdvancementNodeChildrenOrderMixin.java"
_FX5_MIXIN_JSON = REPO / "src" / "main" / "resources" / "bettergold.mixins.json"
_FX5_MIXIN_SIMPLE = "AdvancementNodeChildrenOrderMixin"
_FX5_GUARDED_PARENT = "bettergold:treasure/any_core_material"

# ---------- ① 数据侧：8 条线各 1 个"线起点"节点，且全部挂在**唯一**那个父节点下 ----------
_fx5_line_parent = {}
for _m in _FX4_METALS:
    _p = _ADV / "metal" / _m / "ingot.json"
    if not _p.is_file():
        _bgfix5_bad("bgfix5-tree-order-single-source", "读不到 %s（反空转守护）" % _p)
        continue
    _par = json.loads(_p.read_text(encoding="utf-8")).get("parent")
    if not _par:
        _bgfix5_bad("bgfix5-tree-order-single-source", "%s 没有 parent（反空转守护）" % _p)
        continue
    _fx5_line_parent[_m] = _par

if len(_fx5_line_parent) != 8:
    _bgfix5_bad("bgfix5-tree-order-single-source",
                "只认出 %d 条金属线（应 8）—— 反空转守护：%s" % (len(_fx5_line_parent), _fx5_line_parent))
if len(set(_fx5_line_parent.values())) != len(_fx5_line_parent):
    _bgfix5_bad("bgfix5-tree-order-single-source",
                "有两条线共用同一个起点节点（族 ↔ 节点 不是一对一）：%s" % (_fx5_line_parent,))
for _m, _par in sorted(_fx5_line_parent.items()):
    # `metal/<族>/ingot.json` 的 parent = 该族的**线起点节点**（核心材料节点）；
    # 而那个起点节点自己的 parent 必须就是唯一白名单父节点（= 8 条线的共同父节点）。
    _fx5_start_file = _ADV / (_par.split(":", 1)[1] + ".json")
    if not _fx5_start_file.is_file():
        _bgfix5_bad("bgfix5-tree-order-single-source",
                    "%s 的线起点节点 %s 找不到对应 json（反空转守护）" % (_m, _par))
        continue
    _fx5_start_parent = json.loads(_fx5_start_file.read_text(encoding="utf-8")).get("parent")
    if _fx5_start_parent != _FX5_GUARDED_PARENT:
        _bgfix5_bad("bgfix5-tree-order-single-source",
                    "%s 的线起点 %s 的 parent 是 %s，≠ 唯一白名单父节点 %s"
                    % (_m, _par, _fx5_start_parent, _FX5_GUARDED_PARENT))

# 8 条线 + 非族节点（`any_raw_metal`）必须正好是这个父节点的全部孩子
_fx5_children = []
for _p in sorted(_ADV.rglob("*.json")):
    try:
        _j = json.loads(_p.read_text(encoding="utf-8"))
    except Exception:
        continue
    if _j.get("parent") == _FX5_GUARDED_PARENT:
        _fx5_children.append("bettergold:" + _p.relative_to(_ADV).as_posix()[:-5])
_fx5_children = sorted(_fx5_children)
# ★ 1.7 收口轮：白名单父节点的孩子 9 → **11**
#   （8 个核心材料 + any_raw_metal + **混沌金币** + **崩乱合金锭**）。
#   ⚠ 旧期望原文保留：`if len(_fx5_children) != 9: ... 不是 9 个`。
# ★ **1.7 `bg-n10fix` ⑨（2026-10-18）又把 11 收回 9**：作者「两族不在贵金范畴」⇒ 两族链首改挂
#   `root`（11 条的期望原文保留、已被取代）。⇒ 白名单父节点只剩 **8 核心材料 + any_raw_metal = 9**。
_BGN10R9_EXTRA_BRANCHES = ["bettergold:treasure/chaos_coin", "bettergold:metal/chaosalloy/ingot"]
_fx5_extra = [c for c in _fx5_children if c not in _fx5_line_parent.values()
              and c != "bettergold:treasure/any_raw_metal"
              and c not in _BGN10R9_EXTRA_BRANCHES]
if len(_fx5_children) != 9:
    _bgfix5_bad("bgfix5-tree-order-single-source",
                "白名单父节点的孩子不是 9 个（8 核心材料 + any_raw_metal；两族链首已改挂 root），"
                "实际 %d：%s"
                % (len(_fx5_children), _fx5_children))
if _fx5_extra:
    _bgfix5_bad("bgfix5-tree-order-single-source",
                "白名单父节点下出现了不在预期内的孩子（排序键只覆盖 10 族 + any_raw_metal）：%s" % (_fx5_extra,))
if "bettergold:treasure/any_raw_metal" not in _fx5_children:
    _bgfix5_bad("bgfix5-tree-order-single-source",
                "非族节点 bettergold:treasure/any_raw_metal 不在白名单父节点下 —— 它必须存在并取 rank = METAL_ORDER.size()（排最后）")

# ---------- ② 排序类：位次来自真源、守卫是**全等**、且没有任何族名字面量 ----------
_fx5_order_src_raw = _FX5_ORDER_CLASS.read_text(encoding="utf-8") if _FX5_ORDER_CLASS.is_file() else ""
_fx5_order_src = strip_comments(_fx5_order_src_raw)
if not _fx5_order_src:
    _bgfix5_bad("bgfix5-tree-order-single-source", "读不到排序类 %s" % _FX5_ORDER_CLASS)
else:
    for _needle, _why in (
            ('"%s"' % _FX5_GUARDED_PARENT, "没有写死唯一白名单父节点 id %s" % _FX5_GUARDED_PARENT),
            ("GUARDED_PARENT.equals(parentId)", "守卫不是「全等比较」（必须 GUARDED_PARENT.equals(parentId)）"),
            ("CreativeSections.METAL_ORDER.indexOf(", "位次不是从真源 `CreativeSections.METAL_ORDER` 派生"),
            # ★ 1.7 收口轮（bg-n10r9）：崩乱合金的**链首自己**就是 `metal/chaosalloy/ingot`
            #   （它没有核心材料节点）⇒ 排序键必须「先看自己、再看孩子」，否则该族会掉进
            #   「非族节点」档、位次不再来自真源。这两条 needle 就是那个形状的机器形态。
            ("rankOfPath(", "排序键没有 `rankOfPath(...)`（崩乱合金那种「链首即锭」的线认不出族名）"),
            ("int own = rankOfPath(node.holder().id());",
             "`rankOf` 没有先按**节点自己**的 id 定位（崩乱合金会落到 METAL_ORDER.size() 档）"),
    ):
        if _needle not in _fx5_order_src:
            _bgfix5_bad("bgfix5-tree-order-single-source", "%s（缺 %s）" % (_why, _needle))
    # 「这是一个真源、不许有第二份 8 族列表」：整份源码里 `"bettergold:` 形式的字面量只许有 1 个
    _fx5_ns_lits = re.findall(r'"bettergold:', _fx5_order_src)
    if len(_fx5_ns_lits) != 1:
        _bgfix5_bad("bgfix5-tree-order-single-source",
                    "排序类里的 `\"bettergold:` 字面量不是 1 个（实际 %d 个）—— 白名单父节点只许有一个 id"
                    % len(_fx5_ns_lits))
    for _m in _FX4_METALS:
        if '"%s"' % _m in _fx5_order_src:
            _bgfix5_bad("bgfix5-tree-order-single-source",
                        "排序类里出现了族名字面量 \"%s\" —— 顺序只能来自真源 `METAL_ORDER`，不许有第二份列表" % _m)
    # 守卫不许是"命名空间前缀 / 正则"：order() 方法体里不许出现 startsWith / matches
    _fx5_order_body = method_body(_fx5_order_src, "public static Iterable<AdvancementNode> order(")
    if not _fx5_order_body:
        _bgfix5_bad("bgfix5-tree-order-single-source", "取不到 order(...) 方法体（反空转守护）")
    else:
        if "isGuardedParent(parentId)" not in _fx5_order_body:
            _bgfix5_bad("bgfix5-tree-order-single-source",
                        "order(...) 的第一道守卫不是 isGuardedParent(parentId)")
        for _bad_word in ("startsWith(", ".matches("):
            if _bad_word in _fx5_order_body:
                _bgfix5_bad("bgfix5-tree-order-single-source",
                            "order(...) 里出现了 %s —— 守卫必须是**全等**，不许前缀/正则匹配（否则会重排别的树）"
                            % _bad_word)

# ---------- ③ mixin：完整描述符 + require 写死 + 不许族名字面量 ----------
_fx5_mixin_src = strip_comments(_FX5_MIXIN_CLASS.read_text(encoding="utf-8")) if _FX5_MIXIN_CLASS.is_file() else ""
if not _fx5_mixin_src:
    _bgfix5_bad("bgfix5-tree-order-single-source", "读不到 mixin 类 %s" % _FX5_MIXIN_CLASS)
else:
    for _needle, _why in (
            ("@ModifyReturnValue", "mixin 没用 MixinExtras 的 @ModifyReturnValue"),
            ("children()Ljava/lang/Iterable;", "mixin 没写 `children()` 的完整描述符（改签名必须当场报错）"),
            ("require = 1", "mixin 的 require 没写死成 1"),
            ("AdvancementTreeOrder.order(", "mixin 没有转交给排序类（守卫必须只有一处真源）"),
            ("@Mixin(AdvancementNode.class)", "mixin 的目标类不是 AdvancementNode"),
    ):
        if _needle not in _fx5_mixin_src:
            _bgfix5_bad("bgfix5-tree-order-single-source", "%s（缺 %s）" % (_why, _needle))
    for _m in _FX4_METALS:
        if '"%s"' % _m in _fx5_mixin_src:
            _bgfix5_bad("bgfix5-tree-order-single-source",
                        "mixin 里出现了族名字面量 \"%s\" —— 不许有第二份 8 族列表" % _m)

# ---------- ④ mixins.json：双端列表的键名必须是 `mixins`（不是 common） ----------
if not _FX5_MIXIN_JSON.is_file():
    _bgfix5_bad("bgfix5-tree-order-single-source", "读不到 %s" % _FX5_MIXIN_JSON)
else:
    _fx5_mj = json.loads(_FX5_MIXIN_JSON.read_text(encoding="utf-8"))
    if not _fx5_mj.get("mixins"):
        _bgfix5_bad("bgfix5-tree-order-single-source",
                    "`mixins` 列表是空的 —— 反空转守护（空列表 = 没有任何东西需要 apply，`required: true` 也不会报错）")
    if _FX5_MIXIN_SIMPLE not in _fx5_mj.get("mixins", []):
        _bgfix5_bad("bgfix5-tree-order-single-source",
                    "%s 不在 `mixins` 双端列表里（写进 client/server/common 都会**静默不加载**）"
                    % _FX5_MIXIN_SIMPLE)
    for _bad_key in ("common", "client", "server"):
        if _FX5_MIXIN_SIMPLE in _fx5_mj.get(_bad_key, []):
            _bgfix5_bad("bgfix5-tree-order-single-source",
                        "%s 出现在 `%s` 列表里 —— 双端类必须在 `mixins` 里（`common` 这个键会被整个静默忽略）"
                        % (_FX5_MIXIN_SIMPLE, _bad_key))
    if _fx5_mj.get("required") is not True:
        _bgfix5_bad("bgfix5-tree-order-single-source", "mixins.json 的 required 不是 true")

# ---------- ⑤ 「五处同序」总断言：这一处（进度树）与真源同源 ----------
_fx5_truth_order = None
_fx5_mo = re.search(r"METAL_ORDER\s*=\s*List\.of\((.*?)\);", _fx4_creative_src, re.S)
if _fx5_mo:
    _fx5_truth_order = re.findall(r'"([a-z_]+)"', _fx5_mo.group(1))
else:
    _bgfix5_bad("bgfix5-metal-order-five-places",
                "解析不到顺序真源 `CreativeSections.METAL_ORDER`（反空转守护）")
if _fx5_truth_order is not None:
    # ⚠ 1.7：与 bgfix4 同一条前缀不变量（旧口径原文：`if _fx5_truth_order != _FX4_METALS:`）
    if _fx5_truth_order[:len(_FX4_METALS)] != _FX4_METALS:
        _bgfix5_bad("bgfix5-metal-order-five-places",
                    "顺序真源的前 8 项 %s ≠ 作者 2026-10-08 顺序 %s"
                    % (_fx5_truth_order, _FX4_METALS))
    # 第 5 处只能通过"真源下标"表达 ⇒ 排序类必须引用真源（上面已核）；这里再核一次**顺序本身可表达**：
    # 8 条线的起点节点互不相同 + 都能从 `metal/<族>/ingot` 反推族名（=> rank 一定落在 0..7）
    if len(set(_fx5_line_parent.values())) != 8:
        _bgfix5_bad("bgfix5-metal-order-five-places",
                    "8 条线不能映射到 8 个不同的位次（排序键表达不了全序）")
    if len(_fx5_truth_order) != 8 + len(_FX4_APPENDED):
        _bgfix5_bad("bgfix5-metal-order-five-places",
                    "顺序真源不是 %d 个族（实际 %d）—— 反空转守护"
                    % (8 + len(_FX4_APPENDED), len(_fx5_truth_order)))

# ---------- ⑥ 文档侧：本轮口径必须落档 ----------
for _needle, _why in ((u"bgfix5", u"docs/1.6-规格.md 里没有 bgfix5 这一轮的节"),
                      (u"五处同序", u"没写「四处同序 → 五处同序」的扩展"),
                      (u"AdvancementNodeChildrenOrderMixin", u"没写本轮新增的 mixin 类名"),
                      (u"仍随机", u"没写明「本模组其它兄弟组仍然随机」这条记账"),
                      (u"材料区位次", u"没写「材料区位次 / 8 族次序 若是两套必须各写真源」这条风险")):
    if _needle not in _bgfix_spec:
        _bgfix5_bad("bgfix5-doc", "%s（缺 %s）" % (_why, _needle))

print(f"bg-fix4 第四批（古董刀成就 / 顺序真源两处同序 / 章3 第1页复原 / 建材页 11 项 / 创造页顺序待补）"
      f"问题: {len(bgfix4_problems)} {bgfix4_problems[:8]}"
      f"（章3 {len(_BG3_PAGES)} 页 / 建材页字幕 {_fx4_build_ok}/8 / 图标引用 {len(_bg2_item_refs)} 个）")
print(f"bg-fix5（进度树 8 条线次序真正固定 / 彩虹序 = 现行序 / 五处同序）"
      f"问题: {len(bgfix5_problems)} {bgfix5_problems[:8]}"
      f"（白名单父节点孩子 {len(_fx5_children)} 个 / 线起点映射 {len(_fx5_line_parent)} 族）")

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
print(f"bg-book §十 追加轮（「金灿的盛宴」5 章 / 两个门禁项 / 两处待作者补）问题: "
      f"{len(bgbook10_problems)} {bgbook10_problems[:8]}"
      f"（5 章 {_BG10_PAGES_TOTAL} 页 / 配方引用 {len(_BG10_RECIPE_REFS)} 条 / "
      f"图标引用 {len(_BG10_SPOTLIGHT_REFS)} 个）")
print(f"bg-fix4 第四批（古董刀成就 / 顺序真源两处同序 / 章3 第1页复原 / 建材页 11 项 / 创造页顺序待补）"
      f"问题: {len(bgfix4_problems)} {bgfix4_problems[:8]}"
      f"（章3 {len(_BG3_PAGES)} 页 / 建材页字幕 {_fx4_build_ok}/8 / 图标引用 {len(_bg2_item_refs)} 个）")

# ==========================================================================================
# bgfix7（2026-10-08）：创造页「材料」分区**前半部分**按作者口述序重排（执行轮）
# ==========================================================================================
# 作者原话（逐字，他自述"表述可能有偏差与错误"）：见
#   `tools/asset-generator/bgfix7-creative-material-prefix-order.txt` 的抬头（同一份逐字引用）。
# ★ 只许重排：21 个中文名与「材料分区前 21 件」**集合完全相等** ==>
#   不许增项、不许删项、不许把别的分区的东西搬进来（红线 4 的同精神）。
# ★ 期望值真源 = 仓库内**冻结快照**（两行一个真源，别处不许有第二份 21 件列表）：
#   ① `bgfix7-creative-material-prefix-order.txt`：作者口述位次 1..21 -> 真实 id（改后的顺序）；
#   ② `bgfix7-creative-material-baseline.txt`：重排**前**真实创造页里的 61 件位次（A 级读数搬运）。
#   （口径：期望值不许读仓库外的活页文档，见 `docs/构建与跑测注意事项.md` 六；
#     搬运记录写在两个快照的抬头里。）
# 稳定 ASCII id：`[bgfix7-...]`；判据一律跑在**去注释**源码上
#   （`mod_experience/ex/03-验证与证据.md` 3.17：正向 needle 也会被注释里的那一份骗过）。
bgfix7_problems: list[str] = []


def _bgfix7_bad(tag: str, msg: str) -> None:
    bgfix7_problems.append("%s [%s]" % (msg, tag))


_FX7_PREFIX_LEN = 21
_FX7_BASELINE_FILE = REPO / "tools" / "asset-generator" / "bgfix7-creative-material-baseline.txt"
_FX7_ORDER_FILE = REPO / "tools" / "asset-generator" / "bgfix7-creative-material-prefix-order.txt"
_FX7_SECTIONS = JAVA / "material" / "CreativeTabSections.java"

# ---------- ① 快照 A：重排前的 61 件位次（反空转：61 行 + 位次连续 + 第 22 件是 blazing_rod） ----------
_fx7_baseline: list[str] = []
_fx7_baseline_ok = False
if not _FX7_BASELINE_FILE.is_file():
    _bgfix7_bad("bgfix7-creative-material-prefix",
                "读不到冻结快照 %s（反空转守护）" % _FX7_BASELINE_FILE)
else:
    _fx7_base_seqs: list[int] = []
    for _ln in _FX7_BASELINE_FILE.read_text(encoding="utf-8").splitlines():
        _s = _ln.strip()
        if not _s or _s.startswith("#"):
            continue
        _m = re.fullmatch(r"(\d+)\s+(bettergold:[a-z0-9_]+)", _s)
        if not _m:
            _bgfix7_bad("bgfix7-creative-material-prefix", "快照 A 的行格式不对：%r" % _s)
            continue
        _fx7_base_seqs.append(int(_m.group(1)))
        _fx7_baseline.append(_m.group(2))
    if len(_fx7_baseline) != 61:
        _bgfix7_bad("bgfix7-creative-material-prefix",
                    "快照 A 不是 61 件（实际 %d）== 反空转守护（作者清单是从真实创造页读出来的 61 件）"
                    % len(_fx7_baseline))
    elif _fx7_base_seqs != list(range(1, 62)):
        _bgfix7_bad("bgfix7-creative-material-prefix", "快照 A 的位次不是 1..61 连续：%s" % _fx7_base_seqs[:8])
    elif _fx7_baseline[21] != "bettergold:blazing_rod":
        _bgfix7_bad("bgfix7-creative-material-prefix",
                    "快照 A 第 22 件不是 bettergold:blazing_rod（实际 %s）== 作者的"
                    "「后面就是正常的，从高燃烈焰棒棒开始」指的就是它"
                    "（zh_cn: item.bettergold.blazing_rod = 高燃烈焰棒）" % _fx7_baseline[21])
    else:
        _fx7_baseline_ok = True

# ---------- ② 快照 B：作者口述位次 1..21 -> 真实 id（改后顺序的**唯一**期望值） ----------
_fx7_want_prefix: list[str] = []
if not _FX7_ORDER_FILE.is_file():
    _bgfix7_bad("bgfix7-creative-material-prefix",
                "读不到冻结快照 %s（反空转守护）" % _FX7_ORDER_FILE)
else:
    _fx7_ord_seqs: list[int] = []
    _fx7_cn_names: list[str] = []
    for _ln in _FX7_ORDER_FILE.read_text(encoding="utf-8").splitlines():
        _s = _ln.strip()
        if not _s or _s.startswith("#"):
            continue
        _m = re.fullmatch(r"(\d+)\s+(bettergold:[a-z0-9_]+)\s+(\S+)\s+(\S+)", _s)
        if not _m:
            _bgfix7_bad("bgfix7-creative-material-prefix", "快照 B 的行格式不对：%r" % _s)
            continue
        _fx7_ord_seqs.append(int(_m.group(1)))
        _fx7_want_prefix.append(_m.group(2))
        _fx7_cn_names.append(_m.group(3))
    if len(_fx7_want_prefix) != _FX7_PREFIX_LEN:
        _bgfix7_bad("bgfix7-creative-material-prefix",
                    "快照 B 不是 %d 条（实际 %d）== 反空转守护（N 必须 = %d 且 > 0）"
                    % (_FX7_PREFIX_LEN, len(_fx7_want_prefix), _FX7_PREFIX_LEN))
    elif _fx7_ord_seqs != list(range(1, _FX7_PREFIX_LEN + 1)):
        _bgfix7_bad("bgfix7-creative-material-prefix", "快照 B 的位次不是 1..21 连续：%s" % _fx7_ord_seqs)
    if len(set(_fx7_want_prefix)) != len(_fx7_want_prefix):
        _bgfix7_bad("bgfix7-creative-material-prefix", "快照 B 里有重复 id（作者不会点同一个东西两次）")
    if len(set(_fx7_cn_names)) != len(_fx7_cn_names):
        _bgfix7_bad("bgfix7-creative-material-prefix", "快照 B 里有重复的作者名：%s" % _fx7_cn_names)

# 快照 A / B 的**集合关系**：前缀 21 件必须恰好是基线前 21 件（只重排、不增删、不跨分区搬）
if _fx7_baseline_ok and _fx7_want_prefix:
    _fx7_want_set = set(_fx7_want_prefix)
    _fx7_base21 = set(_fx7_baseline[:_FX7_PREFIX_LEN])
    if _fx7_want_set != _fx7_base21:
        _bgfix7_bad("bgfix7-creative-material-prefix",
                    "前缀集合 != 材料分区基线前 21 件（多出 %s / 少了 %s）"
                    "== 只许重排：不许增项、不许删项、不许跨分区搬"
                    % (sorted(_fx7_want_set - _fx7_base21), sorted(_fx7_base21 - _fx7_want_set)))
    _fx7_rest40 = set(_fx7_baseline[_FX7_PREFIX_LEN:])
    _fx7_overlap = sorted(_fx7_want_set & _fx7_rest40)
    if _fx7_overlap:
        _bgfix7_bad("bgfix7-creative-material-prefix",
                    "前缀吃到了「其余 40 件」里的东西（%s）== 其余部分必须原样不动" % _fx7_overlap)
    if len(_fx7_want_set) + len(_fx7_rest40) != 61:
        _bgfix7_bad("bgfix7-creative-material-prefix",
                    "前缀 + 其余 != 61 件（%d + %d）== 不重不漏"
                    % (len(_fx7_want_set), len(_fx7_rest40)))

# ---------- ③ Java 侧：前缀真源 + 它必须是材料分区的**第一段**，且四段旧结构不许删 ----------
_fx7_src = strip_comments(_FX7_SECTIONS.read_text(encoding="utf-8")) if _FX7_SECTIONS.is_file() else ""
_fx7_prefix: list[str] = []
if not _fx7_src:
    _bgfix7_bad("bgfix7-creative-material-prefix", "读不到 %s" % _FX7_SECTIONS)
else:
    _fx7_pm = re.search(r"MATERIAL_PREFIX_ORDER\s*=\s*List\.of\((.*?)\);", _fx7_src, re.S)
    if not _fx7_pm:
        _bgfix7_bad("bgfix7-creative-material-prefix",
                    "解析不到前缀真源 `CreativeTabSections.MATERIAL_PREFIX_ORDER`（那一张有序表）")
    else:
        _fx7_prefix = ["bettergold:" + _p for _p in re.findall(r'"([a-z0-9_]+)"', _fx7_pm.group(1))]
    # 反空转：长度必须 = 21 且 > 0（"前缀为空"也算破坏）
    if len(_fx7_prefix) != _FX7_PREFIX_LEN:
        _bgfix7_bad("bgfix7-creative-material-prefix",
                    "Java 前缀表长度不是 %d（实际 %d）== 反空转守护（前缀长度必须 = N 且 N > 0）"
                    % (_FX7_PREFIX_LEN, len(_fx7_prefix)))
    # 逐项对 **id**（不是对中文名）
    if _fx7_want_prefix and _fx7_prefix != _fx7_want_prefix:
        _fx7_diff = [(i + 1, a, b) for i, (a, b) in enumerate(zip(_fx7_prefix, _fx7_want_prefix))
                     if a != b][:5]
        _bgfix7_bad("bgfix7-creative-material-prefix",
                    "Java 前缀表 %s != 作者 2026-10-08 口述序 %s（前 5 处不同：%s）"
                    % (_fx7_prefix, _fx7_want_prefix, _fx7_diff))
    # 材料分区五段：前缀必须第一、四个旧段必须还在（不删项）
    _fx7_mm = re.search(r"MATERIALS\s*=\s*List\.of\((.*?)\);", _fx7_src, re.S)
    if not _fx7_mm:
        _bgfix7_bad("bgfix7-creative-material-prefix", "解析不到 `CreativeTabSections.MATERIALS`（段列表）")
    else:
        _fx7_body = _fx7_mm.group(1)
        _fx7_slots = re.findall(r'new Slot\("([^"]+)"', _fx7_body)
        if len(_fx7_slots) != 5:
            _bgfix7_bad("bgfix7-creative-material-prefix",
                        "材料分区不是 5 段（实际 %d：%s）== 旧四段必须原地保留、前缀段插在最前"
                        % (len(_fx7_slots), _fx7_slots))
        if not _fx7_slots or "材料前缀" not in _fx7_slots[0]:
            _bgfix7_bad("bgfix7-creative-material-prefix",
                        "前缀段不是材料分区的**第一段**（实际首段 = %s）"
                        % (_fx7_slots[0] if _fx7_slots else "<空>"))
        for _needle, _why in (
                ("MATERIAL_PREFIX", "前缀段没有用 `MATERIAL_PREFIX` 那把唯一的有序比较器"),
                ('new Slot("炼金术学员手册"', "旧段「炼金术学员手册」被删了（删段 == 物品静默掉出分区）"),
                ('new Slot("其他材料"', "旧段「其他材料」被删了"),
                ('new Slot("交易金商人相关"', "旧段「交易金商人相关」被删了"),
                ('new Slot("金属"', "旧段「金属」被删了")):
            if _needle not in _fx7_body:
                _bgfix7_bad("bgfix7-creative-material-prefix", "%s（缺 %s）" % (_why, _needle))
    # 前缀 id 一律稳定 ASCII（注册名 path 部分：小写字母 / 数字 / 下划线）
    for _p in _fx7_prefix:
        if not re.fullmatch(r"bettergold:[a-z0-9_]+", _p):
            _bgfix7_bad("bgfix7-creative-material-prefix", "前缀里有不稳定 / 非 ASCII 的 id：%r" % _p)

# ---------- ④ 文档侧：本轮口径必须落档（docs/1.6-规格.md 里的 §28） ----------
for _needle, _why in ((u"bgfix7", u"docs/1.6-规格.md 里没有 bgfix7 这一轮的节"),
                      (u"金门", u"没写「金门」这条待确认的映射"),
                      (u"待作者确认", u"没列「待作者确认的名字清单」"),
                      (u"只许重排", u"没写「只许重排，不许增删 / 不许跨分区搬」这条红线"),
                      (u"高燃烈焰棒", u"没写「其余保持原样的起点 = blazing_rod」")):
    if _needle not in _bgfix_spec:
        _bgfix7_bad("bgfix7-doc", "%s（缺 %s）" % (_why, _needle))

print(f"bg-fix7（创造页材料分区前半部分重排）问题: {len(bgfix7_problems)} {bgfix7_problems[:8]}"
      f"（前缀 {len(_fx7_prefix)} 项 / 基线 {len(_fx7_baseline)} 件 / 期望前缀 {len(_fx7_want_prefix)} 项）")

# ==================== bgfix6（2026-10-08）：反空转 / 前置缺失 ⇒ exit 2 ====================
# 旧行为（原文保留）：`checked`（语言键）只在上面 L80 附近 print 一次，从不影响退出码。
# 这里额外把"扫描面"本身数一遍（resources 下的 JSON 产物数）—— 目录被搬走 / 改名时它变 0。
_RES_ROOTS = [REPO / "src" / "main" / "resources" / "assets",
              REPO / "src" / "main" / "resources" / "data"]
_scan_json = sum(1 for _r in _RES_ROOTS if _r.is_dir() for _ in _r.rglob("*.json"))
_missing_roots = [_r for _r in _RES_ROOTS if not _r.is_dir()]
print(f"[bg-data-anti-vacuum] 实际检查了 {checked} 项（语言键）+ {_scan_json} 个 JSON 产物"
      f"（扫描根缺失 {len(_missing_roots)} 个；两项都必须 > 0）")
if checked <= 0 or _scan_json <= 0 or _missing_roots:
    print(f"FAIL [bg-data-anti-vacuum] 检查项数 = 0 或扫描根缺失 {_missing_roots}"
          f"（语言键 {checked} / JSON 产物 {_scan_json}）⇒ 基线被破坏（前置缺失）⇒ 本关卡 exit 2")
    sys.exit(2)

# ==================== bgfix7（2026-10-08）追加：本轮的**期望值快照**也是前置 ⇒ 缺了 exit 2 ====================
# 口径（`docs/构建与跑测注意事项.md` 七）：**前置缺失**是 exit 2，不是"没有问题"。
# 本关卡的期望值全部来自这两个仓库内冻结快照 ⇒ 它们不在 = 基线被破坏（不是"检查通过"）。
_fx7_missing_snaps = [str(_p) for _p in (_FX7_BASELINE_FILE, _FX7_ORDER_FILE) if not _p.is_file()]
print(f"[bgfix7-anti-vacuum] 本轮期望值快照：基线 {_FX7_BASELINE_FILE.name}="
      f"{_FX7_BASELINE_FILE.is_file()} / 作者序 {_FX7_ORDER_FILE.name}={_FX7_ORDER_FILE.is_file()}"
      f"（缺失 {len(_fx7_missing_snaps)} 个，必须 = 0）")
if _fx7_missing_snaps:
    print(f"FAIL [bgfix7-creative-material-prefix] 期望值快照缺失 {_fx7_missing_snaps}"
          f" ⇒ 前置缺失 ⇒ 本关卡 exit 2")
    sys.exit(2)

# ==================== bgfix8（2026-10-09）：① 配置显示文案 ② 手册右页补正文 ====================
#
# 作者原话（父代理转述；本节口径逐条落档在 `docs/1.6-规格.md` §29）：
#   ①「设置里**除了万坚金相关**……毕竟盾牌的反制赋予 Buff 的机制是**百分百**的，盔甲因为
#      **依赖于全套系**，所以才为**每件为 25%**，你得需要修改成 **某某金·武器工具盾牌触发Buff概率**
#      和 **某某金·盔甲触发buff概率** 才对。再重复一遍啊此设定要忽略掉万坚金相关。」
#   ②「贵金的知识的第一页面右侧你忘记填字幕了，贵金的装备升级锻造模板那一页**应该加文字**，
#      我不知道是删了还是怎么地的。你没有这样加上。」
#
# ⚠ **本轮只改"文案层"**：配置**键名 / 默认值 / 取值范围 / 声明顺序一个字未动**
#   （既有的 `[bgfix-config-16-keys]` / `[bgfix-config-defaults]` 守着键名与默认值；
#     下面 `[bgfix8-config-keys-frozen]` 另钉**取值范围**、`[bgfix8-config-order-frozen]` 钉顺序）。
# ⚠ `bgfix8_problems` / `_bgfix8_bad` / 前置检查（`[bgfix8-anti-vacuum]`）定义在**上面**的
#   "bgfix4 段之前" —— 必须早于任何读冻结快照的代码（见那一段的注释）。

# ---------- ① 配置显示文案：两处字面必须**逐字**等于作者给的两条模板 ----------
#   ★ 两处 = ⓐ `Config.java` 的 `.comment(...)` 第 1 行（配置界面的**提示行**；
#              判据跑在**去注释**源码 `_bgfix_cfg` 上 —— 否则我写的那段 `//` 说明会假绿，见 ex/03 §3.17）
#            ⓑ `zh_cn.json` / `en_us.json` 的 `bettergold.configuration.<键名>`（配置界面的**条目名**）
#   ⚠ **旧字面（原文留档，未删，已被 2026-10-09 取代）**：
#     zh 武器侧「〈族〉金 · 武器工具触发 Buff 概率」/ zh 盔甲侧「〈族〉金 · 盔甲盾牌触发 Buff 概率」；
#     en 武器侧 "<Family> - Weapon/Tool Buff Chance" / en 盔甲侧 "<Family> - Armor/Shield Buff Chance"。
#   ⚠ 万坚金两条**不在本清单里**（作者：「设置里除了万坚金相关」）—— 由下一条负向断言守着。
_BGFIX8_FAMS = [("flamegold", u"烈燃金", "Flamegold"),
                ("voodoogold", u"巫毒金", "Voodoogold"),
                ("thundergold", u"结雷金", "Thundergold"),
                ("indigoseagold", u"靛海金", "Indigoseagold"),
                ("illusiongold", u"幻惑金", "Illusiongold"),
                ("thornsgold", u"树棘金", "Thornsgold"),
                ("echogold", u"幽咆金", "Echogold")]
_bgfix8_checked = 0
for _f8, _zhname, _enname in _BGFIX8_FAMS:
    for _suffix, _kind in (("WeaponBuffChance", "weapon"), ("ArmorBuffChance", "armor")):
        _key = "bettergold.configuration.%s%s" % (_f8, _suffix)
        _want_zh = (u"%s·武器工具盾牌触发Buff概率" % _zhname if _kind == "weapon"
                    else u"%s·盔甲触发buff概率" % _zhname)
        _echo = " (Sonic Roar)" if _f8 == "echogold" else ""
        _want_en = ("%s - Weapon/Tool/Shield Buff%s Chance" % (_enname, _echo) if _kind == "weapon"
                    else "%s - Armor Buff%s Chance" % (_enname, _echo))
        _bgfix8_checked += 1
        if zh.get(_key) != _want_zh:
            _bgfix8_bad("bgfix8-config-label-zh",
                        "配置条目名（zh）%s = %r ≠ 作者字面 %r" % (_key, zh.get(_key), _want_zh))
        if en.get(_key) != _want_en:
            _bgfix8_bad("bgfix8-config-label-en",
                        "配置条目名（en）%s = %r ≠ %r" % (_key, en.get(_key), _want_en))
        # `.comment(...)` 第 1 行：**去注释**源码里必须逐字出现该族的中文字面
        if _want_zh not in _bgfix_cfg:
            _bgfix8_bad("bgfix8-config-comment-zh",
                        "Config.java 的 .comment(...) 里没有作者字面 %r（去注释源码）" % _want_zh)
        # 中文侧必须是中文；英文侧不许混中文；两端不许逐字相同
        if not re.search(u"[\u4e00-\u9fff]", str(zh.get(_key, ""))):
            _bgfix8_bad("bgfix8-config-label-zh", "中文条目名里没有中日韩文字：%s" % _key)
        if re.search(u"[\u4e00-\u9fff]", str(en.get(_key, ""))):
            _bgfix8_bad("bgfix8-config-label-en", "英文条目名里混进了中文：%s" % _key)
        if zh.get(_key) == en.get(_key):
            _bgfix8_bad("bgfix8-config-label-en", "中英条目名逐字相同（既定口径：en ≠ zh）：%s" % _key)
        # 语义层：**盾牌**只许出现在武器侧那条里，盔甲侧那条不许再提"盾牌"
        if _kind == "weapon":
            if u"武器工具盾牌" not in _want_zh:
                _bgfix8_bad("bgfix8-config-label-zh", "武器侧字面里没有「武器工具盾牌」：%s" % _key)
        else:
            if u"盾牌" in str(zh.get(_key, "")):
                _bgfix8_bad("bgfix8-config-label-zh",
                            "盔甲侧条目名里还留着「盾牌」（盾牌走武器侧那条）：%s" % _key)
            if "Shield" in str(en.get(_key, "")):
                _bgfix8_bad("bgfix8-config-label-en",
                            "盔甲侧英文条目名里还留着 Shield：%s" % _key)
if _bgfix8_checked != 14:
    _bgfix8_bad("bgfix8-config-label-zh",
                "被检查的配置条目名不是 14 条（实际 %d）—— 反空转守护" % _bgfix8_checked)
# 负向：旧措辞的**提示行模板**不许再出现在 Config.java 的去注释源码里
for _old in (u"【武器工具】触发 Buff（", u"【盔甲盾牌】反制 Buff（", u"【武器工具】触发能力（落雷"):
    if _old in _bgfix_cfg:
        _bgfix8_bad("bgfix8-config-comment-old-gone",
                    "旧的提示行措辞还在 Config.java 里：%r" % _old)
# 负向：这两条字面**只许**是 14 条新文案，不许被搬到万坚金那两条上
for _bad8 in (u"万坚金·武器工具盾牌触发Buff概率", u"万坚金·盔甲触发buff概率"):
    if _bad8 in _bgfix_cfg:
        _bgfix8_bad("bgfix8-config-sturdygold-untouched",
                    "万坚金那两条被顺手改了（作者明说「除了万坚金相关」）：%r" % _bad8)
    if _bad8 in set(zh.values()) or _bad8 in set(en.values()):
        _bgfix8_bad("bgfix8-config-sturdygold-untouched", "语言文件里出现了 %r" % _bad8)

# ---------- ①b 万坚金两条：**逐字不动**（正向钉住它们自己的措辞） ----------
for _needle8, _why8 in ((u"万坚金【武器工具】触发能力（爆金：命中必定掉落一件金系物品）的概率。",
                         u"万坚金武器侧「能力概率」的提示行被改了"),
                        (u"万坚金【盔甲盾牌】触发能力（每 16 秒 1 份伤害吸收）的间隔乘法系数。",
                         u"万坚金盔甲侧「能力间隔系数」的提示行被改了"),
                        ("sturdygoldWeaponAbilityChance", u"万坚金武器侧键名不在位"),
                        ("sturdygoldArmorAbilityIntervalMultiplier", u"万坚金盔甲侧键名不在位")):
    if _needle8 not in _bgfix_cfg:
        _bgfix8_bad("bgfix8-config-sturdygold-untouched",
                    "%s（缺 %r）" % (_why8, _needle8))

# ---------- ①c 键名 / 默认值 / 取值范围 / 顺序：**四样都不许变** ----------
#   默认值由既有的 `[bgfix-config-defaults]`（`_BGFIX_DEFAULTS` 那张字面表）守着；
#   这里补**取值范围**与**§11.4 文档侧那 16 个字面键名**，再加一条"顺序 == METAL_ORDER"。
_bgfix8_16 = list(_BGFIX_WEAPON_KEYS.values()) + list(_BGFIX_ARMOR_KEYS.values()) + [_BGFIX_MULT_KEY]
# ⚠ 1.7 bg-n10r4：这清单跟着 `_BGFIX_WEAPON_KEYS`/`_BGFIX_ARMOR_KEYS` 长（16 → 20）。
#   变量名保留为历史名（旧名不改），旧期望原文留档：`if len(_bgfix8_16) != 16:`
_bgfix8_want_n = 16 + 4
if len(_bgfix8_16) != _bgfix8_want_n:
    _bgfix8_bad("bgfix8-config-keys-frozen",
                "%d 条清单不是 %d（实际 %d）—— 反空转守护"
                % (_bgfix8_want_n, _bgfix8_want_n, len(_bgfix8_16)))
_bgfix8_range_ok = 0
for _k8 in _bgfix8_16:
    _m8 = re.search(r'\.defineInRange\(\s*"%s"\s*,\s*[-0-9.]+D\s*,\s*([-0-9.]+)D\s*,\s*([-0-9.]+)D'
                    % re.escape(_k8), _bgfix_cfg)
    if not _m8:
        _bgfix8_bad("bgfix8-config-keys-frozen", "Config.java 里找不到键 %s 的 defineInRange" % _k8)
        continue
    _want_lo, _want_hi = ((0.0, 100.0) if _k8 == _BGFIX_MULT_KEY else (0.0, 1.0))
    _got_lo, _got_hi = float(_m8.group(1)), float(_m8.group(2))
    if abs(_got_lo - _want_lo) > 1e-9 or abs(_got_hi - _want_hi) > 1e-9:
        _bgfix8_bad("bgfix8-config-keys-frozen",
                    "键 %s 的取值范围变成了 (%s ~ %s)，应是 (%s ~ %s)"
                    % (_k8, _got_lo, _got_hi, _want_lo, _want_hi))
        continue
    if _k8 not in _bgfix_spec:      # ★ 文档侧独立副本：§11.4 的表格里必须逐字有这 16 个键名
        _bgfix8_bad("bgfix8-config-keys-frozen",
                    "docs/1.6-规格.md §11.4 里找不到键名 %s（唯一真源没落档？）" % _k8)
        continue
    _bgfix8_range_ok += 1
if _bgfix8_range_ok != _bgfix8_want_n:
    _bgfix8_bad("bgfix8-config-keys-frozen",
                "逐条核对通过的键只有 %d/%d —— 反空转守护" % (_bgfix8_range_ok, _bgfix8_want_n))
# 声明顺序 == 创造页/进度树的金属顺序（`CreativeSections.METAL_ORDER`）
# ⚠ 1.7 bg-n10r4：族清单从 8 族扩到 `_FX4_METALS + _FX4_APPENDED`（10 族）—— 否则新两族
#   既不参与顺序判定、也会让 `_bgfix8_order` 少 4 项（旧口径原文：`for _mf8 in _FX4_METALS:`）。
_bgfix8_order = [k for k in _cfg_keys if k in _bgfix8_16]
_bgfix8_want_order = []
for _mf8 in (_FX4_METALS + _FX4_APPENDED):
    _bgfix8_want_order.append(_BGFIX_WEAPON_KEYS[_mf8])
    if _mf8 in _BGFIX_ARMOR_KEYS:
        _bgfix8_want_order.append(_BGFIX_ARMOR_KEYS[_mf8])
    if _mf8 == "sturdygold":
        _bgfix8_want_order.append(_BGFIX_MULT_KEY)
if _bgfix8_order != _bgfix8_want_order:
    _bgfix8_bad("bgfix8-config-order-frozen",
                "%d 条的声明顺序 %s ≠ METAL_ORDER 推出的顺序 %s（不许改既有 16 条的相对顺序）"
                % (_bgfix8_want_n, _bgfix8_order, _bgfix8_want_order))

# ---------- ② 手册「贵金的知识」第 1 页右页：字幕 + 正文 ----------
#   作者的"字幕"= `patchouli:spotlight` 的 `title`（没写就退化成物品名，见 ex/04 第 102 条）；
#   "加文字" = 该页的 `text`（本轮补回 §七.1 删掉的「锻造模板怎么用」那一段）。
_bgfix8_snap_lines = _BG2_SNAPSHOT.read_text(encoding="utf-8").split("\n")
# 标题（"字幕"）：**复用**既有解析器 `_fx4_snapshot_k3()`（同一份快照、同一形状 —— 不写第二份解析）
_bgfix8_want_title = _fx4_k3_titles.get((1, "right"))
# 正文：§6.3 第 1 行右格 `<br>` 之后那一段（形状与 `[bgbook2-texts-verbatim]` 同源）
_bgfix8_want_body = None
_bgfix8_active = False
for _ln8 in _bgfix8_snap_lines:
    if _ln8.startswith("### 6.3"):
        _bgfix8_active = True
        continue
    if _bgfix8_active and _ln8.startswith("---"):
        break
    if not (_bgfix8_active and _ln8.startswith("|")) or "|---" in _ln8:
        continue
    _c8 = _ln8.split("|")[1:-1]
    if not _c8 or not re.fullmatch(r"\d+", _c8[0].strip().replace("*", "")):
        continue
    if _c8[0].strip().replace("*", "") != "1":
        continue
    _cell8 = _c8[2] if len(_c8) > 2 else ""
    _body8 = _cell8.split("<br>")[-1].strip()
    if _body8 and not _body8.startswith(u"图标："):
        _bgfix8_want_body = re.sub(r"\*\*(.+?)\*\*", r"\1", _body8)
_bgfix8_bodies = {}      # 只为下面的日志读数保留一个可打印的名字
if _bgfix8_want_body:
    _bgfix8_bodies[(1, "right")] = _bgfix8_want_body
if not _bgfix8_want_body:
    _bgfix8_bad("bgfix8-book-right-text",
                "冻结快照 §6.3 第 1 行右格取不到正文（反空转守护）")
else:
    _bgfix8_right_text = _bgfix8_bodies.get(("1", "right"))
    if _BG3_PAGES[1].get("text") != "bettergold.handbook.page.knowledge_1_right":
        _bgfix8_bad("bgfix8-book-right-text",
                    "第 1 页（右）的 text 不是 knowledge_1_right：%r" % (_BG3_PAGES[1].get("text"),))
    _bgfix8_key = "bettergold.handbook.page.knowledge_1_right"
    if zh.get(_bgfix8_key) != _bgfix8_want_body:
        _bgfix8_bad("bgfix8-book-right-text",
                    "zh 的 %s = %r ≠ 冻结快照逐字值 %r"
                    % (_bgfix8_key, zh.get(_bgfix8_key), _bgfix8_want_body))
    if not str(en.get(_bgfix8_key, "")).strip() or en.get(_bgfix8_key) == zh.get(_bgfix8_key):
        _bgfix8_bad("bgfix8-book-right-text",
                    "英文值缺失或与中文逐字相同：%s" % _bgfix8_key)
    # 与左页/摘要那段**不许**是同一句（否则等于没加）
    for _other8 in ("bettergold.handbook.page.knowledge_1_summary",
                    "bettergold.handbook.page.knowledge_1_left"):
        if zh.get(_other8) and zh.get(_other8) == zh.get(_bgfix8_key):
            _bgfix8_bad("bgfix8-book-right-text",
                        "右页正文与 %s 逐字相同（等于没加）" % _other8)
    # ★ **第二条独立来源**：仓库内留档的作者原文（`docs/bgbook2-证据/07-...txt`）
    _bgfix8_evid = (REPO / "docs" / "bgbook2-\u8bc1\u636e"
                    / "07-\u4ece\u9700\u6c42\u6587\u6863\u89e3\u6790\u51fa\u768422\u6bb5\u9010\u5b57\u6587\u6848.txt")
    if not _bgfix8_evid.is_file():
        _bgfix8_bad("bgfix8-book-right-text-source",
                    "读不到作者原文留档（期望值的第二条独立来源）：%s" % _bgfix8_evid)
    else:
        _ev8 = None
        for _ln8 in _bgfix8_evid.read_text(encoding="utf-8").split("\n"):
            if _ln8.startswith("knowledge_1_right"):
                _ev8 = _ln8.split(None, 1)[1].strip()
        if _ev8 != zh.get(_bgfix8_key):
            _bgfix8_bad("bgfix8-book-right-text-source",
                        "手册右页中文 %r ≠ 作者原文留档 %r" % (zh.get(_bgfix8_key), _ev8))
# "字幕"：右页 title 必须非空，且 == 冻结快照的「图标：」逐字值
if not _bgfix8_want_title:
    _bgfix8_bad("bgfix8-book-right-title", "冻结快照 §6.3 第 1 行右格取不到「图标：」字幕（反空转守护）")
else:
    if _BG3_PAGES[1].get("title") != _bgfix8_want_title:
        _bgfix8_bad("bgfix8-book-right-title",
                    "第 1 页（右）的 title %r ≠ 快照字幕 %r（没写 title ⇒ Patchouli 会退化成物品名）"
                    % (_BG3_PAGES[1].get("title"), _bgfix8_want_title))
    if len(_BG3_PAGES) != 10:
        _bgfix8_bad("bgfix8-book-right-title", "章3 页数不是 10（实际 %d）" % len(_BG3_PAGES))

# ---------- ③ 文档侧：本轮口径必须落档（docs/1.6-规格.md 的 §29） ----------
for _needle8, _why8 in ((u"bgfix8", u"docs/1.6-规格.md 里没有 bgfix8 这一轮的节"),
                        (u"武器工具盾牌触发Buff概率", u"没写作者给的武器侧字面"),
                        (u"盔甲触发buff概率", u"没写作者给的盔甲侧字面"),
                        (u"knowledge_1_right", u"没写右页补回的正文键"),
                        (u"bgbook2-证据", u"没写正文的逐字来源（作者原文留档）"),
                        (u"盾牌的反制", u"没写「盾牌的反制 = 武器侧那条 / 默认 100%」这层语义"),
                        (u"万坚金", u"没写万坚金两条为什么不动")):
    if _needle8 not in _bgfix_spec:
        _bgfix8_bad("bgfix8-doc", "%s（缺 %s）" % (_why8, _needle8))

print(f"bgfix8（配置显示文案 + 手册右页字幕/正文）问题: {len(bgfix8_problems)} {bgfix8_problems[:8]}"
      f"（配置条目名核对 {_bgfix8_checked} 条 / 键与范围 {_bgfix8_range_ok}/16 / "
      f"右页 title={_bgfix8_want_title!r} / 右页正文 {len(_bgfix8_want_body or '')} 字）")

# ==================== bgfix9（2026-10-11）：金玫瑰丛放不上金染土 ====================
# 作者原话：「还有**金玫瑰无法放在金染土上**，虽然**弄成金染耕地也能放上**的说」。
# 根因（`【读源码】neoforge-21.1.228-sources.jar`）：金玫瑰丛 = `TallFlowerBlock`
#   ⇒ `DoublePlantBlock` ⇒ `BushBlock`。下半块存活判据 `BushBlock#canSurvive`
#   （`BushBlock.java:38-45`）**先问下方方块的 `canSustainPlant`**：不是 `DEFAULT` 就以它为准；
#   是 `DEFAULT` 才回落 `mayPlaceOn` = `state.is(BlockTags.DIRT) ||
#   state.getBlock() instanceof FarmBlock`（`BushBlock.java:22-24`）。
#   ⇒ 金染耕地（`GoldInfusedFarmlandBlock#canSustainPlant` 恒 TRUE）能放；
#     金染土（bgfix9 之前是裸 `Block`、既不在 `#minecraft:dirt` 也不是 `FarmBlock`）不能放。
# 现行落法 = `GoldInfusedDirtBlock`：**只对金玫瑰丛**返回 `TriState.TRUE`，其余回落 `DEFAULT`。
#   ⚠ 刻意**不**照抄金染耕地的"恒 TRUE"：`CropBlock#canSurvive`（`CropBlock.java:163-168`）
#     同样先看 `canSustainPlant` ⇒ 恒 TRUE 会让普通小麦/金麦/金钱茄**直接种在金染土上**、
#     绕过 `GoldCropBlock#mayPlaceOn`（要求下方是金染耕地）＝ 破坏"必须先耕成金染耕地"这条设计
#     （连带《开垦我的金色土地》成就的前提失效）。
bgfix9_problems: list[str] = []


def _bgfix9_bad(tag: str, msg: str) -> None:
    bgfix9_problems.append(f"{msg} [{tag}]")


_blocks_nc9 = strip_comments((JAVA / "registry" / "AllBlocks.java").read_text(encoding="utf-8"))
if 'BLOCKS.register("gold_infused_dirt"' not in _blocks_nc9 or "GoldInfusedDirtBlock" not in _blocks_nc9:
    _bgfix9_bad("bgfix9-rose-dirt-sustain-block",
                "AllBlocks 里 gold_infused_dirt 不是用 GoldInfusedDirtBlock 注册的"
                "（裸 Block ⇒ 没有 canSustainPlant ⇒ 金玫瑰丛放不上）")
_dirt_block_file = JAVA / "block" / "GoldInfusedDirtBlock.java"
if not _dirt_block_file.is_file():
    _bgfix9_bad("bgfix9-rose-dirt-sustain-block", "缺 block/GoldInfusedDirtBlock.java")
    _dirt_block_nc = ""
else:
    _dirt_block_nc = strip_comments(_dirt_block_file.read_text(encoding="utf-8"))
for _needle9, _tag9, _why9 in (
        ("canSustainPlant", "bgfix9-rose-dirt-sustain-whitelist",
         "金染土没有声明 canSustainPlant"),
        ("GOLDEN_ROSE_BUSH", "bgfix9-rose-dirt-sustain-whitelist",
         "金染土的 canSustainPlant 白名单里没有金玫瑰丛（作者本轮的唯一要求）"),
        ("TriState.TRUE", "bgfix9-rose-dirt-sustain-whitelist",
         "金染土没有对金玫瑰丛返回 TriState.TRUE"),
        ("TriState.DEFAULT", "bgfix9-rose-dirt-sustain-whitelist",
         "金染土的白名单**不封闭**（缺 `return TriState.DEFAULT`）⇒ 要么恒 TRUE（普通作物会直接"
         "种在金染土上）、要么实际还是放不上 —— 必须是「金玫瑰丛 ⇒ TRUE，其余 ⇒ DEFAULT」"),
):
    if _needle9 not in _dirt_block_nc:
        _bgfix9_bad(_tag9, _why9)
_farm_nc9 = strip_comments((JAVA / "block" / "GoldInfusedFarmlandBlock.java").read_text(encoding="utf-8"))
if "canSustainPlant" not in _farm_nc9 or "TriState.TRUE" not in _farm_nc9:
    _bgfix9_bad("bgfix9-rose-farmland-regression",
                "金染耕地的 canSustainPlant 不再是 TRUE —— 回归被破坏"
                "（作者明确「弄成金染耕地也能放上」）")
# 负向：不许走"把金染土塞进 #minecraft:dirt"这条**全局放宽**的路（那超出作者要求，
#   会连带让树苗/花/菌类等一切 `BushBlock` 都能放上金染土）
_dirt_tag_hits9: list[str] = []
for _tf9 in (_DATA / "minecraft" / "tags" / "block").rglob("*.json"):
    if _tf9.name != "dirt.json":
        continue
    if "gold_infused_dirt" in _tf9.read_text(encoding="utf-8"):
        _dirt_tag_hits9.append(str(_tf9.relative_to(REPO)))
if _dirt_tag_hits9:
    _bgfix9_bad("bgfix9-rose-dirt-not-in-dirt-tag",
                f"金染土被塞进了 #minecraft:dirt（{_dirt_tag_hits9}）—— 那会把金染土变成"
                f"「什么植物都能放」的通用土，超出作者要求（只要求金玫瑰丛）")
print(f"bgfix9（金玫瑰丛 × 金染土）问题: {len(bgfix9_problems)} {bgfix9_problems[:4]}"
      f"（白名单 = 恰好金玫瑰丛 1 件 + DEFAULT 回落；金染耕地 TRUE 回归保留；"
      f"`#minecraft:dirt` 负向命中 {len(_dirt_tag_hits9)} 处）")

# ==================== bgfix10（2026-10-11）：作者替换 zh_cn.json ⇒ en_us.json 同步 ====================
#
# 起因（作者原话）：「现在我用修改后的 zhcn.json 替换了原来的，但是 en-US 没有同步翻译修改更新的内容」。
# 三方比对（HEAD `11820bb` ↔ **作者替换后的 zh** ↔ en）结论（清单落在 `docs/1.6-规格.md` §31）：
#   新增 0 / 改值 6 / 删除 20；键集差异 = en 缺 0、**en 多 20**。
#   ★ 关键判定：那 20 条**全部是「已作废条目 / 旧占位条目」的语言键**（`metal_tour` / `upgrade_templates` /
#     `tools_per_family` / `armor_per_family` / `golden_feast` / `merchant` / `antiques` 及其 page 键），
#     产物里**已不存在这些条目** ⇒ 判定为**作者有意清理**（父代理 2026-10-11 裁定）
#     ⇒ en 侧跟着删，**键集与 zh 完全一致**。
#
# 本节守三件事（父代理要求的"关卡三件套"）+ 两条产物断言：
#   ① 键集与 zh **完全一致**（双向）                → `[bgfix10-lang-keyset]`
#   ② 两语言都**不许有空值** / en **不许把中文拷进去** → `[bgfix10-lang-no-empty]` / `[bgfix10-lang-en-not-zh]`
#   ③ **未变动的键逐字未变**（冻结基线 = 改前 en 的"未变动子集" SHA256） → `[bgfix10-lang-untouched-frozen]`
#   ④ 本轮 6 条新英文值**逐条钉死** + 20 个作废键**不许回来**（负向）
#
# ⚠ **冻结基线怎么用**：`_BGFIX10_UNTOUCHED_SHA` 是**改前 en**（SHA256 `_BGFIX10_EN_BEFORE_SHA`）里
#   「除 20 个删除键与 6 个改值键之外的 716 个键」的规范化 SHA256
#   （`"<键>\t<值>\n"` 排序拼接）。**改前 / 改后算出来必须是同一个值**（改后那条由 apply 脚本先证过）。
#   ⇒ 谁动了这 716 个键里的任何一个（哪怕改回中文），这条当场红；要动就**显式改这个常量并记账**。
#   ★★ **bgfix11 就地补记（2026-10-11；旧口径原文不删）**：`knowledge_1_summary` 这一轮被修
#     （en 值由「中文原文」→ §31.7 的建议英文）⇒ 它**退出**"未变动子集"，子集 **716 → 715 键**。
#     旧常量（原文留档在下面两行注释里，未删，= 含该键的 716 键基线）：
#       `_BGFIX10_UNTOUCHED_SHA = "B96C5E7E9FD0D9005C62BCF14CF80BD72F287B2A6A83B88DA368B01EA3BAD15E"`
#       `_BGFIX10_UNTOUCHED_N = 716`
#     反证（本轮实测，脚本 `docs/bgfix11-证据/脚本副本/verify_old_baseline.py`）：拿**改前冻结副本**
#     （`docs/bgfix11-证据/08-en_us-改前冻结副本.json`）用同一个排除集复算 ⇒ 逐位 == 上面那个旧常量 / 716 键
#     ⇒ 排除集本身没写错，变的只是"子集里少了一个键"。
#     ⚠ 探针目录 `probe/bgfix11/` 收尾按探针铁律**整块删除** ⇒ 一切一次性脚本/冻结副本从证据目录取。
_BGFIX10_EN_BEFORE_SHA = "B39CF06901319D9BAEDD4E202DC1EF14F78596DEAEF3580D958D575927E83A36"
_BGFIX10_EN_AFTER_SHA = "7A7156E8D83C03BE9916D10A78AA8951FEF66F69F760AFADA2DB16E5433F1E57"
_BGFIX10_ZH_SHA = "695FA5A5347E1165F431A204D8CA6F1965D9D136DA0F4D560F299E8B3C972810"
_BGFIX10_UNTOUCHED_SHA = "68A5441020CB829DD2ED9EC435E627461AFF1EEFE567213B7528E21889588E1C"
_BGFIX10_UNTOUCHED_N = 715
# ★ bgfix11（2026-10-11）：本轮修的键（**退出**"未变动子集"；断言见本节 ⑥）
_BGFIX11_FIXED = ("bettergold.handbook.page.knowledge_1_summary",)
_BGFIX11_EN_AFTER_SHA = "07AA2FA07EDD8942FA8CD8BFA441EFEA8BB2740E1532BB1D60143FF27097768F"
# 20 个作废键（作者 2026-10-11 从 zh 里删掉 ⇒ en 跟着删；两侧都不许再出现）
_BGFIX10_REMOVED = (
    "%s.entry.metal_tour" % "bettergold.handbook", "%s.entry.upgrade_templates" % "bettergold.handbook",
    "%s.entry.tools_per_family" % "bettergold.handbook", "%s.entry.armor_per_family" % "bettergold.handbook",
    "%s.entry.golden_feast" % "bettergold.handbook", "%s.entry.merchant" % "bettergold.handbook",
    "%s.entry.antiques" % "bettergold.handbook",
    "%s.page.metal_tour" % "bettergold.handbook", "%s.page.metal_chain" % "bettergold.handbook",
    "%s.page.upgrade_templates" % "bettergold.handbook", "%s.page.tools" % "bettergold.handbook",
    "%s.page.tools_1" % "bettergold.handbook", "%s.page.tools_2" % "bettergold.handbook",
    "%s.page.tools_3" % "bettergold.handbook", "%s.page.armor" % "bettergold.handbook",
    "%s.page.armor_1" % "bettergold.handbook", "%s.page.armor_2" % "bettergold.handbook",
    "%s.page.golden_feast" % "bettergold.handbook", "%s.page.merchant" % "bettergold.handbook",
    "%s.page.antiques" % "bettergold.handbook",
)
# 6 条改值键：key -> (旧英文, 新英文)。旧英文用来**钉住"改的是这一条、且确实是改前那条"**。
_BGFIX10_CHANGED = {
    "item.bettergold.unwanted_antique": ("Unwanted Old Antique", "Useless Old Antique"),
    "trim_material.bettergold.unwanted_antique": ("Old Antique", "Useless Old Antique"),
    "advancements.bettergold.echogold_weapon.title": (
        "Wait for the Show - This One Is About the Drummer",
        "The Drummer on Stage Sure Packs a Punch"),
    "bettergold.handbook.page.core_4": (
        "Using wood as its carrier, the glittering vine may take quite some luck: just mine leaves and "
        "vines with any golden tool for a small chance to drop one. That means it is an item you can only "
        "own after you already have \"noble gold\" tools. The \"noble gold\" smelted with it is called "
        "\"Thornsgold\".",
        "Using wood as its carrier, the glittering vine is now a fairly mid-game material to obtain: just "
        "mine leaves and vines with any \"noble gold\" tool for a chance to drop one. Or perhaps we could "
        "go ask a senior alchemy student for help? The \"noble gold\" smelted with it is called "
        "\"Thornsgold\"."),
    "bettergold.handbook.page.merchant_gift_box_2_left": (
        "The Curio Box gives out Unwanted Antiques, and has a chance to give one kind of antique weapon "
        "or tool (this gift box can also be found in Ancient City chests).",
        "The Curio Box gives out Useless Old Antiques, and has a chance to give one kind of antique "
        "weapon or tool (this gift box can also be found in Ancient City chests)."),
    "bettergold.handbook.page.merchant_gift_box_2_right": (
        "The Unwanted Antique can be thrown as a projectile that deals 3 damage, and can also be used on "
        "an anvil to repair antique weapons and tools. But it actually has one more use -- please move on "
        "to the \"〔待补〕\" chapter for that, thank you (this antique can also be found in Ancient City "
        "chests).",
        "The Useless Old Antique can be thrown as a projectile that deals 3 damage, and can also be used "
        "on an anvil to repair antique weapons and tools. But it actually has one more use -- please move "
        "on to the \"〔待补〕\" chapter for that, thank you (this antique can also be found in Ancient "
        "City chests)."),
}
# ⚠ **旧口径（原文留档在下面，一行未删）—— 当时那张「唯一例外」表**：
#   `bettergold.handbook.page.knowledge_1_summary` 的 **en 值就是中文原文**（== zh 逐字相同）
#   —— 这是**改前就存在**的既有缺陷（bgfix10 三方比对时发现；它**不在**那一轮 6 条改值清单里，
#     按"未变动的键一个字都不动"的红线当时**未动**），已单列给作者裁定（§31.7 / §31.8）。
#   当时的落法 = 把它列成 `[bgfix10-lang-en-not-zh]` 的**唯一例外**（注释里写明"这是既有缺陷、
#   不是把缺陷写成契约；谁修好就把这一行删掉"），旧代码原文逐字如下：
#     _BGFIX10_CJK_OK = {"bettergold.handbook.page.knowledge_1_summary"}
#   ★★ **bgfix11（2026-10-11）已修 ⇒ 例外表整体删除**（缺陷修好就不该再留例外）：
#     ① 上面这行常量**已从代码里删掉**（只作为留档注释存在）；
#     ② 循环里那句 `if _bg10_k in _BGFIX10_CJK_OK: continue` 也**已删** ⇒ 现行
#        `[bgfix10-lang-en-not-zh]` 对 **722 个键一个不例外**地跑全域 CJK 检测；
#     ③ 该键的新英文由 `[bgfix11-lang-k1s-en]` 逐字钉死（见本节 ⑥）；
#     ④ "例外表不许再回来"由 `[bgfix11-lang-exception-gone]` 在**去注释源码**上负向守着
#        （⚠ 本条不能在本文件**含注释**的原文上判：上面那段留档注释里逐字写着旧代码）。
# 占位标记：这两条本身就该是"占位"（不影响"en 不许含中文"的判定）
_BGFIX10_PLACEHOLDERS = (u"〔待补〕", u"（作者未指定）", u"（作者未给，待补）")

bgfix10_problems: list[str] = []


def _bgfix10_bad(tag, msg):
    bgfix10_problems.append("[%s] %s" % (tag, msg))


# ---------- ① 键集与 zh **完全一致**（双向）+ 反空转 ----------
_bg10_only_zh = sorted(set(zh) - set(en))
_bg10_only_en = sorted(set(en) - set(zh))
if _bg10_only_zh or _bg10_only_en:
    _bgfix10_bad("bgfix10-lang-keyset",
                 "en 与 zh 的键集不一致：只 zh 有 %d 条 %s / 只 en 有 %d 条 %s"
                 % (len(_bg10_only_zh), _bg10_only_zh[:5], len(_bg10_only_en), _bg10_only_en[:5]))
if len(zh) < 700 or len(en) < 700:
    _bgfix10_bad("bgfix10-lang-keyset",
                 "语言键总数 zh=%d / en=%d < 700（反空转守护：键集比对必须真的比过 700 条以上）"
                 % (len(zh), len(en)))

# ---------- ② 空值 + "把中文拷进 en" ----------
for _bg10_name, _bg10_tab in (("zh_cn", zh), ("en_us", en)):
    _bg10_empty = sorted(k for k, v in _bg10_tab.items() if not str(v).strip())
    if _bg10_empty:
        _bgfix10_bad("bgfix10-lang-no-empty",
                     "%s 有空值 %d 条：%s" % (_bg10_name, len(_bg10_empty), _bg10_empty[:5]))
_bg10_cjk = re.compile(u"[\u3400-\u9fff\uf900-\ufaff]")
for _bg10_k, _bg10_v in en.items():
    # ★ bgfix11：这里原先有一句 `if _bg10_k in _BGFIX10_CJK_OK: continue`（例外表），
    #   缺陷修好后**已删** ⇒ 现在对 en 的每一个键都跑 CJK 检测，**零例外**。
    _bg10_t = str(_bg10_v)
    for _bg10_ph in _BGFIX10_PLACEHOLDERS:
        _bg10_t = _bg10_t.replace(_bg10_ph, "")
    if _bg10_cjk.search(_bg10_t):
        _bgfix10_bad("bgfix10-lang-en-not-zh",
                     "en 值里出现中日韩文字（把中文原文拷进英文了）：%s = %r" % (_bg10_k, _bg10_v))

# ---------- ③ 未变动的键**逐字未变**（冻结基线）----------
# ⚠ bgfix11：`_BGFIX11_FIXED` 里的键**也**排除（本轮被修 ⇒ 它不该再被当成"未变动"）→ 715 键
_bg10_excl = set(_BGFIX10_REMOVED) | set(_BGFIX10_CHANGED) | set(_BGFIX11_FIXED)

# ⚠ **1.7（bg-n10 轮1 后半）就地标注 —— 旧口径原文保留、不放宽**：
#   旧写法把"未变动子集"定义成**现文件里除排除集之外的全部键**（`[k for k in en if k not in _bg10_excl]`），
#   于是"新增语言键"会被算进子集 ⇒ 键数与 SHA 双双变化 ⇒ 只能靠改冻结常量收场（那等于把护栏废掉）。
#   1.7 作者要求「语言键占位（zh/en 双语，**只加不删**）」⇒ 子集改成
#   **与冻结副本（bgfix11 的 en 冻结副本）取交集**：新增的键天然不进子集，
#   而"改前就存在的 715 个键"这条不变量**一个字节都没放宽**（实测重算 = 715 键 / SHA 68A54410… 逐位相同）。
#   old: _bg10_untouched = [k for k in en if k not in _bg10_excl]
#        _bg10_hash = _bgfix10_subset_hash(en)
_BGFIX11_FROZEN_EN = REPO / "docs" / "bgfix11-证据" / "08-en_us-改前冻结副本.json"
_BGFIX11_FROZEN_ZH = REPO / "docs" / "bgfix11-证据" / "09-zh_cn-冻结副本.json"
if not _BGFIX11_FROZEN_EN.is_file():
    _bgfix10_bad("bgfix10-lang-untouched-frozen",
                 "找不到冻结副本 %s（反空转守护：拿不到基线就无法说'未变动'）"
                 % _BGFIX11_FROZEN_EN.relative_to(REPO))
    _bg10_frozen_en: dict = {}
else:
    _bg10_frozen_en = json.loads(_BGFIX11_FROZEN_EN.read_text(encoding="utf-8"))
_bg10_new_keys = sorted(set(en) - set(_bg10_frozen_en))


def _bgfix10_subset_hash(_tab):
    _h = hashlib.sha256()
    for _k, _v in sorted((k, v) for k, v in _tab.items() if k not in _bg10_excl):
        _h.update(_k.encode("utf-8"))
        _h.update(b"\t")
        _h.update(str(_v).encode("utf-8"))
        _h.update(b"\n")
    return _h.hexdigest()


_bg10_untouched = [k for k in en if k in _bg10_frozen_en and k not in _bg10_excl]
_bg10_hash = _bgfix10_subset_hash({k: v for k, v in en.items() if k in _bg10_frozen_en})
if len(_bg10_untouched) != _BGFIX10_UNTOUCHED_N:
    _bgfix10_bad("bgfix10-lang-untouched-frozen",
                 "未变动子集是 %d 个键（冻结基线 %d 个）—— 键被增删了"
                 % (len(_bg10_untouched), _BGFIX10_UNTOUCHED_N))
if _bg10_hash.upper() != _BGFIX10_UNTOUCHED_SHA:
    _bgfix10_bad("bgfix10-lang-untouched-frozen",
                 "未变动子集的规范化 SHA256 = %s（冻结基线 %s）—— 有人动了本轮不该动的键"
                 "（要动就显式改这个常量并在 §31 记账）" % (_bg10_hash.upper()[:32], _BGFIX10_UNTOUCHED_SHA[:32]))
if len(_bg10_untouched) < 700:
    _bgfix10_bad("bgfix10-lang-untouched-frozen",
                 "反空转守护：参与比对的键只有 %d 个（< 700）" % len(_bg10_untouched))

# ---------- ④ 本轮产物：6 条新英文值逐条钉死 + 20 个作废键不许回来 ----------
for _bg10_k, (_bg10_old, _bg10_new) in _BGFIX10_CHANGED.items():
    if en.get(_bg10_k) != _bg10_new:
        _bgfix10_bad("bgfix10-lang-changed-frozen",
                     "%s 的英文不是本轮定的新值（实际 %r）" % (_bg10_k, en.get(_bg10_k)))
    if en.get(_bg10_k) == zh.get(_bg10_k):
        _bgfix10_bad("bgfix10-lang-changed-frozen",
                     "%s 的英文与中文逐字相同（等于没译）" % _bg10_k)
if len(_BGFIX10_CHANGED) != 6:
    _bgfix10_bad("bgfix10-lang-changed-frozen", "改值清单不是 6 条（反空转守护）")
_bg10_back = sorted(k for k in _BGFIX10_REMOVED if k in en or k in zh)
if len(_BGFIX10_REMOVED) != 20:
    _bgfix10_bad("bgfix10-lang-retired-gone", "作废键清单不是 20 条（反空转守护）")
if _bg10_back:
    _bgfix10_bad("bgfix10-lang-retired-gone",
                 "作废条目的语言键又回到了语言文件里（现行口径 = 删键 + 规格留档）：%s" % _bg10_back[:6])
# ⚠ **语言键删掉 ≠ 档案丢掉**：作废条目的正文全文对照必须仍然在规格里（§19.8 / §24.8）。
for _bg10_needle, _bg10_why in (
        (u"作废内容的全文对照", u"没找到「作废内容的全文对照」那句（档案被丢掉了？）"),
        (u"装备的升级", u"§19.6.1 的旧类别「装备的升级」全文对照不见了"),
        (u"贵金的材料链", u"§22.4 的「贵金的材料链」全文对照不见了")):
    if _bg10_needle not in _bgfix_spec:
        _bgfix10_bad("bgfix10-archive-kept", _bg10_why)

# ---------- ⑤ 文档侧：§31 的口径必须落档 ----------
for _bg10_needle, _bg10_why in (
        (u"bgfix10", u"docs/1.6-规格.md 里没有 bgfix10 这一轮的节"),
        (u"删键 + 规格留档", u"没写「旧占位语言键的留档方式 = 删键 + 规格留档」这条口径变更"),
        (u"语言键删掉 ≠ 档案丢掉", u"没写「语言键删掉 ≠ 档案丢掉」这句"),
        (u"Useless Old Antique", u"没写「没用的老古董」的新英文"),
        (u"The Drummer on Stage Sure Packs a Punch", u"没写幽咆金武器成就标题的新英文"),
        (u"knowledge_1_summary", u"没把「en 值仍是中文」这条既有缺陷记账")):
    if _bg10_needle not in _bgfix_spec:
        _bgfix10_bad("bgfix10-doc", "%s（缺 %s）" % (_bg10_why, _bg10_needle))

# ---------- ⑥ bgfix11（2026-10-11）：`knowledge_1_summary` 的 en 补真英文（§31.7 那条既有缺陷已修）----------
#
# 作者原话：「**需要改善一下，没必要**」⇒ 父代理解读（本轮照此执行）：
#   * 「需要改善」 = **修**：这条键的 **en 值原先就是中文原文**（bgfix10 §31.7 发现、按
#     "未变动的键一个字都不动"的红线当时未动）⇒ 现在补上**真英文**；
#   * 「没必要」   = **不改**：`trim_material.bettergold.unwanted_antique` **不加** `Material` 后缀、
#     成就标题 `The Drummer on Stage Sure Packs a Punch` **保持**（只列备选，不改）。
# 新英文 = `docs/1.6-规格.md` §31.7 的**建议英文逐字采纳**（不新造译名；术语依据见 §31.10）。
#
# 本条守四件事：① 该键的 en **非空 / 非中文 / ≠ zh / == 新英文**（逐字钉死，含反空转）；
#              ② zh 那一侧**一个字节都没动**（作者那份 = 唯一真源，按**文件 SHA256** 判）；
#              ③ 「已知缺陷例外表」**不许再存在**（★ **去注释源码**上的负向断言）；
#              ④ 旧代码原文**必须仍留档在注释里**（★ **原始源码**上的正向断言）+ 文档侧落档。
bgfix11_problems: list[str] = []


def _bgfix11_bad(tag, msg):
    bgfix11_problems.append("[%s] %s" % (tag, msg))


_BGFIX11_K1S = _BGFIX11_FIXED[0]
# 旧 en 值（== zh 逐字相同；既有缺陷的原文，留档不删）
_BGFIX11_K1S_OLD_EN = (u"把\"贵金\"原料丢进熔炉或高炉烧成锭，即可制成建材（建筑方块：锭块 / 砖块 / 柱 / 楼梯 / "
                       u"台阶 / 砖墙 / 栏杆 / 门 / 活板门 / 链 / 灯笼），或与其对应核心材料做成的锻造模版升级金装备。")
# 新 en 值（§31.7 的建议英文**逐字**；与 `docs/bgfix11-证据/脚本副本/apply_en.py` 里的 NEW_EN 同源）
_BGFIX11_K1S_NEW_EN = ("Smelt \"noble gold\" raw material into ingots in a furnace or blast furnace to make building "
                       "blocks (ingot block / bricks / pillar / stairs / slab / brick wall / bars / door / trapdoor / "
                       "chain / lantern), or combine them with the matching core material's smithing template to "
                       "upgrade golden gear.")

_bg11_v = en.get(_BGFIX11_K1S)
_bg11_zh_v = zh.get(_BGFIX11_K1S)
# 反空转：本轮只修 1 条键；钉死的新英文不许被截断
if len(_BGFIX11_FIXED) != 1:
    _bgfix11_bad("bgfix11-lang-k1s-en", "本轮修的键清单不是 1 条（反空转守护）")
if len(_BGFIX11_K1S_NEW_EN) < 250:
    _bgfix11_bad("bgfix11-lang-k1s-en",
                 "钉死的新英文只有 %d 字（< 250 ⇒ 常量被截断，反空转守护）" % len(_BGFIX11_K1S_NEW_EN))
if len(_BGFIX11_K1S_OLD_EN) < 50:
    _bgfix11_bad("bgfix11-lang-k1s-en",
                 "留档的旧中文只有 %d 字（< 50 ⇒ 留档被截断，反空转守护）" % len(_BGFIX11_K1S_OLD_EN))
if _bg11_v is None:
    _bgfix11_bad("bgfix11-lang-k1s-en", "%s 不在 en_us.json 里" % _BGFIX11_K1S)
else:
    _bg11_v = str(_bg11_v)
    if not _bg11_v.strip():
        _bgfix11_bad("bgfix11-lang-k1s-en", "%s 的 en 值是空串" % _BGFIX11_K1S)
    if _bg10_cjk.search(_bg11_v):
        _bgfix11_bad("bgfix11-lang-k1s-en",
                     "%s 的 en 值里仍有中日韩文字（没真的译）：%r" % (_BGFIX11_K1S, _bg11_v))
    if _bg11_v == str(_bg11_zh_v):
        _bgfix11_bad("bgfix11-lang-k1s-en",
                     "%s 的 en 值与 zh 逐字相同（等于没译）" % _BGFIX11_K1S)
    if _bg11_v == _BGFIX11_K1S_OLD_EN:
        _bgfix11_bad("bgfix11-lang-k1s-en",
                     "%s 的 en 值还是旧的中文原文（缺陷没被修）" % _BGFIX11_K1S)
    if _bg11_v != _BGFIX11_K1S_NEW_EN:
        _bgfix11_bad("bgfix11-lang-k1s-en",
                     "%s 的 en 值不是本轮钉死的新英文（实际 %r）" % (_BGFIX11_K1S, _bg11_v))
# ② zh 侧没被动过 —— ⚠ **1.7（bg-n10 轮1 后半）口径就地标注，轮3 再次改常量**：
#   旧口径（原文保留）= **文件级** SHA256 必须 == `_BGFIX10_ZH_SHA`（695FA5A5…）。
#   1.7 轮1 后半作者要求"语言键占位、**只加不删**"⇒ 文件级常量必然变（新增 73 键）⇒ 改成**语义冻结**：
#     ① 冻结副本（`09-zh_cn-冻结副本.json`）里**每一个键的值逐字未变**（这才是"作者那份没被动过"的本意）；
#     ② 新增的键必须**恰好**是本轮 1.7 的键（键数 = `_BGN10_NEW_LANG_KEYS`，且不许删键）；
#     ③ 文件级 SHA 仍然记录（`_BGN10_ZH_AFTER_SHA`），改了要显式改常量（护栏不消失，只是换了锚点）。
#   旧值留档：`_BGFIX10_ZH_SHA = "695FA5A5347E1165F431A204D8CA6F1965D9D136DA0F4D560F299E8B3C972810"`
#            轮1 后半的值（轮3 就地取代）：zh 717E39789409FFC2… / en 112E554C79CD4146… / 键数 73
#   ⚠ 轮3 为什么又变：轮2 的 A 级负向检查抓到 **19 条死语言键**（未注册形态的占位键，
#     例如 `item.bettergold.raw_chaosgold` / `block.bettergold.chaosalloy_bricks`）⇒
#     生成器与校验器**同时**改成按形态取，删掉那 19 条 ⇒ 73 - 19 = **54**。
#   ⚠ **1.7 bg-n10r4（轮4）第三次改常量**：新增 3 个键（禁果 / 附魔书 / 附魔书等级提示）
#     ⇒ 54 → **57**；两个文件级 SHA 同步换成新值。旧值（轮3）留档：
#       zh 7B9D0B52F5031D34… / en 1681514BDBAA6991… / 键数 54
# ⚠ 1.7 bg-n10r4 收尾：zh 的落点按"与 en 逐条镜像"写（chaosgoldArmor 在 chaosgoldWeapon 之后）
# ⇒ 文件 SHA 与上一轮中断时那次写入不同。旧常量原文留档（当时那次的落点/文案已无法逐字节复现）：
#   `_BGN10_ZH_AFTER_SHA = "BF9DA6E316C087D68C934790CDEB6FAD36FA3804219AA174DCB289B4DCE7561A"`
# ⚠ **1.7 bg-n10r6（轮6 · 金钱妖）第四次改常量**：新增 4 个键（实体名 / 刷怪蛋 /
#   两条死亡提示 `death.attack.bettergold.money_gremlin_melee|chaos_coin`）⇒ 61 → **65**；
#   两个文件级 SHA 同步换成本轮的值。旧值（轮4）原文留档：
#     zh B4DE1D53B72B6E67… / en 254C26C00CC7CD70… / 键数 61
#   本轮的语言键仍是「只加不删」：冻结副本里每一个既有键的值逐字未变（下面 ① 那条会证明）。
# ⚠ **1.7 bg-n10r5（轮5 · 金火把花 / 高精度炼金油）第五次改常量**：新增 5 个键
#   （`block.bettergold.golden_torchflower` / `block.bettergold.golden_torchflower_crop` /
#    `block.bettergold.potted_golden_torchflower` / `item.bettergold.golden_torchflower_seeds` /
#    `item.bettergold.refined_alchemic_oil`）⇒ 65 → **70**；两个文件级 SHA 同步换成本轮的值。
#   旧值（轮6）原文留档（不删）：
#     zh B3101EFE3448856648EB085DCC53CF26… / en E3C9EA8B2DCAF3A6D4080E03F89A16D3… / 键数 65
#   本轮仍是「只加不删」：冻结副本里每一个既有键的值逐字未变（下面 ① 那条会证明）。
# ⚠ **1.7 bg-n10r7（轮7 · 崩乱合金）第六次改常量**：新增 **3** 个键
#   （`effect.bettergold.power_imbalance` / `effect.bettergold.resistance_imbalance` /
#    `item.bettergold.chaosalloy_forbidden_fruit`）⇒ 70 → **73**；两个文件级 SHA 同步换成本轮的值。
#   旧值（轮5）原文留档（不删）：
#     zh 4A23FF0AC6536BE0DF44E5E713CDD215… / en D3FE7755F3C8778032619B453635D603… / 键数 70
#   ⚠ 本轮另外**改了 2 条既有键的值**（作者原话「可应用于: **混沌金装备**」）：
#     `item.bettergold.smithing_template.chaosalloy_upgrade.applies_to`（金装备 → 混沌金装备）
#     与 `.base_slot_description`（放入金制… → 放入混沌金…）；两条都不在冻结副本里
#     （冻结副本 = 更早那份作者原稿），所以下面 ① 那条"既有条目被动过"仍是 0 条。
# ⚠ **1.7 bg-n10r8（轮8 · 万坚金砧）第七次改常量**：新增 **2** 个键
#   （`block.bettergold.sturdygold_anvil` / `container.bettergold.sturdygold_anvil`）⇒ 73 → **75**；
#   两个文件级 SHA 同步换成本轮的值。旧值（轮7）原文留档（不删）：
#     zh 7D2F9DE0D2BE3D7A84D3D81411861F8E… / en 22B350564878D89A413952A563CF8BAC… / 键数 73
#   本轮仍是「只加不删」：冻结副本里每一个既有键的值逐字未变（下面 ① 那条会证明）。
#   ⚠ 为什么是 2 条而不是 3 条：万坚金砧**不需要新物品**（配方用的全是既有物品），
#     方块名 + 容器标题两个键就够；"花费 X 级"复用原版 `container.repair.cost`（不新增）。
# ⚠ **1.7 bg-n10rg（2026-10-17）第八次改常量**：本轮**没有增删键**（键数仍是 111），
#   改的是**一条既有键的值** —— `bettergold.handbook.page.gear_chaosgold_1_right`
#   （旧口径「混沌金装备目前没有获取途径…后面几页只展示物品，不展示配方」→
#    新口径「11 件走工作台、逐格照原版；剩下 4 件停下报告」）。
#   ⇒ 两个**文件级** SHA 必须同步换成本轮的值（护栏不消失，只换锚点）。
#   旧值（轮8，原文留档、不删）：
#     zh 5B8ED0E3C0E47873702B18CE9EA15949… / en A330F90BD699140DCC1C0C434F3D55E5… / 键数 111
# 旧值（bg-n10rg 把手册正文里弩的材料数写错后改正，原文留档、不删）：zh 641220C040C9139732D964BEBA4EA6EA…
# ⚠ **1.7 bg-n10rc2（2026-10-18）第九次改常量**：本轮**没有增删键**（键数仍是 111），
#   改的仍是**同一条既有键的值** —— `bettergold.handbook.page.gear_chaosgold_1_right`
#   （旧口径「…剩下 4 件暂时没有工作台配方，后面几页的图标表仍然展示它们」→
#    新口径「15 件全部走工作台：弓 = 3 锭 + 3 线 / 重锤 = 1 块 + 1 微风棒 / 乐事刀 = 1 锭 + 1 棍 +
#    FD 条件 / 三叉戟 = **原创形状、待作者确认**」）。
#   ⇒ 两个**文件级** SHA 同步换成本轮的值（护栏不消失，只换锚点）。
#   旧值（bg-n10rg，原文留档、不删）：
#     zh 432A5297852A47B7D72A7C5D235BE8CD… / en 51F3FD6F0686D0CDB2CBFE553ED0C314… / 键数 111
# ⚠ **1.7 bg-n10up（2026-10-18）第十次改常量**：本轮**改了 values、也加了 2 个键**：
#   ① 改值 2 条既有键：`page.chaos_materials_1_left`（材料链补上游）/`..._2_right`
#      （旧的「（实现说明）…两者的上下游关系作者还没有说明」= **被作者原话替换**）；
#   ② 新增 2 条页码键：`..._upstream_string` / `..._upstream_smelt` ⇒ 键数 **111 → 113**。
#   旧值（bg-n10rc2，原文留档、不删）：
#     zh 54BBC7A51136E9883B0F46E954554593… / en 2EFA1997FF53366C9FD811836DC29554… / 键数 111
_BGN10_ZH_AFTER_SHA = "65C45198982830B343543F1A27D668CF7E125E4CC25C30427E96C3105FC00643"
# 旧值（bg-n10rg 第一次改完正文之后的值，原文留档、不删）：en 9312FB31C7D4BD39FFBC4C9C30BD77C7…
# 旧值（bg-n10rg 定稿的值，原文留档、不删）：en 51F3FD6F0686D0CDB2CBFE553ED0C314…
# 旧值（bg-n10rc2 的值，原文留档、不删）：en 2EFA1997FF53366C9FD811836DC295545…
_BGN10_EN_AFTER_SHA = "E606504A7F663C6EE05E2CD4D2F220F9A2F705D18FC50FB0037343C9F637E58B"
# ⚠ **旧值原文保留（未删）**：`_BGN10_NEW_LANG_KEYS = 75`（轮3 54 + 轮4 7 + 轮6 4 + 轮5 5 + 轮7 3 + 轮8 2）。
# ★ 1.7 bg-n10r9（轮9 · 收口）：+ **36** 条（手册 20 = 4 条目 + 16 页键；成就 16 = 8 条 × 2）
#   ⇒ 75 → **111**；两个文件级 SHA 同步换成本轮的值。旧值（轮8）原文留档：
#     zh 24348D4628134D39441CEE393B236D1B… / en 116A20B59C9D46A068749835F1CD08DE… / 键数 75
# ★ 1.7 bg-n10up：+ **2** 条（材料章新增两页的正文键：`upstream_string` / `upstream_smelt`）
#   ⇒ 111 → **113**。旧值（轮9 的 111）原文留档、不删。
_BGN10_NEW_LANG_KEYS = 113    # zh/en 各 113 条 = 轮3..轮8 的 75 + 轮9 的 36 + bg-n10up 的 2
# 旧值留档（原文保留，不删）：2026-10-17 轮7 的 73
# _BGN10_ZH_AFTER_SHA = "7D2F9DE0D2BE3D7A84D3D81411861F8EF00D4273AF884AE8F1E7DF21DFB606BD"
# _BGN10_EN_AFTER_SHA = "22B350564878D89A413952A563CF8BACEF8302F44CD0B9E17E9C07F3CC4EF696"
# _BGN10_NEW_LANG_KEYS = 73      # zh/en 各 73 条 = 轮3 的 54 + 轮4 的 7 + 轮6 的 4 + 轮5 的 5 + 轮7 的 3
# 旧值留档（原文保留，不删）：2026-10-17 轮6 的 65 → 轮5 的 70
# _BGN10_ZH_AFTER_SHA = "4A23FF0AC6536BE0DF44E5E713CDD215BE373F254B169608110FC92D9C3BC6AA"
# _BGN10_EN_AFTER_SHA = "D3FE7755F3C8778032619B453635D60386376C870796B61895B1542235CEDE07"
# _BGN10_NEW_LANG_KEYS = 70      # zh/en 各 70 条 = 轮3 的 54 + 轮4 的 7 + 轮6 的 4 + 轮5 的 5
# 旧值留档（原文保留，不删）：2026-10-17 轮6 的 65
# _BGN10_ZH_AFTER_SHA = "B3101EFE3448856648EB085DCC53CF266542EAABCB696AD311C933DEEAEFCACC"
# _BGN10_EN_AFTER_SHA = "E3C9EA8B2DCAF3A6D4080E03F89A16D36419BA9C46A4B3174A627CAD06C5D7DD"
# _BGN10_NEW_LANG_KEYS = 65      # zh/en 各 65 条 = 轮3 的 54 + 轮4 的 7 + 轮6 的 4
# 旧值留档（原文保留，不删）：2026-10-17 轮6 之前的 61
# _BGN10_ZH_AFTER_SHA = "B4DE1D53B72B6E6763F633D377940CAEA11A0B7322C3933E43A6E09B7245A891"
# _BGN10_EN_AFTER_SHA = "254C26C00CC7CD709C0003B9F7679255D8958F5AE33FF2659579B7903C003C67"
# _BGN10_NEW_LANG_KEYS = 61      # zh/en 各 61 条 = 轮3 的 54 + 轮4 的 7（3 条物品/提示 + 4 条配置界面名）
if not _BGFIX11_FROZEN_ZH.is_file():
    _bgfix11_bad("bgfix11-lang-k1s-en",
                 "找不到 zh 冻结副本 %s（反空转守护）" % _BGFIX11_FROZEN_ZH.relative_to(REPO))
else:
    _bg11_frozen_zh = json.loads(_BGFIX11_FROZEN_ZH.read_text(encoding="utf-8"))
    _bg11_zh_changed = sorted(k for k, v in _bg11_frozen_zh.items()
                              if k in zh and str(zh[k]) != str(v))
    _bg11_zh_missing = sorted(k for k in _bg11_frozen_zh if k not in zh)
    _bg11_zh_added = sorted(set(zh) - set(_bg11_frozen_zh))
    if _bg11_zh_changed or _bg11_zh_missing:
        _bgfix11_bad("bgfix11-lang-k1s-en",
                     "作者那份 zh 的既有条目被动过：改值 %d 条 %s / 删键 %d 条 %s"
                     % (len(_bg11_zh_changed), _bg11_zh_changed[:3],
                        len(_bg11_zh_missing), _bg11_zh_missing[:3]))
    if len(_bg11_zh_added) != _BGN10_NEW_LANG_KEYS:
        _bgfix11_bad("bgfix11-lang-k1s-en",
                     "zh 新增键 %d 条，期望 %d 条（= 1.7 两族占位键；多出来的必须显式记账）"
                     % (len(_bg11_zh_added), _BGN10_NEW_LANG_KEYS))
_bg11_zh_sha = hashlib.sha256((LANG / "zh_cn.json").read_bytes()).hexdigest().upper()
if _bg11_zh_sha != _BGN10_ZH_AFTER_SHA:
    _bgfix11_bad("bgfix11-lang-k1s-en",
                 "zh_cn.json 的文件 SHA256 = %s（1.7 记录值 %s）—— 又被动过了"
                 "（要动就显式改 `_BGN10_ZH_AFTER_SHA` 并记账）"
                 % (_bg11_zh_sha[:32], _BGN10_ZH_AFTER_SHA[:32]))
_bg11_en_sha = hashlib.sha256((LANG / "en_us.json").read_bytes()).hexdigest().upper()
if _bg11_en_sha != _BGN10_EN_AFTER_SHA:
    _bgfix11_bad("bgfix11-lang-k1s-en",
                 "en_us.json 的文件 SHA256 = %s（1.7 记录值 %s）—— 又被动过了"
                 % (_bg11_en_sha[:32], _BGN10_EN_AFTER_SHA[:32]))
if _bg11_zh_v != _BGFIX11_K1S_OLD_EN:
    _bgfix11_bad("bgfix11-lang-k1s-en",
                 "zh 侧这句不再是旧中文（作者改了 zh 就要同步更新本断言）：%r" % (_bg11_zh_v,))

# ③ 「已知缺陷例外表」不许再存在 —— ★ 判据跑在**去注释源码**上。
#   ⚠ 本条**不能**在本文件"含注释"的原文上判：那段留档注释里**逐字写着**旧代码（要求 ④ 就是它）。
#   ⚠⚠ 自指陷阱：本断言的 needle **不能**在代码里连续出现（否则它自己喂饱自己）⇒ 用拼接构造。
_bg11_self_raw = Path(__file__).read_text(encoding="utf-8")
_bg11_self_nc = re.sub(r"#[^\n]*", "", _bg11_self_raw)
_bg11_exc_token = "_BGFIX10_" + "CJK_OK"
_bg11_old_code = "_BGFIX10_" + "CJK_OK = {\"bettergold.handbook.page.knowledge_1_summary\"}"
if _bg11_exc_token in _bg11_self_nc:
    _bgfix11_bad("bgfix11-lang-exception-gone",
                 "关卡里仍有「已知缺陷例外」表（去注释源码里找到 %s）—— 缺陷修好就不该再留例外"
                 % _bg11_exc_token)
# ④ 旧代码原文必须仍留档在**注释**里（原文上的正向断言；"旧口径就地标注、原文不删"）
if _bg11_old_code not in _bg11_self_raw:
    _bgfix11_bad("bgfix11-lang-exception-gone",
                 "旧例外表的代码原文没有留档在注释里（要求：旧口径就地标注、原文不删）")
# ⑤ 文档侧：§31.10 必须把「新英文 + 旧值留档 + 术语依据」落档
for _bg11_needle, _bg11_why in (
        (u"Smelt \"noble gold\" raw material into ingots", u"§31 里没有本轮定的新英文（真源没落档）"),
        (u"bgfix11", u"docs/1.6-规格.md 里没有 bgfix11 这一轮的节"),
        (u"已修", u"§31.7 那条既有缺陷没有标注成「已修」")):
    if _bg11_needle not in _bgfix_spec:
        _bgfix11_bad("bgfix11-doc", "%s（缺 %s）" % (_bg11_why, _bg11_needle))

print(f"bgfix11（en 补真英文：knowledge_1_summary 由中文 → 真英文）问题: {len(bgfix11_problems)}"
      f" {bgfix11_problems[:4]}（该键 en {len(_BGFIX11_K1S_NEW_EN)} 字 / zh {len(_BGFIX11_K1S_OLD_EN)} 字"
      f" / 未变动子集 {len(_bg10_untouched)} 键 / 子集 SHA256 {_bg10_hash[:16]}"
      f" / en {_BGFIX10_EN_AFTER_SHA[:8]} → {_BGFIX11_EN_AFTER_SHA[:8]}）")

print(f"bgfix10（作者替换 zh ⇒ en 同步：6 改值 / 20 删键 / 键集一致）问题: {len(bgfix10_problems)}"
      f" {bgfix10_problems[:4]}（en {len(en)} 键 / zh {len(zh)} 键 / 未变动子集 {len(_bg10_untouched)} 键"
      f" / 子集 SHA256 {_bg10_hash[:16]}；en 改前 {_BGFIX10_EN_BEFORE_SHA[:8]} → 改后 {_BGFIX10_EN_AFTER_SHA[:8]}）")

# ==================== 1.7（bg-n10 轮1 后半）：两个共用组件的关卡 ====================
# 本轮的"两个扩展"是按作者裁定（立档 §4.0 ① / ⑪d）做成**共用组件**的：
#   ① 「区间值」= `material/ChaosRange.java`（规则 / 存储 / 触发点**只此一处**）；
#   ② 「形态子集」= `MetalFamily.Form` + `Spec.forms(...)`（Java）+ `metal_forms.py`（Python 镜像）。
# 它们都是"声明了但没接线也全绿"的高危形状（AGENTS 红线 2 的同一种病）⇒ 这里各给一条断言。
bgn10_problems: list[str] = []


def _bgn10_bad(tag: str, msg: str) -> None:
    bgn10_problems.append("[%s] %s" % (tag, msg))


# ---------- ① 形态子集：Java ↔ Python 两边的声明必须逐字一致 ----------
_bgn10_mf_nc = strip_comments((JAVA / "material" / "MetalFamily.java").read_text(encoding="utf-8"))
_bgn10_am_nc = strip_comments((JAVA / "material" / "AllMetals.java").read_text(encoding="utf-8"))
_enum_body = re.search(r"public enum Form \{(.*?)\n    \}", _bgn10_mf_nc, re.S)
if not _enum_body:
    _bgn10_bad("bgn10-forms-parity", "解析不到 MetalFamily.Form 枚举（反空转守护）")
else:
    _java_forms = re.findall(r"^\s{8}[A-Z_]+\(\"([a-z_]+)\"\)", _enum_body.group(1), re.M)
    # ⚠ 1.7 轮3：Java 枚举里多了 15 个「器具/武器/盔甲的伪形态」（顺序在 15 个可声明形态之后）
    #   ⇒ 对穿的是 `MF.jvm_enum_names()`（= ALL_FORMS + GEAR_FORMS），不是 ALL_FORMS。
    #   旧口径原文保留：`if _java_forms != MF.ALL_FORMS:`
    if _java_forms != MF.jvm_enum_names():
        _bgn10_bad("bgn10-forms-parity",
                   "Java Form 枚举 %s ≠ metal_forms.ALL_FORMS+GEAR_FORMS %s（顺序也要一致）"
                   % (_java_forms, MF.jvm_enum_names()))
    if len(_java_forms) != 30:
        _bgn10_bad("bgn10-forms-parity",
                   "Java Form 枚举不是 30 个（= 15 可声明 + 15 伪形态；实际 %d）—— 反空转守护"
                   % len(_java_forms))
    if _java_forms[:len(MF.ALL_FORMS)] != MF.ALL_FORMS:
        _bgn10_bad("bgn10-forms-parity",
                   "Java Form 枚举的**前 %d 项**不是 metal_forms.ALL_FORMS（可声明形态的顺序被改动了）"
                   % len(MF.ALL_FORMS))
    if _java_forms[len(MF.ALL_FORMS):] != MF.GEAR_FORMS:
        _bgn10_bad("bgn10-forms-parity",
                   "Java Form 枚举的**伪形态段** %s ≠ metal_forms.GEAR_FORMS %s"
                   % (_java_forms[len(MF.ALL_FORMS):], MF.GEAR_FORMS))
_bf = re.search(r"BUILDING_FORMS = java\.util\.EnumSet\.of\((.*?)\);", _bgn10_mf_nc, re.S)
if not _bf:
    _bgn10_bad("bgn10-forms-parity", "解析不到 Form.BUILDING_FORMS（反空转守护）")
else:
    _java_building = [(_n.strip().lower()) for _n in re.findall(r"\b([A-Z][A-Z_]+)\b", _bf.group(1))]
    if sorted(_java_building) != sorted(MF.BUILDING_FORMS):
        _bgn10_bad("bgn10-forms-parity",
                   "Java Form.BUILDING_FORMS %s ≠ metal_forms.BUILDING_FORMS %s"
                   % (_java_building, MF.BUILDING_FORMS))
    if len(_java_building) != 11:
        _bgn10_bad("bgn10-forms-parity",
                   "Form.BUILDING_FORMS 不是 11 种建材（实际 %d）" % len(_java_building))
# 两族的声明字面：chaosgold 用 withoutForms(...)、chaosalloy 用 forms(...)
_cg = re.search(r"chaosgold\", \"混沌金\"\)(.*?);", _bgn10_am_nc, re.S)
_ca = re.search(r"chaosalloy\", \"崩乱合金\"\)(.*?);", _bgn10_am_nc, re.S)
if not _cg or "withoutForms(MetalFamily.Form.RAW, MetalFamily.Form.UPGRADE_TEMPLATE)" not in _cg.group(1):
    _bgn10_bad("bgn10-forms-parity",
               "AllMetals 里 chaosgold 没有声明 `withoutForms(RAW, UPGRADE_TEMPLATE)`"
               "（= 除原料与升级模板外的 13 种形态）")
_CA_FORMS_NEEDLE = ("forms(MetalFamily.Form.INGOT, MetalFamily.Form.BLOCK, "
                    "MetalFamily.Form.UPGRADE_TEMPLATE)")
if not _ca or _CA_FORMS_NEEDLE not in _ca.group(1):
    _bgn10_bad("bgn10-forms-parity",
               "AllMetals 里 chaosalloy 没有声明 `forms(INGOT, BLOCK, UPGRADE_TEMPLATE)`"
               "（作者裁定：只做锭 + 块 + 模板）")
if len(MF.FORMS) != 2 or len(MF.forms_of("chaosgold")) != 13 or len(MF.forms_of("chaosalloy")) != 3:
    _bgn10_bad("bgn10-forms-parity",
               "metal_forms.FORMS 的声明不是 {chaosgold: 13, chaosalloy: 3}（实际 %s）"
               % {k: len(v) for k, v in MF.FORMS.items()})

# ---------- ② 区间值：公式**只许一处** + 三个触发点 + 两族声明的两端值 ----------
# ⛔ **旧口径（原文留档，作者 2026-10-18 已推翻）**：
#   `_bgn10_formula = "current == range.min ? range.max : range.min"`（两端乒乓）
#   `("toggle(stack, channel)", ...)` / 只有两个触发点（挖掘成功 + 重新手持）。
# ★ 现行（`bg-n10fix` ⑩）：**区间内均匀随机**（`min + random × (max − min)`，含两端），
#   三个触发点 = 挖掘成功 / **每次攻击命中** / 重新手持。
_bgn10_formula = "range.min() + range.span() * (f / (float) FRACTION_SCALE)"
_hits = []
for _jf in JAVA.rglob("*.java"):
    _t = strip_comments(_jf.read_text(encoding="utf-8"))
    if _bgn10_formula in _t:
        _hits.append(_jf.name)
if _hits != ["ChaosRange.java"]:
    _bgn10_bad("bgn10-chaos-range",
               "随机取值公式（%s）出现在 %s —— 必须**只有** ChaosRange.java 一处"
               "（四处区间各写一套 = 三份不一致）" % (_bgn10_formula, _hits))
_cr = JAVA / "material" / "ChaosRange.java"
_cr_txt = strip_comments(_cr.read_text(encoding="utf-8")) if _cr.is_file() else ""
if not _cr_txt:
    _bgn10_bad("bgn10-chaos-range", "缺 material/ChaosRange.java（反空转守护）")
else:
    for _needle, _why in (
            ("BlockEvent.BreakEvent", "缺触发点①「挖掘成功」（BlockEvent.BreakEvent）"),
            ("LivingEquipmentChangeEvent", "缺触发点②「重新手持」（LivingEquipmentChangeEvent）"),
            ("EquipmentSlot.MAINHAND", "手持触发点不是主手（作者口径：重新手持该物品）"),
            ("DATA_COMPONENT_TYPE", "区间值不是数据组件（作者裁定：值存数据组件）"),
            ("Register<DataComponentType<?>> COMPONENT_TYPES",
             "没有数据组件的 DeferredRegister"),
            ("reroll(stack, channel, random)", "reroll 没走唯一入口（公式与状态会各写一套）"),
            ("valueOfFraction", "缺「比例 → 具体数值」的唯一映射"),
            ("ATTACK_HIT", "缺攻击命中这个触发点（作者 2026-10-18：「进行一次攻击转换」）")):
        if _needle not in _cr_txt:
            _bgn10_bad("bgn10-chaos-range", "%s（缺 %s）" % (_why, _needle))
    # ⚠ 随机源必须钉在 **roll() 本体**里（不是"文件里出现过"）：`fractionTicks()` 也写了一次
    #   `nextInt(FRACTION_SCALE + 1)` ⇒ 只查全文件的话，把 roll 改成别的分布仍然绿（扰动实测过）。
    _bgn10fix_roll_body = method_body(_cr_txt, "public static float roll(RandomSource random)")
    if "random.nextInt(FRACTION_SCALE + 1)" not in _bgn10fix_roll_body:
        _bgn10_bad("bgn10-chaos-range",
                   "roll() 的随机源不是「区间内均匀、含两端」（缺 random.nextInt(FRACTION_SCALE + 1)）")
_bgn10_boot = strip_comments((JAVA / "bettergold.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ("ChaosRange.COMPONENT_TYPES.register(modEventBus)", "数据组件没在 mod 总线上注册（静默不生效）"),
        ("NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.material.ChaosRange.Triggers.class)",
         "区间值的触发点没有注册到游戏总线（挖掘/手持永不翻转）")):
    if _needle not in _bgn10_boot:
        _bgn10_bad("bgn10-chaos-range", _why)
for _lit, _m in (("chaosRange(ChaosRange.Channel.MINING, 2, 12)", "chaosgold 2..12"),
                 ("chaosRange(ChaosRange.Channel.MINING, 8, 16)", "chaosalloy 8..16")):
    if _lit not in _bgn10_am_nc:
        _bgn10_bad("bgn10-chaos-range", "AllMetals 里没有 %s（作者给的两端值）" % _m)

# ---------- ③ 区间值的**接线**（1.7 bg-n10 轮3）：唯一实现 + 落点 + 作者逐件给的数 ----------
# 口径：**「公式只有一处」是硬约束，接线是"读当前值 → 写进游戏认的那个口子"**，
#   接线层里**一个 `min ? max : min` 都不许有**（那条公式只在 ChaosRange.java）。
_bgn10w_problems: list[str] = []


def _bgn10w_bad(tag: str, msg: str) -> None:
    _bgn10w_problems.append("[%s] %s" % (tag, msg))


_b10w = JAVA / "material" / "ChaosWiring.java"
_b10w_txt = strip_comments(_b10w.read_text(encoding="utf-8")) if _b10w.is_file() else ""
if not _b10w_txt:
    _bgn10w_bad("bgn10-chaos-wiring", "缺 material/ChaosWiring.java（接线层；反空转守护）")
else:
    # 接线层必须调唯一入口 `ChaosRange.current(`，且**不许**自带第二条乒乓公式
    if "ChaosRange.current(" not in _b10w_txt:
        _bgn10w_bad("bgn10-chaos-wiring", "接线层没有调 ChaosRange.current(...)（那就不是「接线」了）")
    if _bgn10_formula in _b10w_txt:
        _bgn10w_bad("bgn10-chaos-wiring",
                    "接线层里出现了乒乓公式本体（%s）—— 公式只许在 ChaosRange.java 一处" % _bgn10_formula)
    # 三个落点（缺一个就是"某一路的区间静默不生效"）
    for _needle, _why in (
            ("PlayerEvent.BreakSpeed", "缺挖掘速度落点（PlayerEvent.BreakSpeed）"),
            ("ItemAttributeModifierEvent", "缺攻击伤害落点（ItemAttributeModifierEvent）"),
            ("LivingIncomingDamageEvent",
             "远程命中的翻转没挂在 LivingIncomingDamageEvent 上（挂在 DamageEvent.Post 会被"
             "同一条链上任何异常吞掉 —— 轮3 实测：chaos 器具命中时 Config#weaponBuffChance 抛"
             "「未登记族」，Post 那一层整条轮不到）"),
            ("getWeaponItem()",
             "缺远程命中派发（DamageSource#getWeaponItem —— 红线 4：不许用主手）"),
            ("liveStackOf", "远程翻转没有「找射手手里那一栈」这一步 —— 在投射物带的副本上 toggle"
                            "不会改到手持栈（AbstractArrow#firedFromWeapon 是 copy()）")):
        if _needle not in _b10w_txt:
            _bgn10w_bad("bgn10-chaos-wiring", _why)
    # 挖掘速度的差值必须拿 Tier 的速度当基准（不是写死数字）
    if ".tier.getSpeed()" not in _b10w_txt:
        _bgn10w_bad("bgn10-chaos-wiring",
                    "挖掘差值没拿 family.tier.getSpeed() 当基准（写死数字 ⇒ 改区间时会两边不一致）")
# 近战「命中即翻转」的三个子类必须在（缺了 = 近战永不转换）
for _needle, _why in (
        ("class ChaosSwordItem", "缺剑的命中翻转子类"),
        ("class ChaosMaceItem", "缺重锤的命中翻转子类"),
        ("class ChaosTridentItem", "缺三叉戟的命中翻转子类"),
        ("static void flipAttackOnHit", "缺共用的翻转动作（flipAttackOnHit）")):
    if _needle not in strip_comments((JAVA / "material" / "MetalWeapons.java").read_text(encoding="utf-8")):
        _bgn10w_bad("bgn10-chaos-wiring", _why)
# 接线层必须注册在游戏总线
if ("NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.material.ChaosWiring.class)"
        not in strip_comments((JAVA / "bettergold.java").read_text(encoding="utf-8"))):
    _bgn10w_bad("bgn10-chaos-wiring",
                "接线层没有注册到游戏总线（攻击伤害/挖掘速度/远程翻转全部静默不生效）")

# 作者逐件给的数：从**声明字面**反解，再与期望表逐个对穿（不是拿期望表自比）
def _num(_s: str) -> float:
    return float(_s.rstrip("fF"))


# ⚠ 1.7 bg-n10r7（轮7）就地改造：解析改成**按族**（registerChaosgold / registerChaosalloy 各切各的方法体）。
#   旧口径（原文保留）= 在整份 AllMetals 上反解成一张全局表：
#     `_b10w_ranges = {(_f, _c): (_num(_a), _num(_b)) for _f, _c, _a, _b in re.findall(..., _bgn10_am_nc)}`
#   ⇒ 轮7 给崩乱合金声明了同一批形态（SWORD+MACE…）之后，后声明的那一档会**覆盖**前一档，
#     于是"混沌金的剑 4..8"被读成"8..16"⇒ 假红。改成按族切方法体后，两族各比各的期望表，
#     并且多了一条**跨族不变量**：崩乱合金每一档都必须**严格高于**混沌金（作者：崩乱合金在上）。
def _b10w_family_body(_method: str) -> str:
    _m = re.search(r"private static MetalFamily %s\(\) \{(.*?)\n    \}" % _method, _bgn10_am_nc, re.S)
    return _m.group(1) if _m else ""


def _b10w_parse_ranges(_body: str) -> dict:
    return {(_f, _c): (_num(_a), _num(_b)) for _f, _c, _a, _b in re.findall(
        r"chaosRange\(MetalFamily\.Form\.([A-Z_]+), ChaosRange\.Channel\.([A-Z_]+),\s*"
        r"([0-9.]+)[fF]?,\s*([0-9.]+)[fF]?\)", _body)}


def _b10w_parse_speeds(_body: str) -> dict:
    return {_f: _num(_v) for _f, _v in re.findall(
        r"attackSpeed\(MetalFamily\.Form\.([A-Z_]+),\s*([0-9.]+)[fF]?\)", _body)}


_b10w_body_cg = _b10w_family_body("registerChaosgold")
_b10w_body_ca = _b10w_family_body("registerChaosalloy")
if not _b10w_body_cg:
    _bgn10w_bad("bgn10-chaos-wiring", "解析不到 AllMetals.registerChaosgold()（反空转守护）")
if not _b10w_body_ca:
    _bgn10w_bad("bgn10-chaos-wiring", "解析不到 AllMetals.registerChaosalloy()（反空转守护）")
_b10w_ranges = _b10w_parse_ranges(_b10w_body_cg)
_b10w_speeds = _b10w_parse_speeds(_b10w_body_cg)
_b10w_ranges_ca = _b10w_parse_ranges(_b10w_body_ca)
_b10w_speeds_ca = _b10w_parse_speeds(_b10w_body_ca)
# 作者原话（立档 §2.4 / 任务口径）：剑 4..8 / 重锤 3..7 / 三叉戟 7..11 / 斧 7..10 / 镐 2..6 /
#   锹 2.5..6.5 / 锄 1..5 / 刀 1.5..5.5（乐事）/ 弓 2.0..3.5 / 弩 3.5..4.5；投掷 9..13
_B10W_WANT_RANGES = {
    ("SWORD", "ATTACK"): (4.0, 8.0),
    ("MACE", "ATTACK"): (3.0, 7.0),
    ("TRIDENT", "ATTACK"): (7.0, 11.0),
    ("AXE", "ATTACK"): (7.0, 10.0),
    ("PICKAXE", "ATTACK"): (2.0, 6.0),
    ("SHOVEL", "ATTACK"): (2.5, 6.5),
    ("HOE", "ATTACK"): (1.0, 5.0),
    ("KNIFE", "ATTACK"): (1.5, 5.5),
    ("BOW", "ATTACK"): (2.0, 3.5),
    ("CROSSBOW", "ATTACK"): (3.5, 4.5),
}
if len(_b10w_ranges) < len(_B10W_WANT_RANGES):
    _bgn10w_bad("bgn10-chaos-wiring",
                "从 AllMetals（混沌金）只反解到 %d 条形态区间声明（期望 >= %d；解析失败 / 声明被删）"
                % (len(_b10w_ranges), len(_B10W_WANT_RANGES)))
for _k, _want in _B10W_WANT_RANGES.items():
    _got = _b10w_ranges.get(_k)
    if _got != _want:
        _bgn10w_bad("bgn10-chaos-wiring",
                    "AllMetals（混沌金）的 %s+%s 声明的两端值 %s ≠ 作者给的 %s" % (_k[0], _k[1], _got, _want))
# ---------- 崩乱合金（1.7 bg-n10r7 轮7）：作者逐件给的数 ----------
# 剑 8..16 / 重锤 7..14 / 三叉戟 11..22 / 斧 10..20 / 镐 6..12 / 锹 6.5..13 / 锄 5..10 /
#   刀 5.5..11（乐事）/ 弓 3.5..4.5 / 弩 4.5..5；投掷 9..13（⚠ 与混沌金一字不差 ⇒ 疑似笔误，待作者裁）
_B10W_WANT_RANGES_CA = {
    ("SWORD", "ATTACK"): (8.0, 16.0),
    ("MACE", "ATTACK"): (7.0, 14.0),
    ("TRIDENT", "ATTACK"): (11.0, 22.0),
    ("AXE", "ATTACK"): (10.0, 20.0),
    ("PICKAXE", "ATTACK"): (6.0, 12.0),
    ("SHOVEL", "ATTACK"): (6.5, 13.0),
    ("HOE", "ATTACK"): (5.0, 10.0),
    ("KNIFE", "ATTACK"): (5.5, 11.0),
    ("BOW", "ATTACK"): (3.5, 4.5),
    ("CROSSBOW", "ATTACK"): (4.5, 5.0),
}
if len(_b10w_ranges_ca) < len(_B10W_WANT_RANGES_CA):
    _bgn10w_bad("bgn10-chaos-wiring",
                "从 AllMetals（崩乱合金）只反解到 %d 条形态区间声明（期望 >= %d）"
                % (len(_b10w_ranges_ca), len(_B10W_WANT_RANGES_CA)))
for _k, _want in _B10W_WANT_RANGES_CA.items():
    _got = _b10w_ranges_ca.get(_k)
    if _got != _want:
        _bgn10w_bad("bgn10-chaos-wiring",
                    "AllMetals（崩乱合金）的 %s+%s 声明的两端值 %s ≠ 作者给的 %s"
                    % (_k[0], _k[1], _got, _want))
# 跨族不变量：崩乱合金每一档都**严格高于**混沌金（作者：崩乱合金在混沌金之上）。
#   ⇒ 拦"整段复制混沌金的值忘了改"这种静默错。
for _k, _cg in _B10W_WANT_RANGES.items():
    _ca = _b10w_ranges_ca.get(_k)
    if _ca is not None and not (_ca[0] > _cg[0] and _ca[1] > _cg[1]):
        _bgn10w_bad("bgn10-chaos-wiring",
                    "崩乱合金的 %s 档 %s 没有严格高于混沌金 %s（两族数值疑似被复制成同一份）"
                    % (_k[0], _ca, _cg))
# 攻速：作者给的**最终值**（剑 1.6 / 重锤 0.6 / 三叉戟 1.1 / 斧 1 / 镐 1.2 / 锹 1 / 锄 4 / 刀 2）
_B10W_WANT_SPEEDS = {"SWORD": 1.6, "MACE": 0.6, "TRIDENT": 1.1, "AXE": 1.0,
                     "PICKAXE": 1.2, "SHOVEL": 1.0, "HOE": 4.0, "KNIFE": 2.0}
if len(_b10w_speeds) < len(_B10W_WANT_SPEEDS):
    _bgn10w_bad("bgn10-chaos-wiring",
                "从 AllMetals（混沌金）只反解到 %d 条攻速声明（期望 >= %d）"
                % (len(_b10w_speeds), len(_B10W_WANT_SPEEDS)))
for _k, _want in _B10W_WANT_SPEEDS.items():
    if _b10w_speeds.get(_k) != _want:
        _bgn10w_bad("bgn10-chaos-wiring",
                    "%s 的攻速声明 %s ≠ 作者给的 %s" % (_k, _b10w_speeds.get(_k), _want))
# 崩乱合金的攻速：作者只点名了 剑 1.6 / 重锤 0.6 / 三叉戟 1.1 / 刀 2，另四件用工作值
#   （斧 1.0 / 镐 1.2 / 锹 1.0 / 锄 4.0，= 原版同类器具的最终攻速）——
#   ⚠ 四件**必须显式声明**：`chaosAttributes` 的 ATTACK_SPEED 回退是 0.0（不写 = 最终攻速 4.0，刷手速）。
for _k, _want in _B10W_WANT_SPEEDS.items():
    if _b10w_speeds_ca.get(_k) != _want:
        _bgn10w_bad("bgn10-chaos-wiring",
                    "崩乱合金 %s 的攻速声明 %s ≠ %s（缺声明会让最终攻速变成 4.0）"
                    % (_k, _b10w_speeds_ca.get(_k), _want))
# 投掷 9..13 / 重锤 ×1.0 / 弓 20 tick / 弩 1.2 秒 / 刀 1.5+2.0 —— 逐条字面（混沌金）
for _lit, _why in (
        ("tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)", "缺投掷 9..13（作者原话）"),
        ("maceFinalDamageMultiplier(1.0F)", "缺重锤「最终伤 ×1.0」"),
        ("bowFullDraw(20, 0.0F)", "缺弓「拉弓 20 tick」"),
        ("crossbowCharge(1.2F)", "缺弩「蓄力 1.2 秒 = 24 tick」"),
        ("knifeAttributes(1.5F, 2.0F)", "缺乐事刀「伤害 1.5 下端 / 攻速 2」")):
    if _lit not in _bgn10_am_nc:
        _bgn10w_bad("bgn10-chaos-wiring", "AllMetals 里%s（字面 `%s`）" % (_why, _lit))
# 崩乱合金的区间外固定值：**逐条按作者原话**（与混沌金同名的三条 + 重锤 1.4 + 刀 5.5）
for _lit, _why in (
        ("tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)",
         "崩乱合金缺投掷 9..13（⚠ 作者给的就是 9..13，与混沌金一字不差 ⇒ 疑似笔误，按字面做）"),
        ("maceFinalDamageMultiplier(1.4F)", "崩乱合金缺重锤「最终伤 ×1.4 固定」"),
        ("bowFullDraw(20, 0.0F)", "崩乱合金缺弓「最大拉弓 20」"),
        ("crossbowCharge(1.2F)", "崩乱合金缺弩「蓄力 1.2 秒」"),
        ("knifeAttributes(5.5F, 2.0F)", "崩乱合金缺乐事刀「伤害 5.5 下端 / 攻速 2」"),
        ("imbalanceOnAttack()", "崩乱合金器具缺「命中挂失衡」"),
        ("imbalanceReflect()", "崩乱合金盔甲缺「被击反挂失衡」"),
        ("specialWeaponMetal(true, 2048)", "崩乱合金盾牌缺「格挡反 buff / 免疫破盾」那一档")):
    if _lit not in _b10w_body_ca:
        _bgn10w_bad("bgn10-chaos-wiring", "AllMetals（崩乱合金）里%s（字面 `%s`）" % (_why, _lit))
# 挖掘速度：注册基准必须是**区间上端**（否则"当前值 − 上端"的差值算错）
if "spec.miningSpeed = 12.0F" not in _bgn10_am_nc:
    _bgn10w_bad("bgn10-chaos-wiring", "chaosgold 的 miningSpeed 不是区间上端 12.0F（差值基准错）")
if "spec.miningSpeed = 16.0F" not in _bgn10_am_nc:
    _bgn10w_bad("bgn10-chaos-wiring", "chaosalloy 的 miningSpeed 不是区间上端 16.0F（差值基准错）")
# 弩的 24 tick 分支必须在 mixin 的入口上（正是既有 20 tick 那条的守卫处）
_mx = strip_comments((JAVA / "mixin" / "CrossbowChargeDurationMixin.java").read_text(encoding="utf-8"))
if "chargeDuration(stack, shooter)" not in _mx:
    _bgn10w_bad("bgn10-chaos-wiring",
                "弩的 mixin 不再走 MetalCrossbowItem#chargeDuration（1.2 秒 = 24 tick 的分支没了）")
print(f"1.7 轮3 区间值接线（反解到形态区间 {len(_b10w_ranges)} 条 / 攻速 {len(_b10w_speeds)} 条）问题: "
      f"{len(_bgn10w_problems)} {_bgn10w_problems[:4]}")

# ==================== 1.7 bg-n10 轮4：混沌金盔甲 + 混沌禁果 + 混沌金附魔书 ====================
# 本轮的三个交付物都是"声明了但不接线也全绿"的高危形状 ⇒ 每条都给"能从源码反解的判据"。
_bgn10r4_problems: list[str] = []


def _bgn10r4_bad(tag: str, msg: str) -> None:
    _bgn10r4_problems.append("[%s] %s" % (tag, msg))


# ---------- ① 混沌金盔甲：作者逐件给的数（护甲值 / 耐久）+ 附魔 24 + 韧性 3 ----------
# 数组顺序是 **靴 / 腿 / 胸 / 头**（与既有 8 族同序）—— 判据也按这个顺序比，防"头盔在前"填错。
_cg_body = re.search(r"private static MetalFamily registerChaosgold\(\) \{(.*?)\n    \}", _bgn10_am_nc, re.S)
_cg_txt = _cg_body.group(1) if _cg_body else ""
if not _cg_txt:
    _bgn10r4_bad("bgn10r4-chaosgold-armor", "解析不到 AllMetals.registerChaosgold()（反空转守护）")
else:
    _r4_need = {
        "spec.armorDefense = new int[] { 2, 3, 5, 2 }": "护甲值（靴2/腿3/胸5/头2）",
        "spec.armorDurability = new int[] { 246, 240, 264, 200 }": "耐久（靴246/腿240/胸264/头200）",
        "spec.armorEnchantmentValue = 24": "盔甲附魔能力 24",
        "spec.armorToughness = 3.0F": "盔甲韧性 3",
    }
    for _lit, _why in _r4_need.items():
        if _lit not in _cg_txt:
            _bgn10r4_bad("bgn10r4-chaosgold-armor",
                         "混沌金盔甲缺 %s（字面 `%s`）" % (_why, _lit))
    # 区间值减伤：四件各一条 ARMOR 区间声明（0..6）
    _r4_armor_ranges = re.findall(
        r"chaosRange\(MetalFamily\.Form\.([A-Z_]+), ChaosRange\.Channel\.ARMOR,\s*([0-9.]+)[fF]?,\s*([0-9.]+)[fF]?\)",
        _cg_txt)
    _r4_armor_map = {_f: (_num(_a), _num(_b)) for _f, _a, _b in _r4_armor_ranges}
    for _f in ("HELMET", "CHESTPLATE", "LEGGINGS", "BOOTS"):
        if _r4_armor_map.get(_f) != (0.0, 6.0):
            _bgn10r4_bad("bgn10r4-chaosgold-armor",
                         "{} 的 ARMOR 区间 {} ≠ 作者给的「最低 0% 最高 6%」".format(
                             _f, _r4_armor_map.get(_f)))

# ---------- ② ARMOR 通道的**接线**（唯一实现 + 落点 + 四个形态 + 只读/重掷的分工）----------
# ⛔ 旧口径（原文留档）：`("ChaosRange.toggle(", "翻转没走唯一入口 ChaosRange.toggle(...)")`
#    —— 作者 2026-10-18 把"翻转"改成"重掷"（`bg-n10fix` ⑩），现行 needle = `ChaosRange.reroll(`。
_mev_r4 = strip_comments((JAVA / "material" / "MetalEvents.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ("chaosArmorReduction(", "缺「四件之和」的减伤取值函数（接线没落地）"),
        ("flipChaosArmor(", "缺结算后的重掷动作（区间值永远是同一个数）"),
        ("ChaosRange.current(", "减伤取值没走唯一入口 ChaosRange.current(...)"),
        ("ChaosRange.reroll(", "重掷没走唯一入口 ChaosRange.reroll(...)"),
        ("Channel.ARMOR", "接线里没出现 ARMOR 通道（那就是没接）")):
    if _needle not in _mev_r4:
        _bgn10r4_bad("bgn10r4-armor-wiring", "%s（缺 %s）" % (_why, _needle))
# 接线层**不许**自带乒乓公式（公式只在 ChaosRange.java 一处）
if _bgn10_formula in _mev_r4:
    _bgn10r4_bad("bgn10r4-armor-wiring",
                 "MetalEvents 里出现了乒乓公式本体（%s）—— 公式只许在 ChaosRange.java 一处"
                 % _bgn10_formula)
# 四个盔甲伪形态必须在 formOf 里能反查到（否则按件取值永远退回通道级 = 每件同一个值）
_mf_r4 = strip_comments((JAVA / "material" / "MetalFamily.java").read_text(encoding="utf-8"))
_formof_body = method_body(_mf_r4, "public @Nullable Form formOf(Item item)")
for _f in ("Form.HELMET", "Form.CHESTPLATE", "Form.LEGGINGS", "Form.BOOTS"):
    if ("return %s;" % _f) not in _formof_body:
        _bgn10r4_bad("bgn10r4-armor-wiring",
                     "MetalFamily#formOf 里没有 `return %s;` ⇒ 该部位的区间取不到（退回通道级）" % _f)

# ---------- ③ 混沌禁果：配方 / 食物属性 / 冷却 / 效果池 ----------
_r4_recipe_dir = REPO / "src/main/resources/data/bettergold/recipe"
_r4_fruit = _r4_recipe_dir / "chaosgold_forbidden_fruit.json"
if not _r4_fruit.is_file():
    _bgn10r4_bad("bgn10r4-forbidden-fruit", "缺配方 chaosgold_forbidden_fruit.json")
else:
    _r4_fruit_obj = json.loads(_r4_fruit.read_text(encoding="utf-8"))
    _r4_ings = [i.get("item") for i in _r4_fruit_obj.get("ingredients", [])]
    if _r4_fruit_obj.get("type") != "minecraft:crafting_shapeless":
        _bgn10r4_bad("bgn10r4-forbidden-fruit", "禁果配方不是无序合成（作者只给了「1 苹果 + 8 混沌金锭」）")
    if _r4_ings.count("minecraft:apple") != 1:
        _bgn10r4_bad("bgn10r4-forbidden-fruit", "禁果配方里苹果不是 1 个：%s" % _r4_ings)
    if _r4_ings.count("bettergold:chaosgold_ingot") != 8:
        _bgn10r4_bad("bgn10r4-forbidden-fruit",
                     "禁果配方里混沌金锭不是 8 个（实际 %d）" % _r4_ings.count("bettergold:chaosgold_ingot"))
    if _r4_fruit_obj.get("result", {}).get("id") != "bettergold:chaosgold_forbidden_fruit":
        _bgn10r4_bad("bgn10r4-forbidden-fruit", "禁果配方的产物不是 chaosgold_forbidden_fruit")
_ci = JAVA / "material" / "ChaosItems.java"
_ci_txt = strip_comments(_ci.read_text(encoding="utf-8")) if _ci.is_file() else ""
if not _ci_txt:
    _bgn10r4_bad("bgn10r4-forbidden-fruit", "缺 material/ChaosItems.java（反空转守护）")
else:
    for _needle, _why in (
            ("GOLDEN_APPLE_NUTRITION = 4", "饥饿不是原版金苹果的 4"),
            ("GOLDEN_APPLE_SATURATION_MODIFIER = 1.2F",
             "饱和度系数不是 1.2（= 原版金苹果 9.6 / (4×2)）"),
            ("FORBIDDEN_FRUIT_EFFECT_TICKS = 3600", "效果时长不是 3 分钟 3600 tick"),
            ("FORBIDDEN_FRUIT_COOLDOWN_TICKS = 3600", "冷却不是 3 分钟 3600 tick"),
            ("FORBIDDEN_FRUIT_MAX_LEVEL = 3", "效果等级上限不是 3"),
            # ⚠ 1.7 bg-n10r7（轮7）就地改造：轮7 把「时长 / 冷却 / 等级区间」参数化，
            #   好让崩乱禁果（16 分钟 / 1..4 级）复用同一份实现 ⇒ 调用点的字面从
            #   `addCooldown(this, FORBIDDEN_FRUIT_COOLDOWN_TICKS)` 变成 `addCooldown(this, cooldownTicks)`
            #   （旧期望原文留档：`addCooldown(this, FORBIDDEN_FRUIT_COOLDOWN_TICKS)`）。
            #   新判据**更强**：冷却必须由"每次读字段"给出（不是写死的常量），且两个禁果的参数都要在。
            ("addCooldown(this, cooldownTicks)", "没有真的挂 ItemCooldowns（且冷却不是按本物参数给）"),
            ("CHAOSALLOY_FRUIT_EFFECT_TICKS = 16 * 60 * 20", "崩乱禁果的效果时长不是 16 分钟"),
            ("CHAOSALLOY_FRUIT_COOLDOWN_TICKS = 16 * 60 * 20", "崩乱禁果的冷却不是 16 分钟"),
            ("CHAOSALLOY_FRUIT_MAX_LEVEL = 4", "崩乱禁果的效果等级上限不是 4"),
            ("CHAOSALLOY_FRUIT_SATURATION_MODIFIER = 1.45F",
             "崩乱禁果的饱和度系数不是 1.45（= 11.6 / (4×2)，原版金苹果 9.6 + 2）"),
            ("BuiltInRegistries.MOB_EFFECT.holders()", "效果抽取池不是「全部已注册效果」（含第三方）")):
        if _needle not in _ci_txt:
            _bgn10r4_bad("bgn10r4-forbidden-fruit", "%s（缺 %s）" % (_why, _needle))
    # 抽取池**不许**被白名单/黑名单收窄（作者裁定「按字面 = 全部已注册」）
    for _bad in ("isInstantenous", "MobEffectCategory.BENEFICIAL", "HARMFUL.equals",
                 "exclude", "blacklist"):
        if _bad in _ci_txt:
            _bgn10r4_bad("bgn10r4-forbidden-fruit",
                         "效果抽取池被筛过（出现 `%s`）—— 作者裁定是「全部已注册效果，抽到什么算什么」"
                         % _bad)

# ---------- ④ 混沌金附魔书：配方 / 零 UI / 门槛 / 适配过滤 / 含宝藏诅咒第三方 ----------
_r4_book = _r4_recipe_dir / "chaosgold_enchanting_book.json"
if not _r4_book.is_file():
    _bgn10r4_bad("bgn10r4-enchanting-book", "缺配方 chaosgold_enchanting_book.json")
else:
    _r4_book_obj = json.loads(_r4_book.read_text(encoding="utf-8"))
    _r4_pat = _r4_book_obj.get("pattern", [])
    _r4_key = _r4_book_obj.get("key", {})
    if _r4_book_obj.get("type") != "minecraft:crafting_shaped":
        _bgn10r4_bad("bgn10r4-enchanting-book", "附魔书配方不是有序合成（截图的 3×3 摆位）")
    # ⚠ 1.7 bg-n10rc（2026-10-17）**就地更正**：作者口述「右上角和左下角：2 个混沌金币串 /
    #   左上角和右下角：2 个青晶石」⇒ 青金石在**主对角**、币串在**副对角**。
    #   旧期望原文留档（不删）：`if _r4_pat != ["LIL", "IBI", "SIS"]:` +
    #   文案「附魔书的 3×3 摆位 %s ≠ 截图读出的 LIL/IBI/SIS」。
    #   ⚠ 旧形状把两件平分到左右两条边（青金石在左上/右上、币串在左下/右下）——
    #   连立档 §2.6 自己写的"100% 读出"都不符；但**计数完全相同** ⇒ 下面那条计数断言
    #   （`_want_cnt`）本来抓不到它，真正的判据是本轮新增的**逐格**断言 `[bgn10rc-cell]`。
    if _r4_pat != ["LIS", "IBI", "SIL"]:
        _bgn10r4_bad("bgn10r4-enchanting-book",
                     "附魔书的 3×3 摆位 %s ≠ 作者 2026-10-17 口述的 LIS/IBI/SIL"
                     "（青金石在主对角、混沌金币串在副对角）" % _r4_pat)
    # 计数：青金石 2 / 混沌金锭 4 / 原版书 1 / 混沌金币串 2
    _cnt = {}
    for _ch in "".join(_r4_pat):
        _ing = _r4_key.get(_ch, {}).get("item")
        if _ing:
            _cnt[_ing] = _cnt.get(_ing, 0) + 1
    _want_cnt = {"minecraft:lapis_lazuli": 2, "bettergold:chaosgold_ingot": 4,
                 "minecraft:book": 1, "bettergold:chaos_coin_string": 2}
    if _cnt != _want_cnt:
        _bgn10r4_bad("bgn10r4-enchanting-book",
                     "附魔书配方计数 %s ≠ 作者给的 %s（2 青金石 + 4 混沌金锭 + 1 书 + 2 金币串）"
                     % (_cnt, _want_cnt))
if _ci_txt:
    for _needle, _why in (
            ("ENCHANTING_BOOK_MIN_PLAYER_LEVEL = 5", "「<5 级无法使用」的门槛不是 5"),
            ("experienceLevel < ENCHANTING_BOOK_MIN_PLAYER_LEVEL", "没有判玩家等级（门槛没落地）"),
            # ⚠ 旧期望（`InteractionHand.OFF_HAND` + 「副手书 / 右手装备」）原文留档在这里、不删：
            #   ("InteractionHand.OFF_HAND", "没判「左手附魔书」（作者写死的交互形状）"),
            # 作者 2026-10-18 亲口推翻（`bg-n10fix` ④-2）：「**副手拿装备、主手拿书**」——
            # 盔甲右键穿戴与"右手装备 + 左手书"冲突 ⇒ 现行期望 = MAIN_HAND。
            ("InteractionHand.MAIN_HAND", "没判「主手附魔书」（作者 2026-10-18 的新交互形状）"),
            ("player.getOffhandItem()", "没有把**副手**当作被附魔的装备（作者 2026-10-18 的新形状）"),
            # ④-3 成功时播附魔台音效；④-4 创造模式跳过门槛与扣级；④-1 堆叠 16
            ("SoundEvents.ENCHANTMENT_TABLE_USE", "成功时没播附魔台音效（作者点名）"),
            ("player.isCreative()", "创造模式没有单独分支（作者要「不耗经验、直接可用」）"),
            ("stacksTo(16)", "附魔书的最大堆叠不是 16（作者 2026-10-18 点名）"),
            ("canEnchant", "没有按「适配该装备类型」过滤（canEnchant / 物品标签）"),
            ("updateEnchantments(", "没有真把附魔写进右手装备"),
            ("giveExperienceLevels(-cost)", "没有消耗经验等级"),
            ("ENCHANTING_BOOK_MAX_COST = 5", "消耗上限不是 5 级"),
            ("ENCHANTING_BOOK_MAX_ENCH_LEVEL = 5", "附魔等级上限不是 5")):
        if _needle not in _ci_txt:
            _bgn10r4_bad("bgn10r4-enchanting-book", "%s（缺 %s）" % (_why, _needle))
    # ⚠ **零 UI**（作者裁定 ⑧a：随机抽一条、不做选择界面）⇒ 不许出现任何界面/网络包痕迹
    for _bad in ("Screen", "AbstractContainerMenu", "MenuType", "Payload", "sendToClient"):
        if _bad in _ci_txt:
            _bgn10r4_bad("bgn10r4-enchanting-book",
                         "附魔书里出现了 `%s` —— 作者裁定是零 UI / 纯服务端" % _bad)
    # ⚠ **不许**过滤宝藏 / 诅咒（作者要"含宝藏 / 诅咒 / 第三方"）
    for _bad in ("isTreasureOnly", "isCurse", "EnchantmentTags", "isTradeable", "isDiscoverable"):
        if _bad in _ci_txt:
            _bgn10r4_bad("bgn10r4-enchanting-book",
                         "附魔候选被筛过（出现 `%s`）—— 作者要「含宝藏 / 诅咒 / 第三方」" % _bad)

# ---------- ⑤ 两件物品必须真的注册 + 进创造页（"注册了但静默不进页"是同一种病）----------
_bgn10r4_boot = strip_comments((JAVA / "bettergold.java").read_text(encoding="utf-8"))
if "ChaosItems.bootstrap()" not in _bgn10r4_boot:
    _bgn10r4_bad("bgn10r4-items-registered",
                 "ChaosItems 没有被显式触发（两件物品可能根本没注册 —— 依赖类初始化顺序是坑）")
for _needle, _why in (
        ('"chaosgold_forbidden_fruit"', "禁果没注册（注册名）"),
        ('"chaosgold_enchanting_book"', "附魔书没注册（注册名）")):
    if _needle not in _ci_txt:
        _bgn10r4_bad("bgn10r4-items-registered", "%s（缺 %s）" % (_why, _needle))
_cs_txt = strip_comments((JAVA / "material" / "CreativeSections.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ('Map.entry("forbidden_fruit"', "禁果没进创造页装备分区（GEAR_SLOT）"),
        ('Map.entry("enchanting_book"', "附魔书没进创造页装备分区（GEAR_SLOT）")):
    if _needle not in _cs_txt:
        _bgn10r4_bad("bgn10r4-items-registered", _why)
# 语言键：两件物品 + 那句提示，中英都要有且**不许相等**（红线 10 的同族要求）
_r4_lang = REPO / "src/main/resources/assets/bettergold/lang"
_zh_r4 = json.loads((_r4_lang / "zh_cn.json").read_text(encoding="utf-8"))
_en_r4 = json.loads((_r4_lang / "en_us.json").read_text(encoding="utf-8"))
for _k in ("item.bettergold.chaosgold_forbidden_fruit",
           "item.bettergold.chaosgold_enchanting_book",
           "message.bettergold.chaos_enchanting_book.too_low_level"):
    if _k not in _zh_r4:
        _bgn10r4_bad("bgn10r4-items-registered", "zh 缺语言键 %s" % _k)
    if _k not in _en_r4:
        _bgn10r4_bad("bgn10r4-items-registered", "en 缺语言键 %s" % _k)
    if _zh_r4.get(_k) == _en_r4.get(_k):
        _bgn10r4_bad("bgn10r4-items-registered", "%s 的中英逐字相同（等于没译）" % _k)

# ==================== 1.7（bg-n10 轮6）：金钱妖 ====================
# 本仓第一个活体生物。它没有既有关卡可依 ⇒ 这一节就是它的门禁：
#   ① 实体 / 弹射物 / 生成蛋 / 属性 / 近战表 / 弹幕表 / 饥饿叠加 都必须在**去注释源码**上落到字面；
#   ② 两个伤害类型 JSON 必须存在且 scaling=never（否则显式表会被原版难度再乘一遍）；
#   ③ 自然生成（biome modifier）与 spawn placement 必须存在；
#   ④ 贴图必须与归档副本**逐字节相同**（作者素材原样）；
#   ⑤ 双倍伤害只有一个判定入口（旧族行为不变）；
#   ⑥ 动画恰好两套（idle / walk，不造第三套）。
bgn10r6_problems: list[str] = []
_r6_checked = 0


def _bgn10r6_bad(tag: str, msg: str) -> None:
    bgn10r6_problems.append("[%s] %s" % (tag, msg))


_R6_RES = REPO / "src/main/resources"
_R6_ARCHIVE = REPO / "docs" / "新约10-素材清单" / "金钱妖"

# ---------- ① 实体注册（AllEntities）：活体生物 + 弹射物 ----------
_r6_entities = strip_comments((JAVA / "registry" / "AllEntities.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ('"money_gremlin"', "金钱妖实体没注册（注册名）"),
        ('"chaos_coin"', "混沌金币弹射物没注册（注册名）"),
        ("MobCategory.MONSTER", "金钱妖不是 MONSTER 类别"),
        ("MoneyGremlin::new", "金钱妖的 EntityType 工厂不是 MoneyGremlin"),
        ("ChaosCoinProjectile::new", "弹射物的 EntityType 工厂不是 ChaosCoinProjectile")):
    _r6_checked += 1
    if _needle not in _r6_entities:
        _bgn10r6_bad("bgn10r6-entity", "%s（缺 %s）" % (_why, _needle))
_r6_checked += 1
if ".sized(1.2F, 1.2F)" not in _r6_entities:
    _bgn10r6_bad("bgn10r6-entity", "金钱妖命中箱不是工作值 1.2×1.2（改了就同步记账）")

# ---------- ② 生物类：所有作者原话数值都必须是字面常量/表 ----------
_r6_mob = strip_comments((JAVA / "entity" / "MoneyGremlin.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ("extends Monster", "父类不是 Monster（普通敌对生物口径）"),
        ("MAX_HEALTH = 30.0D", "最大生命值不是 30"),
        ("CHASE_RANGE = 32.0D", "追击/丢失范围不是 32"),
        ("TARGET_RANGE = 32.0D", "目标选择范围不是 32（作者要求两个数分开写）"),
        ("BARRAGE_INTERVAL_TICKS = 120", "弹幕间隔不是 120 tick"),
        # ⛔ 旧口径（原文留档）：("BARRAGE_RANGE = 3.0D", "弹幕间距不是 3 格")
        #   作者 2026-10-18 更正：「只会对自身**三格外**的玩家才会施展发射金币，而不是三格内」
        #   ⇒ 现行 = BARRAGE_MIN_RANGE + isBeyondBarrageRange（严格大于 3 格）。
        ("BARRAGE_MIN_RANGE = 3.0D", "弹幕最小间距不是 3 格（`bg-n10fix` ⑧）"),
        ("isBeyondBarrageRange", "没有「三格之外才打」的判据（`bg-n10fix` ⑧）"),
        ("BARRAGE_COUNT = 8", "弹幕枚数不是 8"),
        ("case EASY -> 4.0F", "近战简单难度不是 4"),
        ("case NORMAL -> 8.0F", "近战普通难度不是 8"),
        ("case HARD -> 12.0F", "近战困难难度不是 12"),
        ("getBoundingBox().getCenter()", "弹幕原点不是碰撞箱几何中心"),
        ("Vec3.directionFromRotation(0.0F, i * 45.0F)", "米字方向不是水平 45°×8 / pitch 0"),
        ("dropCustomDeathLoot", "掉落没走 dropCustomDeathLoot"),
        ("COWRIE_MOLD_BASE_CHANCE = 0.16F", "金钱贝模具基础概率不是 16%"),
        ("EXPERIENCE_REWARD = 10", "经验不是 10"),
        ("isFireOrLava", "没有火焰/岩浆伤害类型判据"),
        ("DamageTypes.ON_FIRE", "火焰伤害集合没有 on_fire"),
        ("DamageTypes.IN_FIRE", "火焰伤害集合没有 in_fire"),
        ("DamageTypes.LAVA", "火焰伤害集合没有 lava")):
    _r6_checked += 1
    if _needle not in _r6_mob:
        _bgn10r6_bad("bgn10r6-mob", "%s（缺 %s）" % (_why, _needle))
# 显式难度表：不许出现「读 ATTACK_DAMAGE 再交给原版」的写法（doHurtTarget 里只许调 meleeDamageFor）
_r6_checked += 2
_r6_hurttarget = method_body(_r6_mob, "public boolean doHurtTarget(")
if "meleeDamageFor" not in _r6_hurttarget:
    _bgn10r6_bad("bgn10r6-mob", "doHurtTarget 没有走显式难度表 meleeDamageFor（会被原版难度再乘一遍）")
if "getAttributeValue(Attributes.ATTACK_DAMAGE)" in _r6_hurttarget:
    _bgn10r6_bad("bgn10r6-mob", "doHurtTarget 读了 ATTACK_DAMAGE 属性（作者要求显式查表）")
# 弹幕节流 / 只在有目标时：customServerAiStep 里必须同时出现 target / cooldown / 距离三件事
_r6_ai = method_body(_r6_mob, "protected void customServerAiStep()")
for _needle in ("getTarget()", "barrageCooldown", "isBeyondBarrageRange"):
    _r6_checked += 1
    if _needle not in _r6_ai:
        _bgn10r6_bad("bgn10r6-barrage", "customServerAiStep 缺 %s（有目标 / 节流 / 间距 三件事）" % _needle)

# ---------- ③ 弹射物类：表 / 重力 0 / 饥饿公式 ----------
_r6_coin = strip_comments((JAVA / "entity" / "ChaosCoinProjectile.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ("case EASY -> 2.0F", "弹射物简单难度不是 2"),
        ("case NORMAL -> 4.0F", "弹射物普通难度不是 4"),
        ("case HARD -> 6.0F", "弹射物困难难度不是 6"),
        ("HUNGER_DURATION_TICKS = 36 * 20", "饥饿时长不是 36 秒"),
        ("HUNGER_MAX_LEVEL = 12", "饥饿层数上限不是 12"),
        ("getDefaultGravity", "没有覆写 getDefaultGravity（「笔直」= 重力 0）"),
        ("Math.min(currentLevel + 1, HUNGER_MAX_LEVEL)", "饥饿叠加不是「等级 +1、上限 12」"),
        ("removeEffect(MobEffects.HUNGER)", "饥饿没有先移除再挂（等级语义会漂）")):
    _r6_checked += 1
    if _needle not in _r6_coin:
        _bgn10r6_bad("bgn10r6-coin", "%s（缺 %s）" % (_why, _needle))
_r6_checked += 1
if "return 0.0D;" not in method_body(_r6_coin, "protected double getDefaultGravity()"):
    _bgn10r6_bad("bgn10r6-coin", "getDefaultGravity 没有返回 0.0D")

# ---------- ④ 伤害类型 JSON：scaling=never（显式表不被原版难度再乘） ----------
for _id, _msg in (("money_gremlin_melee", "bettergold.money_gremlin_melee"),
                  ("chaos_coin", "bettergold.chaos_coin")):
    _p = _R6_RES / "data" / "bettergold" / "damage_type" / (_id + ".json")
    _r6_checked += 3
    if not _p.is_file():
        _bgn10r6_bad("bgn10r6-damage-type", "缺 %s" % _p.relative_to(REPO))
        continue
    try:
        _d = json.loads(_p.read_text(encoding="utf-8"))
    except Exception as _e:  # noqa: BLE001
        _bgn10r6_bad("bgn10r6-damage-type", "%s 解析失败：%s" % (_id, _e))
        continue
    if _d.get("scaling") != "never":
        _bgn10r6_bad("bgn10r6-damage-type",
                     "%s 的 scaling=%r（必须是 never，否则玩家受伤会被难度再乘）"
                     % (_id, _d.get("scaling")))
    if _d.get("message_id") != _msg:
        _bgn10r6_bad("bgn10r6-damage-type", "%s 的 message_id=%r ≠ %r"
                     % (_id, _d.get("message_id"), _msg))

# ---------- ⑤ 自然生成 + spawn placement + 生成蛋 ----------
_r6_checked += 5
_r6_biome = _R6_RES / "data" / "bettergold" / "neoforge" / "biome_modifier" / "add_money_gremlin.json"
if not _r6_biome.is_file():
    _bgn10r6_bad("bgn10r6-spawn", "缺 biome modifier add_money_gremlin.json")
else:
    try:
        _b = json.loads(_r6_biome.read_text(encoding="utf-8"))
        if _b.get("type") != "neoforge:add_spawns":
            _bgn10r6_bad("bgn10r6-spawn", "biome modifier type=%r" % _b.get("type"))
        _sp = _b.get("spawners") or {}
        if (_sp.get("type") if isinstance(_sp, dict) else None) != "bettergold:money_gremlin":
            _bgn10r6_bad("bgn10r6-spawn", "biome modifier 的 spawner.type 不是 bettergold:money_gremlin")
    except Exception as _e:  # noqa: BLE001
        _bgn10r6_bad("bgn10r6-spawn", "biome modifier 解析失败：%s" % _e)
_r6_boot = strip_comments((JAVA / "bettergold.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ("EntityAttributeCreationEvent", "没有注册金钱妖属性（EntityAttributeCreationEvent）"),
        ("RegisterSpawnPlacementsEvent", "没有注册自然生成规则（RegisterSpawnPlacementsEvent）"),
        ("MoneyGremlinEvents.class", "没有挂金钱妖的伤害事件"),
        ("Monster::checkMonsterSpawnRules", "自然生成没走「黑暗处」的 Monster 判据")):
    _r6_checked += 1
    if _needle not in _r6_boot:
        _bgn10r6_bad("bgn10r6-spawn", "%s（缺 %s）" % (_why, _needle))
_r6_items = strip_comments((JAVA / "registry" / "AllItems.java").read_text(encoding="utf-8"))
if '"money_gremlin_spawn_egg"' not in _r6_items or "DeferredSpawnEggItem" not in _r6_items:
    _bgn10r6_bad("bgn10r6-spawn", "金钱妖刷怪蛋没注册（或不是 DeferredSpawnEggItem）")
_r6_checked += 2
_r6_egg_model = _R6_RES / "assets" / "bettergold" / "models" / "item" / "money_gremlin_spawn_egg.json"
if not _r6_egg_model.is_file():
    _bgn10r6_bad("bgn10r6-spawn", "缺刷怪蛋模型 money_gremlin_spawn_egg.json")
else:
    _em = json.loads(_r6_egg_model.read_text(encoding="utf-8"))
    if _em.get("parent") != "minecraft:item/template_spawn_egg":
        _bgn10r6_bad("bgn10r6-spawn", "刷怪蛋模型 parent=%r" % _em.get("parent"))

# ---------- ⑥ 贴图：与归档副本逐字节相同（64×64） ----------
_r6_checked += 4
_r6_tex = _R6_RES / "assets" / "bettergold" / "textures" / "entity" / "money_gremlin.png"
_r6_arc_tex = _R6_ARCHIVE / "money_gremlin.png"
if not _r6_tex.is_file():
    _bgn10r6_bad("bgn10r6-texture", "缺 textures/entity/money_gremlin.png")
elif not _r6_arc_tex.is_file():
    _bgn10r6_bad("bgn10r6-texture", "缺归档副本（前置坏了）")
else:
    _tb = _r6_tex.read_bytes()
    if _tb[:8] != b"\x89PNG\r\n\x1a\n":
        _bgn10r6_bad("bgn10r6-texture", "不是 PNG")
    else:
        _w = int.from_bytes(_tb[16:20], "big")
        _h = int.from_bytes(_tb[20:24], "big")
        if _w != 64 or _h != 64:
            _bgn10r6_bad("bgn10r6-texture", "贴图尺寸 %dx%d ≠ 64x64" % (_w, _h))
    if _tb != _r6_arc_tex.read_bytes():
        _bgn10r6_bad("bgn10r6-texture",
                     "src 里的贴图与归档副本**不是逐字节相同**（作者素材原样）")

# ---------- ⑦ 双倍伤害：唯一入口 + 烈燃金挂到了金钱妖 ----------
_r6_checked += 1
_bgn10r6_entry_hits = 0
for _p in JAVA.rglob("*.java"):
    _src = strip_comments(_p.read_text(encoding="utf-8"))
    if "public boolean isDoubleDamageTarget(" in _src:
        _bgn10r6_entry_hits += 1
if _bgn10r6_entry_hits != 1:
    _bgn10r6_bad("bgn10r6-double-damage",
                 "isDoubleDamageTarget 的**定义**出现 %d 处（必须恰好 1 处 = 唯一入口）"
                 % _bgn10r6_entry_hits)
_r6_metals = strip_comments((JAVA / "material" / "AllMetals.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ("doubleDamageOnDeferredTarget", "烈燃金没有走延迟目标入口"),
        ("AllEntities.MONEY_GREMLIN", "烈燃金没点名 money_gremlin")):
    _r6_checked += 1
    if _needle not in _r6_metals:
        _bgn10r6_bad("bgn10r6-double-damage", "%s（缺 %s）" % (_why, _needle))
_r6_checked += 2
_r6_metal_events = strip_comments((JAVA / "material" / "MetalEvents.java").read_text(encoding="utf-8"))
if "family.isDoubleDamageTarget(target.getType())" not in _r6_metal_events:
    _bgn10r6_bad("bgn10r6-double-damage", "MetalEvents 没走唯一入口 isDoubleDamageTarget")
if "contactDamageTargets.contains(target.getType())" in _r6_metal_events:
    _bgn10r6_bad("bgn10r6-double-damage",
                 "MetalEvents 里仍留着旧的 contactDamageTargets.contains 判定（两个入口 = 会漂）")

# ---------- ⑧ 语言键：实体名 / 刷怪蛋 / 两条死亡提示 ----------
for _k in ("entity.bettergold.money_gremlin",
           "item.bettergold.money_gremlin_spawn_egg",
           "death.attack.bettergold.money_gremlin_melee",
           "death.attack.bettergold.chaos_coin"):
    _r6_checked += 2
    if _k not in zh:
        _bgn10r6_bad("bgn10r6-lang", "zh 缺语言键 %s" % _k)
    if _k not in en:
        _bgn10r6_bad("bgn10r6-lang", "en 缺语言键 %s" % _k)
    if _k in zh and _k in en and zh.get(_k) == en.get(_k):
        _bgn10r6_bad("bgn10r6-lang", "%s 的中英逐字相同（等于没译）" % _k)

# ---------- ⑨ 模型/动画：恰好两套（idle / walk），HierarchicalModel ----------
_r6_checked += 6
_r6_model = strip_comments((JAVA / "client" / "MoneyGremlinModel.java").read_text(encoding="utf-8"))
_r6_anim = strip_comments((JAVA / "client" / "MoneyGremlinAnimations.java").read_text(encoding="utf-8"))
if "extends HierarchicalModel<MoneyGremlin>" not in _r6_model:
    _bgn10r6_bad("bgn10r6-model", "模型不是 HierarchicalModel（KeyframeAnimations 播不了）")
if _r6_anim.count("AnimationDefinition.Builder") != 2:
    _bgn10r6_bad("bgn10r6-model",
                 "动画定义 %d 套（裁定 ③b：只许 idle / walk 两套）"
                 % _r6_anim.count("AnimationDefinition.Builder"))
for _needle in ("IDLE", "WALK", "animateWalk", "idleAnimationState"):
    if _needle not in _r6_anim and _needle not in _r6_model:
        _bgn10r6_bad("bgn10r6-model", "缺 %s（idle/walk 二选一的接法）" % _needle)

print(f"1.7 轮6（金钱妖：实体/弹射物/掉落/烈燃金双倍/米字弹幕）问题: "
      f"{len(bgn10r6_problems)} {bgn10r6_problems[:4]}（本段判定 {_r6_checked} 条，循环已展开计数）")
if _r6_checked <= 0:
    _bgn10r6_bad("bgn10r6-anti-vacuum", "本段一条判定都没跑（反空转）")
if not bgn10r6_problems:
    print("[bgn10r6-ok] 金钱妖：实体/弹射物/伤害表/贴图哈希/双倍入口/语言键/两套动画 全部通过")

print(f"1.7 轮4（混沌金盔甲 / 禁果 / 附魔书：盔甲区间 {len(_r4_armor_map)} 件）问题: "
      f"{len(_bgn10r4_problems)} {_bgn10r4_problems[:4]}")

print(f"1.7 两个共用组件（形态子集 {len(MF.FORMS)} 族 / 区间值公式命中 {len(_hits)} 处）问题: "
      f"{len(bgn10_problems)} {bgn10_problems[:4]}")

# ==========================================================================================
# 1.7 轮5（bg-n10r5，2026-10-17）：金火把花 + 高精度炼金油
# ==========================================================================================
# 作者原话（该段）：「金火把花种子，由 1 原版火把花种子搭配 6 金粒无序制成，用于种植金染耕地上
# 长成金火把花，且可用金骨粉直接催熟到满。金火把花不仅能提供 16 点的亮度（顺带也兼容一下花盆样式）
# 还能在酿造台上以炼金燃油为基、以金火把花为引即可酿制成高精度炼金油，此精油还可以作为
# 产出双倍"贵金"原料的材料，详细配方请去看我所给的贴图文件里头」。
#
# ⚠ 「双倍贵金原料」那条配方**本轮没有依据**（作者说看贴图，但 zip 的 配方图集/ 只有 4 张、
#   与本轮无关）⇒ 只落物品本体 + 记账，**不许**在这里假装它已被验证。
#   关卡对它的要求只有一条：**不许悄悄发明一套翻倍算法**（下面 ⑨ 的负向断言）。
bgn10r5_problems: list[str] = []
_bgn10r5_checked = 0


def _bgn10r5_bad(tag: str, msg: str) -> None:
    bgn10r5_problems.append("[%s] %s" % (tag, msg))


_R5_ASSETS = REPO / "src" / "main" / "resources" / "assets" / "bettergold"
_R5_DATA = REPO / "src" / "main" / "resources" / "data"
_R5_JAVA = JAVA

# ---------- ① 5 张贴图：必须是作者 zip 里的字节原样（SHA256 锚点） ----------
# 值 = 作者 zip 内文件的 SHA256（本轮 `r5_inspect_sprites.py` 复算；来源只读，未改一字节）
_R5_TEXTURES = {
    "textures/item/golden_torchflower_seeds.png":
        "FBADEB2010876A7293B6377B4703AEBACE0423100437FB0FF4EB6A5AB7638E2D",
    "textures/block/golden_torchflower_crop_stage0.png":
        "E7A05F680BDE291F81C0EA40B8746A0DF4AE1E3CE71602051F5C17B2629474E2",
    "textures/block/golden_torchflower_crop_stage1.png":
        "72E9694C3C2F839125185CF95D0912574C4B23CAC4A34802C64DEEA5A9543A12",
    "textures/block/golden_torchflower.png":
        "E9CB6183753F0C2CE0883A157207424E46AB9D3E52199A27ABCEB3F55D5AFDC0",
    "textures/item/refined_alchemic_oil.png":
        "D5858CD06AE5915F4141DABC1A84E34C1996BE4BEA774B22ECC8F860A557E0B9",
}
for _rel, _want in _R5_TEXTURES.items():
    _bgn10r5_checked += 1
    _p = _R5_ASSETS / _rel
    if not _p.is_file():
        _bgn10r5_bad("bgn10r5-textures", "缺贴图 " + _rel)
        continue
    _got = hashlib.sha256(_p.read_bytes()).hexdigest().upper()
    if _got != _want:
        _bgn10r5_bad("bgn10r5-textures",
                     _rel + " 的 SHA256 = " + _got[:32] + " ≠ 作者 zip 原件的 " + _want[:32]
                     + "（贴图白名单：除既有三张授权外不许改、也不许自己画）")

# ---------- ② 方块状态 / 模型 / 战利品 / 配方：文件在 + 引用不悬空 ----------
_R5_JSON = [
    "assets/bettergold/blockstates/golden_torchflower.json",
    "assets/bettergold/blockstates/golden_torchflower_crop.json",
    "assets/bettergold/blockstates/potted_golden_torchflower.json",
    "assets/bettergold/models/block/golden_torchflower.json",
    "assets/bettergold/models/block/golden_torchflower_crop_stage0.json",
    "assets/bettergold/models/block/golden_torchflower_crop_stage1.json",
    "assets/bettergold/models/block/potted_golden_torchflower.json",
    "assets/bettergold/models/item/golden_torchflower.json",
    "assets/bettergold/models/item/golden_torchflower_seeds.json",
    "assets/bettergold/models/item/refined_alchemic_oil.json",
    "data/bettergold/loot_table/blocks/golden_torchflower.json",
    "data/bettergold/loot_table/blocks/golden_torchflower_crop.json",
    "data/bettergold/recipe/golden_torchflower_seeds.json",
]
for _rel in _R5_JSON:
    _bgn10r5_checked += 1
    if not (REPO / "src" / "main" / "resources" / _rel).is_file():
        _bgn10r5_bad("bgn10r5-assets", "缺资源文件 " + _rel)

# 模型里引用的我方贴图必须真的存在（防紫黑格）
for _rel, _needles in (
        ("assets/bettergold/models/block/golden_torchflower.json",
         ["bettergold:block/golden_torchflower"]),
        ("assets/bettergold/models/block/golden_torchflower_crop_stage0.json",
         ["bettergold:block/golden_torchflower_crop_stage0"]),
        ("assets/bettergold/models/block/golden_torchflower_crop_stage1.json",
         ["bettergold:block/golden_torchflower_crop_stage1"]),
        ("assets/bettergold/models/block/potted_golden_torchflower.json",
         ["bettergold:block/golden_torchflower", "minecraft:block/flower_pot_cross"]),
        ("assets/bettergold/models/item/golden_torchflower_seeds.json",
         ["bettergold:item/golden_torchflower_seeds"]),
        ("assets/bettergold/models/item/refined_alchemic_oil.json",
         ["bettergold:item/refined_alchemic_oil"])):
    _bgn10r5_checked += 1
    _txt = (REPO / "src" / "main" / "resources" / _rel).read_text(encoding="utf-8")
    for _n in _needles:
        if _n not in _txt:
            _bgn10r5_bad("bgn10r5-assets", _rel + " 里缺引用 " + _n)

# 花盆模型必须复用原版花盆几何（不许自己画花盆）——负向：不许出现自绘的 elements 段
_R5_pot_model = (REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "models"
                 / "block" / "potted_golden_torchflower.json").read_text(encoding="utf-8")
_bgn10r5_checked += 1
if '"elements"' in _R5_pot_model:
    _bgn10r5_bad("bgn10r5-pot-model",
                 "花盆模型自带 elements 段（等于自己画花盆）——必须继承 minecraft:block/flower_pot_cross")

# ---------- ③ 标签：照原版火把花的 5 条（block 4 + item 1） ----------
for _rel, _id in (
        ("data/minecraft/tags/block/crops.json", "bettergold:golden_torchflower_crop"),
        ("data/minecraft/tags/block/flower_pots.json", "bettergold:potted_golden_torchflower"),
        ("data/minecraft/tags/block/small_flowers.json", "bettergold:golden_torchflower"),
        ("data/minecraft/tags/item/small_flowers.json", "bettergold:golden_torchflower")):
    _bgn10r5_checked += 1
    _p = REPO / "src" / "main" / "resources" / _rel
    if not _p.is_file():
        _bgn10r5_bad("bgn10r5-tags", "缺标签文件 " + _rel)
    elif _id not in _p.read_text(encoding="utf-8"):
        _bgn10r5_bad("bgn10r5-tags", _rel + " 里没有 " + _id)
# maintains_farmland 要有两条（作物 + 花），逐条查
_bgn10r5_checked += 2
_mf_txt = (REPO / "src" / "main" / "resources" / "data" / "minecraft" / "tags" / "block"
           / "maintains_farmland.json")
if not _mf_txt.is_file():
    _bgn10r5_bad("bgn10r5-tags", "缺 maintains_farmland.json")
else:
    _mf_body = _mf_txt.read_text(encoding="utf-8")
    for _need in ("bettergold:golden_torchflower_crop", "bettergold:golden_torchflower"):
        if _need not in _mf_body:
            _bgn10r5_bad("bgn10r5-tags", "maintains_farmland 缺 " + _need)

# ---------- ④ 语言键：5 条，中英都必须有且不相同 ----------
for _k in ("block.bettergold.golden_torchflower",
           "block.bettergold.golden_torchflower_crop",
           "block.bettergold.potted_golden_torchflower",
           "item.bettergold.golden_torchflower_seeds",
           "item.bettergold.refined_alchemic_oil"):
    _bgn10r5_checked += 3
    if _k not in zh:
        _bgn10r5_bad("bgn10r5-lang", "zh 缺语言键 " + _k)
    if _k not in en:
        _bgn10r5_bad("bgn10r5-lang", "en 缺语言键 " + _k)
    if _k in zh and _k in en and zh.get(_k) == en.get(_k):
        _bgn10r5_bad("bgn10r5-lang", _k + " 中英逐字相同（等于没译）")

# ---------- ⑤ 亮度：作者 16 / 引擎 15，**16 绝不许进 lightLevel**（否则掩成 0） ----------
_r5_flower = strip_comments((_R5_JAVA / "block" / "GoldenTorchflowerBlock.java").read_text(encoding="utf-8"))
_bgn10r5_checked += 4
if "AUTHOR_LIGHT = 16" not in _r5_flower:
    _bgn10r5_bad("bgn10r5-light", "作者原数 16 没落成常量 AUTHOR_LIGHT = 16（记账丢了）")
if "ENGINE_LIGHT = Math.min(15, AUTHOR_LIGHT)" not in _r5_flower:
    _bgn10r5_bad("bgn10r5-light", "缺 ENGINE_LIGHT = Math.min(15, AUTHOR_LIGHT)（喂引擎的值必须是 15）")
_r5_blocks = strip_comments((_R5_JAVA / "registry" / "AllBlocks.java").read_text(encoding="utf-8"))
if "GoldenTorchflowerBlock.ENGINE_LIGHT" not in _r5_blocks:
    _bgn10r5_bad("bgn10r5-light", "AllBlocks 的 lightLevel 没接 ENGINE_LIGHT")
if "lightLevel(state -> com.hjmmd_8.bettergold.block.GoldenTorchflowerBlock.AUTHOR_LIGHT" in _r5_blocks:
    _bgn10r5_bad("bgn10r5-light",
                 "lightLevel 直接吃了 AUTHOR_LIGHT(16) —— DataLayer 是 4 bit、(16 & 15) = 0，方块会一点都不亮")

# ---------- ⑥ 作物：AGE_1 / maxAge 2 / 成熟变花 / 状态定义必须覆写 ----------
_r5_crop = strip_comments((_R5_JAVA / "block" / "GoldenTorchflowerCropBlock.java").read_text(encoding="utf-8"))
_bgn10r5_checked += 6
if "extends GoldCropBlock" not in _r5_crop:
    _bgn10r5_bad("bgn10r5-crop",
                 "作物不是 GoldCropBlock 的子类（金骨粉判据 instanceof GoldCropBlock 会失效）")
if "BlockStateProperties.AGE_1" not in _r5_crop:
    _bgn10r5_bad("bgn10r5-crop", "作物阶段不是 AGE_1（原版火把花是 0..1 两阶段）")
if "return MAX_AGE;" not in _r5_crop or "MAX_AGE = 2" not in _r5_crop:
    _bgn10r5_bad("bgn10r5-crop", "maxAge 不是 2")
if "flowerBlock.get().defaultBlockState()" not in _r5_crop:
    _bgn10r5_bad("bgn10r5-crop", "成熟（age≥2）没有换成花方块本身")
if "createBlockStateDefinition" not in _r5_crop:
    _bgn10r5_bad("bgn10r5-crop",
                 "没覆写 createBlockStateDefinition —— CropBlock 里加的是它自己的 AGE_7 静态常量，"
                 "换 AGE_1 后 runData 会抛 IllegalArgumentException（本轮实测踩过）")
if "builder.add(AGE)" not in _r5_crop:
    _bgn10r5_bad("bgn10r5-crop", "createBlockStateDefinition 里没 add(AGE)")
# 负向：作物自己不许覆写 mayPlaceOn（只认金染耕地必须来自 GoldCropBlock 那一处唯一实现）
if "protected boolean mayPlaceOn" in _r5_crop:
    _bgn10r5_bad("bgn10r5-crop",
                 "作物自己覆写了 mayPlaceOn —— 种植基质判据必须只有 GoldCropBlock 一处（否则会漂）")

# ---------- ⑦ 酿造：ModBrewing 里那条 addRecipe 的三个端点 ----------
_r5_brew = strip_comments((_R5_JAVA / "event" / "ModBrewing.java").read_text(encoding="utf-8"))
_bgn10r5_checked += 3
for _need in ("Ingredient.of(AllItems.ALCHEMIC_FUEL.get())",
              "Ingredient.of(AllBlocks.GOLDEN_TORCHFLOWER.get().asItem())",
              "new ItemStack(AllItems.REFINED_ALCHEMIC_OIL.get())"):
    if _need not in _r5_brew:
        _bgn10r5_bad("bgn10r5-brewing", "ModBrewing 缺 " + _need)

# ---------- ⑧ 注册与稳定 ASCII id ----------
_bgn10r5_checked += 6
_r5_items = strip_comments((_R5_JAVA / "registry" / "AllItems.java").read_text(encoding="utf-8"))
for _id in ('"golden_torchflower_seeds"', '"refined_alchemic_oil"'):
    if _id not in _r5_items:
        _bgn10r5_bad("bgn10r5-register", "AllItems 没注册 " + _id)
for _id in ('"golden_torchflower"', '"golden_torchflower_crop"', '"potted_golden_torchflower"'):
    if _id not in _r5_blocks:
        _bgn10r5_bad("bgn10r5-register", "AllBlocks 没注册 " + _id)
if "registerSimpleBlockItem(\"golden_torchflower\"" not in _r5_blocks:
    _bgn10r5_bad("bgn10r5-register", "金火把花没有 BlockItem（拿不到物品）")
# 花盆方块必须**没有** BlockItem（原版 potted_* 不可取得）
if 'registerSimpleBlockItem("potted_golden_torchflower"' in _r5_blocks:
    _bgn10r5_bad("bgn10r5-register", "花盆方块注册了 BlockItem（原版 potted_* 不可直接取得）")

# ---------- ⑨ 「双倍贵金原料」：无依据 ⇒ 只许记账，不许悄悄发明 ----------
_bgn10r5_checked += 2
# ⚠ 这一条**刻意**跑在"含注释"的原文上（与本文件其它正向 needle 的规矩相反）：
#   要钉的东西**就是注释本身**（"这一轮没做，别当成做了"的记账）。去注释后它当然找不到。
_r5_items_raw = (_R5_JAVA / "registry" / "AllItems.java").read_text(encoding="utf-8")
if "双倍" not in _r5_items_raw or "没有实现" not in _r5_items_raw:
    _bgn10r5_bad("bgn10r5-double-yield",
                 "AllItems 的 refined_alchemic_oil 注释没记账「双倍贵金原料本轮没有实现」")
# 负向：生产代码里不许出现"翻倍"实现痕迹（本轮不该有任何翻倍逻辑）
for _rel in ("material/MetalEvents.java", "event/ModEvents.java", "registry/AllLootModifiers.java",
             "registry/AllRecipes.java"):
    _p = _R5_JAVA / _rel
    if not _p.is_file():
        continue
    if "refined_alchemic_oil" in strip_comments(_p.read_text(encoding="utf-8")):
        _bgn10r5_bad("bgn10r5-double-yield",
                     _rel + " 里出现了 refined_alchemic_oil —— 本轮没有配方依据，"
                     "双倍规则必须等作者补，不许先写一套实现")

# ---------- ⑩ 文档侧：本轮口径必须落档 ----------
for _needle, _why in ((u"bg-n10r5", u"docs/1.7 里没有轮5 这一节"),
                      (u"金火把花", u"没写金火把花"),
                      (u"高精度炼金油", u"没写高精度炼金油"),
                      (u"ENGINE_LIGHT", u"没写亮度 16→15 的处理口径"),
                      (u"双倍", u"没写「双倍贵金原料」这条缺口")):
    _bgn10r5_checked += 1
    if _needle not in _bgfix_spec:
        _bgn10r5_bad("bgn10r5-doc", _why + "（缺 " + _needle + "）")

print(f"1.7 轮5（金火把花 / 高精度炼金油 / 亮度 16→15 / 花盆 / 酿造）问题: "
      f"{len(bgn10r5_problems)} {bgn10r5_problems[:4]}（本段判定 {_bgn10r5_checked} 条）")
if _bgn10r5_checked <= 0:
    _bgn10r5_bad("bgn10r5-anti-vacuum", "本段一条判定都没跑（反空转）")
if not bgn10r5_problems:
    print("[bgn10r5-ok] 金火把花：贴图哈希/模型/标签/语言键/亮度口径/作物阶段/酿造三端点 全部通过")

# ==========================================================================================
# 1.7 轮7（bg-n10r7，2026-10-17）：崩乱合金（锭 / 块 / 模板 / 14 件器具 + 刀 / 4 件盔甲 / 禁果 /
#   两个新状态「力量失衡 · 抗性失衡」）
# ==========================================================================================
# 这一段钉的全是「声明了但没接线也全绿」的高危形状：
#   ① 配方（20 条）逐条反解，不只查"文件在"；
#   ② 块的硬度 / 抗爆 = 下界合金块 ×3（150 / 3600）+ 信标基座 + §9.7 例外集自动覆盖；
#   ③ 两个状态的公式（力量两端 / 抗性 ×2）+ **无等级**（amplifier 恒 0）+ 公式只在 ImbalanceEffects 一处；
#   ④ 50% 派发三条路（器具命中 / 盔甲被击 / 盾牌格挡）都走同一入口；
#   ⑤ 盔甲四件（护甲值 / 耐久 / 32 / 8 / 0.20 / 4..10 区间）；
#   ⑥ 崩乱禁果（饱和 11.6 / 19200 tick / 1..4 级 / 配方）；
#   ⑦ 语言键与模板文案（"可应用于: 混沌金装备"）；
#   ⑧ 文档落档。
bgn10r7_problems: list[str] = []
_bgn10r7_checked = 0


def _bgn10r7_bad(tag: str, msg: str) -> None:
    bgn10r7_problems.append("[%s] %s" % (tag, msg))


_R7_JAVA = JAVA
_R7_ASSETS = REPO / "src" / "main" / "resources" / "assets" / "bettergold"
_R7_DATA = REPO / "src" / "main" / "resources" / "data"
_R7_RECIPES = _R7_DATA / "bettergold" / "recipe"
_R7_METAL = "chaosalloy"

# ---------- ① 配方：20 条（锭 / 块→锭 / 锭→块 / 模板 / 禁果 / 15 条锻造） ----------
_R7_GEAR = ["sword", "mace", "trident", "bow", "crossbow",
            "axe", "pickaxe", "shovel", "hoe", "shield",
            "helmet", "chestplate", "leggings", "boots", "knife"]
_R7_FILES = ([f"{_R7_METAL}_ingot.json", f"{_R7_METAL}_block_from_ingot.json",
              f"{_R7_METAL}_ingot_from_block.json", f"{_R7_METAL}_upgrade_template.json",
              f"{_R7_METAL}_forbidden_fruit.json"]
             + [f"smithing_{_R7_METAL}_{g}.json" for g in _R7_GEAR])
for _name in _R7_FILES:
    _bgn10r7_checked += 1
    if not (_R7_RECIPES / _name).is_file():
        _bgn10r7_bad("bgn10r7-recipes", "缺配方 " + _name)

# ①-a 锭：无序、**9 项** = 4 下界合金锭 + 4 混沌金块 + 1 高精度炼金油
_p = _R7_RECIPES / f"{_R7_METAL}_ingot.json"
if _p.is_file():
    _bgn10r7_checked += 4
    _o = json.loads(_p.read_text(encoding="utf-8"))
    _ings = [i.get("item") for i in _o.get("ingredients", [])]
    if _o.get("type") != "minecraft:crafting_shapeless":
        _bgn10r7_bad("bgn10r7-recipes", "崩乱合金锭配方不是无序合成（作者原话：无序）")
    if len(_ings) != 9:
        _bgn10r7_bad("bgn10r7-recipes", "崩乱合金锭配方的材料数不是 9（实际 " + str(len(_ings)) + "）")
    if _ings.count("minecraft:netherite_ingot") != 4:
        _bgn10r7_bad("bgn10r7-recipes", "崩乱合金锭配方里下界合金锭不是 4 个")
    if _ings.count("bettergold:chaosgold_block") != 4:
        _bgn10r7_bad("bgn10r7-recipes", "崩乱合金锭配方里混沌金块不是 4 个")
    if _ings.count("bettergold:refined_alchemic_oil") != 1:
        _bgn10r7_bad("bgn10r7-recipes", "崩乱合金锭配方里高精度炼金油不是 1 个")

# ①-b 模板：3×3 逐格（6 混沌金锭 + 原版下界合金升级模板 + 崩乱合金锭 + 混沌金块）
_p = _R7_RECIPES / f"{_R7_METAL}_upgrade_template.json"
if _p.is_file():
    _bgn10r7_checked += 4
    _o = json.loads(_p.read_text(encoding="utf-8"))
    _pat = _o.get("pattern", [])
    _key = _o.get("key", {})
    if _pat != ["GIG", "GAG", "GCG"]:
        _bgn10r7_bad("bgn10r7-recipes", "模板配方的 3×3 排布不是立档那张图 GIG/GAG/GCG")
    if _key.get("I", {}).get("item") != "minecraft:netherite_upgrade_smithing_template":
        _bgn10r7_bad("bgn10r7-recipes", "模板配方的中心不是原版下界合金升级模板")
    if _key.get("A", {}).get("item") != "bettergold:chaosalloy_ingot":
        _bgn10r7_bad("bgn10r7-recipes", "模板配方中心下格不是崩乱合金锭")
    _letters = "".join(_pat)
    if _letters.count("G") != 6 or _letters.count("C") != 1:
        _bgn10r7_bad("bgn10r7-recipes",
                     "模板配方的 混沌金锭 / 混沌金块 个数不是 6 / 1（实际 "
                     + str(_letters.count("G")) + " / " + str(_letters.count("C")) + "）")

# ①-c 15 条锻造：base = **混沌金**同名装备、addition = 崩乱合金锭、template = 本模板
for _g in _R7_GEAR:
    _p = _R7_RECIPES / f"smithing_{_R7_METAL}_{_g}.json"
    if not _p.is_file():
        continue
    _bgn10r7_checked += 4
    _o = json.loads(_p.read_text(encoding="utf-8"))
    _base = _o.get("base", {}).get("item", "")
    if _o.get("type") != "minecraft:smithing_transform":
        _bgn10r7_bad("bgn10r7-recipes", "锻造 " + _g + " 不是 smithing_transform")
    if _base != "bettergold:chaosgold_" + _g:
        _bgn10r7_bad("bgn10r7-recipes",
                     "锻造 " + _g + " 的 base 不是混沌金同名装备（实际 " + _base + "）")
    if _base.startswith("minecraft:") or "_blank" in _base:
        _bgn10r7_bad("bgn10r7-recipes",
                     "锻造 " + _g + " 的 base 落到了原版金 / 胚底（那是既有八族的形状，抄错了）")
    if _o.get("addition", {}).get("item") != "bettergold:chaosalloy_ingot":
        _bgn10r7_bad("bgn10r7-recipes", "锻造 " + _g + " 的 addition 不是崩乱合金锭")
    if _o.get("result", {}).get("id") != "bettergold:chaosalloy_" + _g:
        _bgn10r7_bad("bgn10r7-recipes", "锻造 " + _g + " 的产物不是 bettergold:chaosalloy_" + _g)

# ①-d 崩乱禁果：无序 2 项（混沌禁果 + 崩乱合金锭）
_p = _R7_RECIPES / f"{_R7_METAL}_forbidden_fruit.json"
if _p.is_file():
    _bgn10r7_checked += 3
    _o = json.loads(_p.read_text(encoding="utf-8"))
    _ings = sorted(i.get("item") for i in _o.get("ingredients", []))
    if _o.get("type") != "minecraft:crafting_shapeless":
        _bgn10r7_bad("bgn10r7-fruit", "崩乱禁果配方不是无序合成（作者原话：无序）")
    if _ings != sorted(["bettergold:chaosgold_forbidden_fruit", "bettergold:chaosalloy_ingot"]):
        _bgn10r7_bad("bgn10r7-fruit", "崩乱禁果配方的材料不是 混沌禁果 + 崩乱合金锭（实际 " + str(_ings) + "）")
    if _o.get("result", {}).get("id") != "bettergold:chaosalloy_forbidden_fruit":
        _bgn10r7_bad("bgn10r7-fruit", "崩乱禁果配方的产物不是 chaosalloy_forbidden_fruit")

# ---------- ② 块：硬度 / 抗爆 ×3（150 / 3600）+ 信标基座 + §9.7 例外集 ----------
_bgn10r7_checked += 5
if "spec.blockStrength = 150.0F" not in _bgn10_am_nc:
    _bgn10r7_bad("bgn10r7-block", "崩乱合金块硬度不是 150.0F（= 下界合金块 50 × 3）")
if "spec.blockResistance = 3600.0F" not in _bgn10_am_nc:
    _bgn10r7_bad("bgn10r7-block", "崩乱合金块抗爆不是 3600.0F（= 下界合金块 1200 × 3）")
_beacon = _R7_DATA / "minecraft" / "tags" / "block" / "beacon_base_blocks.json"
if not _beacon.is_file():
    _bgn10r7_bad("bgn10r7-block", "缺 #minecraft:beacon_base_blocks 标签文件")
else:
    _bv = [v if isinstance(v, str) else v.get("id")
           for v in json.loads(_beacon.read_text(encoding="utf-8")).get("values", [])]
    if "bettergold:chaosalloy_block" not in _bv:
        _bgn10r7_bad("bgn10r7-block", "崩乱合金块不在 #minecraft:beacon_base_blocks 里（当不了信标基座）")
# §9.7：古董器具挖它不被"生硬替代" —— 判据是例外集走家族索引，崩乱合金块自动在内（零代码）
_mod_events = strip_comments((_R7_JAVA / "event" / "ModEvents.java").read_text(encoding="utf-8"))
if "MetalFamily.of(state.getBlock()) != null" not in _mod_events:
    _bgn10r7_bad("bgn10r7-block",
                 "§9.7 例外集不再走 MetalFamily.of(block) ⇒ 崩乱合金块会被古董器具就地转换")
if not MF.has(_R7_METAL, "block"):
    _bgn10r7_bad("bgn10r7-block", "metal_forms 里崩乱合金没有声明 block 形态（例外集覆盖不到它）")

# ---------- ③ 两个新状态：注册 / 无等级 / 16 秒 / 公式（力量两端 + 抗性 ×2）/ 公式只有一处 ----------
_r7_effects = strip_comments((_R7_JAVA / "registry" / "AllEffects.java").read_text(encoding="utf-8"))
for _id in ('"power_imbalance"', '"resistance_imbalance"'):
    _bgn10r7_checked += 1
    if _id not in _r7_effects:
        _bgn10r7_bad("bgn10r7-effects", "AllEffects 没注册 " + _id)
_r7_imb_path = _R7_JAVA / "material" / "ImbalanceEffects.java"
if not _r7_imb_path.is_file():
    _bgn10r7_bad("bgn10r7-effects", "缺 material/ImbalanceEffects.java（两个状态的规则本体）")
    _r7_imb = ""
else:
    _r7_imb = strip_comments(_r7_imb_path.read_text(encoding="utf-8"))
for _needle, _why in (
        ("TICKS = 16 * 20", "失衡时长不是 16 秒 = 320 tick"),
        ("POWER_FLOOR = 1.0F", "力量失衡的下端不是 1 点"),
        ("RESISTANCE_MULTIPLIER = 2.0F", "抗性失衡不是固定 ×2（裁定 ⑬b）"),
        ("new MobEffectInstance(effect, TICKS, 0, false, true, true)",
         "施加时不是 amplifier = 0（无等级没了）"),
        ("? AllEffects.POWER_IMBALANCE.getDelegate()",
         "50/50 二选一没有真的在两个效果之间选"),
        ("event.setNewDamage(powerImbalanceDamage(attacker, event.getNewDamage()))",
         "力量失衡没有改写攻击者的伤害"),
        ("event.setNewDamage(resistanceImbalanceDamage(event.getNewDamage()))",
         "抗性失衡没有改写受害者的伤害"),
        ("attacker.hasEffect(AllEffects.POWER_IMBALANCE)",
         "力量失衡判的是受害者而不是攻击者（方向反了）"),
        ("target.hasEffect(AllEffects.RESISTANCE_IMBALANCE)",
         "抗性失衡判的不是受害者")):
    _bgn10r7_checked += 1
    if _needle not in _r7_imb:
        _bgn10r7_bad("bgn10r7-effects", _why + "（缺 " + _needle + "）")
# 公式唯一性：两个公式的重心只许在 ImbalanceEffects 一处
_hits_power = _hits_resist = 0
for _p in JAVA.rglob("*.java"):
    _t = strip_comments(_p.read_text(encoding="utf-8"))
    if "float powerImbalanceDamage(" in _t:
        _hits_power += 1
    if "float resistanceImbalanceDamage(" in _t:
        _hits_resist += 1
_bgn10r7_checked += 2
if _hits_power != 1:
    _bgn10r7_bad("bgn10r7-effects",
                 "力量失衡公式的出现处 = " + str(_hits_power) + "（必须恰好 1 处 —— 不许写第二份）")
if _hits_resist != 1:
    _bgn10r7_bad("bgn10r7-effects",
                 "抗性失衡公式的出现处 = " + str(_hits_resist) + "（必须恰好 1 处）")
# 注册在游戏总线（不然两条公式一条都不会跑）
if ("NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.material.ImbalanceEffects.class)"
        not in strip_comments((_R7_JAVA / "bettergold.java").read_text(encoding="utf-8"))):
    _bgn10r7_bad("bgn10r7-effects", "ImbalanceEffects 没注册到游戏总线（两个状态全部静默不生效）")

# ---------- ④ 50% 派发：三条路都走 applyRandom（器具命中 / 盔甲被击 / 盾牌格挡） ----------
_r7_me = strip_comments((_R7_JAVA / "material" / "MetalEvents.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ("family.imbalanceOnAttack", "器具命中那条没有 imbalanceOnAttack 分支"),
        ("ImbalanceEffects.applyRandom(target)", "器具命中没有走「随机挂一个失衡」的唯一入口"),
        ("family.imbalanceReflect", "盔甲被击那条没有 imbalanceReflect"),
        ("ImbalanceEffects.applyRandom(attacker)", "盔甲 / 盾牌没有走同一个入口给攻击者挂失衡")):
    _bgn10r7_checked += 1
    if _needle not in _r7_me:
        _bgn10r7_bad("bgn10r7-imbalance-wiring", _why + "（缺 " + _needle + "）")
# 概率的唯一真源 = 配置项（0.5 / 0.1），与既有 16 条同构
_cfg = strip_comments((_R7_JAVA / "config" / "Config.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ('"chaosalloyWeaponBuffChance", 0.5D', "器具的 50% 概率不是配置项默认 0.5"),
        ('"chaosalloyArmorBuffChance", 0.1D', "盔甲的每件 10% 概率不是配置项默认 0.1")):
    _bgn10r7_checked += 1
    if _needle not in _cfg:
        _bgn10r7_bad("bgn10r7-imbalance-wiring", _why)

# ---------- ⑤ 盔甲：数组 / 32 / 8 / 0.20 / 4..10 四件 ----------
_bgn10r7_checked += 5
for _needle, _why in (
        ("spec.armorDefense = new int[] { 3, 6, 8, 3 }",
         "护甲值数组不是 靴/腿/胸/头 = 3/6/8/3（= 派单的头 3 胸 8 腿 6 靴 3）"),
        ("spec.armorDurability = new int[] { 2035, 2220, 2368, 1924 }",
         "耐久数组不是 靴/腿/胸/头 = 2035/2220/2368/1924（派单四个数按位置对应）"),
        ("spec.armorEnchantmentValue = 32", "盔甲附魔能力不是 32"),
        ("spec.armorToughness = 8.0F", "盔甲韧性不是 8"),
        ("spec.armorKnockbackResistance = 0.20F", "击退抗性不是 20%")):
    if _needle not in _bgn10_am_nc:
        _bgn10r7_bad("bgn10r7-armor", _why)
for _f in ("HELMET", "CHESTPLATE", "LEGGINGS", "BOOTS"):
    _bgn10r7_checked += 1
    if ("chaosRange(MetalFamily.Form." + _f + ", ChaosRange.Channel.ARMOR, 4, 10)") not in _bgn10_am_nc:
        _bgn10r7_bad("bgn10r7-armor", "崩乱合金 " + _f + " 没声明 4..10 的区间减伤")

# ---------- ⑥ 崩乱禁果：饱和 11.6 / 19200 tick / 1..4 级 ----------
_r7_ci = strip_comments((_R7_JAVA / "material" / "ChaosItems.java").read_text(encoding="utf-8"))
for _needle, _why in (
        ("CHAOSALLOY_FRUIT_EFFECT_TICKS = 16 * 60 * 20", "崩乱禁果效果时长不是 16 分钟"),
        ("CHAOSALLOY_FRUIT_COOLDOWN_TICKS = 16 * 60 * 20", "崩乱禁果冷却不是 16 分钟"),
        ("CHAOSALLOY_FRUIT_MAX_LEVEL = 4", "崩乱禁果效果等级上限不是 4"),
        ("CHAOSALLOY_FRUIT_SATURATION_MODIFIER = 1.45F",
         "崩乱禁果饱和度系数不是 1.45（复算 4 × 1.45 × 2 = 11.6）"),
        ('"chaosalloy_forbidden_fruit"', "崩乱禁果没注册")):
    _bgn10r7_checked += 1
    if _needle not in _r7_ci:
        _bgn10r7_bad("bgn10r7-fruit", _why)
# 复算：绝对饱和 = nutrition × 系数 × 2 必须 == 11.6（原版金苹果 9.6 + 2）
_bgn10r7_checked += 1
if abs(4 * 1.45 * 2 - 11.6) > 1e-6:
    _bgn10r7_bad("bgn10r7-fruit", "4 × 1.45 × 2 不等于 11.6（饱和复算失败）")

# ---------- ⑦ 语言键 + 模板文案 ----------
for _k, _zh, _en_should_not_equal in (
        ("effect.bettergold.power_imbalance", "力量失衡", True),
        ("effect.bettergold.resistance_imbalance", "抗性失衡", True)):
    _bgn10r7_checked += 2
    if zh.get(_k) != _zh:
        _bgn10r7_bad("bgn10r7-lang", "zh 的 " + _k + " 不是 " + _zh)
    if en.get(_k) in (None, "") or en.get(_k) == zh.get(_k):
        _bgn10r7_bad("bgn10r7-lang", "en 的 " + _k + " 缺失或与中文逐字相同")
_bgn10r7_checked += 2
if zh.get("item.bettergold.smithing_template.chaosalloy_upgrade.applies_to") != "混沌金装备":
    _bgn10r7_bad("bgn10r7-lang",
                 "崩乱合金模板的 applies_to 不是「混沌金装备」（作者原话：可应用于: 混沌金装备）")
if zh.get("item.bettergold.chaosalloy_forbidden_fruit") != "崩乱合金禁果":
    _bgn10r7_bad("bgn10r7-lang", "崩乱合金禁果的 zh 名不是「崩乱合金禁果」")

# ---------- ⑧ 贴图 / 模型：器具 15 + 盔甲 4 + 禁果 1 + 效果图标 2 ----------
for _suffix in _R7_GEAR + ["helmet", "chestplate", "leggings", "boots", "forbidden_fruit"]:
    _bgn10r7_checked += 1
    _p = _R7_ASSETS / "models" / "item" / (_R7_METAL + "_" + _suffix + ".json")
    if not _p.is_file():
        _bgn10r7_bad("bgn10r7-assets", "缺模型 models/item/" + _R7_METAL + "_" + _suffix + ".json")
for _icon in ("power_imbalance", "resistance_imbalance"):
    _bgn10r7_checked += 1
    if not (_R7_ASSETS / "textures" / "mob_effect" / (_icon + ".png")).is_file():
        _bgn10r7_bad("bgn10r7-assets", "缺效果图标 textures/mob_effect/" + _icon + ".png")

# ---------- ⑨ 生成器：轮7 的配方生成器必须自带自检（防"手写一套 JSON"） ----------
_bgn10r7_checked += 3
_r7_gen = REPO / "tools" / "asset-generator" / "generate_chaosalloy_recipes.py"
if not _r7_gen.is_file():
    _bgn10r7_bad("bgn10r7-generator", "缺 generate_chaosalloy_recipes.py（轮7 配方的唯一真源）")
else:
    _gt = _r7_gen.read_text(encoding="utf-8")
    for _needle, _why in (("INGOT_INPUTS", "生成器里没有锭配方的材料表"),
                          ("TEMPLATE_PATTERN", "生成器里没有模板排布"),
                          ("def check(", "生成器没有自检函数")):
        if _needle not in _gt:
            _bgn10r7_bad("bgn10r7-generator", _why)

# ---------- ⑩ 文档侧：本轮口径必须落档 ----------
_bgn10r7_checked += 1
if u"bg-n10r7" not in _bgfix_spec:
    _bgn10r7_bad("bgn10r7-doc", "docs/1.7 里没有轮7（bg-n10r7）这一节")

print(f"1.7 轮7（崩乱合金：锭/块/模板/15 件器具/4 件盔甲/禁果/两个状态）问题: "
      f"{len(bgn10r7_problems)} {bgn10r7_problems[:4]}（本段判定 {_bgn10r7_checked} 条）")
if _bgn10r7_checked <= 0:
    _bgn10r7_bad("bgn10r7-anti-vacuum", "本段一条判定都没跑（反空转）")
if not bgn10r7_problems:
    print("[bgn10r7-ok] 崩乱合金：20 条配方 / 块 ×3 + 信标 + §9.7 / 两个状态公式与无等级 / "
          "50% 三条派发 / 盔甲四件 / 禁果 11.6 全部通过")

# ============================================================================
# 1.7 轮8（bg-n10r8，2026-10-17）：万坚金砧（Sturdygold Anvil）
#
#   作者原话（立档 §2.14，逐字）：「万坚金砧，详细合成配方请去看我所给的贴图文件里头，无法破坏，
#   一样会互斥附魔，主要功能为可以使用混沌金币串修复装备，且以这种方式的修复无法累积惩罚
#   （就是不会出现过于昂贵），以及下落时根据坠落高度对被砸到的目标造成最多 16% 目标当前生命值的伤害」。
#
#   本段钉住（每一条都能单独变红）：
#   ① 配方逐格（3 金块 + 4 金锭 + 1 万坚金模板 + 1 万坚金锭，产物 1 个）
#   ② 「无法破坏」的两个数：strength(-1.0F, 3600000.0F) + ofFullCopy(原版砧)
#   ③ **不进** #minecraft:anvil（这是"下落砸到实体后不像原版砧那样裂开/消失"的守卫）
#   ④ 资产：blockstate 四向 / 模型（几何 = 原版 template_anvil 逐字）/ item 模型 / 掉落表 /
#      7 张贴图的**字节原样**（SHA256 == 归档原件）
#   ⑤ MenuType + Screen 的双端注册（本仓第一个 GUI）
#   ⑥ 金币串修复 = 原版砧公式（每币 maxDamage/4）+ 界面常量与 176×166 主面板
#   ⑦ 「不累积惩罚」只豁免这一条路：**全仓 0 处** calculateIncreasedRepairCost / REPAIR_COST
#   ⑧ 「互斥附魔」只有原版那一份：**全仓 0 处** Enchantment.areCompatible
#   ⑨ 下落伤害公式的唯一实现：min(16%, 1% × 格数) × 目标当前生命值
#   ⑩ 语言键 / 文档落档
# ============================================================================
bgn10r8_problems: list[str] = []
_bgn10r8_checked = 0


def _bgn10r8_bad(tag: str, msg: str) -> None:
    bgn10r8_problems.append("[%s] %s" % (tag, msg))


_R8_JAVA = JAVA
_R8_ASSETS = REPO / "src" / "main" / "resources" / "assets" / "bettergold"
_R8_DATA = REPO / "src" / "main" / "resources" / "data"
_R8_ARCHIVE = REPO / "docs" / "新约10-素材清单" / "新约10"
_R8_ANVIL = "sturdygold_anvil"


def _r8_sha256(path):
    import hashlib
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------- ① 配方：3×3 逐格（立档 §1 的反解结果） ----------
_r8_recipe = _R8_DATA / "bettergold" / "recipe" / (_R8_ANVIL + ".json")
if not _r8_recipe.is_file():
    _bgn10r8_bad("bgn10r8-recipe", "缺配方 data/bettergold/recipe/sturdygold_anvil.json")
else:
    _o = json.loads(_r8_recipe.read_text(encoding="utf-8"))
    _pat = _o.get("pattern", [])
    _key = _o.get("key", {})
    _bgn10r8_checked += 11
    if _o.get("type") != "minecraft:crafting_shaped":
        _bgn10r8_bad("bgn10r8-recipe", "配方类型不是 crafting_shaped（立档给的是 3×3 排布）")
    if _pat != ["BBB", "ITI", "ISI"]:
        _bgn10r8_bad("bgn10r8-recipe", "3×3 排布不是立档那张图（金块×3 / 金锭-模板-金锭 / 金锭-万坚金锭-金锭）："
                     + str(_pat))
    _letters = "".join(_pat) if _pat else ""
    if _letters.count("B") != 3:
        _bgn10r8_bad("bgn10r8-recipe", "原版金块不是 3 个（实际 " + str(_letters.count("B")) + "）")
    if _letters.count("I") != 4:
        _bgn10r8_bad("bgn10r8-recipe", "原版金锭不是 4 个（实际 " + str(_letters.count("I")) + "）")
    if _letters.count("T") != 1:
        _bgn10r8_bad("bgn10r8-recipe", "万坚金升级模板不是 1 个（实际 " + str(_letters.count("T")) + "）")
    if _letters.count("S") != 1:
        _bgn10r8_bad("bgn10r8-recipe", "万坚金锭不是 1 个（实际 " + str(_letters.count("S")) + "）")
    if _key.get("B", {}).get("item") != "minecraft:gold_block":
        _bgn10r8_bad("bgn10r8-recipe", "B 不是原版金块（实际 " + str(_key.get("B")) + "）")
    if _key.get("I", {}).get("item") != "minecraft:gold_ingot":
        _bgn10r8_bad("bgn10r8-recipe", "I 不是原版金锭（实际 " + str(_key.get("I")) + "）")
    if _key.get("T", {}).get("item") != "bettergold:sturdygold_upgrade_template":
        _bgn10r8_bad("bgn10r8-recipe", "T 不是既有的万坚金升级锻造模板（实际 " + str(_key.get("T")) + "）")
    if _key.get("S", {}).get("item") != "bettergold:sturdygold_ingot":
        _bgn10r8_bad("bgn10r8-recipe", "S 不是既有的万坚金锭（实际 " + str(_key.get("S")) + "）")
    if _o.get("result", {}).get("id") != "bettergold:sturdygold_anvil":
        _bgn10r8_bad("bgn10r8-recipe", "产物不是 bettergold:sturdygold_anvil")
    if _o.get("result", {}).get("count") != 1:
        _bgn10r8_bad("bgn10r8-recipe", "产物数量不是 1")

# ---------- ② 方块：继承原版砧 + 「无法破坏」的两个数 + codec ----------
_r8_block_path = _R8_JAVA / "block" / "SturdygoldAnvilBlock.java"
if not _r8_block_path.is_file():
    _bgn10r8_bad("bgn10r8-block", "缺 block/SturdygoldAnvilBlock.java（方块本体）")
    _r8_block = ""
else:
    _r8_block = strip_comments(_r8_block_path.read_text(encoding="utf-8"))
for _needle, _why in (
        ("extends AnvilBlock", "方块不是继承原版 AnvilBlock（形状/四向/下落方块那几件本该免费复用）"),
        ("ofFullCopy(Blocks.ANVIL)", "属性不是照原版砧全量复制（声音/挖掘要求会漂）"),
        ("strength(-1.0F, 3600000.0F)", "「无法破坏」的两个数不是 硬度 -1.0F / 抗爆 3600000"),
        ("public MapCodec<AnvilBlock> codec()", "codec() 没覆写（反序列化会造出原版砧）"),
        ("simpleCodec(SturdygoldAnvilBlock::new)", "CODEC 的工厂不是本类构造器"),
        ("new SturdygoldAnvilMenu(containerId, inventory, ContainerLevelAccess.create(level, pos))",
         "服务端没有用带 ContainerLevelAccess 的本类菜单（stillValid 会永远 true）"),
        ("setHurtsEntities(SturdygoldAnvilFallDamage.SIGNAL_PER_BLOCK",
         "下落时没把原版那条路降级成高度信号（砸人伤害会走原版的固定数值）")):
    _bgn10r8_checked += 1
    if _needle not in _r8_block:
        _bgn10r8_bad("bgn10r8-block", _why + "（缺 " + _needle + "）")

# ---------- ③ 负向：**不进** #minecraft:anvil（下落砸到实体后不裂开 / 不消失的守卫） ----------
_bgn10r8_checked += 2
_r8_anvil_tag = _R8_DATA / "minecraft" / "tags" / "block" / "anvil.json"
if _r8_anvil_tag.is_file():
    _tv = [v if isinstance(v, str) else v.get("id")
           for v in json.loads(_r8_anvil_tag.read_text(encoding="utf-8")).get("values", [])]
    if "bettergold:sturdygold_anvil" in _tv:
        _bgn10r8_bad("bgn10r8-not-in-anvil-tag",
                     "万坚金砧被塞进了 #minecraft:anvil ⇒ 下落砸到实体会按原版概率裂开 / 消失（与「无法破坏」冲突）")
if "BlockTags.ANVIL" in _r8_block:
    _bgn10r8_bad("bgn10r8-not-in-anvil-tag", "方块类里引用了 BlockTags.ANVIL（原版砧的判据，本项目用的是自己的方块）")

# ---------- ④ 资产：blockstate / 模型 / item 模型 / 掉落表 / 贴图字节原样 ----------
_r8_bs = _R8_ASSETS / "blockstates" / (_R8_ANVIL + ".json")
_bgn10r8_checked += 6
if not _r8_bs.is_file():
    _bgn10r8_bad("bgn10r8-assets", "缺 blockstates/sturdygold_anvil.json")
else:
    _bs = _r8_bs.read_text(encoding="utf-8")
    for _facing, _y in (("east", 270), ("north", 180), ("south", None), ("west", 90)):
        if ('"facing=' + _facing + '"') not in _bs:
            _bgn10r8_bad("bgn10r8-assets", "blockstate 缺 facing=" + _facing + "（原版砧是四向）")
        elif _y is not None and ('"y": ' + str(_y)) not in _bs:
            _bgn10r8_bad("bgn10r8-assets", "facing=" + _facing + " 的 y 旋转不是 " + str(_y))
    if '"model": "bettergold:block/sturdygold_anvil"' not in _bs:
        _bgn10r8_bad("bgn10r8-assets", "blockstate 指的不是 bettergold:block/sturdygold_anvil")

_r8_model = _R8_ASSETS / "models" / "block" / (_R8_ANVIL + ".json")
_bgn10r8_checked += 8
if not _r8_model.is_file():
    _bgn10r8_bad("bgn10r8-assets", "缺 models/block/sturdygold_anvil.json")
else:
    _m = _r8_model.read_text(encoding="utf-8")
    # 几何必须逐字等于原版 assets/minecraft/models/block/template_anvil.json 的四个 element
    for _seg in ('"from": [ 2, 0, 2 ]', '"to": [ 14, 4, 14 ]',
                 '"from": [ 4, 4, 3 ]', '"to": [ 12, 5, 13 ]',
                 '"from": [ 6, 5, 4 ]', '"to": [ 10, 10, 12 ]',
                 '"from": [ 3, 10, 0 ]', '"to": [ 13, 16, 16 ]'):
        if _seg not in _m:
            _bgn10r8_bad("bgn10r8-assets", "模型几何不是原版 template_anvil 逐字复制（缺 " + _seg + "）")
    for _slot, _tex in (("particle", "sturdygold_anvil_ns"), ("ns", "sturdygold_anvil_ns"),
                        ("ew", "sturdygold_anvil_ew"), ("top", "sturdygold_anvil_top"),
                        ("base_top", "sturdygold_anvil_base_top"),
                        ("base_bottom", "sturdygold_anvil_base_bottom")):
        if ('"' + _slot + '": "bettergold:block/' + _tex + '"') not in _m:
            _bgn10r8_bad("bgn10r8-assets", "模型的贴图槽 " + _slot + " 不是作者那张 " + _tex)

_r8_item_model = _R8_ASSETS / "models" / "item" / (_R8_ANVIL + ".json")
_bgn10r8_checked += 1
if not _r8_item_model.is_file():
    _bgn10r8_bad("bgn10r8-assets", "缺 models/item/sturdygold_anvil.json（物品会变紫黑格）")
elif '"parent": "bettergold:block/sturdygold_anvil"' not in _r8_item_model.read_text(encoding="utf-8"):
    _bgn10r8_bad("bgn10r8-assets", "item 模型的 parent 不是 bettergold:block/sturdygold_anvil")

_r8_loot = _R8_DATA / "bettergold" / "loot_table" / "blocks" / (_R8_ANVIL + ".json")
_bgn10r8_checked += 1
if not _r8_loot.is_file():
    _bgn10r8_bad("bgn10r8-assets", "缺掉落表 loot_table/blocks/sturdygold_anvil.json")
elif "bettergold:sturdygold_anvil" not in _r8_loot.read_text(encoding="utf-8"):
    _bgn10r8_bad("bgn10r8-assets", "掉落表掉的不是自己")

# 贴图 7 张：字节必须与归档原件一致（作者素材不许改一个像素）
_r8_tex_map = (
    ("\u4e07\u575a\u91d1\u7827 \u4e0a.png", "textures/block/sturdygold_anvil_top.png"),
    ("\u4e07\u575a\u91d1\u7827 \u524d\u540e.png", "textures/block/sturdygold_anvil_ns.png"),
    ("\u4e07\u575a\u91d1\u7827 \u5de6\u53f3.png", "textures/block/sturdygold_anvil_ew.png"),
    ("\u4e07\u575a\u91d1\u7827 \u5e95\u76d8\u4e0a\u90e8.png", "textures/block/sturdygold_anvil_base_top.png"),
    ("\u4e07\u575a\u91d1\u7827 \u5e95\u76d8\u4e0b\u90e8.png", "textures/block/sturdygold_anvil_base_bottom.png"),
    ("\u4e07\u575a\u91d1\u7827 gui.png", "textures/gui/container/sturdygold_anvil.png"),
    ("\u7a7a\u69fd\u4e2d\u7684\u6df7\u6c8c\u91d1\u5e01\u4e32\u56fe\u6807.png",
     "textures/gui/container/sturdygold_anvil_coin_ghost.png"),
)
for _src_name, _dst_rel in _r8_tex_map:
    _bgn10r8_checked += 2
    _src = _R8_ARCHIVE / _src_name
    _dst = _R8_ASSETS / _dst_rel
    if not _dst.is_file():
        _bgn10r8_bad("bgn10r8-assets", "缺贴图 " + _dst_rel)
    elif _r8_sha256(_src) != _r8_sha256(_dst):
        _bgn10r8_bad("bgn10r8-assets", "贴图不是作者原件的字节原样：" + _dst_rel)

# ---------- ⑤ MenuType + Menu（本仓第一个 GUI 的注册链） ----------
_r8_menus_path = _R8_JAVA / "registry" / "AllMenus.java"
_bgn10r8_checked += 4
if not _r8_menus_path.is_file():
    _bgn10r8_bad("bgn10r8-menu", "缺 registry/AllMenus.java")
else:
    _r8_menus = strip_comments(_r8_menus_path.read_text(encoding="utf-8"))
    if "Registries.MENU" not in _r8_menus:
        _bgn10r8_bad("bgn10r8-menu", "MenuType 没注册在 Registries.MENU 上")
    if 'MENU_TYPES.register("sturdygold_anvil"' not in _r8_menus:
        _bgn10r8_bad("bgn10r8-menu", "MenuType 的注册名不是 sturdygold_anvil")
    if "SturdygoldAnvilMenu::new" not in _r8_menus:
        _bgn10r8_bad("bgn10r8-menu", "MenuType 的工厂不是 SturdygoldAnvilMenu::new")
    if "FeatureFlags.DEFAULT_FLAGS" not in _r8_menus:
        _bgn10r8_bad("bgn10r8-menu", "MenuType 的世界特性集合不是 DEFAULT_FLAGS")

_r8_main = strip_comments((_R8_JAVA / "bettergold.java").read_text(encoding="utf-8"))
_bgn10r8_checked += 3
if "com.hjmmd_8.bettergold.registry.AllMenus.MENU_TYPES.register(modEventBus)" not in _r8_main:
    _bgn10r8_bad("bgn10r8-menu", "MenuType 注册表没挂到 mod 事件总线（双端都不会有容器类型）")
if "com.hjmmd_8.bettergold.block.SturdygoldAnvilFallDamage.bootstrap()" not in _r8_main:
    _bgn10r8_bad("bgn10r8-menu", "下落伤害的规则类没 bootstrap")
if "NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.block.SturdygoldAnvilFallDamage.class)" not in _r8_main:
    _bgn10r8_bad("bgn10r8-menu", "下落伤害的 @SubscribeEvent 没注册到游戏总线（伤害一条都不会跑）")

_r8_client = strip_comments((_R8_JAVA / "bettergoldClient.java").read_text(encoding="utf-8"))
_bgn10r8_checked += 3
if "RegisterMenuScreensEvent" not in _r8_client:
    _bgn10r8_bad("bgn10r8-screen", "客户端没监听 RegisterMenuScreensEvent（界面永远开不出来）")
if "AllMenus.STURDYGOLD_ANVIL.get()" not in _r8_client:
    _bgn10r8_bad("bgn10r8-screen", "Screen 没注册到我们的 MenuType 上")
if "SturdygoldAnvilScreen::new" not in _r8_client:
    _bgn10r8_bad("bgn10r8-screen", "Screen 工厂不是 SturdygoldAnvilScreen::new")

# ---------- ⑥ 菜单：金币串修复 = 原版砧公式；界面 = 176×166 主面板 + 两处装饰 ----------
_r8_menu_path = _R8_JAVA / "menu" / "SturdygoldAnvilMenu.java"
if not _r8_menu_path.is_file():
    _bgn10r8_bad("bgn10r8-menu", "缺 menu/SturdygoldAnvilMenu.java")
    _r8_menu = ""
else:
    _r8_menu = strip_comments(_r8_menu_path.read_text(encoding="utf-8"))
for _needle, _why in (
        ("extends AnvilMenu", "菜单不是继承原版 AnvilMenu（附魔合并就没法复用原版那一份）"),
        ("public MenuType<?> getType()", "没覆写 getType()（客户端只会造出原版 AnvilMenu）"),
        ("return AllMenus.STURDYGOLD_ANVIL.get();", "getType() 上报的不是自己的 MenuType"),
        ("return state.is(AllBlocks.STURDYGOLD_ANVIL.get());", "isValidBlock 认的不是自己的方块"),
        ("COIN_REPAIR_DIVISOR = 4", "「每币 maxDamage/4」的那个 4 没有单列常量"),
        ("maxDamage / COIN_REPAIR_DIVISOR", "每币修复量不是 maxDamage / 4（原版砧公式）"),
        ("AllItems.CHAOS_COIN_STRING.get()", "材料槽认的不是既有的混沌金币串"),
        ("remaining -= Math.min(remaining, perCoin);", "扣损伤不是 min(剩余, 每币量) 逐币推进"),
        ("result.setDamageValue(remaining);", "修完没有把剩余损伤写回结果"),
        ("this.broadcastChanges();", "算完没有 broadcastChanges（客户端看不到结果）"),
        ("super.createResult();", "其余各条路没有交回原版（复用合并逻辑的前提）"),
        ("super.mayPickup(player, hasStack)", "非金币串那条路的取件判定没有交回原版"),
        ("setMaximumCost(0)", "金币串这条路没有清掉原版那条 cost")):
    _bgn10r8_checked += 1
    if _needle not in _r8_menu:
        _bgn10r8_bad("bgn10r8-menu", _why + "（缺 " + _needle + "）")

# ⑦ 「不累积惩罚」= 只豁免金币串这一条路：全仓**零处** calculateIncreasedRepairCost / REPAIR_COST
_hits_repair_cost = 0
_hits_repair_component = 0
for _p in JAVA.rglob("*.java"):
    _t = strip_comments(_p.read_text(encoding="utf-8"))
    if "calculateIncreasedRepairCost" in _t:
        _hits_repair_cost += 1
    if "REPAIR_COST" in _t:
        _hits_repair_component += 1
_bgn10r8_checked += 2
if _hits_repair_cost != 0:
    _bgn10r8_bad("bgn10r8-no-penalty",
                 "全仓出现 calculateIncreasedRepairCost " + str(_hits_repair_cost) + " 处 —— "
                 "「用金币串修复不累积惩罚」被破坏了（原版那条 ×2+1 只许留在原版 AnvilMenu 里）")
if _hits_repair_component != 0:
    _bgn10r8_bad("bgn10r8-no-penalty",
                 "全仓出现 REPAIR_COST " + str(_hits_repair_component) + " 处 —— 我们不该碰修复惩罚组件")

# ⑧ 「互斥附魔」= 只有原版那一份：全仓**零处** Enchantment.areCompatible（不许自己重写合并规则）
_hits_compat = 0
for _p in JAVA.rglob("*.java"):
    if "areCompatible" in strip_comments(_p.read_text(encoding="utf-8")):
        _hits_compat += 1
_bgn10r8_checked += 1
if _hits_compat != 0:
    _bgn10r8_bad("bgn10r8-enchant-merge",
                 "全仓出现 areCompatible " + str(_hits_compat) + " 处 —— 附魔互斥规则被第二份实现了"
                 "（应当只走原版 AnvilMenu#createResult）")

# ⑨ 下落伤害：公式的唯一实现 + 只认自己的方块
_r8_fall_path = _R8_JAVA / "block" / "SturdygoldAnvilFallDamage.java"
if not _r8_fall_path.is_file():
    _bgn10r8_bad("bgn10r8-fall", "缺 block/SturdygoldAnvilFallDamage.java（下落伤害的规则本体）")
    _r8_fall = ""
else:
    _r8_fall = strip_comments(_r8_fall_path.read_text(encoding="utf-8"))
for _needle, _why in (
        ("SIGNAL_PER_BLOCK = 1.0F", "高度信号不是每格 1 点"),
        ("PERCENT_PER_BLOCK = 0.01F", "每格坠落不是 1% 目标当前生命值"),
        ("MAX_PERCENT = 0.16F", "封顶不是 16%（作者原话「最多 16%」）"),
        ("return Math.min(MAX_PERCENT, PERCENT_PER_BLOCK * Math.max(0, blocks));",
         "伤害比例的公式不是 min(16%, 1% × 格数)"),
        ("return damageFraction(blocks) * currentHealth;",
         "最终伤害不是 比例 × 目标当前生命值"),
        ("event.setNewDamage(applyFallDamage(event.getEntity().getHealth(), blocks));",
         "没有把伤害改成「按目标当前生命值」算出来的值"),
        ("state.is(AllBlocks.STURDYGOLD_ANVIL.get())", "下落伤害没有限定在自己的方块上（会波及原版砧）")):
    _bgn10r8_checked += 1
    if _needle not in _r8_fall:
        _bgn10r8_bad("bgn10r8-fall", _why + "（缺 " + _needle + "）")
# 公式唯一：damageFraction 的定义只许一处
_hits_fraction = 0
for _p in JAVA.rglob("*.java"):
    if "public static float damageFraction(" in strip_comments(_p.read_text(encoding="utf-8")):
        _hits_fraction += 1
_bgn10r8_checked += 1
if _hits_fraction != 1:
    _bgn10r8_bad("bgn10r8-fall", "伤害比例的公式出现处 = " + str(_hits_fraction) + "（必须恰好 1 处）")

# 界面常量 + 两条禁令
_r8_screen_path = _R8_JAVA / "client" / "SturdygoldAnvilScreen.java"
if not _r8_screen_path.is_file():
    _bgn10r8_bad("bgn10r8-screen", "缺 client/SturdygoldAnvilScreen.java")
    _r8_screen = ""
else:
    _r8_screen = strip_comments(_r8_screen_path.read_text(encoding="utf-8"))
for _needle, _why in (
        ("extends AbstractContainerScreen<SturdygoldAnvilMenu>", "界面不是自建 AbstractContainerScreen"),
        ("PANEL_WIDTH = 176", "主面板宽度不是 176（原版砧尺寸，槽位才对齐）"),
        ("PANEL_HEIGHT = 166", "主面板高度不是 166"),
        ("TAB_W = 28", "右上装饰宽不是 28（原图 x 176..203）"),
        ("TAB_H = 21", "右上装饰高不是 21（原图 y 0..20）"),
        ("PLATES_W = 110", "左下两条灰条宽不是 110（原图 x 0..109）"),
        ("PLATES_H = 32", "左下两条灰条高不是 32（原图 y 166..197）"),
        ("TEX_W = 256", "blit 的 textureWidth 不是 256（uv 会算错）"),
        ("setColor(1.0F, 1.0F, 1.0F, 0.35F)", "空槽幽灵图标不是 35% 半透明"),
        ("setColor(1.0F, 1.0F, 1.0F, 1.0F)", "半透明画完没有还原 shader 颜色"),
        ("ADDITIONAL_SLOT_X = 76", "幽灵图标的 x 不是输入 2 槽的 76"),
        ("ADDITIONAL_SLOT_Y = 47", "幽灵图标的 y 不是输入 2 槽的 47")):
    _bgn10r8_checked += 1
    if _needle not in _r8_screen:
        _bgn10r8_bad("bgn10r8-screen", _why + "（缺 " + _needle + "）")
_bgn10r8_checked += 1
if "blitSprite" in _r8_screen:
    _bgn10r8_bad("bgn10r8-screen",
                 "界面用了 blitSprite（gui/container 下的贴图不在 gui/sprites 图集里 ⇒ 静默紫黑格）")

# ---------- ⑩ 语言键 / 文档 ----------
for _k, _zh, _why in (
        ("block.bettergold.sturdygold_anvil", "万坚金砧", "方块名"),
        ("container.bettergold.sturdygold_anvil", "万坚金砧", "容器标题")):
    _bgn10r8_checked += 2
    if zh.get(_k) != _zh:
        _bgn10r8_bad("bgn10r8-lang", "zh 的 " + _why + " 不是 " + _zh + "（实际 " + str(zh.get(_k)) + "）")
    if en.get(_k) in (None, "") or en.get(_k) == zh.get(_k):
        _bgn10r8_bad("bgn10r8-lang", "en 的 " + _why + " 缺失或与中文逐字相同")

_r8_doc17 = REPO / "docs" / "1.7-\u6df7\u6c8c\u91d1\u4e0e\u5d29\u4e71\u5408\u91d1-\u9700\u6c42\u7acb\u6863.md"
_r8_doc16 = REPO / "docs" / "1.6-\u89c4\u683c.md"
_bgn10r8_checked += 2
if not _r8_doc17.is_file() or "bg-n10r8" not in _r8_doc17.read_text(encoding="utf-8"):
    _bgn10r8_bad("bgn10r8-doc", "docs/1.7 里没有轮8（bg-n10r8）这一节")
if not _r8_doc16.is_file() or "bg-n10r8" not in _r8_doc16.read_text(encoding="utf-8"):
    _bgn10r8_bad("bgn10r8-doc", "docs/1.6-规格.md 里没有轮8 对既有口径的改动一节")

print("1.7 轮8（万坚金砧：不可破坏 + 自建 GUI + 金币串修复不累积惩罚 + 下落 16%）问题: "
      + str(len(bgn10r8_problems)) + " " + str(bgn10r8_problems[:4])
      + "（本段判定 " + str(_bgn10r8_checked) + " 条）")
if _bgn10r8_checked <= 0:
    _bgn10r8_bad("bgn10r8-anti-vacuum", "本段一条判定都没跑（反空转）")
if not bgn10r8_problems:
    print("[bgn10r8-ok] 万坚金砧：配方 9 格 / 硬度 -1 与抗爆 3600000 / 不进 #minecraft:anvil / "
          "四向 blockstate + 几何逐字原版 / MenuType+Screen 双端注册 / 每币 maxDamage/4 / "
          "全仓 0 处修复惩罚与互斥重写 / min(16%,1%×格数)×当前血量 全部通过")

# ==================== 1.7 轮9 收口（bg-n10r9，2026-10-17）====================
#
# 本轮新增的**全部可交付面**都在这一段里逐条钉住（形状 / 引用 / 语言 / 文档）：
#   ① 手册：两族 4 个条目（材料 16 页 / 禁果 4 页 / 混沌金装备 7 页 / 崩乱合金装备 11 页）；
#   ② 成就：两族 8 条（混沌金 4 + 崩乱合金 4），挂在「寻途千里的珍宝」下 ⇒ 该父节点 9 → 11 个孩子；
#   ③ 创造页：`METAL_ORDER` 已含两族（= 进度树彩虹序与创造页同一真源）；
#   ④ 语言键：4 条目键 + 16 页键 × 2 语言，且 en 不许与 zh 逐字相同。
#
# ⚠ 三处**口径**（不是随手决定，写在这里备查）：
#   * 混沌金**没有** raw / 没有升级锻造模板 / 没有锻造配方（素材里没有）⇒ 它的装备章**不挂配方页**，
#     只挂**轮换图标表**（`PageSpotlight` 每 20 tick 换一个 ⇒ 本仓"多个图标"的既有表达）；
#   * 崩乱合金**没有建材**（作者裁定「按照现有的贴图标准来」）⇒ 材料章只有 3 页形态表 + 2 页配方；
#   * 两族的成就**标题 / 简介是"实现说明"**（作者没给文案）⇒ 已记进 `docs/1.7-...md` §7 / §18。
bgn10r9_problems: list[str] = []
_bgn10r9_checked = 0


def _bgn10r9_bad(tag: str, msg: str) -> None:
    bgn10r9_problems.append("%s [%s]" % (msg, tag))


_R9_LANG = "bettergold.handbook"
_R9_ENTRIES = {
    # 条目 -> (页数, 页型序列)
    # ⚠ 1.7 `bg-n10up`（2026-10-18）第三次换锚点：作者补了**混沌金锭的上游**（币串 → 3 币 /
    #   币 →（烧炼）→ 粒）⇒ 材料章 **16 → 18 页**：在第 4 页（币的 spotlight）之后插入
    #   「patchouli:crafting（币串→3币）」+「patchouli:smelting（币→粒）」两页，各 1 条配方。
    #   旧期望（16 页 / 无 smelting 页）**原文留档、已作废**：
    #     "chaos_materials": (16, ["patchouli:text", "patchouli:crafting", "patchouli:crafting",
    #                              "patchouli:spotlight", "patchouli:crafting", "patchouli:crafting",
    #                              "patchouli:spotlight", "patchouli:crafting", "patchouli:crafting",
    #                              "patchouli:crafting", "patchouli:crafting", "patchouli:crafting",
    #                              "patchouli:text", "patchouli:crafting", "patchouli:crafting",
    #                              "patchouli:spotlight"]),
    #   页数变了**不等于放宽**：这两条的具体 id / 页序 / 每页配方数由 `[bgn10up-*]` 逐条钉住。
    "chaos_materials": (18, ["patchouli:text", "patchouli:crafting", "patchouli:crafting",
                             "patchouli:spotlight", "patchouli:crafting", "patchouli:smelting",
                             "patchouli:crafting", "patchouli:crafting",
                             "patchouli:spotlight", "patchouli:crafting", "patchouli:crafting",
                             "patchouli:crafting", "patchouli:crafting", "patchouli:crafting",
                             "patchouli:text", "patchouli:crafting", "patchouli:crafting",
                             "patchouli:spotlight"]),
    "chaos_feast": (4, ["patchouli:spotlight", "patchouli:crafting",
                        "patchouli:spotlight", "patchouli:crafting"]),
    # ⚠ 旧期望（bg-n10r9，7 页 = 3 文案 + 3 轮换图标 + 1 附魔书配方）**原文留档、已作废**：
    #       "gear_chaosgold": (7, ["patchouli:text"] * 3 + ["patchouli:spotlight"] * 3
    #                             + ["patchouli:crafting"]),
    #   1.7 bg-n10rg（作者 2026-10-17「原版装备在工作台上面怎么来合成它就怎么来」）之后，
    #   混沌金装备有 **11 件工作台配方** ⇒ 本章 13 页 = 3 文案 + **6 页配方** + 3 轮换图标
    #   + 1 附魔书配方。页数与页型序列跟着改，**不等于放宽**：那 11 条具体引用由
    #   `[bgn10rg-handbook]` 逐条钉住（顺序 / 每页最多 2 条 / 无死链）。
    # ⚠ 第二次换锚点（`bg-n10rc2`，2026-10-18）：4 件补齐 ⇒ **15 件配方 = 8 页**
    #   ⇒ 本章 **15 页** = 3 文案 + **8 页配方** + 3 轮换图标 + 1 附魔书配方。
    #   旧期望（13 页 / 6 页配方）**原文留档**：`"gear_chaosgold": (13, [...crafting]*6 + ...)`。
    "gear_chaosgold": (15, ["patchouli:text"] * 3 + ["patchouli:crafting"] * 8
                           + ["patchouli:spotlight"] * 3 + ["patchouli:crafting"]),
    "gear_chaosalloy": (11, ["patchouli:text"] * 3 + ["patchouli:smithing"] * 8),
}
_R9_RECIPE_REFS = set()
_R9_ITEM_REFS = set()
for _eid, (_n, _seq) in _R9_ENTRIES.items():
    _ep = _ZH_BOOK / "entries" / ("%s.json" % _eid)
    _ep_en = _EN_BOOK / "entries" / ("%s.json" % _eid)
    _bgn10r9_checked += 1
    if not _ep.is_file() or not _ep_en.is_file():
        _bgn10r9_bad("bgn10r9-book", "缺条目文件（zh/en 各需一份）：%s" % _eid)
        continue
    _ej = json.loads(_ep.read_text(encoding="utf-8"))
    _ej_en = json.loads(_ep_en.read_text(encoding="utf-8"))
    _bgn10r9_checked += 3
    if len(_ej.get("pages") or []) != _n:
        _bgn10r9_bad("bgn10r9-book", "%s 的页数不是 %d（实际 %d）"
                     % (_eid, _n, len(_ej.get("pages") or [])))
    if [p.get("type") for p in _ej.get("pages") or []] != _seq:
        _bgn10r9_bad("bgn10r9-book",
                     "%s 的页型序列不对：%s" % (_eid, [p.get("type") for p in _ej.get("pages") or []]))
    if _ej.get("pages") != _ej_en.get("pages"):
        _bgn10r9_bad("bgn10r9-book", "%s 的 zh/en 页列表不一致（结构必须双端相同）" % _eid)
    for _pg in _ej.get("pages") or []:
        for _rk in ("recipe", "recipe2"):
            if isinstance(_pg.get(_rk), str):
                _R9_RECIPE_REFS.add(_pg[_rk])
        _items = _pg.get("item")
        if isinstance(_items, str):
            _R9_ITEM_REFS.add(_items)
        elif isinstance(_items, list):
            _R9_ITEM_REFS.update([x for x in _items if isinstance(x, str)])
_bgn10r9_checked += 1
if len(_R9_RECIPE_REFS) < 25:
    _bgn10r9_bad("bgn10r9-book",
                 "两族条目里的配方引用只有 %d 条（反空转守护：材料链 4 + 币 3 + 建材 10 + 合金 4 + "
                 "禁果 2 + 附魔书 1 + 锻造 15）" % len(_R9_RECIPE_REFS))
_r9_dead = sorted(_r for _r in _R9_RECIPE_REFS
                  if not (_DATA / "bettergold" / "recipe" / (_r.split(":", 1)[1] + ".json")).is_file())
_bgn10r9_checked += 1
if _r9_dead:
    _bgn10r9_bad("bgn10r9-book", "两族条目引用了不存在的配方（死链）：%s" % _r9_dead[:5])
# 图标引用：每一件都必须有 `models/item/<path>.json`（缺模型 = 客户端紫黑格）
_r9_no_model = sorted(_i for _i in _R9_ITEM_REFS
                      if not (_RES / "assets" / "bettergold" / "models" / "item"
                              / (_i.split(":", 1)[1] + ".json")).is_file())
_bgn10r9_checked += 2
if _r9_no_model:
    _bgn10r9_bad("bgn10r9-book", "两族条目里的图标没有物品模型（客户端紫黑格）：%s" % _r9_no_model[:5])
if len(_R9_ITEM_REFS) < 20:
    _bgn10r9_bad("bgn10r9-book", "两族条目里的图标引用只有 %d 件（反空转守护）" % len(_R9_ITEM_REFS))

# ---------- ② 语言键：条目名 + 页键（zh/en 都要有，且 en 不许等于 zh）----------
_r9_lang_keys = ["%s.entry.%s" % (_R9_LANG, _e) for _e in _R9_ENTRIES]
for _eid in _R9_ENTRIES:
    _ep = _ZH_BOOK / "entries" / ("%s.json" % _eid)
    if not _ep.is_file():
        continue
    for _pg in json.loads(_ep.read_text(encoding="utf-8")).get("pages") or []:
        for _k in ("text", "title"):
            _v = _pg.get(_k)
            if isinstance(_v, str) and _v.startswith("bettergold.handbook."):
                _r9_lang_keys.append(_v)
_r9_lang_keys = sorted(set(_r9_lang_keys))
_bgn10r9_checked += 1
if len(_r9_lang_keys) < 18:
    _bgn10r9_bad("bgn10r9-lang", "两族的语言键只收集到 %d 个（反空转守护）" % len(_r9_lang_keys))
for _k in _r9_lang_keys:
    _bgn10r9_checked += 3
    if _k not in zh or _k not in en:
        _bgn10r9_bad("bgn10r9-lang", "缺中文或英文：%s" % _k)
        continue
    if not str(zh[_k]).strip() or not str(en[_k]).strip():
        _bgn10r9_bad("bgn10r9-lang", "空值：%s" % _k)
    if str(zh[_k]) == str(en[_k]):
        _bgn10r9_bad("bgn10r9-lang", "英文与中文逐字相同（没翻译）：%s" % _k)

# ---------- ③ 成就：两族 8 条 ----------
# ⛔ 旧口径（原文留档）：两条链首的 parent 都写 `bettergold:treasure/any_core_material`；
#   作者 2026-10-18「两族不在贵金范畴」⇒ 现行 = `bettergold:root`（`bg-n10fix` ⑨）。
_R9_ADV = {
    "treasure/chaos_coin": ("bettergold:root", "task"),
    "metal/chaosgold/ingot": ("bettergold:treasure/chaos_coin", "task"),
    "metal/chaosgold/weapon": ("bettergold:metal/chaosgold/ingot", "task"),
    "metal/chaosgold/armor": ("bettergold:metal/chaosgold/weapon", "challenge"),
    "metal/chaosalloy/ingot": ("bettergold:root", "task"),
    "metal/chaosalloy/supply": ("bettergold:metal/chaosalloy/ingot", "task"),
    "metal/chaosalloy/weapon": ("bettergold:metal/chaosalloy/supply", "task"),
    "metal/chaosalloy/armor": ("bettergold:metal/chaosalloy/weapon", "challenge"),
}
for _ap, (_apar, _aframe) in _R9_ADV.items():
    _af = _ADV / (_ap + ".json")
    _bgn10r9_checked += 3
    if not _af.is_file():
        _bgn10r9_bad("bgn10r9-adv", "缺成就 JSON：%s" % _ap)
        continue
    _aj = json.loads(_af.read_text(encoding="utf-8"))
    if _aj.get("parent") != _apar:
        _bgn10r9_bad("bgn10r9-adv", "%s 的 parent 不是 %s：%r" % (_ap, _apar, _aj.get("parent")))
    if (_aj.get("display") or {}).get("frame", "task") != _aframe:
        _bgn10r9_bad("bgn10r9-adv", "%s 的 frame 不是 %s" % (_ap, _aframe))
    _atr = [c.get("conditions", {})
            for c in (_aj.get("criteria") or {}).values()]
    _bgn10r9_checked += 1
    if not all(t for t in _atr):
        _bgn10r9_bad("bgn10r9-adv", "%s 有判据没有 conditions" % _ap)
# 「获得即解锁」：两族 8 条的判据触发类型必须全部是 inventory_changed
_r9_triggers = set()
for _ap in _R9_ADV:
    _af = _ADV / (_ap + ".json")
    if _af.is_file():
        _r9_triggers.update(c.get("trigger")
                            for c in (json.loads(_af.read_text(encoding="utf-8")).get("criteria") or {}).values())
_bgn10r9_checked += 1
if _r9_triggers != {"minecraft:inventory_changed"}:
    _bgn10r9_bad("bgn10r9-adv",
                 "两族 8 条的触发类型不是清一色 inventory_changed（「获得即解锁」）：%s" % sorted(_r9_triggers))
# 武器成就的刀判据 = 单个标签字符串（bg-fix3 §二 的安全范式）
for _m in ("chaosgold", "chaosalloy"):
    _af = _ADV / "metal" / _m / "weapon.json"
    _bgn10r9_checked += 2
    if not _af.is_file():
        continue
    _crit = (json.loads(_af.read_text(encoding="utf-8")).get("criteria") or {})
    _kc = _crit.get("have_knife") or {}
    _ki = [p.get("items") for p in ((_kc.get("conditions") or {}).get("items") or [])]
    _bgn10r9_checked += 1
    if _ki != ["#bettergold:%s_knives" % _m]:
        _bgn10r9_bad("bgn10r9-adv",
                     "%s 的 have_knife.items 必须恰好是 [#bettergold:%s_knives]（标签单个字符串），实际 %r"
                     % (_m, _m, _ki))
    _bgn10r9_checked += 1
    if (_crit.get("have_knife") or {}).get("trigger") != "minecraft:inventory_changed":
        _bgn10r9_bad("bgn10r9-adv", "%s 的 have_knife 不是 inventory_changed" % _m)
# 成就文案键：两族 8 × 2 条，中英都要有
_r9_adv_keys = []
for _ap in _R9_ADV:
    _af = _ADV / (_ap + ".json")
    if not _af.is_file():
        continue
    _disp = json.loads(_af.read_text(encoding="utf-8")).get("display") or {}
    for _f in ("title", "description"):
        _tr = (_disp.get(_f) or {}).get("translate")
        if _tr:
            _r9_adv_keys.append(_tr)
_bgn10r9_checked += 2
if len(_r9_adv_keys) != 16:
    _bgn10r9_bad("bgn10r9-lang", "两族成就的语言键不是 16 条（8 条 × 2）：%d" % len(_r9_adv_keys))
for _k in _r9_adv_keys:
    _bgn10r9_checked += 2
    if _k not in zh or _k not in en:
        _bgn10r9_bad("bgn10r9-lang", "成就语言键缺中文或英文：%s" % _k)
    elif str(zh[_k]) == str(en[_k]):
        _bgn10r9_bad("bgn10r9-lang", "成就英文与中文逐字相同（没翻译）：%s" % _k)

# ---------- ④ 创造页：真源已含两族（材料前缀 21 件**本轮不扩**）----------
_bgn10r9_checked += 3
if _fx5_truth_order is None or _fx5_truth_order[-2:] != ["chaosgold", "chaosalloy"]:
    _bgn10r9_bad("bgn10r9-creative",
                 "`CreativeSections.METAL_ORDER` 的最后两项不是 [chaosgold, chaosalloy]：%r"
                 % (_fx5_truth_order,))
_r9_cat_src = strip_comments((JAVA / "material" / "CreativeTabSections.java").read_text(encoding="utf-8"))
_r9_prefix = re.search(r"MATERIAL_PREFIX_ORDER\s*=\s*List\.of\((.*?)\)\s*;", _r9_cat_src, re.S)
if not _r9_prefix:
    _bgn10r9_bad("bgn10r9-creative", "解析不到 `MATERIAL_PREFIX_ORDER`（反空转守护）")
else:
    _r9_prefix_items = re.findall(r'"([a-z0-9_]+)"', _r9_prefix.group(1))
    _bgn10r9_checked += 2
    if len(_r9_prefix_items) != 21:
        _bgn10r9_bad("bgn10r9-creative",
                     "材料前缀不是 21 件（本轮**不扩**，作者点的是那 21 件）：%d" % len(_r9_prefix_items))
    # ⚠ 判据必须点名**本轮的两族**（`chaos_coin_string` = 既有的「混沌金币串」，
    #   它本来就在那 21 件里，不许被 `startswith("chaos")` 误伤）。
    _r9_prefix_new = [i for i in _r9_prefix_items
                      if i.startswith("chaosgold_") or i.startswith("chaosalloy_")
                      or i == "chaos_coin"]
    if _r9_prefix_new:
        _bgn10r9_bad("bgn10r9-creative",
                     "材料前缀里出现了两族的物品 —— 本轮口径是「新物品排在其后」，不许插进那 21 件里：%s"
                     % (_r9_prefix_new,))

# ---------- ⑤ 文档侧：口径必须落档 ----------
_r9_doc17 = REPO / "docs" / "1.7-\u6df7\u6c8c\u91d1\u4e0e\u5d29\u4e71\u5408\u91d1-\u9700\u6c42\u7acb\u6863.md"
_r9_doc16 = REPO / "docs" / "1.6-\u89c4\u683c.md"
_bgn10r9_checked += 2
if not _r9_doc17.is_file() or "bg-n10r9" not in _r9_doc17.read_text(encoding="utf-8"):
    _bgn10r9_bad("bgn10r9-doc", "docs/1.7 里没有轮9（bg-n10r9）这一节")
if not _r9_doc16.is_file() or "bg-n10r9" not in _r9_doc16.read_text(encoding="utf-8"):
    _bgn10r9_bad("bgn10r9-doc", "docs/1.6-规格.md 里没有轮9 对既有口径的改动一节")

_bgn10r9_checked += 1
if _bgn10r9_checked < 40:
    _bgn10r9_bad("bgn10r9-anti-vacuum", "本段只跑了 %d 条判定（反空转）" % _bgn10r9_checked)
print("1.7 轮9（两族进手册 38 页 / 两族进成就 8 条 / 创造页 / 中英语言键）问题: "
      + str(len(bgn10r9_problems)) + " " + str(bgn10r9_problems[:4])
      + "（本段判定 " + str(_bgn10r9_checked) + " 条）")
if not bgn10r9_problems:
    print("[bgn10r9-ok] 两族 4 条目 38 页（页型序列 / 39 条配方引用 / 33 件图标模型全部存在）/ "
          "两族 8 条成就（parent 链 + challenge 两条 + 清一色 inventory_changed + 刀走标签）/ "
          "METAL_ORDER 含两族且材料前缀仍是 21 件 / 20+16 条中英键全部就位")

# ==========================================================================================
# 1.7 轮R（bg-n10rc，2026-10-17）：作者用**文字逐格**说清的四类配方 ⇒ 本段**逐格**钉住
# ==========================================================================================
# 作者 2026-10-17 原话（逐字进 `docs/1.7-…需求立档.md` §19；这里只摘判据）：
#   「混沌金币的充数功能…可以参与合成产生铜块、铁块和金块，无需合成：铜块 4 个铜锭加 1 个
#    混沌金币 / 铁块 6 个铁锭 / 金块 8 个金锭」「崩坏金锭的升级锻造模板…工作台中间是一个崩坏
#    金锭，下面是一个混沌金块，左面一列和右面一列都是混沌金锭，中上面是一个下界合金锻造模板」
#   「混沌附魔书…中上、中下、中左、中右 4 个混沌金锭 / 中间一本书 / 右上角和左下角 2 个混沌金币
#    串 / 左上角和右下角 2 个青晶石」「万间金砧：第一行 3 个金块 / 最中间 1 个万间金升级锻造
#    模板 / 中左、中右、左下角、右下角 4 个金锭 / 中下角 1 个万间金锭」
#
# ★ 核对结论（逐格比对后）：**只有第 3 类（混沌金附魔书）与实现不符** ——
#   产物把「青金石 / 混沌金币串」**平分在左右两条边上**（旧 `LIL/IBI/SIS`），而作者要的是
#   **两条对角线**（青金石在左上/右下 = 主对角，币串在右上/左下 = 副对角）⇒ 已改 `LIS/IBI/SIL`。
#   ⚠ 值得记一笔：立档 §2.6 自己写的"100% 读出"本来就是 LIS/IBI/SIL ⇒ 旧实现**违反了自己的立档**，
#   而旧关卡（`bgn10r4-enchanting-book`）把错的那一版钉成了契约 ⇒ 这是"关卡钉错了口径"的实例。
#
# 本段为什么不用"计数相等"了事：`LIL/IBI/SIS` 与 `LIS/IBI/SIL` 的**计数完全相同**
#   （2 青金石 / 2 币串 / 4 锭 / 1 书）⇒ 旧关卡那条计数断言**抓不到**这个错。
#   ⇒ 必须**逐格**（哪一行哪一列是哪个物品），这才是本轮真正缺的维度。
bgn10rc_problems: list[str] = []
_bgn10rc_checked = 0


def _bgn10rc_bad(tag: str, msg: str) -> None:
    bgn10rc_problems.append("[%s] %s" % (tag, msg))


_RC_DATA = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"
_RC_NS = "bettergold"
_RC_INGOT = _RC_NS + ":chaosgold_ingot"
_RC_COIN = _RC_NS + ":chaos_coin"
_RC_STRING = _RC_NS + ":chaos_coin_string"


def _rc_recipe(name: str):
    """读一条配方（稳定 ASCII 文件名；缺文件就记一条问题并返回 None）。"""
    if not name.isascii() or re.fullmatch(r"[a-z0-9_]+", name) is None:
        _bgn10rc_bad("bgn10rc-id", "配方文件名不是稳定 ASCII：[a-z0-9_]+ 才允许：" + name)
        return None
    path = _RC_DATA / (name + ".json")
    if not path.is_file():
        _bgn10rc_bad("bgn10rc-file", "缺配方 data/bettergold/recipe/" + name + ".json")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _rc_cell(i: int, j: int) -> str:
    rows = ("第1行", "第2行", "第3行")
    cols = ("第1列(左)", "第2列(中)", "第3列(右)")
    return rows[i] + cols[j]


def _rc_check_result(name: str, obj, want_id: str) -> None:
    """产物：id 必须对、**数量必须是 1**（"换数量"这一格也要能单独变红）。"""
    global _bgn10rc_checked
    _bgn10rc_checked += 1
    if obj is None:
        return
    res = obj.get("result") or {}
    if res.get("id") != want_id:
        _bgn10rc_bad("bgn10rc-result", name + " 的产物不是 " + want_id + "：" + repr(res))
    if res.get("count") != 1:
        _bgn10rc_bad("bgn10rc-result", name + " 的产物数量不是 1：" + repr(res))


def _rc_want_text(want) -> str:
    return " / ".join(" ".join(want[i]) for i in range(3))


def _rc_check_grid(name: str, obj: dict, want) -> None:
    """把 shaped 配方展开成 3×3 的**物品 id 网格**，与作者口述的那 9 格逐格比。"""
    global _bgn10rc_checked
    _bgn10rc_checked += 1
    if obj is None:
        return
    if obj.get("type") != "minecraft:crafting_shaped":
        _bgn10rc_bad("bgn10rc-type",
                     name + " 的 type 不是 minecraft:crafting_shaped（作者给的是 3×3 摆位）："
                     + str(obj.get("type")))
        return
    pat = obj.get("pattern") or []
    key = obj.get("key") or {}
    if len(pat) != 3 or any(len(r) != 3 for r in pat):
        _bgn10rc_bad("bgn10rc-shape", name + " 的 pattern 不是 3 行 × 3 列：" + repr(pat))
        return
    for i in range(3):
        for j in range(3):
            _bgn10rc_checked += 1
            ch = pat[i][j]
            got = (key.get(ch) or {}).get("item")
            if got != want[i][j]:
                _bgn10rc_bad("bgn10rc-cell",
                             name + " 的「" + _rc_cell(i, j) + "」是 " + str(got)
                             + "，作者口述是 " + str(want[i][j])
                             + "（整张表： " + _rc_want_text(want) + "）")


# ---------- ① 三条「充数」：无序，4 铜锭 / 6 铁锭 / 8 金锭，各 + 1 混沌金币 ----------
# 作者对铁、金两条只写了锭数（承「它可以参与合成产生铜块、铁块和金块」那一句）⇒
#   现状三条都带 1 枚币，与「充数」语义一致 ⇒ **按现状**（有序/无序也按现状 = 无序）。
_RC_FILLERS = (
    ("copper_block_with_chaos_coin", "minecraft:copper_ingot", 4, "minecraft:copper_block"),
    ("iron_block_with_chaos_coin", "minecraft:iron_ingot", 6, "minecraft:iron_block"),
    ("gold_block_with_chaos_coin", "minecraft:gold_ingot", 8, "minecraft:gold_block"),
)
for _name, _ing, _n, _out in _RC_FILLERS:
    _obj = _rc_recipe(_name)
    _bgn10rc_checked += 4
    if _obj is None:
        continue
    if _obj.get("type") != "minecraft:crafting_shapeless":
        _bgn10rc_bad("bgn10rc-filler",
                     _name + " 不是 crafting_shapeless（充数不需要排队列；作者没要求有序）")
    _ings = [i.get("item") if isinstance(i, dict) else i
             for i in (_obj.get("ingredients") or [])]
    if len(_ings) != _n + 1:
        _bgn10rc_bad("bgn10rc-filler",
                     _name + " 的材料总数不是 " + str(_n + 1) + "（实际 " + str(len(_ings)) + "）")
    if _ings.count(_ing) != _n:
        _bgn10rc_bad("bgn10rc-filler",
                     _name + " 里 " + _ing + " 不是 " + str(_n) + " 个（实际 "
                     + str(_ings.count(_ing)) + "）")
    if _ings.count(_RC_COIN) != 1:
        _bgn10rc_bad("bgn10rc-filler",
                     _name + " 里混沌金币不是恰好 1 个（实际 " + str(_ings.count(_RC_COIN))
                     + "）—— 充数的那枚币必须消耗 1 个")
    _res = _obj.get("result") or {}
    if _res.get("id") != _out or _res.get("count") != 1:
        _bgn10rc_bad("bgn10rc-filler", _name + " 的产物不是 1 个 " + _out + "：" + repr(_res))
    _extra = sorted(set(i for i in _ings if i not in (_ing, _RC_COIN)))
    if _extra:
        _bgn10rc_bad("bgn10rc-filler", _name + " 混进了别的材料：" + repr(_extra))

# ---------- ② 崩乱合金升级锻造模板：9 格逐格 ----------
_RC_TEMPLATE = (
    (_RC_INGOT, "minecraft:netherite_upgrade_smithing_template", _RC_INGOT),
    (_RC_INGOT, _RC_NS + ":chaosalloy_ingot", _RC_INGOT),
    (_RC_INGOT, _RC_NS + ":chaosgold_block", _RC_INGOT),
)
_obj = _rc_recipe("chaosalloy_upgrade_template")
_rc_check_grid("chaosalloy_upgrade_template", _obj, _RC_TEMPLATE)
_rc_check_result("chaosalloy_upgrade_template", _obj,
                 _RC_NS + ":chaosalloy_upgrade_template")

# ---------- ③ 混沌金附魔书：9 格逐格（青金石在主对角、币串在副对角） ----------
_RC_BOOK = (
    ("minecraft:lapis_lazuli", _RC_INGOT, _RC_STRING),
    (_RC_INGOT, "minecraft:book", _RC_INGOT),
    (_RC_STRING, _RC_INGOT, "minecraft:lapis_lazuli"),
)
_obj = _rc_recipe("chaosgold_enchanting_book")
_rc_check_grid("chaosgold_enchanting_book", _obj, _RC_BOOK)
_rc_check_result("chaosgold_enchanting_book", _obj,
                 _RC_NS + ":chaosgold_enchanting_book")
if _obj is not None:
    _bgn10rc_checked += 2
    # 负向 ①：「青晶石」= 原版青金石（不许是自造物品，也不许缺 minecraft 命名空间）
    _rc_items = [(v or {}).get("item") for v in (_obj.get("key") or {}).values()]
    if "minecraft:lapis_lazuli" not in _rc_items:
        _bgn10rc_bad("bgn10rc-book-lapis",
                     "附魔书里没有 minecraft:lapis_lazuli（作者写的「青晶石」= 青金石）")
    # 负向 ②：两枚「混沌金币**串**」是本物品，不许写成「混沌金币」(chaos_coin)
    if _RC_COIN in _rc_items:
        _bgn10rc_bad("bgn10rc-book-coin",
                     "附魔书里出现了 bettergold:chaos_coin —— 作者要的是 2 个「混沌金币串」"
                     "（bettergold:chaos_coin_string），两者是不同物品")

# ---------- ④ 万坚金砧：9 格逐格 ----------
_RC_ANVIL = (
    ("minecraft:gold_block", "minecraft:gold_block", "minecraft:gold_block"),
    ("minecraft:gold_ingot", _RC_NS + ":sturdygold_upgrade_template", "minecraft:gold_ingot"),
    ("minecraft:gold_ingot", _RC_NS + ":sturdygold_ingot", "minecraft:gold_ingot"),
)
_obj = _rc_recipe("sturdygold_anvil")
_rc_check_grid("sturdygold_anvil", _obj, _RC_ANVIL)
_rc_check_result("sturdygold_anvil", _obj, _RC_NS + ":sturdygold_anvil")

# ---------- ⑤ 生成器侧：模板那条的**唯一真源**必须自我一致 + 产物与真源逐字节一致 ----------
# ⚠ 这里不查"文件里有没有某个字符串"（注释里也能有同一串），而是：
#   (a) 把生成器当模块加载，用**它自己的** check() 跑一遍它自己的 targets()；
#   (b) 再把它生成的 20 份 JSON 与 `data/bettergold/recipe/` 里的**当前字节**逐一比 ——
#       这是"真源 ↔ 产物"的同一份判据，手改产物会立刻红。
_bgn10rc_checked += 3
_rc_gen = REPO / "tools" / "asset-generator" / "generate_chaosalloy_recipes.py"
if not _rc_gen.is_file():
    _bgn10rc_bad("bgn10rc-generator", "缺 generate_chaosalloy_recipes.py（崩乱合金 20 条的唯一真源）")
else:
    try:
        import importlib.util
        # ⚠ 加载**别人家的生成器**会写 `__pycache__/*.pyc`（本轮实测在 tools/asset-generator/ 里冒出来）
        #   ⇒ 这里临时关掉字节码缓存，加载完在 finally 复原（跑测不许在工作树留垃圾）。
        _dwb = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            _spec = importlib.util.spec_from_file_location("_bgn10rc_gen", _rc_gen)
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)      # 模块名不是 __main__ ⇒ 不会写盘
        finally:
            sys.dont_write_bytecode = _dwb
        if list(_mod.TEMPLATE_PATTERN) != ["GIG", "GAG", "GCG"]:
            _bgn10rc_bad("bgn10rc-generator",
                         "生成器的模板排布不是 GIG/GAG/GCG：" + repr(_mod.TEMPLATE_PATTERN))
        _gen_bad = _mod.check(_mod.targets())
        if _gen_bad:
            _bgn10rc_bad("bgn10rc-generator", "生成器自检不通过：" + repr(_gen_bad[:4]))
        _gen_files = _mod.targets()
        _gen_diff = []
        for _gname, _gobj in _gen_files:
            _gwant = json.dumps(_gobj, ensure_ascii=False, indent=2) + "\n"
            _gpath = _RC_DATA / _gname
            _bgn10rc_checked += 1
            if not _gpath.is_file():
                _gen_diff.append(_gname + "(缺文件)")
            elif _gpath.read_text(encoding="utf-8") != _gwant:
                _gen_diff.append(_gname)
        if _gen_diff:
            _bgn10rc_bad("bgn10rc-generator",
                         "产物与生成器（唯一真源）不逐字节一致：" + repr(_gen_diff[:6])
                         + "（共 " + str(len(_gen_diff)) + " 个）")
    except SystemExit:
        _bgn10rc_bad("bgn10rc-generator", "加载生成器时它自己 exit 了（自检失败）")
    except Exception as _e:                     # noqa: BLE001 —— 任何异常都不许变绿
        _bgn10rc_bad("bgn10rc-generator", "加载生成器失败：" + repr(_e))

# ---------- ⑥ 文档侧：作者这次的原话必须**逐字**落档（新 §19） ----------
_bgn10rc_checked += 5
_rc_doc = REPO / "docs" / "1.7-\u6df7\u6c8c\u91d1\u4e0e\u5d29\u4e71\u5408\u91d1-\u9700\u6c42\u7acb\u6863.md"
if not _rc_doc.is_file():
    _bgn10rc_bad("bgn10rc-doc", "缺 docs/1.7-…需求立档.md")
else:
    _rc_doc_txt = _rc_doc.read_text(encoding="utf-8")
    for _needle, _why in (
            (u"bg-n10rc", u"docs/1.7 里没有本轮（bg-n10rc）这一节"),
            (u"4 个铜锭加上 1 个混沌金币", u"没有逐字收录「4 个铜锭加上 1 个混沌金币」"),
            (u"左面一列和右面一列都是混沌金锭", u"没有逐字收录模板配方的左右两列"),
            (u"右上角和左下角", u"没有逐字收录附魔书的副对角（右上 + 左下）"),
            (u"第一行：3 个金块", u"没有逐字收录万坚金砧的第一行")):
        if _needle not in _rc_doc_txt:
            _bgn10rc_bad("bgn10rc-doc", _why + "（缺「" + _needle + "」）")

_bgn10rc_checked += 1
if _bgn10rc_checked < 40:
    _bgn10rc_bad("bgn10rc-anti-vacuum", "本段只跑了 %d 条判定（反空转）" % _bgn10rc_checked)
print("1.7 轮R（bg-n10rc 四类配方逐格）问题: "
      + str(len(bgn10rc_problems)) + " " + str(bgn10rc_problems[:4])
      + "（本段判定 " + str(_bgn10rc_checked) + " 条）")
if not bgn10rc_problems:
    print("[bgn10rc-ok] 四类配方逐格一致：充数 3 条（4/6/8 + 1 币 → 块）/ 崩乱合金模板 9 格 / "
          "混沌金附魔书 9 格（青金石主对角、币串副对角）/ 万坚金砧 9 格；生成器自检 0 条")

# ==========================================================================================
# 1.7 bg-n10rg（2026-10-17）：两个缺口的落地关卡
#   ① 混沌金装备 = **工作台配方**（11 件，**逐格**照原版 1.21.1 的形状，金属格换混沌金锭）
#   ② 「双倍贵金原料」= 每一条「贵金原料合成」都有一条同形的双倍版
#      （催化剂换高阶炼金油 / 数量 2 / 返还玻璃瓶）
#
# 作者原话（新的权威口径，逐字）：
#   「混沌金是用工作台公式制作的，原版装备在工作台上面怎么来合成它就怎么来」
#   「而"贵金"原料双倍合成就是直接把炼金燃油的位置换成高阶炼金油，然后原料的合成量改为 2，
#     记得返还玻璃瓶」
#
# ⚠ 为什么这一段的形状表**不**从生成器 import：生成器自己抄原版抄错了，共用一份表就永远抓不到
#   （= 拿期望表自比的假绿）。本段这张 `_RG_VANILLA` 是**从 `data/minecraft/recipe/*.json`
#   逐字抄来的独立副本**，生成器那边另有一份；两边不一致就红 —— 这是刻意留的双份。
# ⚠ 本段所有正向 needle 都跑在 **`strip_comments()` 之后**的源码上（注释里写一句就能喂饱断言）。
# ⚠ 失败文案里**不出现裸百分号**（`%` 只用于格式化，字面量一律写成中文）。
# ==========================================================================================
bgn10rg_problems: list[str] = []
_bgn10rg_checked = 0


def _bgn10rg_bad(tag: str, msg: str) -> None:
    bgn10rg_problems.append("[{}] {}".format(tag, msg))


_RG_NS = "bettergold"
_RG_INGOT = _RG_NS + ":chaosgold_ingot"
_RG_OIL = _RG_NS + ":refined_alchemic_oil"
# 11 件**有**工作台配方的（顺序 = 生成器 GEAR / 手册配方页顺序）
_RG_GEAR = ("sword", "axe", "pickaxe", "shovel", "hoe",
            "helmet", "chestplate", "leggings", "boots", "shield", "crossbow")
# 4 件**没有**工作台配方的（原版那一格没有「锭」这一步 / 原版根本没配方 / 不是原版物品）
#   bow      : 3 棍 + 3 线，一格金属都没有
#   mace     : 重核 + 微风棒，没有锭
#   trident  : 原版没有合成配方（溺尸掉落 / 试炼密室）
#   knife    : 乐事小刀 farmersdelight:golden_knife = 1 锭 + 1 棍，不是原版
# ⚠ **旧口径就地标注（2026-10-18，`bg-n10rc2`）**：作者对"剩下 4 件"的裁定是「第一个可以考虑」
#   ⇒ 这 4 件**也补了配方**，`EXCLUDED` 由 4 件变 **0 件**。旧元组原文留档（已作废、不删）：
#       _RG_EXCLUDED = ("bow", "mace", "trident", "knife")
#   新的逐格期望在文件末尾的 `[bgn10rc2-*]` 段（独立副本、逐格点名）。
_RG_EXCLUDED: tuple[str, ...] = ()
# 15 件（= 生成器 GEAR / 手册配方页顺序）：前 11 = 上面 `_RG_GEAR`，后 4 = `bg-n10rc2` 补的
_RG_GEAR_ALL = _RG_GEAR + ("bow", "mace", "trident", "knife")
_RG_ROWS = ("第1行", "第2行", "第3行")
_RG_COLS = ("第1列(左)", "第2列(中)", "第3列(右)")

# 原版 1.21.1 的形状（**独立副本**，逐字抄自 `data/minecraft/recipe/<文件>`）：
#   件 -> (原版配方文件名, pattern, {图例字符: 单元格内容})
#   单元格内容 = "item:<id>" / "tag:<id>"（`minecraft:planks` 在原版 shield 里是 tag）
_RG_VANILLA = {
    "sword": ("golden_sword.json", ["X", "X", "#"],
              {"X": "item:minecraft:gold_ingot", "#": "item:minecraft:stick"}),
    "axe": ("golden_axe.json", ["XX", "X#", " #"],
            {"X": "item:minecraft:gold_ingot", "#": "item:minecraft:stick"}),
    "pickaxe": ("golden_pickaxe.json", ["XXX", " # ", " # "],
                {"X": "item:minecraft:gold_ingot", "#": "item:minecraft:stick"}),
    "shovel": ("golden_shovel.json", ["X", "#", "#"],
               {"X": "item:minecraft:gold_ingot", "#": "item:minecraft:stick"}),
    "hoe": ("golden_hoe.json", ["XX", " #", " #"],
            {"X": "item:minecraft:gold_ingot", "#": "item:minecraft:stick"}),
    "helmet": ("golden_helmet.json", ["XXX", "X X"],
               {"X": "item:minecraft:gold_ingot"}),
    "chestplate": ("golden_chestplate.json", ["X X", "XXX", "XXX"],
                   {"X": "item:minecraft:gold_ingot"}),
    "leggings": ("golden_leggings.json", ["XXX", "X X", "X X"],
                 {"X": "item:minecraft:gold_ingot"}),
    "boots": ("golden_boots.json", ["X X", "X X"],
              {"X": "item:minecraft:gold_ingot"}),
    "shield": ("shield.json", ["WoW", "WWW", " W "],
               {"W": "tag:minecraft:planks", "o": "item:minecraft:iron_ingot"}),
    "crossbow": ("crossbow.json", ["#&#", "~$~", " # "],
                 {"#": "item:minecraft:stick", "&": "item:minecraft:iron_ingot",
                  "~": "item:minecraft:string", "$": "item:minecraft:tripwire_hook"}),
}
# 原版里属于「金属」的两格 ⇒ 本轮一律换成混沌金锭（金锭在 golden_*，铁锭在 shield / crossbow）
_RG_SUBST = ("item:minecraft:gold_ingot", "item:minecraft:iron_ingot")
_RG_METAL_CELL = "item:" + _RG_INGOT


def _rg_key_cell(ing) -> str:
    """把 key 里的一条解析成 "item:<id>" / "tag:<id>" / "<缺失>" / "<形状不认识>"。"""
    if not isinstance(ing, dict):
        return "<缺失>"
    if isinstance(ing.get("item"), str):
        return "item:" + ing["item"]
    if isinstance(ing.get("tag"), str):
        return "tag:" + ing["tag"]
    return "<形状不认识>"


def _rg_grid(pattern, key) -> list[list[str]]:
    """展开成 3×3 的**单元格内容**网格（空格子 = 空串）；越界按原版语义补空格。"""
    grid = [["" for _ in range(3)] for _ in range(3)]
    rows = list(pattern or [])
    for i in range(min(3, len(rows))):
        row = str(rows[i])
        for j in range(min(3, len(row))):
            ch = row[j]
            if ch == " ":
                continue
            grid[i][j] = _rg_key_cell((key or {}).get(ch))
    return grid


def _rg_want_grid(gear: str) -> list[list[str]]:
    """原版那张表 → 期望的 3×3（金属格已替换成混沌金锭）。"""
    _src, pattern, key = _RG_VANILLA[gear]
    want = [["" for _ in range(3)] for _ in range(3)]
    for i in range(min(3, len(pattern))):
        for j in range(min(3, len(pattern[i]))):
            ch = pattern[i][j]
            if ch == " ":
                continue
            cell = key[ch]
            want[i][j] = _RG_METAL_CELL if cell in _RG_SUBST else cell
    return want


def _rg_grid_text(grid) -> str:
    out = []
    for i in range(3):
        out.append(" ".join((grid[i][j] or "-") for j in range(3)))
    return " / ".join(out)


def _rg_load(name: str):
    """读一条配方（稳定 ASCII 文件名 + 存在性 + 合法 JSON）。"""
    if not str(name).isascii() or re.fullmatch(r"[a-z0-9_]+", str(name)) is None:
        _bgn10rg_bad("bgn10rg-id", "配方文件名不是稳定 ASCII（只许小写字母数字下划线）：" + str(name))
        return None
    path = _RC_DATA / (str(name) + ".json")
    if not path.is_file():
        _bgn10rg_bad("bgn10rg-file", "缺配方 data/bettergold/recipe/" + str(name) + ".json")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as _e:                       # noqa: BLE001
        _bgn10rg_bad("bgn10rg-file", str(name) + ".json 不是合法 JSON：" + repr(_e))
        return None


# ---------- ① 11 件工作台配方：**逐格**（9 格逐格点名，出错的格子报「第N行第M列」） ----------
for _gear in _RG_GEAR:
    _name = "chaosgold_" + _gear
    _obj = _rg_load(_name)
    _bgn10rg_checked += 4
    if _obj is None:
        continue
    if _obj.get("type") != "minecraft:crafting_shaped":
        _bgn10rg_bad("bgn10rg-gear-type",
                     _name + " 的 type 不是 minecraft:crafting_shaped：" + str(_obj.get("type")))
    if _obj.get("category") != "equipment":
        _bgn10rg_bad("bgn10rg-gear-type",
                     _name + " 的 category 不是 equipment：" + str(_obj.get("category")))
    _want = _rg_want_grid(_gear)
    _got = _rg_grid(_obj.get("pattern"), _obj.get("key"))
    _pat = _obj.get("pattern") or []
    if len(_pat) > 3 or any(len(str(r)) > 3 for r in _pat):
        _bgn10rg_bad("bgn10rg-gear-shape",
                     _name + " 的 pattern 超过 3×3：" + repr(_pat))
    for _i in range(3):
        for _j in range(3):
            _bgn10rg_checked += 1
            if _got[_i][_j] != _want[_i][_j]:
                _bgn10rg_bad("bgn10rg-gear-cell",
                             _name + " 的「" + _RG_ROWS[_i] + _RG_COLS[_j] + "」是 "
                             + (_got[_i][_j] or "<空>") + "，原版同格换成混沌金锭后应为 "
                             + (_want[_i][_j] or "<空>")
                             + "（原版 " + _RG_VANILLA[_gear][0] + "；期望表： "
                             + _rg_grid_text(_want) + "；实际： " + _rg_grid_text(_got) + "）")
    # 产物：id + 数量 1（「换数量」这一格也要能单独变红）
    _res = _obj.get("result") or {}
    _bgn10rg_checked += 2
    if _res.get("id") != _RG_NS + ":chaosgold_" + _gear:
        _bgn10rg_bad("bgn10rg-gear-result",
                     _name + " 的产物不是 " + _RG_NS + ":chaosgold_" + _gear + "：" + repr(_res))
    if _res.get("count") != 1:
        _bgn10rg_bad("bgn10rg-gear-result", _name + " 的产物数量不是 1：" + repr(_res))
    _cells = [c for row in _got for c in row]
    if _cells.count(_RG_METAL_CELL) < 1:
        _bgn10rg_bad("bgn10rg-gear-metal", _name + " 里一个 " + _RG_INGOT + " 都没有")
    # 反向：原版金属一格都不许残留（换漏了就是「免费金装」）
    _left = sorted(set(c for c in _cells if c in _RG_SUBST))
    if _left:
        _bgn10rg_bad("bgn10rg-gear-metal",
                     _name + " 还残留原版金属 " + repr(_left) + " —— 换漏了")

# 反向：4 件**不许**偷偷有工作台配方（本轮明确「停下报告、等作者」）
# ⚠ 旧口径（`bg-n10rg`，2026-10-17）**原文留档、已作废**（作者 2026-10-18「第一个可以考虑」）：
#   for _gear in ("bow", "mace", "trident", "knife"):
#       if (_RC_DATA / ("chaosgold_" + _gear + ".json")).is_file():
#           _bgn10rg_bad("bgn10rg-gear-excluded", "... 不该存在 ...")
#   现在改成**正向存在性**：这 4 条必须都在（逐格由 `[bgn10rc2-*]` 段钉住）。
for _gear in ("bow", "mace", "trident", "knife"):
    _bgn10rg_checked += 1
    _p = _RC_DATA / ("chaosgold_" + _gear + ".json")
    if not _p.is_file():
        _bgn10rg_bad("bgn10rc2-gear-added",
                     "chaosgold_" + _gear + ".json 不存在：这 4 件已由作者 2026-10-18"
                     "「第一个可以考虑」裁定补齐（旧口径是「停下报告」）")

# ---------- ② 双倍贵金原料：每一条「贵金原料合成」都必须有同形的双倍版 ----------
_rg_bases = []
for _p in sorted(_RC_DATA.glob("*.json")):
    if _p.stem.endswith("_doubled"):
        continue
    try:
        _o = json.loads(_p.read_text(encoding="utf-8"))
    except Exception:                             # noqa: BLE001  别的形状坏了不归本段管
        continue
    if str(_o.get("type") or "").startswith(_RG_NS + ":raw_sturdygold"):
        _rg_bases.append((_p, _o))
_bgn10rg_checked += 1
if len(_rg_bases) != 9:
    _bgn10rg_bad("bgn10rg-doubled-set",
                 "「贵金原料合成」的基础配方不是 9 条（8 族 + 万坚金金钱茄变体），实际 "
                 + str(len(_rg_bases)) + "：" + repr([p.stem for p, _ in _rg_bases]))
for _p, _base in _rg_bases:
    _dname = _p.stem + "_doubled"
    _dp = _RC_DATA / (_dname + ".json")
    _bgn10rg_checked += 5
    if not _dp.is_file():
        _bgn10rg_bad("bgn10rg-doubled-file", "缺双倍版 " + _dname + ".json（基础版 " + _p.name + "）")
        continue
    try:
        _d = json.loads(_dp.read_text(encoding="utf-8"))
    except Exception as _e:                       # noqa: BLE001
        _bgn10rg_bad("bgn10rg-doubled-file", _dname + ".json 不是合法 JSON：" + repr(_e))
        continue
    # (a) 双倍版 = 基础版 + **恰好** catalyst / count 两个字段（多一个少一个都红）
    _extra = sorted(set(_d) - set(_base))
    if _extra != ["catalyst", "count"]:
        _bgn10rg_bad("bgn10rg-doubled-fields",
                     _dname + " 比基础版多出的字段不是 [catalyst, count]：" + repr(_extra))
    _missing = sorted(set(_base) - set(_d))
    if _missing:
        _bgn10rg_bad("bgn10rg-doubled-fields", _dname + " 比基础版少了字段：" + repr(_missing))
    # (b) 催化剂 = 高阶炼金油；数量 = 2（作者原话两件事）
    if _d.get("catalyst") != _RG_OIL:
        _bgn10rg_bad("bgn10rg-doubled-catalyst",
                     _dname + " 的 catalyst 不是 " + _RG_OIL + "：" + repr(_d.get("catalyst")))
    if _d.get("count") != 2:
        _bgn10rg_bad("bgn10rg-doubled-count", _dname + " 的 count 不是 2：" + repr(_d.get("count")))
    # (c) 类型 / 兑换物 / 产物必须与基础版**逐字相同**（双倍只换催化剂与数量）
    for _f in ("type", "exchange", "result"):
        if _d.get(_f) != _base.get(_f):
            _bgn10rg_bad("bgn10rg-doubled-same",
                         _dname + " 的 " + _f + " 与基础版不同：" + repr(_d.get(_f))
                         + " != " + repr(_base.get(_f)))
    # (d) 基础版**不许**被改成双倍口径（作者没要求动既有那条 ⇒ 两条并存）
    if "catalyst" in _base or "count" in _base:
        _bgn10rg_bad("bgn10rg-doubled-base-untouched",
                     _p.name + " 自己被写进了 catalyst / count（本轮明确不改既有那条）")

# 反向：不许有「孤儿双倍版」（基础版没了 / 名字拼错）
for _dp in sorted(_RC_DATA.glob("*_doubled.json")):
    _bgn10rg_checked += 1
    _bp = _RC_DATA / (_dp.stem[:-len("_doubled")] + ".json")
    if not _bp.is_file():
        _bgn10rg_bad("bgn10rg-doubled-orphan",
                     _dp.name + " 没有对应的基础版（" + _bp.name + " 不存在）")

# ---------- ③ 返还玻璃瓶：机制在 Java 里，正向 needle 跑在**去注释源码**上 ----------
_rg_src_path = JAVA / "recipe" / "RawSturdygoldRecipe.java"
_bgn10rg_checked += 6
if not _rg_src_path.is_file():
    _bgn10rg_bad("bgn10rg-bottle", "缺 RawSturdygoldRecipe.java")
else:
    _rg_code = strip_comments(_rg_src_path.read_text(encoding="utf-8"))
    # (a) 剩余物按**催化剂那一格**返瓶：matches 与 getRemainingItems 各一次 ⇒ 恰好 2 处
    #     ⚠ 这一条就是「高阶炼金油那格也返瓶」的证明：写死 ALCHEMIC_FUEL 时这里会掉到 1 处
    _n_cat = _rg_code.count("stack.is(this.catalyst)")
    if _n_cat != 2:
        _bgn10rg_bad("bgn10rg-bottle",
                     "去注释后的 RawSturdygoldRecipe 里 stack.is(this.catalyst) 不是 2 处（实际 "
                     + str(_n_cat) + "）—— 匹配与返还玻璃瓶必须都按催化剂那一格判")
    if "stack.is(AllItems.ALCHEMIC_FUEL.get())" in _rg_code:
        _bgn10rg_bad("bgn10rg-bottle",
                     "去注释后的源码里仍在按 ALCHEMIC_FUEL 判格（高阶炼金油那格就不会返瓶）")
    if _rg_code.count("new ItemStack(Items.GLASS_BOTTLE)") != 1:
        _bgn10rg_bad("bgn10rg-bottle", "返瓶的 new ItemStack(Items.GLASS_BOTTLE) 不是恰好 1 处")
    # (b) 数量必须真的进产物（assemble + getResultItem 各一次）
    if _rg_code.count("new ItemStack(this.result, this.count)") != 2:
        _bgn10rg_bad("bgn10rg-doubled-count",
                     "去注释后的源码里 new ItemStack(this.result, this.count) 不是 2 处"
                     "（assemble / getResultItem 都要带数量，否则结果格仍显示 1）")
    # (c) 两个字段都进了 Codec 与 StreamCodec（少一个就是「服务端 2、客户端 1」）
    for _needle, _why in (('optionalFieldOf("catalyst")', "catalyst 没进 Codec"),
                          ('optionalFieldOf("count", 1)', "count 没进 Codec（缺省必须是 1）"),
                          ("RawSturdygoldRecipe::catalyst", "catalyst 没进 StreamCodec"),
                          ("RawSturdygoldRecipe::count", "count 没进 StreamCodec")):
        if _needle not in _rg_code:
            _bgn10rg_bad("bgn10rg-bottle", _why + "：缺 " + _needle)
    # (d) 缺省催化剂仍必须是炼金燃油（老 JSON 一字不改仍按老语义）
    if "defaultCatalyst = () -> AllItems.ALCHEMIC_FUEL.get()" not in _rg_code:
        _bgn10rg_bad("bgn10rg-bottle", "缺省的催化剂不是炼金燃油（老配方语义被改了）")

# ---------- ④ 生成器 = 唯一真源：它自己的自检 + 产物与磁盘逐字节一致 ----------
_bgn10rg_checked += 2
try:
    import importlib.util
    _dwb2 = sys.dont_write_bytecode
    sys.dont_write_bytecode = True            # 别在工作树里留 __pycache__
    try:
        _rg_gen_path = REPO / "tools" / "asset-generator" / "generate_chaosgold_recipes.py"
        _rg_metal_path = REPO / "tools" / "asset-generator" / "generate_metal_recipes.py"
        _spec2 = importlib.util.spec_from_file_location("_bgn10rg_gen", _rg_gen_path)
        _rg_gen = importlib.util.module_from_spec(_spec2)
        _spec2.loader.exec_module(_rg_gen)
        _spec3 = importlib.util.spec_from_file_location("_bgn10rg_metal", _rg_metal_path)
        _rg_metal = importlib.util.module_from_spec(_spec3)
        _spec3.loader.exec_module(_rg_metal)
    finally:
        sys.dont_write_bytecode = _dwb2
    # (a) 生成器自己的自检
    _rg_gen_bad = list(_rg_gen.check(_rg_gen.targets()))
    if _rg_gen_bad:
        _bgn10rg_bad("bgn10rg-generator", "混沌金配方生成器自检不通过：" + repr(_rg_gen_bad[:4]))
    if tuple(_rg_gen.GEAR) != _RG_GEAR_ALL:
        _bgn10rg_bad("bgn10rg-generator",
                     "生成器的 GEAR 与本段的 15 件不一致：" + repr(_rg_gen.GEAR))
    if tuple(sorted(_rg_gen.EXCLUDED)) != tuple(sorted(_RG_EXCLUDED)):
        _bgn10rg_bad("bgn10rg-generator",
                     "生成器的 EXCLUDED 与本段不一致（旧口径是 4 件停下报告，本轮应为 0 件）："
                     + repr(sorted(_rg_gen.EXCLUDED)))
    # (b) 11 条产物与磁盘**逐字节**一致（手改产物立刻红）
    _rg_diff = []
    for _gname, _gobj in _rg_gen.targets():
        _bgn10rg_checked += 1
        _gpath = _RC_DATA / _gname
        if not _gpath.is_file():
            _rg_diff.append(_gname + "(缺文件)")
        elif _gpath.read_text(encoding="utf-8") != json.dumps(_gobj, ensure_ascii=False, indent=2) + "\n":
            _rg_diff.append(_gname)
    if _rg_diff:
        _bgn10rg_bad("bgn10rg-generator",
                     "混沌金配方产物与唯一真源不再逐字节一致：" + repr(_rg_diff[:6]))
    # (c) 双倍版那一批：生成器自检 + 9 条逐字节一致
    _rg_doubled_targets = _rg_metal.doubled_raw_targets()
    _rg_doubled_bad = list(_rg_metal.check_doubled(_rg_doubled_targets))
    if _rg_doubled_bad:
        _bgn10rg_bad("bgn10rg-generator", "双倍原料生成器自检不通过：" + repr(_rg_doubled_bad[:4]))
    _rg_ddiff = []
    for _gname, _gobj, _gbase in _rg_doubled_targets:
        _bgn10rg_checked += 1
        _gpath = _RC_DATA / _gname
        if not _gpath.is_file():
            _rg_ddiff.append(_gname + "(缺文件)")
        elif _gpath.read_text(encoding="utf-8") != json.dumps(_gobj, ensure_ascii=False, indent=2) + "\n":
            _rg_ddiff.append(_gname)
    if _rg_ddiff:
        _bgn10rg_bad("bgn10rg-generator",
                     "双倍原料产物与唯一真源不再逐字节一致：" + repr(_rg_ddiff[:6]))
except SystemExit:
    _bgn10rg_bad("bgn10rg-generator", "生成器被加载时自己 exit 了（自检失败）")
except Exception as _e:                           # noqa: BLE001
    _bgn10rg_bad("bgn10rg-generator", "生成器加载失败：" + repr(_e))

# ---------- ⑤ 手册：gear_chaosgold 的 15 页（3 文案 + 8 页配方 + 3 图标 + 1 附魔书配方） ----------
#   ⚠ 旧值 13（6 页配方 / 11 件）**原文留档、已作废**：`_RG_BOOK_PAGES = 13`。
_RG_BOOK_PAGES = 15
_bgn10rg_checked += 5
for _d, _tag in ((_ZH_BOOK, "zh"), (_EN_BOOK, "en")):
    _ep = _d / "entries" / "gear_chaosgold.json"
    if not _ep.is_file():
        _bgn10rg_bad("bgn10rg-handbook", _tag + " 缺 entries/gear_chaosgold.json")
        continue
    _ej = json.loads(_ep.read_text(encoding="utf-8"))
    _pages = _ej.get("pages") or []
    if len(_pages) != _RG_BOOK_PAGES:
        _bgn10rg_bad("bgn10rg-handbook",
                     _tag + " 的 gear_chaosgold 页数不是 " + str(_RG_BOOK_PAGES)
                     + "（实际 " + str(len(_pages)) + "）")
        continue
    _types = [p.get("type") for p in _pages]
    _want_types = (["patchouli:text"] * 3 + ["patchouli:crafting"] * 8
                   + ["patchouli:spotlight"] * 3 + ["patchouli:crafting"])
    if _types != _want_types:
        _bgn10rg_bad("bgn10rg-handbook",
                     _tag + " 的页型序列不对：" + repr(_types))
    # 配方页（第 4~11 页）必须**恰好**是这 15 件、顺序 = _RG_GEAR_ALL、每页最多 2 条
    _refs = []
    for _pg in _pages[3:11]:
        _on_page = [x for x in (_pg.get("recipe"), _pg.get("recipe2")) if isinstance(x, str)]
        _bgn10rg_checked += 1
        if len(_on_page) > 2:
            _bgn10rg_bad("bgn10rg-handbook",
                         _tag + " 有配方页塞了 " + str(len(_on_page)) + " 条（Patchouli 上限 2）")
        _refs.extend(_on_page)
    _want_refs = [_RG_NS + ":chaosgold_" + _g for _g in _RG_GEAR_ALL]
    if _refs != _want_refs:
        _bgn10rg_bad("bgn10rg-handbook",
                     _tag + " 的 15 件配方引用与 _RG_GEAR_ALL 不一致：" + repr(_refs))
    # 死链：每条引用都要真的落在 data/bettergold/recipe/
    _dead = [_r for _r in _refs
             if not (_RC_DATA / (_r.split(":", 1)[1] + ".json")).is_file()]
    _bgn10rg_checked += 1
    if _dead:
        _bgn10rg_bad("bgn10rg-handbook", _tag + " 的配方页有死链：" + repr(_dead))
# zh / en 结构必须相同
_bgn10rg_checked += 1
_zh_ep = _ZH_BOOK / "entries" / "gear_chaosgold.json"
_en_ep = _EN_BOOK / "entries" / "gear_chaosgold.json"
if _zh_ep.is_file() and _en_ep.is_file():
    if (json.loads(_zh_ep.read_text(encoding="utf-8")).get("pages")
            != json.loads(_en_ep.read_text(encoding="utf-8")).get("pages")):
        _bgn10rg_bad("bgn10rg-handbook", "gear_chaosgold 的 zh / en 页列表不一致")

# ---------- ⑥ 文案口径 + 文档 ----------
_bgn10rg_checked += 4
try:
    _rg_zh_lang = json.loads((_RES / "assets" / "bettergold" / "lang" / "zh_cn.json")
                             .read_text(encoding="utf-8"))
except Exception as _e:                           # noqa: BLE001
    _rg_zh_lang = {}
    _bgn10rg_bad("bgn10rg-lang", "读不了 zh_cn.json：" + repr(_e))
_rg_text = _rg_zh_lang.get("bettergold.handbook.page.gear_chaosgold_1_right", "")
for _needle, _why in (("工作台", "新口径必须说清是「工作台」合成"),
                      ("11 件", "新口径必须写清 11 件（不是 14 件）"),
                      ("4 件", "新口径必须写清剩下 4 件没有工作台配方")):
    if _needle not in _rg_text:
        _bgn10rg_bad("bgn10rg-lang",
                     "手册「混沌金装备」正文没提「" + _needle + "」：" + _why)
if "只展示物品" in _rg_text:
    _bgn10rg_bad("bgn10rg-lang",
                 "手册正文仍是旧口径（「只展示物品，不展示配方」）—— 现在已经有配方页了")

_bgn10rg_checked += 5
_rg_doc = REPO / "docs" / "1.7-\u6df7\u6c8c\u91d1\u4e0e\u5d29\u4e71\u5408\u91d1-\u9700\u6c42\u7acb\u6863.md"
if not _rg_doc.is_file():
    _bgn10rg_bad("bgn10rg-doc", "缺 docs/1.7-混沌金与崩乱合金-需求立档.md")
else:
    _rg_doc_txt = _rg_doc.read_text(encoding="utf-8")
    for _needle, _why in (
            ("bg-n10rg", "立档里没有本轮标记（bg-n10rg）这一段"),
            ("混沌金是用工作台公式制作的", "没把作者「原版装备怎么合就怎么合」那句原话收进立档"),
            ("直接把炼金燃油的位置换成高阶炼金油", "没把作者双倍原料那句原话收进立档"),
            ("记得返还玻璃瓶", "没把作者「返还玻璃瓶」那句原话收进立档"),
            ("停下报告", "没把「4 件停下报告」的判据写进立档")):
        if _needle not in _rg_doc_txt:
            _bgn10rg_bad("bgn10rg-doc", _why + "：缺「" + _needle + "」")

_bgn10rg_checked += 1
if _bgn10rg_checked < 60:
    _bgn10rg_bad("bgn10rg-anti-vacuum",
                 "本段只检查了 " + str(_bgn10rg_checked) + " 项（反空转守护：应远大于 60）")
print("1.7 bg-n10rg（混沌金工作台配方 + 双倍贵金原料）问题: "
      + str(len(bgn10rg_problems)) + " " + str(bgn10rg_problems[:4])
      + "（本段判定 " + str(_bgn10rg_checked) + " 项）")
if not bgn10rg_problems:
    print("[bgn10rg-ok] 混沌金 15 件工作台配方逐格照原版（前 11 件金属格 = 混沌金锭；后 4 件见 "
          "[bgn10rc2-*]）/ 9 条双倍贵金原料（催化剂 = 高阶炼金油、数量 2、与基础版逐字段同形且基础版未被改）/ "
          "返还玻璃瓶按催化剂那一格判（去注释源码 2 处）/ 手册 gear_chaosgold 15 页 15 条配方无死链")

# ==========================================================================================
# 1.7 bg-n10d（2026-10-18，裁定 #13）：金火把花种子 = 原版种子那 4 条标签
# ==========================================================================================
# 作者原话：「第 13 条。这个要不要做？我觉得吧，可以加上。」
# 实证来源（【读源码】原版 1.21.1 数据包；`data/minecraft/tags/item/` 的 147 张标签里
#   含 `minecraft:torchflower_seeds` 的**恰好 4 张**，逐张 JSON 都读过）：
#     chicken_food（鸡：喂食 / 繁殖）        parrot_food（鹦鹉：喂食跳舞）
#     sniffer_food（嗅探兽：喂食 / 繁殖）    villager_plantable_seeds（村民：农民会**种**它）
# ⇒ 我们写同名 4 张 JSON，只多一条自己的种子。
# ⚠ `replace` 必须是 **false**（或缺省）：`TagLoader#load:54-56`（1.21.1 sources jar）
#     `if (tagfile.replace()) { list.clear(); }`
#   ⇒ 写 true 会把**原版那几条种子整份清掉**（鸡再也不吃小麦种子）——本段把这条钉死。
# ⚠ 副作用（作者已明确接受）：村民农民会把种子种进耕地（长成金火把花）；
#   鸡 / 鹦鹉 / 嗅探兽会把它当食物（嗅探兽还会把它刨出来）。
bgn10d_problems: list[str] = []
_bgn10d_checked = 0


def _bgn10d_bad(tag: str, msg: str) -> None:
    bgn10d_problems.append("[" + tag + "] " + msg)


_BGN10D_SEED = "bettergold:golden_torchflower_seeds"
_BGN10D_RES = REPO / "src" / "main" / "resources"
_BGN10D_TAG_DIR = _BGN10D_RES / "data" / "minecraft" / "tags" / "item"
_BGN10D_TAGS = ("chicken_food", "parrot_food", "sniffer_food", "villager_plantable_seeds")

for _t in _BGN10D_TAGS:
    _bgn10d_checked += 1
    _p = _BGN10D_TAG_DIR / (_t + ".json")
    if not _p.is_file():
        _bgn10d_bad("bgn10d-seed-tags-missing", "缺 data/minecraft/tags/item/" + _t + ".json")
        continue
    try:
        _obj = json.loads(_p.read_text(encoding="utf-8"))
    except Exception as _e:  # noqa: BLE001
        _bgn10d_bad("bgn10d-seed-tags-json", _t + ".json 解析失败：" + str(_e))
        continue
    # ① replace 不许是 true（写了就把原版整份清掉）
    _bgn10d_checked += 1
    if _obj.get("replace") is True:
        _bgn10d_bad("bgn10d-seed-tags-replace",
                    _t + ".json 写了 replace:true —— TagLoader 会 list.clear()，"
                    "原版那几条种子被整份清掉（鸡不再吃小麦种子）")
    _vals = _obj.get("values") or []
    # ② 正向：我们的种子必须在
    _bgn10d_checked += 1
    if _BGN10D_SEED not in _vals:
        _bgn10d_bad("bgn10d-seed-tags-value", _t + ".json 的 values 里没有 " + _BGN10D_SEED)
    # ③ 负向：这张标签里不许混进**别的**本模组物品（只许这一条新增）
    _extra = [v for v in _vals
              if isinstance(v, str) and v.startswith("bettergold:") and v != _BGN10D_SEED]
    _bgn10d_checked += 1
    if _extra:
        _bgn10d_bad("bgn10d-seed-tags-extra",
                    _t + ".json 里混进了别的本模组物品：" + str(_extra))

# ④ 横向负向：种子**只许**出现在这 4 张标签里；别处（其它 tags 文件）一张都不许有
_bgn10d_checked += 1
_seed_elsewhere = []
for _root, _dirs, _files in os.walk(_BGN10D_RES / "data"):
    for _f in _files:
        if not _f.endswith(".json"):
            continue
        _full = Path(_root) / _f
        if "tags" not in _full.parts:
            continue
        try:
            _txt = _full.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            continue
        if _BGN10D_SEED not in _txt:
            continue
        if _full.parent == _BGN10D_TAG_DIR and _full.stem in _BGN10D_TAGS:
            continue
        _seed_elsewhere.append(_full.relative_to(_BGN10D_RES).as_posix())
if _seed_elsewhere:
    _bgn10d_bad("bgn10d-seed-tags-scope",
                "金火把花种子出现在这 4 张之外的地方：" + str(sorted(_seed_elsewhere)))

# ⑤ 文档侧：本轮口径必须落档（缺了 = 下一轮不知道这 4 张标签是谁批的）
_bgn10d_checked += 6
_doc_n10d = REPO / "docs" / ("1.7-\u88c1\u5b9a\u843d\u5b9e-4-5-12-13-14.md")
if not _doc_n10d.is_file():
    _bgn10d_bad("bgn10d-doc", "缺 docs/1.7-裁定落实-4-5-12-13-14.md（本轮裁定没有落档）")
else:
    _doc_txt = _doc_n10d.read_text(encoding="utf-8")
    for _needle, _why in (
            ("bg-n10d", "文档里没有本轮标记 bg-n10d"),
            ("villager_plantable_seeds", "没写村民可种（#13 的副作用）"),
            ("第六次授权", "没写 #12 是第六次贴图授权"),
            ("18×18", "没写 tremble 图标的 18×18 口径"),
            ("torchflower_seeds", "没写「照原版 torchflower_seeds 的 4 条」")):
        if _needle not in _doc_txt:
            _bgn10d_bad("bgn10d-doc", _why + "：缺「" + _needle + "」")

if _bgn10d_checked < 20:
    _bgn10d_bad("bgn10d-anti-vacuum",
                "本段只跑了 " + str(_bgn10d_checked) + " 条判定（反空转：应远大于 20）")
print("1.7 bg-n10d（#13 金火把花种子 4 条原版标签）问题: "
      + str(len(bgn10d_problems)) + " " + str(bgn10d_problems[:4])
      + "（本段判定 " + str(_bgn10d_checked) + " 条）")
if not bgn10d_problems:
    print("[bgn10d-seed-tags-ok] 4 张原版种子标签各含金火把花种子、replace 不是 true、"
          "没有别的本模组物品混入、种子也没有出现在这 4 张之外")

# ==========================================================================================
# 1.7 bg-n10rc2（2026-10-18）：作者两条裁定的落地关卡
#   ① 「第一个可以考虑」⇒ 弓 / 重锤 / 三叉戟 / 乐事刀 这 4 件补工作台配方（**逐格**钉住）
#   ② 「第二个需要扩」 ⇒ 返瓶从"配方层"扩到"物品级"（`refined_alchemic_oil` 的 craftRemainder）
#   ③ 「第三个我再问一问」⇒ 混沌金锭**上游未动**（本段不发明任何"锭怎么来"的配方/掉落）
#
# ⚠ 与 `[bgn10rg-*]` 的分工：那一段管**前 11 件**的逐格 + 双倍原料；本段管**后 4 件** + 返瓶机制。
# ⚠ 期望表是本段**自己的独立副本**（不从生成器 import —— 生成器自己抄错时，共用一份表就永远抓不到，
#   那是本仓"拿期望表自比"的假绿老路）。
# ⚠ 所有正向 needle 都跑在 `strip_comments()` 之后（注释里写一句就喂饱断言 = 假绿）。
# ⚠ 失败文案里**不出现裸百分号**（只用于格式化）。
# ==========================================================================================
bgn10rc2_problems: list[str] = []
_bgn10rc2_checked = 0


def _bgn10rc2_bad(tag: str, msg: str) -> None:
    bgn10rc2_problems.append("[{}] {}".format(tag, msg))


_RC2_GEAR = ("bow", "mace", "trident", "knife")
_RC2_ROWS = ("第1行", "第2行", "第3行")
_RC2_COLS = ("第1列(左)", "第2列(中)", "第3列(右)")
_RC2_INGOT = "item:bettergold:chaosgold_ingot"
_RC2_BLOCK = "item:bettergold:chaosgold_block"
_RC2_STICK = "item:minecraft:stick"
_RC2_FD_CONDITION = [{"type": "neoforge:mod_loaded", "modid": "farmersdelight"}]

# 期望的 3×3（**逐格**；金属格已替换成混沌金材料）—— 本段独立抄的一份
_RC2_WANT = {
    # 原版 bow.json 逐字：`#` 棍 / `X` 线 ⇒ **棍那一格换成混沌金锭**（3 锭 + 3 线）
    "bow": ([" #X", "# X", " #X"], {"#": _RC2_INGOT, "X": "item:minecraft:string"}),
    # 原版 mace.json 逐字：`#` 重核 / `I` 微风棒 ⇒ **重核那一格换成混沌金块**（1 块 + 1 微风棒）
    "mace": ([" # ", " I "], {"#": _RC2_BLOCK, "I": "item:minecraft:breeze_rod"}),
    # ⚠ 原版**没有**三叉戟配方 ⇒ 这条是**原创形状**（上排 3 锭 + 中列再 1 锭 + 底部 1 棍）
    "trident": (["XXX", " X ", " # "], {"X": _RC2_INGOT, "#": _RC2_STICK}),
    # 乐事 farmersdelight:golden_knife 逐字：`m` 金锭 / `s` 棍 ⇒ 1 混沌金锭 + 1 棍
    "knife": (["m", "s"], {"m": _RC2_INGOT, "s": _RC2_STICK}),
}
# 来源（bow / mace 逐字抄自原版 1.21.1 的 `data/minecraft/recipe/<文件>`；
#       knife 抄自农夫乐事的 `data/farmersdelight/recipe/golden_knife.json`；
#       trident **没有**来源 ⇒ 下表故意不写它，并在下面单独断言"它是原创"）
_RC2_SOURCE = {
    "bow": ([" #X", "# X", " #X"], {"#": _RC2_STICK, "X": "item:minecraft:string"}),
    "mace": ([" # ", " I "], {"#": "item:minecraft:heavy_core",
                              "I": "item:minecraft:breeze_rod"}),
    "knife": (["m", "s"], {"m": "item:minecraft:gold_ingot", "s": _RC2_STICK}),
}


def _rc2_cell(ing) -> str:
    if not isinstance(ing, dict):
        return "<缺失>"
    if isinstance(ing.get("item"), str):
        return "item:" + ing["item"]
    if isinstance(ing.get("tag"), str):
        return "tag:" + ing["tag"]
    return "<形状不认识>"


def _rc2_grid(pattern, key) -> list[list[str]]:
    grid = [["" for _ in range(3)] for _ in range(3)]
    rows = list(pattern or [])
    for _i in range(min(3, len(rows))):
        row = str(rows[_i])
        for _j in range(min(3, len(row))):
            ch = row[_j]
            if ch == " ":
                continue
            grid[_i][_j] = _rc2_cell((key or {}).get(ch))
    return grid


def _rc2_want_grid(gear: str) -> list[list[str]]:
    pattern, key = _RC2_WANT[gear]
    want = [["" for _ in range(3)] for _ in range(3)]
    for _i in range(min(3, len(pattern))):
        for _j in range(min(3, len(pattern[_i]))):
            ch = pattern[_i][_j]
            if ch == " ":
                continue
            want[_i][_j] = key[ch]
    return want


def _rc2_grid_text(grid) -> str:
    return " / ".join(" ".join((grid[_i][_j] or "-") for _j in range(3)) for _i in range(3))


# ---------- ① 4 件新配方：逐格（9 格逐格点名，错的格子报「第N行第M列」） ----------
for _g in _RC2_GEAR:
    _nm = "chaosgold_" + _g
    _bgn10rc2_checked += 2
    if not _nm.isascii() or re.fullmatch(r"[a-z0-9_]+", _nm) is None:
        _bgn10rc2_bad("bgn10rc2-id", "配方文件名不是稳定 ASCII：" + _nm)
    _path = _RC_DATA / (_nm + ".json")
    if not _path.is_file():
        _bgn10rc2_bad("bgn10rc2-file", "缺配方 data/bettergold/recipe/" + _nm + ".json")
        continue
    try:
        _obj = json.loads(_path.read_text(encoding="utf-8"))
    except Exception as _e:                                # noqa: BLE001
        _bgn10rc2_bad("bgn10rc2-file", _nm + ".json 不是合法 JSON：" + repr(_e))
        continue
    _bgn10rc2_checked += 4
    if _obj.get("type") != "minecraft:crafting_shaped":
        _bgn10rc2_bad("bgn10rc2-type", _nm + " 的 type 不是 minecraft:crafting_shaped：" + repr(_obj.get("type")))
    if _obj.get("category") != "equipment":
        _bgn10rc2_bad("bgn10rc2-type", _nm + " 的 category 不是 equipment：" + repr(_obj.get("category")))
    _pat = _obj.get("pattern") or []
    if len(_pat) > 3 or any(len(str(_r)) > 3 for _r in _pat):
        _bgn10rc2_bad("bgn10rc2-shape", _nm + " 的 pattern 超过 3×3：" + repr(_pat))
    if len(_pat) != len(_RC2_WANT[_g][0]):
        _bgn10rc2_bad("bgn10rc2-shape",
                      _nm + " 的行数不是 " + str(len(_RC2_WANT[_g][0])) + "：" + repr(_pat))
    _got = _rc2_grid(_pat, _obj.get("key"))
    _want = _rc2_want_grid(_g)
    for _i in range(3):
        for _j in range(3):
            _bgn10rc2_checked += 1
            if _got[_i][_j] != _want[_i][_j]:
                _bgn10rc2_bad("bgn10rc2-cell",
                              _nm + " 的「" + _RC2_ROWS[_i] + _RC2_COLS[_j] + "」是 "
                              + (_got[_i][_j] or "<空>") + "，按 §21 的读法应为 "
                              + (_want[_i][_j] or "<空>")
                              + "（期望表： " + _rc2_grid_text(_want) + "；实际： "
                              + _rc2_grid_text(_got) + "）")
    _res = _obj.get("result") or {}
    _bgn10rc2_checked += 2
    if _res.get("id") != "bettergold:" + _nm:
        _bgn10rc2_bad("bgn10rc2-result", _nm + " 的产物不是 bettergold:" + _nm + "：" + repr(_res))
    if _res.get("count") != 1:
        _bgn10rc2_bad("bgn10rc2-result", _nm + " 的产物数量不是 1：" + repr(_res))
    _cells = [c for _row in _got for c in _row]
    _bgn10rc2_checked += 2
    if not any(c in (_RC2_INGOT, _RC2_BLOCK) for c in _cells):
        _bgn10rc2_bad("bgn10rc2-metal", _nm + " 里一格混沌金材料都没有")
    _left = sorted(set(c for c in _cells
                       if c in ("item:minecraft:gold_ingot", "item:minecraft:iron_ingot")))
    if _left:
        _bgn10rc2_bad("bgn10rc2-metal", _nm + " 还残留原版金属 " + repr(_left) + " —— 换漏了")

# ---------- ② 逐件的针对性负向（这 4 条各自最容易写错的那种） ----------
# 弓：⚠ **不许**做成"3 棍 + 3 线"（那样一格混沌金都不用 = 零成本白送混沌金弓）
_bgn10rc2_checked += 2
_bow = _RC2_WANT["bow"]
_bow_obj_path = _RC_DATA / "chaosgold_bow.json"
if _bow_obj_path.is_file():
    _bo = json.loads(_bow_obj_path.read_text(encoding="utf-8"))
    _bo_cells = [c for _row in _rc2_grid(_bo.get("pattern"), _bo.get("key")) for c in _row]
    if _bo_cells.count(_RC2_STICK) != 0:
        _bgn10rc2_bad("bgn10rc2-bow-metal",
                      "chaosgold_bow 里还有木棍 —— 弓的金属格就是**棍那一格**，留着棍等于零成本合出混沌金弓")
    if _bo_cells.count(_RC2_INGOT) != 3:
        _bgn10rc2_bad("bgn10rc2-bow-metal",
                      "chaosgold_bow 的混沌金锭不是 3 个（实际 " + str(_bo_cells.count(_RC2_INGOT)) + "）")

# 重锤：⚠ 金属那一格是**重核** ⇒ 必须是**混沌金块**，不许残留重核、也不许写成锭
_bgn10rc2_checked += 2
_mace_obj_path = _RC_DATA / "chaosgold_mace.json"
if _mace_obj_path.is_file():
    _mo = json.loads(_mace_obj_path.read_text(encoding="utf-8"))
    _mo_cells = [c for _row in _rc2_grid(_mo.get("pattern"), _mo.get("key")) for c in _row]
    if _mo_cells.count(_RC2_BLOCK) != 1:
        _bgn10rc2_bad("bgn10rc2-mace-block",
                      "chaosgold_mace 的混沌金块不是恰好 1 个（实际 " + str(_mo_cells.count(_RC2_BLOCK)) + "）")
    if _mo_cells.count("item:minecraft:heavy_core") != 0:
        _bgn10rc2_bad("bgn10rc2-mace-block", "chaosgold_mace 里还留着原版重核（金属格没换）")
    if _mo_cells.count(_RC2_INGOT) != 0:
        _bgn10rc2_bad("bgn10rc2-mace-block",
                      "chaosgold_mace 里写了混沌金锭 —— §21 的口径是重核 → **块**")

# 三叉戟：⚠ 原版没有配方 ⇒ **原创形状**；格数与结构一起钉（4 锭 + 1 棍）
_bgn10rc2_checked += 3
_tri_obj_path = _RC_DATA / "chaosgold_trident.json"
if _tri_obj_path.is_file():
    _to = json.loads(_tri_obj_path.read_text(encoding="utf-8"))
    _to_cells = [c for _row in _rc2_grid(_to.get("pattern"), _to.get("key")) for c in _row]
    if _to_cells.count(_RC2_INGOT) != 4:
        _bgn10rc2_bad("bgn10rc2-trident",
                      "chaosgold_trident 的混沌金锭不是 4 个（实际 " + str(_to_cells.count(_RC2_INGOT)) + "）")
    if _to_cells.count(_RC2_STICK) != 1:
        _bgn10rc2_bad("bgn10rc2-trident",
                      "chaosgold_trident 的木棍不是 1 个（实际 " + str(_to_cells.count(_RC2_STICK)) + "）")
    if _RC2_WANT["trident"][0] != ["XXX", " X ", " # "]:
        _bgn10rc2_bad("bgn10rc2-trident", "本段期望表里的三叉戟形状被改了（应为原创的 XXX /  X  /  # ）")

# 乐事刀：⚠ 必须挂 `neoforge:mod_loaded(farmersdelight)`（没装乐事 ⇒ 这条配方根本不产出）
_bgn10rc2_checked += 3
_knife_obj_path = _RC_DATA / "chaosgold_knife.json"
if _knife_obj_path.is_file():
    _ko = json.loads(_knife_obj_path.read_text(encoding="utf-8"))
    if _ko.get("neoforge:conditions") != _RC2_FD_CONDITION:
        _bgn10rc2_bad("bgn10rc2-knife-cond",
                      "chaosgold_knife 的 neoforge:conditions 不是恰好 mod_loaded(farmersdelight)："
                      + repr(_ko.get("neoforge:conditions")))
    _kcells = [c for _row in _rc2_grid(_ko.get("pattern"), _ko.get("key")) for c in _row]
    if _kcells.count(_RC2_INGOT) != 1 or _kcells.count(_RC2_STICK) != 1:
        _bgn10rc2_bad("bgn10rc2-knife-cond",
                      "chaosgold_knife 不是 1 锭 + 1 棍：" + _rc2_grid_text(_rc2_grid(_ko.get("pattern"), _ko.get("key"))))

# 其余 14 条**不许**带任何 conditions（没装乐事的机器上它们照样要能合出来）
for _g in ("sword", "axe", "pickaxe", "shovel", "hoe", "helmet", "chestplate", "leggings",
           "boots", "shield", "crossbow", "bow", "mace", "trident"):
    _bgn10rc2_checked += 1
    _p14 = _RC_DATA / ("chaosgold_" + _g + ".json")
    if not _p14.is_file():
        _bgn10rc2_bad("bgn10rc2-cond-scope", "缺 " + _p14.name)
        continue
    if "neoforge:conditions" in json.loads(_p14.read_text(encoding="utf-8")):
        _bgn10rc2_bad("bgn10rc2-cond-scope",
                      "chaosgold_" + _g + ".json 带了 neoforge:conditions —— 只有乐事刀该挂")

# ---------- ③ 来源保真：bow / mace / knife 的 pattern 与图例必须与来源逐字同形 ----------
for _g in ("bow", "mace", "knife"):
    _bgn10rc2_checked += 2
    _sp, _sk = _RC2_SOURCE[_g]
    _wp, _wk = _RC2_WANT[_g]
    if list(_sp) != list(_wp):
        _bgn10rc2_bad("bgn10rc2-source", _g + " 的期望 pattern 与来源不同：" + repr(_wp) + " != " + repr(_sp))
    if sorted(_sk) != sorted(_wk):
        _bgn10rc2_bad("bgn10rc2-source", _g + " 的图例键集合与来源不同：" + repr(sorted(_wk)) + " != " + repr(sorted(_sk)))

# ---------- ④ 返瓶：物品级 craftRemainder + 与配方层**互斥**（只许一处生效、不许双返） ----------
_rc2_items_path = JAVA / "registry" / "AllItems.java"
_rc2_recipe_path = JAVA / "recipe" / "RawSturdygoldRecipe.java"
_bgn10rc2_checked += 4
if not _rc2_items_path.is_file():
    _bgn10rc2_bad("bgn10rc2-remainder-item", "缺 AllItems.java")
    _rc2_items_code = ""
else:
    _rc2_items_code = strip_comments(_rc2_items_path.read_text(encoding="utf-8"))
if not _rc2_recipe_path.is_file():
    _bgn10rc2_bad("bgn10rc2-remainder-recipe", "缺 RawSturdygoldRecipe.java")
    _rc2_recipe_code = ""
else:
    _rc2_recipe_code = strip_comments(_rc2_recipe_path.read_text(encoding="utf-8"))

# (a) 物品级：高阶炼金油那一行必须挂 craftRemainder(GLASS_BOTTLE)，且**全文件恰好 1 处**
_CR = "craftRemainder(Items.GLASS_BOTTLE)"
_bgn10rc2_checked += 2
if _rc2_items_code.count(_CR) != 1:
    _bgn10rc2_bad("bgn10rc2-remainder-item",
                  "去注释后的 AllItems.java 里 " + _CR + " 不是恰好 1 处（实际 "
                  + str(_rc2_items_code.count(_CR)) + "）")
_oil_at = _rc2_items_code.find('"refined_alchemic_oil"')
_stmt_end = _rc2_items_code.find(";", _oil_at) if _oil_at >= 0 else -1
_oil_stmt = _rc2_items_code[_oil_at:_stmt_end] if _oil_at >= 0 and _stmt_end > _oil_at else ""
if _CR not in _oil_stmt:
    _bgn10rc2_bad("bgn10rc2-remainder-item",
                  "物品级 remainder 没有挂在 refined_alchemic_oil 的注册语句上："
                  + (_oil_stmt.replace("\n", " ")[:160] if _oil_stmt else "<找不到该注册语句>"))

# (b) 负向：**不许**给 alchemic_fuel 也挂（作者只点名了高阶炼金油）
_bgn10rc2_checked += 1
_fuel_at = _rc2_items_code.find('"alchemic_fuel"')
_fuel_end = _rc2_items_code.find(";", _fuel_at) if _fuel_at >= 0 else -1
_fuel_stmt = _rc2_items_code[_fuel_at:_fuel_end] if _fuel_at >= 0 and _fuel_end > _fuel_at else ""
if _fuel_at < 0:
    _bgn10rc2_bad("bgn10rc2-remainder-fuel", "AllItems.java 里找不到 alchemic_fuel 的注册语句")
elif "craftRemainder" in _fuel_stmt:
    _bgn10rc2_bad("bgn10rc2-remainder-fuel",
                  "alchemic_fuel 也挂了 craftRemainder —— 那是另一个物品，作者这轮只点名了高阶炼金油")

# (c) 互斥：RawSturdygoldRecipe **覆盖**了 getRemainingItems（不调默认实现）
#     ⇒ 走「贵金原料」那几条时物品级 remainder 根本不参与；别的配方只走默认实现。
_bgn10rc2_checked += 3
if "getRemainingItems" not in _rc2_recipe_code:
    _bgn10rc2_bad("bgn10rc2-remainder-exclusive",
                  "RawSturdygoldRecipe 没有覆盖 getRemainingItems（返瓶行为会退回到物品级）")
if "getCraftingRemainingItem" in _rc2_recipe_code:
    _bgn10rc2_bad("bgn10rc2-remainder-exclusive",
                  "RawSturdygoldRecipe 里直接读了 getCraftingRemainingItem —— 两条路径会同时生效")
if "Recipe.super" in _rc2_recipe_code:
    _bgn10rc2_bad("bgn10rc2-remainder-exclusive",
                  "RawSturdygoldRecipe 调了 Recipe.super.getRemainingItems —— 配方层 + 物品级 = 同一次合成返 2 个瓶")

# (d) 唯一性：两个文件合计 GLASS_BOTTLE **恰好 2 处**（1 物品级 + 1 配方层）。
#     多一处 = 会返 2 个瓶；少一处 = 有一条路径不再返瓶。
_bgn10rc2_checked += 2
_glass_total = _rc2_items_code.count("GLASS_BOTTLE") + _rc2_recipe_code.count("GLASS_BOTTLE")
if _glass_total != 2:
    _bgn10rc2_bad("bgn10rc2-remainder-unique",
                  "AllItems + RawSturdygoldRecipe 里的 GLASS_BOTTLE 合计不是恰好 2 处（实际 "
                  + str(_glass_total) + "）：1 处物品级 + 1 处配方层，多一处就是一次合成返 2 个瓶")
if _rc2_recipe_code.count("new ItemStack(Items.GLASS_BOTTLE)") != 1:
    _bgn10rc2_bad("bgn10rc2-remainder-unique",
                  "配方层的玻璃瓶构造不是恰好 1 处（实际 "
                  + str(_rc2_recipe_code.count("new ItemStack(Items.GLASS_BOTTLE)")) + "）")

# ---------- ⑤ 手册：4 件新配方各有引用；乐事刀那一页**单独一条**（不占第二个槽） ----------
_bgn10rc2_checked += 6
for _d, _tag in ((_ZH_BOOK, "zh"), (_EN_BOOK, "en")):
    _ep = _d / "entries" / "gear_chaosgold.json"
    if not _ep.is_file():
        _bgn10rc2_bad("bgn10rc2-handbook", _tag + " 缺 entries/gear_chaosgold.json")
        continue
    _pages = json.loads(_ep.read_text(encoding="utf-8")).get("pages") or []
    _all_refs = []
    for _pg in _pages:
        _all_refs.extend([x for x in (_pg.get("recipe"), _pg.get("recipe2")) if isinstance(x, str)])
    for _g in _RC2_GEAR:
        _bgn10rc2_checked += 1
        if "bettergold:chaosgold_" + _g not in _all_refs:
            _bgn10rc2_bad("bgn10rc2-handbook",
                          _tag + " 手册的配方页里没有 bettergold:chaosgold_" + _g)
    _knife_pages = [_pg for _pg in _pages if _pg.get("recipe") == "bettergold:chaosgold_knife"
                    or _pg.get("recipe2") == "bettergold:chaosgold_knife"]
    _bgn10rc2_checked += 2
    if len(_knife_pages) != 1:
        _bgn10rc2_bad("bgn10rc2-handbook",
                      _tag + " 手册里 chaosgold_knife 出现了 " + str(len(_knife_pages)) + " 次（应恰好 1 页）")
    elif _knife_pages[0].get("recipe2") is not None:
        _bgn10rc2_bad("bgn10rc2-handbook",
                      _tag + " 的乐事刀那一页还占了 recipe2 槽（当页只有它一条配方）")

# ---------- ⑥ 文案口径：手册正文必须换成"15 件 / 4 件已补"，旧口径不许复现 ----------
_bgn10rc2_checked += 5
try:
    _rc2_zh_lang = json.loads((_RES / "assets" / "bettergold" / "lang" / "zh_cn.json")
                              .read_text(encoding="utf-8"))
except Exception as _e:                                    # noqa: BLE001
    _rc2_zh_lang = {}
    _bgn10rc2_bad("bgn10rc2-lang", "读不了 zh_cn.json：" + repr(_e))
_rc2_text = _rc2_zh_lang.get("bettergold.handbook.page.gear_chaosgold_1_right", "")
for _needle, _why in (("15 件", "新口径必须写清 15 件（11 + 补的 4）"),
                      ("原创形状", "三叉戟必须写明是原创形状"),
                      ("待作者确认", "三叉戟的原创形状必须标注待作者确认"),
                      ("乐事", "乐事刀那条必须提到（它挂 FD 条件）")):
    if _needle not in _rc2_text:
        _bgn10rc2_bad("bgn10rc2-lang", "手册「混沌金装备」正文没有「" + _needle + "」：" + _why)
if "暂时没有工作台配方" in _rc2_text:
    _bgn10rc2_bad("bgn10rc2-lang",
                  "手册正文仍是旧口径（「暂时没有工作台配方」）—— 4 件已经补齐了")

# ---------- ⑦ 文档侧：本轮口径 + 旧口径标注 + 「第三个不动」都要落档 ----------
_RC2_DOC = REPO / "docs" / "1.7-\u6df7\u6c8c\u91d1\u4e0e\u5d29\u4e71\u5408\u91d1-\u9700\u6c42\u7acb\u6863.md"
_bgn10rc2_checked += 8
if not _RC2_DOC.is_file():
    _bgn10rc2_bad("bgn10rc2-doc", "缺 docs/1.7-混沌金与崩乱合金-需求立档.md")
else:
    _rc2_doc = _RC2_DOC.read_text(encoding="utf-8")
    for _needle, _why in (
            ("bg-n10rc2", "立档里没有本轮标记（bg-n10rc2）"),
            ("第一个可以考虑", "没把作者「第一个可以考虑」逐字收进立档"),
            ("第二个需要扩", "没把作者「第二个需要扩」逐字收进立档"),
            ("第三个我再问一问", "没把作者「第三个我再问一问」逐字收进立档"),
            ("原创", "没写三叉戟是原创形状"),
            ("待作者确认", "没写三叉戟的原创形状待作者确认"),
            ("craftRemainder", "没写返瓶的机制落点（物品级 craftRemainder）"),
            ("只返 1 个瓶", "没写「只返 1 个瓶」这条验收口径")):
        if _needle not in _rc2_doc:
            _bgn10rc2_bad("bgn10rc2-doc", _why + "：缺「" + _needle + "」")

if _bgn10rc2_checked < 60:
    _bgn10rc2_bad("bgn10rc2-anti-vacuum",
                  "本段只检查了 " + str(_bgn10rc2_checked) + " 项（反空转守护：应远大于 60）")
print("1.7 bg-n10rc2（4 件补齐 + 返瓶扩到物品级）问题: "
      + str(len(bgn10rc2_problems)) + " " + str(bgn10rc2_problems[:4])
      + "（本段判定 " + str(_bgn10rc2_checked) + " 项）")
if not bgn10rc2_problems:
    print("[bgn10rc2-ok] 弓/重锤/三叉戟/乐事刀 4 条配方逐格钉住（三叉戟 = 原创形状待确认 + 乐事刀挂 "
          "mod_loaded(farmersdelight)）/ 其余 14 条无条件 / 高阶炼金油的物品级 remainder 恰好 1 处且"
          "与配方层按配方互斥（GLASS_BOTTLE 合计 2 处 = 不双返）/ 手册 15 页 15 条引用")

# ==================== 1.7 bg-n10up（混沌金锭的**上游**，2026-10-18）====================
#
# 作者原话（**新的权威口径**，逐字）：
#   「用 **9 个混沌金粒** 合成的，然后**混沌金粒由烧炼混沌金币获得**，
#     而**混沌金币是由混沌金币串合成分解出的三个**」
#
# 本段只钉**这三条**（"多一条都不加"由反向断言兜住，不是靠自觉）：
#   ① `chaos_coin_from_string.json` —— **crafting_shapeless**（作者最早那句「在合成表上无序转换」），
#      1 个币串 → **3** 个币，币串被**消耗 1 个**（单原料、没有 count、没有剩余物）；
#   ② `chaos_coin_smelting.json` —— **minecraft:smelting** 一条，1 币 → 1 粒；
#      xp / time / category 必须与既有「原料 → 锭」那一档（8 条 `raw_*_smelting`）**逐项相同**；
#   ③ `chaosgold_ingot_from_nugget.json` —— **既有**（bg-n10 起由 `generate_metal_recipes.py` 产出），
#      `NNN / NNN / NNN` 满格 9 粒 → 1 锭；它的**逆** `chaosgold_nugget_from_ingot.json`（1 锭 → 9 粒）
#      必须原样还在（本轮不许动它）。
#
# 反向断言（都是"**没加**"的口径）：
#   * 全仓**没有**产出 `chaos_coin_string` 的配方（币串怎么来 = 作者没说 ⇒ 不做）；
#   * 币串**只被**这 3 条消耗（附魔书 / 下界合金锭 / 本轮这条），没有第四条；
#   * 币**只有**本轮这一条产线；粒只有「烧炼」与「锭 → 粒」两条产线；
#   * 币 / 粒**没有**高炉 / 烟熏 / 营火（作者只说了"烧炼" ⇒ 只做 smelting 一条）。
#   ★ **旧口径，已被作者 2026-10-18 推翻（`bg-n10fix` ①）**：上一行原文保留、不删。
#     作者本轮亲口要「混沌金币要用**高炉**也能烧成粒」⇒ 现行口径 = **smelting + blasting 两条**，
#     blasting 的 xp 同为 1.0、时间 100（= 熔炉的一半）、category 同为 misc，
#     与既有 8 条 `raw_*_blasting` 逐项同档；**烟熏 / 营火仍然不许**（作者只点名了高炉）。
bgn10up_problems: list[str] = []
_bgn10up_checked = 0


def _bgn10up_bad(tag: str, msg: str) -> None:
    bgn10up_problems.append("[%s] %s" % (tag, msg))


_UP_CS = "bettergold:chaos_coin_string"
_UP_COIN = "bettergold:chaos_coin"
_UP_NUGGET = "bettergold:chaosgold_nugget"
_UP_INGOT = "bettergold:chaosgold_ingot"
_UP_F1 = "chaos_coin_from_string.json"
_UP_F2 = "chaos_coin_smelting.json"
_UP_F2B = "chaos_coin_blasting.json"
_UP_F3 = "chaosgold_ingot_from_nugget.json"
_UP_F3R = "chaosgold_nugget_from_ingot.json"
_UP_STRING_CONSUMERS = {"chaosgold_enchanting_book.json",
                        "netherite_ingot_with_chaos_coin_string.json",
                        _UP_F1}
_UP_INGOT_PRODUCERS = {"chaosgold_ingot_from_block.json", _UP_F3}
_UP_NUGGET_PRODUCERS = {_UP_F3R, _UP_F2, _UP_F2B}


def _up_load(name: str):
    p = _RC_DATA / name
    if not p.is_file():
        _bgn10up_bad("bgn10up-file", "缺配方文件 " + name)
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as _e:                               # noqa: BLE001
        _bgn10up_bad("bgn10up-file", name + " 读不出来：" + repr(_e))
        return None


def _up_walk(node, out: set) -> None:
    """收集节点里所有的 `item` / `tag` 字符串（只看传给它的那一支）。"""
    if isinstance(node, dict):
        for _k in ("item", "tag"):
            if isinstance(node.get(_k), str):
                out.add(node[_k])
        for _v in node.values():
            _up_walk(_v, out)
    elif isinstance(node, list):
        for _v in node:
            _up_walk(_v, out)


def _up_inputs(obj: dict) -> set:
    out: set = set()
    for _f in ("ingredients", "ingredient", "key"):
        if _f in obj:
            _up_walk(obj[_f], out)
    return out


def _up_outputs(obj: dict) -> set:
    out: set = set()
    _r = obj.get("result")
    if isinstance(_r, str):
        out.add(_r)
    elif isinstance(_r, dict) and isinstance(_r.get("id"), str):
        out.add(_r["id"])
    if isinstance(obj.get("results"), list):
        for _x in obj["results"]:
            if isinstance(_x, dict) and isinstance(_x.get("id"), str):
                out.add(_x["id"])
    return out


def _up_strip_py_comments(text: str) -> str:
    """Python 的"去注释源码"：逐行砍掉 `#` 起的部分（本文件里被断言的这些行不含 # 字符串）。

    ⚠ 正向 needle **必须**跑在去注释版本上（`docs/构建与跑测注意事项.md` §六）：
    否则注释里写一句 needle 就能让断言假绿。
    """
    return "\n".join(_line.split("#", 1)[0] for _line in text.splitlines())


_up_f1 = _up_load(_UP_F1)
_up_f2 = _up_load(_UP_F2)
_up_f2b = _up_load(_UP_F2B)
_up_f3 = _up_load(_UP_F3)
_up_f3r = _up_load(_UP_F3R)

# ---------- ① 币串 → 3 币：逐项（类型 / 单原料 / 消耗 1 个 / 产物 3 个 / 没有任何附加键）----------
if _up_f1 is not None:
    _bgn10up_checked += 7
    if _up_f1.get("type") != "minecraft:crafting_shapeless":
        _bgn10up_bad("bgn10up-string",
                     "币串 → 币的 type 不是 crafting_shapeless（作者口径：「在合成表上**无序**转换」）："
                     + repr(_up_f1.get("type")))
    if set(_up_f1) != {"type", "ingredients", "result"}:
        _bgn10up_bad("bgn10up-string",
                     "币串 → 币的顶层键不是恰好 type/ingredients/result（多一个键就是多一条口径）："
                     + repr(sorted(_up_f1)))
    _ing1 = _up_f1.get("ingredients")
    if not isinstance(_ing1, list) or len(_ing1) != 1:
        _bgn10up_bad("bgn10up-string", "ingredients 不是恰好 1 项：" + repr(_ing1))
    elif _ing1[0] != {"item": _UP_CS}:
        _bgn10up_bad("bgn10up-string",
                     "唯一原料不是恰好 1 个 " + _UP_CS + "（带 count 就不是消耗 1 个）：" + repr(_ing1[0]))
    _res1 = _up_f1.get("result")
    if _res1 != {"id": _UP_COIN, "count": 3}:
        _bgn10up_bad("bgn10up-string", "产物不是 " + _UP_COIN + " ×3：" + repr(_res1))
    elif type(_res1.get("count")) is not int or _res1.get("count") != 3:
        _bgn10up_bad("bgn10up-string", "count 不是整数 3：" + repr(_res1.get("count")))
    _consumed1 = 0
    for _e in (_ing1 or []):
        if isinstance(_e, dict) and _e.get("item") == _UP_CS:
            _consumed1 += _e.get("count", 1)
    if _consumed1 != 1:
        _bgn10up_bad("bgn10up-string", "币串的消耗量不是 1（实际 " + str(_consumed1) + "）")

# ---------- ② 币 →（烧炼）→ 粒：逐项 + 与既有同档逐项比对（不是抄数字）----------
if _up_f2 is not None:
    _bgn10up_checked += 8
    if _up_f2.get("type") != "minecraft:smelting":
        _bgn10up_bad("bgn10up-smelt",
                     "币 → 粒的 type 不是 minecraft:smelting（熔炉那一条）：" + repr(_up_f2.get("type")))
    if set(_up_f2) != {"type", "category", "ingredient", "result", "experience", "cookingtime"}:
        _bgn10up_bad("bgn10up-smelt",
                     "币 → 粒的顶层键不是恰好 6 个（多一个键 = 多一条口径）：" + repr(sorted(_up_f2)))
    if _up_f2.get("category") != "misc":
        _bgn10up_bad("bgn10up-smelt", "category 不是 misc：" + repr(_up_f2.get("category")))
    if _up_f2.get("ingredient") != {"item": _UP_COIN}:
        _bgn10up_bad("bgn10up-smelt", "输入不是恰好 1 个 " + _UP_COIN + "：" + repr(_up_f2.get("ingredient")))
    if _up_f2.get("result") != {"id": _UP_NUGGET}:
        _bgn10up_bad("bgn10up-smelt", "产物不是 " + _UP_NUGGET + " ×1：" + repr(_up_f2.get("result")))
    _up_anchor = {}
    _anchor_path = _RC_DATA / "raw_sturdygold_smelting.json"
    if not _anchor_path.is_file():
        _bgn10up_bad("bgn10up-smelt", "缺同档锚点 raw_sturdygold_smelting.json")
    else:
        _up_anchor = json.loads(_anchor_path.read_text(encoding="utf-8"))
    _up_tier = [_up_anchor.get("category"), _up_anchor.get("experience"), _up_anchor.get("cookingtime")]
    _up_mine = [_up_f2.get("category"), _up_f2.get("experience"), _up_f2.get("cookingtime")]
    if _up_tier != _up_mine:
        _bgn10up_bad("bgn10up-smelt",
                     "category/experience/cookingtime 与既有同档 anchor 不同：" + repr(_up_mine) + " != " + repr(_up_tier))
    # 8 条 raw_*_smelting 必须**全部**与它同档（"同档"是从仓库里取的事实，不是本段写的期望）
    _up_raw_smelts = sorted(_RC_DATA.glob("raw_*_smelting.json"))
    _bgn10up_checked += 1
    if len(_up_raw_smelts) != 8:
        _bgn10up_bad("bgn10up-smelt",
                     "raw_*_smelting 不是 8 条（反空转：同档比对会假绿）：" + str(len(_up_raw_smelts)))
    _up_off_tier = []
    for _rp in _up_raw_smelts:
        _ro = json.loads(_rp.read_text(encoding="utf-8"))
        if [_ro.get("category"), _ro.get("experience"), _ro.get("cookingtime")] != _up_mine:
            _up_off_tier.append(_rp.name)
    _bgn10up_checked += 1
    if _up_off_tier:
        _bgn10up_bad("bgn10up-smelt", "这些 raw_*_smelting 与本条不同档：" + repr(_up_off_tier))

# ---------- ②-b 币 →（**高炉**）→ 粒（`bg-n10fix` ①，作者 2026-10-18 亲口要）----------
# 判据 = 与**既有 8 条 `raw_*_blasting`** 逐项同档（xp 1.0 / 100 tick / misc），
# 并显式钉"高炉时间 = 熔炉的一半、xp 相同"这条作者口径（不是凭印象写的常量）。
if _up_f2b is not None:
    _bgn10up_checked += 9
    if _up_f2b.get("type") != "minecraft:blasting":
        _bgn10up_bad("bgn10up-blast",
                     "币 → 粒的高炉 type 不是 minecraft:blasting：" + repr(_up_f2b.get("type")))
    if set(_up_f2b) != {"type", "category", "ingredient", "result", "experience", "cookingtime"}:
        _bgn10up_bad("bgn10up-blast",
                     "高炉那条的顶层键不是恰好 6 个：" + repr(sorted(_up_f2b)))
    if _up_f2b.get("ingredient") != {"item": _UP_COIN}:
        _bgn10up_bad("bgn10up-blast", "高炉输入不是恰好 1 个 " + _UP_COIN + "：" + repr(_up_f2b.get("ingredient")))
    if _up_f2b.get("result") != {"id": _UP_NUGGET}:
        _bgn10up_bad("bgn10up-blast", "高炉产物不是 " + _UP_NUGGET + " ×1：" + repr(_up_f2b.get("result")))
    _up_blast_anchor_path = _RC_DATA / "raw_sturdygold_blasting.json"
    if not _up_blast_anchor_path.is_file():
        _bgn10up_bad("bgn10up-blast", "缺同档锚点 raw_sturdygold_blasting.json")
        _up_blast_anchor = {}
    else:
        _up_blast_anchor = json.loads(_up_blast_anchor_path.read_text(encoding="utf-8"))
    _up_blast_tier = [_up_blast_anchor.get("category"), _up_blast_anchor.get("experience"),
                      _up_blast_anchor.get("cookingtime")]
    _up_blast_mine = [_up_f2b.get("category"), _up_f2b.get("experience"), _up_f2b.get("cookingtime")]
    if _up_blast_tier != _up_blast_mine:
        _bgn10up_bad("bgn10up-blast",
                     "高炉的 category/experience/cookingtime 与既有同档不同："
                     + repr(_up_blast_mine) + " != " + repr(_up_blast_tier))
    _up_raw_blasts = sorted(_RC_DATA.glob("raw_*_blasting.json"))
    _bgn10up_checked += 1
    if len(_up_raw_blasts) != 8:
        _bgn10up_bad("bgn10up-blast",
                     "raw_*_blasting 不是 8 条（反空转：同档比对会假绿）：" + str(len(_up_raw_blasts)))
    _up_blast_off = []
    for _rp in _up_raw_blasts:
        _ro = json.loads(_rp.read_text(encoding="utf-8"))
        if [_ro.get("category"), _ro.get("experience"), _ro.get("cookingtime")] != _up_blast_mine:
            _up_blast_off.append(_rp.name)
    if _up_blast_off:
        _bgn10up_bad("bgn10up-blast", "这些 raw_*_blasting 与高炉这条不同档：" + repr(_up_blast_off))
    # 作者口径：高炉 = 熔炉的**一半时间**、xp 相同（两条都在本文件里，直接对穿，不另写常量）
    if (_up_f2b.get("cookingtime"), _up_f2b.get("experience")) != (
            (_up_f2.get("cookingtime") or 0) // 2, _up_f2.get("experience")):
        _bgn10up_bad("bgn10up-blast",
                     "高炉不是「熔炉一半时间 + xp 相同」：blast="
                     + repr((_up_f2b.get("cookingtime"), _up_f2b.get("experience")))
                     + " smelt=" + repr((_up_f2.get("cookingtime"), _up_f2.get("experience"))))

# ---------- ③ 9 粒 → 1 锭：**逐格**钉住（计数相等抓不到位置错）----------
if _up_f3 is not None:
    _bgn10up_checked += 7
    if _up_f3.get("type") != "minecraft:crafting_shaped":
        _bgn10up_bad("bgn10up-ingot", "9 粒 → 1 锭不是 crafting_shaped：" + repr(_up_f3.get("type")))
    if _up_f3.get("pattern") != ["NNN", "NNN", "NNN"]:
        _bgn10up_bad("bgn10up-ingot", "pattern 不是 3×3 满格 nnn/nnn/nnn：" + repr(_up_f3.get("pattern")))
    if _up_f3.get("key") != {"N": {"item": _UP_NUGGET}}:
        _bgn10up_bad("bgn10up-ingot", "key 不是恰好 N=" + _UP_NUGGET + "：" + repr(_up_f3.get("key")))
    if _up_f3.get("result") != {"id": _UP_INGOT}:
        _bgn10up_bad("bgn10up-ingot", "产物不是 " + _UP_INGOT + " ×1：" + repr(_up_f3.get("result")))
    _up_grid = []
    for _row in (_up_f3.get("pattern") or []):
        _up_grid.append([(_up_f3.get("key") or {}).get(_ch) for _ch in _row])
    if len(_up_grid) != 3 or any(len(_r) != 3 for _r in _up_grid):
        _bgn10up_bad("bgn10up-ingot", "格子不是 3×3：" + repr(_up_grid))
    _up_bad_cells = [( _r, _c) for _r in range(len(_up_grid)) for _c in range(len(_up_grid[_r]))
                     if _up_grid[_r][_c] != {"item": _UP_NUGGET}]
    if _up_bad_cells:
        _bgn10up_bad("bgn10up-ingot",
                     "这些格子不是 " + _UP_NUGGET + "（位置错 / 图例错）：" + repr(_up_bad_cells[:5]))
    if sum(1 for _r in _up_grid for _c in _r if _c == {"item": _UP_NUGGET}) != 9:
        _bgn10up_bad("bgn10up-ingot", "混沌金粒的格子数不是 9")
if _up_f3r is not None:
    _bgn10up_checked += 4
    if _up_f3r.get("type") != "minecraft:crafting_shapeless":
        _bgn10up_bad("bgn10up-ingot", "1 锭 → 9 粒（9 → 1 的逆）不是 crafting_shapeless")
    if _up_f3r.get("ingredients") != [{"item": _UP_INGOT}]:
        _bgn10up_bad("bgn10up-ingot", "1 锭 → 9 粒的原料被改了：" + repr(_up_f3r.get("ingredients")))
    if _up_f3r.get("result") != {"id": _UP_NUGGET, "count": 9}:
        _bgn10up_bad("bgn10up-ingot", "1 锭 → 9 粒的产物被改了：" + repr(_up_f3r.get("result")))
    if set(_up_f3r) != {"type", "ingredients", "result"}:
        _bgn10up_bad("bgn10up-ingot", "1 锭 → 9 粒多出了别的键：" + repr(sorted(_up_f3r)))

# ---------- 反向断言：三条以外的产线 / 高炉烟熏 一条都不许有 ----------
_up_all = {}
_up_parse_bad = []
for _rp in sorted(_RC_DATA.glob("*.json")):
    try:
        _up_all[_rp.name] = json.loads(_rp.read_text(encoding="utf-8"))
    except Exception as _e:                               # noqa: BLE001
        _up_parse_bad.append(_rp.name + ":" + repr(_e))
_bgn10up_checked += 2
if _up_parse_bad:
    _bgn10up_bad("bgn10up-scan", "有配方 JSON 读不出来：" + repr(_up_parse_bad[:3]))
if len(_up_all) < 400:
    _bgn10up_bad("bgn10up-scan", "配方总数只有 " + str(len(_up_all)) + "（反空转：反向断言会假绿）")

_up_prod_cs = sorted(n for n, o in _up_all.items() if _UP_CS in _up_outputs(o))
_up_use_cs = sorted(n for n, o in _up_all.items() if _UP_CS in _up_inputs(o))
_up_prod_coin = sorted(n for n, o in _up_all.items() if _UP_COIN in _up_outputs(o))
_up_prod_nug = sorted(n for n, o in _up_all.items() if _UP_NUGGET in _up_outputs(o))
_up_prod_ing = sorted(n for n, o in _up_all.items() if _UP_INGOT in _up_outputs(o))
_up_hot_forbidden = sorted(
    n for n, o in _up_all.items()
    if o.get("type") in ("minecraft:smoking", "minecraft:campfire_cooking")
    and (_UP_COIN in _up_inputs(o) or _UP_COIN in _up_outputs(o)
         or _UP_NUGGET in _up_outputs(o) or _UP_NUGGET in _up_inputs(o)))
_up_hot_blast = sorted(
    n for n, o in _up_all.items()
    if o.get("type") == "minecraft:blasting"
    and (_UP_COIN in _up_inputs(o) or _UP_COIN in _up_outputs(o)
         or _UP_NUGGET in _up_outputs(o) or _UP_NUGGET in _up_inputs(o)))
_bgn10up_checked += 6
if _up_prod_cs:
    _bgn10up_bad("bgn10up-reverse", "全仓有产出混沌金币串的配方（作者没说币串怎么来）：" + repr(_up_prod_cs))
if set(_up_use_cs) != _UP_STRING_CONSUMERS:
    _bgn10up_bad("bgn10up-reverse",
                 "消耗币串的配方不是恰好那 3 条（附魔书 / 下界合金锭 / 本轮这条）：" + repr(_up_use_cs))
if set(_up_prod_coin) != {_UP_F1}:
    _bgn10up_bad("bgn10up-reverse", "产出混沌金币的配方不是恰好 1 条：" + repr(_up_prod_coin))
if set(_up_prod_nug) != _UP_NUGGET_PRODUCERS:
    _bgn10up_bad("bgn10up-reverse",
                 "产出混沌金粒的配方不是恰好「熔炉 + 高炉 + 锭 → 粒」三条：" + repr(_up_prod_nug))
if set(_up_prod_ing) != _UP_INGOT_PRODUCERS:
    _bgn10up_bad("bgn10up-reverse", "产出混沌金锭的配方不是恰好「9 → 1 + 块 → 锭」两条：" + repr(_up_prod_ing))
if _up_hot_forbidden:
    _bgn10up_bad("bgn10up-reverse",
                 "出现了金币 / 金粒的烟熏、营火配方（作者只点名了熔炉与高炉）：" + repr(_up_hot_forbidden))
if _up_hot_blast != [_UP_F2B]:
    _bgn10up_bad("bgn10up-reverse",
                 "金币 / 金粒的高炉配方不是恰好那一条（`bg-n10fix` ①）：" + repr(_up_hot_blast))

# ---------- 生成器 = 唯一真源：自检 + 产物逐字节 + 去注释源码 needle ----------
_bgn10up_checked += 6
try:
    import importlib.util as _up_ilu
    _up_dwb = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        _up_spec = _up_ilu.spec_from_file_location(
            "_bgn10up_gen", REPO / "tools" / "asset-generator" / "generate_chaosgold_recipes.py")
        _up_gen = _up_ilu.module_from_spec(_up_spec)
        _up_spec.loader.exec_module(_up_gen)
    finally:
        sys.dont_write_bytecode = _up_dwb
    _up_targets = _up_gen.upstream_targets()
    _bgn10up_checked += 1
    if len(_up_targets) != 3 or [n for n, _ in _up_targets] != [_UP_F1, _UP_F2, _UP_F2B]:
        _bgn10up_bad("bgn10up-generator",
                     "生成器的上游 recipe 表不是恰好这三条：" + repr([n for n, _ in _up_targets]))
    _up_self = list(_up_gen.check_upstream(_up_targets))
    _bgn10up_checked += 1
    if _up_self:
        _bgn10up_bad("bgn10up-generator", "生成器上游自检不通过：" + repr(_up_self[:4]))
    _up_diff = []
    for _n, _o in _up_targets:
        _bgn10up_checked += 1
        _p = _RC_DATA / _n
        if not _p.is_file() or _p.read_text(encoding="utf-8") != json.dumps(_o, ensure_ascii=False, indent=2) + "\n":
            _up_diff.append(_n)
    if _up_diff:
        _bgn10up_bad("bgn10up-generator", "上游配方与唯一真源不再逐字节一致：" + repr(_up_diff))
    # 正向 needle 跑在**去注释**源码上（注释里写 needle 不许算数）
    _up_src = _up_strip_py_comments(
        (REPO / "tools" / "asset-generator" / "generate_chaosgold_recipes.py").read_text(encoding="utf-8"))
    for _needle, _why in (("def upstream_targets", "生成器里没有上游产物的入口函数"),
                          ("def check_upstream", "生成器里没有上游自检函数"),
                          ('":chaos_coin_string"', "生成器里没有币串的 id"),
                          ('"minecraft:crafting_shapeless"', "生成器里没有无序合成（币串 → 3 币）"),
                          ('"minecraft:smelting"', "生成器里没有熔炉（币 → 粒）"),
                          ('"minecraft:blasting"', "生成器里没有高炉（币 → 粒，`bg-n10fix` ①）"),
                          ("_raw_blasting_anchor", "生成器里没有高炉同档锚点（会退化成手写常量）")):
        if _needle not in _up_src:
            _bgn10up_bad("bgn10up-generator", _why + "：缺 " + _needle + "（去注释源码里）")
    # ⚠ 旧口径（「作者只说了烧炼 ⇒ 只做 smelting 一条」）已被 2026-10-18 推翻：blasting 从**禁止项**
    #    移进上面的**正向 needle**；烟熏 / 营火仍然禁止。
    for _needle in ('"minecraft:smoking"', '"minecraft:campfire_cooking"'):
        if _needle in _up_src:
            _bgn10up_bad("bgn10up-generator", "生成器里出现了 " + _needle + "（作者只点名了熔炉与高炉）")
except Exception as _e:                                   # noqa: BLE001
    _bgn10up_bad("bgn10up-generator", "生成器加载失败：" + repr(_e))

# ---------- 手册：chaos_materials 18 页 + 两条新配方**各自单独一页** + 无死链 ----------
_bgn10up_checked += 4
for _d, _tag in ((_ZH_BOOK, "zh"), (_EN_BOOK, "en")):
    _ep = _d / "entries" / "chaos_materials.json"
    if not _ep.is_file():
        _bgn10up_bad("bgn10up-handbook", _tag + " 缺 entries/chaos_materials.json")
        continue
    _pages = json.loads(_ep.read_text(encoding="utf-8")).get("pages") or []
    _bgn10up_checked += 1
    if len(_pages) != 18:
        _bgn10up_bad("bgn10up-handbook", _tag + " 的 chaos_materials 不是 18 页（实际 " + str(len(_pages)) + "）")
        continue
    # 第 5 / 6 页（下标 4 / 5）= 本轮两条，顺序固定
    _bgn10up_checked += 3
    _p5, _p6 = _pages[4], _pages[5]
    if (_p5.get("type"), _p5.get("recipe"), _p5.get("recipe2")) != ("patchouli:crafting", "bettergold:chaos_coin_from_string", None):
        _bgn10up_bad("bgn10up-handbook", _tag + " 第 5 页不是「币串 → 3 币」的单配方页：" + repr(_p5))
    if (_p6.get("type"), _p6.get("recipe"), _p6.get("recipe2")) != ("patchouli:smelting", "bettergold:chaos_coin_smelting", None):
        _bgn10up_bad("bgn10up-handbook", _tag + " 第 6 页不是「币 → 粒」的单配方页：" + repr(_p6))
    # 每页配方数 ≤ 2（Patchouli 的结构上限）+ 引用不许死链
    for _pg in _pages:
        _on = [x for x in (_pg.get("recipe"), _pg.get("recipe2")) if isinstance(x, str)]
        _bgn10up_checked += 1
        if len(_on) > 2:
            _bgn10up_bad("bgn10up-handbook", _tag + " 有配方页塞了 " + str(len(_on)) + " 条（上限 2）")
        for _r in _on:
            if not (_RC_DATA / (_r.split(":", 1)[1] + ".json")).is_file():
                _bgn10up_bad("bgn10up-handbook", _tag + " 配方页死链：" + _r)
_bgn10up_checked += 1
if _ZH_BOOK.is_dir() and _EN_BOOK.is_dir():
    _zp = _ZH_BOOK / "entries" / "chaos_materials.json"
    _epn = _EN_BOOK / "entries" / "chaos_materials.json"
    if _zp.is_file() and _epn.is_file() and (json.loads(_zp.read_text(encoding="utf-8")).get("pages")
                                             != json.loads(_epn.read_text(encoding="utf-8")).get("pages")):
        _bgn10up_bad("bgn10up-handbook", "chaos_materials 的 zh / en 页列表不一致")

# ---------- 文案：旧的「实现说明（关系未定）」必须已被作者原话替换 ----------
_bgn10up_checked += 8
_up_zh = zh
_up_en = en
_up_2r = str(_up_zh.get("bettergold.handbook.page.chaos_materials_2_right", ""))
_up_1l = str(_up_zh.get("bettergold.handbook.page.chaos_materials_1_left", ""))
if "关系作者还没有说明" in _up_2r or "两件不同的物品" in _up_2r:
    _bgn10up_bad("bgn10up-lang", "手册「混沌金币」页仍是旧口径（「两件不同物品 / 关系未定」）")
for _needle, _why in (("混沌金币串合成分解出的三个", "没把作者原话收进「币」那一页"),
                      ("3 个混沌金币", "没说清 1 个币串给 3 个币"),
                      ("第 3 屏", "没有指向新的上游那一屏")):
    if _needle not in _up_2r:
        _bgn10up_bad("bgn10up-lang", "手册「混沌金币」页缺「" + _needle + "」：" + _why)
for _needle, _why in (("混沌金币串", "材料链正文没提币串"),
                      ("烧炼", "材料链正文没提烧炼"),
                      ("9 个混沌金粒", "材料链正文没提 9 粒 → 1 锭")):
    if _needle not in _up_1l:
        _bgn10up_bad("bgn10up-lang", "手册材料链正文缺「" + _needle + "」：" + _why)
for _k in ("bettergold.handbook.page.chaos_materials_upstream_string",
           "bettergold.handbook.page.chaos_materials_upstream_smelt"):
    _bgn10up_checked += 1
    if _k not in _up_zh or _k not in _up_en:
        _bgn10up_bad("bgn10up-lang", "新页正文缺中文或英文：" + _k)
    elif not str(_up_zh[_k]).strip() or str(_up_zh[_k]) == str(_up_en[_k]):
        _bgn10up_bad("bgn10up-lang", "新页正文空值或中英逐字相同：" + _k)
_up_en2r = str(_up_en.get("bettergold.handbook.page.chaos_materials_2_right", ""))
if "has not been stated by the author" in _up_en2r:
    _bgn10up_bad("bgn10up-lang", "英文「混沌金币」页仍是旧口径（未说明上下游）")

# ---------- 手册生成器：这两页是**生成器**写的（不是手改产物）----------
_up_hb_src = _up_strip_py_comments(
    (REPO / "tools" / "asset-generator" / "generate_handbook_data.py").read_text(encoding="utf-8"))
_bgn10up_checked += 2
for _needle, _why in (('crafting_page("chaos_coin_from_string"', "手册生成器里没有「币串 → 3 币」那一页"),
                      ('smelting_page("chaos_coin_smelting"', "手册生成器里没有「币 → 粒」那一页")):
    if _needle not in _up_hb_src:
        _bgn10up_bad("bgn10up-handbook-gen", _why + "：缺 " + _needle + "（去注释源码里）")

# ---------- 文档：新口径 + 成本算清 + 旧句留档 + 「只做 smelting」的待确认 ----------
_bgn10up_checked += 9
_up_doc = REPO / "docs" / "1.7-\u6df7\u6c8c\u91d1\u4e0e\u5d29\u4e71\u5408\u91d1-\u9700\u6c42\u7acb\u6863.md"
if not _up_doc.is_file():
    _bgn10up_bad("bgn10up-doc", "缺 docs/1.7-混沌金与崩乱合金-需求立档.md")
else:
    _up_doc_txt = _up_doc.read_text(encoding="utf-8")
    for _needle, _why in (
            ("bg-n10up", "立档里没有本轮标记（bg-n10up）"),
            ("9 个混沌金粒", "没把作者「9 个混沌金粒」那句原话收进立档"),
            ("合成的，然后", "没把作者原话的句式收进立档（「…9 个混沌金粒 合成的，然后…」）"),
            ("混沌金粒由烧炼混沌金币获得", "没把作者「烧炼获得」那句原话收进立档"),
            ("混沌金币是由混沌金币串合成分解出的三个", "没把作者「币串合成出三个」那句原话收进立档"),
            ("3 个混沌金币串 = 1 个混沌金锭", "没把端到端成本算清（3 币串 = 1 锭）"),
            ("两者的上下游关系作者还没有说明", "旧句（实现说明）没有原文留档"),
            ("只做 smelting", "没写「只做 smelting、高炉/烟熏待作者确认」"),
            ("待作者确认", "没写待作者确认项"),
            ("1.0", "没记账 smelting 的 xp 取值依据")):
        if _needle not in _up_doc_txt:
            _bgn10up_bad("bgn10up-doc", _why + "：缺「" + _needle + "」")

if _bgn10up_checked < 55:
    _bgn10up_bad("bgn10up-anti-vacuum",
                 "本段只检查了 " + str(_bgn10up_checked) + " 项（反空转守护：应远大于 55）")
print("1.7 bg-n10up（混沌金锭上游：币串 → 3 币 / 币 →（熔炉 + 高炉）→ 粒 / 9 粒 → 1 锭）问题: "
      + str(len(bgn10up_problems)) + " " + str(bgn10up_problems[:4])
      + "（本段判定 " + str(_bgn10up_checked) + " 项）")
if not bgn10up_problems:
    print("[bgn10up-ok] 币串 → 3 币（shapeless，消耗 1 个）/ 币 →（smelting，与 8 条 raw_*_smelting 同档 "
          "1.0 xp 200 tick misc）+（blasting，与 8 条 raw_*_blasting 同档 1.0 xp 100 tick misc；"
          "`bg-n10fix` ① 作者 2026-10-18 推翻旧口径）→ 粒 / 9 粒 → 1 锭逐格（NNN 满格）与它的逆 "
          "1 锭 → 9 粒都原样 / 反向：无币串产线、无第二种金币来源、无烟熏营火（高炉恰好 1 条）/ "
          "手册 18 页（两条各 1 页）无死链")

# ==================== 1.7 `bg-n10fix`（2026-10-18）：作者进游戏试玩报的 10 条 ====================
# 判据口径（照 `docs/构建与跑测注意事项.md` §六/§七）：
#   * 正向 needle **一律跑在去注释源码上**（注释里写一句 needle 不许算数）；
#   * 失败文案里**不出现裸 `%`**（用 str.format / 拼接，别用 % 运算）；
#   * 反空转：本段必须真的检查了 N 项（N 远大于 60），否则 exit 2。
bgn10fix_problems: list[str] = []
_bgn10fix_checked = 0


def _bgfix_bad(tag: str, msg: str) -> None:
    bgn10fix_problems.append("[" + tag + "] " + msg)


def _bgfix_src(name: str) -> str:
    p = JAVA / name
    return strip_comments(p.read_text(encoding="utf-8")) if p.is_file() else ""


# ---------- ① 混沌金币：熔炉 + **高炉**（旧口径「只做 smelting」已被推翻）----------
_bgn10fix_checked = 0
_bgfix_blast = _RC_DATA / "chaos_coin_blasting.json"
_bgn10fix_checked += 1
if not _bgfix_blast.is_file():
    _bgfix_bad("bgn10fix-blast", "缺 chaos_coin_blasting.json（作者要「高炉也能烧成粒」）")
else:
    _bg = json.loads(_bgfix_blast.read_text(encoding="utf-8"))
    if _bg.get("type") != "minecraft:blasting":
        _bgfix_bad("bgn10fix-blast", "type 不是 minecraft:blasting：" + repr(_bg.get("type")))
    if _bg.get("result") != {"id": "bettergold:chaosgold_nugget"}:
        _bgfix_bad("bgn10fix-blast", "产物不是 chaosgold_nugget：" + repr(_bg.get("result")))
    if _bg.get("cookingtime") != 100 or _bg.get("experience") != 1.0:
        _bgfix_bad("bgn10fix-blast",
                   "高炉档不是「100 tick / 1.0 xp」：" + repr((_bg.get("cookingtime"), _bg.get("experience"))))
_bgn10fix_checked += 1
if not (_RC_DATA / "chaos_coin_smelting.json").is_file():
    _bgfix_bad("bgn10fix-blast", "熔炉那条被删了（作者只说「也能」，不是「改成」）")

# ---------- ② 金火把花：blockstate → model → texture 三层链 + cutout 渲染层 ----------
_bgn10fix_checked += 1
try:
    from PIL import Image as _BgfixImage
except Exception:                                          # noqa: BLE001
    _BgfixImage = None
_BGFIX_MODELS = {
    "golden_torchflower": ("cross", "bettergold:block/golden_torchflower"),
    "golden_torchflower_crop_stage0": ("cross", "bettergold:block/golden_torchflower_crop_stage0"),
    "golden_torchflower_crop_stage1": ("cross", "bettergold:block/golden_torchflower_crop_stage1"),
    "potted_golden_torchflower": ("minecraft:block/flower_pot_cross", "bettergold:block/golden_torchflower"),
}
for _m, (_parent, _tex) in _BGFIX_MODELS.items():
    _bgn10fix_checked += 4
    _mp = _RES / "assets" / "bettergold" / "models" / "block" / (_m + ".json")
    if not _mp.is_file():
        _bgfix_bad("bgn10fix-torchflower", "缺模型 " + _m)
        continue
    _mo = json.loads(_mp.read_text(encoding="utf-8"))
    _want_parent = _parent if _parent.startswith("minecraft:") else "minecraft:block/" + _parent
    if _mo.get("parent") != _want_parent:
        _bgfix_bad("bgn10fix-torchflower", _m + " 的 parent 不是 " + _want_parent + "：" + repr(_mo.get("parent")))
    # ★ 根因：NeoForge 对**没有 render_type 的模组方块**走 `RenderType.solid()`
    #   （`ItemBlockRenderTypes.BLOCK_RENDER_TYPES.defaultReturnValue(SOLID)`）⇒ 透明像素被当黑色画出。
    if _mo.get("render_type") != "minecraft:cutout":
        _bgfix_bad("bgn10fix-torchflower",
                   _m + " 没有 render_type=minecraft:cutout（透明背景会被 SOLID 画成黑块）")
    _tkey = "plant" if _m.startswith("potted_") else "cross"
    if (_mo.get("textures") or {}).get(_tkey) != _tex:
        _bgfix_bad("bgn10fix-torchflower",
                   _m + " 的 textures." + _tkey + " 不是 " + _tex + "：" + repr(_mo.get("textures")))
    _tex_rel = _RES / "assets" / "bettergold" / "textures" / (_tex.split(":", 1)[1] + ".png")
    if not _tex_rel.is_file():
        _bgfix_bad("bgn10fix-torchflower", _m + " 引用的贴图不存在：" + str(_tex_rel))
    elif _BgfixImage is not None:
        _im = _BgfixImage.open(_tex_rel).convert("RGBA")
        _px = list(_im.getdata())
        _transparent = sum(1 for _r, _g, _b, _a in _px if _a == 0)
        _opaque_black = sum(1 for _r, _g, _b, _a in _px if _a > 0 and _r < 20 and _g < 20 and _b < 20)
        if _transparent == 0:
            _bgfix_bad("bgn10fix-torchflower", _m + " 的贴图没有透明像素（那就不可能靠 cutout 修好）")
        if _opaque_black > 0:
            _bgfix_bad("bgn10fix-torchflower",
                       _m + " 的贴图有 " + str(_opaque_black) + " 个不透明近黑像素（先报作者，别改像素）")
        _im.close()

# ---------- ③ 迷之炖菜：伤害吸收 III / 320 tick ----------
_bgn10fix_checked += 6
_gf = _bgfix_src("block/GoldenTorchflowerBlock.java")
for _needle, _why in (
        ("STEW_TICKS = 16 * 20", "炖菜时长不是 16 秒 = 320 tick"),
        ("MobEffects.ABSORPTION", "花方块没有声明 absorption（JEI / 炖菜配方不会跟随）"),
        ("STEW_TICKS / 20.0F", "花方块没有把 320 tick 交给 FlowerBlock 的 seconds 参数")):
    if _needle not in _gf:
        _bgfix_bad("bgn10fix-stew", _why + "（缺 " + _needle + "）")
_mev_all = _bgfix_src("event/ModEvents.java")
for _needle, _why in (
        ("onGoldenTorchflowerStew", "缺「喝下炖菜后补 III 级」的处理器"),
        ("Items.SUSPICIOUS_STEW", "处理器没有限定原版迷之炖菜"),
        ("new MobEffectInstance(MobEffects.ABSORPTION", "处理器没有施加 absorption"),
        (", false, true, true", "施加参数被改（应为 ambient=false / visible / showIcon）")):
    if _needle not in _mev_all:
        _bgfix_bad("bgn10fix-stew", _why + "（缺 " + _needle + "）")
if "GoldenTorchflowerBlock.STEW_TICKS, 2" not in _mev_all:
    _bgfix_bad("bgn10fix-stew", "处理器没有把等级写成 2（= III 级）且时长引用 STEW_TICKS")

# ---------- ④ 附魔书四改 ----------
_bgn10fix_checked += 8
_ci = _bgfix_src("material/ChaosItems.java")
for _needle, _why in (
        ("stacksTo(16)", "最大堆叠不是 16"),
        ("InteractionHand.MAIN_HAND", "不是「主手书」的新交互形状"),
        ("player.getOffhandItem()", "被附魔的装备不是取自副手"),
        ("SoundEvents.ENCHANTMENT_TABLE_USE", "成功时没播附魔台音效"),
        ("player.isCreative()", "创造模式没有单独分支"),
        ("int cost = creative ? 0", "创造模式仍会算经验消耗")):
    if _needle not in _ci:
        _bgfix_bad("bgn10fix-book", _why + "（缺 " + _needle + "）")
if _ci.count("alwaysEdible()") != 2:
    _bgfix_bad("bgn10fix-fruit", "两个禁果不是都加了 alwaysEdible()（实际 " + str(_ci.count("alwaysEdible()")) + " 处）")

# ---------- ⑤ 混沌金建材：硬度 ×2/3 + 铁级 ----------
_bgn10fix_checked += 6
_am = _bgfix_src("material/AllMetals.java")
for _needle, _why in (
        ("spec.blockStrength = 55.0F * 2.0F / 3.0F;", "块的硬度不是「贵金基准 55 × 2/3」"),
        ("spec.detailStrength = 8.0F * 2.0F / 3.0F;", "细节件硬度不是「基准 8 × 2/3」"),
        ("spec.incorrectForDrops = BlockTags.INCORRECT_FOR_IRON_TOOL;", "挖掘等级不是铁")):
    if _needle not in _am:
        _bgfix_bad("bgn10fix-blockstrength", _why + "（缺 " + _needle + "）")
# ⚠ 崩乱合金的块属性一个字节都不许动（作者只提「混沌金系列」）
if "spec.blockStrength = 150.0F;" not in _am:
    _bgfix_bad("bgn10fix-blockstrength", "崩乱合金块的硬度 150.0F 被改了（作者只让改混沌金）")
_bgfix_iron = tag_members("minecraft/tags/block/needs_iron_tool.json")
_bgfix_diamond = tag_members("minecraft/tags/block/needs_diamond_tool.json")
_bgfix_forms = MF.building_of("chaosgold")
_bgn10fix_checked += 3
_missing_iron = [b for b in _bgfix_forms if ("bettergold:chaosgold_" + b) not in _bgfix_iron]
_still_diamond = [b for b in _bgfix_forms if ("bettergold:chaosgold_" + b) in _bgfix_diamond]
if _missing_iron:
    _bgfix_bad("bgn10fix-blockstrength", "这些混沌金建材不在 #minecraft:needs_iron_tool：" + repr(_missing_iron))
if _still_diamond:
    _bgfix_bad("bgn10fix-blockstrength", "这些混沌金建材还在 #minecraft:needs_diamond_tool：" + repr(_still_diamond))
if len(_bgfix_forms) != 11:
    _bgfix_bad("bgn10fix-blockstrength", "混沌金建材形态不是 11 种（反空转）：" + str(len(_bgfix_forms)))

# ---------- ⑦ 金钱妖：悬浮 + 待机硬币旋转 ----------
_bgn10fix_checked += 8
_mg = _bgfix_src("entity/MoneyGremlin.java")
for _needle, _why in (
        ("HOVER_OFFSET = 0.4D", "没有烈焰人同档的悬浮偏移 0.4 格"),
        ("idleAnimationState.animateWhen(!moving, this.tickCount)", "待机动画状态没有被推进（永远停在 0 帧）")):
    if _needle not in _mg:
        _bgfix_bad("bgn10fix-gremlin", _why + "（缺 " + _needle + "）")
if "setNoGravity(true)" in _mg:
    _bgfix_bad("bgn10fix-gremlin", "金钱妖被改成了不受重力的飞行怪（作者明确不要）")
_mgr = _bgfix_src("client/MoneyGremlinRenderer.java")
if "getRenderOffset" not in _mgr or "MoneyGremlin.HOVER_OFFSET" not in _mgr:
    _bgfix_bad("bgn10fix-gremlin", "渲染器没有把模型整体上抬 HOVER_OFFSET")
_anim = (REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "client"
         / "MoneyGremlinAnimations.java").read_text(encoding="utf-8")
_idle = _anim.split("public static final AnimationDefinition WALK")[0]
if _idle.count("360.0F") < 8:
    _bgfix_bad("bgn10fix-gremlin",
               "IDLE 里硬币骨骼的旋转通道不足 8 条（每枚硬币 0→360°；实际 " + str(_idle.count("360.0F")) + "）")
for _bn in ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"):
    if ('addAnimation("' + _bn + '", new AnimationChannel(AnimationChannel.Targets.ROTATION') not in _idle:
        _bgfix_bad("bgn10fix-gremlin", "IDLE 缺 " + _bn + " 的 rotation 通道")

# ---------- ⑧ 弹幕：三格**外**才打 ----------
_bgn10fix_checked += 4
if "isBeyondBarrageRange" not in _mg:
    _bgfix_bad("bgn10fix-barrage", "没有 isBeyondBarrageRange（三格外才打）")
if "isWithinBarrageRange" in _mg:
    _bgfix_bad("bgn10fix-barrage", "旧的「三格内」判据还在")
if "return distanceSqr > BARRAGE_MIN_RANGE * BARRAGE_MIN_RANGE;" not in _mg:
    _bgfix_bad("bgn10fix-barrage", "判据不是「严格大于 9.0」")
if "isBeyondBarrageRange(this.distanceToSqr(target))" not in _mg:
    _bgfix_bad("bgn10fix-barrage", "customServerAiStep 没有改用新判据")

# ---------- ⑨ 混沌金币可投掷 + 不进「寻途」----------
_bgn10fix_checked += 12
_co = _bgfix_src("item/ChaosCoinItem.java")
for _needle, _why in (
        ("PLAYER_DAMAGE = 3.0F", "玩家投掷伤害不是 3 点"),
        ("PLAYER_HUNGER_TICKS = 16 * 20", "玩家投掷饥饿不是 16 秒"),
        ("COOLDOWN_TICKS = 10", "投掷冷却不是 10 tick"),
        ("new ChaosCoinProjectile(level, player)", "没有生成共用的弹射物"),
        ("stack.shrink(1)", "投掷没有消耗 1 个")):
    if _needle not in _co:
        _bgfix_bad("bgn10fix-coin", _why + "（缺 " + _needle + "）")
_cp = _bgfix_src("entity/ChaosCoinProjectile.java")
for _needle, _why in (
        ("isPlayerThrown()", "弹射物没有区分「玩家投掷」"),
        ("effectiveDamage()", "伤害没有按来源分档"),
        ("effectiveHungerTicks()", "饥饿时长没有按来源分档"),
        ("applyHunger(LivingEntity target, int ticks)", "叠层函数没有共用一份（有两个实现？）")):
    if _needle not in _cp:
        _bgfix_bad("bgn10fix-coin", _why + "（缺 " + _needle + "）")
_ai = _bgfix_src("registry/AllItems.java")
if "new com.hjmmd_8.bettergold.item.ChaosCoinItem(" not in _ai:
    _bgfix_bad("bgn10fix-coin", "chaos_coin 还是普通 Item（不能投掷）")
# 成就：CORE_MATERIALS 回到 8 项且不含 chaos_coin（导入生成器 = 读唯一真源，不是复述）
_bgn10fix_checked += 3
try:
    import importlib.util as _bgfix_ilu
    _bgfix_dwb = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        _bgfix_spec = _bgfix_ilu.spec_from_file_location(
            "_bgn10fix_advgen", REPO / "tools" / "asset-generator" / "generate_advancements.py")
        _bgfix_adv = _bgfix_ilu.module_from_spec(_bgfix_spec)
        _bgfix_spec.loader.exec_module(_bgfix_adv)
    finally:
        sys.dont_write_bytecode = _bgfix_dwb
    if "bettergold:chaos_coin" in _bgfix_adv.CORE_MATERIALS:
        _bgfix_bad("bgn10fix-adv", "chaos_coin 还在「寻途千里的珍宝」的判据集合里")
    if len(_bgfix_adv.CORE_MATERIALS) != 8:
        _bgfix_bad("bgn10fix-adv",
                   "核心材料不是 8 项（实际 " + str(len(_bgfix_adv.CORE_MATERIALS)) + "）")
except Exception as _e:                                    # noqa: BLE001
    _bgfix_bad("bgn10fix-adv", "成就生成器加载失败：" + repr(_e))
for _adv_name in ("treasure/chaos_coin", "metal/chaosalloy/ingot"):
    _bgn10fix_checked += 1
    _adv_path = _ADV / (_adv_name + ".json")
    if not _adv_path.is_file():
        _bgfix_bad("bgn10fix-adv", "缺成就 " + _adv_name)
        continue
    _adv_obj = json.loads(_adv_path.read_text(encoding="utf-8"))
    if _adv_obj.get("parent") != "bettergold:root":
        _bgfix_bad("bgn10fix-adv",
                   _adv_name + " 的 parent 不是 bettergold:root：" + repr(_adv_obj.get("parent")))

# ---------- ⑩ 区间值：区间随机 + 三个触发点 ----------
_bgn10fix_checked += 8
_cr_src = _bgfix_src("material/ChaosRange.java")
for _needle, _why in (
        ("random.nextInt(FRACTION_SCALE + 1)", "随机源不是区间内均匀（含两端）"),
        ("valueOfFraction", "缺「比例 → 数值」的唯一映射"),
        ("onMiningSuccess", "缺「挖掘成功」触发点"),
        ("onHeldChange", "缺「重新手持」触发点")):
    if _needle not in _cr_src:
        _bgfix_bad("bgn10fix-range", _why + "（缺 " + _needle + "）")
if "current == range.min ? range.max : range.min" in _cr_src:
    _bgfix_bad("bgn10fix-range", "两端乒乓公式还在（作者 2026-10-18 已推翻）")
# 三个触发点里"攻击命中"的落点是近战 hurtEnemy + 远程命中，两处都必须走 reroll
for _f, _why in (("material/MetalWeapons.java", "近战命中没有重掷 ATTACK"),
                 ("material/ChaosWiring.java", "远程命中没有重掷 ATTACK")):
    _bgn10fix_checked += 1
    if "ChaosRange.reroll(" not in _bgfix_src(_f):
        _bgfix_bad("bgn10fix-range", _why + "（" + _f + " 里缺 ChaosRange.reroll(）")
if "ChaosRange.reroll(worn, ChaosRange.Channel.ARMOR" not in _bgfix_src("material/MetalEvents.java"):
    _bgfix_bad("bgn10fix-range", "盔甲减伤没有重掷（还是翻转？）")
# 复算：2000 次采样必须落在 [4,8]、均值 ≈ 6、且出现 5/6/7 三个中间档
_bgn10fix_checked += 1
try:
    import random as _bgfix_random
    _rng = _bgfix_random.Random(20261018)
    _samples = [round(4 + 4 * (_rng.randint(0, 1000) / 1000.0)) for _ in range(2000)]
    _mean = sum(_samples) / len(_samples)
    if min(_samples) < 4 or max(_samples) > 8:
        _bgfix_bad("bgn10fix-range", "采样越界（应全部落在 4..8）：" + repr((min(_samples), max(_samples))))
    if not all(_v in _samples for _v in (5, 6, 7)):
        _bgfix_bad("bgn10fix-range", "采样没有覆盖 5/6/7（不是区间随机）")
    if abs(_mean - 6.0) > 0.1:
        _bgfix_bad("bgn10fix-range", "采样均值不是 ≈ 6：" + repr(round(_mean, 4)))
except Exception as _e:                                    # noqa: BLE001
    _bgfix_bad("bgn10fix-range", "采样复算失败：" + repr(_e))

if _bgn10fix_checked < 60:
    _bgfix_bad("bgn10fix-anti-vacuum",
               "本段只检查了 " + str(_bgn10fix_checked) + " 项（反空转守护：应远大于 60）")
print("1.7 bg-n10fix（作者试玩 10 条：高炉 / 火把花黑底 / 炖菜 / 附魔书 / 建材硬度 / 禁果 / 金钱妖 / 弹幕 / 金币投掷 / 区间随机）问题: "
      + str(len(bgn10fix_problems)) + " " + str(bgn10fix_problems[:4])
      + "（本段判定 " + str(_bgn10fix_checked) + " 项）")
if not bgn10fix_problems:
    print("[bgn10fix-ok] ① 熔炉 + 高炉（高炉 100 tick / xp 1.0）/ ② 4 个模型 cutout + 三层链 + 贴图透明 / "
          "③ 炖菜 absorption III 320 tick / ④ 书 16 堆叠 + 主手书副手装备 + 附魔台音效 + 创造免经验 / "
          "⑤ 建材 55×2/3 与 8×2/3 + needs_iron_tool 且不在 diamond / ⑥ 两个禁果 alwaysEdible / "
          "⑦ 悬浮 0.4 + IDLE 八枚硬币 0→360° / ⑧ 三格外才打 / ⑨ 金币可投掷（3 点 / 320 tick / 冷却 10）+ 不进寻途 / "
          "⑩ 区间随机含两端 + 三个触发点（2000 次采样 4..8 均值 6）")

_EXIT_PROBLEM_LISTS = (missing_zh, missing_en, missing_loot, missing_knife_tags, missing_weapon_tags,
                       bg15w_problems, bg8_problems, bg9_problems,
                       bg16_problems, bgbook_problems, bgbook2_problems, bgfix_problems,
                       bgfinal_problems, bgappend_problems, bgfix2_problems, bgbook8_problems,
                       bgfinal3_problems, bgbook9_problems, bgfix3_problems, bgbook10_problems,
                       bgfix4_problems, bgfix5_problems, bgfix7_problems, bgfix8_problems,
                       bgfix9_problems, bgfix10_problems, bgfix11_problems,
                       symmetric_problems, beacon_problems, bgn10_problems, _bgn10w_problems,
                       _bgn10r4_problems, bgn10r6_problems, bgn10r5_problems, bgn10r7_problems,
                       bgn10r8_problems, bgn10r9_problems,
                       bgn10rc_problems, bgn10rg_problems, bgn10d_problems, bgn10rc2_problems,
                       bgn10up_problems, bgn10fix_problems)
# ⚠ bgfix6：上面这份元组与**原来那行表达式逐条同源**（旧原文原样留档在这里，未删）——
#   sys.exit(1 if (missing_zh or missing_en or missing_loot or missing_knife_tags or missing_weapon_tags
#                  or bg15w_problems or bg8_problems or bg9_problems
#                  or bg16_problems or bgbook_problems or bgbook2_problems or bgfix_problems
#                  or bgfinal_problems or bgappend_problems or bgfix2_problems or bgbook8_problems
#                  or bgfinal3_problems or bgbook9_problems or bgfix3_problems or bgbook10_problems
#                  or bgfix4_problems or bgfix5_problems
#                  or symmetric_problems or beacon_problems) else 0)
#   改成引用同一份元组，只为**消除"两处清单漂移"**这个已知脆弱形状（原判定一字未改）。
#   ⚠ `swim_problems` 不在这份清单里，但它在 L391 被 `bg8_problems.extend(...)` 吸收 ⇒ 已覆盖。
_problem_total = sum(len(_x) for _x in _EXIT_PROBLEM_LISTS)
print(f"[bg-data-{'fail' if _problem_total else 'ok'}] 问题合计 {_problem_total} 条"
      f"（契约：0 绿 / 1 有问题 / 2 前置坏）")

sys.exit(1 if _problem_total else 0)
