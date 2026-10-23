# -*- coding: utf-8 -*-
"""静态试算：用 validate_golden_prison.py 的 assemble（忠实模式）扫 size × fallback 组合，
看「出入口的父件类型」——只用来**选 size / 预判 wiring**，不作 A 级证据。

跑法（工作区自带 python，禁止 py -3）：
  <python> probe\\gps\\sim_scan.py
输出 build\\gps_sim_scan.txt
"""
import importlib.util
import os
import sys
from collections import Counter

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_golden_prison.py")
OUT = os.path.join(ROOT, "build", "gps_sim_scan.txt")

spec = importlib.util.spec_from_file_location("vgp", GATE)
vgp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vgp)

pieces = {n: vgp.load_piece(n) for n in vgp.EXPECT_SIZE
          if os.path.exists(os.path.join(vgp.STRUCT, n + ".nbt"))}
base = vgp.load_pools_actual()
print("pieces=%d pools=%d" % (len(pieces), len(base)))
print("base fallbacks: " + ", ".join("%s->%s" % (k, v[1]) for k, v in sorted(base.items())))

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


def variant(room_fb, lane_fb):
    p = {k: (list(v[0]), v[1]) for k, v in base.items()}
    p["room"] = (p["room"][0], room_fb)
    p["lane"] = (p["lane"][0], lane_fb)
    return p


w("# 静态试算（assemble 忠实模式 ×3 种子）—— 只用于选 size / 预判 wiring")
w("")
w("| room.fallback | lane.fallback | size | 件数 | 出入口 | 父件类型 | 链尾件 | 最深层 |")
w("|---|---|---|---|---|---|---|---|")
CASES = [("bettergold:golden_prison/exit", "bettergold:golden_prison/exit", "改前基线"),
         ("bettergold:golden_prison/exit", "bettergold:golden_prison/room", "本轮 wiring"),
         ("bettergold:golden_prison/exit", "bettergold:golden_prison/exit", "对照·lane 仍 exit")]
for label, (room_fb, lane_fb, _) in [(c[2], c) for c in CASES]:
    pools = variant(room_fb, lane_fb)
    for size in (4, 5, 6):
        vgp.MAX_DEPTH = size
        agg = Counter()
        tails = Counter()
        nps = []
        nexs = []
        for sd in (11, 22, 33):
            placed = vgp.assemble(pieces, False, pools, sd)
            ex = [z for z in placed if z["name"] == "exit"]
            nps.append(len(placed))
            nexs.append(len(ex))
            for z in ex:
                agg[kind(z["parent"]["name"])] += 1
            tail = [z for z in placed if z["depth"] == max(p["depth"] for p in placed)]
            for z in tail:
                tails[kind(z["name"])] += 1
        w("| `%s` | `%s` | %d | %s | %d | `%s` | `%s` | %d |"
          % (room_fb.split("/")[-1], lane_fb.split("/")[-1], size,
             "%d..%d" % (min(nps), max(nps)), sum(nexs), dict(agg), dict(tails),
             max(p["depth"] for p in vgp.assemble(pieces, False, pools, 11))))
w("")
open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\nwrote " + OUT)
