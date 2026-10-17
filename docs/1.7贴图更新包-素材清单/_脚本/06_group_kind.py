# -*- coding: utf-8 -*-
"""对每个时间戳组（8 张）在"全部 8 个 16x16 候选类"上做匈牙利指派，找出它到底属于哪一类。

候选类（16x16）：item/<f>_axe, _shovel, _knife, _chain, _leggings, _lantern,
                 block/<f>_bars, block/<f>_chain
判据：指派后的 MAE 总和（越小越像）；同时打印每张的 best 目标与次优（族歧义）。
"""
import sys, os
sys.stdout.reconfigure(errors="replace")
import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
ZIPDIR = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
FAM = ["sturdygold", "indigoseagold", "illusiongold", "thornsgold",
       "thundergold", "voodoogold", "flamegold", "echogold"]
CAND16 = [("axe", "item/{f}_axe.png"), ("shovel", "item/{f}_shovel.png"),
          ("knife", "item/{f}_knife.png"), ("chain_item", "item/{f}_chain.png"),
          ("leggings_item", "item/{f}_leggings.png"), ("lantern_item", "item/{f}_lantern.png"),
          ("bars", "block/{f}_bars.png"), ("chain_block", "block/{f}_chain.png")]


def arr(p):
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.float64)


def main():
    zfiles = sorted(f for f in os.listdir(ZIPDIR) if f.endswith(".png"))
    zarr = {f: arr(os.path.join(ZIPDIR, f)) for f in zfiles}
    small = [f for f in zfiles if zarr[f].shape == (16, 16, 4)]
    groups = [small[i:i + 8] for i in range(0, len(small), 8)]
    T = {}
    for kid, pat in CAND16:
        T[kid] = [(f, arr(os.path.join(TEX, pat.format(f=f).replace("/", os.sep)))) for f in FAM]
    print("16x16 zip=%d groups=%d" % (len(small), len(groups)))
    best_map = {}
    for gi, g in enumerate(groups):
        print("\n--- group %d : %s .. %s" % (gi + 1, g[0], g[-1]))
        res = []
        for kid, _p in CAND16:
            M = np.zeros((8, 8))
            for i, zf in enumerate(g):
                for j, (f, a) in enumerate(T[kid]):
                    M[i, j] = np.abs(zarr[zf] - a).mean()
            ri, ci = linear_sum_assignment(M)
            tot = M[ri, ci].sum()
            res.append((tot, kid, M, ri, ci))
        res.sort()
        for tot, kid, M, ri, ci in res[:3]:
            print("   kind=%-14s sumMAE=%8.2f  mean=%6.2f" % (kid, tot, tot / 8.0))
        tot, kid, M, ri, ci = res[0]
        assign = {i: j for i, j in zip(ri, ci)}
        for i, zf in enumerate(g):
            j = assign[i]
            others = sorted((M[i, k] for k in range(8) if k != j))
            print("     %-22s -> %-14s mae=%6.2f 2nd=%6.2f (%-12s) ratio=%.2f"
                  % (zf, FAM[j], M[i, j], others[0], FAM[[k for k in range(8) if k != j][int(np.argmin([M[i, k] for k in range(8) if k != j]))]], (others[0] + 1e-9) / (M[i, j] + 1e-9)))
        best_map[gi] = (kid, tot / 8.0)
    print("\n=== 组 -> 类 ===")
    for gi, (kid, m) in best_map.items():
        print("group %d : %-14s meanMAE=%.2f" % (gi + 1, kid, m))


if __name__ == "__main__":
    main()
