# -*- coding: utf-8 -*-
"""把 lane.json 的 fallback 在 room / exit 之间切换（逐字节写，两值等长）。"""
import sys

sys.stdout.reconfigure(errors="replace")
P = ("src/main/resources/data/bettergold/worldgen/template_pool/golden_prison/lane.json")
b = open(P, "rb").read()
want = sys.argv[1] if len(sys.argv) > 1 else "exit"
olds = {
    "room": b'"fallback": "bettergold:golden_prison/room"',
    "exit": b'"fallback": "bettergold:golden_prison/exit"',
}
cur = [k for k, v in olds.items() if v in b]
assert len(cur) == 1, cur
assert b.count(olds[cur[0]]) == 1
b = b.replace(olds[cur[0]], olds[want], 1)
open(P, "wb").write(b)
print("lane.fallback: %s -> %s (%d B)" % (cur[0], want, len(b)))
