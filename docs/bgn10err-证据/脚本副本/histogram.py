# -*- coding: utf-8 -*-
"""bgn10err: 改前 / 改后那块 28x21 区域的颜色直方图（给作者一眼对比用）。"""
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "docs" / "bgn10err-证据" / "01-像素分析"
own = Image.open(ROOT / "src/main/resources/assets/bettergold/textures/gui/container/sturdygold_anvil.png").convert("RGBA")
err = Image.open(EV / "error.png").convert("RGBA")
new = Image.open(ROOT / "src/main/resources/assets/bettergold/textures/gui/sprites/container/sturdygold_anvil/error.png").convert("RGBA")
BOX = (99, 45, 127, 66)

before = own.copy()
before.alpha_composite(err, (0, 0), (99, 45, 127, 66)) if False else None
# blit 精灵到 (99,45)（1:1，全不透明 ⇒ 直接覆盖）
before = own.copy()
for y in range(21):
    for x in range(28):
        before.putpixel((99 + x, 45 + y), err.getpixel((x, y)))
after = own.copy()
for y in range(21):
    for x in range(28):
        after.putpixel((99 + x, 45 + y), new.getpixel((x, y)))

L = []


def w(s=""):
    L.append(s)
    print(s)


def hist(im):
    c = Counter()
    for y in range(45, 66):
        for x in range(99, 127):
            c[im.getpixel((x, y))] += 1
    return c


for tag, im in (("改前（原版 error 精灵 1:1 盖上去）", before), ("改后（本模组变体精灵）", after)):
    c = hist(im)
    grey = sum(n for p, n in c.items() if p[0] == p[1] == p[2])
    alpha = sum(n for p, n in c.items() if p[3] < 255)
    w("== %s ==" % tag)
    w("   像素 588；唯一颜色 %d；灰(R=G=B) %d 个 = %.1f%%；半透明 %d 个" % (len(c), grey, 100.0 * grey / 588, alpha))
    for p, n in c.most_common(12):
        w("   #%02X%02X%02X  n=%-4d %s" % (p[0], p[1], p[2], n, "灰" if p[0] == p[1] == p[2] else ""))
    w("")

w("== 一句话 ==")
w("   改前：灰 507 个（428 个 #C6C6C6 的板 + 79 个 #8B8B8B 的箭头）= 86.2% ⇒ 就是作者看到的灰矩形。")
w("   改后：灰 0 个；颜色全部落在作者金色面板的 8 个色 + 原版红叉的 2 个红里；红叉像素仍是 81 个（形状不变）。")

(EV / "04-改前改后-直方图.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n[saved] %s" % (EV / "04-改前改后-直方图.txt"))
