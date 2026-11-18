#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1.8 阶段 1（bg25）素材 / 模型 / 数据生成器。

范围 = docs/1.8-规格-新的新约.md §A–§D（第 1–17 条）：
  金染草 / 金染土径 / 金沙 / 金沙玻璃（16 连接态）/ 金沙玻璃板 / 金丝树（苗、叶、13 件建材、
  木棍）/ 黄金国浮现之尘 / 金草丛、金高草丛、金盏花、金郁金香。

铁律：
  * 原始 zip 只读；本脚本只从 docs/1.8-新约10-素材清单/ 下的归档副本读取。
  * 贴图 1:1 字节复制；作者本轮单独授权「花草纯黑外边框改全透明」的那 4 张
    （金草丛 / 金高草丛上 / 金高草丛下 / 金盏花 / 金郁金香）由 strip_black_border() 处理，
    判据 = 只处理「与图片外边框 4 连通」的、alpha>0 且 RGB 恰为 (0,0,0) 的像素；
    主体内黑色一个像素都不动。若没有这种像素，写回原始字节（sha 不变）。
  * 认亲表 / 改前改后 / SHA256 写到 docs/1.8-素材认亲/。

用法：py -3 tools/asset-generator/generate_bg25_agriculture.py
退出码：0 成功；2 前置缺失（归档 / 原版模板 jar / 语言文件）。
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src" / "main" / "resources"
ASSETS = RES / "assets" / "bettergold"
DATA = RES / "data"
ARCHIVE = ROOT / "docs" / "1.8-新约10-素材清单"
NEW10 = ARCHIVE / "新约10"
PATHS = ARCHIVE / "金然土径补充"
KINSHIP = ROOT / "docs" / "1.8-素材认亲"
BLACK = KINSHIP / "黑边处理"
VANILLA_JAR = ROOT / "build" / "moddev" / "artifacts" / \
    "neoforge-21.1.228-client-extra-aka-minecraft-resources.jar"

if not NEW10.is_dir() or not PATHS.is_dir():
    print("[bg25-gen] 素材归档缺失：", ARCHIVE)
    sys.exit(2)
if not VANILLA_JAR.is_file():
    print("[bg25-gen] 原版模板 jar 缺失：", VANILLA_JAR, "（先跑一次 gradlew build/setup）")
    sys.exit(2)

TEXTURE_ROWS = []       # (source, target, bytes, sha256, transform)


def sha256(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def strip_black_border(data: bytes):
    """只去掉与图片外边框连通的纯黑像素（alpha>0 & RGB==0,0,0），返回 (bytes, removed)。"""
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    w, h = im.size
    px = im.load()
    black = {(x, y) for y in range(h) for x in range(w)
             if px[x, y][3] > 0 and px[x, y][0] == 0 and px[x, y][1] == 0 and px[x, y][2] == 0}
    if not black:
        return data, 0
    stack = [p for p in black if p[0] in (0, w - 1) or p[1] in (0, h - 1)]
    seen = set(stack)
    while stack:
        x, y = stack.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) in black and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))
    if not seen:
        return data, 0
    for x, y in seen:
        px[x, y] = (0, 0, 0, 0)
    out = io.BytesIO()
    im.save(out, format="PNG")
    return out.getvalue(), len(seen)


def copy_texture(src: Path, dst_rel: str, plant_border: bool = False):
    raw = src.read_bytes()
    data = raw
    removed = 0
    if plant_border:
        BLACK.mkdir(parents=True, exist_ok=True)
        before = BLACK / (dst_rel.replace("/", "_") + ".before.png")
        after = BLACK / (dst_rel.replace("/", "_") + ".after.png")
        before.write_bytes(raw)
        data, removed = strip_black_border(raw)
        after.write_bytes(data)
        if removed == 0 and data != raw:
            data = raw  # 理论不可达：无黑边时必须原样写回
    dst = ASSETS / "textures" / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    transform = "1:1" if data == raw else ("black-border-strip(%d px)" % removed)
    TEXTURE_ROWS.append((src.relative_to(ARCHIVE).as_posix(), "textures/" + dst_rel,
                         len(data), sha256(data), transform))
    return removed


# ==================== 贴图清单（源 → 目标） ====================
PLANT_BORDER = {
    "block/gold_short_grass.png",
    "block/gold_tall_grass_top.png",
    "block/gold_tall_grass_bottom.png",
    "block/gold_marigold.png",
    "block/gold_tulip.png",
}

TEXTURES = [
    (NEW10 / "金染草方块顶.png", "block/gold_infused_grass_block_top.png"),
    (NEW10 / "金染草方块四面.png", "block/gold_infused_grass_block_side.png"),
    (NEW10 / "金沙.png", "block/gold_sand.png"),
    (NEW10 / "金玻璃.png", "block/gold_sand_glass.png"),
    (NEW10 / "金玻璃板边框.png", "block/gold_sand_glass_pane.png"),
    (NEW10 / "金玻璃板边框.png", "item/gold_sand_glass_pane.png"),
    (NEW10 / "金丝木.png", "block/gold_silk_log.png"),
    (NEW10 / "金丝木原木顶底.png", "block/gold_silk_log_top.png"),
    (NEW10 / "去皮金丝木.png", "block/stripped_gold_silk_log.png"),
    (NEW10 / "去皮金丝木原木顶底.png", "block/stripped_gold_silk_log_top.png"),
    (NEW10 / "金丝木板.png", "block/gold_silk_planks.png"),
    (NEW10 / "金丝木门上.png", "block/gold_silk_door_top.png"),
    (NEW10 / "金丝木门下.png", "block/gold_silk_door_bottom.png"),
    (NEW10 / "金丝木活板门.png", "block/gold_silk_trapdoor.png"),
    (NEW10 / "金丝树叶.png", "block/gold_silk_leaves.png"),
    (NEW10 / "金丝树苗.png", "block/gold_silk_sapling.png"),
    (NEW10 / "金草丛.png", "block/gold_short_grass.png"),
    (NEW10 / "金高草丛上.png", "block/gold_tall_grass_top.png"),
    (NEW10 / "金高草丛下.png", "block/gold_tall_grass_bottom.png"),
    (NEW10 / "金盏花.png", "block/gold_marigold.png"),
    (NEW10 / "金郁金香.png", "block/gold_tulip.png"),
    (PATHS / "1794757065663.png", "block/gold_infused_dirt_path_top.png"),
    (PATHS / "1794757061056.png", "block/gold_infused_dirt_path_side.png"),
    (NEW10 / "金丝木门物品.png", "item/gold_silk_door.png"),
    (NEW10 / "金丝木棍.png", "item/gold_silk_stick.png"),
    (NEW10 / "黄金国浮现之尘.png", "item/el_dorado_dust.png"),
]

# 16 态：无连接 = 金玻璃.png（已在上面）；15 个连接态 = 素材文件夹
SEAMLESS = ["u", "d", "l", "r", "ud", "ul", "ur", "dl", "dr", "lr",
            "udl", "udr", "ulr", "dlr", "udlr"]
for _name in SEAMLESS:
    TEXTURES.append((NEW10 / "无缝化的金沙玻璃" / (_name + ".png"),
                     "block/gold_sand_glass_%s.png" % _name))

# 金丝树叶 12 帧 + 催熟粒子
for _i in range(12):
    TEXTURES.append((NEW10 / "金丝树叶粒子" / ("%d.png" % _i),
                     "particle/gold_silk_leaves_%d.png" % _i))
TEXTURES.append((NEW10 / "金骨粉和黄金国浮现之尘的粒子.png", "particle/golden_growth.png"))


def write_json(rel: str, obj):
    p = RES / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(rel: str):
    p = RES / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def write_text(rel: str, text: str):
    p = RES / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def merge_tag(rel: str, values: list[str]):
    """把 values 追加进已有标签（保留原条目与 replace:false）；不存在则新建。"""
    current = read_json(rel)
    if current is None:
        current = {"replace": False, "values": []}
    if isinstance(current, list):
        current = {"replace": False, "values": current}
    existing = list(current.get("values", []))
    for v in values:
        if v not in existing:
            existing.append(v)
    current["replace"] = False
    current["values"] = existing
    write_json(rel, current)


# ==================== 1. 贴图（1:1 / 授权去黑边） ====================
for src, dst in TEXTURES:
    if not src.is_file():
        print("[bg25-gen] 素材缺失：", src)
        sys.exit(2)
    copy_texture(src, dst, dst in PLANT_BORDER)

# ==================== 2. 模型 ====================
def cube_all(tex):
    return {"parent": "minecraft:block/cube_all", "textures": {"all": tex}}


def cube_column(side, end):
    return {"parent": "minecraft:block/cube_column",
            "textures": {"side": side, "end": end}}


def cube_bottom_top(top, side, bottom):
    return {"parent": "minecraft:block/cube_bottom_top",
            "textures": {"top": top, "side": side, "bottom": bottom}}


def cross(tex):
    return {"parent": "minecraft:block/cross", "textures": {"cross": tex}}


def child(parent, textures):
    return {"parent": parent, "textures": textures}


def simple_model(name, tex):
    write_json("assets/bettergold/models/block/%s.json" % name, cube_all(tex))


# 基础方块
simple_model("gold_sand", "bettergold:block/gold_sand")
simple_model("gold_sand_glass", "bettergold:block/gold_sand_glass")
simple_model("gold_silk_planks", "bettergold:block/gold_silk_planks")
simple_model("gold_silk_leaves", "bettergold:block/gold_silk_leaves")
write_json("assets/bettergold/models/block/gold_silk_log.json",
            cube_column("bettergold:block/gold_silk_log", "bettergold:block/gold_silk_log_top"))
write_json("assets/bettergold/models/block/gold_silk_wood.json",
            cube_all("bettergold:block/gold_silk_log"))
write_json("assets/bettergold/models/block/stripped_gold_silk_log.json",
            cube_column("bettergold:block/stripped_gold_silk_log",
                        "bettergold:block/stripped_gold_silk_log_top"))
write_json("assets/bettergold/models/block/stripped_gold_silk_wood.json",
            cube_all("bettergold:block/stripped_gold_silk_log"))
write_json("assets/bettergold/models/block/gold_infused_grass_block.json",
            cube_bottom_top("bettergold:block/gold_infused_grass_block_top",
                            "bettergold:block/gold_infused_grass_block_side",
                            "bettergold:block/gold_infused_dirt"))

# 金染土径：逐字照原版 dirt_path 模型，只换贴图
write_json("assets/bettergold/models/block/gold_infused_dirt_path.json", {
    "parent": "minecraft:block/block",
    "textures": {
        "particle": "bettergold:block/gold_infused_dirt",
        "top": "bettergold:block/gold_infused_dirt_path_top",
        "side": "bettergold:block/gold_infused_dirt_path_side",
        "bottom": "bettergold:block/gold_infused_dirt",
    },
    "elements": [{
        "from": [0, 0, 0], "to": [16, 15, 16],
        "faces": {
            "down": {"uv": [0, 0, 16, 16], "texture": "#bottom", "cullface": "down"},
            "up": {"uv": [0, 0, 16, 16], "texture": "#top"},
            "north": {"uv": [0, 1, 16, 16], "texture": "#side", "cullface": "north"},
            "south": {"uv": [0, 1, 16, 16], "texture": "#side", "cullface": "south"},
            "west": {"uv": [0, 1, 16, 16], "texture": "#side", "cullface": "west"},
            "east": {"uv": [0, 1, 16, 16], "texture": "#side", "cullface": "east"},
        },
    }],
})

# 16 张玻璃模型：无连接用 金玻璃.png；15 个连接态用对应贴图
glass_models = {"": "bettergold:block/gold_sand_glass"}
for name in SEAMLESS:
    tex = "bettergold:block/gold_sand_glass_%s" % name
    simple_model("gold_sand_glass_%s" % name, tex)
    glass_models[name] = "bettergold:block/gold_sand_glass_%s" % name

# 玻璃板：5 个模板子模型
write_json("assets/bettergold/models/block/gold_sand_glass_pane_post.json",
            child("minecraft:block/template_glass_pane_post",
                  {"edge": "bettergold:block/gold_sand_glass_pane",
                   "pane": "bettergold:block/gold_sand_glass_pane"}))
for _m in ("side", "side_alt"):
    write_json("assets/bettergold/models/block/gold_sand_glass_pane_%s.json" % _m,
                child("minecraft:block/template_glass_pane_%s" % _m,
                      {"edge": "bettergold:block/gold_sand_glass_pane",
                       "pane": "bettergold:block/gold_sand_glass_pane"}))
for _m in ("noside", "noside_alt"):
    write_json("assets/bettergold/models/block/gold_sand_glass_pane_%s.json" % _m,
                child("minecraft:block/template_glass_pane_%s" % _m,
                      {"pane": "bettergold:block/gold_sand_glass_pane"}))

# 楼梯 / 台阶 / 栅栏 / 栅栏门 / 门 / 活板门 / 按钮 / 压力板：原版父模型 + 木板贴图
PLANKS = "bettergold:block/gold_silk_planks"
for suffix, parent in (("", "minecraft:block/stairs"),
                       ("_inner", "minecraft:block/stairs_inner"),
                       ("_outer", "minecraft:block/stairs_outer")):
    write_json("assets/bettergold/models/block/gold_silk_stairs%s.json" % suffix,
                child(parent, {"bottom": PLANKS, "top": PLANKS,
                               "side": PLANKS, "particle": PLANKS}))
for suffix, parent in (("", "minecraft:block/slab"),
                       ("_top", "minecraft:block/slab_top")):
    write_json("assets/bettergold/models/block/gold_silk_slab%s.json" % suffix,
                child(parent, {"bottom": PLANKS, "top": PLANKS,
                               "side": PLANKS, "particle": PLANKS}))
for suffix, parent in (("_post", "minecraft:block/fence_post"),
                       ("_side", "minecraft:block/fence_side"),
                       ("_inventory", "minecraft:block/fence_inventory")):
    write_json("assets/bettergold/models/block/gold_silk_fence%s.json" % suffix,
                child(parent, {"texture": PLANKS, "particle": PLANKS}))
for suffix, parent in (("", "minecraft:block/fence_gate"),
                       ("_open", "minecraft:block/fence_gate_open"),
                       ("_wall", "minecraft:block/fence_gate_wall"),
                       ("_wall_open", "minecraft:block/fence_gate_wall_open")):
    write_json("assets/bettergold/models/block/gold_silk_fence_gate%s.json" % suffix,
                child(parent, {"texture": PLANKS, "particle": PLANKS}))
for suffix, parent in (("", "minecraft:block/button"),
                       ("_pressed", "minecraft:block/button_pressed"),
                       ("_inventory", "minecraft:block/button_inventory")):
    write_json("assets/bettergold/models/block/gold_silk_button%s.json" % suffix,
                child(parent, {"texture": PLANKS}))
for suffix, parent in (("", "minecraft:block/pressure_plate_up"),
                       ("_down", "minecraft:block/pressure_plate_down")):
    write_json("assets/bettergold/models/block/gold_silk_pressure_plate%s.json" % suffix,
                child(parent, {"texture": PLANKS}))
for half in ("bottom", "top"):
    for hinge in ("left", "right"):
        for opened in ("", "_open"):
            write_json(
                "assets/bettergold/models/block/gold_silk_door_%s_%s%s.json" % (half, hinge, opened),
                child("minecraft:block/door_%s_%s%s" % (half, hinge, opened),
                      {"bottom": "bettergold:block/gold_silk_door_bottom",
                       "top": "bettergold:block/gold_silk_door_top"}))
for suffix, parent in (("_bottom", "minecraft:block/template_trapdoor_bottom"),
                       ("_top", "minecraft:block/template_trapdoor_top"),
                       ("_open", "minecraft:block/template_trapdoor_open")):
    write_json("assets/bettergold/models/block/gold_silk_trapdoor%s.json" % suffix,
                child(parent, {"texture": "bettergold:block/gold_silk_trapdoor"}))

# 植物
write_json("assets/bettergold/models/block/gold_silk_sapling.json",
            cross("bettergold:block/gold_silk_sapling"))
write_json("assets/bettergold/models/block/gold_short_grass.json",
            cross("bettergold:block/gold_short_grass"))
write_json("assets/bettergold/models/block/gold_tall_grass_top.json",
            cross("bettergold:block/gold_tall_grass_top"))
write_json("assets/bettergold/models/block/gold_tall_grass_bottom.json",
            cross("bettergold:block/gold_tall_grass_bottom"))
# 物品形态用下半块贴图；方块状态只选上/下两个模型
write_json("assets/bettergold/models/block/gold_tall_grass.json",
            cross("bettergold:block/gold_tall_grass_bottom"))
write_json("assets/bettergold/models/block/gold_marigold.json",
            cross("bettergold:block/gold_marigold"))
write_json("assets/bettergold/models/block/gold_tulip.json",
            cross("bettergold:block/gold_tulip"))

# ==================== 3. 物品模型 ====================
def item_generated(tex):
    return {"parent": "minecraft:item/generated", "textures": {"layer0": tex}}


for name, tex in [
        ("gold_silk_stick", "bettergold:item/gold_silk_stick"),
        ("el_dorado_dust", "bettergold:item/el_dorado_dust"),
        ("gold_silk_door", "bettergold:item/gold_silk_door"),
        ("gold_sand_glass_pane", "bettergold:item/gold_sand_glass_pane")]:
    write_json("assets/bettergold/models/item/%s.json" % name, item_generated(tex))

BLOCK_ITEM_MODELS = [
    "gold_infused_grass_block", "gold_infused_dirt_path", "gold_sand",
    "gold_sand_glass", "gold_silk_log", "gold_silk_wood",
    "stripped_gold_silk_log", "stripped_gold_silk_wood", "gold_silk_planks",
    "gold_silk_stairs", "gold_silk_slab", "gold_silk_fence", "gold_silk_fence_gate",
    "gold_silk_trapdoor", "gold_silk_button", "gold_silk_pressure_plate",
    "gold_silk_leaves", "gold_silk_sapling", "gold_short_grass", "gold_tall_grass",
    "gold_marigold", "gold_tulip", "gold_infused_farmland",
]
for name in BLOCK_ITEM_MODELS:
    if name == "gold_silk_button":
        write_json("assets/bettergold/models/item/%s.json" % name,
                    {"parent": "bettergold:block/gold_silk_button_inventory"})
    elif name == "gold_silk_fence":
        write_json("assets/bettergold/models/item/%s.json" % name,
                    {"parent": "bettergold:block/gold_silk_fence_inventory"})
    elif name == "gold_silk_trapdoor":
        write_json("assets/bettergold/models/item/%s.json" % name,
                    {"parent": "bettergold:block/gold_silk_trapdoor_bottom"})
    else:
        write_json("assets/bettergold/models/item/%s.json" % name,
                    {"parent": "bettergold:block/%s" % name})

# ==================== 4. 方块状态 ====================
def simple_state(model):
    return {"variants": {"": {"model": "bettergold:block/" + model}}}


for name in ("gold_infused_grass_block", "gold_infused_dirt_path", "gold_sand",
             "gold_silk_planks", "gold_silk_leaves", "gold_silk_sapling",
             "gold_short_grass", "gold_marigold", "gold_tulip"):
    write_json("assets/bettergold/blockstates/%s.json" % name, simple_state(name))

for name in ("gold_silk_log", "gold_silk_wood",
             "stripped_gold_silk_log", "stripped_gold_silk_wood"):
    write_json("assets/bettergold/blockstates/%s.json" % name, {
        "variants": {
            "axis=y": {"model": "bettergold:block/" + name},
            "axis=x": {"model": "bettergold:block/" + name, "x": 90, "y": 90},
            "axis=z": {"model": "bettergold:block/" + name, "x": 90},
        }
    })

write_json("assets/bettergold/blockstates/gold_tall_grass.json", {
    "variants": {
        "half=lower": {"model": "bettergold:block/gold_tall_grass_bottom"},
        "half=upper": {"model": "bettergold:block/gold_tall_grass_top"},
    }
})

# 金沙玻璃：16 个状态（up/down/left/right，与素材 u/d/l/r 一一对应）
variants = {}
for up in (False, True):
    for down in (False, True):
        for left in (False, True):
            for right in (False, True):
                combo = "".join([ch for ch, flag in
                                 (("u", up), ("d", down), ("l", left), ("r", right)) if flag])
                key = "up=%s,down=%s,left=%s,right=%s" % (
                    str(up).lower(), str(down).lower(), str(left).lower(), str(right).lower())
                variants[key] = {"model": glass_models[combo]}
write_json("assets/bettergold/blockstates/gold_sand_glass.json", {"variants": variants})

# 其余复杂形状：读原版 blockstate 模板，逐字替换模型名（不手抄，避免转角落错）
def vanilla_text(rel: str) -> str:
    with zipfile.ZipFile(VANILLA_JAR) as z:
        return z.read(rel).decode("utf-8")


def clone_state(rel: str, replacements: dict[str, str], dst: str):
    text = vanilla_text(rel)
    for a, b in replacements.items():
        text = text.replace(a, b)
    write_text("assets/bettergold/blockstates/" + dst, text)


clone_state("assets/minecraft/blockstates/glass_pane.json",
            {"minecraft:block/glass_pane_": "bettergold:block/gold_sand_glass_pane_"},
            "gold_sand_glass_pane.json")
clone_state("assets/minecraft/blockstates/oak_stairs.json",
            {"minecraft:block/oak_stairs": "bettergold:block/gold_silk_stairs"},
            "gold_silk_stairs.json")
clone_state("assets/minecraft/blockstates/oak_slab.json",
            {"minecraft:block/oak_slab": "bettergold:block/gold_silk_slab",
             "minecraft:block/oak_planks": "bettergold:block/gold_silk_planks"},
            "gold_silk_slab.json")
clone_state("assets/minecraft/blockstates/oak_fence.json",
            {"minecraft:block/oak_fence": "bettergold:block/gold_silk_fence"},
            "gold_silk_fence.json")
clone_state("assets/minecraft/blockstates/oak_fence_gate.json",
            {"minecraft:block/oak_fence_gate": "bettergold:block/gold_silk_fence_gate"},
            "gold_silk_fence_gate.json")
clone_state("assets/minecraft/blockstates/oak_door.json",
            {"minecraft:block/oak_door": "bettergold:block/gold_silk_door"},
            "gold_silk_door.json")
clone_state("assets/minecraft/blockstates/oak_trapdoor.json",
            {"minecraft:block/oak_trapdoor": "bettergold:block/gold_silk_trapdoor"},
            "gold_silk_trapdoor.json")
clone_state("assets/minecraft/blockstates/oak_button.json",
            {"minecraft:block/oak_button": "bettergold:block/gold_silk_button"},
            "gold_silk_button.json")
clone_state("assets/minecraft/blockstates/oak_pressure_plate.json",
            {"minecraft:block/oak_pressure_plate": "bettergold:block/gold_silk_pressure_plate"},
            "gold_silk_pressure_plate.json")

# ==================== 5. 战利品表 ====================
def self_loot(name, random_sequence=None):
    return {
        "type": "minecraft:block",
        "pools": [{
            "bonus_rolls": 0.0,
            "conditions": [{"condition": "minecraft:survives_explosion"}],
            "entries": [{"type": "minecraft:item", "name": "bettergold:" + name}],
            "rolls": 1.0,
        }],
        "random_sequence": "bettergold:blocks/" + (random_sequence or name),
    }


def simple_drop(name, drop, random_sequence=None):
    out = self_loot(name, random_sequence)
    out["pools"][0]["entries"] = [{"type": "minecraft:item", "name": drop}]
    return out


SILK = {
    "condition": "minecraft:match_tool",
    "predicate": {"predicates": {"minecraft:enchantments": [
        {"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}]}},
}
SHEARS = {"condition": "minecraft:match_tool", "predicate": {"items": "minecraft:shears"}}


def silk_or(name, drop, self_name=None):
    return {
        "type": "minecraft:block",
        "pools": [{
            "bonus_rolls": 0.0,
            "entries": [{
                "type": "minecraft:alternatives",
                "children": [
                    {"type": "minecraft:item", "conditions": [SILK],
                     "name": self_name or ("bettergold:" + name)},
                    {"type": "minecraft:item",
                     "conditions": [{"condition": "minecraft:survives_explosion"}],
                     "name": drop},
                ],
            }],
            "rolls": 1.0,
        }],
        "random_sequence": "bettergold:blocks/" + name,
    }


# 草方块：丝触 → 自己；否则金染土
write_json("data/bettergold/loot_table/blocks/gold_infused_grass_block.json",
            silk_or("gold_infused_grass_block", "bettergold:gold_infused_dirt"))
# 土径 / 耕地 → 金染土（耕地沿用旧表）
write_json("data/bettergold/loot_table/blocks/gold_infused_dirt_path.json",
            simple_drop("gold_infused_dirt_path", "bettergold:gold_infused_dirt"))
# 金砂 → 自己
write_json("data/bettergold/loot_table/blocks/gold_sand.json", self_loot("gold_sand"))
# 玻璃 / 玻璃板：丝触才掉自己
write_json("data/bettergold/loot_table/blocks/gold_sand_glass.json",
            {"type": "minecraft:block", "pools": [{
                "bonus_rolls": 0.0,
                "conditions": [SILK],
                "entries": [{"type": "minecraft:item", "name": "bettergold:gold_sand_glass"}],
                "rolls": 1.0}],
                "random_sequence": "bettergold:blocks/gold_sand_glass"})
write_json("data/bettergold/loot_table/blocks/gold_sand_glass_pane.json",
            {"type": "minecraft:block", "pools": [{
                "bonus_rolls": 0.0,
                "conditions": [SILK],
                "entries": [{"type": "minecraft:item", "name": "bettergold:gold_sand_glass_pane"}],
                "rolls": 1.0}],
                "random_sequence": "bettergold:blocks/gold_sand_glass_pane"})

for name in ("gold_silk_log", "gold_silk_wood", "stripped_gold_silk_log",
             "stripped_gold_silk_wood", "gold_silk_planks", "gold_silk_stairs",
             "gold_silk_slab", "gold_silk_fence", "gold_silk_fence_gate",
             "gold_silk_door", "gold_silk_trapdoor", "gold_silk_button",
             "gold_silk_pressure_plate", "gold_silk_sapling", "gold_marigold",
             "gold_tulip"):
    write_json("data/bettergold/loot_table/blocks/%s.json" % name, self_loot(name))

# 树叶：剪刀/丝触 → 自己；否则 2% 木棍(1-2)、1% 金苹果、0.1% 附魔金苹果，全部受时运（table_bonus）
NOT_SHEARS_OR_SILK = {
    "condition": "minecraft:inverted",
    "term": {"condition": "minecraft:any_of", "terms": [SHEARS, SILK]},
}


def leaves_pool(name, chances, functions=None):
    entry = {"type": "minecraft:item", "name": name,
             "conditions": [{"condition": "minecraft:table_bonus",
                             "enchantment": "minecraft:fortune", "chances": chances}]}
    if functions:
        entry["functions"] = functions
    return {"bonus_rolls": 0.0, "conditions": [NOT_SHEARS_OR_SILK],
            "entries": [entry], "rolls": 1.0}


write_json("data/bettergold/loot_table/blocks/gold_silk_leaves.json", {
    "type": "minecraft:block",
    "pools": [
        {"bonus_rolls": 0.0, "entries": [{
            "type": "minecraft:alternatives",
            "children": [
                {"type": "minecraft:item", "conditions": [{"condition": "minecraft:any_of",
                                                           "terms": [SHEARS, SILK]}],
                 "name": "bettergold:gold_silk_leaves"},
            ]}], "rolls": 1.0},
        leaves_pool("bettergold:gold_silk_stick", [0.02, 0.0222, 0.025, 0.0333], [
            {"function": "minecraft:set_count", "add": False,
             "count": {"type": "minecraft:uniform", "min": 1.0, "max": 2.0}},
            {"function": "minecraft:explosion_decay"}]),
        leaves_pool("minecraft:golden_apple", [0.01, 0.0125, 0.015, 0.02]),
        leaves_pool("minecraft:enchanted_golden_apple", [0.001, 0.00125, 0.0015, 0.002]),
    ],
    "random_sequence": "bettergold:blocks/gold_silk_leaves",
})

# 金草丛：剪刀 → 自己；否则 12% 金麦种子 / 1% 金钱茄种子（时运按原版 uniform_bonus_count 提升数量）
FORTUNE_BONUS = {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune",
                 "formula": "minecraft:uniform_bonus_count",
                 "parameters": {"bonusMultiplier": 2}}
write_json("data/bettergold/loot_table/blocks/gold_short_grass.json", {
    "type": "minecraft:block",
    "pools": [{
        "bonus_rolls": 0.0,
        "entries": [{
            "type": "minecraft:alternatives",
            "children": [
                {"type": "minecraft:item", "conditions": [SHEARS],
                 "name": "bettergold:gold_short_grass"},
                {"type": "minecraft:item", "conditions": [
                    {"condition": "minecraft:random_chance", "chance": 0.12}],
                 "functions": [FORTUNE_BONUS, {"function": "minecraft:explosion_decay"}],
                 "name": "bettergold:golden_wheat_seeds"},
            ],
        }],
        "rolls": 1.0,
    }, {
        "bonus_rolls": 0.0,
        "conditions": [{"condition": "minecraft:inverted", "term": SHEARS}],
        "entries": [{"type": "minecraft:item", "conditions": [
            {"condition": "minecraft:random_chance", "chance": 0.01}],
            "functions": [FORTUNE_BONUS, {"function": "minecraft:explosion_decay"}],
            "name": "bettergold:golden_eggplant_seeds"}],
        "rolls": 1.0,
    }],
    "random_sequence": "bettergold:blocks/gold_short_grass",
})

# 金高草丛：只在下半块结算一次（避免上下两半各掉一次）；剪刀 → 自己
write_json("data/bettergold/loot_table/blocks/gold_tall_grass.json", {
    "type": "minecraft:block",
    "pools": [{
        "bonus_rolls": 0.0,
        "conditions": [
            {"block": "bettergold:gold_tall_grass",
             "condition": "minecraft:block_state_property",
             "properties": {"half": "lower"}},
            {"condition": "minecraft:location_check", "offsetY": 1,
             "predicate": {"block": {"blocks": "bettergold:gold_tall_grass",
                                     "state": {"half": "upper"}}}},
        ],
        "entries": [{
            "type": "minecraft:alternatives",
            "children": [
                {"type": "minecraft:item", "conditions": [SHEARS],
                 "name": "bettergold:gold_tall_grass"},
                {"type": "minecraft:item", "conditions": [
                    {"condition": "minecraft:random_chance", "chance": 0.12}],
                 "functions": [FORTUNE_BONUS, {"function": "minecraft:explosion_decay"}],
                 "name": "bettergold:golden_wheat_seeds"},
            ],
        }],
        "rolls": 1.0,
    }, {
        "bonus_rolls": 0.0,
        "conditions": [
            {"block": "bettergold:gold_tall_grass",
             "condition": "minecraft:block_state_property",
             "properties": {"half": "lower"}},
            {"condition": "minecraft:location_check", "offsetY": 1,
             "predicate": {"block": {"blocks": "bettergold:gold_tall_grass",
                                     "state": {"half": "upper"}}}},
            {"condition": "minecraft:inverted", "term": SHEARS},
        ],
        "entries": [{"type": "minecraft:item", "conditions": [
            {"condition": "minecraft:random_chance", "chance": 0.01}],
            "functions": [FORTUNE_BONUS, {"function": "minecraft:explosion_decay"}],
            "name": "bettergold:golden_eggplant_seeds"}],
        "rolls": 1.0,
    }],
    "random_sequence": "bettergold:blocks/gold_tall_grass",
})

# ==================== 6. 配方 ====================
def _ingredient(value):
    """1.21.1 的 Ingredient：`{"item": ...}` / `{"tag": ...}`；也允许数组（多选一）。"""
    if isinstance(value, list):
        return [_ingredient(v) for v in value]
    if value.startswith("#"):
        return {"tag": value[1:]}
    return {"item": value}


def shaped(pattern, key, result, count=1):
    return {"type": "minecraft:crafting_shaped", "pattern": pattern,
            "key": {k: _ingredient(v) for k, v in key.items()},
            "result": {"id": result, "count": count}}


def shapeless(ingredients, result, count=1):
    return {"type": "minecraft:crafting_shapeless",
            "ingredients": [_ingredient(v) for v in ingredients],
            "result": {"id": result, "count": count}}


RECIPES = {
    "gold_infused_grass_block": shaped([" G ", "GDG", " G "],
                                       {"G": "minecraft:gold_ingot",
                                        "D": "minecraft:grass_block"},
                                       "bettergold:gold_infused_grass_block"),
    "gold_sand": shaped([" G ", "GSG", " G "],
                        {"G": "minecraft:gold_ingot", "S": "minecraft:sand"},
                        "bettergold:gold_sand"),
    "gold_silk_sapling": shaped(["GGG", "GSG", "GGG"],
                                {"G": "minecraft:gold_ingot",
                                 "S": "#minecraft:saplings"},
                                "bettergold:gold_silk_sapling"),
    "gold_tulip": shaped([" N ", "NTN", " N "],
                         {"N": "minecraft:gold_nugget",
                          "T": ["minecraft:red_tulip", "minecraft:orange_tulip",
                                "minecraft:white_tulip", "minecraft:pink_tulip"]},
                         "bettergold:gold_tulip"),
    "gold_silk_planks_from_log": shapeless(["bettergold:gold_silk_log"],
                                           "bettergold:gold_silk_planks", 4),
    "gold_silk_planks_from_stripped_log": shapeless(["bettergold:stripped_gold_silk_log"],
                                                    "bettergold:gold_silk_planks", 4),
    "gold_silk_wood": shaped(["LL", "LL"], {"L": "bettergold:gold_silk_log"},
                             "bettergold:gold_silk_wood", 3),
    "stripped_gold_silk_wood": shaped(
        ["LL", "LL"], {"L": "bettergold:stripped_gold_silk_log"},
        "bettergold:stripped_gold_silk_wood", 3),
    "gold_silk_stick": shaped(["P", "P"], {"P": "bettergold:gold_silk_planks"},
                              "bettergold:gold_silk_stick", 4),
    "gold_silk_stairs": shaped(["P  ", "PP ", "PPP"],
                               {"P": "bettergold:gold_silk_planks"},
                               "bettergold:gold_silk_stairs", 4),
    "gold_silk_slab": shaped(["PPP"], {"P": "bettergold:gold_silk_planks"},
                             "bettergold:gold_silk_slab", 6),
    "gold_silk_fence": shaped(["PSP", "PSP"],
                              {"P": "bettergold:gold_silk_planks",
                               "S": "bettergold:gold_silk_stick"},
                              "bettergold:gold_silk_fence", 3),
    "gold_silk_fence_gate": shaped(["SPS", "SPS"],
                                   {"P": "bettergold:gold_silk_planks",
                                    "S": "bettergold:gold_silk_stick"},
                                   "bettergold:gold_silk_fence_gate"),
    "gold_silk_door": shaped(["PP", "PP", "PP"],
                             {"P": "bettergold:gold_silk_planks"},
                             "bettergold:gold_silk_door", 3),
    "gold_silk_trapdoor": shaped(["PPP", "PPP"],
                                 {"P": "bettergold:gold_silk_planks"},
                                 "bettergold:gold_silk_trapdoor", 2),
    "gold_silk_button": shapeless(["bettergold:gold_silk_planks"],
                                  "bettergold:gold_silk_button"),
    "gold_silk_pressure_plate": shaped(["PP"],
                                       {"P": "bettergold:gold_silk_planks"},
                                       "bettergold:gold_silk_pressure_plate"),
    "gold_sand_glass_pane": shaped(["GGG", "GGG"],
                                   {"G": "bettergold:gold_sand_glass"},
                                   "bettergold:gold_sand_glass_pane", 16),
    "el_dorado_dust": shaped(["BBB", "BNB", "BBB"],
                             {"B": "bettergold:golden_bone_meal",
                              "N": "bettergold:sturdygold_nugget"},
                             "bettergold:el_dorado_dust", 8),
    "yellow_dye_from_gold_marigold": shapeless(["bettergold:gold_marigold"],
                                               "minecraft:yellow_dye"),
    "yellow_dye_from_gold_tulip": shapeless(["bettergold:gold_tulip"],
                                            "minecraft:yellow_dye"),
}
for name, recipe in RECIPES.items():
    write_json("data/bettergold/recipe/%s.json" % name, recipe)

# 金沙 → 金沙玻璃（熔炉）
write_json("data/bettergold/recipe/gold_sand_glass_smelting.json", {
    "type": "minecraft:smelting",
    "category": "blocks",
    "ingredient": {"item": "bettergold:gold_sand"},
    "result": {"id": "bettergold:gold_sand_glass", "count": 1},
    "experience": 0.1,
    "cookingtime": 200,
})

# ==================== 7. 标签 ====================
WOOD = ["gold_silk_log", "gold_silk_wood", "stripped_gold_silk_log",
        "stripped_gold_silk_wood"]
WOOD_BUILDING = ["gold_silk_planks", "gold_silk_stairs", "gold_silk_slab",
                 "gold_silk_fence", "gold_silk_fence_gate", "gold_silk_door",
                 "gold_silk_trapdoor", "gold_silk_button", "gold_silk_pressure_plate"]
ALL_WOOD = WOOD + WOOD_BUILDING

merge_tag("data/minecraft/tags/block/mineable/axe.json",
          ["bettergold:" + n for n in ALL_WOOD])
merge_tag("data/minecraft/tags/block/mineable/shovel.json",
          ["bettergold:gold_infused_grass_block", "bettergold:gold_infused_dirt_path",
           "bettergold:gold_sand"])
merge_tag("data/minecraft/tags/block/needs_wooden_tool.json",
          ["bettergold:" + n for n in
           ["gold_infused_grass_block", "gold_infused_dirt_path", "gold_sand"] + ALL_WOOD])
merge_tag("data/minecraft/tags/block/planks.json", ["bettergold:gold_silk_planks"])
merge_tag("data/minecraft/tags/item/planks.json", ["bettergold:gold_silk_planks"])
merge_tag("data/minecraft/tags/block/logs.json", ["bettergold:" + n for n in WOOD])
merge_tag("data/minecraft/tags/item/logs.json", ["bettergold:" + n for n in WOOD])
merge_tag("data/minecraft/tags/block/logs_that_burn.json", ["bettergold:" + n for n in WOOD])
merge_tag("data/minecraft/tags/item/logs_that_burn.json", ["bettergold:" + n for n in WOOD])
for tag, members in [
        ("wooden_stairs", ["gold_silk_stairs"]),
        ("wooden_slabs", ["gold_silk_slab"]),
        ("wooden_fences", ["gold_silk_fence"]),
        ("fence_gates", ["gold_silk_fence_gate"]),
        ("wooden_doors", ["gold_silk_door"]),
        ("wooden_trapdoors", ["gold_silk_trapdoor"]),
        ("wooden_buttons", ["gold_silk_button"]),
        ("wooden_pressure_plates", ["gold_silk_pressure_plate"])]:
    merge_tag("data/minecraft/tags/block/%s.json" % tag, ["bettergold:" + n for n in members])
    merge_tag("data/minecraft/tags/item/%s.json" % tag, ["bettergold:" + n for n in members])
merge_tag("data/minecraft/tags/block/small_flowers.json",
          ["bettergold:gold_marigold", "bettergold:gold_tulip"])
merge_tag("data/minecraft/tags/item/small_flowers.json",
          ["bettergold:gold_marigold", "bettergold:gold_tulip"])
merge_tag("data/minecraft/tags/block/flowers.json",
          ["bettergold:gold_marigold", "bettergold:gold_tulip"])
merge_tag("data/minecraft/tags/item/flowers.json",
          ["bettergold:gold_marigold", "bettergold:gold_tulip"])
merge_tag("data/minecraft/tags/block/saplings.json", ["bettergold:gold_silk_sapling"])
merge_tag("data/minecraft/tags/item/saplings.json", ["bettergold:gold_silk_sapling"])
merge_tag("data/c/tags/item/rods/wooden.json", ["bettergold:gold_silk_stick"])

# 负向：金丝树叶不进 #minecraft:leaves（否则全局战利品修饰器会加闪耀藤条）
# 只做检查、不写文件。
_leaves = read_json("data/minecraft/tags/block/leaves.json")
if _leaves and any("gold_silk_leaves" in str(v) for v in _leaves.get("values", [])):
    print("[bg25-gen] 失败：gold_silk_leaves 被写进了 #minecraft:leaves")
    sys.exit(2)

# ==================== 8. 语言键 ====================
LANG = {
    "block.bettergold.gold_infused_grass_block": ("金染草方块", "Gold-Infused Grass Block"),
    "block.bettergold.gold_infused_dirt_path": ("金染土径", "Gold-Infused Dirt Path"),
    "block.bettergold.gold_sand": ("金沙", "Gold Sand"),
    "block.bettergold.gold_sand_glass": ("金沙玻璃", "Gold Sand Glass"),
    "block.bettergold.gold_sand_glass_pane": ("金沙玻璃板", "Gold Sand Glass Pane"),
    "block.bettergold.gold_silk_log": ("金丝原木", "Gold Silk Log"),
    "block.bettergold.gold_silk_wood": ("金丝木", "Gold Silk Wood"),
    "block.bettergold.stripped_gold_silk_log": ("去皮金丝原木", "Stripped Gold Silk Log"),
    "block.bettergold.stripped_gold_silk_wood": ("去皮金丝木", "Stripped Gold Silk Wood"),
    "block.bettergold.gold_silk_planks": ("金丝木板", "Gold Silk Planks"),
    "block.bettergold.gold_silk_stairs": ("金丝木楼梯", "Gold Silk Stairs"),
    "block.bettergold.gold_silk_slab": ("金丝木台阶", "Gold Silk Slab"),
    "block.bettergold.gold_silk_fence": ("金丝木栅栏", "Gold Silk Fence"),
    "block.bettergold.gold_silk_fence_gate": ("金丝木栅栏门", "Gold Silk Fence Gate"),
    "block.bettergold.gold_silk_door": ("金丝木门", "Gold Silk Door"),
    "block.bettergold.gold_silk_trapdoor": ("金丝木活板门", "Gold Silk Trapdoor"),
    "block.bettergold.gold_silk_button": ("金丝木按钮", "Gold Silk Button"),
    "block.bettergold.gold_silk_pressure_plate": ("金丝木压力板", "Gold Silk Pressure Plate"),
    "block.bettergold.gold_silk_leaves": ("金丝树叶", "Gold Silk Leaves"),
    "block.bettergold.gold_silk_sapling": ("金丝树苗", "Gold Silk Sapling"),
    "block.bettergold.gold_short_grass": ("金草丛", "Gold Short Grass"),
    "block.bettergold.gold_tall_grass": ("金高草丛", "Gold Tall Grass"),
    "block.bettergold.gold_marigold": ("金盏花", "Gold Marigold"),
    "block.bettergold.gold_tulip": ("金郁金香", "Gold Tulip"),
    "item.bettergold.gold_silk_stick": ("金丝木棍", "Gold Silk Stick"),
    "item.bettergold.el_dorado_dust": ("黄金国浮现之尘", "El Dorado Dust"),
}
for lang, index in (("zh_cn", 0), ("en_us", 1)):
    p = ASSETS / "lang" / ("%s.json" % lang)
    if not p.is_file():
        print("[bg25-gen] 语言文件缺失：", p)
        sys.exit(2)
    data = json.loads(p.read_text(encoding="utf-8"))
    for key, values in LANG.items():
        data[key] = values[index]
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ==================== 9. 粒子定义 ====================
write_json("assets/bettergold/particles/gold_silk_leaves.json",
            {"textures": ["bettergold:gold_silk_leaves_%d" % i for i in range(12)]})
write_json("assets/bettergold/particles/golden_growth.json",
            {"textures": ["bettergold:golden_growth"]})

# ==================== 10. 认亲表 / 哈希 / 黑边报告 ====================
KINSHIP.mkdir(parents=True, exist_ok=True)
lines = ["source\ttarget\tbytes\tsha256\ttransform"]
for row in TEXTURE_ROWS:
    lines.append("%s\t%s\t%d\t%s\t%s" % row)
(KINSHIP / "认亲表.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

md = ["# 1.8 阶段 1 素材认亲表（bg25）", "",
      "> 源 = `docs/1.8-新约10-素材清单/`（原始 zip 的只读归档副本）。",
      "> 目标 = `src/main/resources/assets/bettergold/textures/`。",
      "> `1:1` = 字节原样复制；`black-border-strip(N px)` = 作者 2026-11-18 确认的",
      "> 「花草不要大黑格」授权处理（只去掉与图片外边框连通的纯黑像素）。", "",
      "| 源 | 目标 | 字节 | SHA256 | 处理 |", "|---|---|---:|---|---|"]
for src, dst, size, sha, transform in TEXTURE_ROWS:
    md.append("| `%s` | `%s` | %d | `%s` | %s |" % (src, dst, size, sha, transform))
md += ["", "合计 **%d** 张；`1:1` **%d** 张；授权去黑边 **%d** 张。" % (
    len(TEXTURE_ROWS),
    sum(1 for r in TEXTURE_ROWS if r[4] == "1:1"),
    sum(1 for r in TEXTURE_ROWS if r[4] != "1:1"))]
(KINSHIP / "认亲表.md").write_text("\n".join(md) + "\n", encoding="utf-8")

black_rows = []
for p in sorted(BLACK.glob("*.before.png")):
    after = p.with_name(p.name.replace(".before.png", ".after.png"))
    before_bytes = p.read_bytes()
    after_bytes = after.read_bytes()
    black_rows.append("%s\t%s\t%s\t%s" % (
        p.name.replace(".before.png", ""), sha256(before_bytes), sha256(after_bytes),
        "changed" if before_bytes != after_bytes else "unchanged"))
(BLACK / "报告.txt").write_text(
    "花草黑边处理（作者 2026-11-18 确认）\n"
    "判据：只处理与图片外边框 4 连通的、alpha>0 且 RGB 恰为 (0,0,0) 的像素；\n"
    "      主体内部黑色（阴影/描边）一个像素不动。\n"
    "文件\t改前 SHA256\t改后 SHA256\t结果\n" + "\n".join(black_rows) + "\n",
    encoding="utf-8")

print("[bg25-gen] 贴图 %d 张（1:1 %d / 去黑边 %d）" % (
    len(TEXTURE_ROWS), sum(1 for r in TEXTURE_ROWS if r[4] == "1:1"),
    sum(1 for r in TEXTURE_ROWS if r[4] != "1:1")))
print("[bg25-gen] 认亲表 -> docs/1.8-素材认亲/认亲表.tsv")
print("[bg25-gen] 完成")
