# -*- coding: utf-8 -*-
"""bg18b · P5 像素认亲：同尺寸 + 像素相似度（不猜，只排候选）。

相似度定义：
  * eq   = 完全相同像素（RGBA 四通道全等）占比
  * mad  = 平均通道差（0..255，RGBA 全算，含 alpha；越小越像）
  * rgb  = 只算 RGB（忽略 alpha）的平均通道差
对每个源图，打印同尺寸候选里 eq 最高 / mad 最低的前 8 名。
"""
import io
import os
import sys

import numpy as np
from PIL import Image

SRC = r"docs\1.7贴图更新包第二关-素材清单"
TEX = r"src\main\resources\assets\bettergold\textures"


def load(path):
    im = Image.open(path).convert("RGBA")
    return np.asarray(im, dtype=np.int16), im.size


def score(a, b):
    if a.shape != b.shape:
        return None
    d = np.abs(a - b)
    eq = float(np.all(d == 0, axis=2).mean())
    mad = float(d.mean())
    rgb = float(d[:, :, :3].mean())
    return eq, mad, rgb


def main():
    # 索引全部现有贴图
    index = {}
    for root, _dirs, files in os.walk(TEX):
        for fn in files:
            if not fn.lower().endswith(".png"):
                continue
            p = os.path.join(root, fn)
            arr, size = load(p)
            index[os.path.relpath(p, TEX).replace("\\", "/")] = (arr, size, p)
    print("[index] textures=%d" % len(index))

    srcs = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".png"))
    for s in srcs:
        arr, size = load(os.path.join(SRC, s))
        rows = []
        for rel, (barr, bsize, _p) in index.items():
            if bsize != size:
                continue
            sc = score(arr, barr)
            if sc:
                rows.append((sc[0], sc[1], sc[2], rel))
        total_same = len(rows)
        rows.sort(key=lambda r: (-r[0], r[1]))
        print("\n=== %s  size=%dx%d  same-size candidates=%d" % (s, size[0], size[1], total_same))
        for eq, mad, rgb, rel in rows[:8]:
            print("   eq=%6.2f%% mad=%7.3f rgb=%7.3f  %s" % (eq * 100, mad, rgb, rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
