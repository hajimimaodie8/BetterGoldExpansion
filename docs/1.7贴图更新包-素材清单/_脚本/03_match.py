# -*- coding: utf-8 -*-
"""1.7 贴图更新包 —— 逐文件"认亲"（像素匹配，可复算）

方法（全部可复算）：
  1) 精确层：SHA256 全等 -> 分数 1.0（本次应为 0 条，因为作者是"翻新"）
  2) 像素层：对每个 (zip 文件, 目标候选) 对计算
       alphaIoU = |A∩B| / |A∪B|        （A/B = alpha>0 的掩码，同尺寸逐像素）
       colorSim = 1 - min(1, d/120)     （d = 两张"不透明像素平均色"的 RGB 欧氏距离）
       score    = 0.5*alphaIoU + 0.5*colorSim
  3) 指派：同尺寸类内做 scipy.optimize.linear_sum_assignment（全局一对一指派），
     每个目标文件恰好被一张 zip 认领 —— 天然给出"与第二名的差距"（gap = best - second_best，
     第二名取的是"同尺寸类内除已指派目标外分数最高者"）。
  4) 候选集 B（作者上一包 docs\\新约10-素材清单\\新约10\\**）也参与打分，作为语义交叉验证。
输出：认亲表.tsv / 认亲详情.txt
"""
import sys, os, io, hashlib, zipfile
sys.stdout.reconfigure(errors="replace")
import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
SRC = r"E:\mc\mc资料\1.7的贴图更新包.zip"
ZIPDIR = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
CAND_B = os.path.join(BASE, "docs", "新约10-素材清单", "新约10")

FAMILIES = ["sturdygold", "indigoseagold", "illusiongold", "thornsgold",
            "thundergold", "voodoogold", "flamegold", "echogold"]

# 9 类目标 × 8 族 = 72 —— 与包内 72 张精确对应
KINDS = [
    ("lantern_block", "block/{f}_lantern.png",            "灯笼（方块放置样式，16x48 动画条）"),
    ("armor_layer1",  "models/armor/{f}_layer_1.png",     "盔甲穿戴层（靴子在 layer_1，64x32）"),
    ("bars",          "block/{f}_bars.png",               "栏杆（方块）"),
    ("chain_block",   "block/{f}_chain.png",              "链（方块放置样式）"),
    ("chain_item",    "item/{f}_chain.png",               "链（物品图标样式）"),
    ("axe",           "item/{f}_axe.png",                 "斧（物品图标）"),
    ("shovel",        "item/{f}_shovel.png",              "锹（物品图标）"),
    ("knife",         "item/{f}_knife.png",               "刀（物品图标）"),
    ("leggings_item", "item/{f}_leggings.png",            "护腿（物品图标样式）"),
]


def load(path):
    im = Image.open(path).convert("RGBA")
    return np.asarray(im).astype(np.float32)


def feats(a):
    mask = a[:, :, 3] > 0
    n = int(mask.sum())
    if n == 0:
        return mask, np.zeros(3, np.float64)
    rgb = a[:, :, :3][mask].astype(np.float64)
    return mask, rgb.mean(axis=0)


def pair_score(a, b):
    ma, ca = feats(a)
    mb, cb = feats(b)
    union = np.logical_or(ma, mb).sum()
    inter = np.logical_and(ma, mb).sum()
    iou = float(inter) / float(union) if union else 0.0
    d = float(np.linalg.norm(ca - cb))
    csim = 1.0 - min(1.0, d / 120.0)
    return 0.5 * iou + 0.5 * csim, iou, d


def main():
    # ---------- 读 zip ----------
    zp = []
    with zipfile.ZipFile(SRC, "r") as z:
        for i in z.infolist():
            if i.is_dir():
                continue
            data = z.read(i.filename)
            zp.append({"name": i.filename,
                       "sha": hashlib.sha256(data).hexdigest(),
                       "arr": load(os.path.join(ZIPDIR, i.filename))})
    zp.sort(key=lambda r: r["name"])
    print("[match] zip files = %d" % len(zp))

    # ---------- 候选集 A ----------
    tgt = []
    for kid, pat, desc in KINDS:
        for f in FAMILIES:
            rel = pat.format(f=f)
            p = os.path.join(TEX, rel.replace("/", os.sep))
            if not os.path.exists(p):
                print("[match] MISSING TARGET %s" % rel)
                continue
            a = load(p)
            tgt.append({"kind": kid, "fam": f, "rel": rel, "arr": a,
                        "sha": hashlib.sha256(open(p, "rb").read()).hexdigest()})
    print("[match] targets = %d" % len(tgt))

    # ---------- 精确层 ----------
    exact = 0
    for z in zp:
        for t in tgt:
            if z["sha"] == t["sha"]:
                print("[match] EXACT %s == %s" % (z["name"], t["rel"]))
                exact += 1
    print("[match] exact_matches = %d" % exact)

    # ---------- 候选集 B 交叉验证 ----------
    bfiles = []
    if os.path.isdir(CAND_B):
        for dp, dn, fn in os.walk(CAND_B):
            for f in fn:
                if f.lower().endswith(".png"):
                    bfiles.append(os.path.join(dp, f))
    print("[match] candB png = %d" % len(bfiles))

    def bestB(a):
        best = (0.0, None)
        for p in bfiles:
            try:
                arr = load(p)
            except Exception:
                continue
            if arr.shape != a.shape:
                continue
            s, _, _ = pair_score(a, arr)
            if s > best[0]:
                best = (s, os.path.relpath(p, CAND_B).replace("\\", "/"))
        return best

    # ---------- 按尺寸分组指派 ----------
    out_rows = []
    for shp in sorted({z["arr"].shape for z in zp}):
        zg = [z for z in zp if z["arr"].shape == shp]
        tg = [t for t in tgt if t["arr"].shape == shp]
        print("\n[match] === size %dx%d : zip=%d targets=%d ===" % (shp[0], shp[1], len(zg), len(tg)))
        if not tg:
            for z in zg:
                out_rows.append((z["name"], "?", "认不出", 0.0, 0.0, "", ""))
            continue
        M = np.zeros((len(zg), len(tg)), np.float64)
        for i, z in enumerate(zg):
            for j, t in enumerate(tg):
                M[i, j] = pair_score(z["arr"], t["arr"])[0]
        ri, ci = linear_sum_assignment(-M)
        assign = {i: j for i, j in zip(ri, ci)}
        for i, z in enumerate(zg):
            j = assign.get(i)
            if j is None:
                out_rows.append((z["name"], "?", "认不出", 0.0, 0.0, "", ""))
                continue
            s = M[i, j]
            others = sorted((M[i, k] for k in range(len(tg)) if k != j), reverse=True)
            second = others[0] if others else 0.0
            gap = s - second
            if s >= 0.80 and gap >= 0.15:
                verdict = "确定"
            elif s >= 0.62:
                verdict = "疑似"
            else:
                verdict = "认不出"
            t = tg[j]
            bs, bn = bestB(z["arr"])
            iou = pair_score(z["arr"], t["arr"])[1]
            out_rows.append((z["name"], t["rel"], verdict, s, gap,
                             "IoU=%.3f" % iou, bn or ""))
            print("  %-22s -> %-34s score=%.4f gap=%.4f  %s   [candB=%s %.3f]"
                  % (z["name"], t["rel"], s, gap, verdict, bn, bs))

    out = os.path.join(ZIPDIR, "认亲表.tsv")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("file\ttarget\tverdict\tscore\tgap\tevidence\tcandB_best\n")
        for r in sorted(out_rows):
            f.write("%s\t%s\t%s\t%.4f\t%.4f\t%s\t%s\n" % r)
    print("\n[match] wrote %s" % out)


if __name__ == "__main__":
    main()
