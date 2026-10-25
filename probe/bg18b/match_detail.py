# -*- coding: utf-8 -*-
"""bg18b · P5 认亲细证：对每张源图给出 MAE / alpha 掩码 / 改动像素明细，并出对照图。"""
import io
import os
import sys

import numpy as np
from PIL import Image

SRC = r"docs\1.7贴图更新包第二关-素材清单"
TEX = r"src\main\resources\assets\bettergold\textures"
OUT = r"docs\bg18-证据\05-P5-认亲"


def rgba(path):
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.int16)


def stats(a, b):
    d = np.abs(a - b)
    changed = np.any(d != 0, axis=2)
    alpha_same = bool(np.all(a[:, :, 3] == b[:, :, 3]))
    return dict(mae=float(d.mean()), changed=int(changed.sum()),
                alpha_same=alpha_same,
                opaque_a=int((a[:, :, 3] == 255).sum()),
                opaque_b=int((b[:, :, 3] == 255).sum()),
                coords=[tuple(map(int, c)) for c in np.argwhere(changed)][:40])


def up(arr, k):
    im = Image.fromarray(arr.astype(np.uint8), "RGBA")
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def main():
    os.makedirs(OUT, exist_ok=True)
    srcs = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".png"))
    for s in srcs:
        a = rgba(os.path.join(SRC, s))
        cands = []
        for root, _d, files in os.walk(TEX):
            for fn in files:
                if not fn.lower().endswith(".png"):
                    continue
                p = os.path.join(root, fn)
                b = rgba(p)
                if b.shape != a.shape:
                    continue
                st = stats(a, b)
                cands.append((st["mae"], os.path.relpath(p, TEX).replace("\\", "/"), st, b))
        cands.sort(key=lambda x: x[0])
        print("\n=== %s" % s)
        for mae, rel, st, _b in cands[:4]:
            print("  %-45s MAE=%8.4f changed=%4d alphaSame=%s opaque=%d/%d"
                  % (rel, mae, st["changed"], st["alpha_same"], st["opaque_a"], st["opaque_b"]))
            if st["changed"] <= 40:
                print("      coords=%s" % st["coords"])
        if len(cands) > 1:
            print("  ratio(2nd/1st)=%.2f" % (cands[1][0] / max(cands[0][0], 1e-9)))
        # 对照图：源 + 前 3 候选，横排
        tiles = [up(a, 10)]
        for mae, rel, st, b in cands[:3]:
            tiles.append(up(b, 10))
        w = sum(t.width for t in tiles) + 10 * (len(tiles) - 1)
        h = max(t.height for t in tiles)
        sheet = Image.new("RGBA", (w, h), (24, 24, 24, 255))
        x = 0
        for t in tiles:
            sheet.paste(t, (x, 0))
            x += t.width + 10
        sheet.save(os.path.join(OUT, s.replace(".png", "") + "_vs.png"))
    print("\n[done] sheets -> %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
