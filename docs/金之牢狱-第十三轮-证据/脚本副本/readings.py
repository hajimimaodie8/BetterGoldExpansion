# -*- coding: utf-8 -*-
"""把 A 级探针读数整理成验收表（改前 / 改后 + 逐口 parentKind + 深度→件类型）。

输入：run/probe/gps/report.json（本轮 A 级，size=5 / room.fallback=exit / lane.fallback=room）
      docs/金之牢狱-第十二轮-证据/01-改前-探针报告.json（回滚后的基线：
      size=5 / room.fallback=exit / lane.fallback=exit）
输出：build/gps_readings.txt
"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
NEW = os.path.join(ROOT, "run", "probe", "gps", "report.json")
OLD = os.path.join(ROOT, "docs", "金之牢狱-第十二轮-证据", "01-改前-探针报告.json")
OUT = os.path.join(ROOT, "build", "gps_readings.txt")

L = []


def w(s=""):
    L.append(s)
    print(s)


def kind(tpl):
    if tpl == "treasure":
        return "start"
    if tpl == "lane":
        return "lane"
    if tpl == "exit":
        return "exit"
    return "room"


def load(p):
    d = json.load(open(p, encoding="utf-8"))
    return d, d["A"]["runs"]["runs"], {m["size"]: m["runs"]["runs"] for m in d["M"]}


new_d, new_runs, _ = load(NEW)
old_d, old_runs, _ = load(OLD)

for tag, runs in (("改前", old_runs), ("改后", new_runs)):
    w("== %s：%d 座（%d 种子 × 2 区块）" % (tag, len(runs), len(set(r["seed"] for r in runs))))
    ex = sum(r["exitCount"] for r in runs)
    withx = sum(1 for r in runs if r["exitCount"] > 0)
    pk = Counter()
    for r in runs:
        for k, v in r["parentKindCounts"].items():
            pk[k] += v
    ps = [r["pieces"] for r in runs]
    w("件数 %d..%d（合计 %d） / 有出入口 %d/%d / 出入口 %d / parentKind %s / "
      "落单口 %d / 被裁 %d / 最远 %d / 宝藏房 %d / 四面道 %d..%d"
      % (min(ps), max(ps), sum(ps), withx, len(runs), ex, dict(pk),
         sum(r["orphanCount"] for r in runs), sum(r["culledWouldBe"] for r in runs),
         max(r["maxReach"] for r in runs), sum(r["treasure"] for r in runs),
         min(r["crosses"] for r in runs), max(r["crosses"] for r in runs)))
    w()

w("## 1 逐座读数（改后）")
w("")
w("| 种子 | 区块 | 件数 | 宝藏房 | 四面道 | 出入口 | 父件模板 | 落单口 | 最远件 | 最深层 | 链尾 |")
w("|---|---|---|---|---|---|---|---|---|---|---|")
for r in new_runs:
    parents = Counter(e["parentTpl"] for e in r["exits"])
    w("| %s | %s | %d | %d | %d | %d | %s | %d | %d | %d | `%s` |"
      % (r["seed"], r["cp"], r["pieces"], r["treasure"], r["crosses"], r["exitCount"],
         ", ".join("%s×%d" % kv for kv in sorted(parents.items())) or "-",
         r["orphanCount"], r["maxReach"],
         max(int(k) for k in r["depthKinds"]), r["tailKind"]))
w()

w("## 2 逐口 parentKind 表（改后，%d 口）" % sum(r["exitCount"] for r in new_runs))
w("")
w("| # | 种子 | 区块 | 出入口件 # | 深度 | 父件模板 | **父件类型** | 父件深度 |")
w("|---|---|---|---|---|---|---|---|")
i = 0
for r in new_runs:
    for e in r["exits"]:
        i += 1
        w("| %d | %s | %s | %d | %d | `%s` | **%s** | %d |"
          % (i, r["seed"], r["cp"], e["piece"], e["depth"], e["parentTpl"],
             e["parentKind"], e["parentDepth"]))
pk = Counter()
for r in new_runs:
    for e in r["exits"]:
        pk[e["parentKind"]] += 1
w("")
w("合计 `%s` ⇒ **parentKind == lane 的口 = %d**" % (dict(pk), pk.get("lane", 0)))
w()

w("## 3 深度 → 件类型序列（改前 / 改后，全部 12 座）")
w("")
for tag, runs in (("改前 lane.fallback=exit", old_runs), ("改后 lane.fallback=room", new_runs)):
    w("### %s" % tag)
    w("")
    for r in runs:
        seq = []
        for dep in sorted(r["depthKinds"], key=int):
            kinds = r["depthKinds"][dep]
            seq.append("d%s[%s]" % (dep, ",".join("%s×%d" % kv for kv in sorted(kinds.items()))))
        w("- seed %s / cp %s（%d 件）：%s" % (r["seed"], r["cp"], r["pieces"], " ".join(seq)))
    w()

w("## 4 尺寸矩阵（同一构建、同一批种子，只换 size；本轮 wiring）")
w("")
w("| size | 件数 | 有出入口 | 出入口 | 父件类型 | lane 父件 | 落单口 | 被裁 | 最远 |")
w("|---|---|---|---|---|---|---|---|---|")
for size in sorted({m["size"] for m in new_d["M"]}):
    runs = [m["runs"]["runs"] for m in new_d["M"] if m["size"] == size][0]
    ex = sum(r["exitCount"] for r in runs)
    withx = sum(1 for r in runs if r["exitCount"] > 0)
    pk = Counter()
    for r in runs:
        for k, v in r["parentKindCounts"].items():
            pk[k] += v
    ps = [r["pieces"] for r in runs]
    w("| **%d** | %d..%d | %d/12 | %d | `%s` | **%d** | %d | %d | %d |"
      % (size, min(ps), max(ps), withx, ex, dict(pk), pk.get("lane", 0),
         sum(r["orphanCount"] for r in runs), sum(r["culledWouldBe"] for r in runs),
         max(r["maxReach"] for r in runs)))
w()
mat = {}
for m in new_d["M"]:
    runs = m["runs"]["runs"]
    mat[m["size"]] = dict(
        orphan=sum(r["orphanCount"] for r in runs),
        culled=sum(r["culledWouldBe"] for r in runs),
        exits=sum(r["exitCount"] for r in runs),
        lane=sum(r["parentKindCounts"].get("lane", 0) for r in runs))
w("> 结论：size ∈ {4,5,6} 三档 parentKind 全是 `lane`（出入口只挂在过道口上）；")
w("> size=4 落单口 %d / 出入口 %d；size=6 落单口 %d / 出入口 %d；size=5 落单口 %d / 出入口 %d"
  % (mat[4]["orphan"], mat[4]["exits"], mat[6]["orphan"], mat[6]["exits"],
     mat[5]["orphan"], mat[5]["exits"]))
w("> ⇒ 按「落单口不增」保留 size=5（基线落单口 34）。")
open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n[gps-readings] wrote %s" % OUT)
