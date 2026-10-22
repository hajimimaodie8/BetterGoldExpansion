# -*- coding: utf-8 -*-
"""把两份 A 级 report.json 汇总成一张表（overwroteNatural / 搬迁 / 退化 / 落单口 / 回归）。"""
import json
import os
import sys

sys.stdout.reconfigure(errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.abspath(os.path.join(HERE, ".."))

for fn in ("02-A-种子20261022.json", "03-B-种子7.json"):
    p = os.path.join(EVID, fn)
    if not os.path.exists(p):
        print("!! missing", fn)
        continue
    d = json.load(open(p, encoding="utf-8"))
    tot = {}
    ex = 0
    rel = []
    port_o = 0
    port_i = 0
    print("=" * 100)
    print(fn, "| world", d["world"], "| seed", d["levelSeed"], "| starts", d["startCount"],
          "| class", d["structureClass"], "| type", d["structureType"], "| typeIsOurs", d["typeIsOurs"])
    for s in d["structures"]:
        port_o += s["ports"]["orphansByTemplate"]
        port_i += s["ports"]["orphansInWorld"]
        row = []
        for e in s["exits"]:
            ex += 1
            r = e.get("record") or {}
            oc = r.get("outcome")
            tot[oc] = tot.get(oc, 0) + 1
            if oc == "relocated":
                rel.append((s["chunk"], r.get("dist"), r.get("strict"), r.get("candidates"),
                            r.get("overwroteNatural"), e.get("shellAirPct"), e.get("oldExitBlocksLeft"),
                            e.get("oldForeignBlocks"), e.get("doorway"), e.get("matched"), e.get("solidCells"),
                            e.get("interiorAirReached"), e.get("interiorAirTotal")))
            row.append("%s%s" % (oc, "" if oc != "relocated" else "(d=%s/%s)" % (r.get("dist"), "S" if r.get("strict") else "L")))
        print("  chunk %-8s pieces=%-3d treasure=%d cross=%d exits=%-2d ports=%d paired=%d orphansT=%d orphansW=%d"
              % (s["chunk"], s["pieces"], s["treasure"], s["cross"], len(s["exits"]),
                 s["ports"]["ports"], s["ports"]["paired"], s["ports"]["orphansByTemplate"], s["ports"]["orphansInWorld"]))
        print("      " + " ".join(row))
    print("  TOTAL exits=%d outcomes=%s orphansT=%d orphansW=%d" % (ex, tot, port_o, port_i))
    print("  relocated rows (chunk, dist, strict, candidates, outNat, shell%, oldLeft, foreign, door, matched/solid, intReached/total):")
    for r in rel:
        print("   ", r)
    print("  records:", len(d["relocationRecords"]))
