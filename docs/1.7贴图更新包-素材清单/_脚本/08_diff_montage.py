# -*- coding: utf-8 -*-
"""生成"旧 / 新 / 差异"三联图（每类一张，取 8 族拼在一起），用于人眼核对翻新点。"""
import sys, os
sys.stdout.reconfigure(errors="replace")
import numpy as np
from PIL import Image, ImageDraw

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
ZIPDIR = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
EVID = os.path.join(ZIPDIR, "_识别证据")
FAM = ["flamegold", "sturdygold", "thornsgold", "echogold",
       "indigoseagold", "voodoogold", "thundergold", "illusiongold"]
KIND = [("axe", "item/{f}_axe.png"), ("shovel", "item/{f}_shovel.png"),
        ("knife", "item/{f}_knife.png"), ("chain_block", "block/{f}_chain.png"),
        ("chain_item", "item/{f}_chain.png"), ("bars", "block/{f}_bars.png"),
        ("leggings", "item/{f}_leggings.png"),
        ("lantern", "block/{f}_lantern.png"),
        ("armor_l1", "models/armor/{f}_layer_1.png")]
Z = 10


def arr(p):
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.int32)


def up(a):
    h, w = a.shape[0], a.shape[1]
    return Image.fromarray(a.astype(np.uint8)).resize((w * Z, h * Z), Image.NEAREST)


def main():
    os.makedirs(EVID, exist_ok=True)
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
        zf0 = plan[kid][0]
        a0 = zarr[zf0]
        cw, ch = a0.shape[1] * Z, a0.shape[0] * Z
        pad, hdr = 8, 20
        W = pad + 8 * (cw + pad)
        H = hdr + 3 * (ch + hdr) + 10
        im = Image.new("RGBA", (W, H), (22, 22, 26, 255))
        d = ImageDraw.Draw(im)
        d.text((pad, 3), "%s  rows: OLD(repo) / NEW(zip) / DIFF" % kid, fill=(240, 240, 240, 255))
        for row in range(3):
            y = hdr + row * (ch + hdr)
            for i, zf in enumerate(plan[kid]):
                t = arr(os.path.join(TEX, pat.format(f=FAM[i]).replace("/", os.sep)))
                a = zarr[zf]
                if row == 0:
                    img = up(t)
                elif row == 1:
                    img = up(a)
                else:
                    m = (np.abs(a - t).max(axis=2) > 0)
                    rgb = np.zeros_like(a)
                    rgb[:, :, 3] = 255
                    rgb[:, :, 0] = np.where(m, 255, 0)
                    rgb[:, :, 1] = np.where(m, 60, 40)
                    rgb[:, :, 2] = np.where(m, 60, 40)
                    base = a.copy()
                    base[:, :, 3] = np.minimum(base[:, :, 3], 60)
                    img = up(base)
                    lay = up(rgb)
                    mask = Image.fromarray(((rgb[:, :, 0] > 0) * 255).astype(np.uint8))
                    im.alpha_composite(img, (pad + i * (cw + pad), y))
                    im.paste((255, 0, 0, 255), (pad + i * (cw + pad), y, pad + i * (cw + pad) + cw, y + ch), mask.resize((cw, ch), Image.NEAREST))
                    d.text((pad + i * (cw + pad), y - 15), FAM[i], fill=(255, 220, 150, 255))
                    continue
                im.alpha_composite(img, (pad + i * (cw + pad), y))
                d.text((pad + i * (cw + pad), y - 15), FAM[i], fill=(255, 220, 150, 255))
        im.save(os.path.join(EVID, "diff_%s.png" % kid))
        print("wrote diff_%s.png" % kid)


if __name__ == "__main__":
    main()
