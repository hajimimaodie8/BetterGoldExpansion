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
        for builder in ENTRIES:
            data = builder()
            write_json(
                os.path.join(ASSET_DIR, lang, "entries", "%s.json" % data["name"].rsplit(".", 1)[-1]),
                data,
            )

    pages = sum(len(b()["pages"]) for b in ENTRIES)
    print(
        "handbook written: 1 book (data/) + %d categories + %d entries + %d pages x2 languages "
        "(assets/) -> %s + %s"
        % (len(CATEGORIES), len(ENTRIES), pages, BOOK_DIR, ASSET_DIR)
    )


if __name__ == "__main__":
    main()
