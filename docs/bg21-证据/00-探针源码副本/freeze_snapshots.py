#!/usr/bin/env python3
"""Freeze the bg21 before/after creative-order snapshots into tools/asset-generator/."""
import hashlib
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "run"


def head(title, fp, extra):
    return (
        "# bg21 冻结快照：创造页（bettergold:bettergold_tab）**全量非空物品顺序**（%s）\n"
        "# 来源：A 级客户端探针 `probe/bg21`（runClient + quickPlay 进 ASCII 探针世界 bg21probe），\n"
        "#       读 `CreativeModeTab#buildContents(...)` 之后的 `getDisplayItems()`；共 413 件非空（含 5 个分区）。\n"
        "# 环境：dev 客户端；农夫乐事 localRuntime 已加载；Patchouli jar 在 run/mods（手册在材料分区第一位）；未装 mut。\n"
        "# 指纹：sha256(ids, LF-joined) = %s\n"
        "%s\n"
        "# 行格式：<item 序号 1..413> <注册名>（序号 = 非空序列下标；创造页里还有分区空行，不计入）\n"
        % (title, fp, extra)
    )


before = (SRC / "bg21-order-before.txt").read_text(encoding="utf-8").strip().splitlines()
after = (SRC / "bg21-order-after.txt").read_text(encoding="utf-8").strip().splitlines()
print("before=%d after=%d" % (len(before), len(after)))
FP_B = "c675330145a814b78afb3e722e82a087ca00bcf42ea1a099ca66925bf8022284"
FP_A = "40771be25b3ebfa31e53035af018377266c55945a6d7f913a327f500d816493f"
b = head("改前基线（HEAD a9f0fe8，未加紧邻钉）", FP_B,
         "# 改前 5 件位次：金币串 5 / 混沌金币 64 / 刷怪蛋 23 / 高精度油 22 / 炼金燃油 3 / 金骨粉 4 / 盾牌胚底 10 / 万坚金砧 195 / 金雕苦力怕 189")
a = head("改后（+ ADJACENCY_PINS 5 条）", FP_A,
         "# 改后 5 件位次：高精度油 4（燃油 3 后）/ 盾牌胚底 9 → 金骨粉 10 / 刷怪蛋 62 → 金币串 63 → 混沌金币 64 / 万坚金砧 189（苦力怕 190 前）")
(REPO / "tools" / "asset-generator" / "bg21-creative-order-before.txt").write_text(
    b + "\n".join(before) + "\n", encoding="utf-8")
(REPO / "tools" / "asset-generator" / "bg21-creative-order-after.txt").write_text(
    a + "\n".join(after) + "\n", encoding="utf-8")
for f in ("tools/asset-generator/bg21-creative-order-before.txt",
          "tools/asset-generator/bg21-creative-order-after.txt"):
    p = REPO / f
    print(f, p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest().upper())
