# -*- coding: utf-8 -*-
"""bgn10err: 生成万坚金砧的「error 精灵变体」—— 只搬运像素，不画新美术。

来源（两处，逐像素）：
  1) 背景 28×21 = 作者 256×256 贴图 `textures/gui/container/sturdygold_anvil.png`
     的矩形 (99,45)-(126,65)（= GUI 坐标 leftPos+99, topPos+45，1:1），**原样搬运**；
     这一块本身就带着作者自己画的深棕色「→」箭头。
  2) 红叉 81 像素 = 原版 `minecraft:container/anvil/error` 精灵里的两个红值
     #962300（56 px）+ #BA370F（25 px），**照坐标搬运**；原版的灰底 #C6C6C6 与
     灰箭头 #8B8B8B **一个都不搬**（那正是作者嫌别扭的灰矩形）。

⇒ 新文件里没有任何"新颜色"：507 个像素来自作者贴图、81 个来自原版精灵。

用法: py -3 probe/bgn10err/make_error_sprite.py [--check]
  --check 只比对不写盘（幂等自检用）
"""
import hashlib
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
AUTHOR = ROOT / "src/main/resources/assets/bettergold/textures/gui/container/sturdygold_anvil.png"
OUT_PNG = ROOT / "src/main/resources/assets/bettergold/textures/gui/sprites/container/sturdygold_anvil/error.png"
VANILLA_ERROR = ROOT / "docs/bgn10err-证据/01-像素分析/error.png"

AUTHOR_SHA = "?"          # 由脚本打印后再钉进关卡（不是本轮改的，是作者原件）
SRC_RECT = (99, 45, 127, 66)   # 28 x 21，右/下开区间
RED = {(150, 35, 0, 255), (186, 55, 15, 255)}   # #962300 / #BA370F


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build():
    own = Image.open(AUTHOR).convert("RGBA")
    err = Image.open(VANILLA_ERROR).convert("RGBA")
    assert own.size == (256, 256), own.size
    assert err.size == (28, 21), err.size
    bg = own.crop(SRC_RECT)
    out = bg.copy()
    reds = 0
    mask_rows = []
    for y in range(21):
        row = ""
        for x in range(28):
            p = err.getpixel((x, y))
            if p in RED:
                out.putpixel((x, y), p)
                reds += 1
                row += "R"
            else:
                row += "."
        mask_rows.append(row)
    return out, reds, mask_rows


def main():
    check_only = "--check" in sys.argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    print("作者贴图 : %s" % AUTHOR)
    print("  SHA256 = %s" % sha(AUTHOR))
    print("原版精灵 : 28x21；红像素 = %d + %d" %
          (sum(1 for y in range(21) for x in range(28)
               if Image.open(VANILLA_ERROR).convert("RGBA").getpixel((x, y)) == (150, 35, 0, 255)),
           sum(1 for y in range(21) for x in range(28)
               if Image.open(VANILLA_ERROR).convert("RGBA").getpixel((x, y)) == (186, 55, 15, 255))))
    out, reds, mask_rows = build()
    assert out.size == (28, 21)
    # 统计：新图里每个像素的来源
    own = Image.open(AUTHOR).convert("RGBA").crop(SRC_RECT)
    from_author = 0
    for y in range(21):
        for x in range(28):
            if out.getpixel((x, y)) == own.getpixel((x, y)):
                from_author += 1
    print("红叉像素 = %d；与作者同坐标同色的像素 = %d；合计 = %d" % (reds, from_author, reds + from_author))
    assert reds == 81, reds
    assert reds + from_author == 588, (reds, from_author)

    tmp = Path("build/bgn10err_error.png")
    out.save(tmp)
    print("临时产物 SHA256 = %s（%d B）" % (sha(tmp), tmp.stat().st_size))
    if check_only:
        same = OUT_PNG.is_file() and OUT_PNG.read_bytes() == tmp.read_bytes()
        print("[check] 已存在文件逐字节相同: %s" % same)
        return 0 if same else 1
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    OUT_PNG.write_bytes(tmp.read_bytes())
    print("写入 %s" % OUT_PNG)
    print("落地 SHA256 = %s（%d B）" % (sha(OUT_PNG), OUT_PNG.stat().st_size))
    print("红叉掩码（21 行 x 28 列，R=红叉 . = 作者原像素）：")
    for i, row in enumerate(mask_rows):
        print("  %2d %s" % (i, row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
