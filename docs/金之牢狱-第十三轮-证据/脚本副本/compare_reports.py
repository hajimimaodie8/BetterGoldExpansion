# -*- coding: utf-8 -*-
"""对比 A 级探针报告：上一轮基线（lane.fallback=exit）vs 本轮（lane.fallback=room）。"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OLD = os.path.join(ROOT, "docs", "金之牢狱-第十二轮-证据", "01-改前-探针报告.json")
NEW = os.path.join(ROOT, "run", "probe", "gps", "report.json")

old = json.load(open(OLD, encoding="utf-8"))["A"]["runs"]["runs"]
new = json.load(open(NEW, encoding="utf-8"))["A"]["runs"]["runs"]
print("%-16s %-6s | %-22s | %-22s" % ("seed", "cp", "before(exit=68)", "after(lane=room)"))
for a, b in zip(old, new):
    assert (a["seed"], a["cp"]) == (b["seed"], b["cp"])
    print("%-16s %-6s | pieces=%-3d exits=%-3d | pieces=%-3d exits=%-3d %s"
          % (a["seed"], a["cp"], a["pieces"], a["exitCount"],
             b["pieces"], b["exitCount"],
             "SAME" if a["pieces"] == b["pieces"] and a["exitCount"] == b["exitCount"] else "DIFF"))
print()
for tag, runs in (("before", old), ("after", new)):
    c = Counter()
    for r in runs:
        for k, v in r["parentKindCounts"].items():
            c[k] += v
    print(tag, "totalExits=%d parentKinds=%s orphans=%d" % (
        sum(r["exitCount"] for r in runs), dict(c), sum(r["orphanCount"] for r in runs)))
    depths = Counter()
    for r in runs:
        for e in r["exits"]:
            depths[(e["depth"], e["parentTpl"])] += 1
    print(tag, "exit depth/parent:", dict(sorted(depths.items())))
print()
print("after tailKinds:", [r["tailKind"] for r in new[:4]])
print("before tailKinds:", [r["tailKind"] for r in old[:4]])
