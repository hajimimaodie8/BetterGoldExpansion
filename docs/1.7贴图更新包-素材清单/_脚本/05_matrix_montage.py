# -*- coding: utf-8 -*-
"""打印每类 zip×目标 的完整 MAE 矩阵 + 生成目视拼图（证据）。

拼图版式：上排 = zip 内 8 张（按数字名排序），下排 = 对应目标（按 FAMILIES 顺序）；
每格放大 8 倍并加 1px 网格，便于人眼核对"同一族/同一类"。
"""
import sys, os
sys.stdout.reconfigure(errors="replace")
import numpy as np
from PIL import Image, ImageDraw

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
ZIPDIR = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
EVID = os.path.join(ZIPDIR, "_识别证据")
FAM = ["sturdygold", "indigoseagold", "illusiongold", "thornsgold",
       "thundergold", "voodoogold", "flamegold", "echogold"]
KINDS = [("axe16", "item/{f}_axe.png", 16), ("shovel16", "item/{f}_shovel.png", 16),
         ("knife16", "item/{f}_knife.png", 16), ("chain_item16", "item/{f}_chain.png", 16),
         ("leggings16", "item/{f}_leggings.png", 16), ("bars16", "block/{f}_bars.png", 16),
         ("chain_block16", "block/{f}_chain.png", 16),
         ("lantern1648", "block/{f}_lantern.png", 48), ("armor6432", "models/armor/{f}_layer_1.png", 32)]


def arr(p):
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.float64)


def mae(a, b):
    return float(np.abs(a - b).mean())


def montage(zfiles, targets, title, out):
    Z = 8
    cw, ch = (16 * Z, 48 * Z) if targets[0][1].shape[0] == 48 else \
             ((64 * Z, 32 * Z) if targets[0][1].shape[1] == 64 else (16 * Z, 16 * Z))
    pad, hdr = 6, 18
    W = pad + 8 * (cw + pad)
    H = hdr + 2 * (ch + hdr) + 40
    im = Image.new("RGBA", (W, H), (24, 24, 28, 255))
    d = ImageDraw.Draw(im)
    d.text((pad, 4), title, fill=(235, 235, 235, 255))
    y0 = hdr + 18
    for i, (nm, a) in enumerate(zfiles):
        x = pad + i * (cw + pad)
        d.text((x, y0 - 16), nm.replace(".png", "")[-6:], fill=(160, 220, 255, 255))
        sub = Image.fromarray(a.astype(np.uint8)).resize((cw, ch), Image.NEAREST)
        im.alpha_composite(sub, (x, y0))
    y1 = y0 + ch + hdr
    for i, (nm, a) in enumerate(targets):
        x = pad + i * (cw + pad)
        d.text((x, y1 - 16), nm, fill=(255, 220, 150, 255))
        sub = Image.fromarray(a.astype(np.uint8)).resize((cw, ch), Image.NEAREST)
        im.alpha_composite(sub, (x, y1))
    im.save(out)


def main():
    os.makedirs(EVID, exist_ok=True)
    zfiles = sorted(f for f in os.listdir(ZIPDIR) if f.endswith(".png"))
    zarr = {f: arr(os.path.join(ZIPDIR, f)) for f in zfiles}
    # 尺寸只分三种：16x16(56) / 16x48(8) / 64x32(8)。
    # 56 张 16x16 按时间戳（文件名前缀）顺序切成 7 段 × 8 张 —— 每段对应一个"类"。
    big = [f for f in zfiles if zarr[f].shape[0] != 16 or zarr[f].shape[1] != 16]
    small = [f for f in zfiles if zarr[f].shape[0] == 16 and zarr[f].shape[1] == 16]
    groups, i = [], 0
    for _ in range(7):
        groups.append(small[i:i + 8])
        i += 8
    k16 = [k for k in KINDS if k[0].endswith("16")]
    named = {k16[j][0]: groups[j] for j in range(7)}
    for k in KINDS:
        if not k[0].endswith("16"):
            named[k[0]] = [f for f in big if zarr[f].shape == (
                arr(os.path.join(TEX, k[1].format(f=FAM[0]).replace("/", os.sep))).shape)]
    for kid, pat, _h in KINDS:
        tg = []
        for f in FAM:
            p = os.path.join(TEX, pat.format(f=f).replace("/", os.sep))
            tg.append((f, arr(p)))
        zg = [(f, zarr[f]) for f in named[kid]]
        print("\n=== %s  zip=%d ===" % (kid, len(zg)))
        print("%-22s %s" % ("", " ".join("%9s" % f[:9] for f in FAM)))
        for zf, za in zg:
            row = [mae(za, ta) for _, ta in tg]
            best = int(np.argmin(row))
            srt = sorted(row)
            print("%-22s %s  best=%-14s mae=%6.2f 2nd=%6.2f ratio=%.2f"
                  % (zf, " ".join("%9.2f" % v for v in row), FAM[best],
                     srt[0], srt[1], (srt[1] + 1e-9) / (srt[0] + 1e-9)))
        montage(zg, tg, "%s : top=zip(%s..) bottom=repo" % (kid, zg[0][0][:10]),
                os.path.join(EVID, "%s.png" % kid))


if __name__ == "__main__":
    main()
