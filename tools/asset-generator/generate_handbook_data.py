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
CATEGORIES = [
    ("alchemy_start", "raw_sturdygold", 0),          # 炼金的起步 (materials first)
    ("gear_upgrade", "sturdygold_sword", 1),         # 装备的升级
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


def crafting_page(recipe_a, recipe_b=None, title_key=None):
    page = {"type": "patchouli:crafting", "recipe": "bettergold:%s" % recipe_a}
    if recipe_b:
        page["recipe2"] = "bettergold:%s" % recipe_b
    if title_key:
        page["title"] = title_key
    return page


def spotlight_page(item, text_key=None, title_key=None):
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


ENTRIES = [
    entry_metal_tour,
    entry_upgrade_templates,
    entry_tools_per_family,
    entry_armor_per_family,
    entry_golden_feast,
    entry_merchant,
    entry_antiques,
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
KNOWLEDGE_ROWS = [
    # row 1: left = ingot+nugget of every family (ingot first), right = every template
    ([x for metal, _core in METALS for x in ("bettergold:%s_ingot" % metal,
                                             "bettergold:%s_nugget" % metal)],
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
    """章3 ·「贵金」的知识（封面图标 = 推断值，见上方注释）。"""
    pages = []
    for index, (left_items, right_items) in enumerate(KNOWLEDGE_ROWS, start=1):
        pages.append(spotlight_page(left_items, "%s.page.knowledge_%d_left" % (LANG, index)))
        pages.append(spotlight_page(right_items, "%s.page.knowledge_%d_right" % (LANG, index)))
    return entry("golden_knowledge", "alchemy_start", "sturdygold_ingot", 4, pages)


CHAPTER_ENTRIES = [
    entry_auxiliary_materials,
    entry_core_materials,
    entry_golden_knowledge,
]

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
        for builder in ENTRIES + CHAPTER_ENTRIES:
            data = builder()
            write_json(
                os.path.join(ASSET_DIR, lang, "entries", "%s.json" % data["name"].rsplit(".", 1)[-1]),
                data,
            )

    pages = sum(len(b()["pages"]) for b in ENTRIES)
    chapter_pages = sum(len(b()["pages"]) for b in CHAPTER_ENTRIES)
    print(
        "handbook written: 1 book (data/) + %d categories + %d entries + %d pages x2 languages "
        "(assets/) -> %s + %s"
        % (len(CATEGORIES), len(ENTRIES) + len(CHAPTER_ENTRIES), pages + chapter_pages,
           BOOK_DIR, ASSET_DIR)
    )
    print(
        "  §6 chapters (bg-book append round): %d entries / %d pages "
        "(aux=%d core=%d knowledge=%d; 1 row = 1 spread = 2 pages)"
        % (len(CHAPTER_ENTRIES), chapter_pages,
           len(entry_auxiliary_materials()["pages"]),
           len(entry_core_materials()["pages"]),
           len(entry_golden_knowledge()["pages"]))
    )


if __name__ == "__main__":
    main()
