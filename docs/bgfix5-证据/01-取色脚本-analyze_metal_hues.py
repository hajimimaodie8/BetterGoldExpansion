# -*- coding: utf-8 -*-
"""
bgfix5 · 8 族金属贴图取色 / 色相计算 / 排序口径对照（可复算）

用法（仓库根）:
    python "docs/bgfix5-证据/01-取色脚本-analyze_metal_hues.py"

产物（全部写在 "docs/bgfix5-证据/" 下，只读贴图、不改任何贴图字节）:
    02-取色读数.txt        控制台同内容
    03-取色读数.json       结构化读数
    04-色谱对照图.png      8 族的色卡 + 锭图标（人眼核对用）

五条色相口径（互相印证，全部可复算）:
    A  ingot 平均色      = item/<族>_ingot.png 里 alpha>=128 像素的 R/G/B 算术均值 → HSV hue
    B  色卡最高彩色度    = trims/color_palettes/<族>.png 的 #1..#7 中 chroma(=S*V) 最大者的 hue
                            （#0 是八族共用的高光 rgb(255,242,149)，不算族色，故排除）
    C  色卡中间调        = 色卡 #4（作者手绘的主色档）hue
    D  色卡彩色度加权圆均值 = #1..#7 以 S*V 为权重的 hue 矢量平均（避免 0/360 环绕）
    E  锭最彩色度像素    = item/<族>_ingot.png 里 chroma(=S*V) 最大像素的 hue

hue 参照：0=红 30=橙 60=黄 120=绿 180=青 240=蓝 270=紫 300=品红 330=粉红
"""
import colorsys
import json
import math
import os
import sys
from collections import Counter

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVID = os.path.join(ROOT, "docs", "bgfix5-证据")
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures")

METALS = [
    ("flamegold", "烈燃金"),
    ("sturdygold", "万坚金"),
    ("thornsgold", "树棘金"),
    ("echogold", "幽咆金"),
    ("indigoseagold", "靛海金"),
    ("voodoogold", "巫毒金"),
    ("thundergold", "结雷金"),
    ("illusiongold", "幻惑金"),
]


def hue_sv(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return h * 360.0, s, v


def circular_mean_hue(pixels):
    """pixels = [(r,g,b,[w])] -> 色相矢量平均（含 0/360 环绕处理）"""
    x = y = 0.0
    for p in pixels:
        r, g, b = p[0], p[1], p[2]
        h, s, v = hue_sv(r, g, b)
        w = (p[3] if len(p) > 3 else 1.0) * s * v
        rad = h * math.pi / 180.0
        x += w * math.cos(rad)
        y += w * math.sin(rad)
    if x == 0.0 and y == 0.0:
        return None
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def opaque_pixels(path, alpha_min=128):
    im = Image.open(path).convert("RGBA")
    return [(r, g, b) for (r, g, b, a) in im.getdata() if a >= alpha_min]


def common_colors(per_family_px):
    """八族贴图里**共有**的像素颜色（= 不属于任何一族的"共用色"）。

    ★ 这一步是必须的：八族贴图共用同一套高光 rgb(255,242,149)（色卡 #0），
    它的 chroma 比巫毒/结雷/幻惑的**族色**还高 ⇒ 不排除它就会把"最彩色度像素"
    判成这个黄色高光（第一次运行就是这么错的：三族都读成 52.64°）。
    """
    sets = [set(px) for px in per_family_px.values()]
    return set.intersection(*sets) if sets else set()


def analyze_file(path):
    px = opaque_pixels(path)
    if not px:
        return None
    n = len(px)
    ar = sum(p[0] for p in px) / n
    ag = sum(p[1] for p in px) / n
    ab = sum(p[2] for p in px) / n
    mh, ms, mv = hue_sv(ar, ag, ab)
    best = None  # 最高色度（chroma = S*V）
    for (r, g, b) in px:
        h, s, v = hue_sv(r, g, b)
        if best is None or s * v > best[0]:
            best = (s * v, r, g, b, h, s, v)
    return {
        "opaque_px": n,
        "mean_rgb": [round(ar, 1), round(ag, 1), round(ab, 1)],
        "mean_hue": round(mh, 2),
        "mean_sat": round(ms, 4),
        "mean_val": round(mv, 4),
        "circ_hue": round(circular_mean_hue(px), 2),
        "maxchroma_rgb": [best[1], best[2], best[3]],
        "maxchroma_hue": round(best[4], 2),
        "maxchroma_sat": round(best[5], 4),
        "maxchroma_val": round(best[6], 4),
        "top_colors": [{"rgb": list(c), "n": k, "hue": round(hue_sv(*c)[0], 1)}
                       for c, k in Counter(px).most_common(6)],
    }


def main():
    os.makedirs(EVID, exist_ok=True)
    lines = []
    data = {}

    def emit(s=""):
        lines.append(s)
        print(s)

    emit("=" * 108)
    emit("bgfix5 · 8 族金属贴图取色（脚本 = docs/bgfix5-证据/01-取色脚本-analyze_metal_hues.py，可复算）")
    emit("口径：alpha>=128 像素。hue：0=红 30=橙 60=黄 120=绿 180=青 240=蓝 270=紫 300=品红 330=粉红")
    emit("=" * 108)

    rows = {}

    # ---- 预扫：八族锭贴图的共有色（= 共用高光，非族色） ----
    ingot_px = {}
    for mid, _cn in METALS:
        p = os.path.join(TEX, "item", mid + "_ingot.png")
        ingot_px[mid] = opaque_pixels(p)
    shared = common_colors(ingot_px)
    emit("")
    emit(f"八族 item/<族>_ingot.png 的共有像素颜色（= 共用高光，全族一致，判定族色时必须排除）："
         f"{sorted(shared)}")

    for mid, cn in METALS:
        data[mid] = {"cn": cn, "samples": {}}
        emit("")
        emit("-" * 108)
        emit(f"【{mid} / {cn}】")
        emit("-" * 108)
        emit(f"{'样本':<30}{'px':>6}{'平均RGB':>18}{'平均hue':>9}{'圆均值':>9}{'最彩色度RGB':>16}{'hue':>8}{'chroma':>8}")
        for label, rel in [
            ("item/<m>_ingot.png", "item/{m}_ingot.png"),
            ("item/<m>_nugget.png", "item/{m}_nugget.png"),
            ("block/<m>_block.png", "block/{m}_block.png"),
            ("trims/color_palettes/<m>.png", "trims/color_palettes/{m}.png"),
            ("models/armor/<m>_layer_1.png", "models/armor/{m}_layer_1.png"),
        ]:
            p = os.path.join(TEX, rel.format(m=mid).replace("/", os.sep))
            if not os.path.exists(p):
                emit(f"{label:<30}{'-- 缺文件 --':>18}")
                continue
            r = analyze_file(p)
            data[mid]["samples"][label] = r
            rgb = "(" + ",".join(str(int(v)) for v in r["mean_rgb"]) + ")"
            mc = "(" + ",".join(str(v) for v in r["maxchroma_rgb"]) + ")"
            emit(f"{label:<30}{r['opaque_px']:>6}{rgb:>18}{r['mean_hue']:>9}{r['circ_hue']:>9}"
                 f"{mc:>16}{r['maxchroma_hue']:>8}{round(r['maxchroma_sat']*r['maxchroma_val'],3):>8}")

        pal_path = os.path.join(TEX, "trims", "color_palettes", mid + ".png")
        im = Image.open(pal_path).convert("RGBA")
        pal = [tuple(p) for p in im.getdata()]
        data[mid]["palette_rgba"] = [list(p) for p in pal]
        emit("  色卡逐像素: " + " | ".join(
            f"#{i} rgb({r},{g},{b}) h={hue_sv(r,g,b)[0]:.1f} s={hue_sv(r,g,b)[1]:.3f} v={hue_sv(r,g,b)[2]:.3f}"
            for i, (r, g, b, a) in enumerate(pal)))

        family = [p[:3] for p in pal[1:8]]        # 排除 #0 共用高光
        best_pal = max(family, key=lambda c: hue_sv(*c)[1] * hue_sv(*c)[2])

        # 族独有色（排除八族共有色）—— E 口径的干净版本
        excl = [p for p in ingot_px[mid] if p not in shared]
        n_ex = len(excl)
        ex_mean = [sum(p[i] for p in excl) / n_ex for i in range(3)]
        ex_best = max(excl, key=lambda c: hue_sv(*c)[1] * hue_sv(*c)[2])
        emit(f"  族独有色像素 {n_ex}/{len(ingot_px[mid])}（排除共有高光）；"
             f"独有色平均 rgb({ex_mean[0]:.0f},{ex_mean[1]:.0f},{ex_mean[2]:.0f}) h={hue_sv(*ex_mean)[0]:.2f}；"
             f"独有色最彩 rgb{list(ex_best)} h={hue_sv(*ex_best)[0]:.2f}")

        rows[mid] = {
            "cn": cn,
            "A_ingot_mean_hue": data[mid]["samples"]["item/<m>_ingot.png"]["mean_hue"],
            "A2_ingot_exclusive_mean_hue": round(hue_sv(*ex_mean)[0], 2),
            "B_palette_maxchroma_hue": round(hue_sv(*best_pal)[0], 2),
            "B_palette_maxchroma_rgb": list(best_pal),
            "C_palette_mid_hue": round(hue_sv(*pal[4][:3])[0], 2),
            "C_palette_mid_rgb": list(pal[4][:3]),
            "D_palette_circ_hue": round(circular_mean_hue(family), 2),
            "E_ingot_exclusive_maxchroma_hue": round(hue_sv(*ex_best)[0], 2),
            "E_ingot_exclusive_maxchroma_rgb": list(ex_best),
            "palette_sat_mid": round(hue_sv(*pal[4][:3])[1], 3),
            "exclusive_px": n_ex,
            "total_px": len(ingot_px[mid]),
        }

    # ---------- 排序口径对照 ----------
    emit("")
    emit("=" * 108)
    emit("五条口径逐族读数（排除八族共用的高光 #0 = rgb(255,242,149)，它不是族色）")
    emit("=" * 108)
    hdr = (f"{'族':<16}{'中文':<8}{'A 锭平均hue':>12}{'A2 独有色均':>12}{'B 色卡最彩':>12}"
           f"{'C 色卡中调':>12}{'D 色卡圆均':>12}{'E 独有色最彩':>12}{'中调S':>8}")
    emit(hdr)
    emit("-" * 108)
    for mid, cn in METALS:
        r = rows[mid]
        emit(f"{mid:<16}{cn:<8}{r['A_ingot_mean_hue']:>12}{r['A2_ingot_exclusive_mean_hue']:>12}"
             f"{r['B_palette_maxchroma_hue']:>12}{r['C_palette_mid_hue']:>12}{r['D_palette_circ_hue']:>12}"
             f"{r['E_ingot_exclusive_maxchroma_hue']:>12}{r['palette_sat_mid']:>8}")

    emit("")
    emit("=" * 108)
    emit("排序对照：现行 METAL_ORDER（作者 2026-10-08 列表，= CreativeSections.METAL_ORDER）")
    emit("        vs 五条口径各自的升序（红→紫）")
    emit("=" * 108)
    current = [m for m, _ in METALS]
    emit("现行顺序        : " + " -> ".join(current))
    result = {"current_order": current, "orders": {}}
    for key, label in [("A_ingot_mean_hue", "A 锭平均hue"),
                       ("A2_ingot_exclusive_mean_hue", "A2 锭独有色均"),
                       ("B_palette_maxchroma_hue", "B 色卡最彩色度"),
                       ("C_palette_mid_hue", "C 色卡中间调"),
                       ("D_palette_circ_hue", "D 色卡彩色度加权圆均"),
                       ("E_ingot_exclusive_maxchroma_hue", "E 锭独有色最彩")]:
        order = sorted(current, key=lambda m: rows[m][key])
        same = order == current
        emit(f"{label:<16}: " + " -> ".join(order) + ("   [== 现行顺序]" if same else "   [!= 现行顺序]"))
        result["orders"][key] = {"order": order, "equals_current": same,
                                 "hues": {m: rows[m][key] for m in current}}

    # 相邻色相差（按现行顺序）
    emit("")
    emit("按现行顺序的相邻色相差（B 口径，单位 度）：")
    prev = None
    for m in current:
        h = rows[m]["B_palette_maxchroma_hue"]
        d = "" if prev is None else f"Δ={round(h - prev, 1)}"
        emit(f"  {m:<16}{rows[m]['cn']:<8}hue={h:>7.2f}   {d}")
        prev = h
    emit(f"  环绕差（幻惑 -> 烈燃+360）: Δ={round(rows[current[0]]['B_palette_maxchroma_hue'] + 360 - rows[current[-1]]['B_palette_maxchroma_hue'], 1)}")
    emit("  最大间隙: 树棘 -> 幽咆 = %.1f 度（中间没有族色）" %
         (rows["echogold"]["B_palette_maxchroma_hue"] - rows["thornsgold"]["B_palette_maxchroma_hue"]))

    # ---------- 色谱对照图 ----------
    S = 24
    W = 8 * S + 40
    H = 8 * (S + 46) + 20
    img = Image.new("RGBA", (W, H), (24, 24, 28, 255))
    d = ImageDraw.Draw(img)
    y = 16
    for mid, cn in METALS:
        pal = data[mid]["palette_rgba"]
        for i, (r, g, b, a) in enumerate(pal):
            d.rectangle([x0 := 20 + i * S, y, x0 + S - 1, y + S - 1], fill=(r, g, b, 255))
        ing = Image.open(os.path.join(TEX, "item", mid + "_ingot.png")).convert("RGBA")
        ing = ing.resize((S * 2, S * 2), Image.NEAREST)
        img.alpha_composite(ing, (20, y + S + 4))
        d.text((20 + S * 2 + 8, y + S + 10),
               f"{mid} {cn}  A={rows[mid]['A_ingot_mean_hue']}  B={rows[mid]['B_palette_maxchroma_hue']}",
               fill=(240, 240, 240, 255))
        y += S + 46
    img.save(os.path.join(EVID, "04-色谱对照图.png"))
    emit("")
    emit("[image] docs/bgfix5-证据/04-色谱对照图.png （上=该族 8 档色卡，下=该族锭图标）")

    data["_rows"] = rows
    data["_order_check"] = result
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(EVID, "02-取色读数.txt"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(txt)
    with open(os.path.join(EVID, "03-取色读数.json"), "w", encoding="utf-8", newline="\r\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\n[written] docs/bgfix5-证据/{02-取色读数.txt, 03-取色读数.json, 04-色谱对照图.png}")


if __name__ == "__main__":
    main()
