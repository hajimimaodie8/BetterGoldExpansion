# -*- coding: utf-8 -*-
"""由 认亲表.tsv 生成人读版 认亲表.md（按 类 分节，每张一行）。"""
import sys, os
from collections import OrderedDict
sys.stdout.reconfigure(errors="replace")

ZIPDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DESC = OrderedDict([
    ("lantern_block", ("灯笼 · 方块放置样式", "16x48", "作者原话「贵金灯笼的放置样式」")),
    ("armor_layer1", ("盔甲穿戴层 · 靴子区", "64x32", "作者原话「盔甲穿戴部分的靴子」；改动全落在 layer_1 的 leg_boot UV 区 (x0-15,y25-26)")),
    ("axe", ("斧 · 物品图标", "16x16", "作者原话「斧 … 的两种样式」之一（本包只到此一套）")),
    ("shovel", ("锹 · 物品图标", "16x16", "作者原话「锹 … 的两种样式」之一（本包只到此一套）")),
    ("knife", ("刀 · 物品图标", "16x16", "作者原话「刀 … 的两种样式」之一（本包只到此一套）")),
    ("chain_block", ("链 · 方块/放置样式", "16x16", "作者原话「链 的两种样式」之一 —— 落 block/<族>_chain.png")),
    ("chain_item", ("链 · 物品图标样式", "16x16", "作者原话「链 的两种样式」之二 —— 落 item/<族>_chain.png")),
    ("bars", ("栏杆", "16x16", "作者原话「栏杆」")),
    ("leggings_item", ("护腿 · 物品图标样式", "16x16", "作者原话「护腿的物品样式」")),
])


def main():
    rows = []
    with open(os.path.join(ZIPDIR, "认亲表.tsv"), encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            rows.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))
    by = OrderedDict((k, []) for k in DESC)
    for r in rows:
        by[r["kind"]].append(r)
    out = []
    out.append("# 1.7 贴图更新包 —— 认亲表（逐文件）\n")
    out.append("识别方法（可复算）：同尺寸前提下算 **逐像素 RGBA 平均绝对误差 MAE**；")
    out.append("类内用 `scipy.optimize.linear_sum_assignment` 做全局一对一指派；")
    out.append("`2nd` = 同尺寸类内次优目标的 MAE；`ratio = 2nd/MAE`；")
    out.append("`原版` = 与原版 `client-extra.jar` 内同尺寸贴图的最小 MAE（排除「这不是我们的」）。\n")
    out.append("判定三条同时满足 = **确定**：`MAE ≤ 2.0` + `ratio ≥ 1.5` + `alpha 掩码与不透明像素数与目标完全一致`。\n")
    out.append("| 类 | 张数 | 判定 |\n|---|---|---|\n")
    for k, v in by.items():
        d = DESC[k]
        n = len(v)
        vd = "、".join(sorted({x["verdict"] for x in v}))
        out.append("| %s | %d | %s |\n" % (d[0], n, vd))
    out.append("\n---\n")
    for k, v in by.items():
        d = DESC[k]
        out.append("\n## %s（%d 张 · %s）\n" % (d[0], len(v), d[1]))
        out.append("> %s\n\n" % d[2])
        out.append("| 数字文件名 | → 目标路径 | MAE | 2nd | ratio | 原版 | 尺寸 | 判定 |\n")
        out.append("|---|---|---|---|---|---|---|---|\n")
        for r in sorted(v, key=lambda r: r["target"]):
            out.append("| `%s` | `%s` | %.3f | %.3f | %.2fx | %.2f | %s %s | **%s** |\n"
                       % (r["file"], r["target"], float(r["MAE"]), float(r["second_MAE"]),
                          float(r["ratio"]), float(r["vanilla_MAE"]), r["size"], r["mode"], r["verdict"]))
    with open(os.path.join(ZIPDIR, "认亲表.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(out))
    print("[md] wrote 认亲表.md  rows=%d" % len(rows))


if __name__ == "__main__":
    main()
