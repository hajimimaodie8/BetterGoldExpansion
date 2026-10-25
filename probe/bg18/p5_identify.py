# -*- coding: utf-8 -*-
"""bg18 / P5 步骤 1-2：**只读**解压 + 素材清单 + 像素认亲（不写任何贴图）。

  * 原始 zip 只读打开（zipfile，'r'），一个字节不改。
  * 归档副本写到 docs/1.7贴图更新包第二关-素材清单/第二关/<原名>（只新增）。
  * 素材清单.tsv：文件名 / 字节 / SHA256 / 宽×高 / 模式。
  * 认亲：同尺寸 + 像素相似度（每像素 RGBA 平均绝对差，0 = 完全相同），
    对 assets/bettergold/textures/** 全量比对，打印 top3。
"""
import hashlib
import io
import os
import sys
import zipfile

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZIP = r"E:\mc\mc资料\1.7的贴图更新包第二关.zip"
OUT = os.path.join(ROOT, "docs", "1.7贴图更新包第二关-素材清单")
DEST = os.path.join(OUT, "第二关")
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures")


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def rgba(img):
    return img.convert("RGBA")


def score(a, b):
    """每像素 RGBA 平均绝对差（0 = 完全一致）；尺寸不同返回 None"""
    if a.size != b.size:
        return None
    pa, pb = a.load(), b.load()
    w, h = a.size
    tot = 0
    for y in range(h):
        for x in range(w):
            ca, cb = pa[x, y], pb[x, y]
            tot += abs(ca[0] - cb[0]) + abs(ca[1] - cb[1]) + abs(ca[2] - cb[2]) + abs(ca[3] - cb[3])
    return tot / float(w * h * 4)


def main():
    os.makedirs(DEST, exist_ok=True)
    rows = []
    items = []
    with zipfile.ZipFile(ZIP, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            data = zf.read(info)                          # 只读
            name = os.path.basename(info.filename)
            path = os.path.join(DEST, name)
            with open(path, "wb") as f:
                f.write(data)                             # 归档副本（只新增）
            img = rgba(Image.open(io.BytesIO(data)))
            rows.append((name, len(data), sha(data), "%dx%d" % img.size, img.mode))
            items.append((name, img, data))
    with open(os.path.join(OUT, "素材清单.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("文件名\t字节\tSHA256\t尺寸\t模式\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    print("归档 %d 个文件 -> %s" % (len(rows), DEST))
    for r in rows:
        print("  %-24s %6d B  %s  %s" % (r[0], r[1], r[3], r[2][:16]))

    # 现有贴图索引
    existing = []
    for dp, _dn, fn in os.walk(TEX):
        for f in fn:
            if not f.lower().endswith(".png"):
                continue
            p = os.path.join(dp, f)
            try:
                im = rgba(Image.open(p))
            except Exception:                              # noqa: BLE001
                continue
            existing.append((os.path.relpath(p, TEX).replace("\\", "/"), im))
    print("现有贴图 %d 张" % len(existing))

    print("\n=== 认亲（同尺寸 + 每像素平均差；0 = 完全相同） ===")
    for name, img, data in items:
        cands = []
        for rel, im in existing:
            s = score(img, im)
            if s is not None:
                cands.append((s, rel))
        cands.sort()
        print("[%s] %dx%d  sha=%s" % (name, img.size[0], img.size[1], sha(data)[:12]))
        if not cands:
            print("    （没有同尺寸的现有贴图）")
        for s, rel in cands[:3]:
            print("    %.2f  %s" % (s, rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
