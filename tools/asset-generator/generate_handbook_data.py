#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_handbook_data.py -- bg-book (Patchouli handbook) data generator.

Writes the handbook tree.  ⚠ Patchouli 1.20+ **split the layout in two halves** (this was a real
A-level finding of this round, not a choice of ours):

    src/main/resources/data/bettergold/patchouli_books/alchemy_handbook/book.json
        -- the ONLY file that stays on the data-pack side.
    src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/<lang>/categories/*.json
    src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/<lang>/entries/*.json
        -- all book CONTENTS are client side, and book.json must set "use_resource_pack": true.

Putting the contents under `data/` (which the requirement doc §5.1 #5 assumed) makes Patchouli
throw `IllegalArgumentException: Book ... has use_resource_pack set to false. This behaviour was
removed in 1.20.` and **skip the whole book** (`Book.java:148` via `BookRegistry.loadBook`).

The language files (assets/bettergold/lang/{zh_cn,en_us}.json) are NOT touched by this script --
every user visible string in the generated JSON is a translation key such as
"bettergold.handbook.category.alchemy_start.name", and validate_metal_data.py checks that each
referenced key exists in BOTH language files.

Why two recipes per page (and not six):
    Patchouli's PageDoubleRecipe (the base of PageCrafting / PageSmithing / ...) only has the two
    slots `recipe` / `recipe2` (see the @SerializedName values in
    vazkii.patchouli.client.book.page.abstr.PageDoubleRecipe) and the page type table
    (ClientBookRegistry#addPageTypes) has no "N recipes" entry.  That is Patchouli's structural
    limit, not a shortcut of ours: "six tools on one page" would require a custom page type
    (a whole new client-side page renderer).

Idempotent: every file it owns is rewritten from scratch; it never touches anything outside its
own two trees.
"""

import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOOK_DIR = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "patchouli_books",
                        "alchemy_handbook")
ASSET_DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "patchouli_books",
                         "alchemy_handbook")

ITEM = "bettergold:alchemy_student_handbook"
BOOK_PATH = "alchemy_handbook"

LANG = "bettergold.handbook"

# --------------------------------------------------------------------------------------
# The eight metal families (order = CreativeSections.METAL_ORDER, i.e. the in-game order).
# `core` = that family's core material item (the one MetalFamily.Spec#coreItem registers).
# --------------------------------------------------------------------------------------
METALS = [
    ("flamegold", "blazing_rod"),
    ("sturdygold", "golden_cowrie"),
    ("thornsgold", "glittering_vine"),
    ("echogold", "bundled_echo_shard"),
    ("indigoseagold", "indigo_ocean_heart"),
    ("voodoogold", "voodoo_feather"),
    ("thundergold", "amethyst_energy_dust"),
    ("illusiongold", "chorus_cherry_branch"),
]

# The six "器具" (tools) and the four armor pieces of every family.
TOOLS = ["sword", "axe", "pickaxe", "shovel", "hoe", "knife"]
ARMOR = ["helmet", "chestplate", "leggings", "boots"]

# The four categories (order = sortnum, i.e. the order shown on the landing screen).
#
# ⚠ bg-book §八（2026-10-06）第 2 个类别**换了名字**（id 与图标**不动**）：
#   旧 `bettergold.handbook.category.gear_upgrade.name` = 「装备的升级」
#   新 = **「装备的强化」**（§8.1「手册四类变为：炼金的起步 / 装备的强化 / 金灿的盛宴 / 商人与古董」）
#   - id 仍是 `gear_upgrade`：类别 id 是条目 `category` 字段的目标，改它没有任何收益、
#     只会让 9 个新条目与 / 或老存档的"已读"记录找不到归属（存档兼容红线：能不动就不动）；
#   - 旧名值**留在语言文件里作历史留档**（原文不删），由关卡负向断言守着"不许回到旧名"；
#   - 类别说明（`.desc`）作者没改，仍是「"贵金"自然而然有着自己的专属装备。」。
CATEGORIES = [
    ("alchemy_start", "raw_sturdygold", 0),          # 炼金的起步 (materials first)
    ("gear_upgrade", "sturdygold_sword", 1),         # 装备的强化（§八 改名，id 未动）
    ("golden_feast", "sturdygold_apple", 2),         # 金灿的盛宴
    ("merchant_antiques", "gold_exchange_counter", 3),  # 商人与古董
]

# Placeholder food / merchant / antique spotlights -- existing items only, no invented content.
FOOD_ITEMS = [
    "sturdygold_apple",
    "sturdygold_carrot",
    "sturdygold_ice_cream",
    "sturdygold_chocolate_bar",
    "sturdygold_brewed_hot_cocoa",
    "golden_chocolate_bar",
]
MERCHANT_ITEMS = [
    "gold_exchange_counter",
    "gift_gold_ticket",
    "alchemy_materials_box",
    "treasure_gift_box",
    "curio_box",
]
ANTIQUE_ITEMS = [
    "unwanted_antique",
    "antique_sword",
    "netherite_antique_sword",
    "netherite_dust",
]

# --------------------------------------------------------------------------------------
# Page builders
# --------------------------------------------------------------------------------------


def text_page(text_key, title_key=None):
    page = {"type": "patchouli:text", "text": text_key}
    if title_key:
        page["title"] = title_key
    return page


def smithing_page(recipe_a, recipe_b, title_key=None):
    """One page holding TWO smithing recipes (Patchouli's maximum)."""
    page = {
        "type": "patchouli:smithing",
        "recipe": "bettergold:%s" % recipe_a,
        "recipe2": "bettergold:%s" % recipe_b,
    }
    if title_key:
        page["title"] = title_key
    return page


def crafting_page(recipe_a, recipe_b=None, title_key=None, text_key=None):
    """⚠ 配方页也能带**正文**：读 Patchouli jar 的字节码实测
    ``PageDoubleRecipe extends PageWithText`` ⇒ ``text`` 字段存在（§六 的结论，本轮复用）。
    """
    page = {"type": "patchouli:crafting", "recipe": "bettergold:%s" % recipe_a}
    if recipe_b:
        page["recipe2"] = "bettergold:%s" % recipe_b
    if title_key:
        page["title"] = title_key
    if text_key:
        page["text"] = text_key
    return page


def spotlight_page(item, text_key=None, title_key=None):
    """⚠ 两个可选参数的语义不同，别写反（会静默变成正文而不是页眉）：

    * ``title`` —— 页面渲染时经 ``i18nText()`` 解析 ⇒ **既接受语言键也接受字面文本**
      （作者 §七 第 2/4 条给的就是中文标题原文）；
    * ``text`` —— 页面**正文**，同样经 ``i18nText()`` 解析。
    """
    page = {"type": "patchouli:spotlight", "item": item}
    if text_key:
        page["text"] = text_key
    if title_key:
        page["title"] = title_key
    return page


def category(name, icon, sortnum):
    return {
        "name": "%s.category.%s.name" % (LANG, name),
        "description": "%s.category.%s.desc" % (LANG, name),
        "icon": "bettergold:%s" % icon,
        "sortnum": sortnum,
    }


def entry(name, category_name, icon, sortnum, pages):
    return {
        "name": "%s.entry.%s" % (LANG, name),
        "category": "bettergold:%s" % category_name,
        "icon": "bettergold:%s" % icon,
        "sortnum": sortnum,
        "read_by_default": True,
        "pages": pages,
    }


# --------------------------------------------------------------------------------------
# The seven entries
# --------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------
# ⛔ bg-fix3 §三（作者 2026-10-07）：「将手册中"**贵金的材料链**"与"**升级锻造模版**"两部分删去」
# --------------------------------------------------------------------------------------
#
# 取证（先做过才动手）：手册**实际数据里真的有这两节** ——
#   * 「贵金的材料链」  = 条目 `metal_tour`（条目名的语言键值逐字就是这五个字），9 页；
#   * 「升级锻造模板」  = 条目 `upgrade_templates`（作者写「模版」、语言键里是「模板」，同一样东西），5 页；
#   两者都挂在类别 `alchemy_start`（炼金的起步）下，sortnum 0 / 1。
#   ⇒ 不是"数据侧本来没有"：这是**上一轮骨架轮**留下的两个条目（§10.4 的"随便写点什么"骨架）。
#   （对照：作者 10-05 提过的「装备的升级」类别 + 章3 第 1 页 已在 §八 处理掉了 —— 那是**另一批**。）
#
# ⚠ **内容不凭空消失**：两个构造函数**原样保留在下面**（一行都没删），
#   由 `RETIRED_ENTRIES` 引用、并在 `main()` 里照常自证它们的页数（9 / 5）；
#   全文对照（页型序列 / 页数 / 图标 / 配方引用）落在 `docs/1.6-规格.md` §二十二。
#   ⇒ 以后谁要看"当年那条材料链 / 那张模板表长什么样"，读这里即可，不必翻 git 历史。
# ⚠ 它们引用的语言键（`entry.metal_tour` / `page.metal_tour` / `page.metal_chain` /
#   `entry.upgrade_templates` / `page.upgrade_templates`）**原样留在两份语言文件里**作历史留档。
RETIRED_BY_BGFIX3 = ["metal_tour", "upgrade_templates"]


def entry_metal_tour():
    pages = [text_page("%s.page.metal_tour" % LANG)]
    for metal, core in METALS:
        chain = [
            "bettergold:%s" % core,
            "bettergold:raw_%s" % metal,
            "bettergold:%s_ingot" % metal,
            "bettergold:%s_nugget" % metal,
            "bettergold:%s_upgrade_template" % metal,
        ]
        pages.append(spotlight_page(chain, "%s.page.metal_chain" % LANG))
    return entry("metal_tour", "alchemy_start", "raw_sturdygold", 0, pages)


def entry_upgrade_templates():
    pages = [text_page("%s.page.upgrade_templates" % LANG)]
    recipes = ["%s_upgrade_template" % metal for metal, _ in METALS]
    for i in range(0, len(recipes), 2):
        pages.append(crafting_page(recipes[i], recipes[i + 1]))
    return entry("upgrade_templates", "alchemy_start", "sturdygold_upgrade_template", 1, pages)


# --------------------------------------------------------------------------------------
# ⛔ bg-book §八（2026-10-06）：下面两个条目**已作废**（retired），不再写进数据树
# --------------------------------------------------------------------------------------
#
# §8.1 要求「删除手册四类里的『装备的升级』类别（整个类别）」⇒ 它下面这两个条目
# （器具 / 头怀腿靴）随之作废，它们的 42 个 Patchouli 页由「装备的强化」章节里
# **每族 7 页的锻造方式**（剑/重锤/三叉戟/弓/弩/斧/镐/锹/锄/盾牌/头盔/胸甲/护腿/靴子）取代。
#
# ⚠ **内容不凭空消失**：两个构造函数**原样保留在下面**（不删），
#   由 `RETIRED_ENTRIES` 引用并在 `main()` 里照常自证它们的页数（25 / 17）；
#   全文对照（页型序列 / 页数 / 分组）另外落在 `docs/1.6-规格.md` §十九。
#   ⇒ 以后谁要看"当年器具同框长什么样"，读这里即可，不必翻 git 历史。


def entry_tools_per_family():
    pages = [text_page("%s.page.tools" % LANG)]
    groups = [
        (("sword", "axe"), "%s.page.tools_1" % LANG),
        (("pickaxe", "shovel"), "%s.page.tools_2" % LANG),
        (("hoe", "knife"), "%s.page.tools_3" % LANG),
    ]
    for metal, _core in METALS:
        for (a, b), title_key in groups:
            pages.append(
                smithing_page("smithing_%s_%s" % (metal, a), "smithing_%s_%s" % (metal, b), title_key)
            )
    return entry("tools_per_family", "gear_upgrade", "sturdygold_sword", 0, pages)


def entry_armor_per_family():
    pages = [text_page("%s.page.armor" % LANG)]
    groups = [
        (("helmet", "chestplate"), "%s.page.armor_1" % LANG),
        (("leggings", "boots"), "%s.page.armor_2" % LANG),
    ]
    for metal, _core in METALS:
        for (a, b), title_key in groups:
            pages.append(
                smithing_page("smithing_%s_%s" % (metal, a), "smithing_%s_%s" % (metal, b), title_key)
            )
    return entry("armor_per_family", "gear_upgrade", "sturdygold_chestplate", 1, pages)


RETIRED_ENTRIES = [entry_tools_per_family, entry_armor_per_family,
                   # ⛔ bg-fix3 §三（2026-10-07）：这两个条目已作废，见上方那段取证注释
                   entry_metal_tour, entry_upgrade_templates]



def entry_golden_feast():
    pages = [text_page("%s.page.golden_feast" % LANG)]
    for item in FOOD_ITEMS:
        pages.append(spotlight_page("bettergold:%s" % item))
    return entry("golden_feast", "golden_feast", "sturdygold_apple", 0, pages)


def entry_merchant():
    pages = [text_page("%s.page.merchant" % LANG)]
    for item in MERCHANT_ITEMS:
        pages.append(spotlight_page("bettergold:%s" % item))
    return entry("merchant", "merchant_antiques", "gold_exchange_counter", 0, pages)


def entry_antiques():
    pages = [text_page("%s.page.antiques" % LANG)]
    for item in ANTIQUE_ITEMS:
        pages.append(spotlight_page("bettergold:%s" % item))
    return entry("antiques", "merchant_antiques", "unwanted_antique", 1, pages)


# --------------------------------------------------------------------------------------
# ⛔ bg-book §九（2026-10-06 20:02）：上面两个「商人与古董」旧占位条目**已作废**，不再写进数据树
# --------------------------------------------------------------------------------------
#
# §9.1 要求「删除『商人与古董』类别下我之前设的旧占位两节」（作者原话「**之前你设的那两个就可以
# 就此毙掉了**」）⇒ 它们的 11 个 Patchouli 页（merchant 6 + antiques 5）由下面的 **3 章 20 页**取代。
#
# ⚠ **内容不凭空消失**：两个构造函数**原样保留在上面**（不删），
#   由下面的 `RETIRED_ENTRIES` 引用并在 `main()` 里照常自证它们的页数（6 / 5 = 11）；
#   全文对照（页型序列 / 页数）另外落在 `docs/1.6-规格.md` §21。
#   ⇒ 以后谁要看"当年那两个占位长什么样"，读这里即可，不必翻 git 历史。
#
# ⚠ 这行**必须**写在两个函数定义之后（列表字面量在定义时求值）——
#   写在上面的 RETIRED_ENTRIES 里会 NameError。
RETIRED_ENTRIES = RETIRED_ENTRIES + [entry_merchant, entry_antiques]

ENTRIES = [
    # ⛔ entry_metal_tour —— bg-fix3 §三 作废（作者 2026-10-07「贵金的材料链」），见上方注释
    # ⛔ entry_upgrade_templates —— bg-fix3 §三 作废（作者 2026-10-07「升级锻造模版」）
    # ⚠ 旧结构原文保留：本轮之前这里依次是
    #     [entry_metal_tour, entry_upgrade_templates, entry_golden_feast]（骨架 3 条）。
    entry_golden_feast,
    # ⛔ entry_tools_per_family / entry_armor_per_family —— §八 作废，见上方 RETIRED_ENTRIES
    # ⛔ entry_merchant / entry_antiques —— §九 作废，见上方 RETIRED_ENTRIES
]

# --------------------------------------------------------------------------------------
# bg-book §六 追加轮 (2026-10-05): 「炼金的起步」三章逐页补全
# --------------------------------------------------------------------------------------
#
# ``一行 = 一个跨页 = 2 个 Patchouli 页``
#     The requirement doc's tables have exactly 2 / 9 / 5 rows (章1 / 章2 / 章3) and every
#     row has a **left** half (icon + verbatim text) and a **right** half (recipe, or a
#     second icon + text).  Patchouli has no two-column page type, but its GUI shows a
#     **spread** (two pages at once) -- which is also what the author's own wording implies:
#     §6.2 row 1 puts "（无）" in the *icon* column while the icon itself ("中上角：炼金珍材盒")
#     is listed in the *right* column, i.e. the row is left page + right page.
#
#     => 章1 2 rows = 4 pages, 章2 9 rows = 18 pages, 章3 5 rows = 10 pages
#        = **32 Patchouli pages = the doc's "16 页" counted in spreads**.
#        (The alternative mapping "one row = one Patchouli page" would give 16 Patchouli
#        pages but cannot express "左侧文案 + 左上角图标 + 右侧挂配方"; switching is a
#        one-line change here -- see docs/1.6-规格.md §12.)
#
#     "随排版顺序不断变化" (章3 page 1) is literal: a Patchouli spotlight page cycles its
#     icon through the whole item list (`stacks[(ticksInBook / 20) % stacks.length]`, read
#     from the bytecode of PageSpotlight#render) -- so a list of all eight families in
#     layout order *is* "不断变化".
#
# Inferred values (docs/1.6-规格.md §12 推断值表; each is a one-line change):
#     * 章3 cover icon            = bettergold:sturdygold_ingot
#     * 章3 p1 left list          = per family (ingot, nugget) in METALS order -> 16 items
#     * 章3 p1 right list         = eight upgrade templates in METALS order
#     * 章3 p2..p5 "某某金建筑方块" = that family's `_bricks` block
CHAPTERS = [
    # (entry id, cover icon, sortnum, builder)  -- appended after the 1st-round entries
    ("auxiliary_materials", "mixed_crystal_pile", 2),
    ("core_materials", "golden_cowrie", 3),
    ("golden_knowledge", "sturdygold_ingot", 4),
]

# 章1 ·「贵金」的副要材料: 2 rows, one recipe each, recipe output == that page's subject item
AUX_ROWS = [
    ("aux_1", "mixed_crystal_pile", "mixed_crystal_pile"),
    ("aux_2", "alchemic_fuel", "alchemic_fuel"),
]

# 章2 ·「贵金」的核心材料: 9 rows.  `icon=None` = that row's left page has no icon (the
# doc's icon column literally says "（无）") and its right page is a spotlight of the box.
CORE_ROWS = [
    (None, "core_1", None),
    ("blazing_rod", "core_2", ("blazing_rod", "raw_flamegold")),
    ("golden_cowrie", "core_3", ("raw_sturdygold",)),
    ("glittering_vine", "core_4", ("raw_thornsgold",)),
    ("bundled_echo_shard", "core_5", ("bundled_echo_shard", "raw_echogold")),
    ("indigo_ocean_heart", "core_6", ("indigo_ocean_heart", "raw_indigoseagold")),
    ("voodoo_feather", "core_7", ("voodoo_feather_duplicate", "raw_voodoogold")),
    ("amethyst_energy_dust", "core_8", ("amethyst_energy_dust", "raw_thundergold")),
    ("chorus_cherry_branch", "core_9", ("chorus_cherry_branch", "raw_illusiongold")),
]

# 章3 ·「贵金」的知识: 5 rows, both halves are icon + text.
#
# 追加轮（bg-book §七，2026-10-05 作者七处修正）第 1/2/3/4 条的落法：
#   * 第 1 条「把那些东西都汇总起来」⇒ 删掉本页原来那两段长文案
#     （原「材料链」段 = 旧 `knowledge_1_left`；原「锻造模板怎么用」段 = 旧 `knowledge_1_right`），
#     整页只剩**两张图标 + 一句汇总**（新键 `knowledge_1_summary`，只有左页承载正文，
#     右页 `spotlight` 不带 `text` ⇒ 两页合起来只有一句话，符合"只留一句"）。
#   * 第 2 条「左图标 = 各种各样的"贵金"锭」⇒ 从左到右 = 八族**锭**（原来还夹着粒）。
#   * 第 3 条「下方图标换成若干变化的贵金锭」⇒ ⚠ **Patchouli 的 spotlight 页只有一个图标槽**
#     （`PageSpotlight` 的字段只有 `item` / `title` / `linkRecipe`，`render()` 只画
#      `stacks[(ticksInBook / 20) % stacks.length]` 一次，坐标写死 (50,15)）⇒
#     "中上角 + 下方"两张图标在一个 Patchouli 页里**表达不了**；本轮按"值得表"取
#     **一份不断轮换的锭表**（与第 2 条同源），并在 docs/1.6-规格.md §17 记为待作者一句话裁定。
#   * 第 4 条「锻造模板那个标题改成『"贵金"装备的升级锻造模版』」⇒ 见 KNOWLEDGE_1_TEMPLATE_TITLE。
KNOWLEDGE_1_INGOT_TITLE = "各种各样的\"贵金\"锭"
KNOWLEDGE_1_TEMPLATE_TITLE = "\"贵金\"装备的升级锻造模版"
# §七 第 7 条：建筑方块的中上角图标按**固定顺序**显示 ——
#   锭块 → 砖块 → 柱 → 楼梯 → 台阶 → 砖墙 → 栏杆 → 门 → 活板门 → 链 → 灯笼
# ⚠ 这是本文件里**唯一的**方块形态清单（生成器覆盖检查：家族里还有 `_bricks_*` 之外的同名形态吗？
#   答案在 `MetalFamily` 的方块注册里 —— 逐条比对见 docs/1.6-规格.md §17.2）。
#   关卡 `[bgappend-book-block-order]` 直接读这个常量与产物核对。
METAL_BLOCK_SUFFIX_ORDER = [
    "_block", "_bricks", "_pillar", "_bricks_stairs", "_bricks_slab",
    "_bricks_wall", "_bars", "_door", "_trapdoor", "_chain", "_lantern",
]
KNOWLEDGE_ROWS = [
    # row 1: left = every family's **ingot** (rotating list = 「随排版顺序不断变化」),
    #        right = every family's upgrade template (rotating list), each with its own title.
    ([ "bettergold:%s_ingot" % metal for metal, _core in METALS ],
     ["bettergold:%s_upgrade_template" % metal for metal, _core in METALS]),
]
for _i in range(0, len(METALS), 2):
    KNOWLEDGE_ROWS.append((["bettergold:%s_bricks" % METALS[_i][0]],
                           ["bettergold:%s_bricks" % METALS[_i + 1][0]]))


def entry_auxiliary_materials():
    """章1 ·「贵金」的副要材料（章节封面 = 混合晶石堆）。"""
    pages = []
    for key, item, recipe in AUX_ROWS:
        # left page: the subject item as the page icon + the verbatim text
        pages.append(spotlight_page("bettergold:%s" % item, "%s.page.%s" % (LANG, key)))
        # right page: that item's recipe (the recipe output is the same icon the author named)
        pages.append(crafting_page(recipe))
    return entry("auxiliary_materials", "alchemy_start", "mixed_crystal_pile", 2, pages)


def entry_core_materials():
    """章2 ·「贵金」的核心材料（章节封面 = 金钱贝）。"""
    pages = []
    for icon, key, recipes in CORE_ROWS:
        left_key = "%s.page.%s" % (LANG, key)
        if icon is None:
            # row 1: the left page is plain text (the doc's icon column = "（无）"), and the
            # item ("中上角：炼金珍材盒") sits on the right page together with the long text
            pages.append(text_page(left_key))
            pages.append(spotlight_page("bettergold:alchemy_materials_box",
                                        "%s.page.%s_right" % (LANG, key)))
        else:
            pages.append(spotlight_page("bettergold:%s" % icon, left_key))
            pages.append(crafting_page(recipes[0],
                                       recipes[1] if len(recipes) > 1 else None))
    return entry("core_materials", "alchemy_start", "golden_cowrie", 3, pages)


def entry_golden_knowledge():
    """章3 ·「贵金」的知识（封面图标 = 推断值，见上方注释）。

    ⛔ **bg-book §八（2026-10-06）删掉了本条目原来的第 1 页** —— §8.1「删除 章 3『贵金的知识』
    第 1 页（我上一轮改成"汇总页"的那页）」⇒ 本条目 **10 页 → 8 页**（第 2~5 行 × 两页）。

    * 该页的两张图标表（八族锭 / 八张升级模板）与两个标题常量
      （`KNOWLEDGE_1_INGOT_TITLE` / `KNOWLEDGE_1_TEMPLATE_TITLE`）**原样保留在文件里**（原文不删）；
    * 语言键 `knowledge_1_summary` / `knowledge_1_ingot_title` / `knowledge_1_template_title`
      也留在两份语言文件里作**历史留档**，只是**没有任何页面再引用它们**
      （关卡 `[bgbook8-k3-p1-gone]` 用负向断言守着）；
    * `KNOWLEDGE_ROWS[0]` 同样保留，本函数**跳过 index == 1**（= 那一跨页）。
    """
    pages = []
    for index, (left_items, right_items) in enumerate(KNOWLEDGE_ROWS, start=1):
        if index == 1:
            continue        # §八：这一跨页（汇总页）已删除，见 docstring
        pages.append(spotlight_page(left_items, "%s.page.knowledge_%d_left" % (LANG, index)))
        pages.append(spotlight_page(right_items, "%s.page.knowledge_%d_right" % (LANG, index)))
    return entry("golden_knowledge", "alchemy_start", "sturdygold_ingot", 4, pages)


CHAPTER_ENTRIES = [
    entry_auxiliary_materials,
    entry_core_materials,
    entry_golden_knowledge,
]

# --------------------------------------------------------------------------------------
# bg-book §八 追加轮（2026-10-06）：「装备的强化」9 章（替掉「装备的升级」类别）
# --------------------------------------------------------------------------------------
#
# 形状（与 §六 / §七 的既有口径一致，逐字文案由脚本从**仓库内冻结快照**
# `tools/asset-generator/bgappend-requirements-snapshot/bg-book-8.md` 解析后注入语言键）：
#
#   章1 · 关于联动与金制胚底（封面 = 金重锤胚底）：**6 页**
#        p1左 / p1右 / p2左 = 三段逐字文案（纯 `patchouli:text`，文档没给图标列）
#        p2右 = crafting(重锤胚底 + 三叉戟胚底) / p3左 = crafting(弓 + 弩) / p3右 = crafting(盾牌)
#   章2~9 · 八族「<金属>装备」（封面 = 该族金剑）：**每章 10 页**
#        p1左 = 武器工具文案 / p1右 = 盾牌文案 / p2左 = 盔甲文案（均纯文本）
#        后页 = 该族装备的锻造方式，**按固定顺序挂 14 件**
#
# ⚠ **门禁项（父代理 2026-10-06 裁定 = 照既有口径落）**：「14 件」**超过 Patchouli 的
#   2 配方/页上限**（`PageDoubleRecipe` 只有 `recipe` / `recipe2` 两个槽，见模块 docstring）。
#   作者 2026-10-04 已亲自裁定过同一件事：「每页 2 个配方是 Patchouli 的**结构上限**，
#   不是我们的退化方案」⇒ 14 件 = **7 页 × 2 配方**（`FORGE_ORDER` 两两配对）。
#
# ⚠ **推断 / 记账项 D2（父代理裁定：引默认那条、只记账）**：后页 14 件里有 5 件
#   （重锤 / 三叉戟 / 弓 / 弩 / 盾牌）在本仓**各存在两条配方**：
#     · `smithing_<族>_<件>`      —— base = 金制胚底，带 `neoforge:not(mod_loaded(mut))`；
#     · `smithing_mut_<族>_<件>`  —— base = `mut:golden_*`，带 `mod_loaded(mut)`。
#   手册页只有 2 个槽、也只能引一个 id ⇒ 本轮**引默认那条**（与第一轮
#   `entry_tools_per_family` 的引法一致）⇒ **装了 mut 的环境里这 5 页会指到未加载的配方**。
#   备选（按环境拆两套页 / 改引 mut 版）都被父代理明确否掉，只记账在
#   `docs/1.6-规格.md` §十九。
GEAR_CATEGORY = "gear_upgrade"

# 章1 的三张配方页，**按作者 §8.2 的表逐行读下来**的顺序（上/下 = recipe / recipe2）
GEAR_BLANK_ROWS = [
    ("golden_mace_blank", "golden_trident_blank"),   # 2 右：上 重锤 / 下 三叉戟
    ("golden_bow_blank", "golden_crossbow_blank"),   # 3 左：上 弓 / 下 弩
    ("golden_shield_blank", None),                   # 3 右：盾牌
]

# 「后页」的 14 件**固定顺序**（§8.3 正文逐字给出；§8.12 第 2 条把它列为推断值）
FORGE_ORDER = ["sword", "mace", "trident", "bow", "crossbow", "axe", "pickaxe", "shovel",
               "hoe", "shield", "helmet", "chestplate", "leggings", "boots"]

# 9 章：(章节 id, 封面图标)。章1 = 联动与金制胚底；章2~9 = 八族装备，
# 顺序 = METALS = 作者给的章节顺序（烈燃金 → 万坚金 → 树棘金 → 幽咆金 →
#          靛海金 → 巫毒金 → 结雷金 → 幻惑金）。
GEAR_CHAPTERS = [("linkage", "golden_mace_blank")] + \
                [("%s" % metal, "%s_sword" % metal) for metal, _core in METALS]

# 三个文案页的语言键后缀（顺序 = 文档的「1 左 / 1 右 / 2 左」）
GEAR_TEXT_LABELS = ("1_left", "1_right", "2_left")


def _gear_text_keys(chapter):
    return ["%s.page.gear_%s_%s" % (LANG, chapter, label) for label in GEAR_TEXT_LABELS]


def entry_gear_linkage():
    pages = [text_page(_k) for _k in _gear_text_keys("linkage")]
    for a, b in GEAR_BLANK_ROWS:
        pages.append(crafting_page(a, b))
    return entry("gear_linkage", GEAR_CATEGORY, "golden_mace_blank", 0, pages)


def entry_gear_metal(metal, sortnum):
    pages = [text_page(_k) for _k in _gear_text_keys(metal)]
    for i in range(0, len(FORGE_ORDER), 2):
        pages.append(smithing_page("smithing_%s_%s" % (metal, FORGE_ORDER[i]),
                                   "smithing_%s_%s" % (metal, FORGE_ORDER[i + 1])))
    return entry("gear_%s" % metal, GEAR_CATEGORY, "%s_sword" % metal, sortnum, pages)


def _make_gear_metal_builder(metal, sortnum):
    def build():
        return entry_gear_metal(metal, sortnum)
    build.__name__ = "entry_gear_%s" % metal
    return build


GEAR_ENTRIES = [entry_gear_linkage] + [
    _make_gear_metal_builder(metal, index)
    for index, (metal, _core) in enumerate(METALS, start=1)
]

# --------------------------------------------------------------------------------------
# bg-book §九 追加轮（2026-10-06 20:02）：「商人与古董」3 章（替掉该类别旧占位两节）
# --------------------------------------------------------------------------------------
#
# 形状**沿用 §八**（同一份需求文档的表格形状：每一行标签 = **一个 Patchouli 页**，
# 相邻两页在书里组成一屏「跨页」）：
#
#   章1 · 关于易金商人（封面 = 易金柜台）：**3 页**
#       1 左 text / 1 右 crafting(易金柜台) + 正文 / 2 左 spotlight(礼品金票) + 正文
#   章2 · 礼品盒（封面 = 万宝礼物盒）：**7 页**
#       1 左 text（唯一没有图标的一页）/ 1 右~4 左 = spotlight(盒/老古董) + 正文
#   章3 · 古董器具（封面 = 万古烬骸剑）：**10 页**
#       1 左 spotlight(古董 剑/斧/镐/锹/锄/刀) + 正文 + 页眉
#       1 右 **上**：两种升级模板配方 = **1 页**（`smithing_template_antique` +
#              `smithing_template_echo_shard`，两份产物同为 `netherite_antique_upgrade_smithing_template`）
#       1 右 **下**：六种器具的升级配方 = **3 页 × 2**（顺序照 1 左的「剑/斧/镐/锹/锄/刀」）
#       2 左 spotlight(万古烬骸剑 / 幽冥断骸刀) + 正文 + 页眉
#       2 右 spotlight(斧/镐/锹/锄) + 正文 + 页眉
#       3 左 text / 3 右 crafting(尘埃→小碎片 + 小碎片→碎片) / 4 左 text（备注）
#
# ⚠ **门禁项**（照 §八 的同一条口径，不是我们的退化方案）：作者在 §9.4 第 1 页右写了
#   「两种配方随时间不断变换」+「六种器具的配方随时间不断变换」= **8 个配方槽**，
#   而 Patchouli 的配方页**只有 recipe / recipe2 两个槽** ⇒ 只能落成 1 + 3 = 4 页。
#
# ⚠ **推断 / 记账 E1**：「**随时间不断变换**」在 Patchouli 的**配方页**上表达不了
#   （只有 `PageSpotlight` 会按 `ticksInBook / 20` 轮换图标，`PageDoubleRecipe` 没有这个行为）
#   ⇒ 配方部分按「**全部并列展示**」落地；图标部分（1 左 / 2 左 / 2 右）**照轮换**。
#   记账在 `docs/1.6-规格.md` §21（作者一句话可改）。
#
# ⚠ **推断 / 记账 E2**：六件里 `upgrade_netherite_antique_knife` 与 `bettergold:antique_knife` /
#   `bettergold:netherite_antique_knife` **只在装了农夫乐事时存在**
#   （`fd/FdItems` 的 `DeferredRegister` 由 `FdModule` 按环境挂载；recipe 自带
#   `neoforge:mod_loaded(farmersdelight)` 条件）⇒ **没装乐事时**：刀具那两页空、轮换图标里
#   刀具会取不到 ⇒ 手册树是**单份静态 JSON**、不能按环境分岔 ⇒ **记账**
#   （作者一句话可改成"只挂 5 件"）。§八 的 D2（mut 配方二选一）是同一类记账。
MERCHANT_CATEGORY = "merchant_antiques"

# 章3 的六件器具，**顺序 = §9.4 第 1 页左逐字给出的「剑/斧/镐/锹/锄/刀」**（不是推断值）
ANTIQUE_TRUE_ORDER = ["sword", "axe", "pickaxe", "shovel", "hoe", "knife"]
# §9.4 第 1 页右的「两种配方」= 两份产出**同一张升级模板**的锻造配方（已核实产物 id 相同）
ANTIQUE_TEMPLATE_RECIPES = ["smithing_template_antique", "smithing_template_echo_shard"]
# §9.4 第 3 页右：尘埃 → 小碎片；小碎片 → 碎片
ANTIQUE_SCRAP_RECIPES = ["netherite_dust_to_small_scrap", "small_scrap_to_scrap"]
# 三张「轮换图标」页（作者写了「按此顺序不断替换」/「随时间不断替换」）
ANTIQUE_1_LEFT_ITEMS = ["bettergold:antique_%s" % _t for _t in ANTIQUE_TRUE_ORDER]
ANTIQUE_2_LEFT_ITEMS = ["bettergold:netherite_antique_sword",
                        "bettergold:netherite_antique_knife"]
ANTIQUE_2_RIGHT_ITEMS = ["bettergold:netherite_antique_%s" % _t
                         for _t in ("axe", "pickaxe", "shovel", "hoe")]

# 章2 的 7 行：(页标签, 该页图标物品 或 None)
MERCHANT_GIFT_ROWS = [
    ("1_left", None),
    ("1_right", "treasure_gift_box"),
    ("2_left", "curio_box"),
    ("2_right", "unwanted_antique"),
    ("3_left", "idol_gift_box"),
    ("3_right", "gourmet_box"),
    ("4_left", "alchemy_materials_box"),
]


def _ph(entry_id, label):
    """该页正文的语言键"""
    return "%s.page.%s_%s" % (LANG, entry_id, label)


def _pht(entry_id, label):
    """该页**页眉**（作者写的「上边字体『…』」）的语言键 —— 用键而不是字面中文，
    这样 en_us 侧也能有英文页眉（§七 当时用的是字面中文，本轮改成键并记账）。"""
    return "%s.page.%s_%s_title" % (LANG, entry_id, label)


def entry_merchant_intro():
    """章1 · 关于易金商人（封面 = 易金柜台）。3 页。"""
    pages = [
        text_page(_ph("merchant_intro", "1_left")),
        # 「（上边挂：易金柜台配方）」⇒ 配方页本来就自带正文槽（PageDoubleRecipe extends PageWithText）
        crafting_page("gold_exchange_counter", None, None, _ph("merchant_intro", "1_right")),
        # 「（中上边挂：礼品金票）」
        spotlight_page("bettergold:gift_gold_ticket", _ph("merchant_intro", "2_left")),
    ]
    return entry("merchant_intro", MERCHANT_CATEGORY, "gold_exchange_counter", 0, pages)


def entry_merchant_gift_box():
    """章2 · 礼品盒（封面 = 万宝礼物盒）。7 页（1 行 = 1 页）。"""
    pages = []
    for label, icon in MERCHANT_GIFT_ROWS:
        key = _ph("merchant_gift_box", label)
        if icon is None:
            pages.append(text_page(key))
        else:
            pages.append(spotlight_page("bettergold:%s" % icon, key))
    return entry("merchant_gift_box", MERCHANT_CATEGORY, "treasure_gift_box", 1, pages)


def entry_merchant_antique_gear():
    """章3 · 古董器具（封面 = 万古烬骸剑）。10 页（1 右 那一行展开成 4 个配方页）。"""
    pages = [
        spotlight_page(ANTIQUE_1_LEFT_ITEMS, _ph("merchant_antique_gear", "1_left"),
                       _pht("merchant_antique_gear", "1_left")),
        smithing_page(ANTIQUE_TEMPLATE_RECIPES[0], ANTIQUE_TEMPLATE_RECIPES[1]),
    ]
    for _i in range(0, len(ANTIQUE_TRUE_ORDER), 2):
        pages.append(smithing_page(
            "upgrade_netherite_antique_%s" % ANTIQUE_TRUE_ORDER[_i],
            "upgrade_netherite_antique_%s" % ANTIQUE_TRUE_ORDER[_i + 1]))
    pages.append(spotlight_page(ANTIQUE_2_LEFT_ITEMS, _ph("merchant_antique_gear", "2_left"),
                                _pht("merchant_antique_gear", "2_left")))
    pages.append(spotlight_page(ANTIQUE_2_RIGHT_ITEMS, _ph("merchant_antique_gear", "2_right"),
                                _pht("merchant_antique_gear", "2_right")))
    pages.append(text_page(_ph("merchant_antique_gear", "3_left")))
    pages.append(crafting_page(ANTIQUE_SCRAP_RECIPES[0], ANTIQUE_SCRAP_RECIPES[1]))
    pages.append(text_page(_ph("merchant_antique_gear", "4_left")))
    return entry("merchant_antique_gear", MERCHANT_CATEGORY, "netherite_antique_sword", 2, pages)


MERCHANT_ENTRIES = [entry_merchant_intro, entry_merchant_gift_box, entry_merchant_antique_gear]

BOOK = {
    "name": "%s.name" % LANG,
    "subtitle": "%s.subtitle" % LANG,
    "landing_text": "%s.landing" % LANG,
    # The item that represents this book is OURS (bg-book §3.1.2): `dont_generate_book` keeps
    # Patchouli from minting its own guide_book based stack, and `custom_book_item` is parsed by
    # vanilla's ItemParser (so a bare "namespace:path" is valid -- a malformed one only logs a
    # warning and silently becomes ItemStack.EMPTY, which is why the validator checks it).
    "dont_generate_book": True,
    "custom_book_item": ITEM,
    # ⚠ REQUIRED since Patchouli 1.20: the old data-pack-side content loading was removed, so this
    # flag must be true and all categories/entries live under assets/ (see the module docstring).
    "use_resource_pack": True,
    "i18n": True,
    "version": "1.6.0",
}


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def main():
    # data side: book.json only (and nothing else -- leftover contents here make Patchouli skip
    # the book entirely, that is exactly the bug this round hit at A level)
    if os.path.isdir(BOOK_DIR):
        shutil.rmtree(BOOK_DIR)
    os.makedirs(BOOK_DIR, exist_ok=True)
    write_json(os.path.join(BOOK_DIR, "book.json"), BOOK)

    # assets side: categories + entries, per language
    if os.path.isdir(ASSET_DIR):
        shutil.rmtree(ASSET_DIR)
    for lang in ("zh_cn", "en_us"):
        for name, icon, sortnum in CATEGORIES:
            write_json(
                os.path.join(ASSET_DIR, lang, "categories", "%s.json" % name),
                category(name, icon, sortnum),
            )
        for builder in ENTRIES + CHAPTER_ENTRIES + GEAR_ENTRIES + MERCHANT_ENTRIES:
            data = builder()
            write_json(
                os.path.join(ASSET_DIR, lang, "entries", "%s.json" % data["name"].rsplit(".", 1)[-1]),
                data,
            )

    pages = sum(len(b()["pages"]) for b in ENTRIES)
    chapter_pages = sum(len(b()["pages"]) for b in CHAPTER_ENTRIES)
    gear_pages = sum(len(b()["pages"]) for b in GEAR_ENTRIES)
    merchant_pages = sum(len(b()["pages"]) for b in MERCHANT_ENTRIES)
    retired_pages = sum(len(b()["pages"]) for b in RETIRED_ENTRIES)
    print(
        "handbook written: 1 book (data/) + %d categories + %d entries + %d pages x2 languages "
        "(assets/) -> %s + %s"
        % (len(CATEGORIES),
           len(ENTRIES) + len(CHAPTER_ENTRIES) + len(GEAR_ENTRIES) + len(MERCHANT_ENTRIES),
           pages + chapter_pages + gear_pages + merchant_pages, BOOK_DIR, ASSET_DIR)
    )
    print(
        "  §6 chapters (bg-book append round): %d entries / %d pages "
        "(aux=%d core=%d knowledge=%d; 1 row = 1 spread = 2 pages; knowledge 第1页 已被 §八 删除)"
        % (len(CHAPTER_ENTRIES), chapter_pages,
           len(entry_auxiliary_materials()["pages"]),
           len(entry_core_materials()["pages"]),
           len(entry_golden_knowledge()["pages"]))
    )
    print(
        "  §8 gear chapters (bg-book §八): %d entries / %d pages "
        "(linkage=%d, 八族各=%d；后页 14 件 = 7 页 x 2 配方 = Patchouli 的结构上限)"
        % (len(GEAR_ENTRIES), gear_pages,
           len(entry_gear_linkage()["pages"]),
           len(GEAR_ENTRIES[1]()["pages"]))
    )
    print(
        "  §9 merchant/antiques chapters (bg-book §九): %d entries / %d pages "
        "(intro=%d, gift_box=%d, antique_gear=%d; 1 右 那一行 = 1+3 个配方页 = Patchouli 的结构上限)"
        % (len(MERCHANT_ENTRIES), merchant_pages,
           len(entry_merchant_intro()["pages"]),
           len(entry_merchant_gift_box()["pages"]),
           len(entry_merchant_antique_gear()["pages"]))
    )
    print(
        "  RETIRED (§八 两个装备条目 + §九 两个商人与古董旧占位 + bg-fix3 §三 两个骨架条目，不写盘): "
        "tools=%d + armor=%d + merchant=%d + antiques=%d + metal_tour=%d + upgrade_templates=%d = %d"
        % (len(entry_tools_per_family()["pages"]), len(entry_armor_per_family()["pages"]),
           len(entry_merchant()["pages"]), len(entry_antiques()["pages"]),
           len(entry_metal_tour()["pages"]), len(entry_upgrade_templates()["pages"]),
           retired_pages)
    )


if __name__ == "__main__":
    main()
