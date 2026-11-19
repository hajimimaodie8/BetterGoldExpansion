#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1.8 阶段 3 · 段 A（§G 长矛）的**素材 / 模型 / 语言 / 标签**生成器。

作者给的素材 zip 是**只读**的（一字节不许动，见 AGENTS.md 第 6 条）：
本脚本只用 ``zipfile`` 以只读方式读出 ``长矛/`` 下的 28 张 PNG，然后

* 贴图：**1:1 字节复制**（``矛1`` = 手持帧 → ``<key>_spear_in_hand.png``；
  ``矛2`` = 物品帧 → ``<key>_spear.png``），一个像素都不改；
* 模型：每件两 JSON（``neoforge:separate_transforms`` 主模型 + ``_in_hand`` 子模型），
  形状照抄 SpearCore 自带的 ``netherite_spear`` / ``netherite_spear_in_hand``；
* 语言：中英各 +14 键（**只追加**，不动既有 965 键的顺序与内容）；
* 标签：把 14 件矛加进 ``#minecraft:enchantable/*``（附魔台要给它们选项）；
* 认亲表：``docs/1.8-素材认亲/阶段3/认亲表.tsv``（源 → 目标 → 字节数 → SHA256）。

幂等：重复运行不会重复追加键/标签；贴图每次都重算 SHA 并核对「拷贝后 == zip 内」。

用法：``python tools/asset-generator/generate_bg27_spears.py``
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZIP = r"E:\mc\mc资料\新的新约\更有用的金 新约10 (1).zip"
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold")
TEX = os.path.join(ASSETS, "textures", "item")
MODELS = os.path.join(ASSETS, "models", "item")
LANG = os.path.join(ASSETS, "lang")
TAGS = os.path.join(ROOT, "src", "main", "resources", "data", "minecraft", "tags", "item", "enchantable")
EVID = os.path.join(ROOT, "docs", "1.8-素材认亲", "阶段3")

# (zip 里的文件名主干, 物品 id 前缀, 中文名, 英文名)
#   ⚠ 两件特殊矛的文件名主干已经含「矛」（古董长矛1.png / 夜叉贯骸矛1.png），
#     与「<族>矛1.png」不是同一个规律，所以这里列的是**主干**而不是族名。
SPEARS = [
    ("万坚金矛", "sturdygold", "万坚金矛", "Sturdygold Spear"),
    ("烈燃金矛", "flamegold", "烈燃金矛", "Flamegold Spear"),
    ("翠风金矛", "windgold", "翠风金矛", "Windgold Spear"),
    ("树棘金矛", "thornsgold", "树棘金矛", "Thornsgold Spear"),
    ("幽咆金矛", "echogold", "幽咆金矛", "Echogold Spear"),
    ("凛冰金矛", "frostgold", "凛冰金矛", "Frostgold Spear"),
    ("靛海金矛", "indigoseagold", "靛海金矛", "Indigoseagold Spear"),
    ("巫毒金矛", "voodoogold", "巫毒金矛", "Voodoogold Spear"),
    ("结雷金矛", "thundergold", "结雷金矛", "Thundergold Spear"),
    ("幻惑金矛", "illusiongold", "幻惑金矛", "Illusiongold Spear"),
    ("混沌金矛", "chaosgold", "混沌金矛", "Chaosgold Spear"),
    ("崩乱合金矛", "chaosalloy", "崩乱合金矛", "Chaosalloy Spear"),
    ("古董长矛", "antique", "古董长矛", "Antique Spear"),
    ("夜叉贯骸矛", "yaksha", "夜叉贯骸矛", "Yaksha Bone-Piercing Spear"),
]

# 两张帧：作者命名「<主干>1.png」= 手持、 「<主干>2.png」= 物品图标（主干已含「矛」）
HELD_SUFFIX = "1.png"
ITEM_SUFFIX = "2.png"

# 矛要进哪些附魔标签（1.21 附魔的 supported_items 全是标签）
ENCHANT_TAGS = ["durability", "sharp_weapon", "weapon", "fire_aspect", "sword"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    data = text.encode("utf-8")
    old = None
    if os.path.isfile(path):
        with io.open(path, "rb") as fh:
            old = fh.read()
    if old != data:
        with io.open(path, "wb") as fh:
            fh.write(data)
    return old != data


def write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    old = None
    if os.path.isfile(path):
        with io.open(path, "rb") as fh:
            old = fh.read()
    if old != data:
        with io.open(path, "wb") as fh:
            fh.write(data)
    return old != data


def main_item_model(key: str):
    """主模型：手持帧作为 base（3D/动画那一路），GUI/掉落/展示框用物品帧。"""
    return {
        "loader": "neoforge:separate_transforms",
        "gui_light": "front",
        "base": {
            "parent": "bettergold:item/%s_spear_in_hand" % key,
            "textures": {"layer0": "bettergold:item/%s_spear_in_hand" % key},
        },
        "perspectives": {
            ctx: {
                "parent": "item/generated",
                "textures": {"layer0": "bettergold:item/%s_spear" % key},
            }
            for ctx in ("gui", "fixed", "ground")
        },
    }


def in_hand_model(key: str):
    """手持子模型：只换贴图，display 变换整组继承 SpearCore 的基模型。"""
    return {
        "parent": "spearcore:item/spear_in_hand_base",
        "textures": {"layer0": "bettergold:item/%s_spear_in_hand" % key},
    }


def main() -> int:
    if not os.path.isfile(ZIP):
        print("[bg27-assets] 前置缺失：素材 zip 不存在 -> %s" % ZIP)
        return 2

    zf = zipfile.ZipFile(ZIP, "r")
    names = set(zf.namelist())

    rows = []
    copied = 0
    unchanged = 0

    for cn, key, zh, en in SPEARS:
        for suffix, target in ((HELD_SUFFIX, "%s_spear_in_hand.png" % key),
                               (ITEM_SUFFIX, "%s_spear.png" % key)):
            src = "长矛/%s%s" % (cn, suffix)
            if src not in names:
                print("[bg27-assets] 缺素材：%s" % src)
                return 2
            data = zf.read(src)
            dst = os.path.join(TEX, target)
            changed = write_bytes(dst, data)
            with io.open(dst, "rb") as fh:
                after = fh.read()
            if after != data:
                print("[bg27-assets] 1:1 复制后不一致：%s" % dst)
                return 1
            rows.append((src, "src/main/resources/assets/bettergold/textures/item/%s" % target,
                         len(data), sha(data), zh + ("手持帧" if suffix == HELD_SUFFIX else "物品图标")))
            copied += 1
            unchanged += 0 if changed else 1

        if write_json(os.path.join(MODELS, "%s_spear.json" % key), main_item_model(key)):
            pass
        write_json(os.path.join(MODELS, "%s_spear_in_hand.json" % key), in_hand_model(key))

    zf.close()

    # ---------- 语言（只追加） ----------
    added = {}
    for lang, idx in (("zh_cn", 2), ("en_us", 3)):
        path = os.path.join(LANG, "%s.json" % lang)
        obj = read_json(path)
        before = len(obj)
        for row in SPEARS:
            obj["item.bettergold.%s_spear" % row[1]] = row[idx]
        write_json(path, obj)
        added[lang] = len(obj) - before

    # ---------- 附魔标签（追加、去重） ----------
    tag_added = {}
    for tag in ENCHANT_TAGS:
        path = os.path.join(TAGS, "%s.json" % tag)
        obj = read_json(path) if os.path.isfile(path) else {"replace": False, "values": []}
        values = obj.setdefault("values", [])
        before = len(values)
        for row in SPEARS:
            rid = "bettergold:%s_spear" % row[1]
            if rid not in values:
                values.append(rid)
        obj.setdefault("replace", False)
        write_json(path, obj)
        tag_added[tag] = len(values) - before

    # ---------- 认亲表 ----------
    os.makedirs(EVID, exist_ok=True)
    tsv = os.path.join(EVID, "认亲表.tsv")
    lines = [
        "# 1.8 阶段 3 · 段 A（§G 长矛）素材认亲表 —— 1:1 字节复制，0 像素改动",
        "# 来源 zip（**只读**）：%s" % ZIP,
        "# 源\t目标\t字节数\tSHA256\t用途",
    ]
    for row in rows:
        lines.append("\t".join(str(x) for x in row))
    with io.open(tsv, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    print("[bg27-assets] 贴图 %d 张（其中 %d 张本次无变化）" % (copied, unchanged))
    print("[bg27-assets] 语言 +%d(zh) / +%d(en)；标签追加 %s"
          % (added["zh_cn"], added["en_us"], tag_added))
    print("[bg27-assets] 认亲表 -> %s（%d 行）" % (tsv, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
