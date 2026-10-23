# -*- coding: utf-8 -*-
"""静态试算 2：size 1..8 × 本轮 wiring（room.fallback=exit, lane.fallback=room）——
看「出入口父件类型」「最深层件类型」。只用于选 size / 预判，不作 A 级证据。

跑法（工作区自带 python，禁止 py -3）：
  <python> probe\\gps\\sim_depth.py
"""
import importlib.util
import os
import sys
from collections import Counter

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")
OUT = os.path.join(ROOT, "build", "gps_sim_depth.txt")

spec = importlib.util.spec_from_file_location("vgp", GATE)
vgp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vgp)

pieces = {n: vgp.load_piece(n) for n in vgp.EXPECT_SIZE
          if os.path.exists(os.path.join(vgp.STRUCT, n + ".nbt"))}
base = vgp.load_pools_actual()
pools = {k: (list(v[0]), v[1]) for k, v in base.items()}
pools["room"] = (pools["room"][0], "bettergold:golden_prison/exit")
pools["lane"] = (pools["lane"][0], "bettergold:golden_prison/room")

L = []


def w(s=""):
    L.append(s)
    print(s)


def kind(n):
    if n == "treasure":
        return "start"
    if n == "lane":
        return "lane"
    if n == "exit":
        return "exit"
    return "room"


w("# 静态试算 2：size 1..8，room.fallback=exit / lane.fallback=room（6 种子）")
w("")
w("| size | 件数 | 出入口 | 出口父件 `lane` | 出口父件 `room` | 最深层件类型 | 最深 |")
w("|---|---|---|---|---|---|---|")
for size in range(1, 9):
    vgp.MAX_DEPTH = size
    agg = Counter()
    tails = Counter()
    nps, nexs = [], []
    for sd in (11, 22, 33, 44, 55, 66):
        placed = vgp.assemble(pieces, False, pools, sd)
        ex = [z for z in placed if z["name"] == "exit"]
        nps.append(len(placed))
        nexs.append(len(ex))
        for z in ex:
            agg[kind(z["parent"]["name"])] += 1
        md = max(p["depth"] for p in placed)
        for z in placed:
            if z["depth"] == md:
                tails[kind(z["name"])] += 1
    w("| %d | %d..%d | %d | %d | %d | `%s` | %d |"
      % (size, min(nps), max(nps), sum(nexs), agg.get("lane", 0), agg.get("room", 0),
         dict(tails), size + 1))
w("")
open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\nwrote " + OUT)
