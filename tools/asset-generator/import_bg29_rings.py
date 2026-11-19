#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg29（1.8 阶段 3 · 段 C 转化之戒）：素材导入 + 模型 / 语言 / sounds.json / Curios 标签。

设计口径（与 bg25~bg28 一致）：
  * 原始 zip **只读**（绝不改 / 不重打包 / 不改名 / 不移动）；
  * 贴图 = **1:1 字节复制**（sha256 与 zip 内条目逐张比对）；
  * 作者给的 2 张「配方图」只作展示 / 归档，**不落数据**（作者没点名做成配方，与 bg28 的
    `混沌金马铠配方.png` 同一条先例）；
  * mp3 → ogg：`ffmpeg -vn -map 0:a:0 -ac 1 -ar 44100 -c:a libvorbis`（3D 定位音必须单声道）；
  * 归档副本 + 认亲表 → `docs/1.8-素材认亲/阶段3C/`。

用法：python tools/asset-generator/import_bg29_rings.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

REPO = Path(__file__).resolve().parents[2]
ZIP = Path(r"E:\mc\mc资料\新的新约\更有用的金 新约10 (1).zip")
SRC_DIR = "转化之戒/"
ARCHIVE = REPO / "docs" / "1.8-素材认亲" / "阶段3C"
ASSETS = REPO / "src" / "main" / "resources" / "assets" / "bettergold"
TEX_ITEM = ASSETS / "textures" / "item"
TEX_EFFECT = ASSETS / "textures" / "mob_effect"
SOUNDS = ASSETS / "sounds"

# (金属 id, 中文, 英文, zip 内文件名)
RINGS = [
    ("flamegold", "烈火", "Flame", "烈火转化之戒.png"),
    ("sturdygold", "点金", "Gilding", "点金转化之戒.png"),
    ("windgold", "风起", "Windrise", "风起转化之戒.png"),
    ("thornsgold", "木棘", "Thorn", "木棘转化之戒.png"),
    ("echogold", "幽爆", "Echo Burst", "幽爆转化之戒.png"),
    ("frostgold", "冰霜", "Frost", "冰霜转化之戒.png"),
    ("indigoseagold", "水压", "Hydro Pressure", "水压转化之戒.png"),
    ("voodoogold", "毒腺", "Venom Gland", "毒腺转化之戒.png"),
    ("thundergold", "雷波", "Thunder Wave", "雷波转化之戒.png"),
    ("illusiongold", "幻奏", "Phantom Melody", "幻奏转化之戒.png"),
    ("chaosgold", "混源稳定", "Chaos Stabilizer", "混源稳定之戒.png"),
    ("chaosalloy", "分崩离析", "Disintegration", "分崩离析之戒.png"),
]

BLANK = ("ring_blank", "转化之戒胚底", "Ring Blank", "转化之戒胚底.png")

EFFECTS = [
    ("soothe_ii.png", "安抚二式.png"),
    ("soothe_ii_cooldown.png", "安抚二式(冷却中).png"),
]

SOUND = ("thunder_ring.ogg", "雷波转化之戒和新版结雷金建筑方块音效.mp3")

# 只归档、不落数据（作者未点名做成配方）
DISPLAY_ONLY = ["混源稳定之戒配方.png", "转化之戒胚底配方.png"]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if not ZIP.is_file():
        print("[bg29-import-fail] 原始 zip 不在：%s" % ZIP)
        return 2
    z = zipfile.ZipFile(ZIP)
    names = set(z.namelist())
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    TEX_ITEM.mkdir(parents=True, exist_ok=True)
    TEX_EFFECT.mkdir(parents=True, exist_ok=True)
    SOUNDS.mkdir(parents=True, exist_ok=True)

    rows = [["源(zip内)", "目标(仓内)", "字节数", "SHA256"]]
    copied = 0

    def put(src_name: str, dst: Path) -> bytes:
        nonlocal copied
        data = z.read(SRC_DIR + src_name)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        assert dst.read_bytes() == data, "字节复制不一致：%s" % dst
        rows.append([SRC_DIR + src_name, dst.relative_to(REPO).as_posix(),
                     str(len(data)), sha256(data)])
        copied += 1
        return data

    # 1) 12 枚戒指 + 胚底
    for metal, cn, en, fname in RINGS:
        put(fname, TEX_ITEM / ("%s_ring.png" % metal))
    put(BLANK[3], TEX_ITEM / "ring_blank.png")

    # 2) 两个状态图标（18x18，原版 mob_effect 图集的尺寸）
    for dst_name, src_name in EFFECTS:
        put(src_name, TEX_EFFECT / dst_name)

    # 3) mp3 → ogg
    ogg_name, mp3_name = SOUND
    mp3 = z.read(SRC_DIR + mp3_name)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in.mp3"
        src.write_bytes(mp3)
        out = Path(tmp) / "out.ogg"
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-map", "0:a:0",
               "-ac", "1", "-ar", "44100", "-c:a", "libvorbis", str(out)]
        subprocess.run(cmd, check=True)
        ogg = out.read_bytes()
    (SOUNDS / ogg_name).write_bytes(ogg)
    rows.append([SRC_DIR + mp3_name, (SOUNDS / ogg_name).relative_to(REPO).as_posix(),
                 "%d -> %d" % (len(mp3), len(ogg)), sha256(ogg)])
    copied += 1

    # 4) 归档：全部 18 件（只读解压，归档只增不改）
    for info in z.infolist():
        if not info.filename.startswith(SRC_DIR) or info.is_dir():
            continue
        dst = ARCHIVE / Path(info.filename).name
        if not dst.exists():
            dst.write_bytes(z.read(info))
    # 认亲表（12 戒 + 胚底 + 2 状态 + 1 音效 = 16 行 + 表头）
    (ARCHIVE / "认亲表.tsv").write_text(
        "\n".join("\t".join(r) for r in rows) + "\n", encoding="utf-8", newline="\n")

    # 5) 模型（13 件 item/generated 单层）
    models = ASSETS / "models" / "item"
    models.mkdir(parents=True, exist_ok=True)
    for path in [r[0] + "_ring" for r in RINGS] + ["ring_blank"]:
        (models / ("%s.json" % path)).write_text(json.dumps({
            "parent": "minecraft:item/generated",
            "textures": {"layer0": "bettergold:item/%s" % path}
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 6) 语言（中英各 +15：13 物品 + 2 状态）
    for lang in ("zh_cn", "en_us"):
        p = ASSETS / "lang" / ("%s.json" % lang)
        obj = json.loads(p.read_text(encoding="utf-8"))
        for metal, cn, en, _f in RINGS:
            obj["item.bettergold.%s_ring" % metal] = ("%s转化之戒" % cn) if lang == "zh_cn" \
                else ("%s Ring" % en)
        obj["item.bettergold.ring_blank"] = BLANK[1] if lang == "zh_cn" else BLANK[2]
        obj["effect.bettergold.soothe_ii"] = "安抚二式" if lang == "zh_cn" else "Soothe II"
        obj["effect.bettergold.soothe_ii_cooldown"] = \
            "安抚二式（冷却中）" if lang == "zh_cn" else "Soothe II (Cooldown)"
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8", newline="\n")

    # 7) sounds.json（追加雷波专属音效 + 中英字幕键由语言文件给）
    sp = ASSETS / "sounds.json"
    sounds = json.loads(sp.read_text(encoding="utf-8"))
    sounds["thunder_ring"] = {
        "subtitle": "subtitles.bettergold.thunder_ring",
        "sounds": [{"name": "bettergold:thunder_ring", "stream": False}],
    }
    sp.write_text(json.dumps(sounds, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8", newline="\n")
    for lang, text in (("zh_cn", "雷波：雷霆轰响"), ("en_us", "Thunder Wave: thunder crack")):
        p = ASSETS / "lang" / ("%s.json" % lang)
        obj = json.loads(p.read_text(encoding="utf-8"))
        obj["subtitles.bettergold.thunder_ring"] = text
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8", newline="\n")

    # 8) Curios 数据标签（没装 Curios 时这个文件被忽略；戒指物品始终注册）
    tag = REPO / "src" / "main" / "resources" / "data" / "curios" / "tags" / "item" / "ring.json"
    tag.parent.mkdir(parents=True, exist_ok=True)
    tag.write_text(json.dumps({
        "replace": False,
        "values": ["bettergold:%s_ring" % r[0] for r in RINGS],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 9) 配方：转化之戒 × 输入 → 产物（戒指不消耗，见 RingConversionRecipe）
    recipes = {
        "ring_gild_raw_copper": ("sturdygold", "minecraft:raw_copper",
                                 {"id": "minecraft:raw_gold", "count": 1}),
        "ring_gild_raw_iron": ("sturdygold", "minecraft:raw_iron",
                               {"id": "minecraft:raw_gold", "count": 1}),
        "ring_gild_gold_nugget": ("sturdygold", "minecraft:gold_nugget",
                                  {"id": "minecraft:raw_gold", "count": 1}),
        "ring_frost_water_bucket": ("frostgold", "minecraft:water_bucket",
                                    {"id": "minecraft:ice", "count": 1}),
        "ring_pressure_glass_bottle": ("indigoseagold", "minecraft:glass_bottle",
                                       {"id": "minecraft:potion", "count": 1,
                                        "components": {"minecraft:potion_contents":
                                                       {"potion": "minecraft:water"}}}),
        "ring_pressure_bucket": ("indigoseagold", "minecraft:bucket",
                                 {"id": "minecraft:water_bucket", "count": 1}),
    }
    rdir = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"
    rdir.mkdir(parents=True, exist_ok=True)
    for name, (metal, ing, out) in recipes.items():
        body = {
            "type": "bettergold:ring_conversion",
            "ring": "bettergold:%s_ring" % metal,
            "ingredient": ing,
            "result": out,
        }
        (rdir / ("%s.json" % name)).write_text(
            json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    print("[bg29-import-ok] 复制 %d 件（16 行认亲表）；归档 %d 项 → %s"
          % (copied, len(list(ARCHIVE.iterdir())), ARCHIVE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
