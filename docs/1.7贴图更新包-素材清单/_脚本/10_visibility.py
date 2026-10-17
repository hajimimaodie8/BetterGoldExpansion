# -*- coding: utf-8 -*-
"""关键判定：改动像素是否落在 alpha==0（不可见）处。

若全部落在 alpha==0 => 两图"视觉完全相同"，只是透明区 RGB 不同（重新导出/清底）。
若落在 alpha>0  => 是真实的可见改色。
同时打印这些像素的 old/new 具体 RGBA，便于人工核对。
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
KIND = [("axe", "item/{f}_axe.png"), ("shovel", "item/{f}_shovel.png"),
        ("knife", "item/{f}_knife.png"), ("chain_block", "block/{f}_chain.png"),
        ("chain_item", "item/{f}_chain.png"), ("bars", "block/{f}_bars.png"),
        ("leggings", "item/{f}_leggings.png"),
        ("lantern", "block/{f}_lantern.png"),
        ("armor_l1", "models/armor/{f}_layer_1.png")]


def arr(p):
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.int32)


def main():
    zfiles = sorted(f for f in os.listdir(ZIPDIR) if f.endswith(".png"))
    zarr = {f: arr(os.path.join(ZIPDIR, f)) for f in zfiles}
    small = [f for f in zfiles if zarr[f].shape == (16, 16, 4)]
    lantern = [f for f in zfiles if zarr[f].shape == (48, 16, 4)]
    armor = [f for f in zfiles if zarr[f].shape == (32, 64, 4)]
    plan = {}
    for i, (kid, _p) in enumerate(KIND):
        plan[kid] = small[i * 8:(i + 1) * 8] if i < 7 else None
    plan["lantern"] = lantern
    plan["armor_l1"] = armor

    grand_vis, grand_inv = 0, 0
    for kid, pat in KIND:
        vis, inv = 0, 0
        samples = []
        for i, zf in enumerate(plan[kid]):
            t = arr(os.path.join(TEX, pat.format(f=FAM[i]).replace("/", os.sep)))
            a = zarr[zf]
            m = (np.abs(a - t).max(axis=2) > 0)
            ys, xs = np.nonzero(m)
            for y, x in zip(ys, xs):
                if t[y, x, 3] == 0 and a[y, x, 3] == 0:
                    inv += 1
                else:
                    vis += 1
                if len(samples) < 6:
                    samples.append("(%d,%d) %s -> %s" % (y, x, tuple(t[y, x]), tuple(a[y, x])))
        grand_vis += vis
        grand_inv += inv
        print("%-13s visible_changed=%3d  invisible_changed(alpha0)=%3d" % (kid, vis, inv))
        for s in samples:
            print("      %s" % s)
    print("\n[verdict] visible_changed=%d  invisible_changed=%d" % (grand_vis, grand_inv))
    if grand_vis == 0:
        print("[verdict] 全部改动都在 alpha==0 的不可见区 => 两图视觉完全相同")
    else:
        print("[verdict] 存在可见改动像素 => 是真实的可见翻新")


if __name__ == "__main__":
    main()
