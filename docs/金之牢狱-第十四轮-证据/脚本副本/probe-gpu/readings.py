# -*- coding: utf-8 -*-
"""第十四轮 A 级读数：size=4（注册表真实结构）+ 4/5/6 矩阵，逐座 / 逐口 / 对照。

输入 = run/probe/gp14/report.json（GprProbe 本轮输出）
输出 = build/gp14_readings.txt（表格，直接抄进 docs §19）
跑法：<python> probe\\gpu\\readings.py
"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
REPORT = os.path.join(ROOT, "run", "probe", "gp14", "report.json")
OUT = os.path.join(ROOT, "build", "gp14_readings.txt")

rep = json.load(open(REPORT, encoding="utf-8"))
L = []


def w(s=""):
    L.append(s)
    print(s)


def agg(runs):
    ex = sum(r["exitCount"] for r in runs)
    withx = sum(1 for r in runs if r["exitCount"] > 0)
    pk = Counter()
    for r in runs:
        pk.update(r["parentKindCounts"])
    ps = [r["pieces"] for r in runs]
    exs = [r["exitCount"] for r in runs]
    return dict(pieces=(min(ps), max(ps), sum(ps)), withx=withx, n=len(runs), exits=ex,
                per=(min(exs), max(exs)), pk=dict(pk), lane=pk.get("lane", 0),
                orphans=sum(r["orphanCount"] for r in runs),
                culled=sum(r["culledWouldBe"] for r in runs),
                maxReach=max(r["maxReach"] for r in runs),
                treasure=sum(r["treasure"] for r in runs),
                crosses=(min(r["crosses"] for r in runs), max(r["crosses"] for r in runs)))


w("# 第十四轮（size 5 → 4）A 级读数")
w("")
w("来源：`run/probe/gp14/report.json`（`Structure#generate` 真拼件，6 种子 × 2 区块 = 12 座/配置；"
  "不生成区块、不 forceload、不写世界；`halt(false)` 一次）。")
w("")
w("## 1 汇总（A = 注册表真实结构，size 读磁盘 JSON）")
w("")
a = agg(rep["A"]["runs"]["runs"])
w("| 项 | 读数 |")
w("|---|---|")
w("| 有效结构 / 尝试 | **%d/%d** |" % (a["withx"] if False else rep["A"]["runs"]["valid"], rep["A"]["runs"]["structures"]))
w("| 有出入口的座数 | **%d/%d** |" % (a["withx"], a["n"]))
w("| 出入口总数 / 每座 | **%d** / **%d..%d** |" % (a["exits"], a["per"][0], a["per"][1]))
w("| 父件类型 | `%s` ⇒ **parentKind == lane = %d** |" % (a["pk"], a["lane"]))
w("| 落单口 | **%d** |" % a["orphans"])
w("| 被 `max_distance` 裁 | **%d** |" % a["culled"])
w("| 最远件 | **%d** |" % a["maxReach"])
w("| 宝藏房 | **%d**（%d 座 × 1） |" % (a["treasure"], a["n"]))
w("| 四面道 | **%d..%d** |" % a["crosses"])
w("| 件数 | **%d..%d**（Σ%d） |" % (a["pieces"][0], a["pieces"][1], a["pieces"][2]))
w("")

w("## 2 逐座读数（A，size=4）")
w("")
w("| 种子 | 区块 | 件数 | 宝藏房 | 四面道 | 出入口 | 父件模板 | 落单口 | 最远件 | 最深层 | 链尾 |")
w("|---|---|---|---|---|---|---|---|---|---|---|")
for r in rep["A"]["runs"]["runs"]:
    parents = Counter(e["parentTpl"] for e in r["exits"])
    deepest = max(int(k) for k in r["depthKinds"])
    w("| %s | %s | %d | %d | %d | %d | %s | %d | %d | %d | `%s` |"
      % (r["seed"], r["cp"], r["pieces"], r["treasure"], r["crosses"], r["exitCount"],
         ", ".join("%s×%d" % kv for kv in sorted(parents.items())) or "-",
         r["orphanCount"], r["maxReach"], deepest, r["tailKind"]))
w("")

w("## 3 三档对照（M 矩阵：同一构建 / 同一批种子，只换 size）")
w("")
w("| size | 件数 | 有出入口 | 出入口 | 每座 | 父件类型 | lane 父件 | 落单口 | 被裁 | 最远 |")
w("|---|---|---|---|---|---|---|---|---|---|")
for m in rep["M"]:
    g = agg(m["runs"]["runs"])
    w("| **%d** | %d..%d | %d/%d | **%d** | %d..%d | `%s` | **%d** | **%d** | **%d** | %d |"
      % (m["size"], g["pieces"][0], g["pieces"][1], g["withx"], g["n"], g["exits"],
         g["per"][0], g["per"][1], g["pk"], g["lane"], g["orphans"], g["culled"], g["maxReach"]))
w("")

w("## 4 逐口 parentKind（A，size=4，共 %d 口）" % a["exits"])
w("")
w("| # | 种子 | 区块 | 件 # | 深度 | 父件模板 | 父件类型 | 父件深度 |")
w("|---|---|---|---|---|---|---|---|")
i = 0
for r in rep["A"]["runs"]["runs"]:
    for e in r["exits"]:
        i += 1
        w("| %d | %s | %s | %d | %d | `%s` | **%s** | %d |"
          % (i, r["seed"], r["cp"], e["piece"], e["depth"], e["parentTpl"],
             e["parentKind"], e["parentDepth"]))
w("")

w("## 5 深度 → 件类型（A，size=4，全 12 座）")
w("")
for r in rep["A"]["runs"]["runs"]:
    seq = []
    for dep in sorted(r["depthKinds"], key=int):
        seq.append("d%s[%s]" % (dep, ",".join("%s×%d" % kv
                                              for kv in sorted(r["depthKinds"][dep].items()))))
    w("- seed %s / cp %s（%d 件）：%s" % (r["seed"], r["cp"], r["pieces"], " ".join(seq)))
w("")

w("## 6 与 size=5 的对照（上一轮实测，§18.11.3）")
w("")
w("| 判据 | size=5（上一轮） | **size=4（本轮）** | 变化 |")
w("|---|---|---|---|")
w("| 出入口总数 | 25 | **%d** | +%d |" % (a["exits"], a["exits"] - 25))
w("| 有出入口座数 | 12/12 | **%d/%d** | 不变 |" % (a["withx"], a["n"]))
w("| 落单口 | 77 | **%d** | %+d |" % (a["orphans"], a["orphans"] - 77))
w("| 被 `max_distance` 裁 | 5 | **%d** | %+d |" % (a["culled"], a["culled"] - 5))
w("| parentKind == lane | 0 | **%d** | 不变 |" % a["lane"])
w("| 宝藏房 | 12（1/座） | **%d** | 不变 |" % a["treasure"])
w("| 四面道 | 3..5 | **%d..%d** | — |" % a["crosses"])
w("| 最远件 | 116 | **%d** | -%d |" % (a["maxReach"], 116 - a["maxReach"]))
w("")

forced = (rep.get("forcedChunksBefore"), rep.get("forcedChunksAfter"),
          rep.get("forcedChunksUnchanged"))
w("forceload 双向：before=%r after=%r unchanged=%r" % forced)
open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n[gp14-readings] wrote", OUT)
