# -*- coding: utf-8 -*-
"""gpm：打印不可达出入口的 reason / blockers / 非固体口径。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
p = os.path.join(ROOT, "docs", "金之牢狱-第九轮收尾-证据", "02-A-种子20261022.json")
d = json.load(open(p, encoding="utf-8"))
for row in d["structures"]:
    for ex in row.get("exits", []):
        if not ex.get("reachable"):
            print("=" * 20, row["chunk"], "#", ex["idx"])
            for k in ("moved", "dist", "outcome", "mouth", "parent", "mouthState", "parentState",
                      "reachable", "reachableNonSolid", "reason", "gapPathLen", "blockers",
                      "oldCavity27Air", "oldDoorPlane9Air", "cavityFromParent", "oldMouth",
                      "oldParent", "oldParentState", "record"):
                print("  ", k, "=", ex.get(k))
            r = ex.get("record") or {}
            print("   rec:", {k: r.get(k) for k in ("oldMin", "oldMax", "newMin", "newMax", "dist",
                                                     "outcome", "restored", "skipped", "doorway",
                                                     "keptAir", "violations", "overwroteNatural")})
