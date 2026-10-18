# -*- coding: utf-8 -*-
"""bgn10err: 生成候选修法的预览图（只读源 PNG）"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "docs" / "bgn10err-证据" / "01-像素分析"
own = Image.open(ROOT / "src/main/resources/assets/bettergold/textures/gui/container/sturdygold_anvil.png").convert("RGBA")
err = Image.open(EV / "error.png").convert("RGBA")
BOX = (99, 45, 127, 66)
PLATE = (198, 198, 198, 255)
GREY = (139, 139, 139, 255)
REDS = {(150, 35, 0, 255), (186, 55, 15, 255)}

bg = own.crop(BOX)

variants = {}
# V1: 原版精灵里除「板」以外的全部像素（红叉 + 灰箭头）
v1 = bg.copy()
for y in range(21):
    for x in range(28):
        p = err.getpixel((x, y))
        if p != PLATE:
            v1.putpixel((x, y), p)
variants["v1-red-and-grey-arrow"] = v1
# V2: 只取红叉像素
v2 = bg.copy()
for y in range(21):
    for x in range(28):
        if err.getpixel((x, y)) in REDS:
            v2.putpixel((x, y), err.getpixel((x, y)))
variants["v2-red-x-only"] = v2
# V3: 红叉 + 把灰箭头换成作者自己的暗棕（作者图该位置原像素，即直接去掉箭头覆盖）
v3 = v2.copy()
variants["v3-same-as-v2"] = v3

for name, im in variants.items():
    im.save(EV / ("cand-%s.png" % name))
    comp = own.copy()
    comp.alpha_composite(im, (99, 45))
    c = comp.crop((88, 34, 139, 77))
    c.resize((c.width * 10, c.height * 10), Image.NEAREST).save(EV / ("cand-ctx-%s.png" % name))

# 对比度量化：红叉像素下面的作者原色
print("红叉像素数 = %d" % sum(1 for y in range(21) for x in range(28) if err.getpixel((x, y)) in REDS))
under = {}
for y in range(21):
    for x in range(28):
        if err.getpixel((x, y)) in REDS:
            under[bg.getpixel((x, y))] = under.get(bg.getpixel((x, y)), 0) + 1
print("红叉像素下方的作者原色（前 8）：")
for p, n in sorted(under.items(), key=lambda kv: -kv[1])[:8]:
    print("   #%02X%02X%02X n=%d" % (p[0], p[1], p[2], n))


def lum(p):
    return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]


print("\n红叉 vs 作者原色 亮度差（<25 视为难辨）：")
pairs = {}
for y in range(21):
    for x in range(28):
        e = err.getpixel((x, y))
        if e in REDS:
            a = bg.getpixel((x, y))
            d = int(abs(lum(e) - lum(a)))
            pairs[d] = pairs.get(d, 0) + 1
bad = sum(n for d, n in pairs.items() if d < 25)
print("   最小差 = %d / 最大差 = %d / 亮度差<25 的像素 = %d / 81" % (min(pairs), max(pairs), bad))
print("\n[saved] cand-*.png")
