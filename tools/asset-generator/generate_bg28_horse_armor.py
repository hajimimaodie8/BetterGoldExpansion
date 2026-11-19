#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1.8 阶段 3 · 段 B：12 套马铠的贴图 / 模型 / 语言（§H-33..35）。

* 贴图 **1:1 字节复制**（作者 zip `马铠/` 24 张，一个像素都不改）：
  - `<族>马铠.png`（64×64，坐骑实体贴图）→
    `assets/bettergold/textures/entity/horse/armor/horse_armor_<族>.png`
    （路径由 `AnimalArmorItem.BodyType.EQUESTRIAN` 从 ArmorMaterial 的 key 推出）
  - `<族>马铠物品.png`（16×16）→ `assets/bettergold/textures/item/<族>_horse_armor.png`
* 模型：`item/generated` 单层（16×16 图标，与其它物品同构）。
* 语言：中英各 +12 键；**追加到文件末尾**（不重排、不重写既有行）。
* 认亲表：`docs/1.8-素材认亲/阶段3B/认亲表.tsv`（源 → 目标 → 字节数 → SHA256）。

用法：`python tools/asset-generator/generate_bg28_horse_armor.py`
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZIP = r"E:\mc\mc资料\新的新约\更有用的金 新约10 (1).zip"
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold")
TEX_ENTITY = os.path.join(ASSETS, "textures", "entity", "horse", "armor")
TEX_ITEM = os.path.join(ASSETS, "textures", "item")
MODELS = os.path.join(ASSETS, "models", "item")
LANG = os.path.join(ASSETS, "lang")
EVID = os.path.join(ROOT, "docs", "1.8-素材认亲", "阶段3B")

# (zip 里的中文族名, 族 id, 英文名)
FAMILIES = [
    ("烈燃金", "flamegold", "Flamegold"),
    ("巫毒金", "voodoogold", "Voodoogold"),
    ("结雷金", "thundergold", "Thundergold"),
    ("靛海金", "indigoseagold", "Indigoseagold"),
    ("幻惑金", "illusiongold", "Illusiongold"),
    ("树棘金", "thornsgold", "Thornsgold"),
    ("幽咆金", "echogold", "Echogold"),
    ("万坚金", "sturdygold", "Sturdygold"),
    ("混沌金", "chaosgold", "Chaosgold"),
    ("崩乱合金", "chaosalloy", "Chaosalloy"),
    ("翠风金", "windgold", "Windgold"),
    ("凛冰金", "frostgold", "Frostgold"),
]


def append_lang(path: str, entries: list[tuple[str, str]]) -> None:
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8")
    existing = json.loads(text)
    missing = [(k, v) for k, v in entries if k not in existing]
    if not missing:
        return
    body = text.rstrip()
    assert body.endswith("}")
    inner = body[:-1].rstrip()
    lines = [json.dumps(k, ensure_ascii=False) + ": " + json.dumps(v, ensure_ascii=False)
             for k, v in missing]
    out = inner + ",\n" + ",\n".join("  " + line for line in lines) + "\n}\n"
    with open(path, "wb") as f:
        f.write(out.encode("utf-8"))


def main() -> None:
    os.makedirs(TEX_ENTITY, exist_ok=True)
    os.makedirs(TEX_ITEM, exist_ok=True)
    os.makedirs(MODELS, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    rows = []
    zh_entries, en_entries = [], []
    with zipfile.ZipFile(ZIP) as z:
        for cn, fid, en in FAMILIES:
            mount_src = "马铠/%s马铠.png" % cn
            icon_src = "马铠/%s马铠物品.png" % cn
            mount_dst = os.path.join(TEX_ENTITY, "horse_armor_%s.png" % fid)
            icon_dst = os.path.join(TEX_ITEM, "%s_horse_armor.png" % fid)
            for src, dst in ((mount_src, mount_dst), (icon_src, icon_dst)):
                data = z.read(src)
                with open(dst, "wb") as f:
                    f.write(data)
                rows.append((src, os.path.relpath(dst, ROOT).replace("\\", "/"),
                             len(data), hashlib.sha256(data).hexdigest()))
            model = {
                "parent": "minecraft:item/generated",
                "textures": {"layer0": "bettergold:item/%s_horse_armor" % fid},
            }
            with open(os.path.join(MODELS, "%s_horse_armor.json" % fid), "wb") as f:
                f.write((json.dumps(model, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            zh_entries.append(("item.bettergold.%s_horse_armor" % fid, "%s马铠" % cn))
            en_entries.append(("item.bettergold.%s_horse_armor" % fid, "%s Horse Armor" % en))
    append_lang(os.path.join(LANG, "zh_cn.json"), zh_entries)
    append_lang(os.path.join(LANG, "en_us.json"), en_entries)
    with open(os.path.join(EVID, "认亲表.tsv"), "wb") as f:
        head = "源(zip内)\t目标(仓内)\t字节数\tSHA256\n"
        f.write(head.encode("utf-8"))
        for row in rows:
            f.write(("\t".join(str(x) for x in row) + "\n").encode("utf-8"))
    print("textures/models:", len(rows) // 2, "sets,", len(rows), "files")
    print("lang zh/en:", len(zh_entries), len(en_entries))
    print("认亲表:", os.path.join(EVID, "认亲表.tsv"))


if __name__ == "__main__":
    main()
