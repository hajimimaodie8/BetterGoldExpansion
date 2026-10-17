# -*- coding: utf-8 -*-
"""歧义对消歧：对每类 flamegold / sturdygold 两张做逐像素 RGBA 诊断。

指标（全部可复算，稳定 ASCII id）：
  - pix_identical : 两图逐像素 RGBA 完全相同的像素占比（16x16 全图）
  - mae_rgba      : 逐像素 RGBA 平均绝对误差（0-255）
  - mean_rgb      : 不透明像素平均色（看色相/明度）
  - hue_lab       : CIELAB L/a/b 均值
"""
import sys, os
sys.stdout.reconfigure(errors="replace")
import numpy as np
from PIL import Image

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
ZIPDIR = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
FAM = ["sturdygold", "indigoseagold", "illusiongold", "thornsgold",
       "thundergold", "voodoogold", "flamegold", "echogold"]


def arr(p):
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.float64)


def lab_mean(a):
    m = a[:, :, 3] > 0
    if not m.any():
        return (0, 0, 0)
    rgb = a[:, :, :3][m] / 255.0
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T
    wp = np.array([0.95047, 1.0, 1.08883])
    t = xyz / wp
    f = np.where(t > 0.008856, t ** (1.0 / 3.0), 7.787 * t + 16.0 / 116.0)
    L = 116 * f[:, 1] - 16
    A = 500 * (f[:, 0] - f[:, 1])
    B = 200 * (f[:, 1] - f[:, 2])
    return (float(L.mean()), float(A.mean()), float(B.mean()))


def diag(a, b):
    same = np.all(a == b, axis=2)
    mae = np.abs(a - b).mean()
    return float(same.mean()), float(mae)


def main():
    # 注意 zip 内 16x16 共 7 类；这里直接把 7 类各 8 张与 8 族目标做全表诊断
    kinds = [("axe", "item/{f}_axe.png"), ("shovel", "item/{f}_shovel.png"),
             ("knife", "item/{f}_knife.png"), ("chain_item", "item/{f}_chain.png"),
             ("leggings", "item/{f}_leggings.png"), ("bars", "block/{f}_bars.png"),
             ("chain_block", "block/{f}_chain.png")]
    zfiles = sorted(f for f in os.listdir(ZIPDIR) if f.endswith(".png"))
    zarr = {f: arr(os.path.join(ZIPDIR, f)) for f in zfiles}
    for kid, pat in kinds:
        print("\n=== %s ===" % kid)
        for f in FAM:
            t = arr(os.path.join(TEX, pat.format(f=f).replace("/", os.sep)))
            print("  target %-14s L/a/b=%6.1f %6.1f %6.1f" % ((f,) + lab_mean(t)))
        for zf in zfiles:
            a = zarr[zf]
            if a.shape != (16, 16, 4):
                continue
            # 只对 flamegold / sturdygold 两张报最像
            rows = []
            for f in FAM:
                t = arr(os.path.join(TEX, pat.format(f=f).replace("/", os.sep)))
                s, mae = diag(a, t)
                rows.append((s, -mae, f, mae))
            rows.sort(reverse=True)
            if rows[0][0] >= 0.55 or rows[0][2] in ("flamegold", "sturdygold"):
                print("  %-22s 同像素=%5.1f%% mae=%6.2f -> %-14s  | 2nd %-14s 同像素=%5.1f%% mae=%6.2f"
                      % (zf, rows[0][0] * 100, rows[0][3], rows[0][2],
                         rows[1][2], rows[1][0] * 100, rows[1][3]))


if __name__ == "__main__":
    main()
