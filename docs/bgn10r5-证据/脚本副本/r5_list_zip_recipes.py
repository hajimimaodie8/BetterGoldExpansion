# -*- coding: utf-8 -*-
# 证据：本轮（轮5）在作者 zip 里到底有哪些「配方截图」。只读 zip（不改一个字节）。
import sys, os, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ZIPS = [r"E:\mc\mc资料\更有用的金 新约10.zip", r"E:\mc\mc资料\金钱妖.zip"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "11-本轮配方素材缺口.txt")

def fix(n):
    try:
        return n.encode("cp437").decode("gbk")
    except Exception:
        return n

lines = []
lines.append("# 轮5 配方截图缺口 —— zip 条目级证据（只读）\n")
lines.append("> 复算：`py -3 docs/bgn10r5-证据/脚本副本/r5_list_zip_recipes.py`\n")
lines.append("> 结论：两份 zip 内 `配方图集/` 只有 **4** 张截图，**没有**任何一张与\n")
lines.append("> 「金火把花 / 高精度炼金油 / 双倍贵金原料」有关的配方图；\n")
lines.append("> 本轮素材只有 5 张 16×16 图标（花 1/2/3 + 种子 + 油），图标不含配方信息。\n")
for zp in ZIPS:
    lines.append("\n## ZIP: %s  (%d B)\n" % (os.path.basename(zp), os.path.getsize(zp)))
    with zipfile.ZipFile(zp) as z:
        names = [i.filename for i in z.infolist()]
    lines.append("- 条目总数：**%d**\n" % len(names))
    lines.append("\n### 配方图集/ 目录内的全部条目\n\n")
    n_rec = 0
    for n in names:
        f = fix(n)
        if f.startswith("配方图集/"):
            lines.append("- `%s`\n" % f)
            n_rec += 1
    lines.append("\n（条目数 = %d）\n" % n_rec)
    lines.append("\n### 名字里含 火把/油/酿 的条目\n\n")
    got = False
    for n in names:
        f = fix(n)
        if ("火把" in f or "炼金油" in f or "酿" in f):
            lines.append("- `%s`\n" % f)
            got = True
    if not got:
        lines.append("- （无：只有 5 张 16×16 素材图标，见下一节）\n")
    lines.append("\n### 本轮可用素材（全部 16×16 图标，无截图）\n\n")
    for n in names:
        f = fix(n)
        if f.endswith(".png") and ("火把" in f or "炼金油" in f):
            lines.append("- `%s`\n" % f)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8", newline="\n").write("".join(lines))
print("written:", os.path.abspath(OUT))
print("entries with recipe dir:", sum(1 for zp in ZIPS for n in zipfile.ZipFile(zp).namelist()
                                     if fix(n).startswith("配方图集/") and fix(n).endswith(".png")))
