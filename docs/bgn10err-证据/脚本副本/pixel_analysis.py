# -*- coding: utf-8 -*-
"""bgn10err: 万坚金砧 GUI「无法锻造时的灰色矩形」来源定位（逐像素）。
只读：不改任何 PNG / 源码。
用法: py -3 probe/bgn10err/pixel_analysis.py
"""
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "docs" / "bgn10err-证据" / "01-像素分析"
OUT = []

BOX = (99, 45, 127, 66)  # 28 x 21  (right/bottom exclusive)


def w(line=""):
    OUT.append(line)
    print(line)


def hx(p):
    return "%02X%02X%02X%02X" % p


def hist_of(img, box=None):
    im = img.crop(box) if box else img
    c = Counter()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            c[im.getpixel((x, y))] += 1
    return c


def dump(img, box, title, sym=None):
    crop = img.crop(box) if box else img
    wch, hch = crop.size
    w("=" * 78)
    w("%s  box=%s  size=%dx%d" % (title, box, wch, hch))
    hist = hist_of(crop)
    alpha0 = sum(n for p, n in hist.items() if p[3] == 0)
    semi = sum(n for p, n in hist.items() if 0 < p[3] < 255)
    w("  像素总数 = %d；alpha==0 = %d；0<alpha<255 = %d；alpha==255 = %d"
      % (wch * hch, alpha0, semi, wch * hch - alpha0 - semi))
    w("  唯一颜色数 = %d" % len(hist))
    w("  颜色直方图（按像素数降序）:")
    for p, n in hist.most_common(20):
        w("    %s  n=%-4d  rgb=(%3d,%3d,%3d) a=%3d  %s"
          % (hx(p), n, p[0], p[1], p[2], p[3],
             "灰(R=G=B)" if p[0] == p[1] == p[2] else "彩"))
    if sym:
        w("  4 值图例由调用方提供")
    # 每像素 6 位十六进制（2 位 RGB 灰阶/红）
    w("  逐像素 RGB 十六进制（行=y）:")
    w("      " + "".join("%5d" % x for x in range(wch)))
    for y in range(hch):
        row = "".join("%5s" % ("....." if crop.getpixel((x, y))[3] == 0
                               else "%02X%02X%02X" % crop.getpixel((x, y))[:3]) for x in range(wch))
        w("  %3d %s" % (y, row))
    return crop


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    perr = EV / "error.png"
    pvan = EV / "anvil.png"
    pown = ROOT / "src/main/resources/assets/bettergold/textures/gui/container/sturdygold_anvil.png"
    err = Image.open(perr).convert("RGBA")
    van = Image.open(pvan).convert("RGBA")
    own = Image.open(pown).convert("RGBA")

    w("### 0 文件基本信息（只读打开）")
    for name, im, p in [("vanilla error.png", err, perr), ("vanilla anvil.png", van, pvan),
                        ("author sturdygold_anvil.png", own, pown)]:
        w("  %-30s size=%-9s mode=%s bytes=%d" % (name, str(im.size), im.mode, p.stat().st_size))

    w("")
    w("### 1 原版 error 精灵本体（整张，28x21）")
    dump(err, None, "vanilla error.png 全图")

    w("")
    w("### 2 目标区域 = GUI 左上角 +(99,45) 起 28x21")
    dump(own, BOX, "作者 sturdygold_anvil.png 的 (99,45)-(126,65)")
    dump(van, BOX, "原版 anvil.png 同区域（对照：原版这里是不是就是 #C6C6C6）")

    w("")
    w("### 3 4 值 ASCII：原版 error 精灵的结构")
    w("  图例: '.'=#C6C6C6(198,198,198)  '#'=#8B8B8B(139,139,139)  'D'=#962300(150,35,0)  'R'=#BA370F(186,55,15)")
    legend = {(198, 198, 198, 255): ".", (139, 139, 139, 255): "#",
              (150, 35, 0, 255): "D", (186, 55, 15, 255): "R"}
    for y in range(21):
        s = ""
        for x in range(28):
            p = err.getpixel((x, y))
            s += legend.get(p, "?")
        w("  %2d |%s|" % (y, s))

    w("")
    w("### 4 结构量化：灰底矩形 vs 红叉 vs 灰阴影")
    eh = hist_of(err)
    n_c6 = eh[(198, 198, 198, 255)]
    n_8b = eh[(139, 139, 139, 255)]
    n_d = eh[(150, 35, 0, 255)]
    n_r = eh[(186, 55, 15, 255)]
    w("  #C6C6C6 灰底 = %d 像素" % n_c6)
    w("  #8B8B8B 灰   = %d 像素（位置的 x 范围 / y 范围见下）" % n_8b)
    xs = [x for y in range(21) for x in range(28) if err.getpixel((x, y)) == (139, 139, 139, 255)]
    ys = [y for y in range(21) for x in range(28) if err.getpixel((x, y)) == (139, 139, 139, 255)]
    w("       #8B8B8B 的 x∈[%d,%d], y∈[%d,%d]" % (min(xs), max(xs), min(ys), max(ys)))
    w("  #962300 深红 = %d 像素；#BA370F 亮红 = %d 像素；红合计 = %d" % (n_d, n_r, n_d + n_r))
    w("  ⇒ 灰(R=G=B 不透明) 合计 = %d / 588 = %.1f%%；红合计 = %.1f%%；半透明 = 0"
      % (n_c6 + n_8b, 100.0 * (n_c6 + n_8b) / 588, 100.0 * (n_d + n_r) / 588))

    w("")
    w("### 5 作者图同区域：有没有灰？")
    oh = hist_of(own, BOX)
    w("  像素数 = %d；唯一颜色 = %d" % (sum(oh.values()), len(oh)))
    grey = sum(n for p, n in oh.items() if p[0] == p[1] == p[2])
    w("  R==G==B 的像素 = %d（含 alpha 任何值）" % grey)
    for p, n in oh.most_common(10):
        w("    %s n=%-4d rgb=(%3d,%3d,%3d)" % (hx(p), n, p[0], p[1], p[2]))
    w("  ⇒ 作者贴图该区域是不是灰底：%s" % ("是" if grey > 0 else "不是（%d 个灰像素）" % grey))

    w("")
    w("### 6 原版 anvil.png 同区域（解释「通常来说这是正常的」）")
    vh = hist_of(van, BOX)
    w("  像素数 = %d；唯一颜色 = %d" % (sum(vh.values()), len(vh)))
    for p, n in vh.most_common(6):
        w("    %s n=%-4d" % (hx(p), n))
    c6 = vh[(198, 198, 198, 255)]
    w("  #C6C6C6 = %d / 588 ⇒ 与原版 error 精灵灰底同色 ⇒ 在原版里这块灰矩形**与面板融为一体、看不出来**"
      % c6)

    w("")
    w("### 7 叠加后玩家实际看到什么（最近邻 1:1，精灵全部不透明 ⇒ 完全覆盖）")
    w("  因为精灵 28x21 且 alpha 全 255，`blitSprite(err, x+99, y+45, 28, 21)` 是 1:1 贴上去、把作者金色像素**整块盖掉**。")
    w("  合成图（= 精灵原图，逐像素）:")
    for y in range(21):
        s = ""
        for x in range(28):
            p = err.getpixel((x, y))
            if p[0] == p[1] == p[2]:
                s += "#" if p[0] < 180 else "+"
            else:
                s += "R"
        w("  %2d |%s|" % (y, s))
    w("  图例: '+'=#C6C6C6 灰底  '#'=#8B8B8B 灰  'R'=红叉")

    (EV / "01-像素分析.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
    print("\n[saved] %s" % (EV / "01-像素分析.txt"))


if __name__ == "__main__":
    main()
