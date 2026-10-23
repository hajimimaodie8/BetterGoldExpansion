# -*- coding: utf-8 -*-
"""gpm：查看归档报告的关键字段（world/seed/chunks/一条 exit 记录）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for name in ("02-A-种子20261022.json", "03-B-种子7.json"):
    p = os.path.join(ROOT, "docs", "金之牢狱-第九轮收尾-证据", name)
    if not os.path.exists(p):
        print("missing", name, os.path.getsize(p) if os.path.exists(p) else "")
        continue
    d = json.load(open(p, encoding="utf-8"))
    print("=" * 30, name, os.path.getsize(p), "B")
    for k in ("world", "levelSeed", "scanRadiusChunks", "startCount", "startChunks", "chainSummary"):
        print(k, "=", d.get(k))
    for row in d.get("structures", []):
        print("-- structure", row.get("chunk"), "pieces", row.get("pieces"), "treasure", row.get("treasure"),
              "cross", row.get("cross"), "chain", row.get("chain"))
        print("   ports", {k: v for k, v in (row.get("ports") or {}).items() if k != "detail"})
        for ex in (row.get("exits") or [])[:3]:
            print("   exit", ex.get("idx"), "moved", ex.get("moved"), "dist", ex.get("dist"),
                  "outcome", ex.get("outcome"), "mouth", ex.get("mouth"),
                  "reach", ex.get("reachable"), "cav", ex.get("oldCavity27Air"),
                  "door", ex.get("oldDoorPlane9Air"), "fromParent", ex.get("cavityFromParent"),
                  "oldMin", ex.get("oldOrigin"), "left", ex.get("oldExitBlocksLeft"),
                  "fore", ex.get("oldForeignBlocks"))
            r = ex.get("record") or {}
            print("        rec oldMin", r.get("oldMin"), "oldMax", r.get("oldMax"), "new", r.get("newMin"),
                  "dist", r.get("dist"), "outcome", r.get("outcome"), "restored", r.get("restored"),
                  "skipped", r.get("skipped"), "doorway", r.get("doorway"), "keptAir", r.get("keptAir"),
                  "viol", r.get("violations"), "over", r.get("overwroteNatural"))
