# -*- coding: utf-8 -*-
"""A 级读数（第十三轮 A 方案终态）：三配置对照 + 逐口 parentKind + 深度序列 + 尺寸矩阵。

- 基线：exit.name=room / lane.fallback=exit / room.fallback=exit / size=5
        （docs/金之牢狱-第十二轮-证据/01-改前-探针报告.json）
- 中间：exit.name=lane / lane.fallback=room（本轮先按父代理「保持 room」跑的那一档）
        （docs/金之牢狱-第十三轮-证据/02a-…json）
- 终态：exit.name=lane / lane.fallback=exit / room.fallback=exit / size=5
        （run/probe/gps/report.json == 02-改后-探针报告.json）
输出 build/gps_readings2.txt
"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
E13 = os.path.join(ROOT, "docs", "金之牢狱-第十三轮-证据")
E12 = os.path.join(ROOT, "docs", "金之牢狱-第十二轮-证据")
OUT = os.path.join(ROOT, "build", "gps_readings2.txt")

L = []


def w(s=""):
    L.append(s)
    print(s)


def load(p):
    return json.load(open(p, encoding="utf-8"))


fin = load(os.path.join(ROOT, "run", "probe", "gps", "report.json"))
mid = load(os.path.join(E13, "02a-探针-exit-name-lane_lane-fb-room（0出口）.json"))
base = load(os.path.join(E12, "01-改前-探针报告.json"))

CONF = [("基线（exit.name=room, lane.fb=exit）", base["A"]["runs"]["runs"]),
        ("中间（exit.name=lane, lane.fb=room）", mid["A"]["runs"]["runs"]),
        ("终态（exit.name=lane, lane.fb=exit）", fin["A"]["runs"]["runs"])]

w("# 第十三轮 A 方案（改 exit.nbt 的 jigsaw name 4 字节）A 级读数")
w("")
w("| 配置 | 件数 | 有出入口 | 出入口 | 父件类型 | 落单口 | 被裁 | 最远 | 宝藏房 | 四面道 |")
w("|---|---|---|---|---|---|---|---|---|---|")
for tag, runs in CONF:
    ex = sum(r["exitCount"] for r in runs)
    withx = sum(1 for r in runs if r["exitCount"] > 0)
    pk = Counter()
    for r in runs:
        for k, v in r["parentKindCounts"].items():
            pk[k] += v
    ps = [r["pieces"] for r in runs]
    w("| %s | %d..%d | **%d/12** | **%d** | `%s` | %d | %d | %d | %d | %d..%d |"
      % (tag, min(ps), max(ps), withx, ex, dict(pk),
         sum(r["orphanCount"] for r in runs), sum(r["culledWouldBe"] for r in runs),
         max(r["maxReach"] for r in runs), sum(r["treasure"] for r in runs),
         min(r["crosses"] for r in runs), max(r["crosses"] for r in runs)))
w()

w("## 1 逐座读数（终态）")
w("")
w("| 种子 | 区块 | 件数 | 宝藏房 | 四面道 | 出入口 | 父件模板 | 落单口 | 最远件 | 最深层 | 链尾 |")
w("|---|---|---|---|---|---|---|---|---|---|---|")
for r in fin["A"]["runs"]["runs"]:
    parents = Counter(e["parentTpl"] for e in r["exits"])
    w("| %s | %s | %d | %d | %d | %d | %s | %d | %d | %d | `%s` |"
      % (r["seed"], r["cp"], r["pieces"], r["treasure"], r["crosses"], r["exitCount"],
         ", ".join("%s×%d" % kv for kv in sorted(parents.items())) or "-",
         r["orphanCount"], r["maxReach"], max(int(k) for k in r["depthKinds"]), r["tailKind"]))
w()

w("## 2 逐口 parentKind 表（终态，%d 口）" % sum(r["exitCount"] for r in fin["A"]["runs"]["runs"]))
w("")
w("| # | 种子 | 区块 | 出入口件 # | 深度 | 父件模板 | **父件类型** | 父件深度 |")
w("|---|---|---|---|---|---|---|---|")
i = 0
for r in fin["A"]["runs"]["runs"]:
    for e in r["exits"]:
        i += 1
        w("| %d | %s | %s | %d | %d | `%s` | **%s** | %d |"
          % (i, r["seed"], r["cp"], e["piece"], e["depth"], e["parentTpl"],
             e["parentKind"], e["parentDepth"]))
pk = Counter()
for r in fin["A"]["runs"]["runs"]:
    for e in r["exits"]:
        pk[e["parentKind"]] += 1
w("")
w("合计 `%s` ⇒ **parentKind == lane 的口 = %d**" % (dict(pk), pk.get("lane", 0)))
w()

w("## 3 深度 → 件类型序列（终态，全 12 座）")
w("")
for r in fin["A"]["runs"]["runs"]:
    seq = []
    for dep in sorted(r["depthKinds"], key=int):
        seq.append("d%s[%s]" % (dep, ",".join("%s×%d" % kv
                                              for kv in sorted(r["depthKinds"][dep].items()))))
    w("- seed %s / cp %s（%d 件）：%s" % (r["seed"], r["cp"], r["pieces"], " ".join(seq)))
w()

w("## 4 尺寸矩阵（终态 wiring，只换 size）")
w("")
w("| size | 件数 | 有出入口 | 出入口 | 父件类型 | lane 父件 | 落单口 | 被裁 | 最远 |")
w("|---|---|---|---|---|---|---|---|---|")
for m in fin["M"]:
    runs = m["runs"]["runs"]
    pk = Counter()
    for r in runs:
        for k, v in r["parentKindCounts"].items():
            pk[k] += v
    ps = [r["pieces"] for r in runs]
    w("| **%d** | %d..%d | %d/12 | %d | `%s` | **%d** | %d | %d | %d |"
      % (m["size"], min(ps), max(ps), sum(1 for r in runs if r["exitCount"] > 0),
         sum(r["exitCount"] for r in runs), dict(pk), pk.get("lane", 0),
         sum(r["orphanCount"] for r in runs), sum(r["culledWouldBe"] for r in runs),
         max(r["maxReach"] for r in runs)))
w("")
open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n[gps-readings2] wrote %s" % OUT)
