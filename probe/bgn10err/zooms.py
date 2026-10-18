# -*- coding: utf-8 -*-
"""bgn10err: 放大截图（只读源 PNG，输出新文件到证据目录）"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "docs" / "bgn10err-证据" / "01-像素分析"
own = Image.open(ROOT / "src/main/resources/assets/bettergold/textures/gui/container/sturdygold_anvil.png").convert("RGBA")
van = Image.open(EV / "anvil.png").convert("RGBA")
err = Image.open(EV / "error.png").convert("RGBA")

CTX = (88, 34, 139, 77)  # 上下文 51x43
for tag, im, box in [("author-ctx", own, CTX), ("vanilla-ctx", van, CTX)]:
    c = im.crop(box)
    c.resize((c.width * 10, c.height * 10), Image.NEAREST).save(EV / ("zoom-%s.png" % tag))
e = err.resize((28 * 12, 21 * 12), Image.NEAREST)
e.save(EV / "zoom-error-sprite.png")

# 对照图：作者 ctx + 把原版 error 精灵 1:1 盖上去
comp = own.copy()
comp.alpha_composite(err, (99, 45))
c = comp.crop(CTX)
c.resize((c.width * 10, c.height * 10), Image.NEAREST).save(EV / "zoom-composited-before.png")

# 8B8B8B 掩码对比
def mask(im, col, box):
    s = set()
    c = im.crop(box)
    for y in range(c.size[1]):
        for x in range(c.size[0]):
            if c.getpixel((x, y)) == col:
                s.add((x, y))
    return s

BOX = (99, 45, 127, 66)
m_err = mask(err, (139, 139, 139, 255), (0, 0, 28, 21))
m_van = mask(van, (139, 139, 139, 255), BOX)
print("error #8B8B8B n=%d" % len(m_err))
print("vanilla panel #8B8B8B n=%d" % len(m_van))
print("两集合相等: %s   对称差 = %d" % (m_err == m_van, len(m_err ^ m_van)))
print("error ∩ vanilla = %d" % len(m_err & m_van))

# 作者图里"暗"像素（亮度<120）掩码，和 error 的灰掩码比
def mask_cond(im, box, fn):
    s = set()
    c = im.crop(box)
    for y in range(c.size[1]):
        for x in range(c.size[0]):
            p = c.getpixel((x, y))
            if fn(p):
                s.add((x, y))
    return s

m_own_dark = mask_cond(own, BOX, lambda p: p[3] == 255 and max(p[:3]) < 120)
print("作者图暗像素(亮度<120) n=%d" % len(m_own_dark))
print("作者暗像素 ∩ vanilla #8B8B8B = %d" % len(m_own_dark & m_van))
print("作者暗像素 == vanilla #8B8B8B 掩码: %s" % (m_own_dark == m_van))
print("\n[saved] zoom-*.png")
