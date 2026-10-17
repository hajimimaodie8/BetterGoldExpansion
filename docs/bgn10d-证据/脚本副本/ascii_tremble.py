# -*- coding: utf-8 -*-
"""#12 颤栗贴图：把两张 18x18 图标打成 ASCII 图（alpha 掩码 + 亮度）并算形状相似度。
视觉模型不可用时的替代证据：形状/颜色可逐像素复算。"""
import hashlib
import os
import sys
from collections import Counter

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OLD = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold",
                   "textures", "mob_effect", "tremble.png")
NEW = os.path.join(ROOT, "docs", "新约10-素材清单", "新约10", "颤栗(新图标).png")

RAMP = " .:-=+*#%@"


def load(p):
    im = Image.open(p).convert("RGBA")
    return im, im.load()


def ascii_art(px, w, h, mode="alpha"):
    lines = []
    for y in range(h):
        row = []
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                row.append(" ")
                continue
            if mode == "alpha":
                row.append("#" if a >= 128 else "+")
            else:
                lum = (r * 299 + g * 587 + b * 114) // 1000
                row.append(RAMP[min(len(RAMP) - 1, lum * len(RAMP) // 256)])
        lines.append("".join(row))
    return lines


def bbox(px, w, h):
    xs = [x for y in range(h) for x in range(w) if px[x, y][3] > 0]
    ys = [y for y in range(h) for x in range(w) if px[x, y][3] > 0]
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def main():
    o_img, o = load(OLD)
    n_img, n = load(NEW)
    w, h = o_img.size
    print("== 旧 tremble.png ==")
    for ln in ascii_art(o, w, h, "alpha"):
        print("  " + ln)
    print("  亮度：")
    for ln in ascii_art(o, w, h, "lum"):
        print("  " + ln)
    print("== 新 颤栗(新图标).png ==")
    for ln in ascii_art(n, w, h, "alpha"):
        print("  " + ln)
    print("  亮度：")
    for ln in ascii_art(n, w, h, "lum"):
        print("  " + ln)

    # 形状相似度：alpha>0 掩码的 IoU
    inter = union = 0
    mask_o = set()
    mask_n = set()
    for y in range(h):
        for x in range(w):
            if o[x, y][3] > 0:
                mask_o.add((x, y))
            if n[x, y][3] > 0:
                mask_n.add((x, y))
    inter = len(mask_o & mask_n)
    union = len(mask_o | mask_n)
    print("alpha-mask IoU = %d/%d = %.3f" % (inter, union, inter / union))
    print("bbox old =", bbox(o, w, h), " bbox new =", bbox(n, w, h))

    # 颜色统计（只统计不透明像素）
    for tag, px in (("old", o), ("new", n)):
        c = Counter(px[x, y] for y in range(h) for x in range(w) if px[x, y][3] > 0)
        print("%s 颜色 TOP6: %s" % (tag, c.most_common(6)))
        print("%s 独立颜色数 = %d" % (tag, len(c)))


if __name__ == "__main__":
    main()
