# -*- coding: utf-8 -*-
"""金之牢狱「生成预览」渲染器 —— 数据可视化，不画美术。

输入：docs/金之牢狱-生成预览/_raw/{meta.json, blocks.tsv, section_x.tsv, section_z.tsv}
     （由 GpPreviewProbe 在 runServer 里从真实生成的结构 dump 出来）
输出：docs/金之牢狱-生成预览/*.png + 终端 ASCII 缩略图

只依赖 Pillow（本机自带），不装任何库。
"""
import argparse
import colorsys
import json
import math
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
AIR = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:structure_void"}
DIRV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
TEMPLATE_CN = {
    "treasure": "宝藏房", "lane": "过道", "exit": "出入口",
    "cross_a": "四面道A", "cross_b": "四面道B",
}


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def load(inp):
    meta = json.loads((inp / "meta.json").read_text(encoding="utf-8"))
    pieces = meta["pieces"]
    blocks = []
    for line in (inp / "blocks.tsv").read_text(encoding="utf-8").splitlines():
        x, y, z, bid = line.split(",", 3)
        if bid in AIR:
            continue
        blocks.append((int(x), int(y), int(z), bid))
    secs = {}
    for name in ("section_x", "section_z"):
        arr = []
        for line in (inp / f"{name}.tsv").read_text(encoding="utf-8").splitlines():
            x, y, z, bid = line.split(",", 3)
            if bid in AIR:
                continue
            arr.append((int(x), int(y), int(z), bid))
        secs[name] = arr
    return meta, pieces, blocks, secs


def piece_boxes(pieces):
    return [p["bbox"] for p in pieces]


def piece_at(boxes, x, y, z):
    for i, b in enumerate(boxes):
        if b[0] <= x <= b[3] and b[1] <= y <= b[4] and b[2] <= z <= b[5]:
            return i
    return -1


def palette(pieces):
    base = {"treasure": (201, 158, 42), "lane": (112, 120, 132)}
    pal = {}
    for i, p in enumerate(pieces):
        t = p["template"]
        if t == "treasure":
            pal[i] = base["treasure"]
        elif t == "exit":
            pal[i] = shade((205, 70, 70), 0.9 + 0.06 * (i % 3))
        elif t == "lane":
            pal[i] = shade(base["lane"], 0.9 + 0.07 * (i % 4))
        elif t.startswith("cross_"):
            pal[i] = shade((62, 108, 188), 0.92 + 0.05 * (i % 2))
        else:
            pal[i] = hsv(i * 0.61803398875, 0.58, 0.82)
    return pal


def mat_color(bid):
    b = bid.split(":", 1)[-1]
    if b in ("air", "cave_air", "void_air", "structure_void"):
        return (255, 255, 255)
    if "gold_bricks" in b or "gold_pillar" in b or "gold_block" in b or "gold_bars" in b \
            or "gold_chain" in b or "gold_trapdoor" in b or "golden_rose" in b:
        return (231, 188, 61)
    if "gilded_blackstone" in b:
        return (116, 86, 48)
    if "blackstone" in b:
        return (54, 49, 55)
    if "netherrack" in b:
        return (88, 58, 58)
    if "basalt" in b:
        return (84, 84, 92)
    if "soul_" in b:
        return (100, 76, 58)
    if "magma" in b:
        return (166, 74, 30)
    if "lava" in b:
        return (236, 122, 28)
    if "chest" in b:
        return (203, 128, 44)
    if "spawner" in b:
        return (72, 46, 86)
    if "toad" in b:
        return (196, 150, 26)
    if "farmland" in b or "infused_dirt" in b:
        return (120, 80, 46)
    if "crop" in b or "wheat" in b:
        return (104, 168, 68)
    if "water" in b:
        return (62, 112, 200)
    if "quartz" in b:
        return (222, 217, 206)
    if "glass" in b:
        return (226, 196, 92)
    if "raw_gold" in b:
        return (188, 142, 48)
    if "ancient_debris" in b:
        return (92, 62, 52)
    if "bone" in b:
        return (216, 210, 188)
    return (128, 118, 108)


def header(d, left, title, sub, note):
    d.text((left, 10), title, font=font(26, True), fill=(20, 20, 24))
    d.text((left, 48), sub, font=font(14), fill=(70, 70, 78))
    if note:
        d.text((left, 76), note, font=font(11), fill=(95, 95, 102))


def draw_ticks(d, ox, oy, minx, minz, mapw, maph, scale):
    step = 8
    maxx = minx + mapw // scale - 1
    maxz = minz + maph // scale - 1
    for x in range(minx - (minx % step), maxx + 1, step):
        if x < minx or x > maxx:
            continue
        px = ox + (x - minx) * scale
        d.line([(px, oy), (px, oy - 6)], fill=(90, 90, 96), width=1)
        d.text((px, oy - 9), str(x), font=font(10), fill=(70, 70, 76), anchor="mb")
    for z in range(minz - (minz % step), maxz + 1, step):
        if z < minz or z > maxz:
            continue
        py = oy + (z - minz) * scale
        d.line([(ox, py), (ox - 6, py)], fill=(90, 90, 96), width=1)
        d.text((ox - 9, py), str(z), font=font(10), fill=(70, 70, 76), anchor="rm")
    d.rectangle([ox, oy, ox + mapw - 1, oy + maph - 1], outline=(120, 120, 126), width=1)


def draw_compass(d, cx, cy, r=24):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255), outline=(90, 90, 96), width=1)
    d.line([(cx, cy - r + 5), (cx, cy + r - 5)], fill=(120, 120, 126), width=1)
    d.line([(cx - r + 5, cy), (cx + r - 5, cy)], fill=(120, 120, 126), width=1)
    d.polygon([(cx, cy - r + 3), (cx - 5, cy - r + 12), (cx + 5, cy - r + 12)], fill=(190, 50, 50))
    d.text((cx, cy - r - 11), "N", font=font(13, True), fill=(20, 20, 24), anchor="mm")
    d.text((cx, cy + r + 11), "S", font=font(12), fill=(70, 70, 76), anchor="mm")
    d.text((cx + r + 11, cy), "E", font=font(12), fill=(70, 70, 76), anchor="mm")
    d.text((cx - r - 11, cy), "W", font=font(12), fill=(70, 70, 76), anchor="mm")


def draw_legend(d, x, y, entries, title):
    d.text((x, y), title, font=font(15, True), fill=(20, 20, 24))
    y += 24
    for color, text in entries:
        d.rectangle([x, y + 3, x + 12, y + 15], fill=color, outline=(70, 70, 76), width=1)
        d.text((x + 19, y), text, font=font(12), fill=(35, 35, 40))
        y += 20
    return y


def short_name(tpl):
    return TEMPLATE_CN.get(tpl, tpl)


def display_name(tpl):
    cn = TEMPLATE_CN.get(tpl)
    return f"{cn} [{tpl}]" if cn else tpl


def label_num(d, x, y, idx, tpl, size=12):
    txt = f"#{idx}"
    if tpl == "treasure":
        txt = "#0 ★"
    f = font(size, True)
    d.text((x, y), txt, font=f, fill=(10, 10, 12), stroke_width=2, stroke_fill=(255, 255, 255))


def build_columns(blocks, boxes):
    top_struct = {}
    layers = defaultdict(dict)
    for x, y, z, bid in blocks:
        pi = piece_at(boxes, x, y, z)
        layers[y][(x, z)] = (bid, pi)
        k = (x, z)
        if pi >= 0 and (k not in top_struct or y > top_struct[k][0]):
            top_struct[k] = (y, bid, pi)
    return top_struct, layers


def fig_overview(meta, pieces, blocks, pal, out, scale=5):
    bb = meta["pieceUnionBBox"]
    minx, maxx = bb[0] - 8, bb[3] + 8
    minz, maxz = bb[2] - 8, bb[5] + 8
    mapw, maph = (maxx - minx + 1) * scale, (maxz - minz + 1) * scale
    left, top, right, bottom = 74, 112, 366, 74
    W, H = left + mapw + right, top + maph + bottom
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    stats = meta["stats"]
    sub = (f"种子 {meta['seed']} · 世界 {meta['worldName']} · 起点 {meta['locate']['result']} · "
           f"{stats['pieces']} 件 / {stats['templates']} 种模板 · 包围盒 "
           f"{bb[3]-bb[0]+1}×{bb[4]-bb[1]+1}×{bb[5]-bb[2]+1}")
    header(d, left, "金之牢狱 · 整体俯视图（按件着色 / 俯视投影）", sub,
           "每格 1 方块 · 黑框 = 该件包围盒 · 颜色按件区分 · 取每列最高的结构件方块"
           f"（结构整体埋在 y={bb[1]}..{bb[4]}，埋深见剖面图）")

    ox, oy = left, top
    d.rectangle([ox, oy, ox + mapw - 1, oy + maph - 1], fill=(246, 245, 241))
    for x in range(minx - minx % 8, maxx + 1, 8):
        px = ox + (x - minx) * scale
        d.line([(px, oy), (px, oy + maph)], fill=(235, 234, 230), width=1)
    for z in range(minz - minz % 8, maxz + 1, 8):
        py = oy + (z - minz) * scale
        d.line([(ox, py), (ox + mapw, py)], fill=(235, 234, 230), width=1)

    top_struct, _ = build_columns(blocks, piece_boxes(pieces))
    ys = [v[0] for v in top_struct.values()]
    ymin, ymax = min(ys), max(ys)
    for (x, z), (y, bid, pi) in top_struct.items():
        f = 0.84 + 0.16 * ((y - ymin) / max(1, ymax - ymin))
        px = ox + (x - minx) * scale
        pz = oy + (z - minz) * scale
        d.rectangle([px, pz, px + scale - 1, pz + scale - 1], fill=shade(pal[pi], f))

    for p in pieces:
        b = p["bbox"]
        x0 = ox + (b[0] - minx) * scale
        z0 = oy + (b[2] - minz) * scale
        x1 = ox + (b[3] - minx + 1) * scale - 1
        z1 = oy + (b[5] - minz + 1) * scale - 1
        d.rectangle([x0, z0, x1, z1], outline=(0, 0, 0), width=2)
        if p["template"] == "exit":
            d.rectangle([x0 - 2, z0 - 2, x1 + 2, z1 + 2], outline=(205, 40, 40), width=2)
        if p["template"] == "treasure":
            d.rectangle([x0 - 2, z0 - 2, x1 + 2, z1 + 2], outline=(150, 105, 10), width=2)
        label_num(d, x0 + 3, z0 + 2, p["index"], p["template"],
                  size=10 if p["template"] in ("lane", "exit") else 13)

    draw_ticks(d, ox, oy, minx, minz, mapw, maph, scale)
    draw_compass(d, ox + mapw - 42, oy + 44)

    entries = []
    for p in pieces:
        i = p["index"]
        extra = []
        if p.get("chests"):
            extra.append(f"箱{p['chests']}")
        if p.get("spawners"):
            extra.append(f"笼{p['spawners']}")
        if p.get("toads"):
            extra.append(f"蟾{p['toads']}")
        marker = " ★" if p["template"] == "treasure" else ""
        entries.append((pal[i], f"#{i:02d} {display_name(p['template'])}{marker}" +
                        (f"  {'/'.join(extra)}" if extra else "")))
    ly = draw_legend(d, left + mapw + 18, top, entries, "件号 / 模板 / 箱·笼·蟾")
    d.text((left + mapw + 18, ly + 6),
           "★ = 宝藏房（start_pool 唯一）\n红框 = 出入口（末端 fallback）\n每格 5 px，每 8 格一条刻度",
           font=font(12), fill=(60, 60, 66), spacing=5)
    d.text((left, H - 38), "N/S/E/W 为世界方向（上 = 北 = −z）。本图只显示结构件方块；"
                           "结构外的地形与埋深见剖面图。", font=font(12), fill=(90, 90, 98))
    img.save(out, "PNG")
    print("[png]", out.name, img.size)


def fig_layer(meta, pieces, blocks, pal, out, y, tag, scale=5):
    bb = meta["dumpBBox"]
    minx, maxx, minz, maxz = bb[0], bb[3], bb[2], bb[5]
    mapw, maph = (maxx - minx + 1) * scale, (maxz - minz + 1) * scale
    left, top, right, bottom = 74, 112, 320, 74
    W, H = left + mapw + right, top + maph + bottom
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    sub = (f"种子 {meta['seed']} · 世界 {meta['worldName']} · y={y} · "
           f"黄色 = 金砖/金柱/金栅栏 · 白色 = 空气（可走）")
    header(d, left, f"金之牢狱 · 分层俯视 y={y} —— {tag}", sub,
           "深色 = 结构外的下界岩/灵魂沙（地形） · 橙 = 箱子 · 紫 = 刷怪笼 · 黑框 = 件包围盒")

    ox, oy = left, top
    d.rectangle([ox, oy, ox + mapw - 1, oy + maph - 1], fill=(255, 255, 255))
    _, layers = build_columns(blocks, piece_boxes(pieces))
    for (x, z), (bid, pi) in layers.get(y, {}).items():
        px = ox + (x - minx) * scale
        pz = oy + (z - minz) * scale
        c = mat_color(bid) if pi >= 0 else shade(mat_color(bid), 0.72)
        d.rectangle([px, pz, px + scale - 1, pz + scale - 1], fill=c)

    for p in pieces:
        b = p["bbox"]
        if not (b[1] <= y <= b[4]):
            continue
        x0 = ox + (b[0] - minx) * scale
        z0 = oy + (b[2] - minz) * scale
        x1 = ox + (b[3] - minx + 1) * scale - 1
        z1 = oy + (b[5] - minz + 1) * scale - 1
        d.rectangle([x0, z0, x1, z1], outline=(20, 20, 24), width=1)
        label_num(d, x0 + 2, z0 + 1, p["index"], p["template"], size=9)

    draw_ticks(d, ox, oy, minx, minz, mapw, maph, scale)
    draw_compass(d, ox + mapw - 42, oy + 44)
    entries = [(mat_color("minecraft:gold_block"), "金砖 / 金柱 / 金栅栏"),
               (mat_color("minecraft:netherrack"), "结构外的下界岩（地形）"),
               (mat_color("minecraft:soul_sand"), "灵魂沙 / 灵魂土"),
               (mat_color("minecraft:chest"), "箱子"),
               (mat_color("minecraft:spawner"), "刷怪笼"),
               (mat_color("bettergold:golden_toad_figurine"), "金蟾摆件"),
               (mat_color("bettergold:gold_infused_farmland"), "金农田"),
               ((255, 255, 255), "空气（可走）")]
    draw_legend(d, left + mapw + 18, top, entries, "方块图例")
    d.text((left, H - 36), "门洞 = 空气（白）穿过金墙的缺口；四面道 4 口在本层都能看到开口。",
           font=font(12), fill=(90, 90, 98))
    img.save(out, "PNG")
    print("[png]", out.name, img.size)


def fig_connect(meta, pieces, pal, out, scale=6):
    bb = meta["pieceUnionBBox"]
    minx, maxx = bb[0] - 8, bb[3] + 8
    minz, maxz = bb[2] - 8, bb[5] + 8
    mapw, maph = (maxx - minx + 1) * scale, (maxz - minz + 1) * scale
    left, top, right, bottom = 74, 112, 356, 78
    W, H = left + mapw + right, top + maph + bottom
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    sub = (f"种子 {meta['seed']} · {meta['stats']['pieces']} 件 · "
           f"{meta['portStats']['paired']}/{meta['portStats']['total']} 口成对 · "
           f"BFS 深度 0..{max(p['depth'] for p in pieces)}")
    header(d, left, "金之牢狱 · 连通示意图（包围盒 + 父口→子口）", sub,
           "箭头从父件口穿过门洞指向子件口 · ○ = jigsaw 口 · ★ = 宝藏房 · 红框 = 出入口")

    ox, oy = left, top
    d.rectangle([ox, oy, ox + mapw - 1, oy + maph - 1], fill=(250, 249, 246))
    for x in range(minx - minx % 8, maxx + 1, 8):
        px = ox + (x - minx) * scale
        d.line([(px, oy), (px, oy + maph)], fill=(238, 237, 233), width=1)
    for z in range(minz - minz % 8, maxz + 1, 8):
        py = oy + (z - minz) * scale
        d.line([(ox, py), (ox + mapw, py)], fill=(238, 237, 233), width=1)

    for p in pieces:
        b = p["bbox"]
        x0 = ox + (b[0] - minx) * scale
        z0 = oy + (b[2] - minz) * scale
        x1 = ox + (b[3] - minx + 1) * scale - 1
        z1 = oy + (b[5] - minz + 1) * scale - 1
        d.rectangle([x0, z0, x1, z1], fill=shade(pal[p["index"]], 1.14), outline=(30, 30, 34), width=2)
        if p["template"] == "exit":
            d.rectangle([x0 - 3, z0 - 3, x1 + 3, z1 + 3], outline=(205, 40, 40), width=3)
        if p["template"] == "treasure":
            d.rectangle([x0 - 3, z0 - 3, x1 + 3, z1 + 3], outline=(150, 105, 10), width=3)

    for c in meta["connections"]:
        pp, cp = c["parentPort"], c["childPort"]
        dx, dz = DIRV[c["parentDir"]]
        sx, sz = pp[0] - dx * 4 + 0.5, pp[2] - dz * 4 + 0.5
        ex, ez = cp[0] + dx * 4 + 0.5, cp[2] + dz * 4 + 0.5
        x0, z0 = ox + (sx - minx) * scale, oy + (sz - minz) * scale
        x1, z1 = ox + (ex - minx) * scale, oy + (ez - minz) * scale
        d.line([(x0, z0), (x1, z1)], fill=(30, 30, 34), width=2)
        ang = math.atan2(z1 - z0, x1 - x0)
        L = 9
        d.polygon([(x1, z1),
                   (x1 - L * math.cos(ang - 0.42), z1 - L * math.sin(ang - 0.42)),
                   (x1 - L * math.cos(ang + 0.42), z1 - L * math.sin(ang + 0.42))], fill=(30, 30, 34))
        jx = ox + (pp[0] + dx * 0.5 - minx) * scale
        jz = oy + (pp[2] + dz * 0.5 - minz) * scale
        d.ellipse([jx - 2, jz - 2, jx + 2, jz + 2], fill=(240, 240, 240), outline=(30, 30, 34))

    for p in pieces:
        for port in p.get("ports", []):
            pos = port["pos"]
            d.ellipse([ox + (pos[0] - minx) * scale - 1, oy + (pos[2] - minz) * scale - 1,
                       ox + (pos[0] - minx) * scale + 2, oy + (pos[2] - minz) * scale + 2],
                      outline=(20, 20, 24))

    for p in pieces:
        b = p["bbox"]
        x0 = ox + (b[0] - minx) * scale
        z0 = oy + (b[2] - minz) * scale
        label_num(d, x0 + 3, z0 + 2, p["index"], p["template"],
                  size=10 if p["template"] in ("lane", "exit") else 13)

    draw_ticks(d, ox, oy, minx, minz, mapw, maph, scale)
    draw_compass(d, ox + mapw - 42, oy + 44)

    entries = [(pal[p["index"]], f"#{p['index']:02d} {display_name(p['template'])} "
                                 f"d{p['depth']} ← 父#{p['parent']}") for p in pieces]
    ly = draw_legend(d, left + mapw + 18, top, entries, "件 / 模板 / 深度 / 父件")
    d.text((left + mapw + 18, ly + 6),
           "箭头 = 父件口 → 子件口（穿门）\n○ = jigsaw 口（本座 34/34 成对）\n"
           f"箭头 17 条 = 18 件 − 1（树）",
           font=font(12), fill=(60, 60, 66), spacing=5)
    d.text((left, H - 38), "平面坐标 = 世界 (x,z)；上方 = 北。所有包围盒按 (x,z) 投影，互不重叠。",
           font=font(12), fill=(90, 90, 98))
    img.save(out, "PNG")
    print("[png]", out.name, img.size)


def fig_section(meta, pieces, pal, sec, axis, out, scale=5):
    boxes = piece_boxes(pieces)
    if axis == "x":
        fixed = meta["sectionX"]
        arr = [b for b in sec if b[0] == fixed]
        hmin, hmax = meta["dumpBBox"][2] - 2, meta["dumpBBox"][5] + 2
        hname = "z"
        plane = [p for p in pieces if p["bbox"][0] <= fixed <= p["bbox"][3]]
    else:
        fixed = meta["sectionZ"]
        arr = [b for b in sec if b[2] == fixed]
        hmin, hmax = meta["dumpBBox"][0] - 2, meta["dumpBBox"][3] + 2
        hname = "x"
        plane = [p for p in pieces if p["bbox"][2] <= fixed <= p["bbox"][5]]
    sy0 = min(p["bbox"][1] for p in pieces)
    sy1 = max(p["bbox"][4] for p in pieces)
    walk = max(p["bbox"][1] for p in pieces) + 1
    surface = {}
    cap = sy1 + 36  # 只统计「屋顶上方 36 格内」的覆盖层，别把下界顶层基岩（y≈127）当地表
    for x, y, z, bid in arr:
        h = z if axis == "x" else x
        if y <= cap:
            surface[h] = max(surface.get(h, -1), y)
    ph0 = min((p["bbox"][2] if axis == "x" else p["bbox"][0]) for p in plane)
    ph1 = max((p["bbox"][5] if axis == "x" else p["bbox"][3]) for p in plane)
    local = [surface[h] for h in range(ph0, ph1 + 1) if h in surface]
    surf_max = max(local) if local else sy1 + 8
    ymax = min(127, max(sy1 + 8, surf_max + 3))
    ymin = max(0, sy0 - 14)
    mapw = (hmax - hmin + 1) * scale
    maph = (ymax - ymin + 1) * scale
    entries = [(pal[p["index"]], f"#{p['index']:02d} {display_name(p['template'])}") for p in plane]
    entries.append(((30, 140, 60), "地表线（最高非空气）"))
    entries.append(((88, 58, 58), "下界岩（地形）"))
    left, top, right, bottom = 92, 112, 330, 64
    W = left + mapw + right
    H = top + max(maph, 26 + len(entries) * 20) + bottom
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    title = f"金之牢狱 · 剖面 {'A' if axis == 'x' else 'B'}：{'x' if axis == 'x' else 'z'}={fixed}（横轴 {hname} · 纵轴 y）"
    sub = (f"种子 {meta['seed']} · 行走面 y={walk} · 结构 y={sy0}..{sy1} · "
           f"屋顶到地表最多 {max(0, surf_max - sy1)} 格")
    header(d, left, title, sub,
           "白 = 空气 · 彩色 = 结构件（按件着色）· 深色 = 地形 · 绿色折线 = 每列地表（最高非空气）")

    ox, oy = left, top
    d.rectangle([ox, oy, ox + mapw - 1, oy + maph - 1], fill=(255, 255, 255))
    for y in range(ymin - ymin % 4, ymax + 1, 4):
        py = oy + (ymax - y) * scale
        d.line([(ox, py), (ox - 6, py)], fill=(90, 90, 96), width=1)
        d.text((ox - 9, py), str(y), font=font(10), fill=(70, 70, 76), anchor="rm")
    for h in range(hmin - hmin % 8, hmax + 1, 8):
        px = ox + (h - hmin) * scale
        d.line([(px, oy + maph), (px, oy + maph + 6)], fill=(90, 90, 96), width=1)
        d.text((px, oy + maph + 9), str(h), font=font(10), fill=(70, 70, 76), anchor="mt")

    for x, y, z, bid in arr:
        h = z if axis == "x" else x
        if not (ymin <= y <= ymax):
            continue
        pi = piece_at(boxes, x, y, z)
        c = pal[pi] if pi >= 0 else shade(mat_color(bid), 0.78)
        px = ox + (h - hmin) * scale
        py = oy + (ymax - y) * scale
        d.rectangle([px, py, px + scale - 1, py + scale - 1], fill=c)

    for p in plane:
        b = p["bbox"]
        h0 = b[2] if axis == "x" else b[0]
        h1 = b[5] if axis == "x" else b[3]
        if not (b[1] <= ymax and b[4] >= ymin):
            continue
        px0 = ox + (h0 - hmin) * scale
        px1 = ox + (h1 - hmin + 1) * scale - 1
        d.rectangle([px0, oy, px1, oy + maph - 1], outline=(40, 40, 44), width=1)
        d.text(((px0 + px1) / 2, oy - 3), f"#{p['index']}", font=font(9), fill=(30, 30, 34), anchor="mb")

    pts = [(ox + (h - hmin) * scale + scale / 2, oy + (ymax - surface[h]) * scale)
           for h in sorted(surface) if ymin <= surface[h] <= ymax]
    if len(pts) > 1:
        d.line(pts, fill=(30, 140, 60), width=2)
    py = oy + (ymax - walk) * scale
    for px in range(0, mapw, 14):
        d.line([(ox + px, py), (ox + min(px + 7, mapw), py)], fill=(190, 40, 40), width=1)
    txt = f"行走面 y={walk}"
    f = font(11)
    tw = d.textbbox((0, 0), txt, font=f)[2]
    d.rectangle([ox + 4, py - 14, ox + 10 + tw, py - 1], fill=(255, 255, 255))
    d.text((ox + 6, py - 13), txt, font=f, fill=(170, 30, 30))

    draw_compass(d, ox + mapw - 40, oy + maph - 38)
    draw_legend(d, left + mapw + 18, top, entries, "该剖面穿过的件")
    d.text((left, H - 34), f"沿 {'x' if axis == 'x' else 'z'}={fixed} 切开；"
                           "绿色折线 = 每列最高方块（地表），与屋顶的高差 = 埋深。",
           font=font(12), fill=(90, 90, 98))
    img.save(out, "PNG")
    print("[png]", out.name, img.size)


def ascii_map(meta, pieces):
    """粗网格缩略图：每 4 格 1 字符，用 0-9A-H 填件号（0 = 宝藏房）。"""
    bb = meta["pieceUnionBBox"]
    step = 4
    W = (bb[3] - bb[0]) // step + 1
    H = (bb[5] - bb[2]) // step + 1
    grid = [[" "] * W for _ in range(H)]
    for p in pieces:
        b = p["bbox"]
        x0 = (b[0] - bb[0]) // step
        x1 = min(W - 1, (b[3] - bb[0]) // step)
        z0 = (b[2] - bb[2]) // step
        z1 = min(H - 1, (b[5] - bb[2]) // step)
        ch = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[p["index"]]
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                grid[z][x] = ch
    lines = []
    for row in grid:
        lines.append("".join(row))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=r"docs\金之牢狱-生成预览\_raw")
    ap.add_argument("--out", dest="out", default=r"docs\金之牢狱-生成预览")
    args = ap.parse_args()
    inp, out = Path(args.inp), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    meta, pieces, blocks, secs = load(inp)
    pal = palette(pieces)
    fig_overview(meta, pieces, blocks, pal, out / "00-整体俯视图.png")
    miny = min(p["bbox"][1] for p in pieces)
    maxy = max(p["bbox"][4] for p in pieces)
    walk = max(p["bbox"][1] for p in pieces) + 1
    layers = sorted(set([miny, walk - 1, walk, walk + 1, walk + 2, maxy]))
    tags = {miny: "宝藏房地板", walk - 1: "普通件地板 / 门洞下",
            walk: "门洞下沿（行走面）", walk + 1: "门洞中段", walk + 2: "门洞上沿",
            maxy: "屋顶层"}
    n = 1
    for y in layers:
        fig_layer(meta, pieces, blocks, pal, out / f"{n:02d}-分层俯视-y{y}.png", y,
                  tags.get(y, f"y={y}"))
        n += 1
    fig_connect(meta, pieces, pal, out / f"{n:02d}-连通示意图.png")
    n += 1
    fig_section(meta, pieces, pal, secs["section_x"], "x", out / f"{n:02d}-剖面A-x{meta['sectionX']}.png")
    n += 1
    fig_section(meta, pieces, pal, secs["section_z"], "z", out / f"{n:02d}-剖面B-z{meta['sectionZ']}.png")
    print()
    print(ascii_map(meta, pieces))


if __name__ == "__main__":
    main()
