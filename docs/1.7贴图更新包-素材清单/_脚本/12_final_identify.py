# -*- coding: utf-8 -*-
"""最终认亲表：候选集 A/B/C 三方比对 + 查重 + 判定。

候选集 C = 原版 jar 内贴图。本机无 1.21.1 客户端 jar，
改用 C:\\Users\\<user>\\.gradle\\caches\\forge_gradle\\minecraft_repo\\versions\\1.20.1\\client-extra.jar
（1.20.1 原版 assets，物品/方块图标与 1.21.1 基本一致），仅用于"排除这不是原版的"。

判定口径（三者皆需满足才算"确定"）：
  R1  best_MAE <= 2.0            （真配都是 0.1-1.9；任何一个错配都 >= 20）
  R2  ratio = 2nd_MAE/best_MAE >= 1.5
  R3  与目标 alpha 掩码完全一致、不透明像素数相同（同一条美术血脉）
  R4  best_MAE < vanilla_MAE（明显比任何原版贴图更像）
"""
import sys, os, io, hashlib, zipfile
sys.stdout.reconfigure(errors="replace")
import numpy as np
from PIL import Image

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
ZIPDIR = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
CAND_B = os.path.join(BASE, "docs", "新约10-素材清单", "新约10")
VJAR = os.path.expanduser(r"~\.gradle\caches\forge_gradle\minecraft_repo\versions\1.20.1\client-extra.jar")

FAM_ORDER = ["flamegold", "sturdygold", "thornsgold", "echogold",
             "indigoseagold", "voodoogold", "thundergold", "illusiongold"]
KIND = [("axe", "item/{f}_axe.png", "斧（物品图标）"),
        ("shovel", "item/{f}_shovel.png", "锹（物品图标）"),
        ("knife", "item/{f}_knife.png", "刀（物品图标）"),
        ("chain_block", "block/{f}_chain.png", "链 · 方块/放置样式"),
        ("chain_item", "item/{f}_chain.png", "链 · 物品图标样式"),
        ("bars", "block/{f}_bars.png", "栏杆（方块）"),
        ("leggings_item", "item/{f}_leggings.png", "护腿（物品图标样式）"),
        ("lantern_block", "block/{f}_lantern.png", "灯笼 · 方块放置样式（16x48）"),
        ("armor_layer1", "models/armor/{f}_layer_1.png", "盔甲穿戴层 · 靴子区（64x32）")]


def arr_bytes(b):
    return np.asarray(Image.open(io.BytesIO(b)).convert("RGBA")).astype(np.int32)


def arr(p):
    with open(p, "rb") as f:
        return arr_bytes(f.read())


def mae(a, b):
    if a.shape != b.shape:
        return 1e9
    return float(np.abs(a - b).mean())


def main():
    zf = sorted(f for f in os.listdir(ZIPDIR) if f.endswith(".png"))
    zarr = {f: arr(os.path.join(ZIPDIR, f)) for f in zf}
    zsha = {f: hashlib.sha256(open(os.path.join(ZIPDIR, f), "rb").read()).hexdigest() for f in zf}

    # 查重
    dup = {}
    for f in zf:
        dup.setdefault(zsha[f], []).append(f)
    dups = {k: v for k, v in dup.items() if len(v) > 1}
    print("[dup] 包内重复 SHA256 = %d" % len(dups))
    for k, v in dups.items():
        print("   ", k[:16], v)

    small = [f for f in zf if zarr[f].shape == (16, 16, 4)]
    big = {f: zarr[f].shape for f in zf if zarr[f].shape != (16, 16, 4)}
    groups = [small[i:i + 8] for i in range(0, 56, 8)]
    plan = {}
    for i, (kid, _p, _d) in enumerate(KIND):
        plan[kid] = groups[i] if kid not in ("lantern_block", "armor_layer1") else []
    plan["lantern_block"] = [f for f in zf if big.get(f) == (48, 16, 4)]
    plan["armor_layer1"] = [f for f in zf if big.get(f) == (32, 64, 4)]

    # 原版贴图池
    van = {}
    if os.path.exists(VJAR):
        with zipfile.ZipFile(VJAR) as z:
            for i in z.infolist():
                n = i.filename
                if n.startswith("assets/minecraft/textures/") and n.endswith(".png"):
                    try:
                        a = arr_bytes(z.read(n))
                    except Exception:
                        continue
                    van[n] = a
        print("[candC] vanilla textures = %d" % len(van))
    else:
        print("[candC] vanilla jar NOT FOUND -> 跳过 C")

    rows = []
    for kid, pat, desc in KIND:
        for i, name in enumerate(plan[kid]):
            t = arr(os.path.join(TEX, pat.format(f=FAM_ORDER[i]).replace("/", os.sep)))
            a = zarr[name]
            best = mae(a, t)
            # 同尺寸类内其它目标
            others = []
            for j, f2 in enumerate(FAM_ORDER):
                if j == i:
                    continue
                others.append((mae(a, arr(os.path.join(TEX, pat.format(f=f2).replace("/", os.sep)))), f2))
            others.sort()
            # 同尺寸、其它类的最像者（跨类第二）
            cross = []
            for kid2, pat2, _d2 in KIND:
                t2 = arr(os.path.join(TEX, pat2.format(f=FAM_ORDER[i]).replace("/", os.sep)))
                if t2.shape == a.shape and kid2 != kid:
                    for f2 in FAM_ORDER:
                        m2 = mae(a, arr(os.path.join(TEX, pat2.format(f=f2).replace("/", os.sep))))
                        cross.append((m2, f2))
            second = min(others[0][0], min(cross)[0] if cross else 1e9)
            ratio = second / (best + 1e-9)
            # 原版最像
            vbest = (1e9, "")
            for vn, va in van.items():
                if va.shape == a.shape:
                    m = mae(a, va)
                    if m < vbest[0]:
                        vbest = (m, vn)
            alpha_same = bool(np.array_equal(a[:, :, 3], t[:, :, 3]))
            op_same = int((a[:, :, 3] > 0).sum()) == int((t[:, :, 3] > 0).sum())
            if best <= 2.0 and ratio >= 1.5 and alpha_same and op_same and best < vbest[0]:
                verdict = "确定"
            elif best <= 6.0 and ratio >= 1.3:
                verdict = "疑似"
            else:
                verdict = "认不出"
            rows.append(dict(name=name, kind=kid, desc=desc, fam=FAM_ORDER[i],
                             target=pat.format(f=FAM_ORDER[i]), best=best, second=second,
                             ratio=ratio, vbest=vbest[0], vname=vbest[1],
                             alpha_same=alpha_same, op_same=op_same, verdict=verdict,
                             size="%dx%d" % (a.shape[1], a.shape[0]), mode="RGBA"))

    # 输出
    with open(os.path.join(ZIPDIR, "认亲表.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("file\ttarget\tkind\tfamily\tverdict\tMAE\tsecond_MAE\tratio\tvanilla_MAE\talpha_identical\tsize\tmode\n")
        for r in sorted(rows, key=lambda r: r["name"]):
            f.write("%s\t%s\t%s\t%s\t%s\t%.4f\t%.4f\t%.2f\t%.4f\t%s\t%s\t%s\n"
                    % (r["name"], r["target"], r["kind"], r["fam"], r["verdict"],
                       r["best"], r["second"], r["ratio"], r["vbest"],
                       "yes" if r["alpha_same"] else "no", r["size"], r["mode"]))
    from collections import Counter
    print("[verdict] %s" % Counter(r["verdict"] for r in rows))
    print("%-22s %-36s %-6s %7s %7s %6s %8s" % ("file", "target", "判定", "MAE", "2nd", "ratio", "vanilla"))
    for r in sorted(rows, key=lambda r: r["name"]):
        print("%-22s %-36s %-6s %7.3f %7.3f %6.2f %8.3f"
              % (r["name"], r["target"], r["verdict"], r["best"], r["second"], r["ratio"], r["vbest"]))


if __name__ == "__main__":
    main()
