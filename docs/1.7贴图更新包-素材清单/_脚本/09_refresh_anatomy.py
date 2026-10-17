# -*- coding: utf-8 -*-
"""刻画"翻新点"：alpha 掩码是否变化、改动落在哪些坐标、亮暗方向。

对每类取 8 族，汇报：
  alpha_changed : alpha 通道发生变化的像素数（0 => 剪影完全没变，只是内部颜色）
  opaque_old/new: 不透明像素数
  darker/lighter: 改动像素中 R+G+B 总和变小/变大的个数
  coords        : 改动坐标（按族合并去重，最多列 24 个）
"""
import sys, os
from collections import Counter
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

    for kid, pat in KIND:
        ca, dark, light, co = 0, 0, 0, Counter()
        permask = []
        for i, zf in enumerate(plan[kid]):
            t = arr(os.path.join(TEX, pat.format(f=FAM[i]).replace("/", os.sep)))
            a = zarr[zf]
            da = (a[:, :, 3] != t[:, :, 3])
            ca += int(da.sum())
            m = (np.abs(a - t).max(axis=2) > 0)
            so = t[:, :, :3].sum(axis=2)
            sn = a[:, :, :3].sum(axis=2)
            dark += int((sn[m] < so[m]).sum())
            light += int((sn[m] > so[m]).sum())
            ys, xs = np.nonzero(m)
            for y, x in zip(ys, xs):
                co[(int(y), int(x))] += 1
            o_old = int((t[:, :, 3] > 0).sum())
            o_new = int((a[:, :, 3] > 0).sum())
            permask.append((o_old, o_new))
        mv = sorted({v for v in [p[0] for p in permask]})
        print("\n=== %s  (alpha_changed=%d, darker=%d lighter=%d)" % (kid, ca, dark, light))
        print("    opaque_old=%s opaque_new=%s" % (sorted({p[0] for p in permask}),
                                                   sorted({p[1] for p in permask})))
        top = co.most_common(24)
        print("    改动坐标(族计数) %s" % " ".join("%d,%d x%d" % (y, x, n) for (y, x), n in top))


if __name__ == "__main__":
    main()
