# -*- coding: utf-8 -*-
"""验证 armor 组：① 与 layer_1 / layer_2 谁更像；② 改动是否全部落在靴子矩形 (x 0-15, y 16-31)。
标准 64x32 layer_1 的 UV 分区：
  头盔 x0-31  y0-15 | 身体 x16-39 y16-31 | 手臂 x40-55 y16-31 | 腿/靴 x0-15 y16-31
"""
import sys, os
sys.stdout.reconfigure(errors="replace")
import numpy as np
from PIL import Image

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
ZIPDIR = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
FAM = ["flamegold", "sturdygold", "thornsgold", "echogold",
       "indigoseagold", "voodoogold", "thundergold", "illusiongold"]


def arr(p):
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.int32)


def zone(x, y):
    if y < 16:
        return "head"
    if x < 16:
        return "leg_boot"
    if x < 40:
        return "body"
    return "arm"


def main():
    zfiles = sorted(f for f in os.listdir(ZIPDIR) if f.endswith(".png"))
    zarr = {f: arr(os.path.join(ZIPDIR, f)) for f in zfiles}
    armor = [f for f in zfiles if zarr[f].shape == (32, 64, 4)]
    print("armor zip files = %d" % len(armor))
    tot_l1 = tot_l2 = 0.0
    zones = {}
    for i, zf in enumerate(armor):
        a = zarr[zf]
        l1 = arr(os.path.join(TEX, "models", "armor", "%s_layer_1.png" % FAM[i]))
        l2 = arr(os.path.join(TEX, "models", "armor", "%s_layer_2.png" % FAM[i]))
        m1 = float(np.abs(a - l1).mean())
        m2 = float(np.abs(a - l2).mean())
        tot_l1 += m1
        tot_l2 += m2
        m = (np.abs(a - l1).max(axis=2) > 0)
        ys, xs = np.nonzero(m)
        for y, x in zip(ys, xs):
            z = zone(int(x), int(y))
            zones[z] = zones.get(z, 0) + 1
        print("  %-22s %-14s layer1=%.3f layer2=%.3f  changed_px=%d  x=[%d..%d] y=[%d..%d]"
              % (zf, FAM[i], m1, m2, int(m.sum()),
                 xs.min() if len(xs) else -1, xs.max() if len(xs) else -1,
                 ys.min() if len(ys) else -1, ys.max() if len(ys) else -1))
    print("\n[armor] mean layer_1 MAE=%.3f  mean layer_2 MAE=%.3f" % (tot_l1 / 8, tot_l2 / 8))
    print("[armor] 改动像素按 UV 分区计数: %s" % zones)


if __name__ == "__main__":
    main()
