# -*- coding: utf-8 -*-
"""逐张 diff 统计：翻新包 vs 仓库现有贴图，到底改了哪些像素。"""
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
    tot = 0
    print("%-13s %-22s %-34s %6s %6s %6s %6s" %
          ("kind", "zipfile", "target", "npx", "diff", "mae", "maxd"))
    for kid, pat in KIND:
        for i, zf in enumerate(plan[kid]):
            t = arr(os.path.join(TEX, pat.format(f=FAM[i]).replace("/", os.sep)))
            a = zarr[zf]
            assert a.shape == t.shape, (a.shape, t.shape)
            d = np.abs(a - t)
            npx = int((d.max(axis=2) > 0).sum())
            print("%-13s %-22s %-34s %6d %6d %6.3f %6d"
                  % (kid, zf, pat.format(f=FAM[i]), a.shape[0] * a.shape[1],
                     npx, d.mean(), int(d.max())))
            tot += npx
    print("\n[diff] total differing px across 72 pairs = %d" % tot)


if __name__ == "__main__":
    main()
