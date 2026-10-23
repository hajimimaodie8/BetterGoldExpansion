# -*- coding: utf-8 -*-
"""gpm：打印两份报告里不可达出入口的 reason / blockers / 旧父口洪泛。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for name in ("02-A-种子20261022.json", "03-B-种子7.json"):
    p = os.path.join(ROOT, "docs", "金之牢狱-第九轮收尾-证据", name)
    d = json.load(open(p, encoding="utf-8"))
    print("#" * 20, name, d["chainSummary"])
    for row in d["structures"]:
        for ex in row.get("exits", []):
            if not ex.get("reachable"):
                r = ex.get("record") or {}
                print("--", row["chunk"], "#%s" % ex["idx"], "moved", ex["moved"], "dist", ex["dist"],
                      "mouth", ex["mouth"], "state", ex["mouthState"], "parent", ex["parentState"])
                print("   reachableNonSolid", ex.get("reachableNonSolid"),
                      "fromOldParent", ex.get("reachedFromOldParent"),
                      "reason", ex.get("reason"), "gap", ex.get("gapPathLen"))
                print("   blockers", ex.get("blockers"))
                print("   rec outcome", r.get("outcome"), "dist", r.get("dist"),
                      "restored", r.get("restored"), "skipped", r.get("skipped"),
                      "doorway", r.get("doorway"), "keptAir", r.get("keptAir"),
                      "viol", r.get("violations"), "over", r.get("overwroteNatural"))
